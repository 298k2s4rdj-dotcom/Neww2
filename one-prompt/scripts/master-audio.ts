/**
 * Masters the rendered film's audio to YouTube loudness (-14 LUFS, -1.5 dBTP)
 * with a two-pass loudnorm. The video stream is copied untouched.
 * Uses the ffmpeg that ships with Remotion (`npx remotion ffmpeg`).
 *
 *   npm run master            # processes out/one-prompt.mp4 in place
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(import.meta.dirname, "..");
const file = path.resolve(ROOT, process.argv[2] ?? "out/one-prompt.mp4");
const TARGET = { I: -14, TP: -1.5, LRA: 11 };

if (!fs.existsSync(file)) {
  console.error(`✖ ${path.relative(ROOT, file)} not found – run "npm run render" first.`);
  process.exit(1);
}

const ffmpeg = (args: string[]) =>
  spawnSync("npx", ["remotion", "ffmpeg", ...args], { cwd: ROOT, encoding: "utf8", shell: process.platform === "win32", maxBuffer: 64 * 1024 * 1024 });

const filter = `loudnorm=I=${TARGET.I}:TP=${TARGET.TP}:LRA=${TARGET.LRA}`;
console.log("[master] measuring loudness…");
const pass1 = ffmpeg(["-hide_banner", "-i", file, "-af", `${filter}:print_format=json`, "-vn", "-f", "null", "-"]);
const json = (pass1.stderr ?? "").match(/\{[^{}]*"input_i"[^{}]*\}/);
if (!json) {
  console.error("✖ Could not measure loudness:\n" + pass1.stderr);
  process.exit(1);
}
const m = JSON.parse(json[0]);
console.log(`[master] input ${m.input_i} LUFS, true peak ${m.input_tp} dBTP → target ${TARGET.I} LUFS`);

const tmp = file.replace(/\.mp4$/, ".mastering.mp4");
const pass2 = ffmpeg([
  "-hide_banner", "-y", "-i", file,
  "-af",
  `${filter}:measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true`,
  "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart",
  tmp,
]);
if (pass2.status !== 0 || !fs.existsSync(tmp)) {
  console.error("✖ Mastering failed:\n" + pass2.stderr);
  process.exit(1);
}
fs.renameSync(tmp, file);
console.log(`[master] ✔ ${path.relative(ROOT, file)} mastered`);

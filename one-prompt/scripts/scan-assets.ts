/**
 * Scans /public for optional audio files and writes src/generated/assets.json:
 *   { "music": "music.mp3", "rain": "sfx/rain.mp3", ... }
 * Every file in public/sfx is registered under its base name. The film only
 * mounts <Audio> for files that exist, so missing music/SFX simply render
 * silently instead of crashing the render.
 */
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const publicDir = path.join(root, "public");
const outFile = path.join(root, "src", "generated", "assets.json");
const EXT = [".mp3", ".wav", ".m4a", ".aac", ".ogg"];

const found: Record<string, string> = {};
const music = EXT.map((e) => "music" + e).find((f) => fs.existsSync(path.join(publicDir, f)));
if (music) found.music = music;

const sfxDir = path.join(publicDir, "sfx");
if (fs.existsSync(sfxDir)) {
  for (const file of fs.readdirSync(sfxDir).sort()) {
    const ext = path.extname(file).toLowerCase();
    if (!EXT.includes(ext)) continue;
    found[path.basename(file, ext)] = `sfx/${file}`;
  }
}

fs.mkdirSync(path.dirname(outFile), { recursive: true });
fs.writeFileSync(outFile, JSON.stringify(found, null, 2) + "\n");
const n = Object.keys(found).length;
console.log(n ? `[assets] ${n} audio files: ${Object.keys(found).join(", ")}` : "[assets] no audio files found – rendering silently");

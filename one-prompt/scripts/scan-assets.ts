/**
 * Scans /public for optional audio files and writes src/generated/assets.json.
 * The film only mounts <Audio> for files that exist, so missing music/SFX
 * simply render silently instead of crashing the render.
 */
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const publicDir = path.join(root, "public");
const outFile = path.join(root, "src", "generated", "assets.json");
const EXT = [".mp3", ".wav", ".m4a", ".aac", ".ogg"];

const SLOTS = {
  music: "music",
  alarm: "sfx/alarm",
  keyboard: "sfx/keyboard",
  rain: "sfx/rain",
  crumple: "sfx/paper-crumple",
  ding: "sfx/ding",
} as const;

const found: Record<string, string | null> = {};
for (const [key, base] of Object.entries(SLOTS)) {
  const hit = EXT.map((e) => base + e).find((rel) => fs.existsSync(path.join(publicDir, rel)));
  found[key] = hit ?? null;
}

fs.mkdirSync(path.dirname(outFile), { recursive: true });
fs.writeFileSync(outFile, JSON.stringify(found, null, 2) + "\n");
const present = Object.entries(found).filter(([, v]) => v).map(([k, v]) => `${k} → ${v}`);
console.log(`[assets] ${present.length ? present.join(", ") : "no audio files found – rendering silently"}`);

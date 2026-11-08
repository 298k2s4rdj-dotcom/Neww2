/**
 * Uploads out/one-prompt.mp4 to YouTube (Data API v3).
 *
 *   npm run upload                 # private (default)
 *   npm run upload -- --public     # public
 *   npm run upload -- --unlisted   # unlisted
 *   npm run upload -- --no-thumbnail
 *   npm run upload -- --file path/to/video.mp4
 *
 * Auth: OAuth2 desktop flow. Put client_secret.json (Desktop app credentials
 * from Google Cloud Console) in the project root. The first run opens the
 * consent page and stores the token in token.json, which later runs reuse.
 */
import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import type { AddressInfo } from "node:net";
import path from "node:path";
import { google } from "googleapis";
import type { OAuth2Client } from "google-auth-library";

const ROOT = path.resolve(import.meta.dirname, "..");
const CLIENT_SECRET = path.join(ROOT, "client_secret.json");
const TOKEN = path.join(ROOT, "token.json");
const SCOPES = ["https://www.googleapis.com/auth/youtube.upload"];
const CHUNK = 8 * 1024 * 1024; // must be a multiple of 256 KiB

const METADATA = {
  snippet: {
    title: "ONE PROMPT | An Animated Short Film About Learning AI",
    description:
      "You don't need a 30-day course to learn AI. You need one prompt a day.\n\nA short animated film about starting small and staying consistent.\n\nFollow @howtowithai on X for daily AI tips.",
    tags: ["ai for beginners", "learn ai", "chatgpt", "habits", "animated short film", "motivation", "consistency"],
    categoryId: "1", // Film & Animation
    defaultLanguage: "en",
    defaultAudioLanguage: "en",
  },
  status: {
    privacyStatus: "private" as "private" | "public" | "unlisted",
    selfDeclaredMadeForKids: false,
  },
};

/* ------------------------------ arguments ------------------------------ */
const args = process.argv.slice(2);
const flag = (name: string) => args.includes(`--${name}`);
const option = (name: string) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : undefined;
};
if (flag("public")) METADATA.status.privacyStatus = "public";
if (flag("unlisted")) METADATA.status.privacyStatus = "unlisted";
const videoPath = path.resolve(ROOT, option("file") ?? "out/one-prompt.mp4");
const thumbPath = path.resolve(ROOT, option("thumbnail") ?? "out/thumbnail.png");
const wantThumb = !flag("no-thumbnail");

/* -------------------------------- auth --------------------------------- */
function openBrowser(url: string) {
  const cmd = process.platform === "darwin" ? "open" : process.platform === "win32" ? "cmd" : "xdg-open";
  const cmdArgs = process.platform === "win32" ? ["/c", "start", "", url] : [url];
  try {
    const child = spawn(cmd, cmdArgs, { stdio: "ignore", detached: true });
    child.on("error", () => undefined);
    child.unref();
  } catch {
    /* the URL is printed anyway */
  }
}

async function authorize(): Promise<OAuth2Client> {
  if (!fs.existsSync(CLIENT_SECRET)) {
    throw new Error(
      `Missing ${path.basename(CLIENT_SECRET)} in the project root.\n` +
        "Create an OAuth client ID (type: Desktop app) in Google Cloud Console with the YouTube Data API v3 enabled, download the JSON and save it as client_secret.json. See README.md.",
    );
  }
  const raw = JSON.parse(fs.readFileSync(CLIENT_SECRET, "utf8"));
  const cfg = raw.installed ?? raw.web;
  if (!cfg?.client_id || !cfg?.client_secret) throw new Error("client_secret.json has no client_id/client_secret.");

  const client = new google.auth.OAuth2(cfg.client_id, cfg.client_secret);
  // Persist refreshed tokens (keep the refresh_token, Google only sends it once).
  client.on("tokens", (tokens) => {
    const prev = fs.existsSync(TOKEN) ? JSON.parse(fs.readFileSync(TOKEN, "utf8")) : {};
    fs.writeFileSync(TOKEN, JSON.stringify({ ...prev, ...tokens }, null, 2));
  });

  if (fs.existsSync(TOKEN)) {
    client.setCredentials(JSON.parse(fs.readFileSync(TOKEN, "utf8")));
    try {
      await client.getAccessToken();
      console.log("✔ Using saved token (token.json)");
      return client;
    } catch {
      console.log("Saved token is no longer valid – starting a new sign-in.");
      fs.rmSync(TOKEN);
    }
  }

  // Loopback flow: Google redirects to a temporary local server with ?code=...
  const server = http.createServer();
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const redirectUri = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  const url = client.generateAuthUrl({ access_type: "offline", prompt: "consent", scope: SCOPES, redirect_uri: redirectUri });

  console.log("\nOpen this URL to authorize the upload (opening your browser…):\n\n" + url + "\n");
  openBrowser(url);

  const code = await new Promise<string>((resolve, reject) => {
    server.on("request", (req, res) => {
      const q = new URL(req.url ?? "/", redirectUri).searchParams;
      const err = q.get("error");
      const c = q.get("code");
      if (!c && !err) {
        res.writeHead(404).end();
        return;
      }
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(
        err
          ? `<h2>Authorization failed: ${err}</h2>`
          : "<h2>Authorized ✔</h2><p>You can close this tab and return to the terminal.</p>",
      );
      server.close();
      if (err) reject(new Error(`Authorization failed: ${err}`));
      else resolve(c!);
    });
  });

  const { tokens } = await client.getToken({ code, redirect_uri: redirectUri });
  client.setCredentials(tokens);
  fs.writeFileSync(TOKEN, JSON.stringify(tokens, null, 2));
  console.log("✔ Authorized – token saved to token.json");
  return client;
}

/* --------------------------- progress output --------------------------- */
const MB = 1024 * 1024;
function progress(done: number, total: number, startedAt: number) {
  const width = 30;
  const p = total ? done / total : 0;
  const filled = Math.round(p * width);
  const secs = (Date.now() - startedAt) / 1000;
  const speed = secs > 0 ? done / MB / secs : 0;
  const eta = speed > 0 ? (total - done) / MB / speed : 0;
  const line =
    `  [${"█".repeat(filled)}${"░".repeat(width - filled)}] ${(p * 100).toFixed(1).padStart(5)}%  ` +
    `${(done / MB).toFixed(1)}/${(total / MB).toFixed(1)} MB  ${speed.toFixed(2)} MB/s  ETA ${Math.ceil(eta)}s`;
  if (process.stdout.isTTY) process.stdout.write(`\r${line}`);
  else console.log(line);
}

/* --------------------------- resumable upload -------------------------- */
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function bearer(auth: OAuth2Client) {
  const { token } = await auth.getAccessToken();
  if (!token) throw new Error("Could not get an access token.");
  return `Bearer ${token}`;
}

async function startSession(auth: OAuth2Client, size: number): Promise<string> {
  const res = await fetch("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status", {
    method: "POST",
    headers: {
      Authorization: await bearer(auth),
      "Content-Type": "application/json; charset=UTF-8",
      "X-Upload-Content-Length": String(size),
      "X-Upload-Content-Type": "video/mp4",
    },
    body: JSON.stringify(METADATA),
  });
  const location = res.headers.get("location");
  if (!res.ok || !location) throw new Error(`Could not start upload (${res.status}): ${await res.text()}`);
  return location;
}

/** Ask the server how many bytes it already has (after an interruption). */
async function queryOffset(auth: OAuth2Client, session: string, size: number): Promise<number | { id: string }> {
  const res = await fetch(session, {
    method: "PUT",
    headers: { Authorization: await bearer(auth), "Content-Range": `bytes */${size}` },
  });
  if (res.status === 200 || res.status === 201) return (await res.json()) as { id: string };
  if (res.status === 308) {
    const range = res.headers.get("range");
    return range ? Number(range.split("-")[1]) + 1 : 0;
  }
  throw new Error(`Upload session lost (${res.status}): ${await res.text()}`);
}

async function uploadVideo(auth: OAuth2Client, file: string): Promise<string> {
  const size = fs.statSync(file).size;
  const fd = fs.openSync(file, "r");
  const session = await startSession(auth, size);
  const startedAt = Date.now();
  let offset = 0;
  let retries = 0;
  console.log(`\nUploading ${path.relative(ROOT, file)} (${(size / MB).toFixed(1)} MB) as ${METADATA.status.privacyStatus}…`);
  progress(0, size, startedAt);

  try {
    while (true) {
      const end = Math.min(offset + CHUNK, size);
      const buf = Buffer.alloc(end - offset);
      fs.readSync(fd, buf, 0, buf.length, offset);
      try {
        const res = await fetch(session, {
          method: "PUT",
          headers: {
            Authorization: await bearer(auth),
            "Content-Length": String(buf.length),
            "Content-Type": "video/mp4",
            "Content-Range": `bytes ${offset}-${end - 1}/${size}`,
          },
          body: buf,
        });
        if (res.status === 200 || res.status === 201) {
          progress(size, size, startedAt);
          const body = (await res.json()) as { id: string };
          process.stdout.write("\n");
          return body.id;
        }
        if (res.status === 308) {
          const range = res.headers.get("range");
          offset = range ? Number(range.split("-")[1]) + 1 : 0;
          retries = 0;
          progress(offset, size, startedAt);
          continue;
        }
        if (res.status >= 500 || res.status === 429) throw new Error(`HTTP ${res.status}`);
        throw Object.assign(new Error(`Upload failed (${res.status}): ${await res.text()}`), { fatal: true });
      } catch (e) {
        if ((e as { fatal?: boolean }).fatal || retries >= 8) throw e;
        retries++;
        const wait = Math.min(64, 2 ** retries) * 1000;
        console.log(`\n  ⚠ ${(e as Error).message} – retrying in ${wait / 1000}s (attempt ${retries}/8)`);
        await sleep(wait);
        const status = await queryOffset(auth, session, size);
        if (typeof status === "object") return status.id;
        offset = status;
      }
    }
  } finally {
    fs.closeSync(fd);
  }
}

/* -------------------------------- main --------------------------------- */
async function main() {
  if (!fs.existsSync(videoPath)) {
    throw new Error(`Video not found: ${path.relative(ROOT, videoPath)}\nRun "npm run render" first.`);
  }
  const auth = await authorize();
  const id = await uploadVideo(auth, videoPath);
  console.log(`✔ Uploaded. Video ID: ${id}`);

  if (wantThumb) {
    if (!fs.existsSync(thumbPath)) {
      console.log("Rendering thumbnail (npm run thumbnail)…");
      spawnSync("npm", ["run", "thumbnail"], { cwd: ROOT, stdio: "inherit", shell: process.platform === "win32" });
    }
    if (fs.existsSync(thumbPath)) {
      try {
        const youtube = google.youtube({ version: "v3", auth });
        await youtube.thumbnails.set({
          videoId: id,
          media: { mimeType: "image/png", body: fs.createReadStream(thumbPath) },
        });
        console.log("✔ Custom thumbnail set");
      } catch (e) {
        console.warn(
          `⚠ Could not set the thumbnail: ${(e as Error).message}\n` +
            "  (Custom thumbnails need a phone-verified channel: youtube.com/verify.) The video itself is uploaded.",
        );
      }
    } else {
      console.warn("⚠ No thumbnail found – skipped.");
    }
  }

  console.log(`\n🎬 https://www.youtube.com/watch?v=${id}`);
  console.log(`   Studio: https://studio.youtube.com/video/${id}/edit`);
}

main().catch((e) => {
  console.error(`\n✖ ${(e as Error).message}`);
  process.exit(1);
});

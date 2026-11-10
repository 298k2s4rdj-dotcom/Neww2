#!/usr/bin/env python3
"""Vertical Shorts (1080x1920) cut from the landscape video '1 Woche ohne Schlaf'.

Each short: "Rate mal"-hook (new voice line) -> scenes from the long video (visuals re-rendered without
subtitles, audio sliced from the master mix incl. SFX/music) -> call-to-action card pointing to the full video.
Usage: python3 shorts.py [--stills] [name ...]
"""
import json
import math
import os
import random
import subprocess
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[1:]
sys.argv = [sys.argv[0]]
import render as R  # noqa: E402
import longlib as L  # noqa: E402
from longlib import text, text_w, NAVY, YELLOW, WHITE, RED, GREEN, FONT_XB, ease_out, ease_io, back_out, prog  # noqa: E402

PW, PH, FPS, SR = 1080, 1920, 30, 48000
CROP = (60, 115, 1860, 1128)              # 1800x1013: whole scene incl. edges              # 16:9 window of the landscape frame
PANEL = (90, 600, 990, 1106)               # 900x506, 90 px margin each side             # 1000x563 in the portrait frame
SUB_Y = 1340
RAW = os.path.join(HERE, "audio_raw")
BUILD = os.path.join(HERE, "build")
OUT = os.path.join(HERE, "shorts")

SHORTS = {
    "short1_betrunken": dict(hook="h1", head=["24 H WACH =", "BETRUNKEN?"], preview=("s04", "Sekundenschlaf", 1.0),
                             pieces=["s03", "s04"]),
    "short2_gefuehle": dict(hook="h2", head=["1 NACHT OHNE", "SCHLAF: +60 %"], preview=("s05", "60", 0.5),
                            pieces=["s05", "s07"]),
    "short3_halluzinationen": dict(hook="h3", head=["3 TAGE OHNE", "SCHLAF?!"], preview=("s09", "flimmern", 0.3),
                                   pieces=["c3", "s09", "s10", "s11"]),
    "short4_kaffee": dict(hook="h4", head=["KAFFEE MACHT", "NICHT FIT?"], preview=("s02", "Koffein", 1.2),
                          pieces=["s02", "s15"]),
}

PIECES = []
TOTAL = 0.0
PBG = None


# ------------------------------------------------------------------ timeline
def words(name, pre=0.0):
    w = json.load(open(os.path.join(RAW, name + ".words.json")))["words"]
    return [dict(text=x["text"], s=x["start"] + pre, e=x["end"] + pre) for x in w]


def voice_wav(name):
    wav = os.path.join(BUILD, name + ".wav")
    dur = L.mp3_to_wav(os.path.join(RAW, name + ".mp3"), wav)
    return wav, dur


def build(spec):
    global TOTAL
    PIECES.clear()
    t = 0.0
    wav, d = voice_wav(spec["hook"])
    PIECES.append(dict(kind="hook", start=t, dur=0.15 + d + 0.35, wav=wav, pre=0.15, toks=words(spec["hook"], 0.15)))
    t += PIECES[-1]["dur"]
    for key in spec["pieces"]:
        seg = L.BY[key]
        PIECES.append(dict(kind="land", start=t, dur=seg["dur"], seg=seg, toks=seg["toks"]))
        t += seg["dur"]
    wav, d = voice_wav("cta")
    PIECES.append(dict(kind="cta", start=t, dur=0.2 + d + 1.6, wav=wav, pre=0.2, toks=words("cta", 0.2)))
    t += PIECES[-1]["dur"]
    TOTAL = t


def piece_at(gt):
    for p in PIECES:
        if gt < p["start"] + p["dur"]:
            return p
    return PIECES[-1]


# ------------------------------------------------------------------ drawing
def portrait_bg():
    y = np.linspace(0, 1, PH)[:, None, None]
    bg = np.array([12, 14, 52]) * (1 - y) + np.array([70, 30, 120]) * y
    bg = np.repeat(bg, PW, axis=1)
    yy, xx = np.mgrid[0:PH, 0:PW]
    g = np.exp(-(((xx - PW / 2) / 600) ** 2 + ((yy - 870) / 600) ** 2))[..., None]
    bg = bg + g * np.array([40, 50, 110])
    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    r = random.Random(9)
    for _ in range(260):
        x, yv, s = r.uniform(0, PW), r.uniform(0, PH), r.uniform(0.8, 2.4)
        v = int(r.uniform(110, 230))
        d.ellipse((x - s, yv - s, x + s, yv + s), fill=(v, v, v + 20))
    return img


_mask = None


def panel_mask(w, h):
    global _mask
    if _mask is None or _mask.size != (w, h):
        _mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(_mask).rounded_rectangle((0, 0, w - 1, h - 1), 34, fill=255)
    return _mask


def paste_panel(img, src, s=1.0):
    x0, y0, x1, y1 = PANEL
    w, h = int((x1 - x0) * s), int((y1 - y0) * s)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    src = src.resize((w, h), Image.BILINEAR)
    bx, by = int(cx - w / 2), int(cy - h / 2)
    ImageDraw.Draw(img).rounded_rectangle((bx - 7, by - 7, bx + w + 7, by + h + 7), 38, fill=WHITE)
    img.paste(src, (bx, by), panel_mask(w, h))


def land_frame(seg, t):
    gt = seg["start"] + t
    im = L.BG.copy()
    L.draw_bg(im, gt)
    L.CFG["draw"](im, seg, t, gt)
    return im.crop(CROP)


def headline(img, lines, t, a=1.0, big=False):
    y = 395 if not big else 370
    for i, ln in enumerate(lines):
        p = back_out(prog(t, 0.05 + 0.12 * i, 0.45)) if big else 1.0
        size = 104 if big else 88
        size = min(size, size * 860 / max(1, text_w(ln, size)))
        col = YELLOW if i == 0 else WHITE
        text(img, ln, size, PW / 2, y + i * (size * 1.08), fill=col, scale=max(0.05, p), alpha=a, stroke=10,
             sfill=NAVY, rotate=-2)


def mini_hud(img, seg, t, gt):
    if "hh" not in seg:
        return
    k = ease_io(prog(t, 0, seg["dur"]))
    h = R.lerp(seg["hh"][0], seg["hh"][1], k)
    b = R.lerp(seg["bb"][0], seg["bb"][1], k)
    L.pill(img, seg["label"], 260, 1190, YELLOW, 1.0, size=46, path=L.FONT_BLACK)
    text(img, f"{int(round(h))} h WACH", 54, 560, 1190, fill=WHITE, stroke=7, sfill=NAVY)
    R.battery(img, 810, 1190, b, w=100, h=50, gt=gt)


def subtitles(img, toks, t, y=SUB_Y, size=80, maxw=840):
    if not toks:
        return
    chunks, cur = [], []
    for tk in toks:
        trial = cur + [tk]
        if cur and (len(trial) > 3 or text_w(" ".join(x["text"] for x in trial), size) > maxw):
            chunks.append(cur)
            cur = [tk]
        else:
            cur = trial
        if tk["text"][-1] in ".!?:":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    active = None
    for i, ch in enumerate(chunks):
        st = ch[0]["s"] - 0.05
        en = chunks[i + 1][0]["s"] - 0.05 if i + 1 < len(chunks) else ch[-1]["e"] + 0.5
        if st <= t < en:
            active = ch
            break
    if not active:
        return
    p = ease_out(prog(t, active[0]["s"] - 0.05, 0.12))
    ws = [x["text"] for x in active]
    curs = [tk["s"] - 0.03 <= t < tk["e"] + 0.05 for tk in active]
    widths = [text_w(w, size * (1.1 if c else 1.0)) + 14 for w, c in zip(ws, curs)]
    total = sum(widths) + 18 * (len(ws) - 1)
    x = PW / 2 - total / 2
    for tk, w, wd, c in zip(active, ws, widths, curs):
        col = YELLOW if c else WHITE
        text(img, w, size, x + wd / 2, y, fill=col, scale=(1.1 if c else 1.0) * (0.85 + 0.15 * p), alpha=p,
             stroke=9, sfill=(0, 0, 0))
        x += wd + 18


_thumb = None


def thumb():
    global _thumb
    if _thumb is None:
        _thumb = Image.open(os.path.join(HERE, "thumbnail_4k.png")).convert("RGBA").resize((900, 506), Image.LANCZOS)
    return _thumb


def render_frame(fi):
    gt = fi / FPS
    p = piece_at(gt)
    t = gt - p["start"]
    img = PBG.copy()
    spec = CUR
    L.brand(img, PW / 2, 250, gt, 1.15)
    if p["kind"] == "hook":
        sk, word, off = spec["preview"]
        seg = L.BY[sk]
        st = L.wt(seg, word) + off
        paste_panel(img, land_frame(seg, min(seg["dur"] - 0.05, st + t)), 0.9 + 0.1 * ease_out(prog(t, 0, 0.4)))
        headline(img, spec["head"], t, big=True)
        q = 1 + 0.12 * math.sin(gt * 7)
        text(img, "?", 150 * q, 900, 1170, fill=RED, stroke=10, sfill=NAVY, rotate=12)
    elif p["kind"] == "land":
        seg = p["seg"]
        paste_panel(img, land_frame(seg, t))
        headline(img, spec["head"], 10)
        mini_hud(img, seg, t, gt)
    else:
        a = ease_out(prog(t, 0, 0.4))
        sc = 0.92 + 0.08 * back_out(prog(t, 0, 0.5)) + 0.015 * math.sin(gt * 5)
        paste_panel(img, thumb(), sc)
        text(img, "GANZES VIDEO", 88, PW / 2, 430, fill=YELLOW, stroke=10, sfill=NAVY, alpha=a, rotate=-2)
        text(img, "AUF DEM KANAL", 74, PW / 2, 525, fill=WHITE, stroke=9, sfill=NAVY, alpha=a, rotate=-2)
        rb = back_out(prog(t, 0.6, 0.5))
        if rb > 0.03:
            L.rrect(img, (PW / 2 - 280 * rb, 1200 - 58 * rb, PW / 2 + 280 * rb, 1200 + 58 * rb), int(58 * rb),
                    (230, 30, 40, 255))
            text(img, "▶ JETZT ANSEHEN", 52 * rb, PW / 2, 1202, fill=WHITE)
    if p["kind"] != "cta" and gt > 4.0:
        L.pill(img, "GANZES VIDEO ▶ KANAL", PW / 2, 1480, WHITE, 0.9, size=30)
    subtitles(img, p["toks"], t)
    return img.convert("RGB")


def render_bytes(fi):
    return render_frame(fi).tobytes()


# ------------------------------------------------------------------ audio
def read_wav(path):
    with wave.open(path) as wf:
        return np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16) / 32768.0


def build_audio(name):
    master = read_wav(os.path.join(BUILD, "mix.wav"))
    n = int((TOTAL + 0.5) * SR)
    out = np.zeros(n)
    r = np.random.default_rng(3)

    def add(sig, t0, g=1.0):
        a = int(t0 * SR)
        b = min(n, a + len(sig))
        out[a:b] += sig[:b - a] * g
    for p in PIECES:
        if p["kind"] == "land":
            seg = p["seg"]
            a = int(seg["start"] * SR)
            sl = master[a:a + int(seg["dur"] * SR)].copy()
            f = int(0.03 * SR)
            sl[:f] *= np.linspace(0, 1, f)
            sl[-f:] *= np.linspace(1, 0, f)
            add(sl, p["start"])
        else:
            v = read_wav(p["wav"])
            add(v / (np.abs(v).max() + 1e-9) * 0.89, p["start"] + p["pre"])
            if p["kind"] == "hook":
                add(L._whoosh(r), p["start"], 0.10)
                add(L._thump(), p["start"] + 0.2, 0.16)
            else:
                add(L._whoosh(r), p["start"], 0.10)
                add(L._chime(), p["start"] + 0.3, 0.12)
                add(L._pop(), p["start"] + 0.6, 0.12)
    # soft pad under hook + CTA (the landscape slices already carry the music bed)
    tt = np.arange(n) / SR
    pad = sum(np.sin(2 * np.pi * f * tt) for f in (220.0, 261.63, 329.63)) * 0.010
    mask = np.zeros(n)
    for p in PIECES:
        if p["kind"] != "land":
            a, b = int(p["start"] * SR), int((p["start"] + p["dur"]) * SR)
            mask[a:b] = 1
    out += pad * np.convolve(mask, np.ones(2400) / 2400, mode="same")
    out = np.clip(out, -0.98, 0.98)
    path = os.path.join(BUILD, f"{name}.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((out[:int(TOTAL * SR)] * 32767).astype(np.int16).tobytes())
    return path


def loudness(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    vals = [ln for ln in r.splitlines() if ln.strip().startswith("I:")]
    return float(vals[-1].split()[1])


CUR = None


def init(name):
    global CUR, PBG
    CUR = SHORTS[name]
    PBG = portrait_bg()
    build(CUR)


def make(name):
    init(name)
    os.makedirs(OUT, exist_ok=True)
    audio = build_audio(name)
    nfr = int(math.ceil(TOTAL * FPS))
    tmp = os.path.join(BUILD, f"{name}_tmp.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{PW}x{PH}", "-r", str(FPS), "-i", "-", "-i", audio, "-c:v", "libx264",
                           "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                           "-ar", "48000", "-ac", "2", "-movflags", "+faststart", "-shortest", tmp],
                          stdin=subprocess.PIPE)
    with Pool(4, initializer=init, initargs=(name,)) as pool:
        for k0 in range(0, nfr, 48):
            for b in pool.map(render_bytes, range(k0, min(nfr, k0 + 48)), chunksize=4):
                ff.stdin.write(b)
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg failed")
    gain = -14.0 - loudness(tmp)
    out = os.path.join(OUT, f"{name}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:v", "copy", "-af",
                    f"volume={gain:.2f}dB,alimiter=limit=0.84:level=false", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-movflags", "+faststart", out], check=True)
    os.remove(tmp)
    print(f"wrote {out}  {TOTAL:.1f}s  {nfr} frames  loudness {loudness(out):.1f} LUFS")


def stills(name):
    init(name)
    qc = os.path.join(HERE, "qc_shorts")
    os.makedirs(qc, exist_ok=True)
    for p in PIECES:
        for f in (0.5,):
            gt = p["start"] + p["dur"] * f
            render_frame(int(gt * FPS)).save(os.path.join(qc, f"{name}_{gt:06.2f}.png"))
    print(name, round(TOTAL, 1))


if __name__ == "__main__":
    names = [a for a in ARGS if not a.startswith("--")] or list(SHORTS)
    for nm in names:
        if "--stills" in ARGS:
            stills(nm)
        else:
            make(nm)

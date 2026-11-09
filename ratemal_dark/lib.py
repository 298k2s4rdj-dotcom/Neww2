"""Shared toolkit for narrated "Rate mal, was passiert, wenn …" shorts in the dark stick-figure style.

Re-uses the drawing primitives of stickman/nine_to_five_v2/render.py (figure, Stage, Over, colours) and adds
an audio-driven timeline, word-synced subtitles, a brand pill and the compositing / encoding pipeline.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "stickman", "nine_to_five_v2"))
import render as S  # noqa: E402  (drawing primitives only; its main() is not run)

W, H, FPS, K = S.W, S.H, S.FPS, S.K
SR = 48000
GAP, HOLD = 0.18, 1.0
PUNCT = ".,:;!?…"
Stage, Over, figure, pose, walk = S.Stage, S.Over, S.figure, S.pose, S.walk
clamp, prog, eo, eio, bo, mix = S.clamp, S.prog, S.eo, S.eio, S.bo, S.mix
TXT, DIM, AMBER, CORAL, BLUE, BG, PROP, PROP2, LINE, NAVY = (S.TXT, S.DIM, S.AMBER, S.CORAL, S.BLUE, S.BG, S.PROP,
                                                            S.PROP2, S.LINE, S.NAVY)
TONE_COOL, TONE_WARM, TONE_OLD, TONE_BLUE, tone_mix = S.TONE_COOL, S.TONE_WARM, S.TONE_OLD, S.TONE_BLUE, S.tone_mix
INTER, MONO, MONO_XB, F = S.INTER, S.MONO, S.MONO_XB, S.F
FLOOR = S.FLOOR
PINK = (255, 120, 190)
GREEN = (110, 230, 150)

CFG = {}
SCENES = []


# ------------------------------------------------------------------ timeline from the voice-over
def strip(w):
    return w.strip(PUNCT)


def setup(here, out, scenes, tempo=1.0, sub_map=None, sfx=None):
    """scenes: list of draw functions f(t_local, sc, gt) -> (stage, overlay, zoom, focus)"""
    CFG.clear()
    CFG.update(here=here, out=out, fns=scenes, tempo=tempo, sub_map=sub_map or [], sfx=sfx or (lambda: []))
    raw = os.path.join(here, "audio_raw")
    build = os.path.join(here, "build")
    os.makedirs(build, exist_ok=True)
    SCENES.clear()
    t = 0.0
    n = len(scenes)
    for i in range(n):
        words = json.load(open(os.path.join(raw, f"w{i}.json")))["words"]
        words = [w for w in words if w.get("type") == "word" and "[" not in w["text"] and "]" not in w["text"]]
        end = words[-1]["end"] + 0.08
        wav = os.path.join(build, f"s{i}_{tempo:.3f}.wav")
        if not os.path.exists(wav):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(raw, f"s{i}.mp3"), "-af",
                            f"atrim=0:{end:.3f},atempo={tempo:.4f},afade=t=out:st={end / tempo - 0.05:.3f}:d=0.05",
                            "-ar", str(SR), "-ac", "1", wav], check=True)
        with wave.open(wav) as wf:
            alen = wf.getnframes() / wf.getframerate()
        dur = alen + (HOLD if i == n - 1 else GAP)
        ws = [dict(text=w["text"], s=w["start"] / tempo, e=w["end"] / tempo) for w in words]
        SCENES.append(dict(i=i, start=t, dur=dur, alen=alen, wav=wav, words=ws, toks=tokens(ws)))
        t += dur
    CFG["total"] = t
    CFG["nfr"] = int(math.ceil(t * FPS))


def tokens(ws):
    out, k = [], 0
    while k < len(ws):
        hit = None
        for pat, disp in CFG["sub_map"]:
            m = len(pat)
            if tuple(strip(w["text"]) for w in ws[k:k + m]) == pat:
                hit = (m, disp)
                break
        if hit:
            m, disp = hit
            tail = ws[k + m - 1]["text"]
            out.append(dict(text=disp + tail[len(tail.rstrip(PUNCT)):], s=ws[k]["s"], e=ws[k + m - 1]["e"]))
            k += m
        else:
            out.append(dict(ws[k]))
            k += 1
    return out


def wt(sc, word, n=1, edge="s"):
    c = 0
    for w in sc["words"]:
        if strip(w["text"]).lower() == word.lower():
            c += 1
            if c == n:
                return w[edge]
    raise KeyError(word)


# ------------------------------------------------------------------ overlay helpers
def subtitles(o, sc, t, y=1430):
    toks = sc["toks"]
    chunks, cur = [], []
    for tk in toks:
        trial = cur + [tk]
        wdt = F(66 * K, INTER).getlength(" ".join(x["text"] for x in trial)) / K
        if cur and (len(trial) > 3 or wdt > 820):
            chunks.append(cur)
            cur = [tk]
        else:
            cur = trial
        if tk["text"][-1] in ".!?:":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    act = None
    for i, ch in enumerate(chunks):
        st = ch[0]["s"] - 0.05
        en = chunks[i + 1][0]["s"] - 0.05 if i + 1 < len(chunks) else ch[-1]["e"] + 0.5
        if st <= t < en:
            act = ch
            break
    if not act:
        return
    p = eo(prog(t, act[0]["s"] - 0.05, 0.14))
    size = 66
    f = F(size * K, INTER)
    words = [x["text"] for x in act]
    widths = [f.getlength(w) / K for w in words]
    gap = 22
    total = sum(widths) + gap * (len(words) - 1)
    x = 540 - total / 2
    for tk, w, wd in zip(act, words, widths):
        cur = tk["s"] - 0.03 <= t < tk["e"] + 0.06
        col = AMBER if cur else TXT
        yy = y + (1 - p) * 14 - (6 if cur else 0)
        o.d.text(((x + wd / 2) * K, yy * K), w, font=f, fill=col + (int(255 * p),), anchor="mm",
                 stroke_width=int(7 * K), stroke_fill=(0, 0, 0, int(220 * p)))
        x += wd + gap


def brand(o, t, y=190, a=1.0):
    p = bo(prog(t, 0.0, 0.45)) * a
    if p <= 0.03:
        return
    w, h = 190 * p, 40 * p
    o.d.rounded_rectangle(((540 - w) * K, (y - h) * K, (540 + w) * K, (y + h) * K), int(h * K),
                          fill=AMBER + (255,))
    o.d.text((540 * K, (y + 1) * K), "RATE MAL?", font=F(46 * p * K, MONO_XB), fill=(20, 16, 10, 255), anchor="mm")


def chip(o, s, x, y, col, a=1.0, size=34):
    if a <= 0.01:
        return
    f = F(size * K, MONO_XB)
    w = f.getlength(s) / K + 36
    h = size * 0.85
    o.d.rounded_rectangle(((x - w / 2) * K, (y - h) * K, (x + w / 2) * K, (y + h) * K), int(14 * K),
                          fill=(14, 14, 18, int(240 * a)), outline=col + (int(255 * a),), width=int(3 * K))
    o.d.text((x * K, y * K), s, font=f, fill=col + (int(255 * a),), anchor="mm")


def question(o, text, t, t_in, y=300, size=64, col=TXT):
    p = prog(t, t_in, 0.35)
    if p > 0:
        o.text(text, size, 540, y + 16 * (1 - eo(p)), col, a=eo(p), sc=0.92 + 0.08 * bo(p))


def outro_cta(o, t, gt, line="SCHREIB'S IN DIE KOMMENTARE", t_in=0.0):
    a = eo(prog(t, t_in, 0.4))
    if a <= 0.01:
        return
    o.text(line, 36, 540, 1270, AMBER, path=MONO_XB, a=a)
    ax = 860 + 16 * math.sin(gt * 8)
    o.d.line(((ax - 90) * K, 1330 * K, ax * K, 1330 * K), fill=AMBER + (int(255 * a),), width=10 * K)
    o.d.polygon([((ax + 30) * K, 1330 * K), ((ax - 4) * K, 1307 * K), ((ax - 4) * K, 1353 * K)],
                fill=AMBER + (int(255 * a),))


# ------------------------------------------------------------------ compositing
_yy, _xx = np.mgrid[0:H, 0:W]
VIGN = S.VIGN


def compose(st, o, z, focus, extra=None, reflect=True):
    fx, fy = focus
    cw, ch = W * K / z, H * K / z
    x0 = clamp(fx * K - cw / 2, 0, W * K - cw)
    y0 = clamp(fy * K - ch / 2, 0, H * K - ch)
    img = st.im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    arr = np.asarray(img).astype(np.float32)
    fl = int((FLOOR * K - y0) / (ch / H))
    depth = 230
    if reflect and 0 < fl < H - depth:
        src = arr[fl - depth:fl][::-1]
        fade = np.linspace(0.2, 0.0, depth)[:, None, None]
        arr[fl + 4:fl + 4 + depth] = arr[fl + 4:fl + 4 + depth] * (1 - fade) + src * fade
    if extra:
        arr = extra(arr, x0, y0, ch / H)
    arr *= VIGN[..., None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    ov = o.im.resize((W, H), Image.LANCZOS)
    img.paste(ov, (0, 0), ov)
    return img


def frame(fi):
    gt = fi / FPS
    idx = 0
    for i, sc in enumerate(SCENES):
        if gt >= sc["start"]:
            idx = i
    sc = SCENES[idx]
    t = gt - sc["start"]
    res = CFG["fns"][idx](t, sc, gt)
    st, o, z, focus = res[:4]
    extra = res[4] if len(res) > 4 else None
    subtitles(o, sc, t)
    img = compose(st, o, z, focus, extra)
    for c in [s["start"] for s in SCENES[1:]]:
        dt = gt - c
        if -0.1 <= dt < 0.1:
            img = Image.blend(img, Image.new("RGB", img.size, BG), 0.8 * (1 - abs(dt) / 0.1))
    return img


def frame_bytes(fi):
    return frame(fi).tobytes()


# ------------------------------------------------------------------ audio
def build_audio():
    total = CFG["total"]
    n = int((total + 0.5) * SR)
    tt = np.arange(n) / SR
    voice = np.zeros(n)
    for sc in SCENES:
        with wave.open(sc["wav"]) as wf:
            d = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16) / 32768.0
        a = int(sc["start"] * SR)
        voice[a:a + len(d)] += d[:n - a]
    voice = voice / (np.abs(voice).max() + 1e-9) * 0.9
    bed = np.zeros(n)
    chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7), (164.8, 207.7, 246.9)]
    seg = 3.2
    for i in range(int(total / seg) + 1):
        a, b = int(i * seg * SR), min(n, int((i + 1) * seg * SR) + int(0.4 * SR))
        x = tt[a:b] - tt[a]
        s = sum(np.sin(2 * np.pi * f * x) + 0.2 * np.sin(2 * np.pi * f * 2.003 * x) for f in chords[i % 4])
        bed[a:b] += s * np.minimum(1, x / 0.5) * np.exp(-np.maximum(0, x - seg) * 5)
    bed *= 0.012 * np.clip(tt / 1.0, 0, 1) * np.clip((total - tt) / 1.0, 0, 1)
    sfx = np.zeros(n)
    r = np.random.default_rng(3)

    def add(sig, t0, g):
        a = int(max(0, t0) * SR)
        if a < n:
            b = min(n, a + len(sig))
            sfx[a:b] += sig[:b - a] * g

    for sc in SCENES[1:]:
        m = int(0.32 * SR)
        y = np.convolve(r.standard_normal(m), np.ones(40) / 40, "same") * np.sin(np.linspace(0, np.pi, m)) ** 2
        add(y / (np.abs(y).max() + 1e-9), sc["start"] - 0.14, 0.06)
    for t0, kind, g in CFG["sfx"]():
        add(SFX[kind](r), t0, g)
    mix_ = np.clip(voice + bed + sfx, -0.98, 0.98)
    path = os.path.join(CFG["here"], "build", "mix.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((mix_[:int(total * SR)] * 32767).astype(np.int16).tobytes())
    return path


def _env(m, atk=0.004, dec=8.0):
    x = np.arange(m) / SR
    return np.minimum(1, x / atk) * np.exp(-x * dec)


def _tone(f, d, dec=6.0):
    m = int(d * SR)
    x = np.arange(m) / SR
    return np.sin(2 * np.pi * f * x) * _env(m, dec=dec)


SFX = {
    "pop": lambda r: _tone(900, 0.12, 30) + 0.5 * r.standard_normal(int(0.12 * SR)) * _env(int(0.12 * SR), dec=60),
    "gulp": lambda r: np.sin(2 * np.pi * np.cumsum(np.linspace(420, 140, int(0.3 * SR))) / SR) * _env(int(0.3 * SR),
                                                                                                      dec=9),
    "tick": lambda r: _tone(2500, 0.03, 180),
    "hit": lambda r: (_tone(48, 1.0, 3) + 0.3 * r.standard_normal(int(1.0 * SR)) * _env(int(1.0 * SR), dec=25)),
    "ding": lambda r: (_tone(1046, 1.0, 4) + _tone(1318, 1.0, 4.5)) * 0.5,
    "alarm": lambda r: np.sign(np.sin(2 * np.pi * 880 * np.arange(int(0.18 * SR)) / SR)) * _env(int(0.18 * SR),
                                                                                             dec=6),
    "heart": lambda r: _tone(55, 0.22, 16),
    "breath": lambda r: np.convolve(r.standard_normal(int(0.9 * SR)), np.ones(60) / 60, "same") *
    np.sin(np.linspace(0, np.pi, int(0.9 * SR))),
    "splash": lambda r: np.convolve(r.standard_normal(int(0.7 * SR)), np.ones(12) / 12, "same") *
    _env(int(0.7 * SR), atk=0.01, dec=5),
}


def main():
    here = CFG["here"]
    if "--stills" in sys.argv:
        qc = os.path.join(here, "qc")
        os.makedirs(qc, exist_ok=True)
        for f in os.listdir(qc):
            os.remove(os.path.join(qc, f))
        args = [float(a) for a in sys.argv[sys.argv.index("--stills") + 1:]]
        times = args
        if not times:
            for sc in SCENES:
                for f in (0.15, 0.5, 0.85):
                    times.append(sc["start"] + sc["dur"] * f)
        for t in times:
            frame(int(t * FPS)).save(os.path.join(qc, f"f_{t:06.2f}.png"))
        print("stills", len(times), "total", round(CFG["total"], 2))
        return
    wav = build_audio()
    out = os.path.join(here, CFG["out"])
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                           f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium",
                           "-crf", "18", "-pix_fmt", "yuv420p", "-af",
                           "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                           "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, b in enumerate(pool.imap(frame_bytes, range(CFG["nfr"]), chunksize=4)):
            ff.stdin.write(b)
    ff.stdin.close()
    ff.wait()
    print("wrote", out, round(CFG["total"], 2))

#!/usr/bin/env python3
"""Animated German TikTok comparison video: "Erde vs. Sonne".

Everything visual is drawn procedurally here (Pillow + NumPy) and encoded
with ffmpeg. The voice comes from ElevenLabs (one file per scene in
audio_raw/), word timings from ElevenLabs Scribe (audio_raw/w*.json).
Sound effects are synthesised in this script (no third-party audio).

Usage:
  python3 render.py                 # full render -> erde_vs_sonne.mp4
  python3 render.py --stills        # QC stills -> qc/
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
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "audio_raw")
BUILD = os.path.join(HERE, "build")
os.makedirs(BUILD, exist_ok=True)

W, H, FPS = 1080, 1920, 30
TEMPO = 1.2          # voice speed-up (pitch preserved, ffmpeg atempo)
GAP = 0.10           # pause between scenes
HOLD = 0.9           # hold after the last line
XF = 0.25            # cross-fade between scenes
SR = 48000

# TikTok safe zone: top 150, bottom 400, right 140 stay free of content
SAFE_T, SAFE_B, SAFE_R = 150, H - 400, W - 140
SPLIT = 540                       # exakte 50:50-Teilung des Bildes
CXL, CXR = 290, 740               # Panel-Mitten (rechts bleibt x > 940 frei)
VIS_Y = 700                       # centre of the main visual
NUM_Y = 1085                      # counters
SUB_Y = 1395                      # subtitles

C_EARTH = (64, 196, 255)
C_SUN = (255, 176, 0)
C_HI = (255, 226, 60)
WHITE = (255, 255, 255)

FONT_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
_fonts = {}


def F(size, path=FONT_BLACK):
    key = (int(size), path)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, max(4, int(size)))
    return _fonts[key]


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def back_out(x, s=1.9):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def prog(t, t0, d):
    return clamp((t - t0) / d) if d > 0 else float(t >= t0)


def fmt_int(n):
    return f"{int(round(n)):,}".replace(",", ".")


def fmt_dec(x, nd=1):
    return f"{x:.{nd}f}".replace(".", ",")


# ---------------------------------------------------------------- scenes / audio
SCENES = [
    dict(key="hook"), dict(key="breite"), dict(key="hitze"),
    dict(key="schwerkraft"), dict(key="masse"), dict(key="finale"),
    dict(key="outro"),
]

# spoken words -> subtitle display (numbers as digits, words unchanged)
SUB_MAP = [
    (("eins", "Komma", "vier"), "1,4"), (("eins", "Komma", "drei"), "1,3"),
    (("neunundneunzig", "Komma", "acht"), "99,8"),
    (("dreizehntausend",), "13.000"), (("Hundertneunmal",), "109-mal"),
    (("fünfzehn",), "15"), (("fünftausendfünfhundert",), "5.500"),
    (("achtundzwanzigmal",), "28-mal"), (("siebzig",), "70"),
    (("zwei",), "2"), (("dreihundertdreiunddreißigtausendmal",), "333.000-mal"),
    (("eins",), "1"), (("drei",), "3"), (("vier",), "4"),
]
PUNCT = ".,:;!?"


def strip(w):
    return w.strip(PUNCT)


def build_timeline():
    t = 0.0
    for i, sc in enumerate(SCENES):
        raw = os.path.join(RAW, f"s{i}.mp3")
        words = json.load(open(os.path.join(RAW, f"w{i}.json")))["words"]
        words = [w for w in words if w.get("type") == "word"]
        end = words[-1]["end"] + 0.06
        out = os.path.join(BUILD, f"s{i}.wav")
        if not os.path.exists(out):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                            f"atrim=0:{end:.3f},atempo={TEMPO},afade=t=out:st={end / TEMPO - 0.04:.3f}:d=0.04",
                            "-ar", str(SR), "-ac", "1", out], check=True)
        with wave.open(out) as wf:
            alen = wf.getnframes() / wf.getframerate()
        sc["wav"] = out
        sc["alen"] = alen
        sc["start"] = t
        sc["dur"] = alen + (HOLD if i == len(SCENES) - 1 else GAP)
        sc["words"] = [dict(text=w["text"], s=w["start"] / TEMPO, e=w["end"] / TEMPO) for w in words]
        # subtitle tokens (merge spoken number groups)
        toks, k, ws = [], 0, sc["words"]
        while k < len(ws):
            hit = None
            for pat, disp in SUB_MAP:
                n = len(pat)
                if tuple(strip(w["text"]) for w in ws[k:k + n]) == pat:
                    hit = (n, disp)
                    break
            if hit:
                n, disp = hit
                tail = ws[k + n - 1]["text"]
                p = tail[len(strip(tail)):] if tail != strip(tail) else ""
                toks.append(dict(text=disp + p, s=ws[k]["s"], e=ws[k + n - 1]["e"]))
                k += n
            else:
                toks.append(dict(ws[k]))
                k += 1
        sc["toks"] = toks
        t += sc["dur"]
    return t


TOTAL = build_timeline()
NFRAMES = int(math.ceil(TOTAL * FPS))


def wt(sc, word, n=1, edge="s"):
    """local time of the n-th occurrence of a spoken word"""
    c = 0
    for w in sc["words"]:
        if strip(w["text"]).lower() == word.lower():
            c += 1
            if c == n:
                return w[edge]
    raise KeyError(word)


S = SCENES
# score events (global time) -> sun gets a point
SCORE_T = [
    S[1]["start"] + wt(S[1], "Hundertneunmal"),
    S[2]["start"] + wt(S[2], "Grad", 2),
    S[3]["start"] + wt(S[3], "Tonnen"),
    S[4]["start"] + wt(S[4], "Prozent"),
    S[5]["start"] + wt(S[5], "Sieger"),
]

# ---------------------------------------------------------------- sprites
rng = np.random.default_rng(7)


def make_earth_texture(w=1024, h=512):
    lon = np.linspace(0, 2 * np.pi, w, endpoint=False)[None, :]
    lat = np.linspace(-np.pi / 2, np.pi / 2, h)[:, None]
    f = np.zeros((h, w))
    r = np.random.default_rng(3)
    for _ in range(16):
        n = r.integers(1, 6)
        m = r.uniform(1, 5)
        f += r.uniform(0.4, 1.0) / n * np.sin(n * lon + r.uniform(0, 6.3)) * np.cos(m * lat + r.uniform(0, 6.3))
    f = (f - f.mean()) / f.std()
    land = f > 0.45
    tex = np.zeros((h, w, 3))
    ocean = np.array([30, 110, 215]) / 255
    deep = np.array([18, 70, 170]) / 255
    tex[:] = deep + (ocean - deep) * np.clip(f + 1.5, 0, 2)[..., None] / 2
    g1 = np.array([60, 170, 80]) / 255
    g2 = np.array([150, 140, 70]) / 255
    mix = np.clip((f - 0.45) / 1.2, 0, 1)[..., None]
    tex = np.where(land[..., None], g1 * (1 - mix) + g2 * mix, tex)
    ice = np.abs(lat) > np.radians(68) + 0.05 * np.sin(5 * lon)
    tex = np.where(ice[..., None], np.array([0.93, 0.96, 1.0]), tex)
    # clouds
    c = np.zeros((h, w))
    for _ in range(10):
        n = r.integers(2, 9)
        c += np.sin(n * lon + r.uniform(0, 6.3)) * np.cos(r.uniform(2, 8) * lat + r.uniform(0, 6.3))
    c = np.clip((c / c.std() - 1.1) * 0.6, 0, 0.7)[..., None]
    tex = tex * (1 - c) + c
    return tex


EARTH_TEX = make_earth_texture()


def earth_sprite(size, rot):
    size = max(2, int(size))
    if size < 14:
        im = Image.new("RGBA", (size + 2, size + 2))
        ImageDraw.Draw(im).ellipse((1, 1, size, size), fill=(70, 160, 255, 255))
        return im
    th, tw = EARTH_TEX.shape[:2]
    pad = int(size * 0.12) + 2
    n = size + 2 * pad
    c = (n - 1) / 2
    y, x = np.mgrid[0:n, 0:n]
    x = (x - c) / (size / 2)
    y = (y - c) / (size / 2)
    rr = np.sqrt(x * x + y * y)
    inside = rr <= 1
    z = np.sqrt(np.clip(1 - rr * rr, 0, 1))
    lat = np.arcsin(np.clip(-y, -1, 1))
    lon = (np.arctan2(x, z) + rot) % (2 * np.pi)
    ti = np.clip(((lat + np.pi / 2) / np.pi * (th - 1)).astype(int), 0, th - 1)
    tj = np.clip((lon / (2 * np.pi) * tw).astype(int), 0, tw - 1)
    col = EARTH_TEX[th - 1 - ti, tj]
    L = np.array([-0.55, -0.45, 0.7])
    L = L / np.linalg.norm(L)
    diff = np.clip(x * L[0] + y * L[1] + z * L[2], 0, 1)
    shade = 0.28 + 0.85 * diff
    col = col * shade[..., None]
    rim = np.clip((1 - z) ** 2.5, 0, 1)[..., None]
    col = col * (1 - 0.5 * rim) + np.array([0.45, 0.8, 1.0]) * 0.5 * rim
    alpha = np.clip((1 - rr) * size / 2 + 0.5, 0, 1)
    # atmosphere glow
    glow = np.clip(1 - (rr - 1) / 0.12, 0, 1) * (rr > 1) * 0.55
    out = np.zeros((n, n, 4))
    out[..., :3] = np.where(inside[..., None], col, np.array([0.4, 0.75, 1.0]))
    out[..., 3] = np.where(inside, alpha, glow ** 2)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), "RGBA")


def make_sun(core=900):
    n = int(core * 1.6)
    c = (n - 1) / 2
    y, x = np.mgrid[0:n, 0:n]
    r = np.sqrt((x - c) ** 2 + (y - c) ** 2) / (core / 2)
    z = np.sqrt(np.clip(1 - r * r, 0, 1))
    noise = Image.fromarray((np.random.default_rng(5).random((n // 6, n // 6)) * 255).astype(np.uint8))
    noise = noise.resize((n, n), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    g = np.asarray(noise) / 255.0
    noise2 = Image.fromarray((np.random.default_rng(9).random((n // 30, n // 30)) * 255).astype(np.uint8))
    g2 = np.asarray(noise2.resize((n, n), Image.BICUBIC)) / 255.0
    inner = np.array([1.0, 0.9, 0.45])
    mid = np.array([1.0, 0.62, 0.06])
    edge = np.array([0.95, 0.35, 0.02])
    mu = z
    t = np.clip(1 - mu, 0, 1)[..., None]
    col = inner * (1 - t) ** 2 + mid * 2 * t * (1 - t) + edge * t ** 2
    col = col * (0.86 + 0.14 * g[..., None]) * (0.92 + 0.1 * g2[..., None])
    col = col * (0.72 + 0.28 * mu[..., None])
    a_core = np.clip((1 - r) * core / 2 + 0.5, 0, 1)
    glow = np.exp(-np.clip(r - 1, 0, None) / 0.12) * 0.85 + np.exp(-np.clip(r - 1, 0, None) / 0.35) * 0.35
    glow = np.where(r > 1, glow, 0) * np.clip((1.58 - r) / 0.4, 0, 1) ** 2
    gcol = np.array([1.0, 0.55, 0.08])
    out = np.zeros((n, n, 4))
    out[..., :3] = np.where((r <= 1)[..., None], col, gcol)
    out[..., 3] = np.where(r <= 1, a_core, np.clip(glow, 0, 1))
    out[..., 3] = np.maximum(out[..., 3], np.where(r <= 1, a_core, 0))
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), "RGBA")


SUN_BASE = make_sun(900)
SUN_RATIO = SUN_BASE.size[0] / 900


def sun_sprite(core, t):
    core = max(4, int(core))
    im = SUN_BASE.rotate(t * 6 % 360, resample=Image.BILINEAR)
    n = int(core * SUN_RATIO)
    return im.resize((n, n), Image.BILINEAR)


def paste_c(img, sprite, cx, cy, alpha=1.0):
    if alpha <= 0.01:
        return
    if alpha < 0.999:
        a = sprite.getchannel("A").point(lambda v: int(v * alpha))
        sprite = sprite.copy()
        sprite.putalpha(a)
    img.paste(sprite, (int(cx - sprite.size[0] / 2), int(cy - sprite.size[1] / 2)), sprite)


# ---------------------------------------------------------------- background
def make_bg():
    y = np.linspace(0, 1, H)[:, None, None]
    left = np.array([6, 18, 52]) * (1 - y) + np.array([10, 52, 125]) * y
    right = np.array([60, 8, 4]) * (1 - y) + np.array([150, 52, 0]) * y
    bg = np.zeros((H, W, 3))
    xs = np.arange(W)[None, :, None]
    m = np.clip((xs - SPLIT + 3) / 6, 0, 1)
    bg = left * (1 - m) + right * m
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.35 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
    bg = bg * v[..., None]
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB")


BG = make_bg()
_r = random.Random(11)
STARS = [(_r.uniform(0, W), _r.uniform(0, H), _r.uniform(0.8, 2.6), _r.uniform(0, 6.3), _r.uniform(0.5, 2.0))
         for _ in range(170)]


def draw_bg(img, t):
    d = ImageDraw.Draw(img)
    for x, y, s, ph, sp in STARS:
        b = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * sp * 2 + ph))
        v = int(255 * b)
        x2 = (x + t * 6 * s) % W
        d.ellipse((x2 - s, y - s, x2 + s, y + s), fill=(v, v, min(255, v + 20)))


# ---------------------------------------------------------------- text helpers
def text(img, s, size, cx, cy, fill=WHITE, scale=1.0, alpha=1.0, stroke=0, sfill=(0, 0, 0),
         path=FONT_BLACK, rotate=0.0, anchor="mm"):
    if alpha <= 0.01 or scale <= 0.02:
        return (0, 0)
    font = F(size * scale, path)
    sw = int(round(stroke * scale))
    bb = font.getbbox(s, stroke_width=sw)
    w, h = bb[2] - bb[0] + 8, bb[3] - bb[1] + 8
    layer = Image.new("RGBA", (w, h))
    ImageDraw.Draw(layer).text((4 - bb[0], 4 - bb[1]), s, font=font, fill=fill + (255,),
                               stroke_width=sw, stroke_fill=sfill + (255,))
    if rotate:
        layer = layer.rotate(rotate, resample=Image.BICUBIC, expand=True)
        w, h = layer.size
    if alpha < 0.999:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    if anchor == "mm":
        x, y = cx - w / 2, cy - h / 2
    elif anchor == "lm":
        x, y = cx, cy - h / 2
    else:
        x, y = cx - w, cy - h / 2
    img.paste(layer, (int(x), int(y)), layer)
    return (w, h)


def rrect_layer(img, box, radius, fill, outline=None, width=0):
    x0, y0, x1, y1 = [int(v) for v in box]
    layer = Image.new("RGBA", (x1 - x0, y1 - y0))
    ImageDraw.Draw(layer).rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), radius, fill=fill,
                                            outline=outline, width=width)
    img.paste(layer, (x0, y0), layer)


def text_w(s, size, path=FONT_BLACK):
    bb = F(size, path).getbbox(s)
    return bb[2] - bb[0]


# ---------------------------------------------------------------- common UI
def draw_header(img, gt, title, t, show_score=True, title_a=1.0):
    if show_score:
        score = sum(1 for st in SCORE_T if gt >= st)
        pop = 1.0
        for st in SCORE_T:
            if 0 <= gt - st < 0.45:
                pop = 1 + 0.6 * (1 - ease_out((gt - st) / 0.45))
        rrect_layer(img, (SPLIT - 250, 168, SPLIT + 250, 238), 35, (0, 0, 0, 150),
                    outline=(255, 255, 255, 60), width=2)
        text(img, "ERDE", 34, SPLIT - 160, 203, fill=C_EARTH)
        text(img, "SONNE", 34, SPLIT + 150, 203, fill=C_SUN)
        text(img, "0", 46, SPLIT - 50, 203)
        text(img, ":", 46, SPLIT, 200)
        text(img, str(score), 46, SPLIT + 50, 203, scale=pop, fill=C_HI if pop > 1.01 else WHITE)
    if title:
        k = ease_out(prog(t, 0.0, 0.35))
        sc = 1.5 - 0.5 * back_out(prog(t, 0.0, 0.4))
        text(img, title, 62, SPLIT, 300, scale=sc, alpha=k * title_a, stroke=5, sfill=(20, 10, 40))


def panel_labels(img, t, a=1.0):
    k = ease_out(prog(t, 0.05, 0.4)) * a
    text(img, "ERDE", 58, CXL - (1 - k) * 120, 395, fill=C_EARTH, alpha=k, stroke=4, sfill=(0, 20, 50))
    text(img, "SONNE", 58, CXR + (1 - k) * 120, 395, fill=C_SUN, alpha=k, stroke=4, sfill=(50, 10, 0))


def vs_badge(img, t, a=1.0, y=VIS_Y):
    if a <= 0:
        return
    p = 1 + 0.06 * math.sin(t * 6)
    r = int(52 * p)
    layer = Image.new("RGBA", (2 * r + 30, 2 * r + 30))
    d = ImageDraw.Draw(layer)
    d.ellipse((15, 15, 15 + 2 * r, 15 + 2 * r), fill=(255, 255, 255, int(235 * a)),
              outline=(255, 226, 60, int(255 * a)), width=6)
    img.paste(layer, (SPLIT - r - 15, y - r - 15), layer)
    text(img, "VS", 46 * p, SPLIT, y + 1, fill=(30, 20, 60), alpha=a)


def counter(img, cx, val, unit, color, a=1.0, size=70, y=NUM_Y):
    if a <= 0:
        return
    text(img, val, size, cx, y, alpha=a, stroke=6, sfill=(0, 0, 0))
    if unit:
        text(img, unit, 40, cx, y + 70, fill=color, alpha=a, stroke=4, sfill=(0, 0, 0), path=FONT_XB)


def stamp(img, s, t, t0, cx=SPLIT, cy=VIS_Y, size=150, rot=-8, hold=99.0):
    if t < t0:
        return
    p = prog(t, t0, 0.35)
    q = ease_io(prog(t, t0 + hold, 0.35))
    sc = (2.4 - 1.4 * back_out(p, 2.4)) * (1 - 0.6 * q)
    text(img, s, size, cx, cy, fill=C_HI, scale=sc, alpha=ease_out(p * 2) * (1 - q), stroke=12,
         sfill=(170, 20, 0), rotate=rot)


def burst(img, cx, cy, t, t0, color=C_HI, n=16, rad=260):
    p = prog(t, t0, 0.6)
    if p <= 0 or p >= 1:
        return
    d = ImageDraw.Draw(img)
    e = ease_out(p)
    for i in range(n):
        a = i / n * 2 * math.pi + 0.3
        r0, r1 = rad * (0.35 + 0.6 * e), rad * (0.5 + 0.75 * e)
        wdt = max(1, int(10 * (1 - p)))
        d.line((cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
               fill=color, width=wdt)


def subtitles(img, sc, t):
    toks = sc["toks"]
    # chunk greedily: max 3 tokens, max width, break after sentence punctuation
    chunks, cur = [], []
    for tk in toks:
        trial = cur + [tk]
        wdt = text_w(" ".join(x["text"] for x in trial), 74)
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
    active = None
    for i, ch in enumerate(chunks):
        st = ch[0]["s"] - 0.05
        en = chunks[i + 1][0]["s"] - 0.05 if i + 1 < len(chunks) else ch[-1]["e"] + 0.6
        if st <= t < en:
            active = ch
            break
    if not active:
        return
    p = ease_out(prog(t, active[0]["s"] - 0.05, 0.12))
    size = 74
    words = [x["text"] for x in active]
    curs = [tk["s"] - 0.03 <= t < tk["e"] + 0.05 for tk in active]
    scales = [(1.1 if c else 1.0) for c in curs]
    widths = [text_w(w, size * k) + 16 for w, k in zip(words, scales)]
    space = 20
    total = sum(widths) + space * (len(words) - 1)
    x = SPLIT - total / 2
    for tk, wtxt, wd, cur, k in zip(active, words, widths, curs, scales):
        on = tk["s"] - 0.03 <= t
        col = C_HI if cur else (WHITE if on else (215, 215, 225))
        text(img, wtxt, size, x + wd / 2, SUB_Y, fill=col, scale=k * (0.85 + 0.15 * p), alpha=p, stroke=8,
             sfill=(0, 0, 0))
        x += wd + space


# ---------------------------------------------------------------- scenes
def sc_hook(img, sc, t, gt):
    title_p = back_out(prog(t, 0.0, 0.45))
    text(img, "ERDE", 96, CXL, 300, fill=C_EARTH, scale=title_p, stroke=6, sfill=(0, 20, 50))
    text(img, "SONNE", 96, CXR, 300, fill=C_SUN, scale=back_out(prog(t, 0.12, 0.45)), stroke=6,
         sfill=(50, 10, 0))
    ex = CXL - 400 * (1 - ease_out(prog(t, 0.0, 0.5)))
    paste_c(img, earth_sprite(230, gt * 0.6), ex, VIS_Y)
    s = 340 * ease_out(prog(t, 0.1, 0.6)) * (1 + 0.03 * math.sin(gt * 5))
    paste_c(img, sun_sprite(s, gt), CXR + 15, VIS_Y)
    vs_badge(img, gt, ease_out(prog(t, 0.3, 0.3)))
    # slot-machine counter: how many Earths?
    counter(img, CXL, "1", "Erde", C_EARTH, a=ease_out(prog(t, 0.3, 0.3)))
    r = random.Random(int(gt * FPS))
    digits = "".join(str(r.randint(0, 9)) for _ in range(7))
    roll = f"{digits[0]}.{digits[1:4]}.{digits[4:7]}" if t < sc["alen"] - 0.45 else "?.???.???"
    counter(img, CXR, roll, "Erden?", C_SUN, a=ease_out(prog(t, 0.45, 0.3)))
    qp = 1 + 0.12 * math.sin(gt * 10)
    text(img, "?", 150, CXR + 15, VIS_Y, fill=WHITE, scale=qp * ease_out(prog(t, wt(sc, "Sonne"), 0.3)),
         stroke=8, sfill=(120, 30, 0))


def sc_breite(img, sc, t, gt):
    draw_header(img, gt, "RUNDE 1 · BREITE", t)
    panel_labels(img, t)
    t_e, t_s, t_x = wt(sc, "Erde"), wt(sc, "Sonne"), wt(sc, "Hundertneunmal")
    g = ease_io(prog(t, t_s, 1.4))
    sun_core = 250 + (450 - 250) * g
    earth_size = 250 + (450 / 109 - 250) * g
    # earth: shrinks to true scale, with a magnifier ring
    paste_c(img, earth_sprite(earth_size, gt * 0.6), CXL, VIS_Y)
    if g > 0.85:
        a = prog(g, 0.85, 0.15)
        d = ImageDraw.Draw(img)
        rr = 26 + 6 * math.sin(gt * 6)
        d.ellipse((CXL - rr, VIS_Y - rr, CXL + rr, VIS_Y + rr), outline=C_EARTH + (int(255 * a),), width=4)
        text(img, "so klein!", 40, CXL, VIS_Y + 80, fill=C_EARTH, alpha=a, stroke=4, path=FONT_XB)
    paste_c(img, sun_sprite(sun_core, gt), CXR, VIS_Y)
    # diameter line through the earth while the number counts
    pe = prog(t, t_e, 1.0)
    if 0 < pe and g < 0.3:
        d = ImageDraw.Draw(img)
        half = earth_size / 2 * ease_out(pe)
        d.line((CXL - half, VIS_Y, CXL + half, VIS_Y), fill=WHITE, width=5)
    ps = prog(t, t_s, 1.0)
    if 0 < ps:
        d = ImageDraw.Draw(img)
        half = sun_core / 2 * ease_out(ps)
        d.line((CXR - half, VIS_Y, CXR + half, VIS_Y), fill=WHITE, width=5)
    vs_badge(img, gt, 1 - prog(t, t_s, 0.4))
    a_e = ease_out(prog(t, t_e, 0.3))
    counter(img, CXL, fmt_int(12742 * ease_out(prog(t, t_e + 0.1, 1.3))), "km Durchmesser", C_EARTH, a_e)
    a_s = ease_out(prog(t, t_s, 0.3))
    counter(img, CXR, fmt_int(1391400 * ease_out(prog(t, t_s + 0.1, 1.5))), "km Durchmesser", C_SUN, a_s)
    burst(img, SPLIT, VIS_Y, t, t_x)
    stamp(img, "109×", t, t_x)


def thermo(img, cx, frac, color, t, label_icon):
    top, bot = 470, 940
    d = ImageDraw.Draw(img)
    w = 70
    rrect_layer(img, (cx - w / 2, top, cx + w / 2, bot), 35, (255, 255, 255, 40), outline=(255, 255, 255, 180),
                width=4)
    # ticks
    for i in range(7):
        y = bot - 40 - i * (bot - top - 70) / 6
        d.line((cx + w / 2 + 6, y, cx + w / 2 + 26, y), fill=(255, 255, 255), width=3)
        if i in (0, 6):
            text(img, ("0" if i == 0 else "6.000") + " °C", 26, cx + w / 2 + 34, y, fill=(230, 230, 240),
                 path=FONT_XB, anchor="lm")
    h = (bot - top - 70) * clamp(frac, 0, 1.05)
    fill_top = bot - 40 - h
    rrect_layer(img, (cx - w / 2 + 12, fill_top - 6, cx + w / 2 - 12, bot - 20), 22, color + (255,))
    # bulb
    r = 62
    d.ellipse((cx - r, bot - 20 - r + 30, cx + r, bot - 20 + r + 30), fill=color, outline=WHITE, width=5)
    label_icon(cx, bot + 10)
    return fill_top


def sc_hitze(img, sc, t, gt):
    draw_header(img, gt, "RUNDE 2 · HITZE", t)
    panel_labels(img, t)
    t_e, t_15 = wt(sc, "Erde"), wt(sc, "fünfzehn")
    t_s, t_55 = wt(sc, "Oberfläche"), wt(sc, "fünftausendfünfhundert")
    fe = 15 / 6000 * ease_out(prog(t, t_15, 0.8))
    fs = 5500 / 6000 * ease_out(prog(t, t_55, 1.3))
    thermo(img, CXL - 30, fe + 0.01, (60, 170, 255), t, lambda x, y: paste_c(img, earth_sprite(90, gt), x, y))
    top = thermo(img, CXR - 30, fs + 0.01, (255, 120, 0), t,
                 lambda x, y: paste_c(img, sun_sprite(84, gt), x, y))
    # flames / heat particles rising from the sun thermometer
    if fs > 0.3:
        d = ImageDraw.Draw(img)
        r = random.Random(4)
        for i in range(40):
            ph = r.random()
            sp = r.uniform(0.6, 1.4)
            u = (gt * sp * 0.9 + ph) % 1.0
            x = CXR - 30 + r.uniform(-120, 120) + 20 * math.sin(gt * 4 + i)
            y = top + 380 - u * 520
            s = 14 * (1 - u) + 2
            col = (255, int(200 - 140 * u), 20)
            d.ellipse((x - s, y - s, x + s, y + s), fill=col)
    a_e = ease_out(prog(t, t_e, 0.3))
    counter(img, CXL, f"{int(round(15 * ease_out(prog(t, t_15, 0.8))))} °C", "im Schnitt", C_EARTH, a_e)
    a_s = ease_out(prog(t, t_s, 0.3))
    counter(img, CXR, fmt_int(5500 * ease_out(prog(t, t_55, 1.3))) + " °C", "an der Oberfläche", C_SUN, a_s)
    vs_badge(img, gt, 1 - prog(t, t_55, 0.4), y=VIS_Y - 40)
    t_g = wt(sc, "Grad", 2)
    burst(img, CXR - 30, 520, t, t_g)


def person(d, cx, base_y, squash, color):
    """simple self-drawn figure standing on base_y"""
    hgt = 210 * squash
    wid = 1 / max(squash, 0.4) ** 0.5
    head = 30 * (0.7 + 0.3 * squash)
    body_w = 46 * wid
    d.rounded_rectangle((cx - body_w, base_y - hgt * 0.72, cx + body_w, base_y - hgt * 0.1), 24, fill=color)
    d.ellipse((cx - head * wid, base_y - hgt - head * 0.2, cx + head * wid, base_y - hgt + head * 1.6),
              fill=color)
    leg = 14 * wid
    d.rounded_rectangle((cx - body_w + 6, base_y - hgt * 0.14, cx - body_w + 6 + 2 * leg, base_y), 8, fill=color)
    d.rounded_rectangle((cx + body_w - 6 - 2 * leg, base_y - hgt * 0.14, cx + body_w - 6, base_y), 8, fill=color)


def scale_dev(img, cx, y, reading, color, sink=0.0, crack=0.0):
    d = ImageDraw.Draw(img)
    y = y + sink
    d.rounded_rectangle((cx - 150, y, cx + 150, y + 56), 18, fill=(235, 238, 245), outline=(40, 40, 60), width=4)
    rrect_layer(img, (cx - 105, y + 72, cx + 105, y + 132), 12, (15, 20, 30, 255), outline=color + (255,), width=4)
    text(img, reading, 38, cx, y + 102, fill=(120, 255, 140) if crack == 0 else (255, 90, 70))
    if crack > 0:
        pts = [(cx - 20, y), (cx - 5, y + 18), (cx - 28, y + 30), (cx - 8, y + 56)]
        d.line(pts, fill=(40, 40, 60), width=4)


def sc_schwerkraft(img, sc, t, gt):
    draw_header(img, gt, "RUNDE 3 · SCHWERKRAFT", t)
    panel_labels(img, t)
    t_s, t_28 = wt(sc, "Sonne"), wt(sc, "achtundzwanzigmal")
    t_w, t_70, t_2 = wt(sc, "Wiegst"), wt(sc, "siebzig"), wt(sc, "zwei")
    sw = prog(t, t_w - 0.2, 0.45)          # switch arrows -> scales
    a1 = 1 - ease_io(sw)
    if a1 > 0:
        layer = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(layer)
        for side, cx, n, spd, wd in ((0, CXL, 4, 0.35, 8), (1, CXR, 14, 1.6, 14)):
            r = random.Random(side + 2)
            act = 1.0 if side == 0 else ease_out(prog(t, t_s, 0.4))
            for i in range(n):
                x = cx + r.uniform(-170, 170)
                u = (gt * spd * (0.7 + 0.6 * r.random()) + r.random()) % 1.0
                y0 = 470 + u * 440
                ln = 50 + 40 * side
                col = (C_EARTH if side == 0 else C_SUN) + (int(255 * a1 * act),)
                d.line((x, y0, x, y0 + ln), fill=col, width=wd)
                d.polygon([(x - wd * 1.4, y0 + ln), (x + wd * 1.4, y0 + ln), (x, y0 + ln + wd * 2.2)], fill=col)
        img.paste(layer, (0, 0), layer)
        paste_c(img, earth_sprite(120, gt), CXL, 940, a1)
        paste_c(img, sun_sprite(120, gt), CXR, 940, a1)
        counter(img, CXL, "9,8 m/s²", "Anziehung", C_EARTH, a1 * ease_out(prog(t, 0.6, 0.3)))
        counter(img, CXR, "274 m/s²", "Anziehung", C_SUN, a1 * ease_out(prog(t, t_s, 0.3)))
    if sw > 0:
        a2 = ease_io(sw)
        layer = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(layer)
        squash = 1 - 0.45 * ease_out(prog(t, t_2, 0.6))
        sink = 26 * ease_out(prog(t, t_2, 0.5))
        shake = 6 * math.sin(gt * 60) * (1 - prog(t, t_2 + 0.5, 0.4)) if t > t_2 else 0
        person(d, CXL, 860, 1.0, C_EARTH)
        person(d, CXR + shake, 860 + sink, squash, C_SUN)
        img.paste(layer, (0, int(-40 * (1 - a2))), layer)
        re = 70 * ease_out(prog(t, t_70, 0.6))
        rs = 1953 * ease_out(prog(t, t_2 - 0.3, 0.6))
        scale_dev(img, CXL, 860, f"{int(round(re))} kg", C_EARTH)
        scale_dev(img, CXR + shake, 860, f"{fmt_int(rs)} kg", C_SUN, sink=sink,
                  crack=1.0 if t > t_2 + 0.3 else 0)
        counter(img, CXL, "70 kg", "auf der Erde", C_EARTH, a2 * ease_out(prog(t, t_70, 0.3)), y=NUM_Y + 30)
        counter(img, CXR, "fast 2 t", "auf der Sonne", C_SUN, a2 * ease_out(prog(t, t_2, 0.3)), y=NUM_Y + 30)
    vs_badge(img, gt, (1 - prog(t, t_s, 0.3)) + 0 * a1, y=VIS_Y)
    stamp(img, "≈28×", t, t_28, cy=VIS_Y - 20, hold=max(0.6, t_w - 0.45 - t_28))
    burst(img, CXR, 960, t, t_2 + 0.1)


def sc_masse(img, sc, t, gt):
    draw_header(img, gt, "RUNDE 4 · MASSE", t)
    t_s, t_x = wt(sc, "Sonne"), wt(sc, "dreihundertdreiunddreißigtausendmal")
    t_d, t_p = wt(sc, "Das"), wt(sc, "neunundneunzig")
    sw = ease_io(prog(t, t_d + 0.05, 0.35))
    a1 = 1 - ease_io(prog(t, t_d - 0.2, 0.25))
    if a1 > 0:
        panel_labels(img, t, a1)
        # balance beam
        tilt = 0.30 * ease_out(prog(t, t_x, 1.0)) + 0.04 * math.sin(gt * 9) * (1 - prog(t, t_x + 0.4, 0.8)) * (t > t_x)
        px, py = SPLIT, 760
        L = 290
        lx, ly = px - L * math.cos(tilt), py - L * math.sin(tilt)
        rx, ry = px + L * math.cos(tilt), py + L * math.sin(tilt)
        layer = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(layer)
        al = int(255 * a1)
        d.polygon([(px, py), (px - 60, py + 230), (px + 60, py + 230)], fill=(220, 220, 235, al))
        d.line((lx, ly, rx, ry), fill=(240, 240, 250, al), width=16)
        d.ellipse((px - 16, py - 16, px + 16, py + 16), fill=(255, 226, 60, al))
        for (x, y) in ((lx, ly), (rx, ry)):
            d.line((x, y, x - 70, y + 120), fill=(220, 220, 235, al), width=4)
            d.line((x, y, x + 70, y + 120), fill=(220, 220, 235, al), width=4)
            d.rounded_rectangle((x - 95, y + 118, x + 95, y + 134), 8, fill=(220, 220, 235, al))
        img.paste(layer, (0, 0), layer)
        paste_c(img, earth_sprite(60, gt), lx, ly + 86, a1)
        paste_c(img, sun_sprite(200, gt), rx, ry + 16, a1)
        counter(img, CXL, "1×", "Erdmasse", C_EARTH, a1 * ease_out(prog(t, t_s, 0.3)), y=NUM_Y + 60)
        counter(img, CXR, fmt_int(333000 * ease_out(prog(t, t_x, 1.4))) + "×", "Erdmassen", C_SUN,
                a1 * ease_out(prog(t, t_s, 0.3)), y=NUM_Y + 60)
    if sw > 0:
        # donut: share of the solar system's mass
        cx, cy, R = SPLIT, VIS_Y + 20, 300
        fr = 0.998 * ease_out(prog(t, t_p, 1.4))
        layer = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(layer)
        al = int(255 * sw)
        d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(60, 170, 255, al))
        if fr > 0:
            d.pieslice((cx - R, cy - R, cx + R, cy + R), -90, -90 + 360 * fr, fill=(255, 150, 0, al))
        r2 = R - 90
        d.ellipse((cx - r2, cy - r2, cx + r2, cy + r2), fill=(40, 20, 30, al))
        img.paste(layer, (0, 0), layer)
        if t >= t_p:
            text(img, fmt_dec(99.8 * ease_out(prog(t, t_p, 1.4))) + " %", 84, cx, cy - 20,
                 alpha=sw * ease_out(prog(t, t_p, 0.15)), stroke=5)
        text(img, "Sonne", 44, cx, cy + 50, fill=C_SUN, alpha=sw, path=FONT_XB)
        text(img, "Masse des Sonnensystems", 44, cx, NUM_Y + 10, alpha=sw, stroke=5, path=FONT_XB)
        text(img, "Rest (Planeten & Co.): 0,2 %", 38, cx, NUM_Y + 75, fill=C_EARTH, alpha=sw, stroke=4,
             path=FONT_XB)
    stamp(img, "333.000×", t, t_x + 0.9, size=118, cy=VIS_Y - 110, hold=max(0.4, t_d - 0.5 - t_x - 0.9))
    burst(img, SPLIT, VIS_Y + 20, t, wt(sc, "Prozent"))


DOTS = None


def finale_dots(R, d0):
    pts = []
    step = d0 * 1.05
    rr = random.Random(2)
    y = -R
    row = 0
    while y <= R:
        x = -R + (step / 2 if row % 2 else 0)
        while x <= R:
            if x * x + y * y <= (R - d0 / 2) ** 2:
                pts.append((x, y, rr.random()))
            x += step
        y += step * 0.866
        row += 1
    return pts


def sc_finale(img, sc, t, gt):
    t_p, t_e, t_k = wt(sc, "passen"), wt(sc, "Erden"), wt(sc, "Klarer")
    draw_header(img, gt, "FINALE · VOLUMEN", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    flash = 1 - prog(t, 0, 0.35)
    cx, cy = SPLIT, VIS_Y + 10
    pulse = 1 + 0.05 * ease_out(prog(t, t_k, 0.2)) * (1 - prog(t, t_k + 0.2, 0.6))
    core = 520 * ease_out(prog(t, 0, 0.6)) * pulse
    paste_c(img, sun_sprite(core, gt), cx, cy)
    global DOTS
    if DOTS is None:
        DOTS = finale_dots(248, 16)
    fill = ease_io(prog(t, t_p, t_e + 0.3 - t_p))
    if fill > 0:
        layer = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(layer)
        a = 1 - 0.7 * prog(t, t_k, 0.5)
        for (x, y, r) in DOTS:
            if r < fill:
                s = 7
                d.ellipse((cx + x - s, cy + y - s, cx + x + s, cy + y + s), fill=(70, 170, 255, int(235 * a)))
                d.ellipse((cx + x - s + 2, cy + y - s + 2, cx + x - 1, cy + y - 1), fill=(120, 220, 140, int(200 * a)))
        img.paste(layer, (0, 0), layer)
    # one real Earth for reference
    paste_c(img, earth_sprite(70, gt), 110, 470, ease_out(prog(t, 0.2, 0.4)))
    text(img, "= 1 Erde", 38, 160, 470, fill=C_EARTH, alpha=ease_out(prog(t, 0.2, 0.4)), stroke=4,
         path=FONT_XB, anchor="lm")
    n = 1304000 * ease_io(prog(t, t_p, t_e + 0.3 - t_p))
    big = ease_out(prog(t, t_e + 0.3, 0.3))
    if big < 1:
        counter(img, SPLIT, fmt_int(n), "Erden", C_EARTH, ease_out(prog(t, t_p - 0.2, 0.3)) * (1 - big))
    text(img, "≈ 1,3 Millionen Erden", 66, SPLIT, NUM_Y + 20, scale=0.6 + 0.4 * back_out(big), alpha=big,
         stroke=6, fill=WHITE)
    if t > t_k:
        p = prog(t, t_k, 0.5)
        # crown
        layer = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(layer)
        cy0 = cy - core / 2 - 40 + (1 - back_out(p)) * -200
        pts = [(cx - 120, cy0 + 60), (cx - 130, cy0 - 50), (cx - 60, cy0 + 5), (cx, cy0 - 80),
               (cx + 60, cy0 + 5), (cx + 130, cy0 - 50), (cx + 120, cy0 + 60)]
        d.polygon(pts, fill=(255, 215, 0, 255), outline=(150, 80, 0, 255))
        for (x, y) in pts[1:6:2]:
            d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=(255, 60, 60, 255))
        img.paste(layer, (0, 0), layer)
        text(img, "SIEGER: SONNE", 84, SPLIT, cy + 120, fill=C_HI, scale=2 - back_out(p),
             alpha=ease_out(p * 2), stroke=10, sfill=(160, 20, 0), rotate=-4)
        # confetti
        d = ImageDraw.Draw(img)
        r = random.Random(8)
        for i in range(90):
            x0 = r.uniform(30, 920)
            vy = r.uniform(250, 520)
            u = t - t_k
            y = 260 + u * vy - 60 * r.random()
            if y > SAFE_B:
                continue
            x = x0 + 30 * math.sin(u * 4 + i)
            s = r.uniform(6, 12)
            col = r.choice([(255, 226, 60), (64, 196, 255), (255, 90, 90), (120, 255, 160), (255, 255, 255)])
            ang = u * 6 + i
            dx, dy = s * math.cos(ang), s * 0.5 * math.sin(ang)
            d.polygon([(x - dx, y - dy), (x + dy, y - dx * 0.5), (x + dx, y + dy), (x - dy, y + dx * 0.5)], fill=col)
    if flash > 0:
        ov = Image.new("RGB", (W, H), (255, 240, 200))
        img.paste(Image.blend(img, ov, 0.6 * flash))


def sc_outro(img, sc, t, gt):
    draw_header(img, gt, "", t)
    t_s = wt(sc, "Schreib's")
    p = back_out(prog(t, 0.0, 0.5))
    cx, cy = SPLIT, 640
    bw, bh = 380 * p, 170 * p
    if p > 0.05:
        layer = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(layer)
        d.rounded_rectangle((cx - bw, cy - bh, cx + bw, cy + bh), 50, fill=(255, 255, 255, 245))
        d.polygon([(cx - 60 * p, cy + bh - 2), (cx - 130 * p, cy + bh + 80 * p), (cx + 10 * p, cy + bh - 2)],
                  fill=(255, 255, 255, 245))
        img.paste(layer, (0, 0), layer)
        text(img, "Deine Schätzung?", 52, cx, cy - 70, fill=(40, 40, 70), scale=p, path=FONT_XB)
        typed = "_ _ _ _ _ _ _"
        blink = "|" if int(gt * 3) % 2 == 0 else " "
        text(img, typed + " " + blink, 64, cx, cy + 40, fill=(255, 120, 0), scale=p)
    bob = 12 * math.sin(gt * 4)
    paste_c(img, earth_sprite(170, gt * 0.6), CXL - 40, 1000 + bob, ease_out(prog(t, 0.2, 0.4)))
    paste_c(img, sun_sprite(190, gt), CXR + 40, 1000 - bob, ease_out(prog(t, 0.3, 0.4)))
    if t > t_s:
        q = prog(t, t_s, 0.4)
        # comment icon + arrow to the right edge (TikTok comment button)
        layer = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(layer)
        ix, iy = SPLIT, 1000 - 30 * (1 - back_out(q))
        s = 90 * back_out(q)
        d.rounded_rectangle((ix - s, iy - s * 0.7, ix + s, iy + s * 0.7), int(s * 0.45), fill=(255, 226, 60, 255))
        d.polygon([(ix - s * 0.3, iy + s * 0.65), (ix - s * 0.6, iy + s * 1.05), (ix + s * 0.1, iy + s * 0.65)],
                  fill=(255, 226, 60, 255))
        for k in (-1, 0, 1):
            d.ellipse((ix + k * s * 0.45 - s * 0.12, iy - s * 0.12, ix + k * s * 0.45 + s * 0.12, iy + s * 0.12),
                      fill=(40, 30, 60, 255))
        img.paste(layer, (0, 0), layer)
        ax = 760 + 30 * math.sin(gt * 8)
        a = ease_out(q)
        dd = ImageDraw.Draw(img)
        if a > 0.1:
            dd.line((ax - 110, 1180, ax, 1180), fill=C_HI, width=14)
            dd.polygon([(ax + 40, 1180), (ax - 5, 1145), (ax - 5, 1215)], fill=C_HI)


DRAW = dict(hook=sc_hook, breite=sc_breite, hitze=sc_hitze, schwerkraft=sc_schwerkraft, masse=sc_masse,
            finale=sc_finale, outro=sc_outro)


def scene_at(gt):
    for i, sc in enumerate(SCENES):
        if gt < sc["start"] + sc["dur"] or i == len(SCENES) - 1:
            return i


def render_scene(i, gt):
    sc = SCENES[i]
    t = gt - sc["start"]
    img = BG.copy()
    draw_bg(img, gt)
    DRAW[sc["key"]](img, sc, t, gt)
    subtitles(img, sc, t)
    return img


def render_frame(fi):
    gt = fi / FPS
    i = scene_at(gt)
    img = render_scene(i, gt)
    t = gt - SCENES[i]["start"]
    if i > 0 and t < XF:
        prev = SCENES[i - 1]
        pimg = render_scene(i - 1, prev["start"] + prev["dur"] - 1 / FPS)
        img = Image.blend(pimg, img, ease_io(t / XF))
    return img


def render_bytes(fi):
    return render_frame(fi).tobytes()


# ---------------------------------------------------------------- audio mix
def synth_sfx():
    n = int((TOTAL + 0.5) * SR)
    out = np.zeros(n)
    r = np.random.default_rng(1)

    def add(sig, t0, gain):
        a = int(t0 * SR)
        b = min(n, a + len(sig))
        if a < n:
            out[a:b] += sig[:b - a] * gain

    def whoosh(d=0.45):
        m = int(d * SR)
        x = r.standard_normal(m)
        env = np.sin(np.linspace(0, np.pi, m)) ** 2
        # simple moving low-pass with sweeping width
        y = np.convolve(x, np.ones(24) / 24, mode="same") * env
        return y / (np.abs(y).max() + 1e-9)

    def thump(d=0.35):
        m = int(d * SR)
        tt = np.arange(m) / SR
        f = 120 * np.exp(-tt * 9) + 45
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 10)
        y[:200] += r.standard_normal(200) * np.linspace(0.6, 0, 200)
        return y

    def chime(d=1.2):
        m = int(d * SR)
        tt = np.arange(m) / SR
        y = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * k) for f, k in ((1046.5, 3), (1318.5, 3.5), (1568, 4)))
        return y / 3

    def tick():
        m = int(0.03 * SR)
        tt = np.arange(m) / SR
        return np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 200)

    for i, sc in enumerate(SCENES):
        if i > 0:
            add(whoosh(), sc["start"] - 0.15, 0.10)
    for st in SCORE_T:
        add(thump(), st, 0.15)
    add(chime(), SCORE_T[-1] + 0.05, 0.10)
    # soft ticks while counters run (scene 1/2/4/5)
    for i, word, d in ((1, "Sonne", 1.5), (2, "fünftausendfünfhundert", 1.3), (4, "dreihundertdreiunddreißigtausendmal", 1.4),
                       (5, "passen", 2.4)):
        t0 = SCENES[i]["start"] + wt(SCENES[i], word)
        k = 0.0
        while k < d:
            add(tick(), t0 + k, 0.05)
            k += 0.06 + 0.10 * (k / d) ** 2
    # quiet self-synthesised pad
    tt = np.arange(n) / SR
    pad = np.zeros(n)
    for f in (110, 164.81, 220, 277.18):
        pad += np.sin(2 * np.pi * f * tt + f) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * tt + f))
    pad *= 0.012 * np.clip(tt / 1.0, 0, 1) * np.clip((TOTAL - tt) / 1.0, 0, 1)
    out += pad
    return out


def build_audio():
    n = int((TOTAL + 0.5) * SR)
    voice = np.zeros(n)
    for sc in SCENES:
        with wave.open(sc["wav"]) as wf:
            data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16) / 32768.0
        a = int(sc["start"] * SR)
        voice[a:a + len(data)] += data[:n - a]
    pk = np.abs(voice).max()
    voice = voice / pk * 0.89
    mix = voice + synth_sfx()
    mix = np.clip(mix, -0.98, 0.98)
    path = os.path.join(BUILD, "mix.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((mix[:int(TOTAL * SR)] * 32767).astype(np.int16).tobytes())
    return path


def main():
    if "--stills" in sys.argv:
        os.makedirs(os.path.join(HERE, "qc"), exist_ok=True)
        times = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1:]] if len(sys.argv) > 2 else None
        if not times:
            times = []
            for sc in SCENES:
                for f in (0.3, 0.55, 0.8, 0.97):
                    times.append(sc["start"] + sc["dur"] * f)
        for gt in times:
            render_frame(int(gt * FPS)).save(os.path.join(HERE, "qc", f"f_{gt:06.2f}.png"))
        print("stills", len(times))
        return
    print(f"total {TOTAL:.2f}s, {NFRAMES} frames")
    for i, sc in enumerate(SCENES):
        print(f"  scene {i} {sc['key']:12s} start {sc['start']:6.2f} dur {sc['dur']:5.2f}")
    audio = build_audio()
    out = os.path.join(HERE, "erde_vs_sonne.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                           "-profile:v", "high", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ac", "2",
                           "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                           "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(render_bytes, range(NFRAMES), chunksize=4)):
            ff.stdin.write(b)
            if k % 150 == 0:
                print(f"  frame {k}/{NFRAMES}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()

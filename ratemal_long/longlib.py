#!/usr/bin/env python3
"""Landscape (1920x1080) "Rate mal" quiz engine for long-form YouTube videos.

Colourful starry style of the shorts: purple-blue gradient, flat shapes, yellow brand pill,
white subtitles with yellow word highlight. Quiz flow per question:
    FRAGE-Karte (stumm) -> Frage (Sprache, Karten A/B/C ploppen auf) -> Countdown (stumm)
    -> Auflösung (richtige Karte grün, Erklär-Animation rechts).
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
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tiere"))
import engine as E  # noqa: E402
from engine import (SS, back_out, clamp, ease_io, ease_out, paste_c, prog, rrect, text, text_w, F,  # noqa: E402,F401
                    FONT_BLACK, FONT_XB, C_HI)

W, H, FPS = 1920, 1080, 30
SR = 48000
YELLOW = C_HI
NAVY = (40, 20, 60)
ORANGE = (255, 150, 70)
SKIN = (255, 196, 150)
RED = (235, 50, 70)
BLUE = (70, 160, 255)
GREEN = (80, 215, 115)
WHITE = (255, 255, 255)
PURPLE = (170, 120, 255)
LETTER_COL = [(255, 120, 60), (70, 160, 255), (190, 110, 255)]
SUB_Y = 1000
XF = 0.3
PUNCT = ".,:;!?-…"

CFG = {}
SEGS = []          # timeline segments
BY = {}            # key -> seg
TOTAL = 0.0
BG = None
STARS = []


# ------------------------------------------------------------------ timeline
def strip(w):
    return w.strip(PUNCT)


def wt(seg, word, n=1, edge="s"):
    c = 0
    for w in seg["toks"]:
        if strip(w["text"]).lower() == word.lower():
            c += 1
            if c == n:
                return w[edge]
    raise KeyError(f"{seg['key']}: {word}")


def mp3_to_wav(src, dst):
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", str(SR), dst], check=True)
    with wave.open(dst) as wf:
        return wf.getnframes() / SR


def build_timeline(plan):
    """plan: list of dicts {key, audio(optional), dur(optional silent), pre, post, kind, q}"""
    global TOTAL
    raw, build = CFG["raw"], CFG["build"]
    t = 0.0
    SEGS.clear()
    BY.clear()
    for p in plan:
        seg = dict(p)
        seg.setdefault("pre", 0.0)
        seg.setdefault("post", 0.0)
        if p.get("audio"):
            wav = os.path.join(build, p["audio"] + ".wav")
            dur = mp3_to_wav(os.path.join(raw, p["audio"] + ".mp3"), wav)
            words = json.load(open(os.path.join(raw, p["audio"] + ".words.json")))["words"]
            seg["wav"] = wav
            seg["toks"] = [dict(text=w["text"], s=w["start"] + seg["pre"], e=w["end"] + seg["pre"]) for w in words]
            seg["vdur"] = dur
            seg["dur"] = seg["pre"] + dur + seg["post"]
        else:
            seg["toks"] = []
            seg["dur"] = p["dur"]
        seg["start"] = t
        t += seg["dur"]
        SEGS.append(seg)
        BY[seg["key"]] = seg
    TOTAL = t
    return TOTAL


def seg_at(gt):
    for i, s in enumerate(SEGS):
        if gt < s["start"] + s["dur"] or i == len(SEGS) - 1:
            return i


# ------------------------------------------------------------------ background
def make_bg():
    y = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([12, 14, 52]), np.array([66, 30, 116])
    bg = top * (1 - y) + bot * y
    bg = np.repeat(bg, W, axis=1)
    yy, xx = np.mgrid[0:H, 0:W]
    glow = np.exp(-(((xx - W / 2) / 760) ** 2 + ((yy - H * 0.45) / 330) ** 2))[..., None]
    bg = bg + glow * np.array([36, 52, 110])
    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    r = random.Random(4)
    for _ in range(260):
        x, yv, s = r.uniform(0, W), r.uniform(0, H), r.uniform(0.8, 2.2)
        v = int(r.uniform(90, 200))
        d.ellipse((x - s, yv - s, x + s, yv + s), fill=(v, v, v + 20))
    return img


def draw_bg(img, gt):
    d = ImageDraw.Draw(img)
    for x, y, s, ph, sp in STARS:
        a = 0.5 + 0.5 * math.sin(gt * sp + ph)
        v = int(150 + 105 * a)
        r = s * (0.7 + 0.5 * a)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(v, v, 255))


# ------------------------------------------------------------------ widgets
def pill(img, s, cx, cy, col=WHITE, a=1.0, size=38, bg=(15, 20, 40), path=FONT_XB, tcol=None):
    if a <= 0.02:
        return
    w = text_w(s, size, path) + 54
    rrect(img, (cx - w / 2, cy - size * 0.88, cx + w / 2, cy + size * 0.88), int(size * 0.88),
          bg + (int(230 * a),), outline=col + (int(255 * a),), width=4)
    text(img, s, size, cx, cy, fill=tcol or col, alpha=a, path=path)


def brand(img, cx, cy, gt, s=1.0, a=1.0):
    if a <= 0.03 or s <= 0.03:
        return
    w, h = 175 * s, 44 * s
    rrect(img, (cx - w, cy - h, cx + w, cy + h), int(h), YELLOW + (int(255 * a),), outline=NAVY + (255,),
          width=max(2, int(5 * s)))
    text(img, "RATE MAL", 48 * s, cx - 24 * s, cy + 2, fill=NAVY, alpha=a)
    q = 1 + 0.12 * math.sin(gt * 6)
    text(img, "?", 60 * s * q, cx + 137 * s, cy + 2, fill=(255, 70, 70), stroke=max(2, int(4 * s)), sfill=NAVY,
         rotate=10 * math.sin(gt * 4), alpha=a)


def stamp(img, s, t, t0, cx, cy, size=120, rot=-6, hold=99.0, fill=YELLOW, sfill=(170, 20, 0)):
    if t < t0:
        return
    p = prog(t, t0, 0.35)
    q = ease_io(prog(t, t0 + hold, 0.35))
    sc = (2.2 - 1.2 * back_out(p, 2.4)) * (1 - 0.6 * q)
    text(img, s, size, cx, cy, fill=fill, scale=sc, alpha=ease_out(p * 2) * (1 - q), stroke=11, sfill=sfill,
         rotate=rot)


def burst(img, cx, cy, t, t0, color=YELLOW, n=16, rad=220):
    p = prog(t, t0, 0.6)
    if p <= 0 or p >= 1:
        return
    d = ImageDraw.Draw(img)
    e = ease_out(p)
    for i in range(n):
        a = i / n * 2 * math.pi + 0.3
        r0, r1 = rad * (0.35 + 0.6 * e), rad * (0.5 + 0.75 * e)
        d.line((cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
               fill=color, width=max(1, int(10 * (1 - p))))


def confetti(img, t, t0, n=120, x0=60, x1=1860, y0=-20, ybot=940, seed=8):
    if t < t0:
        return
    d = ImageDraw.Draw(img)
    r = random.Random(seed)
    u = t - t0
    for i in range(n):
        x = r.uniform(x0, x1)
        vy = r.uniform(220, 480)
        y = y0 + u * vy - 300 * r.random()
        if y > ybot or y < -20:
            continue
        x += 30 * math.sin(u * 4 + i)
        s = r.uniform(6, 12)
        col = r.choice([YELLOW, (64, 196, 255), (255, 90, 90), (120, 255, 160), WHITE])
        ang = u * 6 + i
        dx, dy = s * math.cos(ang), s * 0.5 * math.sin(ang)
        d.polygon([(x - dx, y - dy), (x + dy, y - dx * 0.5), (x + dx, y + dy), (x - dy, y + dx * 0.5)], fill=col)


def check(img, cx, cy, r, a=1.0, col=GREEN, w=22):
    if a <= 0.02:
        return
    d = ImageDraw.Draw(img)
    p1, p2, p3 = (cx - r * 0.7, cy), (cx - r * 0.2, cy + r * 0.5), (cx + r * 0.8, cy - r * 0.6)
    if a < 0.5:
        q = a / 0.5
        d.line((p1[0], p1[1], p1[0] + (p2[0] - p1[0]) * q, p1[1] + (p2[1] - p1[1]) * q), fill=col, width=w)
    else:
        q = (a - 0.5) / 0.5
        d.line((p1, p2), fill=col, width=w)
        d.line((p2[0], p2[1], p2[0] + (p3[0] - p2[0]) * q, p2[1] + (p3[1] - p2[1]) * q), fill=col, width=w)


def cross(img, cx, cy, r, a=1.0, col=RED, w=20):
    if a <= 0.02:
        return
    d = ImageDraw.Draw(img)
    k = r * a
    d.line((cx - k, cy - k, cx + k, cy + k), fill=col, width=w)
    d.line((cx - k, cy + k, cx + k, cy - k), fill=col, width=w)


def ring(img, cx, cy, r, frac, col, label, size=None, a=1.0, width=18):
    if a <= 0.02:
        return
    box = (int(cx - r - width), int(cy - r - width), int(cx + r + width), int(cy + r + width))
    lay = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]))
    d = ImageDraw.Draw(lay)
    o = width
    rr = (o, o, o + 2 * r, o + 2 * r)
    d.ellipse(rr, fill=(15, 20, 40, int(200 * a)), outline=(255, 255, 255, int(70 * a)), width=width)
    if frac > 0:
        d.arc(rr, -90, -90 + 360 * min(1, frac), fill=col + (int(255 * a),), width=width)
    img.paste(lay, box[:2], lay)
    text(img, label, size or r * 0.9, cx, cy, alpha=a, stroke=6, sfill=NAVY)


def wrap(s, size, maxw, path=FONT_BLACK):
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if cur and text_w(trial, size, path) > maxw:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def fit_text(img, s, size, cx, cy, maxw, **kw):
    path = kw.get("path", FONT_BLACK)
    w = text_w(s, size, path)
    if w > maxw:
        size = size * maxw / w
    return text(img, s, size, cx, cy, **kw)


# ------------------------------------------------------------------ quiz layout
CARD_X = [400, 960, 1520]
CARD_Y = 560
CARD_W, CARD_H = 500, 300


def question_text(img, s, a=1.0, y=215, size=62):
    lines = wrap(s, size, 1600)
    if len(lines) > 2:
        size = size * 0.86
        lines = wrap(s, size, 1650)
    lh = size * 1.18
    y0 = y - lh * (len(lines) - 1) / 2
    for i, ln in enumerate(lines):
        text(img, ln, size, W / 2, y0 + i * lh, alpha=a, stroke=8, sfill=NAVY)


def card(img, i, label, cx, cy, s=1.0, a=1.0, state=None, gt=0.0, w=CARD_W, h=CARD_H):
    """state None | 'right' | 'wrong'"""
    if a <= 0.02 or s <= 0.03:
        return
    cw, ch = w * s, h * s
    col = LETTER_COL[i]
    fill = (255, 255, 255)
    outline = col
    if state == "right":
        outline = GREEN
        fill = (225, 255, 232)
    a_card = a * (0.42 if state == "wrong" else 1.0)
    if state == "right":
        g = 0.5 + 0.5 * math.sin(gt * 6)
        gw = 18 + 8 * g
        rrect(img, (cx - cw / 2 - gw, cy - ch / 2 - gw, cx + cw / 2 + gw, cy + ch / 2 + gw), int(46 * s + gw),
              GREEN + (int(110 * a),))
    rrect(img, (cx - cw / 2 + 10 * s, cy - ch / 2 + 16 * s, cx + cw / 2 + 10 * s, cy + ch / 2 + 16 * s), int(40 * s),
          (0, 0, 0, int(90 * a_card)))
    rrect(img, (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2), int(40 * s), fill + (int(255 * a_card),),
          outline=outline + (int(255 * a_card),), width=max(2, int(9 * s)))
    # letter badge
    bx, by, br = cx - cw / 2 + 62 * s, cy - ch / 2 + 62 * s, 40 * s
    d = ImageDraw.Draw(img)
    d.ellipse((bx - br, by - br, bx + br, by + br), fill=(col if state != "right" else GREEN) + (int(255 * a_card),))
    text(img, "ABC"[i], 50 * s, bx, by + 1, fill=WHITE, alpha=a_card)
    lines = label.split("\n")
    size = 56 * s
    for ln in lines:
        ww = text_w(ln, size)
        if ww > cw - 70 * s:
            size = size * (cw - 70 * s) / ww
    lh = size * 1.15
    y0 = cy + 22 * s - lh * (len(lines) - 1) / 2
    for k, ln in enumerate(lines):
        text(img, ln, size, cx, y0 + k * lh, fill=NAVY, alpha=a_card)
    if state == "right":
        check(img, cx + cw / 2 - 50 * s, cy - ch / 2 + 50 * s, 34 * s, 1.0, w=max(4, int(14 * s)))
    elif state == "wrong":
        cross(img, cx + cw / 2 - 50 * s, cy - ch / 2 + 50 * s, 22 * s, a, w=max(4, int(12 * s)))


def top_bar(img, gt, qn, a=1.0, score_marks=None):
    if a <= 0.02:
        return
    if qn:
        pill(img, f"FRAGE {qn}/7", 175, 70, YELLOW, a, size=40, path=FONT_BLACK)
    brand(img, W - 230, 70, gt, 0.9, a)
    # progress dots
    for k in range(7):
        x = W / 2 - 3 * 46 + k * 46
        done = qn and k < qn
        d = ImageDraw.Draw(img)
        r = 13 if (qn and k == qn - 1) else 10
        col = YELLOW if done else (255, 255, 255)
        d.ellipse((x - r, 70 - r, x + r, 70 + r), fill=col + (int((255 if done else 90) * a),))


def countdown(img, t, dur, gt):
    """3-2-1 style ring under the cards (t relative to countdown start)."""
    n = int(round(dur))
    a = ease_out(prog(t, 0, 0.25)) * (1 - prog(t, dur - 0.2, 0.2))
    left = max(0, dur - t)
    k = int(math.ceil(left - 1e-6))
    frac = 1 - left / dur
    pulse = 1 + 0.12 * (1 - (t % 1.0)) ** 3
    ring(img, W / 2, 930, 62 * pulse, frac, YELLOW, str(max(1, min(n, k))), size=66, a=a)
    q = 1 + 0.05 * math.sin(gt * 8)
    text(img, "Rate mal!", 54 * q, W / 2 - 330, 930, fill=YELLOW, stroke=7, sfill=NAVY, alpha=a, rotate=-4)
    text(img, "Dein Tipp?", 54 * q, W / 2 + 340, 930, fill=WHITE, stroke=7, sfill=NAVY, alpha=a, rotate=4)


# ------------------------------------------------------------------ subtitles
def subtitles(img, seg, t, y=SUB_Y, size=56, maxw=1500):
    toks = seg["toks"]
    if not toks:
        return
    chunks, cur = [], []
    for tk in toks:
        trial = cur + [tk]
        wdt = text_w(" ".join(x["text"] for x in trial), size)
        if cur and (len(trial) > 7 or wdt > maxw):
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
    words = [x["text"] for x in active]
    curs = [tk["s"] - 0.03 <= t < tk["e"] + 0.05 for tk in active]
    widths = [text_w(w, size * (1.08 if c else 1.0)) + 12 for w, c in zip(words, curs)]
    space = 16
    total = sum(widths) + space * (len(words) - 1)
    rrect(img, (W / 2 - total / 2 - 30, y - size * 0.85, W / 2 + total / 2 + 30, y + size * 0.85), int(size * 0.5),
          (10, 8, 30, int(150 * p)))
    x = W / 2 - total / 2
    for tk, wtxt, wd, c in zip(active, words, widths, curs):
        on = tk["s"] - 0.03 <= t
        col = YELLOW if c else (WHITE if on else (205, 205, 220))
        text(img, wtxt, size, x + wd / 2, y, fill=col, scale=(1.08 if c else 1.0) * (0.88 + 0.12 * p), alpha=p,
             stroke=7, sfill=(0, 0, 0))
        x += wd + space


# ------------------------------------------------------------------ render loop
def render_seg(i, gt):
    seg = SEGS[i]
    t = gt - seg["start"]
    img = BG.copy()
    draw_bg(img, gt)
    CFG["draw"](img, seg, t, gt)
    subtitles(img, seg, t)
    return img


def render_frame(fi):
    gt = fi / FPS
    i = seg_at(gt)
    img = render_seg(i, gt)
    t = gt - SEGS[i]["start"]
    if i > 0 and t < XF and SEGS[i].get("xf", True):
        prev = SEGS[i - 1]
        pimg = render_seg(i - 1, prev["start"] + prev["dur"] - 1 / FPS)
        img = Image.blend(pimg, img, ease_io(t / XF))
    return img.convert("RGB")


UPSCALE = 2 if "--4k" in sys.argv else 1


def render_bytes(fi):
    im = render_frame(fi)
    if UPSCALE > 1:
        im = im.resize((W * UPSCALE, H * UPSCALE), Image.LANCZOS)
    return im.tobytes()


# ------------------------------------------------------------------ audio
def _whoosh(r, d=0.45):
    m = int(d * SR)
    y = np.convolve(r.standard_normal(m), np.ones(24) / 24, mode="same") * np.sin(np.linspace(0, np.pi, m)) ** 2
    return y / (np.abs(y).max() + 1e-9)


def _tick(f=2200, d=0.04):
    tt = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * f * tt) * np.exp(-tt * 140)


def _pop():
    tt = np.arange(int(0.12 * SR)) / SR
    f = 500 + 900 * np.exp(-tt * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 35)


def _chime():
    tt = np.arange(int(1.3 * SR)) / SR
    return sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * k) for f, k in ((784, 3), (1046.5, 3.2), (1318.5, 3.6),
                                                                          (1568, 4))) / 4


def _thump():
    tt = np.arange(int(0.35 * SR)) / SR
    f = 120 * np.exp(-tt * 9) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 10)


def _beep():
    tt = np.arange(int(0.32 * SR)) / SR
    y = np.sin(2 * np.pi * 1320 * tt) * ((tt < 0.12) | (tt > 0.2)) * (tt < 0.32)
    return y * 0.7


def _glitch(r):
    m = int(0.35 * SR)
    y = r.standard_normal(m)
    y = np.convolve(y, np.ones(6) / 6, mode="same")
    gate = (np.sin(2 * np.pi * 23 * np.arange(m) / SR) > 0).astype(float)
    return y * gate * np.linspace(1, 0.2, m) * 0.6


def _heart():
    a = _thump()
    out = np.zeros(int(0.7 * SR))
    out[:len(a)] += a
    k = int(0.24 * SR)
    out[k:k + len(a)] += a[:len(out) - k] * 0.7
    return out


def _rise(r, d=0.7):
    m = int(d * SR)
    tt = np.arange(m) / SR
    f = 300 + 900 * (tt / d) ** 2
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.linspace(0, np.pi, m)) ** 2 * 0.4
    y += _whoosh(r, d) * 0.5
    return y


def _alarm():
    tt = np.arange(int(0.9 * SR)) / SR
    y = np.sign(np.sin(2 * np.pi * 1800 * tt)) * 0.25 * (np.sin(2 * np.pi * 14 * tt) > 0)
    return y * np.exp(-tt * 1.5)


def _ding():
    tt = np.arange(int(0.7 * SR)) / SR
    return (np.sin(2 * np.pi * 1568 * tt) + 0.5 * np.sin(2 * np.pi * 2349 * tt)) * np.exp(-tt * 6) / 1.5


def synth(events):
    """events: list of (gt, kind, gain)"""
    n = int((TOTAL + 1.0) * SR)
    out = np.zeros(n)
    r = np.random.default_rng(1)

    def add(sig, t0, gain):
        a = int(max(0, t0) * SR)
        b = min(n, a + len(sig))
        if a < n:
            out[a:b] += sig[:b - a] * gain

    lib = dict(whoosh=lambda: _whoosh(r), tick=_tick, tock=lambda: _tick(1500, 0.05), pop=_pop, chime=_chime,
               thump=_thump, beep=_beep, glitch=lambda: _glitch(r), heart=_heart, rise=lambda: _rise(r),
               alarm=_alarm, ding=_ding)
    for gt, kind, gain in events:
        add(lib[kind](), gt, gain)
    # music bed: soft pad + gentle pluck arpeggio (A minor / F / C / G), 96 bpm
    tt = np.arange(n) / SR
    pad = np.zeros(n)
    prog_ch = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (130.81, 196.0, 261.63), (196.0, 246.94, 293.66)]
    bar = 60 / 96 * 4
    idx = ((tt // bar) % 4).astype(int)
    for k in range(3):
        f = np.array([c[k] for c in prog_ch])[idx]
        ph = np.cumsum(2 * np.pi * f / SR)
        pad += np.sin(ph) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * tt + k))
    pad *= 0.010
    pl = np.zeros(n)
    step = 60 / 96 / 2
    m = int(0.5 * SR)
    env = np.exp(-np.arange(m) / SR * 7)
    j = 0
    while j * step < TOTAL:
        t0 = j * step
        ch = prog_ch[int(t0 // bar) % 4]
        f = ch[[0, 1, 2, 1][j % 4]] * 2
        a = int(t0 * SR)
        b = min(n, a + m)
        pl[a:b] += np.sin(2 * np.pi * f * np.arange(b - a) / SR) * env[:b - a]
        j += 1
    pl *= 0.006
    fade = np.clip(tt / 2.0, 0, 1) * np.clip((TOTAL - tt) / 2.0, 0, 1)
    return out + (pad + pl) * fade


def build_audio(events):
    n = int((TOTAL + 1.0) * SR)
    voice = np.zeros(n)
    for seg in SEGS:
        if "wav" not in seg:
            continue
        with wave.open(seg["wav"]) as wf:
            data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16) / 32768.0
        a = int((seg["start"] + seg["pre"]) * SR)
        voice[a:a + len(data)] += data[:n - a]
    voice = voice / np.abs(voice).max() * 0.89
    mix = np.clip(voice + synth(events), -0.98, 0.98)
    path = os.path.join(CFG["build"], "mix.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((mix[:int(TOTAL * SR)] * 32767).astype(np.int16).tobytes())
    return path


# ------------------------------------------------------------------ setup / main
def setup(here, out, plan, draw, events):
    global BG
    CFG.update(here=here, out=out, draw=draw, events=events,
               raw=os.path.join(here, "audio_raw"), build=os.path.join(here, "build"))
    os.makedirs(CFG["build"], exist_ok=True)
    build_timeline(plan)
    BG = make_bg()
    r = random.Random(11)
    STARS[:] = [(r.uniform(0, W), r.uniform(0, H), r.uniform(0.8, 2.2), r.uniform(0, 6.3), r.uniform(0.5, 2.0))
                for _ in range(90)]


def main():
    here = CFG["here"]
    if "--stills" in sys.argv:
        qc = os.path.join(here, "qc")
        os.makedirs(qc, exist_ok=True)
        for f in os.listdir(qc):
            os.remove(os.path.join(qc, f))
        args = sys.argv[sys.argv.index("--stills") + 1:]
        times = [float(x) for x in args]
        if not times:
            for s in SEGS:
                for f in (0.2, 0.5, 0.85):
                    times.append(s["start"] + s["dur"] * f)
        with Pool(4) as pool:
            ims = pool.map(render_frame, [int(gt * FPS) for gt in times])
        for gt, im in zip(times, ims):
            im.save(os.path.join(qc, f"f_{gt:06.2f}.png"))
        print("stills", len(times), "total", round(TOTAL, 2))
        return
    nfr = int(math.ceil(TOTAL * FPS))
    print(f"total {TOTAL:.2f}s, {nfr} frames")
    for s in SEGS:
        print(f"  {s['key']:8s} start {s['start']:7.2f} dur {s['dur']:6.2f}")
    audio = build_audio(CFG["events"]())
    out = os.path.join(here, CFG["out"])
    if UPSCALE > 1:
        out = out.replace(".mp4", "_4k.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W * UPSCALE}x{H * UPSCALE}", "-r", str(FPS), "-i", "-", "-i", audio,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "19" if UPSCALE == 1 else "20",
                           "-af", "volume=10.9dB,alimiter=limit=0.84:level=false", "-pix_fmt", "yuv420p",
                           "-profile:v", "high", "-ac", "2", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                           "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(render_bytes, range(nfr), chunksize=8)):
            ff.stdin.write(b)
            if k % 1500 == 0:
                print("frame", k, flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", out)

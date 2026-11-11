#!/usr/bin/env python3
"""Voice-less 'Rate mal' fact Shorts (1080x1920): animated text cards, flat visuals, music + SFX.

Usage: python3 make.py [--stills] [name ...]   names: hirnfrost, ohren, gaensehaut
"""
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
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tiere"))
sys.path.insert(0, os.path.join(ROOT, "ratemal_long"))
ARGS = sys.argv[1:]
sys.argv = [sys.argv[0]]
import engine as E  # noqa: E402
import longlib as LL  # noqa: E402
from engine import text, text_w, back_out, ease_out, ease_io, prog, paste_c, FONT_XB  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 48000
NAVY = (40, 20, 60)
YELLOW, WHITE, RED, BLUE, GREEN = (255, 226, 60), (255, 255, 255), (235, 50, 70), (90, 170, 255), (90, 220, 120)
SKIN = (255, 205, 165)
CAP_Y = 1290
WPS = 3.5            # words per second for the caption reveal


# ------------------------------------------------------------------ shared drawing
def make_bg(c0, c1):
    y = np.linspace(0, 1, H)[:, None, None]
    bg = np.array(c0) * (1 - y) + np.array(c1) * y
    bg = np.repeat(bg, W, axis=1)
    yy, xx = np.mgrid[0:H, 0:W]
    g = np.exp(-(((xx - W / 2) / 520) ** 2 + ((yy - 820) / 560) ** 2))[..., None]
    bg = bg + g * np.array([40, 40, 80])
    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    r = random.Random(5)
    for _ in range(240):
        x, yv, s = r.uniform(0, W), r.uniform(0, H), r.uniform(0.8, 2.4)
        v = int(r.uniform(110, 230))
        d.ellipse((x - s, yv - s, x + s, yv + s), fill=(v, v, v + 20))
    return img


def wrap(words, size, maxw):
    lines, cur = [], []
    for w in words:
        trial = cur + [w]
        if cur and text_w(" ".join(trial), size) > maxw:
            lines.append(cur)
            cur = [w]
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


SEG = {}


def W_(word, n=1, fallback=1.0):
    """time (in scene) of the n-th spoken occurrence of word"""
    c = 0
    for tx, st, en in SEG.get("words", []):
        if tx.strip(".,!?:;").lower() == word.lower():
            c += 1
            if c == n:
                return st
    return fallback


def caption(img, s, t, size=72, y=CAP_Y, start=0.25, hl=()):
    """word-by-word reveal; words in hl are drawn yellow. With a voice track the words follow the speech."""
    if SEG.get("words"):
        return voice_caption(img, t, size, y, hl)
    words = s.split()
    lines = wrap(words, size, 900)
    lh = size * 1.22
    y0 = y - lh * (len(lines) - 1) / 2
    k = 0
    hls = {h.strip(".,!?:").upper() for h in hl}
    for li, ln in enumerate(lines):
        widths = [text_w(w, size) for w in ln]
        total = sum(widths) + 22 * (len(ln) - 1)
        x = W / 2 - total / 2
        for w, wd in zip(ln, widths):
            p = ease_out(prog(t, start + k / WPS, 0.18))
            if p > 0.02:
                col = YELLOW if w.strip(".,!?:").upper() in hls else WHITE
                text(img, w, size, x + wd / 2, y0 + li * lh + 14 * (1 - p), fill=col, alpha=p, stroke=8,
                     sfill=(0, 0, 0), scale=0.9 + 0.1 * back_out(p))
            x += wd + 22
            k += 1
    return start + len(words) / WPS


def voice_caption(img, t, size, y, hl):
    ws = SEG["words"]
    # chunk into sentences / max 9 words; show the chunk containing the current time
    chunks, cur = [], []
    for w in ws:
        cur.append(w)
        if w[0][-1] in ".!?" or len(cur) >= 8:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    merged = []
    for ch in chunks:
        if merged and len(ch) < 3 and len(merged[-1]) + len(ch) <= 11:
            merged[-1] = merged[-1] + ch
        else:
            merged.append(ch)
    chunks = merged
    active = chunks[0]
    for i, ch in enumerate(chunks):
        if t >= ch[0][1] - 0.15:
            active = ch
    hls = {h.strip(".,!?:").upper() for h in hl}
    words = [w[0] for w in active]
    lines = wrap(words, size, 900)
    lh = size * 1.22
    y0 = y - lh * (len(lines) - 1) / 2
    k = 0
    for li, ln in enumerate(lines):
        widths = [text_w(w, size) for w in ln]
        total = sum(widths) + 22 * (len(ln) - 1)
        x = W / 2 - total / 2
        for w, wd in zip(ln, widths):
            tx, st, en = active[k]
            p = ease_out(prog(t, st - 0.08, 0.15))
            if p > 0.02:
                now = st - 0.03 <= t < en + 0.05
                col = YELLOW if (now or w.strip(".,!?:").upper() in hls) else WHITE
                text(img, w, size, x + wd / 2, y0 + li * lh + 12 * (1 - p), fill=col, alpha=p, stroke=8,
                     sfill=(0, 0, 0), scale=(1.08 if now else 1.0) * (0.9 + 0.1 * back_out(p)))
            x += wd + 22
            k += 1
    return 0


def word_times(s, start=0.25):
    return [start + i / WPS for i in range(len(s.split()))]


def pill(img, s, cx, cy, col, a, size=42):
    if a <= 0.02:
        return
    w = text_w(s, size, FONT_XB) + 56
    E.rrect(img, (cx - w / 2, cy - size * 0.9, cx + w / 2, cy + size * 0.9), int(size * 0.9), (15, 20, 40, int(230 * a)),
            outline=col + (int(255 * a),), width=4)
    text(img, s, size, cx, cy, fill=col, alpha=a, path=FONT_XB)


def stamp(img, s, t, t0, cx, cy, size=130, rot=-6, fill=YELLOW, sfill=(170, 20, 0)):
    E.stamp(img, s, t, t0, cx=cx, cy=cy, size=size, rot=rot, fill=fill, sfill=sfill)


def check(img, cx, cy, r, a):
    if a <= 0.02:
        return
    d = ImageDraw.Draw(img)
    d.line([(cx - r * 0.7, cy), (cx - r * 0.2, cy + r * 0.5), (cx + r * 0.8, cy - r * 0.6)][:2 + int(a > 0.5)],
           fill=GREEN, width=max(6, int(r * 0.3)))


def head_profile(img, cx, cy, s=1.0, col=SKIN):
    d = ImageDraw.Draw(img)
    d.ellipse((cx - 230 * s, cy - 250 * s, cx + 230 * s, cy + 230 * s), fill=col)
    d.polygon([(cx + 200 * s, cy - 40 * s), (cx + 290 * s, cy + 30 * s), (cx + 210 * s, cy + 60 * s)], fill=col)
    d.rectangle((cx - 90 * s, cy + 180 * s, cx + 90 * s, cy + 420 * s), fill=col)
    d.ellipse((cx + 110 * s, cy - 90 * s, cx + 150 * s, cy - 50 * s), fill=NAVY)


# ------------------------------------------------------------------ SHORT: Hirnfrost
def icecream(img, cx, cy, s, gt):
    d = ImageDraw.Draw(img)
    d.polygon([(cx - 70 * s, cy), (cx + 70 * s, cy), (cx, cy + 220 * s)], fill=(230, 170, 90))
    for k in range(4):
        d.line((cx - 60 * s + k * 35 * s, cy + 5 * s, cx - 10 * s + k * 20 * s, cy + 150 * s), fill=(200, 140, 70),
               width=max(2, int(4 * s)))
    for (dx, dy, c) in ((-45, -20, (255, 170, 200)), (45, -20, (160, 230, 255)), (0, -90, (255, 240, 200))):
        d.ellipse((cx + (dx - 75) * s, cy + (dy - 75) * s, cx + (dx + 75) * s, cy + (dy + 75) * s), fill=c)


def bolt(img, x, y, s, col=YELLOW):
    d = ImageDraw.Draw(img)
    d.polygon([(x, y - 70 * s), (x - 40 * s, y + 10 * s), (x - 5 * s, y + 10 * s), (x - 25 * s, y + 80 * s),
               (x + 45 * s, y - 15 * s), (x + 8 * s, y - 15 * s), (x + 25 * s, y - 70 * s)], fill=col, outline=NAVY)


def hf_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    head_profile(img, 470, 760, 1.0)
    icecream(img, 830, 820 + 10 * math.sin(gt * 3), 0.9, gt)
    if t > 1.0:
        bolt(img, 420, 560, 1.0 + 0.1 * math.sin(gt * 9))
        bolt(img, 300, 620, 0.7 + 0.1 * math.sin(gt * 8 + 1))
    q = 1 + 0.1 * math.sin(gt * 6)
    text(img, "?", 200 * q, 900, 520, fill=YELLOW, stroke=10, sfill=NAVY, rotate=10, alpha=ease_out(prog(t, 0.5, 0.3)))
    caption(img, "Rate mal, was passiert, wenn du Eis zu schnell isst!", t, hl=("RATE", "MAL,", "EIS"))


def mouth_panel(img, t, gt, cold=0.0, vessel=1.0, nerve=0.0):
    head_profile(img, 520, 760, 1.15)
    d = ImageDraw.Draw(img)
    # palate line + mouth cavity
    d.chord((560, 760, 860, 960), 180, 360, fill=(170, 60, 80))
    d.line((560, 860, 860, 860), fill=(255, 150, 160), width=10)
    if cold > 0.02:
        lay = Image.new("RGBA", (W, H))
        ImageDraw.Draw(lay).ellipse((600, 780, 820, 900), fill=(140, 210, 255, int(150 * cold)))
        img.alpha_composite(lay)
        icecream(img, 900, 880, 0.5, gt)
    # vessel
    w = 26 * vessel
    E.rrect(img, (590, 820 - w / 2, 830, 820 + w / 2), int(max(2, w / 2)), (220, 40, 60, 255))
    if nerve > 0.02:
        pts = [(700, 840), (650, 700), (560, 600), (430, 560)]
        k = int(len(pts) * nerve + 0.999)
        d.line(pts[:max(2, k)], fill=YELLOW, width=10, joint="curve")
        if nerve > 0.9:
            bolt(img, 360, 560, 1.0 + 0.1 * math.sin(gt * 9), col=(255, 120, 80))


def hf_c1(img, t, gt, d):
    pill(img, "GAUMEN", 540, 400, BLUE, ease_out(prog(t, 0.3, 0.3)))
    mouth_panel(img, t, gt, cold=ease_out(prog(t, 0.6, 0.6)))
    caption(img, "Das kalte Eis trifft deinen Gaumen – die Blutgefäße dort kühlen blitzschnell ab.", t,
            hl=("KALTE", "GAUMEN"))


def hf_c2(img, t, gt, d):
    tz, tw_ = W_("zusammen", fallback=0.5), W_("weiten", fallback=2.0)
    v = 1.0 - 0.6 * ease_io(prog(t, tz - 0.2, 0.6)) + 1.2 * ease_io(prog(t, tw_ - 0.1, 0.5))
    mouth_panel(img, t, gt, cold=1.0, vessel=v)
    pill(img, "ZUSAMMEN …" if t < tw_ else "… UND WIEDER WEIT!", 540, 400, RED, 1.0)
    caption(img, "Sie ziehen sich zusammen – und weiten sich gleich danach wieder stark.", t, hl=("ZUSAMMEN", "WEITEN"))


def hf_c3(img, t, gt, d):
    mouth_panel(img, t, gt, cold=1.0, vessel=1.4, nerve=ease_out(prog(t, W_("Nerv", fallback=0.4) - 0.1, 1.4)))
    pill(img, "GESICHTSNERV", 540, 400, YELLOW, ease_out(prog(t, 0.2, 0.3)))
    caption(img, "Ein Gesichtsnerv meldet das ans Gehirn – und du spürst den Schmerz in der STIRN!", t,
            hl=("STIRN!",))


def brain(img, cx, cy, s):
    d = ImageDraw.Draw(img)
    for dx, dy, rx, ry in ((-70, -10, 130, 120), (60, -40, 140, 120), (110, 40, 110, 100), (-20, 50, 160, 100)):
        d.ellipse((cx + (dx - rx) * s, cy + (dy - ry) * s, cx + (dx + rx) * s, cy + (dy + ry) * s),
                  fill=(255, 160, 190))
    rr = random.Random(2)
    for _ in range(10):
        x, y = cx + rr.uniform(-180, 180) * s, cy + rr.uniform(-100, 100) * s
        d.arc((x - 40 * s, y - 20 * s, x + 40 * s, y + 20 * s), 200, 340, fill=(215, 110, 150), width=max(2, int(6 * s)))


def hf_c4(img, t, gt, d):
    brain(img, 540, 800, 1.2)
    check(img, 820, 640, 90, ease_out(prog(t, W_("nicht", fallback=1.2) - 0.1, 0.4)))
    pill(img, "KEIN EINFRIEREN", 540, 400, GREEN, ease_out(prog(t, 0.3, 0.3)))
    caption(img, "Keine Sorge: Dein Gehirn friert NICHT ein. Meist ist es nach wenigen Sekunden vorbei.", t,
            hl=("NICHT",))


def cup(img, cx, cy, s, gt):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((cx - 80 * s, cy - 70 * s, cx + 80 * s, cy + 90 * s), int(20 * s), fill=WHITE)
    d.arc((cx + 50 * s, cy - 40 * s, cx + 130 * s, cy + 40 * s), 270, 90, fill=WHITE, width=int(16 * s))
    d.ellipse((cx - 70 * s, cy - 80 * s, cx + 70 * s, cy - 55 * s), fill=(180, 110, 60))
    for k in range(3):
        ph = (gt + k / 3) % 1
        d.arc((cx - 45 + k * 35, cy - 170 - ph * 50, cx - 10 + k * 35, cy - 100 - ph * 50), 90, 270, fill=WHITE,
              width=5)


def hf_tip(img, t, gt, d):
    pill(img, "DER TRICK", 540, 400, YELLOW, ease_out(prog(t, 0.2, 0.3)), size=48)
    head_profile(img, 380, 820, 0.85)
    dd = ImageDraw.Draw(img)
    dd.chord((420, 820, 650, 980), 180, 360, fill=(170, 60, 80))
    up = ease_io(prog(t, W_("Zunge", fallback=0.8) - 0.1, 0.6))
    dd.ellipse((440, 900 - 50 * up, 640, 980 - 50 * up), fill=(255, 120, 140))
    dd.line((540, 1000, 540, 900 - 40 * up), fill=YELLOW, width=10)
    dd.polygon([(515, 930 - 40 * up), (565, 930 - 40 * up), (540, 890 - 40 * up)], fill=YELLOW)
    p = back_out(prog(t, W_("Warmes", fallback=2.2) - 0.2, 0.5))
    if p > 0.03:
        cup(img, 840, 850, p, gt)
    caption(img, "Zunge fest gegen den Gaumen drücken – oder etwas Warmes trinken!", t, hl=("ZUNGE", "WARMES"))


# ------------------------------------------------------------------ SHORT: Ohren im Flugzeug
def plane(img, cx, cy, s, ang=0):
    sp = E.SS(520 * s, 220 * s)
    c = (240, 242, 250, 255)
    sp.rect(30 * s, 80 * s, 470 * s, 140 * s, 30 * s, c)
    sp.poly([(440 * s, 85 * s), (515 * s, 20 * s), (490 * s, 100 * s)], (235, 60, 80, 255))
    sp.poly([(200 * s, 110 * s), (300 * s, 110 * s), (230 * s, 210 * s), (180 * s, 210 * s)], (200, 205, 220, 255))
    for k in range(6):
        sp.ell(90 * s + k * 45 * s, 100 * s, 9 * s, 9 * s, (90, 160, 255, 255))
    paste_c(img, sp.img().rotate(ang, resample=Image.BICUBIC, expand=True), cx, cy)


def ear_panel(img, t, gt, push=0.0, tube=0.0, a=1.0):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((90, 760, 470, 860), 50, fill=(255, 200, 170))              # ear canal
    d.ellipse((560, 690, 820, 930), fill=(255, 230, 220), outline=(220, 150, 150), width=6)   # middle ear
    bend = 50 * push
    d.arc((470 - bend, 700, 560 + bend * 0.2, 920), -70, 70, fill=(255, 110, 130), width=16)  # drum
    if tube > 0.02:
        d.line([(700, 920), (740, 1040), (820, 1130)], fill=(255, 190, 180), width=int(10 + 30 * tube), joint="curve")
        text(img, "OHRTROMPETE", 32, 900, 1000, fill=WHITE, path=FONT_XB, stroke=4, sfill=NAVY, alpha=tube)
        text(img, "→ RACHEN", 32, 900, 1045, fill=WHITE, path=FONT_XB, stroke=4, sfill=NAVY, alpha=tube)
    text(img, "TROMMELFELL", 30, 515, 650, fill=YELLOW, path=FONT_XB, stroke=4, sfill=NAVY, alpha=a)
    text(img, "LUFT", 34, 690, 810, fill=NAVY, path=FONT_XB, alpha=a)
    if push > 0.05:
        for k in range(3):
            x = 150 + ((gt * 200 + k * 100) % 260)
            d.line((x, 810, x + 50, 810), fill=WHITE, width=8)
            d.polygon([(x + 50, 795), (x + 50, 825), (x + 72, 810)], fill=WHITE)


def oh_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    k = (t * 0.25) % 1
    plane(img, 300 + 500 * k, 560 + 260 * k, 1.0, ang=-14)
    dd = ImageDraw.Draw(img)
    dd.rectangle((0, 1000, W, 1060), fill=(90, 100, 120))
    for x in range(40, W, 140):
        dd.rectangle((x, 1022, x + 70, 1036), fill=WHITE)
    q = 1 + 0.1 * math.sin(gt * 6)
    text(img, "?", 200 * q, 170, 760, fill=YELLOW, stroke=10, sfill=NAVY, rotate=-10, alpha=ease_out(prog(t, 0.5, 0.3)))
    caption(img, "Rate mal, was passiert, wenn ein Flugzeug landet!", t, hl=("RATE", "MAL,", "LANDET!"))


def oh_c1(img, t, gt, d):
    pill(img, "IM OHR", 540, 400, BLUE, ease_out(prog(t, 0.2, 0.3)))
    ear_panel(img, t, gt)
    caption(img, "Hinter deinem Trommelfell sitzt ein kleiner Raum voller Luft.", t, hl=("TROMMELFELL", "LUFT."))


def gauge(img, cx, cy, r, frac, lab):
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE, outline=NAVY, width=8)
    an = math.pi * (0.8 + 1.4 * frac)
    d.line((cx, cy, cx + 0.8 * r * math.cos(an), cy + 0.8 * r * math.sin(an)), fill=RED, width=10)
    d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=NAVY)
    text(img, lab, 34, cx, cy + r + 40, fill=WHITE, path=FONT_XB, stroke=4, sfill=NAVY)


def oh_c2(img, t, gt, d):
    k = ease_io(prog(t, 0.3, 3.5))
    plane(img, 330 + 160 * k, 640 + 180 * k, 0.9, ang=-12)
    gauge(img, 800, 900, 120, k, "DRUCK IN DER KABINE")
    pill(img, "SINKFLUG", 540, 400, YELLOW, ease_out(prog(t, 0.2, 0.3)))
    caption(img, "Beim Sinkflug steigt der Luftdruck in der Kabine – und drückt auf dein Trommelfell.", t,
            hl=("STEIGT", "TROMMELFELL."))


def oh_c3(img, t, gt, d):
    ear_panel(img, t, gt, push=ease_out(prog(t, W_("wölbt", fallback=0.3) - 0.3, 0.8)))
    ta = W_("Druck", fallback=1.2)
    if t > ta:
        pill(img, "AUA!", 540, 400, RED, ease_out(prog(t, ta, 0.3)), size=56)
    caption(img, "Die Luft dahinter kommt nicht hinterher: Das Trommelfell wölbt sich nach innen – das drückt!", t,
            hl=("INNEN",))


def oh_c4(img, t, gt, d):
    op = ease_out(prog(t, W_("Ohrtrompete", fallback=0.6) - 0.2, 0.6))
    ear_panel(img, t, gt, push=1 - op, tube=op)
    tp = W_("Plopp", fallback=1.6)
    if t > tp - 0.05:
        stamp(img, "PLOPP!", t, tp - 0.05, 540, 400, size=150, rot=-6)
    caption(img, "Die Ohrtrompete öffnet sich, der Druck gleicht sich aus – PLOPP!", t, hl=("OHRTROMPETE", "PLOPP!"))


def gum(img, cx, cy, s, gt):
    d = ImageDraw.Draw(img)
    r = 110 * s * (1 + 0.15 * math.sin(gt * 3))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 140, 200), outline=NAVY, width=6)
    d.ellipse((cx - r * 0.5, cy - r * 0.6, cx - r * 0.2, cy - r * 0.3), fill=(255, 220, 240))


def oh_tip(img, t, gt, d):
    pill(img, "SO HILFST DU NACH", 540, 400, YELLOW, ease_out(prog(t, 0.2, 0.3)), size=44)
    items = [("SCHLUCKEN", W_("Schlucken", fallback=0.4) - 0.1), ("GÄHNEN", W_("Gähnen", fallback=1.1) - 0.1),
             ("KAUGUMMI", W_("Kaugummi", fallback=1.8) - 0.1)]
    for k, (lab, t0) in enumerate(items):
        p = back_out(prog(t, t0, 0.45))
        if p > 0.03:
            y = 640 + k * 160
            check(img, 260, y, 50, min(1, p))
            text(img, lab, 64 * min(1.1, p), 560, y, fill=WHITE, stroke=7, sfill=NAVY)
    tg = W_("Kaugummi", fallback=2.0) + 0.3
    if t > tg:
        gum(img, 870, 800, back_out(prog(t, tg, 0.5)), gt)
    caption(img, "Schlucken, gähnen oder Kaugummi kauen. Babys hilft Trinken beim Landen.", t,
            hl=("SCHLUCKEN,", "GÄHNEN", "KAUGUMMI"))


# ------------------------------------------------------------------ SHORT: Gänsehaut
def arm(img, cx, cy, bumps, gt):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((cx - 380, cy - 90, cx + 380, cy + 90), 90, fill=SKIN)
    rr = random.Random(3)
    for k in range(28):
        x, y = cx + rr.uniform(-340, 340), cy + rr.uniform(-60, 60)
        r = 10 * bumps
        if r > 1:
            d.ellipse((x - r, y - r, x + r, y + r), fill=(240, 180, 140))
        d.line((x, y, x + 8, y - 26 - 20 * bumps), fill=(120, 80, 60), width=3)


def skin_panel(img, t, gt, contract=0.0, label=1.0):
    d = ImageDraw.Draw(img)
    top = 760
    bump = 40 * contract
    pts = [(x, top - bump * math.exp(-((x - 540) / 90) ** 2)) for x in range(140, 941, 10)]
    d.polygon(pts + [(940, 1180), (140, 1180)], fill=(255, 205, 165))
    d.line(pts, fill=(200, 120, 90), width=8)
    # follicle + hair
    d.line((540, top + 220, 540, top - bump), fill=(150, 100, 80), width=14)
    ang = math.radians(60 - 55 * contract)
    hx, hy = 540 + 230 * math.cos(ang), top - bump - 230 * math.sin(ang)
    d.line((540, top - bump, hx, hy), fill=(90, 60, 45), width=10)
    # arrector pili muscle
    mw = 26 + 18 * contract
    d.line((560, top + 180, 760 - 60 * contract, top + 40), fill=(220, 60, 80), width=int(mw))
    text(img, "MUSKEL", 34, 800, top + 160, fill=(255, 130, 140), path=FONT_XB, stroke=4, sfill=NAVY, alpha=label)
    text(img, "HAAR", 34, 760, top - 230, fill=YELLOW, path=FONT_XB, stroke=4, sfill=NAVY, alpha=label)


def gh_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    arm(img, 540, 820, ease_out(prog(t, 1.2, 0.8)), gt)
    q = 1 + 0.1 * math.sin(gt * 6)
    text(img, "?", 200 * q, 880, 560, fill=YELLOW, stroke=10, sfill=NAVY, rotate=10, alpha=ease_out(prog(t, 0.5, 0.3)))
    caption(img, "Rate mal, was passiert, wenn du Gänsehaut bekommst!", t, hl=("RATE", "MAL,", "GÄNSEHAUT"))


def gh_c1(img, t, gt, d):
    pill(img, "UNTER DER HAUT", 540, 400, BLUE, ease_out(prog(t, 0.2, 0.3)))
    skin_panel(img, t, gt, label=ease_out(prog(t, 0.8, 0.4)))
    caption(img, "An jedem Haar sitzt ein winziger Muskel.", t, hl=("MUSKEL.",))


def snow(img, cx, cy, gt):
    d = ImageDraw.Draw(img)
    for k in range(3):
        an = k * math.pi / 3 + gt
        d.line((cx - 40 * math.cos(an), cy - 40 * math.sin(an), cx + 40 * math.cos(an), cy + 40 * math.sin(an)),
               fill=(180, 230, 255), width=8)


def gh_c2(img, t, gt, d):
    c = ease_io(prog(t, W_("zusammen", fallback=1.0) - 0.3, 0.6))
    skin_panel(img, t, gt, contract=c)
    snow(img, 220, 600, gt)
    na = ease_out(prog(t, 0.6, 0.3))
    if na > 0.02:
        dn = ImageDraw.Draw(img)
        dn.ellipse((830, 620, 880, 660), fill=YELLOW)
        dn.line((875, 640, 875, 530), fill=YELLOW, width=10)
        dn.line((875, 530, 920, 560), fill=YELLOW, width=10)
    pill(img, "KÄLTE · ANGST · GÄNSEHAUT-MUSIK", 540, 400, YELLOW, ease_out(prog(t, 0.2, 0.3)), size=34)
    caption(img, "Bei Kälte oder starken Gefühlen zieht er sich zusammen – das Haar stellt sich auf.", t,
            hl=("ZUSAMMEN", "AUF."))


def gh_c3(img, t, gt, d):
    arm(img, 540, 800, 1.0, gt)
    stamp(img, "GÄNSEHAUT!", t, W_("Gänsehaut", fallback=0.4) - 0.1, 540, 400, size=120, rot=-5)
    caption(img, "Um jedes Haar wölbt sich die Haut – fertig sind die kleinen Hügel.", t, hl=("HÜGEL.",))


def cat(img, cx, cy, fluff, gt):
    d = ImageDraw.Draw(img)
    r = 150 * (1 + 0.35 * fluff)
    rr = random.Random(4)
    for k in range(40):
        an = k / 40 * 2 * math.pi
        rad = r * (1 + 0.12 * fluff * rr.random())
        d.line((cx, cy, cx + rad * math.cos(an), cy + rad * 0.8 * math.sin(an)), fill=(70, 70, 80), width=14)
    d.ellipse((cx - 150, cy - 120, cx + 150, cy + 120), fill=(60, 60, 70))
    d.polygon([(cx - 130, cy - 90), (cx - 100, cy - 190), (cx - 50, cy - 110)], fill=(60, 60, 70))
    d.polygon([(cx + 130, cy - 90), (cx + 100, cy - 190), (cx + 50, cy - 110)], fill=(60, 60, 70))
    for k in (-1, 1):
        d.ellipse((cx + k * 55 - 22, cy - 40, cx + k * 55 + 22, cy + 4), fill=YELLOW)
        d.ellipse((cx + k * 55 - 6, cy - 34, cx + k * 55 + 6, cy - 2), fill=(20, 20, 20))


def gh_c4(img, t, gt, d):
    f = ease_out(prog(t, W_("aufgeplusterte", fallback=0.6) - 0.2, 0.6))
    cat(img, 540, 820, f, gt)
    pill(img, "ERBE UNSERER VORFAHREN", 540, 400, YELLOW, ease_out(prog(t, 0.2, 0.3)), size=38)
    caption(img, "Ein Erbe unserer Vorfahren: Aufgeplustertes Fell hält warm – und lässt Tiere größer wirken.", t,
            hl=("WARM", "GRÖSSER"))


# ------------------------------------------------------------------ outro (shared)
def outro(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    p = back_out(prog(t, 0.1, 0.5))
    if p > 0.05:
        cx, cy, bw, bh = 540, 700, 400 * p, 170 * p
        E.rrect(img, (cx - bw, cy - bh, cx + bw, cy + bh), 50, (255, 255, 255, 245))
        ImageDraw.Draw(img).polygon([(cx - 60 * p, cy + bh - 2), (cx - 130 * p, cy + bh + 80 * p),
                                     (cx + 10 * p, cy + bh - 2)], fill=(255, 255, 255))
        text(img, "Hättest du's gewusst?", 56 * p, cx, cy - 50, fill=(40, 40, 70))
        text(img, "Ja / Nein", 70 * p, cx, cy + 60, fill=(255, 120, 0))
    tr = W_("Kommentare", fallback=1.0) + 0.5
    if t > tr:
        stamp(img, "RATE MAL!", t, tr, 540, 1000, size=150, rot=-6)
        E.confetti(img, t, tr)
    caption(img, "Schreib's in die Kommentare!", t, hl=("KOMMENTARE!",), start=1.4)


SHORTS = {
    "hirnfrost": dict(bg=((10, 40, 90), (60, 130, 200)), out="hirnfrost_eis.mp4",
                      scenes=[(hf_hook, 4.4, "Rate mal, was passiert, wenn du Eis zu schnell isst!"),
                              (hf_c1, 5.2, "Das kalte Eis trifft deinen Gaumen – die Blutgefäße dort kühlen blitzschnell ab."),
                              (hf_c2, 4.6, "Sie ziehen sich zusammen – und weiten sich gleich danach wieder stark."),
                              (hf_c3, 5.4, "Ein Gesichtsnerv meldet das ans Gehirn – und du spürst den Schmerz in der STIRN!"),
                              (hf_c4, 5.4, "Keine Sorge: Dein Gehirn friert NICHT ein. Meist ist es nach wenigen Sekunden vorbei."),
                              (hf_tip, 4.8, "Zunge fest gegen den Gaumen drücken – oder etwas Warmes trinken!"),
                              (outro, 4.0, "")]),
    "ohren": dict(bg=((20, 30, 80), (90, 60, 150)), out="ohren_flugzeug.mp4",
                  scenes=[(oh_hook, 4.0, "Rate mal, was passiert, wenn ein Flugzeug landet!"),
                          (oh_c1, 4.2, "Hinter deinem Trommelfell sitzt ein kleiner Raum voller Luft."),
                          (oh_c2, 5.2, "Beim Sinkflug steigt der Luftdruck in der Kabine – und drückt auf dein Trommelfell."),
                          (oh_c3, 5.6, "Die Luft dahinter kommt nicht hinterher: Das Trommelfell wölbt sich nach innen – das drückt!"),
                          (oh_c4, 4.8, "Die Ohrtrompete öffnet sich, der Druck gleicht sich aus – PLOPP!"),
                          (oh_tip, 5.0, "Schlucken, gähnen oder Kaugummi kauen. Babys hilft Trinken beim Landen."),
                          (outro, 4.0, "")]),
    "gaensehaut": dict(bg=((50, 15, 60), (140, 50, 90)), out="gaensehaut.mp4",
                       scenes=[(gh_hook, 4.0, "Rate mal, was passiert, wenn du Gänsehaut bekommst!"),
                               (gh_c1, 3.6, "An jedem Haar sitzt ein winziger Muskel."),
                               (gh_c2, 5.2, "Bei Kälte oder starken Gefühlen zieht er sich zusammen – das Haar stellt sich auf."),
                               (gh_c3, 4.2, "Um jedes Haar wölbt sich die Haut – fertig sind die kleinen Hügel."),
                               (gh_c4, 5.6, "Ein Erbe unserer Vorfahren: Aufgeplustertes Fell hält warm – und lässt Tiere größer wirken."),
                               (outro, 4.0, "")]),
}

CUR = {}


def init(name):
    spec = SHORTS[name]
    CUR["name"] = name
    CUR.clear()
    CUR.update(spec)
    CUR["BG"] = make_bg(*spec["bg"])
    t, segs = 0.0, []
    import json as _json
    for i, (fn, dur, cap) in enumerate(spec["scenes"]):
        key = "outro" if fn is outro else f"{name}_{i}"
        mp3 = os.path.join(HERE, "audio", key + ".mp3")
        seg = dict(fn=fn, start=t, cap=cap)
        if os.path.exists(mp3):
            ws = _json.load(open(os.path.join(HERE, "audio", key + ".words.json")))["words"]
            pre = 0.25
            seg["words"] = [(w["text"], w["start"] + pre, w["end"] + pre) for w in ws]
            seg["mp3"], seg["pre"] = mp3, pre
            dur = pre + ws[-1]["end"] + (1.8 if fn is outro else 0.55)
        else:
            dur = max(dur, 0.25 + len(cap.split()) / WPS + 1.4)
        seg["dur"] = dur
        segs.append(seg)
        t += dur
    CUR["segs"], CUR["total"] = segs, t


def seg_at(gt):
    for s in CUR["segs"]:
        if gt < s["start"] + s["dur"]:
            return s
    return CUR["segs"][-1]


def render_frame(fi):
    gt = fi / FPS
    s = seg_at(gt)
    t = gt - s["start"]
    img = CUR["BG"].copy()
    SEG.clear()
    SEG.update(s)
    s["fn"](img, t, gt, None)
    if t < 0.25 and s is not CUR["segs"][0]:
        prev = CUR["segs"][CUR["segs"].index(s) - 1]
        pimg = CUR["BG"].copy()
        SEG.clear()
        SEG.update(prev)
        prev["fn"](pimg, prev["dur"] - 0.01, prev["start"] + prev["dur"] - 0.01, None)
        img = Image.blend(pimg, img, ease_io(t / 0.25))
    return img.convert("RGB")


def render_bytes(fi):
    return render_frame(fi).tobytes()


def seg_word(sg, word, fallback):
    for tx, st, en in sg.get("words", []):
        if tx.strip(".,!?:;").lower() == word.lower():
            return st
    return fallback


def events():
    ev = []
    keys = {hf_c3: ("Stirn", "thump"), oh_c4: ("Plopp", "thump"), gh_c3: ("Gänsehaut", "thump"),
            hf_c4: ("nicht", "ding"), oh_tip: ("Kaugummi", "ding"), hf_c2: ("weiten", "pop"),
            oh_c3: ("wölbt", "pop"), gh_c2: ("zusammen", "pop"), gh_c4: ("aufgeplusterte", "pop"),
            hf_tip: ("Warmes", "pop")}
    for i, s in enumerate(CUR["segs"]):
        st = s["start"]
        if i > 0:
            ev += [(st - 0.1, "whoosh", 0.10)]
        ev += [(st + 0.3, "pop", 0.08)]
        if not s.get("words"):
            for k, tt in enumerate(word_times(s["cap"])):
                if k % 3 == 0:
                    ev.append((st + tt, "tick", 0.05))
        if s["fn"] in keys:
            w, kind = keys[s["fn"]]
            ev.append((st + seg_word(s, w, 1.0) - 0.05, kind, 0.14 if kind == "thump" else 0.10))
        if s["fn"] is outro:
            tr = seg_word(s, "Kommentare", 1.0) + 0.5
            ev += [(st + tr, "chime", 0.12), (st + tr, "thump", 0.12)]
    return ev


def make(name):
    init(name)
    LL.TOTAL = CUR["total"]
    mix = LL.synth(events())
    voiced = any(sg.get("mp3") for sg in CUR["segs"])
    if voiced:
        voice = np.zeros(len(mix))
        for sg in CUR["segs"]:
            if not sg.get("mp3"):
                continue
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sg["mp3"], "-f", "s16le", "-ac", "1", "-ar", str(SR),
                                  "-"], capture_output=True, check=True).stdout
            v = np.frombuffer(raw, dtype=np.int16) / 32768.0
            a0 = int((sg["start"] + sg["pre"]) * SR)
            b0 = min(len(voice), a0 + len(v))
            voice[a0:b0] += v[:b0 - a0] / (np.abs(v).max() + 1e-9) * 0.89
        mix = np.clip(voice + mix * 1.2, -0.98, 0.98)
    else:
        mix = np.clip(mix * 2.2, -0.98, 0.98)   # louder music bed: no voice
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    wav = os.path.join(HERE, "build", f"{name}.wav")
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((mix[:int(CUR["total"] * SR)] * 32767).astype(np.int16).tobytes())
    tmp = os.path.join(HERE, "build", f"{name}_tmp.mp4")
    nfr = int(math.ceil(CUR["total"] * FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                           f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium",
                           "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                           "-ac", "2", "-movflags", "+faststart", "-shortest", tmp], stdin=subprocess.PIPE)
    with Pool(4, initializer=init, initargs=(name,)) as pool:
        for k0 in range(0, nfr, 48):
            for b in pool.map(render_bytes, range(k0, min(nfr, k0 + 48)), chunksize=4):
                ff.stdin.write(b)
    ff.stdin.close()
    ff.wait()
    r = subprocess.run(["ffmpeg", "-nostats", "-i", tmp, "-af", "ebur128", "-f", "null", "-"], capture_output=True,
                       text=True).stderr
    lufs = float([ln for ln in r.splitlines() if ln.strip().startswith("I:")][-1].split()[1])
    out = os.path.join(HERE, CUR["out"])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:v", "copy", "-af",
                    f"volume={-14 - lufs:.2f}dB,alimiter=limit=0.84:level=false", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", out], check=True)
    os.remove(tmp)
    print("wrote", out, round(CUR["total"], 1), "s")


def stills(name):
    init(name)
    qc = os.path.join(HERE, "qc")
    os.makedirs(qc, exist_ok=True)
    for s in CUR["segs"]:
        gt = s["start"] + s["dur"] * 0.85
        render_frame(int(gt * FPS)).save(os.path.join(qc, f"{name}_{gt:05.1f}.png"))


if __name__ == "__main__":
    names = [a for a in ARGS if not a.startswith("--")] or list(SHORTS)
    for nm in names:
        stills(nm) if "--stills" in ARGS else make(nm)

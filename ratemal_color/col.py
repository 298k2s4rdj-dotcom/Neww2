"""Colourful flat-shape helpers for full-frame "Rate mal, was passiert, wenn …" shorts (Blauwal-video look).

Builds on tiere/engine.py (starry gradient background, word-synced subtitles, stamps, bursts, confetti, counters).
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tiere"))
import engine as E  # noqa: E402
from engine import (SS, back_out, clamp, ease_io, ease_out, paste_c, prog, rrect, text, wt, FONT_XB,  # noqa: E402
                    C_HI)

E.header = lambda *a, **k: None          # no scoreboard in this format

ORANGE = (255, 150, 70)
SKIN = (255, 196, 150)
RED = (235, 40, 70)
BLUE = (70, 160, 255)
GREEN = (90, 220, 120)
WHITE = (255, 255, 255)
PURPLE = (170, 120, 255)
YELLOW = C_HI


def pill(img, s, cx, cy, col=WHITE, a=1.0, size=40, bg=(15, 20, 40)):
    if a <= 0.02:
        return
    w = E.text_w(s, size, FONT_XB) + 50
    rrect(img, (cx - w / 2, cy - size * 0.85, cx + w / 2, cy + size * 0.85), int(size * 0.85),
          bg + (int(225 * a),), outline=col + (int(255 * a),), width=4)
    text(img, s, size, cx, cy, fill=col, alpha=a, path=FONT_XB)


def cross(img, cx, cy, r, a=1.0, col=RED, w=26):
    if a <= 0.02:
        return
    d = ImageDraw.Draw(img)
    k = r * a
    d.line((cx - k, cy - k, cx + k, cy + k), fill=col, width=w)
    d.line((cx - k, cy + k, cx + k, cy - k), fill=col, width=w)


def check(img, cx, cy, r, a=1.0, col=GREEN, w=26):
    if a <= 0.02:
        return
    d = ImageDraw.Draw(img)
    p1 = (cx - r * 0.7, cy)
    p2 = (cx - r * 0.2, cy + r * 0.5)
    p3 = (cx + r * 0.8, cy - r * 0.6)
    if a < 0.5:
        q = a / 0.5
        d.line((p1[0], p1[1], p1[0] + (p2[0] - p1[0]) * q, p1[1] + (p2[1] - p1[1]) * q), fill=col, width=w)
    else:
        q = (a - 0.5) / 0.5
        d.line((p1, p2), fill=col, width=w)
        d.line((p2[0], p2[1], p2[0] + (p3[0] - p2[0]) * q, p2[1] + (p3[1] - p2[1]) * q), fill=col, width=w)


def ring(img, cx, cy, r, frac, col, label, sub=None, a=1.0):
    if a <= 0.02:
        return
    lay = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, int(60 * a)), width=22)
    if frac > 0:
        d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * min(1, frac), fill=col + (int(255 * a),),
              width=22)
    img.paste(lay, (0, 0), lay)
    text(img, label, r * 0.55, cx, cy - (12 if sub else 0), alpha=a, stroke=6)
    if sub:
        text(img, sub, 34, cx, cy + r * 0.38, fill=col, alpha=a, stroke=4, path=FONT_XB)


def cloud(img, cx, cy, s=1.0, col=(150, 155, 175)):
    sp = SS(420 * s, 220 * s)
    for dx, dy, r in ((110, 130, 80), (200, 100, 100), (300, 130, 80), (200, 150, 90)):
        sp.ell(dx * s, dy * s, r * s, r * s, col + (255,))
    paste_c(img, sp.img(), cx, cy)


def bolt(img, x0, y0, x1, y1, seed=1, w=14, col=(255, 240, 120), a=1.0):
    if a <= 0.02:
        return
    r = random.Random(seed)
    n = 9
    pts = []
    for k in range(n + 1):
        f = k / n
        jit = 0 if k in (0, n) else r.uniform(-45, 45)
        pts.append((x0 + (x1 - x0) * f + jit, y0 + (y1 - y0) * f))
    lay = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(lay)
    d.line(pts, fill=(200, 180, 255, int(110 * a)), width=w * 4, joint="curve")
    d.line(pts, fill=col + (int(255 * a),), width=w, joint="curve")
    d.line(pts, fill=(255, 255, 255, int(255 * a)), width=max(2, w // 3), joint="curve")
    img.paste(lay, (0, 0), lay)


def bubbles(img, cx, cy, gt, n=10, spread=200, rise=420, seed=0, col=(200, 235, 255)):
    d = ImageDraw.Draw(img)
    rr = random.Random(seed)
    for k in range(n):
        x0 = cx + rr.uniform(-spread, spread)
        sp = rr.uniform(60, 120)
        y = cy - ((gt * sp + rr.uniform(0, rise)) % rise)
        rad = rr.uniform(6, 16)
        d.ellipse((x0 - rad, y - rad, x0 + rad, y + rad), outline=col, width=3)


def duck(s=1.0):
    sp = SS(220 * s, 180 * s)
    sp.ell(110 * s, 120 * s, 90 * s, 52 * s, (255, 214, 40, 255))
    sp.ell(150 * s, 62 * s, 44 * s, 44 * s, (255, 214, 40, 255))
    sp.poly([(186 * s, 60 * s), (218 * s, 70 * s), (186 * s, 82 * s)], (255, 140, 30, 255))
    sp.ell(160 * s, 52 * s, 7 * s, 7 * s, (30, 30, 40, 255))
    sp.ell(80 * s, 110 * s, 40 * s, 22 * s, (255, 190, 30, 255))
    return sp.img()


def hand(wrinkle=0.0, s=1.0, smooth_finger=None, col=SKIN):
    """flat cartoon hand, fingers up; wrinkle 0..1 draws ridges on the fingertips"""
    W_, H_ = 420 * s, 560 * s
    sp = SS(W_, H_)
    sp.rect(70 * s, 260 * s, 350 * s, 540 * s, 70 * s, col + (255,))
    fingers = [(95, 70), (165, 30), (235, 40), (305, 90)]
    for i, (fx, top) in enumerate(fingers):
        sp.rect((fx - 32) * s, top * s, (fx + 32) * s, 330 * s, 32 * s, col + (255,))
    sp.thick([(80 * s, 430 * s), (20 * s, 330 * s), (10 * s, 260 * s)], [70 * s, 62 * s, 56 * s], col + (255,))
    img = sp.img()
    d = ImageDraw.Draw(img)
    if wrinkle > 0.02:
        for i, (fx, top) in enumerate(fingers):
            if smooth_finger is not None and i == smooth_finger:
                continue
            for k in range(5):
                y = (top + 30 + k * 18) * s
                amp = 6 * s * wrinkle
                pts = [((fx - 24 + j * 6) * s, y + amp * math.sin(j * 1.6 + k)) for j in range(9)]
                d.line(pts, fill=(200, 120, 90, int(255 * min(1, wrinkle * 1.4))), width=max(2, int(4 * s)))
    return img


def house(img, cx, cy, s=1.0):
    sp = SS(260 * s, 240 * s)
    sp.poly([(10 * s, 110 * s), (130 * s, 10 * s), (250 * s, 110 * s)], (235, 90, 70, 255))
    sp.rect(35 * s, 105 * s, 225 * s, 235 * s, 6 * s, (240, 220, 180, 255))
    sp.rect(105 * s, 160 * s, 155 * s, 235 * s, 4 * s, (140, 90, 60, 255))
    sp.rect(55 * s, 130 * s, 95 * s, 170 * s, 4 * s, (120, 190, 255, 255))
    paste_c(img, sp.img(), cx, cy)


def car(img, cx, cy, s=1.0):
    sp = SS(300 * s, 160 * s)
    sp.rect(10 * s, 60 * s, 290 * s, 120 * s, 20 * s, (70, 160, 255, 255))
    sp.poly([(70 * s, 62 * s), (110 * s, 15 * s), (210 * s, 15 * s), (245 * s, 62 * s)], (70, 160, 255, 255))
    sp.poly([(95 * s, 58 * s), (120 * s, 26 * s), (200 * s, 26 * s), (225 * s, 58 * s)], (190, 230, 255, 255))
    for x in (70, 230):
        sp.ell(x * s, 125 * s, 28 * s, 28 * s, (40, 40, 50, 255))
    paste_c(img, sp.img(), cx, cy)


def tree(img, cx, cy, s=1.0):
    sp = SS(240 * s, 320 * s)
    sp.rect(100 * s, 180 * s, 140 * s, 320 * s, 8 * s, (140, 90, 50, 255))
    for dx, dy, r in ((120, 100, 95), (70, 150, 70), (170, 150, 70)):
        sp.ell(dx * s, dy * s, r * s, r * s, (60, 170, 80, 255))
    paste_c(img, sp.img(), cx, cy)


def lungs(s=1.0, col=(255, 130, 160), puff=1.0):
    sp = SS(300 * s, 300 * s)
    sp.rect(140 * s, 10 * s, 160 * s, 120 * s, 8 * s, (230, 230, 240, 255))
    for sx in (-1, 1):
        cx = 150 + sx * 70
        sp.ell(cx * s, 170 * s, 62 * s * puff, 115 * s * puff, col + (255,))
    return sp.img()


def thermometer(img, cx, top, bot, frac, col):
    rrect(img, (cx - 26, top - 6, cx + 26, bot + 6), 26, (255, 255, 255, 230))
    rrect(img, (cx - 14, top + 8 + (bot - top - 16) * (1 - frac), cx + 14, bot), 14, col + (255,))
    d = ImageDraw.Draw(img)
    d.ellipse((cx - 44, bot - 20, cx + 44, bot + 68), fill=(255, 255, 255))
    d.ellipse((cx - 32, bot - 8, cx + 32, bot + 56), fill=col)

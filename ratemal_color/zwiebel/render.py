#!/usr/bin/env python3
"""Rate mal, was passiert, wenn du eine Zwiebel schneidest? – colourful full-frame Short."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import col as C  # noqa: E402
from col import E, prog, ease_out, ease_io, back_out, paste_c, text, wt, FONT_XB  # noqa: E402

NAVY = (40, 20, 60)
GAS = (190, 230, 90)
_c = {}


def ap(sc, t, word, n=1, d=0.3, off=-0.1):
    try:
        return ease_out(prog(t, wt(sc, word, n) + off, d))
    except KeyError:
        return 0.0


def onion(r, half=False):
    k = ("onion", r, half)
    if k in _c:
        return _c[k]
    s = E.SS(2.4 * r, 2.8 * r)
    cx, cy = 1.2 * r, 1.55 * r
    if not half:
        s.poly([(cx - 0.18 * r, cy - 0.85 * r), (cx, cy - 1.45 * r), (cx + 0.18 * r, cy - 0.85 * r)],
               (120, 170, 80, 255))
        s.ell(cx, cy, r, r * 1.0, (190, 100, 150, 255))
        for k2 in (-0.55, -0.2, 0.2, 0.55):
            s.line([(cx + k2 * r * 0.9, cy - 0.85 * r), (cx + k2 * r * 1.15, cy), (cx + k2 * r * 0.9, cy + 0.85 * r)],
                   (230, 160, 200, 255), r * 0.04)
        for k2 in range(5):
            s.line([(cx - 0.2 * r + k2 * 0.1 * r, cy + 0.95 * r), (cx - 0.3 * r + k2 * 0.15 * r, cy + 1.2 * r)],
                   (200, 180, 150, 255), r * 0.03)
    else:
        s.ell(cx, cy, r, r, (190, 100, 150, 255))
        for k2 in range(6, 0, -1):
            rr = r * k2 / 6.5
            s.ell(cx, cy, rr, rr, (245, 225, 235, 255) if k2 % 2 else (225, 190, 215, 255))
    img = s.img()
    _c[k] = img
    return img


def knife(img, cx, cy, ang, s=1.0):
    sp = E.SS(420 * s, 90 * s)
    sp.poly([(10 * s, 45 * s), (270 * s, 20 * s), (270 * s, 70 * s), (40 * s, 70 * s)], (225, 230, 240, 255))
    sp.rect(265 * s, 25 * s, 410 * s, 65 * s, 18 * s, (70, 45, 35, 255))
    paste_c(img, sp.img().rotate(ang, resample=Image.BICUBIC, expand=True), cx, cy)


def eye(img, cx, cy, r, tear=0.0, red=0.0, gt=0.0):
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r * 0.6, cx + r, cy + r * 0.6), fill=(255, int(255 - 70 * red), int(255 - 70 * red)),
              outline=NAVY, width=8)
    d.ellipse((cx - r * 0.38, cy - r * 0.38, cx + r * 0.38, cy + r * 0.38), fill=(80, 140, 220))
    d.ellipse((cx - r * 0.18, cy - r * 0.18, cx + r * 0.18, cy + r * 0.18), fill=NAVY)
    d.ellipse((cx - r * 0.3, cy - r * 0.3, cx - r * 0.12, cy - r * 0.12), fill=(255, 255, 255))
    if tear > 0.02:
        rr = random.Random(2)
        for k in range(6):
            ph = (gt * 0.9 + k / 6) % 1
            x = cx - r * 0.5 + rr.uniform(0, r)
            y = cy + r * 0.55 + ph * 420 * tear
            d.ellipse((x - 14, y - 20, x + 14, y + 16), fill=(120, 200, 255))


def gas(img, x0, y0, x1, y1, gt, a):
    d = ImageDraw.Draw(img)
    rr = random.Random(9)
    for k in range(14):
        ph = (gt * 0.45 + rr.random()) % 1
        x = x0 + (x1 - x0) * ph + 40 * math.sin(gt * 2 + k)
        y = y0 + (y1 - y0) * ph
        r = 22 + 18 * ph
        col = GAS + (int(200 * a * (1 - 0.5 * ph)),)
        lay = Image.new("RGBA", (int(2 * r), int(2 * r)))
        ImageDraw.Draw(lay).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=col)
        img.paste(lay, (int(x - r), int(y - r)), lay)


def crying_face(img, cx, cy, r, gt, a=1.0):
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 210, 90), outline=NAVY, width=8)
    for k in (-1, 1):
        d.arc((cx + k * r * 0.38 - 30, cy - r * 0.2 - 18, cx + k * r * 0.38 + 30, cy - r * 0.2 + 18), 200, 340,
              fill=NAVY, width=8)
        for j in range(3):
            ph = (gt * 1.2 + j / 3) % 1
            y = cy - r * 0.1 + ph * r * 1.3
            d.ellipse((cx + k * r * 0.38 - 12, y - 16, cx + k * r * 0.38 + 12, y + 12), fill=(110, 190, 255))
    d.arc((cx - r * 0.35, cy + r * 0.3, cx + r * 0.35, cy + r * 0.75), 200, 340, fill=NAVY, width=8)


def sc_hook(img, sc, t, gt):
    E.brand(img, t, gt, y=300)
    paste_c(img, onion(200), 540, 900, ease_out(prog(t, 0.0, 0.3)))
    cut = (gt * 1.6) % 1
    knife(img, 600, 700 + 260 * ease_io(min(1, cut * 1.5)), -8)
    pw = ap(sc, t, "weinen")
    if pw > 0.02:
        crying_face(img, 830, 560, 110 * back_out(prog(t, wt(sc, "weinen") - 0.1, 0.4)), gt)
    q = 1 + 0.1 * math.sin(gt * 6)
    text(img, "?", 230 * q, 230, 620, fill=C.YELLOW, stroke=10, sfill=NAVY, rotate=-10,
         alpha=ease_out(prog(t, 0.4, 0.3)))


def sc_cells(img, sc, t, gt):
    t_s, t_z, t_e = wt(sc, "Schwefelstoffe"), wt(sc, "Zellen"), wt(sc, "Enzymen")
    t_gas = t_e + 0.8
    d = ImageDraw.Draw(img)
    half = t > t_z - 0.2
    paste_c(img, onion(230, half=half), 540, 950)
    if half and t < t_gas:
        knife(img, 560, 760, -4 + 10 * math.sin(gt * 6))
    if ap(sc, t, "Schwefelstoffe") > 0.02:
        rr = random.Random(4)
        for k in range(10):
            x, y = 540 + rr.uniform(-170, 170), 950 + rr.uniform(-170, 170)
            q = ap(sc, t, "Schwefelstoffe", off=-0.1 + k * 0.05)
            d.ellipse((x - 26 * q, y - 26 * q, x + 26 * q, y + 26 * q), fill=C.YELLOW, outline=NAVY, width=4)
            if q > 0.5:
                text(img, "S", 30, x, y, fill=NAVY)
        C.pill(img, "SCHWEFELSTOFFE", 540, 470, C.YELLOW, ap(sc, t, "Schwefelstoffe") * (1 - prog(t, t_z - 0.4, 0.3)))
    pg = ap(sc, t, "nichts")
    if pg > 0.02 and t < t_z - 0.3:
        C.check(img, 860, 700, 50, pg, w=16)
        text(img, "GANZ = OK", 34, 860, 790, fill=C.GREEN, path=FONT_XB, stroke=4, sfill=NAVY, alpha=pg)
    if t > t_z - 0.3:
        C.pill(img, "ZELLEN KAPUTT", 540, 470, C.RED, ap(sc, t, "Zellen") * (1 - prog(t, t_e - 0.4, 0.3)))
    pe = ap(sc, t, "Enzymen")
    if pe > 0.02 and t < t_gas + 0.3:
        rr = random.Random(7)
        for k in range(6):
            x, y = 540 + rr.uniform(-160, 160), 950 + rr.uniform(-160, 160)
            m = 20 + 10 * math.sin(gt * 10 + k)
            d.pieslice((x - 30, y - 30, x + 30, y + 30), m, 360 - m, fill=C.GREEN)
        C.pill(img, "+ ENZYME", 540, 470, C.GREEN, pe * (1 - prog(t, t_gas, 0.3)))
    if t > t_gas - 0.1:
        a = ease_out(prog(t, t_gas - 0.1, 0.4))
        gas(img, 540, 900, 540, 420, gt, a)
        E.stamp(img, "REIZGAS!", t, t_gas, cx=540, cy=560, size=150, rot=-6, fill=(190, 240, 90), sfill=(40, 80, 20))
        eye(img, 540, 420, 130 * a, red=prog(t, t_gas + 0.8, 1.5), gt=gt)
        if t > t_gas + 1.4:
            text(img, "steigt in deine Augen", 50, 540, 1265, fill=C.WHITE, path=FONT_XB, stroke=6, sfill=NAVY,
                 alpha=ease_out(prog(t, t_gas + 1.4, 0.4)))


def sc_tears(img, sc, t, gt):
    tw_ = ap(sc, t, "Tränen", d=0.6)
    eye(img, 540, 700, 230, tear=tw_, red=1 - 0.6 * tw_, gt=gt)
    gas(img, 300, 1150, 540, 760, gt, 1 - tw_)
    pr = ap(sc, t, "Schutzreflex")
    if pr > 0.02:
        E.stamp(img, "SCHUTZREFLEX", t, wt(sc, "Schutzreflex") - 0.1, cx=540, cy=470, size=110, rot=-5)
    else:
        C.pill(img, "TRÄNEN SPÜLEN DAS GAS WEG", 540, 470, C.BLUE, ap(sc, t, "spült"), size=36)


def fridge(img, cx, cy, s, a=1.0):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((cx - 120 * s, cy - 220 * s, cx + 120 * s, cy + 220 * s), int(24 * s), fill=(235, 240, 250),
                        outline=NAVY, width=max(2, int(8 * s)))
    d.line((cx - 120 * s, cy - 60 * s, cx + 120 * s, cy - 60 * s), fill=NAVY, width=max(2, int(6 * s)))
    d.rectangle((cx + 80 * s, cy - 180 * s, cx + 95 * s, cy - 100 * s), fill=(150, 160, 180))
    d.rectangle((cx + 80 * s, cy - 20 * s, cx + 95 * s, cy + 80 * s), fill=(150, 160, 180))
    for k in range(3):
        an = k * math.pi / 3
        x, y = cx - 40 * s, cy - 140 * s
        d.line((x - 30 * s * math.cos(an), y - 30 * s * math.sin(an), x + 30 * s * math.cos(an),
                y + 30 * s * math.sin(an)), fill=(90, 170, 255), width=max(2, int(6 * s)))


def sc_trick(img, sc, t, gt):
    pf = back_out(prog(t, wt(sc, "Kühlschrank") - 0.2, 0.45))
    if pf > 0.02:
        fridge(img, 310, 880, pf)
        paste_c(img, onion(70), 310, 980)
    pm = back_out(prog(t, wt(sc, "Messer") - 0.2, 0.45))
    if pm > 0.02:
        knife(img, 770, 880 + 10 * math.sin(gt * 3), 60, s=min(1.1, pm))
    if ap(sc, t, "Kälte") > 0.02:
        C.check(img, 310, 1180, 50, ap(sc, t, "Kälte"), w=16)
        text(img, "KÄLTE BREMST", 34, 310, 1270, fill=C.WHITE, path=FONT_XB, stroke=4, sfill=NAVY,
             alpha=ap(sc, t, "Kälte"))
    if ap(sc, t, "weniger") > 0.02:
        C.check(img, 770, 1180, 50, ap(sc, t, "weniger"), w=16)
        text(img, "WENIGER ZELLEN KAPUTT", 34, 770, 1270, fill=C.WHITE, path=FONT_XB, stroke=4, sfill=NAVY,
             alpha=ap(sc, t, "weniger"))
    C.pill(img, "DER TRICK", 540, 470, C.YELLOW, ap(sc, t, "Trick"), size=44)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, onion(110), x, y, a)

    def mr(im, x, y, a, g):
        crying_face(im, x, y, 90 * a, g)

    E.brand(img, t, gt, y=300)
    E.outro(img, sc, t, gt, ml, mr, line1="Gewusst? Ja / Nein", line2="Schreib's uns!")


def extra_sfx():
    ev = []
    marks = {1: [("Schwefelstoffe", "pop"), ("Zellen", "thump"), ("Enzymen", "pop")],
             2: [("Tränen", "pop"), ("Schutzreflex", "thump")],
             3: [("Kühlschrank", "pop"), ("Messer", "pop"), ("Kälte", "pop"), ("weniger", "pop")],
             0: [("weinen", "pop")]}
    for si, lst in marks.items():
        sc = E.SCENES[si]
        for w, k in lst:
            ev.append((sc["start"] + wt(sc, w) - 0.08, k))
    sc = E.SCENES[1]
    ev.append((sc["start"] + wt(sc, "Enzymen") + 0.7, "thump"))
    return ev


E.setup(
    here=HERE, out="zwiebel_weinen.mp4",
    name_l="", name_r="", col_l=C.YELLOW, col_r=C.YELLOW,
    bg_l=((36, 12, 58), (110, 40, 110)), bg_r=((36, 12, 58), (110, 40, 110)),
    scenes=["hook", "cells", "tears", "trick", "outro"],
    draw=dict(hook=sc_hook, cells=sc_cells, tears=sc_tears, trick=sc_trick, outro=sc_outro),
    sub_map=[], score=[], ticks=[], tempo=1.05,
    chimes=[], extra_sfx=extra_sfx,
)

if __name__ == "__main__":
    E.main()

#!/usr/bin/env python3
"""Rate mal, was passiert, wenn dich ein Blitz trifft? – colourful full-frame style."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import col as C  # noqa: E402
from col import E, prog, ease_out, ease_io, back_out, paste_c, text, wt, rrect, FONT_XB  # noqa: E402

GROUND = 1190


def ground(img):
    d = ImageDraw.Draw(img)
    d.rectangle((0, GROUND, 1080, 1920), fill=(26, 60, 52))
    d.line((0, GROUND, 1080, GROUND), fill=(70, 150, 100), width=8)


def rain(img, gt, n=60, seed=3):
    d = ImageDraw.Draw(img)
    rr = random.Random(seed)
    for _ in range(n):
        x = rr.uniform(0, 1080)
        y = 420 + ((gt * 900 + rr.uniform(0, 800)) % 800)
        d.line((x, y, x - 8, y + 30), fill=(140, 170, 230), width=3)


def flash(img, a):
    if a > 0.02:
        lay = Image.new("RGBA", img.size, (255, 255, 255, int(150 * a)))
        img.paste(lay, (0, 0), lay)


def storm(img, gt):
    C.cloud(img, 330, 520 + 6 * math.sin(gt), 1.0, (120, 125, 150))
    C.cloud(img, 760, 470 + 6 * math.sin(gt + 1), 1.15, (140, 145, 170))
    rain(img, gt)


def strike(img, t, t0, x0, y0, x1, y1, seed=1, dur=0.35):
    if t0 <= t < t0 + dur:
        a = 1 - (t - t0) / dur
        C.bolt(img, x0, y0, x1, y1, seed=seed + int((t - t0) * 20), w=16, a=a)
        return a
    return 0.0


def sc_hook(img, sc, t, gt):
    ground(img)
    storm(img, gt)
    paste_c(img, E.person_sprite(460, C.ORANGE, arms_up=0.1), 480, GROUND, ease_out(prog(t, 0.0, 0.3)), anchor="b")
    tb = wt(sc, "Blitz")
    f = strike(img, t, tb - 0.1, 760, 560, 640, GROUND, seed=2, dur=0.5)
    f = max(f, strike(img, t, 0.15, 300, 600, 200, GROUND, seed=5, dur=0.55))
    E.burst(img, 640, GROUND - 10, t, tb - 0.05, color=C.YELLOW, rad=180)
    E.brand(img, t, gt, y=300)
    q = 1 + 0.1 * math.sin(gt * 6)
    text(img, "?", 180 * q, 860, 780, fill=C.YELLOW, stroke=10, sfill=(40, 20, 60), rotate=10,
         alpha=ease_out(prog(t, 0.5, 0.3)))
    flash(img, f * 0.8)


def sun_icon(img, cx, cy, r, gt):
    d = ImageDraw.Draw(img)
    for k in range(12):
        a = k / 12 * 2 * math.pi + gt * 0.5
        d.polygon([(cx + r * 1.1 * math.cos(a - 0.12), cy + r * 1.1 * math.sin(a - 0.12)),
                   (cx + r * 1.45 * math.cos(a), cy + r * 1.45 * math.sin(a)),
                   (cx + r * 1.1 * math.cos(a + 0.12), cy + r * 1.1 * math.sin(a + 0.12))], fill=(255, 190, 40))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 160, 30))
    d.ellipse((cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8), fill=(255, 200, 60))


def sc_hot(img, sc, t, gt):
    t5, ts, tu, t9 = wt(sc, "fünfmal"), wt(sc, "Sonne"), wt(sc, "überleben"), wt(sc, "9")
    part1 = 1 - prog(t, tu - 0.5, 0.3)
    if part1 > 0.02:
        C.bolt(img, 380, 470, 330, 1150, seed=int(gt * 6), w=22, a=part1)
        C.thermometer(img, 560, 520, 1050, 0.95 * ease_out(prog(t, 0.2, 1.2)), C.RED)
        if t > ts - 0.4:
            sun_icon(img, 820, 900, 70 * back_out(prog(t, ts - 0.4, 0.4)), gt)
            text(img, "Sonnenoberfläche", 30, 820, 1040, path=FONT_XB, stroke=4, alpha=part1)
        if t > t5:
            E.stamp(img, "5× HEISSER", t, t5, cx=540, cy=470, size=110, rot=-6, hold=tu - 0.6 - t5)
    if t > tu - 0.5:
        a = ease_out(prog(t, tu - 0.5, 0.3))
        green = int(9 * ease_out(prog(t, t9 - 0.3, 0.9)))
        for k in range(10):
            r_, c_ = divmod(k, 5)
            x, y = 180 + c_ * 180, 760 + r_ * 290
            alive = k < green
            colr = C.GREEN if alive else ((150, 150, 160) if k == 9 and t > t9 + 0.4 else C.ORANGE)
            paste_c(img, E.person_icon(220, colr), x, y, a)
            if alive:
                C.check(img, x + 40, y - 100, 26, a=min(1, (t - (t9 - 0.3)) * 3 - k * 0.2), w=10)
        if t > t9 - 0.3:
            text(img, "9 VON 10", 110, 540, 470, fill=C.GREEN, stroke=10, sfill=(20, 60, 30), alpha=a,
                 scale=0.9 + 0.1 * back_out(prog(t, t9 - 0.3, 0.4)))
            text(img, "überleben", 44, 540, 560, path=FONT_XB, stroke=5, alpha=a)


def fern(d, x, y, ang, length, depth, width, col):
    if depth == 0 or length < 6:
        return
    x2, y2 = x + length * math.cos(ang), y + length * math.sin(ang)
    d.line((x, y, x2, y2), fill=col, width=max(1, int(width)))
    fern(d, x2, y2, ang - 0.45, length * 0.7, depth - 1, width * 0.7, col)
    fern(d, x2, y2, ang + 0.4, length * 0.62, depth - 1, width * 0.7, col)
    fern(d, x2, y2, ang + 0.05, length * 0.75, depth - 1, width * 0.75, col)


def sc_skin(img, sc, t, gt):
    tst, tm, tf = wt(sc, "Strom"), wt(sc, "Muster"), wt(sc, "Farnblatt")
    part1 = 1 - prog(t, tm - 0.5, 0.3)
    if part1 > 0.02:
        ground(img)
        paste_c(img, E.person_sprite(520, C.ORANGE), 540, GROUND, part1, anchor="b")
        if t > tst - 0.2:
            d = ImageDraw.Draw(img)
            path = [(540, 690), (600, 760), (610, 900), (590, 1020), (600, GROUND)]
            for k in range(8):
                f = ((t - tst) * 1.2 + k / 8) % 1
                i = min(len(path) - 2, int(f * (len(path) - 1)))
                kk = f * (len(path) - 1) - i
                x = path[i][0] + (path[i + 1][0] - path[i][0]) * kk
                y = path[i][1] + (path[i + 1][1] - path[i][1]) * kk
                d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=(255, 250, 160))
            C.pill(img, "STROM FLIESST ÜBER DIE HAUT", 540, 470, C.YELLOW, ease_out(prog(t, tst - 0.2, 0.3)) * part1,
                   size=34)
    if t > tm - 0.5:
        a = ease_out(prog(t, tm - 0.5, 0.3))
        rrect(img, (150, 560, 930, 1220), 90, C.SKIN + (int(255 * a),))
        g = prog(t, tm - 0.2, 1.6)
        lay = Image.new("RGBA", img.size)
        d = ImageDraw.Draw(lay)
        fern(d, 260, 1150, -0.9, 260 * ease_out(g), int(1 + 6 * g), 16, (225, 80, 100, int(255 * a)))
        fern(d, 820, 1150, -2.1, 230 * ease_out(g), int(1 + 6 * g), 14, (225, 80, 100, int(255 * a)))
        img.paste(lay, (0, 0), lay)
        if t > tf - 0.3:
            C.pill(img, "LICHTENBERG-FIGUR", 540, 470, C.SKIN, ease_out(prog(t, tf - 0.3, 0.3)))


def ranger(img, cx, bottom, h=420, a=1.0):
    paste_c(img, E.person_sprite(h, C.ORANGE), cx, bottom, a, anchor="b")
    d = ImageDraw.Draw(img)
    top = bottom - h
    d.ellipse((cx - 95, top + 10, cx + 95, top + 50), fill=(150, 100, 50))
    d.rounded_rectangle((cx - 50, top - 45, cx + 50, top + 30), 18, fill=(170, 115, 60))


def sc_ranger(img, sc, t, gt):
    ground(img)
    storm(img, gt)
    t7, tu = wt(sc, "7"), wt(sc, "überlebt")
    ranger(img, 540, GROUND, a=ease_out(prog(t, 0.0, 0.3)))
    C.pill(img, "PARKRANGER, USA", 540, 470, C.WHITE, ease_out(prog(t, 0.2, 0.3)) * (1 - prog(t, t7 - 0.4, 0.2)))
    hits = 0
    fl = 0.0
    span = max(0.5, tu - t7 + 0.3)
    for k in range(7):
        tk = t7 - 0.3 + span * k / 7
        if t >= tk:
            hits = k + 1
        fl = max(fl, strike(img, t, tk, 560 + 60 * math.sin(k), 560, 545, GROUND - 400, seed=10 + k, dur=0.18))
    if hits:
        text(img, f"{hits}×", 150, 540, 470, fill=C.YELLOW, stroke=10, sfill=(40, 20, 60),
             scale=1 + 0.15 * (1 - min(1, (t - (t7 - 0.3 + span * (hits - 1) / 7)) / 0.2)))
    if t > tu:
        E.stamp(img, "ÜBERLEBT!", t, tu, cx=540, cy=600, size=110, rot=-6, fill=C.GREEN, sfill=(20, 80, 40))
        E.confetti(img, t, tu, y0=420)
    flash(img, fl * 0.6)


def sc_safety(img, sc, t, gt):
    ts, th, ta, tb = wt(sc, "Schäden"), wt(sc, "Haus"), wt(sc, "Auto"), wt(sc, "Baum")
    ground(img)
    rain(img, gt, n=40)
    a0 = ease_out(prog(t, 0.0, 0.3)) * (1 - prog(t, th - 0.6, 0.3))
    if a0 > 0.02:
        C.pill(img, "OFT BLEIBENDE SCHÄDEN", 540, 760, C.RED, a0)
        paste_c(img, E.heart_sprite(200, beat=0.5 + 0.5 * math.sin(gt * 8)), 540, 960, a0)
    if t > th - 0.4:
        a = ease_out(prog(t, th - 0.4, 0.4))
        C.house(img, 300, 700, 1.1)
        C.check(img, 300, 520, 50, a=prog(t, th, 0.4))
    if t > ta - 0.4:
        C.car(img, 790, 720, 1.0)
        C.check(img, 790, 560, 50, a=prog(t, ta, 0.4))
    if t > tb - 0.4:
        C.tree(img, 540, GROUND - 160, 1.1)
        fl = strike(img, t, tb, 560, 430, 540, GROUND - 300, seed=4, dur=0.4)
        C.cross(img, 540, GROUND - 160, 120 * ease_out(prog(t, tb + 0.2, 0.3)), w=24)
        flash(img, fl * 0.5)
    if t > th - 0.4:
        C.pill(img, "BEI GEWITTER: REIN!", 540, 470, C.GREEN, ease_out(prog(t, th - 0.4, 0.3)))


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        C.cloud(im, x, y - 30, 0.45, (150, 155, 180))
        C.bolt(im, x, y, x - 10, y + 90, seed=int(g * 4), w=8, a=a)

    def mr(im, x, y, a, g):
        paste_c(im, E.person_sprite(170, C.ORANGE), x, y, a)

    E.brand(img, t, gt, y=300)
    E.outro(img, sc, t, gt, ml, mr, line1="Gewusst? Ja / Nein", line2="Schreib's uns!")


E.setup(
    here=HERE, out="vom_blitz_getroffen.mp4",
    name_l="", name_r="", col_l=C.YELLOW, col_r=C.YELLOW,
    bg_l=((12, 8, 34), (66, 40, 104)), bg_r=((12, 8, 34), (66, 40, 104)),
    scenes=["hook", "hot", "skin", "ranger", "safety", "outro"],
    draw=dict(hook=sc_hook, hot=sc_hot, skin=sc_skin, ranger=sc_ranger, safety=sc_safety, outro=sc_outro),
    sub_map=[], score=[], ticks=[], tempo=1.04, chimes=[],
    extra_sfx=lambda: [(E.SCENES[0]["start"] + wt(E.SCENES[0], "Blitz") - 0.1, "beat"), (0.15, "beat"),
                       (E.SCENES[4]["start"] + wt(E.SCENES[4], "Baum"), "beat")] +
    [(E.SCENES[3]["start"] + wt(E.SCENES[3], "7") - 0.3 + k * 0.3, "beat") for k in range(7)],
)

if __name__ == "__main__":
    E.main()

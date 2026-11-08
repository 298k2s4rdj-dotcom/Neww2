#!/usr/bin/env python3
"""Mensch vs. Hund (Sinne) – animated German TikTok comparison."""
import colorsys
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tiere"))
import engine as E  # noqa: E402
from engine import (CXL, CXR, SPLIT, VIS_Y, NUM_Y, GROUND, SS, back_out, clamp, counter, ease_io,  # noqa: E402
                    ease_out, header, panel_labels, paste_c, person_sprite, prog, stamp, burst, text, vs_badge, wt,
                    rrect, crown, winner, FONT_XB)

C_L = (80, 190, 255)      # Mensch
C_R = (245, 170, 80)      # Hund
FUR = (205, 145, 85, 255)
FUR_D = (150, 95, 50, 255)


def dog_sprite(h, t, wag=1.0):
    w = h * 1.35
    s = SS(w, h)
    # legs
    for x in (0.30, 0.42, 0.78, 0.9):
        s.rect(w * (x - 0.04), h * 0.55, w * (x + 0.04), h * 0.98, w * 0.03, FUR_D if x in (0.42, 0.9) else FUR)
    # tail
    a = 0.5 * math.sin(t * 9) * wag
    tx, ty = w * 0.93, h * 0.42
    s.thick([(tx, ty), (tx + w * 0.08 * math.cos(-0.9 + a), ty - h * 0.25 * math.cos(a)),
             (tx + w * 0.1 * math.cos(-0.6 + a), ty - h * 0.38)], [h * 0.07, h * 0.05, h * 0.03], FUR)
    # body
    s.ell(w * 0.6, h * 0.48, w * 0.34, h * 0.2, FUR)
    # head
    s.ell(w * 0.24, h * 0.3, h * 0.2, h * 0.19, FUR)
    s.ell(w * 0.1, h * 0.37, h * 0.13, h * 0.09, (225, 175, 120, 255))
    s.ell(w * 0.03, h * 0.33, h * 0.045, h * 0.04, (30, 20, 20, 255))
    s.ell(w * 0.2, h * 0.24, h * 0.028, h * 0.032, (30, 20, 20, 255))
    s.ell(w * 0.32, h * 0.32, h * 0.08, h * 0.17, FUR_D)       # ear
    s.ell(w * 0.05, h * 0.45, h * 0.035, h * 0.02, (230, 90, 110, 255))  # tongue
    return s.img()


def eye_sprite(size):
    s = SS(size, size * 0.6)
    s.ell(size / 2, size * 0.3, size * 0.48, size * 0.28, (255, 255, 255, 255))
    s.ell(size / 2, size * 0.3, size * 0.2, size * 0.2, (90, 150, 220, 255))
    s.ell(size / 2, size * 0.3, size * 0.09, size * 0.09, (15, 15, 25, 255))
    return s.img()


def spectrum(img, cx, y, w, h, dog=False, a=1.0):
    xs = np.linspace(0, 1, int(w))
    cols = []
    for x in xs:
        r, g, b = colorsys.hsv_to_rgb(x * 0.8, 0.85, 1.0)
        if dog:  # dichromatic approximation: collapse red/green onto a blue–yellow axis
            yb = (r + g) / 2
            r, g, b = yb, yb * 0.95, b * 0.9 + 0.1 * (1 - yb)
        cols.append((int(r * 255), int(g * 255), int(b * 255)))
    strip = Image.new("RGB", (int(w), int(h)))
    arr = np.array(cols, dtype=np.uint8)[None, :, :].repeat(int(h), axis=0)
    strip = Image.fromarray(arr, "RGB").convert("RGBA")
    m = Image.new("L", strip.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, strip.size[0] - 1, strip.size[1] - 1), 18, fill=int(255 * a))
    strip.putalpha(m)
    img.paste(strip, (int(cx - w / 2), int(y - h / 2)), strip)


def sc_hook(img, sc, t, gt):
    header(img, gt, "", t)
    panel_labels(img, t)
    t_b = wt(sc, "besser")
    pa = back_out(prog(t, 0.0, 0.4))
    paste_c(img, person_sprite(260 * pa + 1, C_L), CXL, GROUND - 60, anchor="b")
    pd = back_out(prog(t, 0.15, 0.4))
    paste_c(img, dog_sprite(200 * pd + 1, gt), CXR, GROUND - 60, anchor="b")
    text(img, "?", 170, SPLIT, VIS_Y - 40, fill=E.C_HI, scale=back_out(prog(t, t_b, 0.35)) * (1 + 0.08 * math.sin(gt * 9)),
         stroke=10)


def sc_farben(img, sc, t, gt):
    header(img, gt, "RUNDE 1 · FARBEN SEHEN", t)
    panel_labels(img, t)
    t_3, t_h, t_2 = wt(sc, "drei"), wt(sc, "Hund"), wt(sc, "zwei")
    a1 = ease_out(prog(t, t_3 - 0.2, 0.5))
    a2 = ease_out(prog(t, t_2 - 0.2, 0.5))
    paste_c(img, eye_sprite(230), CXL, 520, ease_out(prog(t, 0.2, 0.4)))
    paste_c(img, eye_sprite(230), CXR, 520, ease_out(prog(t, 0.2, 0.4)))
    d = ImageDraw.Draw(img)
    for k, col in enumerate(((235, 60, 60), (70, 200, 90), (70, 110, 255))):
        p = ease_out(prog(t, t_3 + k * 0.12, 0.25))
        if p > 0:
            x = CXL - 70 + k * 70
            d.ellipse((x - 26 * p, 660 - 26 * p, x + 26 * p, 660 + 26 * p), fill=col)
    for k, col in enumerate(((235, 210, 60), (70, 110, 255))):
        p = ease_out(prog(t, t_2 + k * 0.12, 0.25))
        if p > 0:
            x = CXR - 35 + k * 70
            d.ellipse((x - 26 * p, 660 - 26 * p, x + 26 * p, 660 + 26 * p), fill=col)
    if a1 > 0:
        spectrum(img, CXL, 800, 380, 90, a=a1)
        text(img, "so siehst du", 30, CXL, 875, fill=(230, 230, 240), alpha=a1, path=FONT_XB)
    if a2 > 0:
        spectrum(img, CXR, 800, 380, 90, dog=True, a=a2)
        text(img, "so ungefähr der Hund", 30, CXR, 875, fill=(230, 230, 240), alpha=a2, path=FONT_XB)
    counter(img, CXL, "3", "Zapfenarten", C_L, ease_out(prog(t, t_3, 0.3)), y=NUM_Y + 20)
    counter(img, CXR, "2", "Zapfenarten", C_R, ease_out(prog(t, t_2, 0.3)), y=NUM_Y + 20)
    burst(img, CXL, 660, t, wt(sc, "Punkt"), color=C_L, rad=200)


def sc_gehoer(img, sc, t, gt):
    header(img, gt, "RUNDE 2 · GEHÖR", t)
    panel_labels(img, t)
    t_20, t_45 = wt(sc, "zwanzigtausend"), wt(sc, "fünfundvierzigtausend")
    base = 1000
    ppk = 9.5           # px per kHz
    d = ImageDraw.Draw(img)
    # axis in the middle
    for k in range(0, 46, 5):
        y = base - k * ppk
        d.line((SPLIT - 14, y, SPLIT + 14, y), fill=(255, 255, 255), width=3)
        if k % 10 == 0:
            text(img, f"{k} kHz", 22, SPLIT + 22, y, fill=(220, 220, 235), path=FONT_XB, anchor="lm")
    d.line((SPLIT, base, SPLIT, base - 45 * ppk), fill=(255, 255, 255), width=3)
    fl = 20 * ease_out(prog(t, t_20, 0.9))
    fr = 45 * ease_out(prog(t, t_45, 1.2))
    for cx, f, col in ((CXL, fl, C_L), (CXR, fr, C_R)):
        if f > 0.1:
            rrect(img, (cx - 70, base - f * ppk, cx + 70, base), 18, col + (255,))
            # sound waves above the bar
            for k in range(3):
                r = 30 + k * 26 + 10 * math.sin(gt * 8 + k)
                yy = base - f * ppk - 30
                d.arc((cx - r, yy - r, cx + r, yy + r), 220, 320, fill=col, width=6)
    paste_c(img, person_sprite(120, C_L), CXL - 150, base, ease_out(prog(t, 0.2, 0.3)), anchor="b")
    paste_c(img, dog_sprite(110, gt), CXR + 120, base, ease_out(prog(t, 0.2, 0.3)), anchor="b")
    counter(img, CXL, f"{E.fmt_int(fl * 1000)} Hz", "du (etwa)", C_L, ease_out(prog(t, t_20, 0.3)))
    counter(img, CXR, f"{E.fmt_int(fr * 1000)} Hz", "Hund (etwa)", C_R, ease_out(prog(t, t_45, 0.3)))
    burst(img, CXR, base - 45 * ppk, t, t_45 + 1.2, color=C_R, rad=160)


def brain_sprite(w, region_frac, col_region):
    s = SS(w, w * 0.75)
    s.ell(w * 0.5, w * 0.38, w * 0.46, w * 0.33, (240, 170, 185, 255))
    for k in range(6):
        y = w * (0.18 + k * 0.08)
        s.line([(w * 0.12, y), (w * 0.3, y - w * 0.04), (w * 0.5, y + w * 0.02), (w * 0.7, y - w * 0.03),
                (w * 0.88, y)], (205, 130, 150, 255), max(1, w * 0.01))
    rw = w * 0.42 * region_frac ** 0.5
    s.ell(w * 0.2, w * 0.5, rw, rw * 0.7, col_region)
    return s.img()


def sc_riechen(img, sc, t, gt):
    header(img, gt, "RUNDE 3 · RIECHZENTRUM", t)
    panel_labels(img, t)
    t_t, t_40 = wt(sc, "Teil"), wt(sc, "vierzigmal")
    g = ease_out(prog(t, t_40, 0.9))
    paste_c(img, brain_sprite(330, 0.025, C_L + (255,)), CXL, 640, ease_out(prog(t, 0.3, 0.4)))
    paste_c(img, brain_sprite(330, 0.025 + (1.0 - 0.025) * g, C_R + (255,)), CXR, 640,
            ease_out(prog(t, t_t - 0.2, 0.4)))
    text(img, "Riechzentrum (im Verhältnis)", 30, SPLIT, 880, fill=(230, 230, 240), path=FONT_XB,
         alpha=ease_out(prog(t, t_t, 0.3)))
    counter(img, CXL, "1×", "Mensch", C_L, ease_out(prog(t, t_t, 0.3)))
    counter(img, CXR, f"{int(round(1 + 39 * g))}×", "Hund", C_R, ease_out(prog(t, t_40, 0.3)))
    stamp(img, "40×", t, t_40 + 0.6, cx=SPLIT, cy=790, size=110, rot=-8)


def sc_finale(img, sc, t, gt):
    t_k = wt(sc, "Klarer")
    header(img, gt, "FINALE · NASE", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    t_6, t_300, t_50 = wt(sc, "sechs"), wt(sc, "dreihundert"), wt(sc, "Fünfzigmal")
    d = ImageDraw.Draw(img)
    # one dot = 6 million receptors
    if t > t_6 - 0.2:
        p = back_out(prog(t, t_6 - 0.2, 0.4))
        r = 22 * p
        d.ellipse((CXL - r, 640 - r, CXL + r, 640 + r), fill=C_L)
        text(img, "1 Punkt = 6 Mio.", 30, CXL, 700, fill=(230, 230, 240), path=FONT_XB, alpha=clamp(p))
    if t > t_300 - 0.2:
        n = int(clamp((t - (t_300 - 0.2)) / 1.0) * 50 + 0.999)
        for k in range(n):
            row, col = divmod(k, 10)
            x = CXR - 180 + col * 40
            y = 470 + row * 44
            d.ellipse((x - 15, y - 15, x + 15, y + 15), fill=C_R)
        text(img, f"{n} Punkte", 32, CXR, 720, fill=(230, 230, 240), path=FONT_XB)
    paste_c(img, person_sprite(160, C_L), CXL, 950, ease_out(prog(t, 0.3, 0.3)), anchor="b")
    paste_c(img, dog_sprite(150, gt), CXR, 950, ease_out(prog(t, 0.3, 0.3)), anchor="b")
    counter(img, CXL, "≈ 6 Mio.", "Riechrezeptoren", C_L, ease_out(prog(t, t_6, 0.3)), y=NUM_Y + 30)
    counter(img, CXR, "bis 300 Mio.", "Riechrezeptoren", C_R, ease_out(prog(t, t_300, 0.3)), y=NUM_Y + 30)
    stamp(img, "50×", t, t_50, cx=SPLIT, cy=820, size=120, rot=-8, hold=1.6)
    if t > t_k:
        crown(img, CXR - 60, 820, prog(t, t_k, 0.5), size=0.45)
        winner(img, t, t_k, "HUND", cy=380)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, person_sprite(170, C_L), x, y + 85, a, anchor="b")

    def mr(im, x, y, a, g):
        paste_c(im, dog_sprite(130, g), x, y + 80, a, anchor="b")

    E.outro(img, sc, t, gt, ml, mr, line1="Und dein Haustier?", line2="Schreib's uns!")


E.setup(
    here=HERE, out="mensch_vs_hund.mp4",
    name_l="MENSCH", name_r="HUND", col_l=C_L, col_r=C_R,
    bg_l=((6, 18, 52), (14, 56, 120)), bg_r=((30, 20, 8), (115, 75, 28)),
    scenes=["hook", "farben", "gehoer", "riechen", "finale", "outro"],
    draw=dict(hook=sc_hook, farben=sc_farben, gehoer=sc_gehoer, riechen=sc_riechen, finale=sc_finale,
              outro=sc_outro),
    sub_map=[
        (("zwanzigtausend",), "20.000"), (("fünfundvierzigtausend",), "45.000"), (("vierzigmal",), "40-mal"),
        (("sechs",), "6"), (("dreihundert",), "300"), (("Fünfzigmal",), "50-mal"),
        (("eins",), "1"), (("zwei",), "2"), (("drei",), "3"),
    ],
    score=[(1, "Punkt", 1, "L"), (2, "fünfundvierzigtausend", 1, "R"), (3, "vierzigmal", 1, "R"),
           (4, "Sieger", 1, "R")],
    ticks=[(2, "fünfundvierzigtausend", 1, 1.1), (4, "dreihundert", 1, 1.0)],
)

if __name__ == "__main__":
    E.main()

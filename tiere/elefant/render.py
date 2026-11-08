#!/usr/bin/env python3
"""Elefant vs. Mensch – animated German TikTok comparison.

Usage: python3 render.py [--stills [t1 t2 ...]]
"""
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import engine as E  # noqa: E402
from engine import (CXL, CXR, SPLIT, VIS_Y, NUM_Y, GROUND, SS, back_out, clamp, counter, ease_io,  # noqa: E402
                    ease_out, fmt_int, header, panel_labels, paste_c, person_icon, person_sprite, baby_sprite,
                    prog, stamp, burst, text, vs_badge, wt, rrect, crown, winner, ruler, FONT_XB)

C_L = (255, 128, 80)      # Mensch
C_R = (190, 130, 255)     # Elefant

SKIN = (152, 152, 172, 255)
SKIN_D = (122, 122, 142, 255)
EAR = (138, 132, 160, 255)
EAR_IN = (196, 156, 176, 255)
IVORY = (245, 238, 220, 255)


class EMap:
    """unit coords (ground 0, shoulder height 1) -> pixels"""

    def __init__(self, h, ox=0, oy=0):
        self.h, self.ox, self.oy = h, ox, oy

    def __call__(self, x, y):
        return (self.ox + (x + 0.32) * self.h, self.oy + (1.18 - y) * self.h)


def elephant_sprite(h, t, tusks=True, tint=None):
    h = max(20, h)
    s = SS(1.55 * h, 1.2 * h)
    m = EMap(h)

    def P(x, y):
        return m(x, y)

    sk, skd = (tint, tint) if tint else (SKIN, SKIN_D)
    for x in (0.80, 0.30):
        s.rect(*P(x - 0.075, 0.58), *P(x + 0.075, 0.0), 0.04 * h, skd)
    s.thick([P(1.04, 0.86), P(1.09, 0.52)], [0.025 * h, 0.018 * h], skd)
    s.ell(*P(1.095, 0.49), 0.02 * h, 0.045 * h, (70, 70, 80, 255) if not tint else tint)
    s.ell(*P(0.62, 0.70), 0.46 * h, 0.33 * h, sk)
    for x in (0.94, 0.20):
        s.rect(*P(x - 0.08, 0.60), *P(x + 0.08, 0.0), 0.04 * h, sk)
        if not tint:
            for k in range(3):
                s.ell(*P(x - 0.05 + k * 0.05, 0.015), 0.018 * h, 0.012 * h, (220, 215, 205, 255))
    s.ell(*P(0.12, 0.88), 0.21 * h, 0.23 * h, sk)
    sw = 0.05 * math.sin(t * 1.6)
    trunk = [P(0.0, 0.84), P(-0.11, 0.62), P(-0.15 + sw * 0.5, 0.38), P(-0.12 + sw, 0.17), P(-0.06 + sw, 0.10)]
    s.thick(trunk, [0.17 * h, 0.13 * h, 0.10 * h, 0.075 * h, 0.06 * h], sk)
    if not tint:
        for k in range(6):
            yy = 0.70 - k * 0.08
            x0 = -0.12 - (sw * 0.6 if yy < 0.4 else 0)
            s.line([P(x0 - 0.03, yy), P(x0 + 0.04, yy - 0.01)], skd, max(1, 0.006 * h))
    if tusks and not tint:
        s.poly([P(-0.01, 0.70), P(0.04, 0.68), P(-0.10, 0.52), P(-0.17, 0.50), P(-0.12, 0.55)], IVORY)
    flap = 1 + 0.04 * math.sin(t * 2.3)
    s.ell(*P(0.30, 0.86), 0.17 * h * flap, 0.25 * h, EAR if not tint else tint)
    if not tint:
        s.ell(*P(0.31, 0.86), 0.12 * h * flap, 0.19 * h, EAR_IN)
        s.ell(*P(0.07, 0.95), 0.012 * h, 0.012 * h, (25, 25, 35, 255))
    return s.img()


def draw_elephant(img, h, cx, ground, t, alpha=1.0, **kw):
    spr = elephant_sprite(h, t, **kw)
    w, hh = spr.size
    # horizontal anchor: body centre (unit x 0.45)
    ox = cx - (0.45 + 0.32) * h
    oy = ground - 1.18 * h
    paste_c(img, spr, ox + w / 2, oy + hh / 2, alpha)
    return EMap(h, ox, oy)


def sc_hook(img, sc, t, gt):
    header(img, gt, "", t)
    panel_labels(img, t, right="???")
    t_t = wt(sc, "Tier")
    paste_c(img, person_sprite(220 * back_out(prog(t, 0.0, 0.4)) + 1, C_L), CXL, GROUND - 40, anchor="b")
    rise = ease_out(prog(t, t_t - 0.6, 0.7))
    if rise > 0:
        draw_elephant(img, 300, CXR - 40, GROUND - 40 + (1 - rise) * 600, gt, tint=(20, 10, 40, 255))
        text(img, "?", 130, CXR - 40, GROUND - 230, fill=C_R, scale=1 + 0.1 * math.sin(gt * 9), stroke=8,
             alpha=rise)
    # calendar counting the months
    p = back_out(prog(t, 0.0, 0.35))
    if p > 0.02:
        cx, cy = SPLIT, 560
        rrect(img, (cx - 150 * p, cy - 120 * p, cx + 150 * p, cy + 140 * p), 26, (255, 255, 255, 240))
        rrect(img, (cx - 150 * p, cy - 120 * p, cx + 150 * p, cy - 50 * p), 26, (230, 60, 70, 255))
        n = int(round(22 * ease_out(prog(t, 0.05, 0.9))))
        text(img, str(n), 130, cx, cy + 45, fill=(40, 30, 60), scale=p)
        text(img, "MONATE", 34, cx, cy - 85, fill=(255, 255, 255), scale=p)


def sc_groesse(img, sc, t, gt):
    header(img, gt, "RUNDE 1 · GRÖSSE", t)
    panel_labels(img, t)
    t_du, t_180 = wt(sc, "Du"), wt(sc, "eins", 2)
    t_el, t_35, t_s = wt(sc, "Elefantenbullen"), wt(sc, "dreieinhalb"), wt(sc, "Schulter")
    ppm = 120
    ruler(img, 40, GROUND, ppm, 4, a=ease_out(prog(t, 0.2, 0.4)), side="right", step=0.5)
    pa = back_out(prog(t, t_du - 0.1, 0.4))
    if pa > 0.02:
        paste_c(img, person_sprite(1.8 * ppm * pa, C_L), 150, GROUND, anchor="b")
    g = ease_out(prog(t, t_el - 0.1, 0.9))
    if g > 0.02:
        draw_elephant(img, 3.5 * ppm * g, 595, GROUND, gt)
    if t > t_35:
        a = ease_out(prog(t, t_35, 0.4))
        y = GROUND - 3.5 * ppm
        d = ImageDraw.Draw(img)
        x = 45
        while x < 600 * a:
            d.line((x, y, x + 18, y), fill=(255, 226, 60), width=4)
            x += 30
    if t > t_s - 0.2:
        text(img, "Schulterhöhe", 40, 330, GROUND - 3.5 * ppm - 34, fill=E.C_HI, stroke=5,
             scale=back_out(prog(t, t_s - 0.2, 0.35)), path=FONT_XB)
    counter(img, CXL, "1,80 m", "du (Beispiel)", C_L, ease_out(prog(t, t_180, 0.3)))
    counter(img, CXR, "über " + E.fmt_dec(3.5 * ease_out(prog(t, t_35, 0.8)), 1) + " m", "bis zur Schulter", C_R,
            ease_out(prog(t, t_35, 0.3)))
    burst(img, 595, GROUND - 3.5 * ppm, t, t_s, color=C_R, rad=200)


def tiles(img, cx, top, cols, n_total, n_lit, size, gap, color):
    rows = math.ceil(n_total / cols)
    w = cols * size + (cols - 1) * gap
    x0 = cx - w / 2
    for k in range(n_total):
        r, c = divmod(k, cols)
        x = x0 + c * (size + gap)
        y = top + r * (size + gap)
        lit = n_lit > k
        pop = 1.0
        if lit and n_lit - k < 1.0:
            pop = 0.6 + 0.4 * (n_lit - k)
        fill = color + (255,) if lit else (255, 255, 255, 45)
        s2 = size * pop
        rrect(img, (x + (size - s2) / 2, y + (size - s2) / 2, x + (size + s2) / 2, y + (size + s2) / 2), 14, fill)
        if lit:
            text(img, str(k + 1), size * 0.42, x + size / 2, y + size / 2, fill=(30, 20, 50))


def sc_schwanger(img, sc, t, gt):
    header(img, gt, "RUNDE 2 · SCHWANGERSCHAFT", t)
    panel_labels(img, t)
    t_m, t_9 = wt(sc, "Menschen"), wt(sc, "neun")
    t_e, t_22, t_f = wt(sc, "Elefanten"), wt(sc, "zweiundzwanzig"), wt(sc, "Fast")
    al = ease_out(prog(t, t_m - 0.2, 0.3))
    if al > 0:
        tiles(img, CXL, 560, 3, 9, 9 * clamp((t - t_9 + 0.1) / 0.7) if t > t_9 - 0.1 else 0, 100, 14, C_L)
    ar = ease_out(prog(t, t_e - 0.2, 0.3))
    if ar > 0:
        tiles(img, CXR, 450, 4, 22, 22 * clamp((t - t_22 + 0.1) / 1.1) if t > t_22 - 0.1 else 0, 80, 12, C_R)
    counter(img, CXL, "≈ 9 Monate", "Mensch", C_L, ease_out(prog(t, t_9, 0.3)))
    counter(img, CXR, "≈ 22 Monate", "Elefant (Schnitt)", C_R, ease_out(prog(t, t_22, 0.3)))
    stamp(img, "fast 2 Jahre!", t, t_f, cx=SPLIT, cy=VIS_Y + 90, size=96, rot=-7)


def scale_dev(img, cx, y, reading, color, a=1.0):
    rrect(img, (cx - 170, y, cx + 170, y + 26), 10, (230, 230, 240, int(255 * a)))
    rrect(img, (cx - 130, y + 40, cx + 130, y + 120), 16, (15, 20, 30, int(255 * a)), outline=color + (int(255 * a),),
          width=5)
    text(img, reading, 50, cx, y + 80, fill=(120, 255, 140), alpha=a)


def sc_baby(img, sc, t, gt):
    header(img, gt, "RUNDE 3 · BABY", t)
    panel_labels(img, t)
    t_b, t_35 = wt(sc, "Baby", 2), wt(sc, "dreieinhalb")
    t_eb, t_120 = wt(sc, "Elefantenbaby"), wt(sc, "hundertzwanzig")
    sy = 820
    al = ease_out(prog(t, t_b - 0.2, 0.3))
    if al > 0:
        pb = back_out(prog(t, t_b - 0.2, 0.4))
        paste_c(img, baby_sprite(150 * pb + 1), CXL, sy, anchor="b")
        v = 3.48 * ease_out(prog(t, t_35, 0.7))
        scale_dev(img, CXL, sy, E.fmt_dec(v, 2) + " kg", C_L, al)
    ar = ease_out(prog(t, t_eb - 0.2, 0.3))
    if ar > 0:
        pe = back_out(prog(t, t_eb - 0.2, 0.5))
        sink = 10 * ease_out(prog(t, t_120, 0.4))
        draw_elephant(img, 260 * pe + 1, CXR - 10, sy + sink, gt, tusks=False)
        v = 120 * ease_out(prog(t, t_120, 0.8))
        scale_dev(img, CXR, sy + sink, f"{int(round(v))} kg", C_R, ar)
    vs_badge(img, gt, ease_out(prog(t, 0.3, 0.3)) * (1 - prog(t, t_eb, 0.3)), y=VIS_Y)
    counter(img, CXL, "knapp 3,5 kg", "Baby (Ø Deutschland)", C_L, ease_out(prog(t, t_35, 0.3)), size=60,
            y=NUM_Y + 30)
    counter(img, CXR, "bis 120 kg", "Elefantenbaby", C_R, ease_out(prog(t, t_120, 0.3)), size=60, y=NUM_Y + 30)
    burst(img, CXR, sy + 80, t, t_120 + 0.5, color=C_R, rad=200)


CROWD = None


def sc_finale(img, sc, t, gt):
    t_k = wt(sc, "Klarer")
    header(img, gt, "FINALE · GEWICHT", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    t_eb, t_6, t_85 = wt(sc, "Elefantenbulle"), wt(sc, "sechs"), wt(sc, "fünfundachtzig")
    gy = 700
    ga = ease_out(prog(t, t_eb - 0.3, 0.5))
    m = draw_elephant(img, 280, SPLIT + 10, gy, gt, alpha=ga)
    v = 6000 * ease_out(prog(t, t_6, 1.1))
    scale_dev(img, SPLIT, gy, f"{fmt_int(v)} kg", C_R, ga)
    if t > t_85 - 0.2:
        f = clamp((t - (t_85 - 0.2)) / 1.0)
        n = int(f * 85 + 0.999)
        icon = person_icon(46, C_L)
        for k in range(n):
            row, col = divmod(k, 22)
            paste_c(img, icon, 70 + col * 38, 880 + row * 52)
        counter(img, SPLIT, f"über {n}" if f >= 1 else str(n), "Menschen à 70 kg", C_L, 1.0, size=60, y=NUM_Y + 120)
    if t > t_k:
        hx, hy = m(0.12, 1.12)
        crown(img, hx, hy - 30, prog(t, t_k, 0.5), size=0.55)
        winner(img, t, t_k, "ELEFANT", cy=470)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, person_sprite(170, C_L), x, y + 85, a, anchor="b")

    def mr(im, x, y, a, g):
        draw_elephant(im, 130, x + 10, y + 85, g, alpha=a)

    E.outro(img, sc, t, gt, ml, mr, line1="Wer als Nächstes?")


E.setup(
    here=HERE, out="elefant_vs_mensch.mp4", tempo=1.15,
    name_l="MENSCH", name_r="ELEFANT", col_l=C_L, col_r=C_R,
    bg_l=((42, 10, 22), (120, 36, 34)), bg_r=((22, 8, 48), (78, 30, 125)),
    scenes=["hook", "groesse", "schwanger", "baby", "finale", "outro"],
    draw=dict(hook=sc_hook, groesse=sc_groesse, schwanger=sc_schwanger, baby=sc_baby, finale=sc_finale,
              outro=sc_outro),
    sub_map=[
        (("Zweiundzwanzig",), "22"), (("zweiundzwanzig",), "22"), (("eins", "achtzig"), "1,80"),
        (("dreieinhalb",), "3,5"), (("neun",), "9"), (("hundertzwanzig",), "120"), (("sechs",), "6"),
        (("fünfundachtzig",), "85"), (("eins",), "1"), (("zwei",), "2"), (("drei",), "3"),
    ],
    score=[(1, "Nur", 1, "R"), (2, "Fast", 1, "R"), (3, "hundertzwanzig", 1, "R"), (4, "Sieger", 1, "R")],
    ticks=[(2, "zweiundzwanzig", 1, 1.0), (3, "hundertzwanzig", 1, 0.8), (4, "sechs", 1, 1.0)],
)

if __name__ == "__main__":
    E.main()

#!/usr/bin/env python3
"""Giraffe vs. Mensch – animated German TikTok comparison.

Usage: python3 render.py [--stills [t1 t2 ...]]
"""
import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import engine as E  # noqa: E402
from engine import (CXL, CXR, SPLIT, VIS_Y, NUM_Y, GROUND, SS, back_out, clamp, counter, ease_io,  # noqa: E402
                    ease_out, fmt_int, header, panel_labels, paste_c, person_icon, person_sprite, baby_sprite,
                    prog, stamp, burst, text, vs_badge, wt, rrect, crown, winner, ruler, FONT_XB)

C_L = (80, 190, 255)      # Mensch
C_R = (255, 190, 40)      # Giraffe

BODY = (236, 182, 72, 255)
SPOT = (150, 86, 32, 255)
DARK = (95, 55, 25, 255)

NECK_A, NECK_B = (0.22, 0.60), (0.06, 0.90)     # neck axis in unit coords


class GMap:
    """unit coords (x right, y up, ground 0, top 1) -> sprite/screen pixels"""

    def __init__(self, h, ox=0, oy=0):
        self.h, self.ox, self.oy = h, ox, oy

    def __call__(self, x, y):
        return (self.ox + (x + 0.14) * self.h, self.oy + (1.03 - y) * self.h)


def giraffe_sprite(h, t, sway=1.0):
    h = max(30, h)
    w = 0.9 * h
    s = SS(w, 1.05 * h)
    sp = SS(w, 1.05 * h)
    m = GMap(h)
    nod = 0.012 * math.sin(t * 1.7) * sway

    def P(x, y):
        return m(x, y)

    # legs
    for x, back in ((0.17, 0), (0.25, 1), (0.52, 0), (0.60, 1)):
        c = BODY if not back else (220, 165, 60, 255)
        s.thick([P(x, 0.50), P(x + 0.005, 0.03)], [0.05 * h, 0.03 * h], c)
        s.ell(*P(x + 0.006, 0.02), 0.022 * h, 0.014 * h, DARK)
    # tail
    s.thick([P(0.63, 0.58), P(0.67, 0.37)], [0.012 * h, 0.008 * h], BODY)
    s.ell(*P(0.672, 0.35), 0.014 * h, 0.03 * h, DARK)
    # body + shoulder
    s.ell(*P(0.40, 0.55), 0.25 * h, 0.10 * h, BODY)
    s.ell(*P(0.24, 0.59), 0.12 * h, 0.105 * h, BODY)
    # neck
    nb = (NECK_B[0], NECK_B[1] + nod)
    s.thick([P(*NECK_A), P((NECK_A[0] + nb[0]) / 2, (NECK_A[1] + nb[1]) / 2), P(*nb)],
            [0.13 * h, 0.09 * h, 0.06 * h], BODY)
    # mane
    s.thick([P(0.27, 0.62), P(nb[0] + 0.045, nb[1] + 0.005)], [0.018 * h, 0.012 * h], DARK)
    # head
    hx, hy = nb[0] - 0.035, nb[1] + 0.03
    s.ell(*P(hx, hy), 0.075 * h, 0.04 * h, BODY)
    s.ell(*P(hx - 0.06, hy - 0.012), 0.04 * h, 0.03 * h, (225, 170, 70, 255))
    s.ell(*P(hx + 0.07, hy + 0.025), 0.026 * h, 0.012 * h, BODY)
    for ox in (0.0, 0.03):
        s.thick([P(hx + 0.02 + ox, hy + 0.03), P(hx + 0.025 + ox, hy + 0.075)], [0.012 * h, 0.01 * h], BODY)
        s.ell(*P(hx + 0.025 + ox, hy + 0.078), 0.012 * h, 0.012 * h, DARK)
    s.ell(*P(hx - 0.01, hy + 0.008), 0.008 * h, 0.008 * h, (30, 20, 10, 255))
    s.ell(*P(hx - 0.09, hy - 0.012), 0.005 * h, 0.005 * h, (60, 35, 15, 255))
    # spots (clipped to the silhouette)
    r = random.Random(7)
    for _ in range(85):
        x = r.uniform(0.05, 0.66)
        y = r.uniform(0.40, 0.92)
        rr = r.uniform(0.018, 0.032)
        pts = []
        for k in range(7):
            a = k / 7 * 2 * math.pi + r.uniform(-0.3, 0.3)
            q = rr * r.uniform(0.7, 1.15)
            pts.append(P(x + q * math.cos(a), y + q * math.sin(a)))
        sp.poly(pts, SPOT)
    base = s.img()
    spots = sp.img()
    body_a = base.getchannel("A")
    spots.putalpha(ImageChops.multiply(spots.getchannel("A"), body_a))
    base.alpha_composite(spots)
    return base


def draw_giraffe(img, h, cx, ground, t, alpha=1.0):
    spr = giraffe_sprite(h, t)
    w, hh = spr.size
    ox, oy = cx - w / 2, ground - (1.03 - 0.0) * h
    paste_c(img, spr, ox + w / 2, oy + hh / 2, alpha)
    return GMap(h, ox, oy)


def sc_hook(img, sc, t, gt):
    header(img, gt, "", t)
    panel_labels(img, t)
    t_g, t_ge = wt(sc, "Giraffe"), wt(sc, "gemeinsam")
    pa = back_out(prog(t, 0.0, 0.4))
    paste_c(img, person_sprite(220 * pa + 1, C_L), CXL, GROUND - 60, anchor="b")
    rise = ease_out(prog(t, 0.0, 0.6))
    draw_giraffe(img, 470, CXR + 40, GROUND - 60 + (1 - rise) * 90, gt, alpha=rise)
    q = back_out(prog(t, t_ge, 0.35))
    text(img, "?", 170, SPLIT - 10, VIS_Y - 40, fill=E.C_HI, scale=q * (1 + 0.08 * math.sin(gt * 9)), stroke=10,
         sfill=(0, 0, 0))


def sc_groesse(img, sc, t, gt):
    header(img, gt, "RUNDE 1 · GRÖSSE", t)
    panel_labels(img, t)
    t_du, t_180 = wt(sc, "Du"), wt(sc, "eins", 2)
    t_g, t_55, t_3 = wt(sc, "Giraffe"), wt(sc, "fünfeinhalb"), wt(sc, "Dreimal")
    ppm = 100
    ruler(img, SPLIT - 12, GROUND, ppm, 5.5, a=ease_out(prog(t, 0.2, 0.4)), step=0.5)
    pa = back_out(prog(t, t_du - 0.1, 0.4))
    if pa > 0.02:
        paste_c(img, person_sprite(1.8 * ppm * pa, C_L), CXL - 60, GROUND, anchor="b")
    g = ease_out(prog(t, t_g - 0.1, 1.0))
    if g > 0.02:
        draw_giraffe(img, 5.5 * ppm * g, CXR + 30, GROUND, gt)
    # three people stacked = giraffe height
    if t > t_3 - 0.1:
        for k in range(3):
            p = back_out(prog(t, t_3 - 0.1 + k * 0.18, 0.3))
            if p > 0.02:
                spr = person_sprite(1.8 * ppm, C_L)
                paste_c(img, spr, 330, GROUND - k * 1.8 * ppm, alpha=0.85 * clamp(p), anchor="b")
        text(img, "3×", 70, 330, GROUND - 5.6 * ppm, fill=C_L, stroke=6, alpha=ease_out(prog(t, t_3 + 0.4, 0.3)))
    counter(img, CXL, "1,80 m", "du (Beispiel)", C_L, ease_out(prog(t, t_180, 0.3)))
    counter(img, CXR, E.fmt_dec(5.5 * ease_out(prog(t, t_55, 0.9)), 2) + " m", "Giraffe (bis zu)", C_R,
            ease_out(prog(t, t_55, 0.3)))
    burst(img, 330, GROUND - 2.7 * ppm, t, t_3 + 0.5, color=C_L, rad=180)


def sc_baby(img, sc, t, gt):
    header(img, gt, "RUNDE 2 · BABY", t)
    panel_labels(img, t)
    t_mb, t_50 = wt(sc, "Menschenbaby"), wt(sc, "fünfzig")
    t_gb, t_180, t_so = wt(sc, "Giraffenbaby"), wt(sc, "eins"), wt(sc, "So")
    ppm = 250
    ruler(img, SPLIT - 12, GROUND, ppm, 2, a=ease_out(prog(t, 0.2, 0.4)), step=0.25)
    pa = back_out(prog(t, t_mb - 0.1, 0.4))
    if pa > 0.02:
        spr = baby_sprite(0.5 * ppm * pa)
        paste_c(img, spr, CXL - 40, GROUND, anchor="b")
        d = ImageDraw.Draw(img)
        x0, x1 = CXL - 40 - 0.25 * ppm, CXL - 40 + 0.25 * ppm
        if pa > 0.9:
            d.line((x0, GROUND + 18, x1, GROUND + 18), fill=C_L, width=4)
            d.line((x0, GROUND + 8, x0, GROUND + 28), fill=C_L, width=4)
            d.line((x1, GROUND + 8, x1, GROUND + 28), fill=C_L, width=4)
    g = back_out(prog(t, t_gb - 0.1, 0.6))
    if g > 0.02:
        draw_giraffe(img, 1.8 * ppm * clamp(g, 0, 1.08), CXR + 30, GROUND, gt)
    # outline of an adult (1.80 m) next to the calf
    if t > t_so - 0.1:
        a = ease_out(prog(t, t_so - 0.1, 0.4))
        spr = person_sprite(1.8 * ppm, (255, 255, 255))
        paste_c(img, spr, CXL + 90, GROUND, alpha=0.45 * a, anchor="b")
        text(img, "du: 1,80 m", 34, CXL + 90, GROUND - 1.8 * ppm - 30, fill=WHITE_, alpha=a, stroke=4,
             path=FONT_XB)
    counter(img, CXL, "≈ 50 cm", "Menschenbaby", C_L, ease_out(prog(t, t_50, 0.3)))
    counter(img, CXR, "bis 1,80 m", "Giraffenbaby", C_R, ease_out(prog(t, t_180, 0.3)))
    burst(img, CXR + 30, GROUND - 0.9 * ppm, t, t_so, color=C_R, rad=230)


WHITE_ = (255, 255, 255)


def human_bust(img, cx, top, lit, t):
    """side profile head + neck with 7 cervical vertebrae; lit = number highlighted (float)"""
    s = SS(320, 460)
    skin = C_L + (255,)
    s.ell(160, 95, 85, 90, skin)                         # head
    s.ell(90, 115, 25, 20, skin)                          # nose area
    s.rect(120, 150, 205, 330, 30, skin)                  # neck
    s.rect(20, 320, 300, 460, 70, skin)                   # shoulders
    spr = s.img()
    paste_c(img, spr, cx, top + 230)
    d = ImageDraw.Draw(img)
    for k in range(7):
        y = top + 160 + k * 24
        on = lit > k
        col = (255, 226, 60) if on else (255, 255, 255)
        a = 255 if on else 110
        layer = Image.new("RGBA", (60, 22))
        ImageDraw.Draw(layer).rounded_rectangle((0, 0, 59, 21), 8, fill=col + (a,), outline=(40, 40, 60, 255),
                                                width=2)
        img.paste(layer, (int(cx - 30 + 5), int(y)), layer)


def giraffe_vertebrae(img, m, lit):
    (ax, ay), (bx, by) = m(*NECK_A), m(*NECK_B)
    ang = math.degrees(math.atan2(by - ay, bx - ax))
    L = math.hypot(bx - ax, by - ay)
    seg = L / 7
    for k in range(7):
        u = (k + 0.5) / 7
        x, y = ax + (bx - ax) * u, ay + (by - ay) * u
        on = lit > k
        col = (255, 226, 60) if on else (255, 255, 255)
        a = 255 if on else 120
        layer = Image.new("RGBA", (int(seg * 0.82) + 4, 30))
        ImageDraw.Draw(layer).rounded_rectangle((2, 2, int(seg * 0.82) + 1, 27), 10, fill=col + (a,),
                                                outline=(60, 40, 20, 255), width=3)
        layer = layer.rotate(-ang, expand=True, resample=Image.BICUBIC)
        paste_c(img, layer, x, y)


def sc_wirbel(img, sc, t, gt):
    header(img, gt, "RUNDE 3 · HALSWIRBEL", t)
    panel_labels(img, t)
    t_hals, t_7a = wt(sc, "Hals"), wt(sc, "sieben", 1)
    t_du, t_7b, t_u = wt(sc, "du"), wt(sc, "sieben", 2), wt(sc, "Unentschieden")
    m = draw_giraffe(img, 560, CXR + 40, GROUND, gt, alpha=ease_out(prog(t, 0.1, 0.4)))
    lit_r = 7 * clamp((t - (t_7a - 0.3)) / 0.8) if t > t_7a - 0.3 else (0 if t < t_hals else 0)
    if t > t_hals - 0.2:
        giraffe_vertebrae(img, m, lit_r)
    ha = ease_out(prog(t, t_du - 0.4, 0.4))
    if ha > 0.02:
        lit_l = 7 * clamp((t - (t_7b - 0.3)) / 0.6) if t > t_7b - 0.3 else 0
        human_bust(img, CXL - 10, 470 + (1 - ha) * 300, lit_l, gt)
    if t > t_7a - 0.3:
        counter(img, CXR, str(int(math.ceil(lit_r))), "Halswirbel", C_R, 1.0)
    if t > t_7b - 0.3:
        counter(img, CXL, str(int(math.ceil(7 * clamp((t - (t_7b - 0.3)) / 0.6)))), "Halswirbel", C_L, 1.0)
    stamp(img, "7 : 7", t, t_u, cx=SPLIT, cy=VIS_Y - 110, size=150, rot=-6)
    if t > t_u + 0.2:
        text(img, "UNENTSCHIEDEN!", 64, SPLIT, VIS_Y + 30, fill=WHITE_, stroke=8, sfill=(150, 20, 0),
             scale=back_out(prog(t, t_u + 0.2, 0.35)), rotate=-6)
    burst(img, SPLIT, VIS_Y - 110, t, t_u)


def sc_finale(img, sc, t, gt):
    t_k = wt(sc, "Klarer")
    header(img, gt, "FINALE · GEWICHT", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    t_gb, t_12, t_17 = wt(sc, "Giraffenbulle"), wt(sc, "zwölfhundert"), wt(sc, "siebzehn")
    gy = 770
    ga = ease_out(prog(t, t_gb - 0.3, 0.5))
    gx = SPLIT + 40
    m = draw_giraffe(img, 400, gx, gy, gt, alpha=ga)
    rrect(img, (gx - 240, gy, gx + 240, gy + 26), 10, (230, 230, 240, int(255 * ga)))
    rrect(img, (gx - 150, gy + 40, gx + 150, gy + 120), 16, (15, 20, 30, int(255 * ga)),
          outline=C_R + (int(255 * ga),), width=5)
    v = 1191.8 * ease_out(prog(t, t_12, 1.1))
    text(img, f"{fmt_int(v)} kg", 54, gx, gy + 80, fill=(120, 255, 140), alpha=ga)
    if t > t_17 - 0.1:
        n = int(clamp((t - (t_17 - 0.1)) / 0.8) * 17 + 0.999)
        icon = person_icon(80, C_L)
        for k in range(n):
            row, col = divmod(k, 9)
            x = SPLIT - 4 * 88 + col * 88 + (44 if row else 0)
            y = gy + 210 + row * 92
            paste_c(img, icon, x, y)
        counter(img, SPLIT, f"= {n} Menschen", "à 70 kg", C_L, 1.0, size=58, y=NUM_Y + 140)
    if t > t_k:
        hx, hy = m(NECK_B[0] - 0.01, 1.03)
        crown(img, hx, hy - 30, prog(t, t_k, 0.5), size=0.55)
        winner(img, t, t_k, "GIRAFFE", cy=560)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, person_sprite(170, C_L), x, y + 85, a, anchor="b")

    def mr(im, x, y, a, g):
        spr = giraffe_sprite(240, g)
        paste_c(im, spr, x, y - 10, a)

    E.outro(img, sc, t, gt, ml, mr, line1="Gewusst?", line2="Schreib's uns!")


E.setup(
    here=HERE, out="giraffe_vs_mensch.mp4",
    name_l="MENSCH", name_r="GIRAFFE", col_l=C_L, col_r=C_R,
    bg_l=((6, 18, 52), (14, 56, 120)), bg_r=((48, 22, 4), (135, 78, 8)),
    scenes=["hook", "groesse", "baby", "wirbel", "finale", "outro"],
    draw=dict(hook=sc_hook, groesse=sc_groesse, baby=sc_baby, wirbel=sc_wirbel, finale=sc_finale, outro=sc_outro),
    sub_map=[
        (("eins", "achtzig"), "1,80"), (("fünfeinhalb",), "5,5"), (("Dreimal",), "3-mal"),
        (("fünfzig",), "50"), (("sieben",), "7"), (("zwölfhundert",), "1.200"), (("siebzehn",), "17"),
        (("eins",), "1"), (("zwei",), "2"), (("drei",), "3"),
    ],
    score=[(1, "Dreimal", 1, "R"), (2, "So", 1, "R"), (3, "Unentschieden", 1, "B"), (4, "Sieger", 1, "R")],
    ticks=[(1, "fünfeinhalb", 1, 0.9), (4, "zwölfhundert", 1, 1.0)],
)

if __name__ == "__main__":
    E.main()

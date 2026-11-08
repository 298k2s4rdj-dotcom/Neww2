#!/usr/bin/env python3
"""Kaffee vs. Energydrink – animated German TikTok comparison."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tiere"))
import engine as E  # noqa: E402
from engine import (CXL, CXR, SPLIT, VIS_Y, NUM_Y, GROUND, SS, back_out, clamp, counter, ease_io,  # noqa: E402
                    ease_out, header, panel_labels, paste_c, prog, stamp, burst, text, vs_badge, wt, rrect,
                    crown, winner, FONT_XB)

C_L = (240, 170, 100)     # Kaffee
C_R = (140, 255, 90)      # Energydrink
COFFEE = (92, 52, 28, 255)


def cup_sprite(h, t, small=False):
    w = h * (1.25 if not small else 1.1)
    s = SS(w + 10, h * 1.6)
    top = h * 0.55
    body_w = w * (0.72 if not small else 0.62)
    x0 = (w - body_w) / 2
    s.poly([(x0, top), (x0 + body_w, top), (x0 + body_w * 0.9, top + h * 0.85), (x0 + body_w * 0.1, top + h * 0.85)],
           (250, 250, 252, 255))
    s.ell(x0 + body_w / 2, top, body_w / 2, h * 0.07, (240, 240, 245, 255))
    s.ell(x0 + body_w / 2, top + 2, body_w / 2 - 5, h * 0.055, COFFEE)
    # handle
    s.ell(x0 + body_w + h * 0.08, top + h * 0.35, h * 0.14, h * 0.18, (250, 250, 252, 255))
    s.ell(x0 + body_w + h * 0.08, top + h * 0.35, h * 0.07, h * 0.1, (0, 0, 0, 0))
    s.ell(x0 + body_w / 2, top + h * 0.88, body_w * 0.62, h * 0.05, (225, 225, 232, 255))
    # steam
    for k in range(3):
        xs = x0 + body_w * (0.3 + 0.2 * k)
        pts = []
        for i in range(12):
            u = i / 11
            pts.append((xs + h * 0.05 * math.sin(t * 3 + u * 6 + k), top - h * 0.08 - u * h * 0.42))
        s.line(pts, (255, 255, 255, 120), max(2, h * 0.025))
    im = s.img()
    if small:
        return im
    return im


def can_sprite(h, t, big=False):
    w = h * 0.5
    s = SS(w + 8, h + 8)
    x0, y0 = 4, 4
    s.rect(x0, y0 + h * 0.04, x0 + w, y0 + h, w * 0.14, (40, 50, 60, 255))
    s.rect(x0 + 3, y0 + h * 0.06, x0 + w - 3, y0 + h - 3, w * 0.12, (130, 240, 80, 255))
    s.rect(x0 + 3, y0 + h * 0.28, x0 + w - 3, y0 + h * 0.72, 4, (25, 30, 40, 255))
    bolt = [(0.58, 0.31), (0.36, 0.52), (0.5, 0.52), (0.42, 0.69), (0.66, 0.46), (0.52, 0.46)]
    s.poly([(x0 + w * a, y0 + h * b) for a, b in bolt], (255, 230, 40, 255))
    s.ell(x0 + w / 2, y0 + h * 0.05, w / 2 - 1, h * 0.04, (200, 205, 215, 255))
    s.ell(x0 + w * 0.32, y0 + h * 0.5, w * 0.06, h * 0.3, (255, 255, 255, 60))
    return s.img()


def espresso_sprite(h, t):
    return cup_sprite(h, t, small=True)


def sugar_cube(sz):
    s = SS(sz * 1.3, sz * 1.3)
    a = sz * 0.25
    s.poly([(a, a), (a + sz * 0.75, a), (a + sz * 1.0, a - sz * 0.0), (a + sz * 0.25, a)], (255, 255, 255, 255))
    s.rect(a * 0.6, a * 0.9, a * 0.6 + sz * 0.85, a * 0.9 + sz * 0.85, sz * 0.12, (252, 252, 255, 255))
    s.poly([(a * 0.6, a * 0.9), (a * 0.6 + sz * 0.25, a * 0.2), (a * 0.6 + sz * 1.1, a * 0.2),
            (a * 0.6 + sz * 0.85, a * 0.9)], (232, 236, 245, 255))
    for _ in range(6):
        r = random.Random(_)
        s.ell(a * 0.6 + r.uniform(0.15, 0.7) * sz, a * 0.9 + r.uniform(0.15, 0.7) * sz, 2, 2, (210, 215, 230, 255))
    return s.img()


def bar(img, cx, bottom, h_px, color, w=110, a=1.0):
    if h_px <= 1 or a <= 0.01:
        return
    rrect(img, (cx - w / 2, bottom - h_px, cx + w / 2, bottom), 18, color + (int(255 * a),))
    rrect(img, (cx - w / 2 + 10, bottom - h_px + 8, cx - w / 2 + 26, bottom - 8), 8, (255, 255, 255, int(70 * a)))


def sc_hook(img, sc, t, gt):
    header(img, gt, "", t)
    panel_labels(img, t)
    t_m = wt(sc, "mehr")
    pl = back_out(prog(t, 0.0, 0.4))
    paste_c(img, cup_sprite(200 * pl + 1, gt), CXL - 30, VIS_Y)
    pr = back_out(prog(t, 0.1, 0.4))
    paste_c(img, can_sprite(330 * pr + 1, gt), CXR, VIS_Y)
    q = back_out(prog(t, t_m, 0.35))
    text(img, ">", 200, SPLIT, VIS_Y - 20, fill=E.C_HI, scale=q * (1 + 0.08 * math.sin(gt * 9)), stroke=10)
    text(img, "?", 110, SPLIT, VIS_Y + 150, fill=E.WHITE, scale=back_out(prog(t, t_m + 0.4, 0.3)), stroke=8)


def sc_koffein(img, sc, t, gt):
    header(img, gt, "RUNDE 1 · KOFFEIN", t)
    panel_labels(img, t)
    t_t, t_90 = wt(sc, "Tasse"), wt(sc, "neunzig")
    t_d, t_80 = wt(sc, "Dose"), wt(sc, "achtzig")
    base = 990
    ppm = 4.2
    pl = back_out(prog(t, t_t - 0.2, 0.4))
    if pl > 0.02:
        paste_c(img, cup_sprite(150 * pl, gt), CXL - 95, base, anchor="b")
    pr = back_out(prog(t, t_d - 0.2, 0.4))
    if pr > 0.02:
        paste_c(img, can_sprite(210 * pr, gt), CXR - 95, base, anchor="b")
    bar(img, CXL + 85, base, 90 * ppm * ease_out(prog(t, t_90, 0.8)), C_L)
    bar(img, CXR + 85, base, 80 * ppm * ease_out(prog(t, t_80, 0.8)), C_R)
    vs_badge(img, gt, ease_out(prog(t, 0.3, 0.3)), y=520)
    counter(img, CXL, f"{int(round(90 * ease_out(prog(t, t_90, 0.8))))} mg", "Filterkaffee (200 ml)", C_L,
            ease_out(prog(t, t_90, 0.3)))
    counter(img, CXR, f"{int(round(80 * ease_out(prog(t, t_80, 0.8))))} mg", "Dose (250 ml)", C_R,
            ease_out(prog(t, t_80, 0.3)))
    burst(img, CXL + 85, base - 90 * ppm, t, t_80 + 0.6, color=C_L, rad=160)


def sc_espresso(img, sc, t, gt):
    header(img, gt, "RUNDE 2 · ESPRESSO", t)
    panel_labels(img, t)
    t_e, t_80, t_g, t_u = wt(sc, "Espresso", 2), wt(sc, "achtzig"), wt(sc, "Genauso"), wt(sc, "Unentschieden")
    base = 990
    ppm = 4.2
    pl = back_out(prog(t, t_e - 0.3, 0.4))
    if pl > 0.02:
        paste_c(img, espresso_sprite(95 * pl, gt), CXL - 95, base, anchor="b")
    pr = ease_out(prog(t, 0.2, 0.4))
    paste_c(img, can_sprite(210, gt), CXR - 95, base, alpha=pr, anchor="b")
    bar(img, CXL + 85, base, 80 * ppm * ease_out(prog(t, t_80, 0.8)), C_L)
    bar(img, CXR + 85, base, 80 * ppm * pr, C_R, a=pr)
    if t > t_g:
        a = ease_out(prog(t, t_g, 0.3))
        d = ImageDraw.Draw(img)
        y = base - 80 * ppm
        x = 40
        while x < 900 * a:
            d.line((x, y, x + 20, y), fill=E.C_HI, width=5)
            x += 34
    counter(img, CXL, "80 mg", "Espresso (60 ml)", C_L, ease_out(prog(t, t_80, 0.3)))
    counter(img, CXR, "80 mg", "Dose (250 ml)", C_R, ease_out(prog(t, 0.4, 0.3)))
    stamp(img, "=", t, t_g, cy=VIS_Y - 160, size=170, rot=0)
    if t > t_u:
        text(img, "UNENTSCHIEDEN!", 64, SPLIT, VIS_Y - 20, fill=E.WHITE, stroke=8, sfill=(150, 20, 0),
             scale=back_out(prog(t, t_u, 0.35)), rotate=-6)


def sc_grenze(img, sc, t, gt):
    header(img, gt, "RUNDE 3 · TAGESGRENZE", t)
    panel_labels(img, t)
    t_400, t_4, t_5 = wt(sc, "vierhundert"), wt(sc, "vier"), wt(sc, "fünf")
    base = 1000
    ppm = 1.15
    lim_y = base - 400 * ppm
    a = ease_out(prog(t, t_400 - 0.1, 0.4))
    if a > 0:
        d = ImageDraw.Draw(img)
        x = 30
        while x < 30 + 880 * a:
            d.line((x, lim_y, x + 24, lim_y), fill=(255, 80, 80), width=6)
            x += 38
        text(img, "max. 400 mg pro Tag (EFSA, Erwachsene)", 32, SPLIT, lim_y - 34, fill=(255, 140, 140), alpha=a,
             stroke=4, path=FONT_XB)
    nl = clamp((t - (t_4 - 0.2)) / 0.8) * 4 if t > t_4 - 0.2 else 0
    for k in range(int(math.ceil(nl))):
        y = base - (k + 1) * 90 * ppm
        p = clamp(nl - k)
        rrect(img, (CXL - 60, y, CXL + 60, y + 90 * ppm - 4), 10, C_L + (int(255 * p),))
        text(img, "90 mg", 26, CXL, y + 45 * ppm, fill=(40, 20, 10), alpha=p, path=FONT_XB)
    nr = clamp((t - (t_5 - 0.2)) / 0.9) * 5 if t > t_5 - 0.2 else 0
    for k in range(int(math.ceil(nr))):
        y = base - (k + 1) * 80 * ppm
        p = clamp(nr - k)
        rrect(img, (CXR - 60, y, CXR + 60, y + 80 * ppm - 4), 10, C_R + (int(255 * p),))
        text(img, "80 mg", 26, CXR, y + 40 * ppm, fill=(20, 40, 10), alpha=p, path=FONT_XB)
    if t < t_4:
        paste_c(img, cup_sprite(120, gt), CXL, base, alpha=ease_out(prog(t, 0.2, 0.3)), anchor="b")
        paste_c(img, can_sprite(170, gt), CXR, base, alpha=ease_out(prog(t, 0.2, 0.3)), anchor="b")
    counter(img, CXL, "4 Tassen", "≈ 360 mg", C_L, ease_out(prog(t, t_4, 0.3)))
    counter(img, CXR, "5 Dosen", "= 400 mg", C_R, ease_out(prog(t, t_5, 0.3)))


def sc_finale(img, sc, t, gt):
    t_k = wt(sc, "Klarer")
    header(img, gt, "FINALE · ZUCKER", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    if t < t_k:
        panel_labels(img, t)
    t_s, t_0, t_d, t_60, t_20 = wt(sc, "Schwarzer"), wt(sc, "null"), wt(sc, "große"), wt(sc, "sechzig"), \
        wt(sc, "zwanzig")
    pl = back_out(prog(t, t_s - 0.2, 0.4))
    if pl > 0.02:
        paste_c(img, cup_sprite(200 * pl, gt), CXL, 760, anchor="b")
    pr = back_out(prog(t, t_d - 0.2, 0.45))
    if pr > 0.02:
        paste_c(img, can_sprite(330 * pr, gt), CXR, 760, anchor="b")
    counter(img, CXL, "0 g", "Zucker (schwarz)", C_L, ease_out(prog(t, t_0, 0.3)))
    counter(img, CXR, f"≈ {int(round(60 * ease_out(prog(t, t_60, 0.8))))} g", "Zucker (500-ml-Dose)", C_R,
            ease_out(prog(t, t_60, 0.3)))
    if t > t_20 - 0.2:
        n = int(clamp((t - (t_20 - 0.2)) / 1.0) * 20 + 0.999)
        cube = sugar_cube(46)
        for k in range(n):
            r, c = divmod(k, 10)
            x = 95 + c * 82
            y = 830 + r * 72
            paste_c(img, cube, x, y)
        text(img, f"{n} Würfelzucker", 44, SPLIT, 990, fill=E.WHITE, stroke=5, path=FONT_XB)
    if t > t_k:
        crown(img, CXL, 470, prog(t, t_k, 0.5), size=0.55)
        winner(img, t, t_k, "KAFFEE", cy=420)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, cup_sprite(150, g), x, y, a)

    def mr(im, x, y, a, g):
        paste_c(im, can_sprite(190, g), x, y, a)

    E.outro(img, sc, t, gt, ml, mr, line1="Dein Team?", line2="Schreib's uns!")


E.setup(
    here=HERE, out="kaffee_vs_energydrink.mp4",
    name_l="KAFFEE", name_r="ENERGYDRINK", col_l=C_L, col_r=C_R,
    bg_l=((30, 14, 6), (100, 52, 22)), bg_r=((4, 24, 18), (16, 90, 48)),
    scenes=["hook", "koffein", "espresso", "grenze", "finale", "outro"],
    draw=dict(hook=sc_hook, koffein=sc_koffein, espresso=sc_espresso, grenze=sc_grenze, finale=sc_finale,
              outro=sc_outro),
    sub_map=[
        (("neunzig",), "90"), (("achtzig",), "80"), (("vierhundert",), "400"), (("vier",), "4"), (("fünf",), "5"),
        (("null",), "0"), (("sechzig",), "60"), (("zwanzig",), "20"),
        (("eins",), "1"), (("zwei",), "2"), (("drei",), "3"),
    ],
    score=[(1, "achtzig", 1, "L"), (2, "Unentschieden", 1, "B"), (4, "Sieger", 1, "L")],
    ticks=[(1, "neunzig", 1, 0.7), (1, "achtzig", 1, 0.7), (4, "zwanzig", 1, 1.0)],
)

if __name__ == "__main__":
    E.main()

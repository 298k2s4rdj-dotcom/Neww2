#!/usr/bin/env python3
"""Eiffelturm vs. Burj Khalifa – animated German TikTok comparison."""
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tiere"))
import engine as E  # noqa: E402
from engine import (CXL, CXR, SPLIT, VIS_Y, NUM_Y, GROUND, SS, back_out, clamp, counter, ease_io,  # noqa: E402
                    ease_out, header, panel_labels, paste_c, prog, stamp, burst, text, vs_badge, wt, rrect,
                    crown, winner, ruler, FONT_XB)

C_L = (245, 165, 85)      # Eiffelturm
C_R = (120, 220, 255)     # Burj Khalifa


def eiffel_sprite(h, levels_lit=0.0):
    w = h * 0.42
    s = SS(w + 6, h + 6)
    col = (190, 120, 70, 255)
    dark = (120, 70, 40, 255)
    cx = (w + 6) / 2

    def half(yf):  # half width at height fraction yf (0 bottom .. 1 top)
        return (w / 2) * (1 - min(yf, 0.97)) ** 2.3 + h * 0.008

    pts_l, pts_r = [], []
    for i in range(41):
        yf = i / 40 * 0.9
        y = h + 3 - yf * h
        hw = half(yf)
        pts_l.append((cx - hw, y))
        pts_r.append((cx + hw, y))
    s.poly(pts_l + pts_r[::-1], col)
    # arch between the legs
    s.ell(cx, h + 3, half(0.0) * 0.62, h * 0.12, (0, 0, 0, 0))
    # lattice
    for i in range(0, 36):
        yf0, yf1 = i / 40 * 0.9, (i + 1) / 40 * 0.9
        y0, y1 = h + 3 - yf0 * h, h + 3 - yf1 * h
        s.line([(cx - half(yf0), y0), (cx + half(yf1), y1)], dark, max(1, h * 0.004))
        s.line([(cx + half(yf0), y0), (cx - half(yf1), y1)], dark, max(1, h * 0.004))
    # platforms (levels at ~57 m, 116 m, 276 m of 330 m)
    for k, yf in enumerate((0.17, 0.35, 0.84)):
        y = h + 3 - yf * h
        hw = half(yf) * 1.25 + h * 0.01
        c = (255, 226, 60, 255) if levels_lit > k else dark
        s.rect(cx - hw, y - h * 0.012, cx + hw, y + h * 0.012, h * 0.004, c)
    # antenna
    s.rect(cx - h * 0.005, 3, cx + h * 0.005, h + 3 - 0.9 * h, 1, dark)
    return s.img()


def burj_sprite(h, floors_lit=0.0):
    w = h * 0.16
    s = SS(w + 6, h + 6)
    cx = (w + 6) / 2
    glass = (170, 200, 225, 255)
    edge = (110, 140, 170, 255)
    steps = [(0.00, 1.00), (0.12, 0.86), (0.25, 0.72), (0.38, 0.58), (0.50, 0.46), (0.62, 0.34), (0.72, 0.24),
             (0.80, 0.14)]
    for i, (yf, wf) in enumerate(steps):
        y0 = h + 3 - yf * h
        y1 = h + 3 - (steps[i + 1][0] if i + 1 < len(steps) else 0.86) * h
        s.rect(cx - w / 2 * wf, y1, cx + w / 2 * wf, y0, 2, glass)
        s.line([(cx - w / 2 * wf, y1), (cx - w / 2 * wf, y0)], edge, max(1, h * 0.003))
    # spire
    s.poly([(cx - w * 0.05, h + 3 - 0.86 * h), (cx + w * 0.05, h + 3 - 0.86 * h), (cx, 3)], edge)
    # lit floors (bottom-up)
    if floors_lit > 0:
        n = int(163 * clamp(floors_lit))
        for f in range(0, n, 3):
            yf = f / 163 * 0.8
            wf = next((b for a, b in reversed(steps) if a <= yf), 1.0)
            y = h + 3 - yf * h
            s.line([(cx - w / 2 * wf + 2, y), (cx + w / 2 * wf - 2, y)], (255, 226, 60, 255), max(1, h * 0.002))
    s.line([(cx, h + 3), (cx, h + 3 - 0.86 * h)], (230, 240, 255, 160), max(1, h * 0.004))
    return s.img()


def sc_hook(img, sc, t, gt):
    header(img, gt, "", t)
    panel_labels(img, t)
    t_g = wt(sc, "Gebäude")
    ge = ease_out(prog(t, 0.0, 0.6))
    if ge > 0.02:
        paste_c(img, eiffel_sprite(330 * ge), CXL, GROUND, anchor="b")
    gb = ease_out(prog(t, 0.3, 0.9))
    if gb > 0.02:
        paste_c(img, burj_sprite(560 * gb, floors_lit=gb), CXR, GROUND, anchor="b")
    vs_badge(img, gt, ease_out(prog(t, 0.2, 0.3)), y=VIS_Y + 120)
    text(img, "Wer gewinnt?", 60, SPLIT, NUM_Y + 30, fill=E.C_HI, stroke=6, scale=back_out(prog(t, t_g, 0.35)))


def sc_bauzeit(img, sc, t, gt):
    header(img, gt, "RUNDE 1 · BAUZEIT", t)
    panel_labels(img, t)
    t_e, t_2, t_b, t_6 = wt(sc, "Eiffelturm"), wt(sc, "zwei"), wt(sc, "Burj"), wt(sc, "sechs")
    base = 1000
    ppy = 85
    fe = ease_out(prog(t, t_e, 0.9))
    fb = ease_out(prog(t, t_b, 1.4))
    # towers growing like construction
    if fe > 0.02:
        paste_c(img, eiffel_sprite(300 * fe), CXL - 70, base, anchor="b")
    if fb > 0.02:
        paste_c(img, burj_sprite(480 * fb, floors_lit=fb), CXR - 80, base, anchor="b")
    for cx, years, f, col in ((CXL + 120, 2.17, fe, C_L), (CXR + 90, 6.0, fb, C_R)):
        hpx = years * ppy * f
        if hpx > 2:
            rrect(img, (cx - 45, base - hpx, cx + 45, base), 14, col + (255,))
        for y in range(1, int(years * f) + 1):
            d = ImageDraw.Draw(img)
            d.line((cx - 45, base - y * ppy, cx + 45, base - y * ppy), fill=(40, 30, 30), width=3)
    counter(img, CXL, "gut 2 Jahre", "1887 – 1889", C_L, ease_out(prog(t, t_2, 0.3)), size=56)
    counter(img, CXR, "≈ 6 Jahre", "2004 – 2010", C_R, ease_out(prog(t, t_6, 0.3)), size=56)
    burst(img, CXL, 700, t, wt(sc, "Punkt"), color=C_L, rad=200)


def sc_alter(img, sc, t, gt):
    header(img, gt, "RUNDE 2 · ALTER", t)
    panel_labels(img, t)
    t_89, t_10, t_k = wt(sc, "achtzehnhundertneunundachtzig"), wt(sc, "zweitausendzehn"), wt(sc, "Klassiker")
    y = 760
    x0, x1 = 70, 900
    y_from, y_to = 1880, 2020

    def X(year):
        return x0 + (x1 - x0) * (year - y_from) / (y_to - y_from)

    a = ease_out(prog(t, 0.2, 0.5))
    d = ImageDraw.Draw(img)
    d.line((x0, y, x0 + (x1 - x0) * a, y), fill=(255, 255, 255), width=6)
    for yr in range(1880, 2021, 20):
        if X(yr) <= x0 + (x1 - x0) * a:
            d.line((X(yr), y - 14, X(yr), y + 14), fill=(255, 255, 255), width=4)
            text(img, str(yr), 26, X(yr), y + 44, fill=(220, 220, 235), path=FONT_XB)
    if t > t_89 - 0.2:
        p = back_out(prog(t, t_89 - 0.2, 0.5))
        paste_c(img, eiffel_sprite(220 * clamp(p, 0, 1.1)), X(1889), y - 10, anchor="b")
        text(img, "1889", 50, X(1889) + 10, y - 260, fill=C_L, stroke=5, scale=p)
    if t > t_10 - 0.2:
        p = back_out(prog(t, t_10 - 0.2, 0.5))
        paste_c(img, burj_sprite(240 * clamp(p, 0, 1.1)), X(2010), y - 10, anchor="b")
        text(img, "2010", 50, X(2010) - 30, y - 290, fill=C_R, stroke=5, scale=p)
    if t > t_10 + 0.3:
        q = ease_out(prog(t, t_10 + 0.3, 0.6))
        d.line((X(1889), y - 90, X(1889) + (X(2010) - X(1889)) * q, y - 90), fill=E.C_HI, width=6)
        if q > 0.95:
            text(img, "121 Jahre", 44, (X(1889) + X(2010)) / 2, y - 125, fill=E.C_HI, stroke=5, path=FONT_XB)
    counter(img, CXL, "1889", "fertiggestellt", C_L, ease_out(prog(t, t_89, 0.3)))
    counter(img, CXR, "2010", "eröffnet", C_R, ease_out(prog(t, t_10, 0.3)))
    stamp(img, "Klassiker!", t, t_k, cx=CXL, cy=900, size=80, rot=-8)


def sc_etagen(img, sc, t, gt):
    header(img, gt, "RUNDE 3 · ETAGEN", t)
    panel_labels(img, t)
    t_3, t_b, t_163 = wt(sc, "drei", 2), wt(sc, "Burj"), wt(sc, "hundertdreiundsechzig")
    lit = 3 * clamp((t - t_3 + 0.1) / 0.6) if t > t_3 - 0.1 else 0
    paste_c(img, eiffel_sprite(520, levels_lit=lit), CXL, GROUND, ease_out(prog(t, 0.1, 0.4)), anchor="b")
    f = ease_out(prog(t, t_163 - 0.1, 1.2))
    paste_c(img, burj_sprite(590, floors_lit=f), CXR, GROUND, ease_out(prog(t, t_b - 0.3, 0.4)), anchor="b")
    counter(img, CXL, f"{int(math.ceil(lit))}", "Ebenen zum Besuchen", C_L, ease_out(prog(t, t_3, 0.3)))
    counter(img, CXR, f"{int(round(163 * f))}", "Stockwerke", C_R, ease_out(prog(t, t_163, 0.3)))
    burst(img, CXR, 620, t, wt(sc, "Stockwerke"), color=C_R, rad=200)


def sc_finale(img, sc, t, gt):
    t_k = wt(sc, "Klarer")
    header(img, gt, "FINALE · HÖHE", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    if 0.3 < t < t_k:
        text(img, "Finale zählt doppelt!", 34, SPLIT, 350, fill=E.C_HI, stroke=4, path=FONT_XB,
             alpha=ease_out(prog(t, 0.3, 0.3)))
    t_e, t_330, t_b, t_828, t_25 = wt(sc, "Eiffelturm"), wt(sc, "dreihundertdreißig"), wt(sc, "Burj"), \
        wt(sc, "achthundertachtundzwanzig"), wt(sc, "zweieinhalb")
    ppm = 560 / 828
    ruler_a = ease_out(prog(t, 0.2, 0.4))
    # ruler every 100 m
    d = ImageDraw.Draw(img)
    if ruler_a > 0:
        d.line((60, GROUND, 60, GROUND - 828 * ppm), fill=(255, 255, 255), width=3)
        for m in range(0, 801, 100):
            yy = GROUND - m * ppm
            d.line((60, yy, 78, yy), fill=(255, 255, 255), width=3)
            text(img, f"{m} m", 22, 86, yy, fill=(220, 220, 235), path=FONT_XB, anchor="lm")
    fe = ease_out(prog(t, t_e - 0.2, 0.8))
    if fe > 0.02:
        paste_c(img, eiffel_sprite(330 * ppm * fe), CXL, GROUND, anchor="b")
    fb = ease_out(prog(t, t_b - 0.2, 1.2))
    if fb > 0.02:
        paste_c(img, burj_sprite(828 * ppm * fb, floors_lit=fb), CXR, GROUND, anchor="b")
    # 2.5 Eiffel towers stacked next to the Burj
    if t > t_25 - 0.2:
        for k in range(3):
            p = ease_out(prog(t, t_25 - 0.2 + k * 0.2, 0.3))
            if p <= 0:
                continue
            hh = 330 * ppm
            spr = eiffel_sprite(hh)
            if k == 2:
                spr = spr.crop((0, int(spr.size[1] * 0.5), spr.size[0], spr.size[1]))
            paste_c(img, spr, CXR - 150, GROUND - k * hh, alpha=0.75 * p, anchor="b")
        text(img, "2,5×", 56, CXR - 150, GROUND - 828 * ppm - 40, fill=C_L, stroke=6,
             alpha=ease_out(prog(t, t_25 + 0.4, 0.3)))
    counter(img, CXL, f"{int(round(330 * ease_out(prog(t, t_330, 0.8))))} m", "Eiffelturm", C_L,
            ease_out(prog(t, t_330, 0.3)))
    counter(img, CXR, f"{int(round(828 * ease_out(prog(t, t_828, 1.0))))} m", "Burj Khalifa", C_R,
            ease_out(prog(t, t_828, 0.3)))
    if t > t_k:
        crown(img, CXR + 5, GROUND - 828 * ppm - 80, prog(t, t_k, 0.5), size=0.5)
        winner(img, t, t_k, "BURJ KHALIFA", cy=700)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, eiffel_sprite(200), x, y + 90, a, anchor="b")

    def mr(im, x, y, a, g):
        paste_c(im, burj_sprite(260, floors_lit=1.0), x, y + 100, a, anchor="b")

    E.outro(img, sc, t, gt, ml, mr, line1="Paris oder Dubai?", line2="Schreib's uns!")


E.setup(
    here=HERE, out="eiffelturm_vs_burj_khalifa.mp4",
    name_l="EIFFELTURM", name_r="BURJ KHALIFA", col_l=C_L, col_r=C_R,
    bg_l=((30, 16, 10), (110, 60, 30)), bg_r=((6, 14, 32), (20, 60, 110)),
    scenes=["hook", "bauzeit", "alter", "etagen", "finale", "outro"],
    draw=dict(hook=sc_hook, bauzeit=sc_bauzeit, alter=sc_alter, etagen=sc_etagen, finale=sc_finale, outro=sc_outro),
    sub_map=[
        (("achtzehnhundertneunundachtzig",), "1889"), (("zweitausendzehn",), "2010"),
        (("hundertdreiundsechzig",), "163"), (("dreihundertdreißig",), "330"),
        (("achthundertachtundzwanzig",), "828"), (("zweieinhalb",), "2,5"), (("sechs",), "6"),
        (("eins",), "1"), (("zwei",), "2"), (("drei",), "3"),
    ],
    score=[(1, "Paris", 1, "L"), (2, "Klassiker", 1, "L"), (3, "Stockwerke", 1, "R"), (4, "Sieger", 1, "R"),
           (4, "Burj", 2, "R")],
    ticks=[(4, "dreihundertdreißig", 1, 0.8), (4, "achthundertachtundzwanzig", 1, 1.0), (3, "hundertdreiundsechzig", 1, 1.0)],
)

if __name__ == "__main__":
    E.main()

#!/usr/bin/env python3
"""ENIAC (1946) vs. Smartphone – animated German TikTok comparison."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tiere"))
import engine as E  # noqa: E402
from engine import (CXL, CXR, SPLIT, VIS_Y, NUM_Y, GROUND, SS, back_out, clamp, counter, ease_io,  # noqa: E402
                    ease_out, fmt_int, header, panel_labels, paste_c, person_icon, prog, stamp, burst, text,
                    vs_badge, wt, rrect, crown, winner, FONT_XB)

C_L = (255, 165, 70)      # ENIAC
C_R = (80, 220, 255)      # Smartphone


def eniac_sprite(w, h, t, panels=4):
    s = SS(w, h)
    pw = w / panels
    r = random.Random(5)
    for p in range(panels):
        x0 = p * pw + 3
        s.rect(x0, 0, x0 + pw - 6, h, 6, (70, 70, 78, 255))
        s.rect(x0 + 6, 6, x0 + pw - 12, h * 0.12, 3, (45, 45, 50, 255))
        rows, cols = 6, 4
        for i in range(rows):
            for j in range(cols):
                cx = x0 + (j + 0.75) * (pw - 6) / (cols + 0.5)
                cy = h * 0.2 + i * h * 0.1
                on = 0.5 + 0.5 * math.sin(t * 7 + r.random() * 30)
                col = (255, int(120 + 100 * on), 40, 255)
                s.ell(cx, cy, pw * 0.055, pw * 0.055, col)
        for j in range(3):
            s.ell(x0 + (j + 0.7) * pw / 3.3, h * 0.85, pw * 0.07, pw * 0.07, (225, 225, 230, 255))
        s.line([(x0 + pw * 0.15, h * 0.78), (x0 + pw * 0.85, h * 0.72)], (30, 30, 30, 255), max(1, pw * 0.02))
    return s.img()


def phone_sprite(h, t):
    w = h * 0.48
    s = SS(w + 4, h + 4)
    s.rect(2, 2, w + 2, h + 2, w * 0.17, (25, 25, 30, 255))
    s.rect(2 + w * 0.05, 2 + w * 0.05, w + 2 - w * 0.05, h + 2 - w * 0.05, w * 0.13, (40, 90, 200, 255))
    for k in range(5):
        y = 2 + h * (0.2 + 0.14 * k)
        a = int(160 + 60 * math.sin(t * 2 + k))
        s.rect(2 + w * 0.15, y, 2 + w * (0.35 + 0.08 * k % 0.5), y + h * 0.08, w * 0.04, (120, 200, 255, a))
    s.rect(2 + w * 0.36, 2 + w * 0.09, 2 + w * 0.64, 2 + w * 0.17, w * 0.04, (10, 10, 12, 255))
    return s.img()


def elephant_icon(h, color=(170, 170, 190, 255)):
    s = SS(h * 1.4, h)
    s.ell(h * 0.8, h * 0.45, h * 0.5, h * 0.33, color)
    s.ell(h * 0.32, h * 0.38, h * 0.24, h * 0.24, color)
    s.thick([(h * 0.15, h * 0.4), (h * 0.08, h * 0.7), (h * 0.12, h * 0.92)], [h * 0.14, h * 0.1, h * 0.08], color)
    for x in (0.5, 0.7, 0.95, 1.12):
        s.rect(h * (x - 0.07), h * 0.6, h * (x + 0.07), h * 0.98, h * 0.03, color)
    s.ell(h * 0.42, h * 0.38, h * 0.12, h * 0.18, (140, 135, 160, 255))
    return s.img()


def scale_dev(img, cx, y, reading, color, a=1.0, w=170):
    rrect(img, (cx - w, y, cx + w, y + 26), 10, (230, 230, 240, int(255 * a)))
    rrect(img, (cx - 140, y + 40, cx + 140, y + 120), 16, (15, 20, 30, int(255 * a)), outline=color + (int(255 * a),),
          width=5)
    text(img, reading, 46, cx, y + 80, fill=(120, 255, 140), alpha=a)


def beam(img, tilt, py=820):
    L = 265
    lx, ly = SPLIT - L * math.cos(tilt), py - L * math.sin(tilt)
    rx, ry = SPLIT + L * math.cos(tilt), py + L * math.sin(tilt)
    layer = Image.new("RGBA", (E.W, E.H))
    d = ImageDraw.Draw(layer)
    d.polygon([(SPLIT, py), (SPLIT - 60, py + 200), (SPLIT + 60, py + 200)], fill=(220, 220, 235, 255))
    d.line((lx, ly, rx, ry), fill=(240, 240, 250, 255), width=16)
    d.ellipse((SPLIT - 16, py - 16, SPLIT + 16, py + 16), fill=(255, 226, 60, 255))
    for (x, y) in ((lx, ly), (rx, ry)):
        d.rounded_rectangle((x - 130, y - 8, x + 130, y + 8), 8, fill=(220, 220, 235, 255))
    img.paste(layer, (0, 0), layer)
    return (lx, ly - 8), (rx, ry - 8)


def sc_hook(img, sc, t, gt):
    header(img, gt, "", t)
    panel_labels(img, t)
    t_s, t_v, t_e = wt(sc, "schwerer"), wt(sc, "vier"), wt(sc, "Elefanten")
    tilt = -0.18 * ease_out(prog(t, t_s, 0.6))
    (lx, ly), (rx, ry) = beam(img, tilt)
    paste_c(img, eniac_sprite(240, 190, gt, panels=3), lx, ly, ease_out(prog(t, 0.0, 0.3)), anchor="b")
    n = int(clamp((t - (t_v - 0.1)) / 0.6) * 4 + 0.999) if t > t_v - 0.1 else 0
    ic = elephant_icon(62)
    for k in range(n):
        r, c = divmod(k, 2)
        paste_c(img, ic, rx - 50 + c * 95, ry - r * 64, anchor="b")
    if t > t_e:
        text(img, "4 × 6 t = 24 t", 36, CXR, 560, fill=(220, 220, 235), stroke=4, path=FONT_XB,
             alpha=ease_out(prog(t, t_e, 0.3)))
        text(img, "27 t", 70, CXL, 520, fill=C_L, stroke=6, scale=back_out(prog(t, t_e, 0.3)))


def sc_gewicht(img, sc, t, gt):
    header(img, gt, "RUNDE 1 · GEWICHT", t)
    panel_labels(img, t)
    t_e, t_27, t_i, t_187 = wt(sc, "Eniac"), wt(sc, "siebenundzwanzig"), wt(sc, "iPhone"), \
        wt(sc, "hundertsiebenundachtzig")
    sy = 860
    a = ease_out(prog(t, t_e - 0.2, 0.4))
    paste_c(img, eniac_sprite(380, 300, gt), CXL, sy, a, anchor="b")
    scale_dev(img, CXL, sy, f"{fmt_int(27000 * ease_out(prog(t, t_27, 1.0)))} kg", C_L, a, w=200)
    b = ease_out(prog(t, t_i - 0.2, 0.4))
    paste_c(img, phone_sprite(170 * back_out(prog(t, t_i - 0.2, 0.4)) + 1, gt), CXR, sy, b, anchor="b")
    scale_dev(img, CXR, sy, f"{int(round(187 * ease_out(prog(t, t_187, 0.8))))} g", C_R, b)
    counter(img, CXL, "≈ 27 t", "ENIAC (1946)", C_L, ease_out(prog(t, t_27, 0.3)), y=NUM_Y + 20)
    counter(img, CXR, "187 g", "iPhone 15 Pro", C_R, ease_out(prog(t, t_187, 0.3)), y=NUM_Y + 20)


def sc_groesse(img, sc, t, gt):
    header(img, gt, "RUNDE 2 · GRÖSSE", t)
    panel_labels(img, t)
    t_r, t_9, t_h, t_ht = wt(sc, "Raum"), wt(sc, "neun"), wt(sc, "Handy"), wt(sc, "Hosentasche")
    a = ease_out(prog(t, t_r - 0.3, 0.4))
    ppm = 26
    rw, rh = 9 * ppm, 15 * ppm
    x0, y0 = CXL - rw / 2, 520
    if a > 0:
        rrect(img, (x0, y0, x0 + rw, y0 + rh), 6, (255, 255, 255, int(30 * a)), outline=(255, 255, 255, int(220 * a)),
              width=4)
        # U-shaped row of cabinets along three walls
        d = ImageDraw.Draw(img)
        g = ease_out(prog(t, t_r, 0.9))
        cab = (C_L[0], C_L[1], C_L[2])
        for k in range(int(12 * g)):
            yy = y0 + 20 + k * 28
            d.rectangle((x0 + 12, yy, x0 + 36, yy + 22), fill=cab)
            d.rectangle((x0 + rw - 36, yy, x0 + rw - 12, yy + 22), fill=cab)
        for k in range(int(6 * g)):
            xx = x0 + 44 + k * 25
            d.rectangle((xx, y0 + 12, xx + 20, y0 + 36), fill=cab)
        paste_c(img, person_icon(int(1.8 * ppm), (230, 230, 240)), CXL, y0 + rh - 40)
        text(img, "9 m", 34, CXL, y0 + rh + 30, alpha=prog(t, t_9, 0.3), path=FONT_XB)
        text(img, "15 m", 34, x0 - 40, y0 + rh / 2, alpha=prog(t, t_9, 0.3), path=FONT_XB, rotate=90)
    b = ease_out(prog(t, t_h - 0.3, 0.4))
    if b > 0:
        s = SS(300, 340)
        s.poly([(10, 10), (290, 10), (280, 250), (150, 330), (20, 250)], (40, 80, 160, 255))
        s.line([(28, 28), (272, 28), (264, 240), (150, 312), (36, 240), (28, 28)], (230, 180, 80, 255), 4)
        pocket = s.img()
        slide = ease_io(prog(t, t_ht - 0.2, 0.6))
        ph = phone_sprite(200, gt)
        paste_c(img, ph, CXR, 520 + 180 * slide, b)
        paste_c(img, pocket, CXR, 760, b)
    counter(img, CXL, "≈ 9 × 15 m", "Raum für den ENIAC", C_L, ease_out(prog(t, t_9, 0.3)))
    counter(img, CXR, "Hosentasche", "Smartphone", C_R, ease_out(prog(t, t_ht, 0.3)), size=58)


def sc_bauteile(img, sc, t, gt):
    header(img, gt, "RUNDE 3 · BAUTEILE", t)
    panel_labels(img, t)
    t_17, t_c, t_19 = wt(sc, "siebzehntausend"), wt(sc, "Chip"), wt(sc, "neunzehn")
    f = ease_out(prog(t, t_17 - 0.2, 1.0))
    d = ImageDraw.Draw(img)
    cols, rows = 10, 12
    n = int(cols * rows * f)
    for k in range(n):
        r, c = divmod(k, cols)
        x = CXL - 190 + c * 42
        y = 470 + r * 42
        on = 0.5 + 0.5 * math.sin(gt * 6 + k * 1.7)
        d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=(255, int(110 + 120 * on), 40))
        d.ellipse((x - 6, y - 9, x + 2, y - 3), fill=(255, 240, 200))
    ca = ease_out(prog(t, t_c - 0.2, 0.4))
    if ca > 0:
        cx, cy, R = CXR, 720, 170
        layer = Image.new("RGBA", (E.W, E.H))
        dl = ImageDraw.Draw(layer)
        for k in range(10):
            o = -R + 20 + k * (2 * R - 40) / 9
            for (x0, y0, x1, y1) in ((cx + o, cy - R - 26, cx + o, cy - R), (cx + o, cy + R, cx + o, cy + R + 26),
                                     (cx - R - 26, cy + o, cx - R, cy + o), (cx + R, cy + o, cx + R + 26, cy + o)):
                dl.line((x0, y0, x1, y1), fill=(200, 200, 210, int(255 * ca)), width=8)
        dl.rounded_rectangle((cx - R, cy - R, cx + R, cy + R), 22, fill=(30, 40, 60, int(255 * ca)),
                             outline=C_R + (int(255 * ca),), width=6)
        g = ease_out(prog(t, t_19 - 0.1, 1.0))
        step = 6
        for i in range(int((2 * R - 40) / step * g)):
            x = cx - R + 20 + i * step
            al = int(140 + 100 * math.sin(gt * 5 + i * 0.4))
            dl.line((x, cy - R + 20, x, cy + R - 20), fill=C_R + (al,), width=2)
        img.paste(layer, (0, 0), layer)
    v = 17000 * ease_out(prog(t, t_17, 1.0))
    counter(img, CXL, "über " + fmt_int(v), "Röhren", C_L, ease_out(prog(t, t_17, 0.3)), size=60)
    m = 19 * ease_out(prog(t, t_19, 1.0))
    counter(img, CXR, f"{int(round(m))} Mrd.", "Transistoren", C_R, ease_out(prog(t, t_19, 0.3)), size=60)


def gauge(img, cx, cy, R, frac, color, shake=0.0):
    layer = Image.new("RGBA", (E.W, E.H))
    d = ImageDraw.Draw(layer)
    d.pieslice((cx - R, cy - R, cx + R, cy + R), 180, 360, fill=(255, 255, 255, 30))
    d.arc((cx - R, cy - R, cx + R, cy + R), 180, 180 + 180 * clamp(frac), fill=color + (255,), width=26)
    d.arc((cx - R, cy - R, cx + R, cy + R), 180, 360, fill=(255, 255, 255, 90), width=4)
    for k in range(11):
        a = math.pi + k / 10 * math.pi
        d.line((cx + (R - 40) * math.cos(a), cy + (R - 40) * math.sin(a), cx + (R - 20) * math.cos(a),
                cy + (R - 20) * math.sin(a)), fill=(255, 255, 255, 200), width=4)
    a = math.pi + clamp(frac) * math.pi + shake
    d.line((cx, cy, cx + (R - 30) * math.cos(a), cy + (R - 30) * math.sin(a)), fill=(255, 80, 80, 255), width=10)
    d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=(240, 240, 250, 255))
    img.paste(layer, (0, 0), layer)


def big_num(v):
    if v >= 1e12:
        return E.fmt_dec(v / 1e12, 0 if v >= 1e13 else 1) + " Billionen"
    if v >= 1e9:
        return E.fmt_dec(v / 1e9, 0) + " Mrd."
    if v >= 1e6:
        return E.fmt_dec(v / 1e6, 0) + " Mio."
    return fmt_int(v)


def sc_finale(img, sc, t, gt):
    t_k = wt(sc, "Klarer")
    header(img, gt, "FINALE · TEMPO", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    if t < t_k:
        panel_labels(img, t)
    t_5, t_ki, t_35 = wt(sc, "fünftausend"), wt(sc, "KI-Chip"), wt(sc, "fünfunddreißig")
    gauge(img, CXL, 760, 190, 0.02 * ease_out(prog(t, t_5, 0.6)), C_L)
    f = ease_out(prog(t, t_35, 1.0))
    shake = 0.04 * math.sin(gt * 50) * (t > t_35 + 0.8)
    gauge(img, CXR, 760, 190, f, C_R, shake)
    paste_c(img, eniac_sprite(150, 110, gt, panels=2), CXL, 920, ease_out(prog(t, 0.2, 0.3)))
    paste_c(img, phone_sprite(130, gt), CXR, 920, ease_out(prog(t, t_ki - 0.2, 0.3)))
    counter(img, CXL, fmt_int(5000 * ease_out(prog(t, t_5, 0.6))), "Additionen/s", C_L,
            ease_out(prog(t, t_5, 0.3)), size=58, y=NUM_Y + 20)
    v = 35e12 * (f ** 3)
    counter(img, CXR, big_num(max(v, 5000)), "KI-Schritte/s", C_R, ease_out(prog(t, t_35, 0.3)),
            size=48, y=NUM_Y + 20)
    burst(img, CXR, 760, t, t_35 + 1.0, color=C_R, rad=230)
    if t > t_k:
        crown(img, CXR, 470, prog(t, t_k, 0.5), size=0.55)
        winner(img, t, t_k, "SMARTPHONE", cy=420)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, eniac_sprite(170, 130, g, panels=2), x, y, a)

    def mr(im, x, y, a, g):
        paste_c(im, phone_sprite(160, g), x, y, a)

    E.outro(img, sc, t, gt, ml, mr, line1="Computer in 80 Jahren?", line2="Schreib's uns!")


E.setup(
    here=HERE, out="eniac_vs_smartphone.mp4",
    name_l="ENIAC", name_r="SMARTPHONE", col_l=C_L, col_r=C_R,
    bg_l=((30, 18, 8), (95, 60, 26)), bg_r=((5, 10, 36), (18, 42, 105)),
    scenes=["hook", "gewicht", "groesse", "bauteile", "finale", "outro"],
    draw=dict(hook=sc_hook, gewicht=sc_gewicht, groesse=sc_groesse, bauteile=sc_bauteile, finale=sc_finale,
              outro=sc_outro),
    sub_map=[
        (("Eniac",), "ENIAC"), (("neunzehnhundertsechsundvierzig",), "1946"), (("siebenundzwanzig",), "27"),
        (("fünfzehn", "Pro"), "15 Pro"), (("hundertsiebenundachtzig",), "187"), (("neun",), "9"),
        (("fünfzehn",), "15"), (("siebzehntausend",), "17.000"), (("neunzehn",), "19"),
        (("fünftausend",), "5.000"), (("fünfunddreißig",), "35"), (("vier",), "4"), (("achtzig",), "80"),
        (("eins",), "1"), (("zwei",), "2"), (("drei",), "3"),
    ],
    score=[(1, "Gramm", 1, "R"), (2, "Hosentasche", 1, "R"), (3, "Transistoren", 1, "R"), (4, "Sieger", 1, "R")],
    ticks=[(1, "siebenundzwanzig", 1, 1.0), (3, "siebzehntausend", 1, 1.0), (4, "fünfunddreißig", 1, 1.0)],
)

if __name__ == "__main__":
    E.main()

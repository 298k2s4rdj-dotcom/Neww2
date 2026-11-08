#!/usr/bin/env python3
"""Rate mal (Test): Weißer Hai vs. Orca – animated German TikTok comparison."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tiere"))
import engine as E  # noqa: E402
from engine import (CXL, CXR, SPLIT, NUM_Y, SS, back_out, clamp, counter, ease_io, ease_out,  # noqa: E402
                    header, panel_labels, paste_c, prog, stamp, burst, text, vs_badge, wt, rrect, crown, winner,
                    brand, FONT_XB)

C_L = (100, 200, 255)     # Weißer Hai
C_R = (255, 120, 140)     # Orca
SHARK = (120, 140, 160, 255)
SHARK_D = (90, 108, 128, 255)
BELLY = (240, 244, 250, 255)
ORCA = (22, 24, 30, 255)
WHITE = (250, 250, 255, 255)


def shark_sprite(w, phase=0.0, mouth=0.0):
    """side view, facing right; w = body length in px"""
    h = w * 0.42
    s = SS(w, h)
    cy = h * 0.55
    sw = math.sin(phase) * 0.08
    # tail (crescent)
    s.poly([(w * 0.14, cy), (w * 0.0, cy - h * (0.42 + sw)), (w * 0.06, cy), (w * 0.02, cy + h * (0.3 - sw))],
           SHARK_D)
    # body
    s.poly([(w * 0.12, cy - h * 0.04), (w * 0.4, cy - h * 0.27), (w * 0.75, cy - h * 0.22), (w * 0.98, cy + h * 0.02),
            (w * 0.8, cy + h * 0.2), (w * 0.4, cy + h * 0.2), (w * 0.12, cy + h * 0.05)], SHARK)
    s.ell(w * 0.6, cy - h * 0.02, w * 0.32, h * 0.2, SHARK)
    # belly
    s.poly([(w * 0.3, cy + h * 0.08), (w * 0.75, cy + h * 0.06), (w * 0.96, cy + h * 0.04), (w * 0.8, cy + h * 0.2),
            (w * 0.4, cy + h * 0.2)], BELLY)
    # dorsal + pectoral fin
    s.poly([(w * 0.46, cy - h * 0.22), (w * 0.52, cy - h * 0.55), (w * 0.62, cy - h * 0.22)], SHARK_D)
    s.poly([(w * 0.6, cy + h * 0.14), (w * 0.5, cy + h * 0.42), (w * 0.7, cy + h * 0.16)], SHARK_D)
    # gills, eye, mouth
    for k in range(4):
        x = w * (0.72 - k * 0.03)
        s.line([(x, cy - h * 0.06), (x - w * 0.01, cy + h * 0.08)], (70, 85, 100, 255), max(1, w * 0.006))
    s.ell(w * 0.86, cy - h * 0.06, w * 0.014, w * 0.014, (10, 10, 15, 255))
    mo = mouth * h * 0.12
    s.poly([(w * 0.8, cy + h * 0.1), (w * 0.95, cy + h * 0.06 - mo * 0.3), (w * 0.95, cy + h * 0.1 + mo)],
           (150, 40, 50, 255))
    for k in range(6):
        x = w * (0.82 + k * 0.022)
        s.poly([(x, cy + h * 0.08), (x + w * 0.01, cy + h * 0.13), (x + w * 0.02, cy + h * 0.08)], WHITE)
    return s.img()


def orca_sprite(w, phase=0.0, face_left=True):
    h = w * 0.45
    s = SS(w, h)
    cy = h * 0.58
    sw = math.sin(phase) * 0.1
    # flukes (horizontal tail seen from side)
    s.poly([(w * 0.12, cy), (w * 0.0, cy - h * (0.16 + sw)), (w * 0.03, cy), (w * 0.0, cy + h * (0.16 - sw))], ORCA)
    # body
    s.ell(w * 0.55, cy, w * 0.43, h * 0.26, ORCA)
    s.poly([(w * 0.1, cy - h * 0.04), (w * 0.3, cy - h * 0.18), (w * 0.3, cy + h * 0.16), (w * 0.1, cy + h * 0.04)],
           ORCA)
    # tall dorsal fin
    s.poly([(w * 0.46, cy - h * 0.22), (w * 0.5, cy - h * 0.82), (w * 0.6, cy - h * 0.22)], ORCA)
    # white belly + eye patch + saddle
    s.ell(w * 0.66, cy + h * 0.14, w * 0.26, h * 0.1, WHITE)
    s.ell(w * 0.36, cy + h * 0.1, w * 0.1, h * 0.08, WHITE)
    s.ell(w * 0.82, cy - h * 0.1, w * 0.06, h * 0.05, WHITE)
    s.ell(w * 0.42, cy - h * 0.2, w * 0.08, h * 0.04, (110, 115, 125, 255))
    # pectoral fin
    s.ell(w * 0.7, cy + h * 0.3, w * 0.07, h * 0.12, ORCA)
    s.ell(w * 0.88, cy - h * 0.04, w * 0.012, w * 0.012, (240, 240, 250, 255))
    img = s.img()
    return img.transpose(Image.FLIP_LEFT_RIGHT) if face_left else img


def bubbles(img, cx, cy, gt, n=8, spread=200, seed=0):
    d = ImageDraw.Draw(img)
    rr = random.Random(seed)
    for k in range(n):
        x0 = cx + rr.uniform(-spread, spread)
        sp = rr.uniform(40, 90)
        y = cy - ((gt * sp + rr.uniform(0, 400)) % 420)
        r = rr.uniform(4, 11)
        d.ellipse((x0 - r, y - r, x0 + r, y + r), outline=(200, 235, 255), width=2)


def sc_hook(img, sc, t, gt):
    header(img, gt, "", t)
    brand(img, t, gt)
    panel_labels(img, t)
    bubbles(img, CXL, 1000, gt, seed=1)
    bubbles(img, CXR, 1000, gt, seed=2)
    p = back_out(prog(t, 0.0, 0.5))
    if p > 0.05:
        paste_c(img, shark_sprite(400 * p, gt * 4, mouth=0.5 + 0.5 * math.sin(gt * 3)), CXL - 20,
                650 + 14 * math.sin(gt * 2))
    q = back_out(prog(t, 0.15, 0.5))
    if q > 0.05:
        paste_c(img, orca_sprite(400 * q, gt * 4), CXR + 20, 830 + 14 * math.sin(gt * 2 + 1))
    vs_badge(img, t, ease_out(prog(t, 0.35, 0.3)), y=760)
    t_w = wt(sc, "gewinnt")
    if t > t_w:
        text(img, "Wer ist König im Meer?", 50, SPLIT, 1060, fill=E.C_HI, stroke=6,
             alpha=ease_out(prog(t, t_w, 0.3)), scale=back_out(prog(t, t_w, 0.4)))


PPM = 40   # px per metre (to scale)


def meter_ruler(img, x0, y, metres, color, a=1.0):
    d = ImageDraw.Draw(img)
    L = metres * PPM
    d.line((x0, y, x0 + L, y), fill=color, width=5)
    for m in range(int(metres) + 1):
        hh = 18 if m % 5 == 0 else 10
        d.line((x0 + m * PPM, y - hh, x0 + m * PPM, y + hh), fill=color, width=3)
        if m % 5 == 0:
            text(img, f"{m} m", 24, x0 + m * PPM, y + 34, fill=color, path=FONT_XB, alpha=a)


def sc_laenge(img, sc, t, gt):
    header(img, gt, "RUNDE 1 · LÄNGE", t)
    panel_labels(img, t)
    t_6, t_10 = wt(sc, "6"), wt(sc, "10")
    ps = ease_out(prog(t, t_6 - 0.5, 1.0))
    po = ease_out(prog(t, t_10 - 0.5, 1.0))
    # shark: 6 m, orca: 9.8 m – same scale
    xs0 = CXL - 3 * PPM - 60
    xo0 = CXR - 4.9 * PPM
    a = ease_out(prog(t, 0.2, 0.4))
    if a > 0.02:
        paste_c(img, shark_sprite(max(30, 6 * PPM * max(ps, 0.35)), gt * 4), xs0 + 3 * PPM * max(ps, 0.35) + 0,
                640, a)
        paste_c(img, orca_sprite(max(30, 9.8 * PPM * max(po, 0.25)), gt * 4), xo0 + 4.9 * PPM * max(po, 0.25),
                660, a)
    meter_ruler(img, xs0, 820, 6 * ps, C_L)
    meter_ruler(img, xo0, 820, 9.8 * po, C_R)
    counter(img, CXL, "bis " + E.fmt_dec(6 * ps, 1).replace(",0", "") + " m", "Weißer Hai", C_L,
            ease_out(prog(t, t_6 - 0.5, 0.3)))
    counter(img, CXR, "bis " + E.fmt_dec(9.8 * po, 1) + " m", "Orca (Männchen)", C_R,
            ease_out(prog(t, t_10 - 0.5, 0.3)))
    if t > t_10 + 0.6:
        text(img, "maßstabsgetreu", 30, SPLIT, 990, fill=(230, 230, 240), path=FONT_XB, stroke=4,
             alpha=ease_out(prog(t, t_10 + 0.6, 0.3)))


def weight_block(img, cx, cy, w, h, label, color):
    rrect(img, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 10, color + (255,), outline=(255, 255, 255, 255),
          width=3)
    text(img, label, h * 0.5, cx, cy, fill=(20, 20, 30), path=FONT_XB)


def sc_gewicht(img, sc, t, gt):
    header(img, gt, "RUNDE 2 · GEWICHT", t)
    panel_labels(img, t)
    t_2, t_10 = wt(sc, "2"), wt(sc, "10")
    base = 960
    d = ImageDraw.Draw(img)
    for cx in (CXL, CXR):
        d.rectangle((cx - 170, base, cx + 170, base + 18), fill=(220, 225, 235))
        d.rectangle((cx - 12, base + 18, cx + 12, base + 60), fill=(220, 225, 235))
    bw, bh = 120, 46
    ns = 2 * ease_out(prog(t, t_2 - 0.3, 0.6))
    no = 9.8 * ease_out(prog(t, t_10 - 0.3, 1.2))
    for k in range(int(math.ceil(ns - 0.01))):
        f = clamp(ns - k)
        drop = (1 - ease_out(f)) * 200
        weight_block(img, CXL + 0, base - bh / 2 - k * bh - drop, bw, bh - 4, "1 t", C_L)
    for k in range(int(math.ceil(no - 0.01))):
        f = clamp(no - k)
        drop = (1 - ease_out(f)) * 200
        x = CXR - 65 + 130 * (k % 2)
        weight_block(img, x, base - bh / 2 - (k // 2) * bh - drop, bw, bh - 4, "1 t" if k < 9 else "0,8", C_R)
    paste_c(img, shark_sprite(220, gt * 4), CXL, 560, ease_out(prog(t, 0.2, 0.3)))
    paste_c(img, orca_sprite(240, gt * 4), CXR, 520, ease_out(prog(t, 0.2, 0.3)))
    counter(img, CXL, "≈ " + E.fmt_dec(ns, 1).replace(",0", "") + " t", "Weißer Hai", C_L,
            ease_out(prog(t, t_2 - 0.3, 0.3)))
    counter(img, CXR, "bis " + E.fmt_dec(no, 1) + " t", "Orca (Männchen)", C_R, ease_out(prog(t, t_10 - 0.3, 0.3)))


def jaw(img, cx, cy, n, rows, mouth_col, tooth, size, shown):
    """open mouth seen from the front: `n` teeth in `rows` rows (upper + lower jaw); first `shown` drawn"""
    d = ImageDraw.Draw(img)
    RX, RY = 178, 134
    d.ellipse((cx - RX - 16, cy - RY - 16, cx + RX + 16, cy + RY + 16), fill=(200, 110, 120))
    d.ellipse((cx - RX, cy - RY, cx + RX, cy + RY), fill=mouth_col)
    d.ellipse((cx - RX * 0.45, cy - RY * 0.1, cx + RX * 0.45, cy + RY * 0.55), fill=(170, 60, 80))   # tongue
    per_arc = n // (2 * rows)
    k = 0
    for r in range(rows):
        fx, fy = RX - 8 - r * size * 1.05, RY - 8 - r * size * 1.05
        for arc in ((200, 340), (20, 160)):
            for i in range(per_arc):
                if k >= shown:
                    return
                a = math.radians(arc[0] + (arc[1] - arc[0]) * (i + 0.5) / per_arc)
                x, y = cx + fx * math.cos(a), cy + fy * math.sin(a)
                nx, ny = -math.cos(a), -math.sin(a)
                tx, ty = -ny, nx
                w = size * 0.5 * (math.pi * fx / per_arc / size if per_arc else 1)
                w = min(w, size * 0.55)
                d.polygon([(x + tx * w, y + ty * w), (x - tx * w, y - ty * w),
                           (x + nx * size * 1.2, y + ny * size * 1.2)], fill=tooth)
                k += 1


def sc_zaehne(img, sc, t, gt):
    header(img, gt, "RUNDE 3 · ZÄHNE", t)
    panel_labels(img, t)
    t_300, t_56 = wt(sc, "300"), wt(sc, "56")
    ns = int(300 * ease_out(prog(t, t_300 - 0.5, 1.2)))
    no = int(56 * ease_out(prog(t, t_56 - 0.4, 0.8)))
    jaw(img, CXL, 640, 300, 5, (60, 10, 20), (250, 250, 255), 14, ns)
    jaw(img, CXR, 640, 56, 1, (60, 10, 20), (250, 250, 255), 26, no)
    if ns:
        text(img, "mehrere Reihen", 32, CXL, 850, fill=(230, 230, 240), path=FONT_XB, stroke=4,
             alpha=ease_out(prog(t, t_300 + 0.6, 0.3)))
    counter(img, CXL, "≈ " + str(ns), "Zähne (Weißer Hai)", C_L, ease_out(prog(t, t_300 - 0.5, 0.3)))
    counter(img, CXR, "max. " + str(no), "Zähne (Orca)", C_R, ease_out(prog(t, t_56 - 0.4, 0.3)))
    stamp(img, "Punkt Hai!", t, wt(sc, "Punkt"), cx=CXL, cy=950, size=72, rot=-6)


def sc_finale(img, sc, t, gt):
    t_k = wt(sc, "Klarer")
    header(img, gt, "FINALE · WER JAGT WEN?", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    panel_labels(img, t, a=1 - prog(t, t_k - 0.1, 0.3))
    t_sa, t_l, t_f = wt(sc, "Südafrika"), wt(sc, "Leber"), wt(sc, "flüchten")
    bubbles(img, CXL, 1000, gt, n=10, seed=3)
    bubbles(img, CXR, 1000, gt, n=10, seed=4)
    # chase: orca (right) closes in, shark flees to the left and disappears
    pc = ease_io(prog(t, t_sa - 0.3, 3.0))
    pf = prog(t, t_f, 1.2) ** 2
    sx = CXL + 40 - 120 * pc - 500 * pf
    paste_c(img, shark_sprite(280, gt * 9, mouth=0.2).transpose(Image.FLIP_LEFT_RIGHT), sx, 680,
            1 - prog(t, t_f + 0.6, 0.6))
    ox = CXR + 60 - 140 * pc - 60 * pf
    paste_c(img, orca_sprite(380, gt * 7), ox, 700 + 10 * math.sin(gt * 3))
    if t > t_sa - 0.2:
        a = ease_out(prog(t, t_sa - 0.2, 0.3)) * (1 - prog(t, t_k - 0.2, 0.3))
        rrect(img, (SPLIT - 150, 460, SPLIT + 150, 516), 28, (0, 0, 0, int(160 * a)))
        text(img, "Südafrika", 36, SPLIT, 488, fill=E.C_HI, path=FONT_XB, alpha=a)
    if t > t_f:
        text(img, "Haie flüchten!", 54, CXL, 900, fill=(255, 255, 255), stroke=6,
             alpha=ease_out(prog(t, t_f, 0.3)) * (1 - prog(t, t_k - 0.1, 0.3)),
             scale=back_out(prog(t, t_f, 0.4)))
    if t_l - 0.5 < t < t_f:
        text(img, "Sie wollen die Leber!", 34, CXR, 900, fill=C_R, stroke=4, path=FONT_XB,
             alpha=ease_out(prog(t, t_l - 0.5, 0.3)))
    if t > t_k:
        crown(img, ox, 560, prog(t, t_k, 0.5), size=0.6)
        winner(img, t, t_k, "ORCA", cy=900)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, shark_sprite(190, g * 4), x, y, a)

    def mr(im, x, y, a, g):
        paste_c(im, orca_sprite(200, g * 4), x, y, a)

    brand(img, t, gt)
    E.outro(img, sc, t, gt, ml, mr, line1="Richtig geraten?", line2="Schreib's uns!")


E.setup(
    here=HERE, out="weisser_hai_vs_orca.mp4",
    name_l="WEISSER HAI", name_r="ORCA", short_l="HAI", col_l=C_L, col_r=C_R,
    bg_l=((4, 30, 60), (16, 92, 140)), bg_r=((2, 12, 28), (8, 46, 78)),
    scenes=["hook", "laenge", "gewicht", "zaehne", "finale", "outro"],
    draw=dict(hook=sc_hook, laenge=sc_laenge, gewicht=sc_gewicht, zaehne=sc_zaehne, finale=sc_finale,
              outro=sc_outro),
    sub_map=[(("eins",), "1"), (("zwei",), "2"), (("drei",), "3")],
    score=[(1, "Punkt", 1, "R"), (2, "Punkt", 1, "R"), (3, "Punkt", 1, "L"), (4, "Sieger", 1, "R")],
    ticks=[(3, "300", 1, 1.2), (2, "10", 1, 1.0)],
    tempo=1.15,
)

if __name__ == "__main__":
    E.main()

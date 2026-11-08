#!/usr/bin/env python3
"""Mond vs. Erde – animated German TikTok comparison."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tiere"))
import engine as E  # noqa: E402
from engine import (CXL, CXR, SPLIT, VIS_Y, NUM_Y, GROUND, SS, back_out, clamp, counter, ease_io,  # noqa: E402
                    ease_out, header, panel_labels, paste_c, person_sprite, prog, stamp, burst, text, vs_badge, wt,
                    rrect, crown, winner, FONT_XB)

C_L = (205, 205, 225)     # Mond
C_R = (80, 200, 255)      # Erde


def moon_sprite(d):
    r = max(3, d / 2)
    s = SS(2 * r + 4, 2 * r + 4)
    s.ell(r + 2, r + 2, r, r, (195, 195, 210, 255))
    rr = random.Random(2)
    for _ in range(9):
        a = rr.uniform(0, 6.28)
        q = rr.uniform(0, 0.65) * r
        cr = r * rr.uniform(0.08, 0.2)
        s.ell(r + 2 + q * math.cos(a), r + 2 + q * math.sin(a), cr, cr, (160, 160, 178, 255))
    s.ell(r + 2 - r * 0.35, r + 2 - r * 0.35, r * 0.25, r * 0.2, (255, 255, 255, 50))
    return s.img()


def earth_sprite(d, t=0.0):
    r = max(3, d / 2)
    s = SS(2 * r + 4, 2 * r + 4)
    s.ell(r + 2, r + 2, r, r, (40, 120, 230, 255))
    rr = random.Random(3)
    for _ in range(10):
        a = rr.uniform(0, 6.28) + t * 0.15
        q = rr.uniform(0, 0.62) * r
        s.ell(r + 2 + q * math.cos(a), r + 2 + q * math.sin(a), r * rr.uniform(0.12, 0.28),
              r * rr.uniform(0.1, 0.2), (70, 180, 90, 255))
    s.ell(r + 2 - r * 0.35, r + 2 - r * 0.35, r * 0.25, r * 0.18, (255, 255, 255, 50))
    return s.img()


def scale_dev(img, cx, y, reading, color, a=1.0):
    rrect(img, (cx - 150, y, cx + 150, y + 24), 10, (230, 230, 240, int(255 * a)))
    rrect(img, (cx - 115, y + 38, cx + 115, y + 110), 16, (15, 20, 30, int(255 * a)), outline=color + (int(255 * a),),
          width=5)
    text(img, reading, 44, cx, y + 74, fill=(120, 255, 140), alpha=a)


def sc_hook(img, sc, t, gt):
    header(img, gt, "", t)
    panel_labels(img, t)
    t_12 = wt(sc, "zwölf")
    paste_c(img, moon_sprite(260), CXL, 560, ease_out(prog(t, 0.0, 0.4)))
    paste_c(img, earth_sprite(260, gt), CXR, 560, ease_out(prog(t, 0.1, 0.4)))
    sy = 900
    hop = abs(math.sin(gt * 2.0)) * 120
    paste_c(img, person_sprite(150, (230, 230, 240)), CXL, sy - hop, anchor="b")
    paste_c(img, person_sprite(150, (230, 230, 240)), CXR, sy - abs(math.sin(gt * 5)) * 15, anchor="b")
    v = 70 - 58.4 * ease_out(prog(t, t_12 - 0.3, 0.8))
    scale_dev(img, CXL, sy, f"{fmt(v)} kg", C_L)
    scale_dev(img, CXR, sy, "70 kg", C_R)


def fmt(v):
    return E.fmt_dec(v, 1) if v < 20 else str(int(round(v)))


def sc_groesse(img, sc, t, gt):
    header(img, gt, "RUNDE 1 · GRÖSSE", t)
    panel_labels(img, t)
    t_m, t_35, t_e, t_13 = wt(sc, "Mond"), wt(sc, "dreitausendfünfhundert"), wt(sc, "Erde"), wt(sc, "dreizehntausend")
    D = 380
    dm = D * 3475 / 12742
    pm = back_out(prog(t, t_m - 0.2, 0.5))
    pe = back_out(prog(t, t_e - 0.2, 0.6))
    cy = 700
    if pm > 0.02:
        paste_c(img, moon_sprite(dm * pm), CXL, cy)
    if pe > 0.02:
        paste_c(img, earth_sprite(D * pe, gt), CXR, cy)
    d = ImageDraw.Draw(img)
    if t > t_35:
        q = ease_out(prog(t, t_35, 0.6))
        d.line((CXL - dm / 2 * q, cy + dm / 2 + 30, CXL + dm / 2 * q, cy + dm / 2 + 30), fill=C_L, width=5)
    if t > t_13:
        q = ease_out(prog(t, t_13, 0.6))
        d.line((CXR - D / 2 * q, cy + D / 2 + 30, CXR + D / 2 * q, cy + D / 2 + 30), fill=C_R, width=5)
    if t > t_13 + 0.4:
        text(img, "maßstabsgetreu", 30, SPLIT, 950, fill=(230, 230, 240), path=FONT_XB,
             alpha=ease_out(prog(t, t_13 + 0.4, 0.3)))
    counter(img, CXL, E.fmt_int(3475 * ease_out(prog(t, t_35, 0.9))) + " km", "Durchmesser", C_L,
            ease_out(prog(t, t_35, 0.3)))
    counter(img, CXR, E.fmt_int(12742 * ease_out(prog(t, t_13, 0.9))) + " km", "Durchmesser", C_R,
            ease_out(prog(t, t_13, 0.3)))


def sc_schwerkraft(img, sc, t, gt):
    header(img, gt, "RUNDE 2 · SCHWERKRAFT", t)
    panel_labels(img, t)
    t_6, t_70, t_12 = wt(sc, "Sechstel"), wt(sc, "siebzig"), wt(sc, "zwölf")
    ground = 860
    # jump heights (illustrative): on the Moon ~6× higher, slower
    pm = (math.sin(gt * 1.6) * 0.5 + 0.5)
    pe = (math.sin(gt * 4.0) * 0.5 + 0.5)
    jm = 300 * pm * pm
    je = 50 * pe * pe
    d = ImageDraw.Draw(img)
    d.rectangle((CXL - 210, ground, CXL + 210, ground + 14), fill=(170, 170, 185))
    d.rectangle((CXR - 210, ground, CXR + 210, ground + 14), fill=(70, 160, 90))
    paste_c(img, person_sprite(150, (230, 230, 240), arms_up=pm), CXL, ground - jm, anchor="b")
    paste_c(img, person_sprite(150, (230, 230, 240), arms_up=pe), CXR, ground - je, anchor="b")
    paste_c(img, moon_sprite(90), CXL + 150, 470, ease_out(prog(t, 0.2, 0.3)))
    paste_c(img, earth_sprite(90, gt), CXR + 150, 470, ease_out(prog(t, 0.2, 0.3)))
    stamp(img, "1/6", t, t_6, cx=CXL - 120, cy=520, size=100, rot=-8)
    v = 70 - 58.4 * ease_out(prog(t, t_12 - 0.2, 0.8))
    counter(img, CXL, f"{fmt(v)} kg", "Waage auf dem Mond", C_L, ease_out(prog(t, t_70, 0.3)))
    counter(img, CXR, "70 kg", "Waage auf der Erde", C_R, ease_out(prog(t, t_70, 0.3)))


def clock(img, cx, cy, R, frac, color, label):
    layer = Image.new("RGBA", (E.W, E.H))
    d = ImageDraw.Draw(layer)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(20, 25, 40, 230), outline=color + (255,), width=8)
    if frac > 0:
        d.pieslice((cx - R + 14, cy - R + 14, cx + R - 14, cy + R - 14), -90, -90 + 360 * min(frac, 1),
                   fill=color + (120,))
    for k in range(12):
        a = k / 12 * 2 * math.pi
        d.line((cx + (R - 26) * math.cos(a), cy + (R - 26) * math.sin(a), cx + (R - 12) * math.cos(a),
                cy + (R - 12) * math.sin(a)), fill=(255, 255, 255, 220), width=4)
    a = -math.pi / 2 + 2 * math.pi * frac
    d.line((cx, cy, cx + (R - 34) * math.cos(a), cy + (R - 34) * math.sin(a)), fill=(255, 80, 80, 255), width=8)
    img.paste(layer, (0, 0), layer)
    text(img, label, 34, cx, cy + R + 40, fill=(230, 230, 240), path=FONT_XB)


def sc_tag(img, sc, t, gt):
    header(img, gt, "RUNDE 3 · EIN TAG", t)
    panel_labels(img, t)
    t_e, t_24, t_mt, t_29 = wt(sc, "Erde"), wt(sc, "vierundzwanzig"), wt(sc, "Mondtag"), \
        wt(sc, "neunundzwanzigeinhalb")
    # Earth: one full turn per second of animation = 24 h; Moon: 29.5× slower
    ce = (t - t_e) * 0.9 if t > t_e else 0
    cm = ce / 29.5
    clock(img, CXR, 680, 170, ce % 1.0 if t > t_e else 0, C_R, "1 Erdtag")
    clock(img, CXL, 680, 170, cm, C_L, "1 Mondtag")
    nd = int(ce) + 1 if t > t_e else 0
    if t > t_mt:
        text(img, f"{min(nd, 30)} Erdtage …", 36, CXL, 470, fill=C_L, stroke=4, path=FONT_XB)
    counter(img, CXR, "24 h", "Erde", C_R, ease_out(prog(t, t_24, 0.3)))
    counter(img, CXL, "≈ 29,5", "Erdtage", C_L, ease_out(prog(t, t_29, 0.3)))
    burst(img, CXL, 680, t, t_29 + 0.6, color=C_L, rad=200)


def sc_finale(img, sc, t, gt):
    t_k = wt(sc, "Klarer")
    header(img, gt, "FINALE · VOLUMEN", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    t_e, t_49 = wt(sc, "Erde"), wt(sc, "neunundvierzig")
    cx, cy = SPLIT, 700
    R = 270
    paste_c(img, earth_sprite(2 * R, gt), cx, cy, ease_out(prog(t, 0.05, 0.5)))
    # 49 moons (same scale: moon diameter = 0.273 × Earth diameter) arranged in the disc
    dm = 62      # drawn smaller so all 49 fit visibly
    pts = []
    rr = random.Random(5)
    step = dm * 1.02
    y = -R + dm / 2
    row = 0
    while y < R and len(pts) < 49:
        x = -R + dm / 2 + (step / 2 if row % 2 else 0)
        while x < R and len(pts) < 49:
            if x * x + y * y < (R - dm / 2) ** 2:
                pts.append((x, y))
            x += step
        y += step * 0.88
        row += 1
    assert len(pts) == 49, len(pts)
    n = int(clamp((t - (t_49 - 0.3)) / 1.0) * len(pts) + 0.999) if t > t_49 - 0.3 else 0
    m = moon_sprite(dm)
    for k in range(n):
        x, y = pts[k]
        paste_c(img, m, cx + x, cy + y)
    if n:
        counter(img, SPLIT, f"{n} Monde", "passen in die Erde", C_L, 1.0, y=NUM_Y + 30)
    if t > t_k:
        crown(img, cx, cy - R - 60, prog(t, t_k, 0.5), size=0.6)
        winner(img, t, t_k, "ERDE", cy=cy + 40)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, moon_sprite(130), x, y, a)

    def mr(im, x, y, a, g):
        paste_c(im, earth_sprite(150, g), x, y, a)

    E.outro(img, sc, t, gt, ml, mr, line1="Mond-WG? Ja/Nein", line2="Schreib's uns!")


E.setup(
    here=HERE, out="mond_vs_erde.mp4",
    name_l="MOND", name_r="ERDE", col_l=C_L, col_r=C_R,
    bg_l=((14, 14, 24), (60, 60, 84)), bg_r=((5, 15, 45), (10, 72, 132)),
    scenes=["hook", "groesse", "schwerkraft", "tag", "finale", "outro"],
    draw=dict(hook=sc_hook, groesse=sc_groesse, schwerkraft=sc_schwerkraft, tag=sc_tag, finale=sc_finale,
              outro=sc_outro),
    sub_map=[
        (("zwölf",), "12"), (("dreitausendfünfhundert",), "3.500"), (("dreizehntausend",), "13.000"),
        (("siebzig",), "70"), (("vierundzwanzig",), "24"), (("neunundzwanzigeinhalb",), "29,5"),
        (("neunundvierzig",), "49"), (("eins",), "1"), (("zwei",), "2"), (("drei",), "3"),
    ],
    score=[(1, "dreizehntausend", 1, "R"), (3, "neunundzwanzigeinhalb", 1, "L"), (4, "Sieger", 1, "R")],
    ticks=[(1, "dreizehntausend", 1, 0.9), (4, "neunundvierzig", 1, 1.0)],
)

if __name__ == "__main__":
    E.main()

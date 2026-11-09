#!/usr/bin/env python3
"""Rate mal, was passiert, wenn du zu lange in der Badewanne bleibst? – colourful full-frame style."""
import math
import os
import random
import sys

from PIL import ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import col as C  # noqa: E402
from col import E, prog, ease_out, ease_io, back_out, paste_c, text, wt, rrect, FONT_XB  # noqa: E402

WATER = (60, 150, 230)


def sc_hook(img, sc, t, gt):
    E.brand(img, t, gt, y=300)
    d = ImageDraw.Draw(img)
    # person in the tub (head + shoulders above the water)
    bob = 6 * math.sin(gt * 2)
    paste_c(img, E.person_sprite(560, C.ORANGE, arms_up=0.15), 450, 1172 + bob, ease_out(prog(t, 0.0, 0.3)),
            anchor="b")
    rrect(img, (150, 940, 930, 1180), 90, (245, 248, 255, 255))
    rrect(img, (175, 950, 905, 1060), 40, WATER + (230,))
    d.line([(x, 950 + 8 * math.sin(x / 50 + gt * 3)) for x in range(185, 900, 10)], fill=(180, 225, 255), width=6)
    for x in (230, 850):
        d.ellipse((x - 30, 1170, x + 30, 1230), fill=(220, 225, 235))
    paste_c(img, C.duck(0.9), 760, 940 + 8 * math.sin(gt * 2.5), ease_out(prog(t, 0.3, 0.3)))
    C.bubbles(img, 540, 940, gt, n=12, spread=330, rise=380)
    m = int(30 * prog(t, 0.3, sc["dur"] - 0.4))
    C.ring(img, 790, 600, 130, m / 60, C.BLUE, f"{m}", "MIN", ease_out(prog(t, 0.2, 0.3)))
    q = 1 + 0.1 * math.sin(gt * 6)
    text(img, "?", 220 * q, 290, 640, fill=C.YELLOW, stroke=10, sfill=(40, 20, 60), rotate=-10,
         alpha=ease_out(prog(t, 0.5, 0.3)))


def sc_wrinkle(img, sc, t, gt):
    ts, tw = wt(sc, "schrumpelig"), wt(sc, "warum")
    wr = ease_io(prog(t, ts - 0.4, 1.4))
    paste_c(img, C.hand(wr, 1.25), 540, 850, ease_out(prog(t, 0.0, 0.3)))
    C.bubbles(img, 540, 1250, gt, n=8, spread=380, rise=700, seed=3)
    if t > ts:
        C.pill(img, "SCHRUMPELIG", 540, 470, C.SKIN, ease_out(prog(t, ts, 0.3)) * (1 - prog(t, tw - 0.3, 0.2)))
    E.stamp(img, "WARUM?", t, tw - 0.15, cx=540, cy=470, size=130, rot=-6)


def skin_section(img, gt, wrinkle, vessel, nerve_a, pulse_t):
    d = ImageDraw.Draw(img)
    x0, x1, top = 140, 940, 620
    amp = 34 * wrinkle
    surf = [(x, top + amp * math.sin((x - x0) / 55)) for x in range(x0, x1 + 1, 8)]
    d.polygon(surf + [(x1, 1200), (x0, 1200)], fill=(255, 205, 165))
    d.polygon([(x, y + 60) for x, y in surf] + [(x1, 1200), (x0, 1200)], fill=(250, 175, 140))
    d.line(surf, fill=(200, 120, 90), width=8)
    for k, y in enumerate((880, 980, 1080)):
        w = 46 * vessel - k * 4
        d.rounded_rectangle((x0 + 20, y - w / 2, x1 - 20, y + w / 2), int(w / 2), fill=(220, 50, 70))
        d.line((x0 + 40, y - w / 4, x1 - 40, y - w / 4), fill=(255, 120, 130), width=4)
    if nerve_a > 0.02:
        pts = [(x1 - 10, 760), (760, 800), (640, 830), (520, 860), (400, 820), (280, 850), (170, 830)]
        d.line(pts, fill=C.YELLOW, width=10, joint="curve")
        if pulse_t is not None:
            f = (pulse_t * 1.2) % 1
            i = min(len(pts) - 2, int(f * (len(pts) - 1)))
            k = f * (len(pts) - 1) - i
            px = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k
            py = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k
            d.ellipse((px - 22, py - 22, px + 22, py + 22), fill=(255, 255, 200))


def sc_nerves(img, sc, t, gt):
    tf, tn, tz = wt(sc, "Falsch"), wt(sc, "Nervensystem"), wt(sc, "zusammen")
    tg = wt(sc, "Blutgefäße")
    vessel = 1 - 0.55 * ease_io(prog(t, tg, 1.2))
    wrinkle = 0.2 + 0.8 * ease_io(prog(t, tg + 0.2, 1.4))
    skin_section(img, gt, wrinkle if t > tf else 0.15, vessel, ease_out(prog(t, tn - 0.2, 0.3)),
                 t - tn if t > tn else None)
    if t < tf + 0.6:
        d = ImageDraw.Draw(img)
        a = 1 - prog(t, tf + 0.3, 0.3)
        rr = random.Random(4)
        for k in range(10):
            x = rr.uniform(200, 880)
            y = 420 + ((gt * 220 + rr.uniform(0, 200)) % 220)
            d.ellipse((x - 12, y - 18, x + 12, y + 12), fill=(120, 190, 255))
        C.pill(img, "HAUT SAUGT WASSER?", 540, 470, C.BLUE, a * ease_out(prog(t, 0.1, 0.3)))
        C.cross(img, 540, 470, 160 * ease_out(prog(t, tf, 0.25)), a=a)
    E.stamp(img, "FALSCH!", t, tf, cx=540, cy=470, size=120, rot=-6, hold=0.9)
    if t > tn:
        C.pill(img, "NERV", 820, 700, C.YELLOW, ease_out(prog(t, tn, 0.3)))
    if t > tg:
        C.pill(img, "GEFÄSSE ZIEHEN SICH ZUSAMMEN", 540, 470, C.RED, ease_out(prog(t, tg, 0.3)), size=34)
    _ = tz


def sc_proof(img, sc, t, gt):
    tn, tg = wt(sc, "Fingernerven"), wt(sc, "glatt")
    paste_c(img, C.hand(1.0, 1.25, smooth_finger=1 if t > tn - 0.3 else None), 540, 850)
    d = ImageDraw.Draw(img)
    a = ease_out(prog(t, tn - 0.3, 0.3))
    if a > 0.02:
        x = 540 - 1.25 * 210 + 1.25 * 165      # finger 1 centre
        d.line((x, 1060, x, 900), fill=C.YELLOW, width=10)
        d.line((x, 840, x, 700), fill=C.YELLOW, width=10)
        C.cross(img, x, 870, 26, a=a, w=12)
        C.pill(img, "NERV VERLETZT", 760, 1150, C.YELLOW, a, size=34)
    if t > tg - 0.2:
        C.pill(img, "BLEIBT GLATT!", 540, 470, C.GREEN, ease_out(prog(t, tg - 0.2, 0.3)))
        E.burst(img, 540 - 1.25 * 45, 600, t, tg, color=C.GREEN, rad=150)
    C.pill(img, "DER BEWEIS", 540, 470, C.WHITE, ease_out(prog(t, 0.0, 0.3)) * (1 - prog(t, tg - 0.4, 0.2)))


def tire(img, cx, cy, r, gt):
    sp = E.SS(2 * r + 4, 2 * r + 4)
    c = r + 2
    sp.ell(c, c, r, r, (40, 40, 48, 255))
    for k in range(14):
        a = k / 14 * 2 * math.pi + gt * 1.5
        sp.poly([(c + r * 0.98 * math.cos(a - 0.1), c + r * 0.98 * math.sin(a - 0.1)),
                 (c + r * 0.78 * math.cos(a - 0.06), c + r * 0.78 * math.sin(a - 0.06)),
                 (c + r * 0.78 * math.cos(a + 0.06), c + r * 0.78 * math.sin(a + 0.06)),
                 (c + r * 0.98 * math.cos(a + 0.1), c + r * 0.98 * math.sin(a + 0.1))], (90, 90, 100, 255))
    sp.ell(c, c, r * 0.55, r * 0.55, (180, 185, 195, 255))
    sp.ell(c, c, r * 0.2, r * 0.2, (90, 95, 110, 255))
    paste_c(img, sp.img(), cx, cy)


def sc_grip(img, sc, t, gt):
    t12, tr = wt(sc, "12"), wt(sc, "Reifenprofil")
    d = ImageDraw.Draw(img)
    a = 1 - prog(t, tr - 0.3, 0.3)
    if a > 0.02:
        for bx in (270, 810):
            d.chord((bx - 150, 960, bx + 150, 1200), 0, 180, fill=(120, 200, 255))
            d.line((bx - 150, 1080, bx + 150, 1080), fill=(220, 240, 255), width=6)
        cols = [C.RED, C.YELLOW, C.GREEN, C.BLUE, C.PURPLE]
        for k in range(5):
            ph = (gt * 0.9 + k / 5) % 1
            x = 270 + 540 * ease_io(ph)
            y = 1050 - 360 * math.sin(ph * math.pi)
            d.ellipse((x - 26, y - 26, x + 26, y + 26), fill=cols[k])
            d.ellipse((x - 14, y - 16, x - 4, y - 6), fill=(255, 255, 255))
        paste_c(img, C.hand(1.0, 0.45), 540, 600 + 20 * math.sin(gt * 3), a)
        C.pill(img, "NASSE MURMELN", 540, 470, C.BLUE, ease_out(prog(t, wt(sc, "Murmeln") - 0.3, 0.3)) * a)
    if t > t12 - 0.4:
        v = int(12 * ease_out(prog(t, t12 - 0.4, 0.8)))
        k = ease_out(prog(t, t12 - 0.4, 0.3)) * a
        text(img, f"+{v} %", 150, 540, 820, fill=C.YELLOW, stroke=10, sfill=(40, 20, 60), alpha=k)
        text(img, "schneller gegriffen", 44, 540, 920, alpha=k, stroke=5, path=FONT_XB)
    if t > tr - 0.3:
        b = ease_out(prog(t, tr - 0.3, 0.4))
        tire(img, 540, 820, 230 * back_out(prog(t, tr - 0.3, 0.5)), gt)
        rr = random.Random(7)
        for k in range(30):
            x = rr.uniform(120, 960)
            y = 420 + ((gt * 600 + rr.uniform(0, 700)) % 700)
            d.line((x, y, x - 6, y + 26), fill=(150, 200, 255), width=3)
        C.pill(img, "WIE REIFENPROFIL", 540, 470, C.WHITE, b)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, C.duck(0.7), x, y, a)

    def mr(im, x, y, a, g):
        paste_c(im, C.hand(1.0, 0.3), x, y, a)

    E.brand(img, t, gt, y=300)
    E.outro(img, sc, t, gt, ml, mr, line1="Gewusst? Ja / Nein", line2="Schreib's uns!")


E.setup(
    here=HERE, out="schrumpelige_finger.mp4",
    name_l="", name_r="", col_l=C.YELLOW, col_r=C.YELLOW,
    bg_l=((6, 22, 60), (12, 96, 140)), bg_r=((6, 22, 60), (12, 96, 140)),
    scenes=["hook", "wrinkle", "nerves", "proof", "grip", "outro"],
    draw=dict(hook=sc_hook, wrinkle=sc_wrinkle, nerves=sc_nerves, proof=sc_proof, grip=sc_grip, outro=sc_outro),
    sub_map=[], score=[], ticks=[(4, "12", 1, 0.8)], tempo=1.06,
    chimes=[],
)

if __name__ == "__main__":
    E.main()

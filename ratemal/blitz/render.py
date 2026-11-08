#!/usr/bin/env python3
"""Rate mal: Blitz vs. Sonne – animated German TikTok comparison."""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tiere"))
import engine as E  # noqa: E402
from engine import (CXL, CXR, SPLIT, NUM_Y, SS, back_out, clamp, counter, ease_io, ease_out,  # noqa: E402
                    header, panel_labels, paste_c, prog, stamp, burst, text, vs_badge, wt, rrect, crown, winner,
                    brand, FONT_XB)

C_L = (170, 150, 255)     # Blitz (violett-elektrisch)
C_R = (255, 170, 40)      # Sonne (orange)
BOLT = (250, 250, 210)


def bolt_pts(h):
    """zigzag lightning polygon in a box h tall, ~0.45h wide"""
    w = h * 0.45
    return [(w * 0.62, 0), (w * 0.18, h * 0.47), (w * 0.47, h * 0.47), (w * 0.12, h),
            (w * 0.88, h * 0.4), (w * 0.56, h * 0.4), (w * 0.95, 0)]


def bolt_sprite(h, glow=1.0):
    w = h * 0.45
    pad = h * 0.12
    s = SS(w + 2 * pad, h + 2 * pad)
    pts = [(x + pad, y + pad) for x, y in bolt_pts(h)]
    for k, a in ((1.0, 50), (0.6, 90)):
        cx, cy = pad + w / 2, pad + h / 2
        s.ell(cx, cy, w * 0.55 * (1 + k), h * 0.5 * (0.6 + k * 0.4), (150, 120, 255, int(a * glow)))
    s.poly(pts, BOLT + (255,))
    inner = [(pad + w / 2 + (x - pad - w / 2) * 0.55, pad + h / 2 + (y - pad - h / 2) * 0.8) for x, y in pts]
    s.poly(inner, (255, 255, 255, 255))
    return s.img()


def sun_sprite(d, gt=0.0, rays=True):
    r = d / 2
    pad = r * 0.45 if rays else 4
    s = SS(2 * (r + pad), 2 * (r + pad))
    c = r + pad
    s.ell(c, c, r * 1.3, r * 1.3, (255, 140, 0, 50))
    if rays:
        for i in range(12):
            a = i / 12 * 2 * math.pi + gt * 0.6
            p1 = (c + r * 1.05 * math.cos(a - 0.12), c + r * 1.05 * math.sin(a - 0.12))
            p2 = (c + r * 1.38 * math.cos(a), c + r * 1.38 * math.sin(a))
            p3 = (c + r * 1.05 * math.cos(a + 0.12), c + r * 1.05 * math.sin(a + 0.12))
            s.poly([p1, p2, p3], (255, 190, 40, 255))
    s.ell(c, c, r, r, (255, 150, 20, 255))
    s.ell(c, c, r * 0.82, r * 0.82, (255, 190, 40, 255))
    s.ell(c - r * 0.3, c - r * 0.3, r * 0.28, r * 0.2, (255, 240, 170, 120))
    return s.img()


def flicker(gt, seed=0):
    """lightning-like brightness: mostly on, short drop-outs"""
    v = math.sin(gt * 23 + seed) + math.sin(gt * 37 + 2 * seed)
    return 0.35 if v > 1.5 else 1.0


def sc_hook(img, sc, t, gt):
    header(img, gt, "", t)
    brand(img, t, gt)
    panel_labels(img, t)
    p = back_out(prog(t, 0.0, 0.45))
    if p > 0.05:
        paste_c(img, bolt_sprite(430 * p, flicker(gt)), CXL, 720, ease_out(prog(t, 0.0, 0.3)) * flicker(gt))
    q = back_out(prog(t, 0.15, 0.5))
    if q > 0.05:
        paste_c(img, sun_sprite(260 * q * (1 + 0.04 * math.sin(gt * 5)), gt), CXR, 720)
    vs_badge(img, t, ease_out(prog(t, 0.35, 0.3)), y=720)
    t_h = wt(sc, "heißer")
    if t > t_h:
        text(img, "Was ist heißer?", 52, SPLIT, 1040, fill=E.C_HI, stroke=6, alpha=ease_out(prog(t, t_h, 0.3)),
             scale=back_out(prog(t, t_h, 0.4)))


def thermo(img, cx, top, bot, frac, color, a=1.0):
    d = ImageDraw.Draw(img)
    w = 46
    rrect(img, (cx - w / 2 - 8, top - 8, cx + w / 2 + 8, bot + 8), 30, (255, 255, 255, int(220 * a)))
    rrect(img, (cx - w / 2, top, cx + w / 2, bot), 22, (30, 30, 50, 255))
    fy = bot - (bot - top - 20) * clamp(frac)
    rrect(img, (cx - w / 2 + 6, fy, cx + w / 2 - 6, bot), 16, color + (255,))
    d.ellipse((cx - 50, bot - 30, cx + 50, bot + 70), fill=(255, 255, 255), outline=None)
    d.ellipse((cx - 40, bot - 20, cx + 40, bot + 60), fill=color)
    for k in range(7):
        y = bot - (bot - top - 20) * k / 6
        d.line((cx + 40, y, cx + 62, y), fill=(255, 255, 255), width=4)
    return fy


def sc_hitze(img, sc, t, gt):
    header(img, gt, "RUNDE 1 · HITZE", t)
    panel_labels(img, t)
    t_55 = wt(sc, "fünftausendfünfhundert")
    t_30 = wt(sc, "dreißigtausend")
    top, bot = 470, 930
    ps = ease_out(prog(t, t_55, 1.0))
    pb = ease_out(prog(t, t_30, 1.2))
    thermo(img, CXR, top, bot, ps * 5500 / 30000, C_R)
    fy = thermo(img, CXL, top, bot, pb, (255, 255, 255) if int(gt * 12) % 2 and pb < 1 else (200, 180, 255))
    paste_c(img, sun_sprite(110, gt), CXR - 140, 560, ease_out(prog(t, 0.2, 0.3)))
    paste_c(img, bolt_sprite(150, flicker(gt)), CXL - 140, 560, ease_out(prog(t, 0.2, 0.3)) * flicker(gt, 1))
    if pb > 0.95:
        burst(img, CXL, fy, t, t_30 + 1.1, color=(220, 200, 255), rad=150)
    counter(img, CXR, E.fmt_int(5500 * ps) + " °C", "Sonnenoberfläche", C_R, ease_out(prog(t, t_55, 0.3)))
    counter(img, CXL, E.fmt_int(30000 * pb) + " °C", "Blitz (fast)", C_L, ease_out(prog(t, t_30, 0.3)))
    stamp(img, "5× heißer!", t, wt(sc, "Punkt"), cx=SPLIT, cy=780, size=96, rot=-8)


def earth_small(d):
    r = d / 2
    s = SS(d + 4, d + 4)
    s.ell(r + 2, r + 2, r, r, (40, 120, 230, 255))
    rr = random.Random(3)
    for _ in range(9):
        a = rr.uniform(0, 6.28)
        q = rr.uniform(0, 0.6) * r
        s.ell(r + 2 + q * math.cos(a), r + 2 + q * math.sin(a), r * rr.uniform(0.12, 0.28), r * rr.uniform(0.1, 0.2),
              (70, 180, 90, 255))
    return s.img()


EARTH = None


def sc_oft(img, sc, t, gt):
    global EARTH
    header(img, gt, "RUNDE 2 · WIE OFT?", t)
    panel_labels(img, t)
    t_1, t_44 = wt(sc, "Sonne"), wt(sc, "vierundvierzigmal")
    cy = 690
    if EARTH is None:
        EARTH = earth_small(330)
    paste_c(img, EARTH, CXL, cy, ease_out(prog(t, 0.1, 0.4)))
    # flashes: before the number a few, afterwards 44 per second (each visible ~0.12 s)
    rate = 6 + 38 * ease_out(prog(t, t_44, 0.8))
    d = ImageDraw.Draw(img)
    start = int((gt - 0.12) * 44)
    for k in range(start, int(gt * 44) + 1):
        rr = random.Random(k)
        if rr.random() > rate / 44:
            continue
        a = rr.uniform(0, 6.28)
        q = math.sqrt(rr.random()) * 150
        x, y = CXL + q * math.cos(a), cy + q * math.sin(a)
        L = rr.uniform(18, 34)
        d.line((x, y - L, x - 7, y - 3, x + 5, y + 2, x - 3, y + L), fill=(255, 255, 220), width=5)
        d.ellipse((x - 10, y - 10, x + 10, y + 10), outline=(200, 180, 255), width=3)
    p = back_out(prog(t, t_1 - 0.2, 0.5))
    if p > 0.05:
        paste_c(img, sun_sprite(240 * p, gt), CXR, cy)
    counter(img, CXR, "1", "Sonne", C_R, ease_out(prog(t, t_1, 0.3)))
    counter(img, CXL, f"≈ {int(round(44 * ease_out(prog(t, t_44, 0.8))))}", "Blitze pro Sekunde", C_L,
            ease_out(prog(t, t_44, 0.3)))


Y0, Y1 = 330, 1060
YY, XX = np.mgrid[Y0:Y1, SPLIT:E.W]


def sc_groesse(img, sc, t, gt):
    header(img, gt, "RUNDE 3 · GRÖSSE", t)
    panel_labels(img, t)
    t_829, t_s, t_14 = wt(sc, "achthundertneunundzwanzig"), wt(sc, "Sonne"), wt(sc, "Millionen")
    cy = 690
    # zoom: z = 1 → record bolt is 360 px long; end → sun 380 px wide (to scale: sun ≈ 1.677 × the bolt)
    ratio = 1390000 / 829
    zmax = 360 * ratio / 380
    z0 = 360 * ratio / 2 / 360        # sun radius 360 px = just bigger than the panel
    pa, pb2 = ease_io(prog(t, t_s, 1.0)), ease_io(prog(t, t_s + 1.0, 1.4))
    z = math.exp(math.log(z0) * pa + (math.log(zmax) - math.log(z0)) * pb2)
    bl = 360 / z
    pb = ease_out(prog(t, t_829 - 0.3, 0.6))
    d = ImageDraw.Draw(img)
    if pb > 0.02:
        if bl > 6:
            L = bl * pb
            x0 = CXL - L / 2
            pts = []
            n = 9
            for k in range(n + 1):
                pts.append((x0 + L * k / n, cy + (0 if k in (0, n) else (14 if k % 2 else -14) * min(1, bl / 60))))
            d.line(pts, fill=(255, 255, 220), width=max(2, int(8 * min(1, bl / 120))))
        else:
            d.ellipse((CXL - 4, cy - 4, CXL + 4, cy + 4), fill=(255, 255, 220))
            a = ease_out(prog(t, t_s + 1.6, 0.4))
            if a > 0:
                d.ellipse((CXL - 40, cy - 40, CXL + 40, cy + 40), outline=E.C_HI, width=5)
                text(img, "der Blitz!", 40, CXL, cy - 80, fill=E.C_HI, alpha=a, stroke=4, path=FONT_XB)
    # sun (clipped to right panel); fades in once it fits the panel (R <= 340 px)
    R = 360 * ratio / 2 / z
    ps = clamp((360 - R) / 40) if t > t_s else 0
    if ps > 0.02:
        dist = np.hypot(XX - CXR, YY - cy)
        m = dist < R
        if m.any():
            arr = np.array(img)
            sub = arr[Y0:Y1, SPLIT:E.W]
            k = np.clip(dist / max(R, 1), 0, 1)[..., None]
            col = (np.array([255, 200, 60]) * (1 - k) + np.array([255, 130, 10]) * k)
            sub[m] = (sub[m] * (1 - ps) + col[m] * ps).astype(np.uint8)
            arr[Y0:Y1, SPLIT:E.W] = sub
            img.paste(Image.fromarray(arr))
    if R > 345 and t > t_s - 0.2:
        text(img, "Zoom raus …", 40, CXR, cy, fill=(255, 220, 150), stroke=4, path=FONT_XB,
             alpha=ease_out(prog(t, t_s - 0.2, 0.3)))
    counter(img, CXL, "829 km", "längster Blitz", C_L, ease_out(prog(t, t_829, 0.3)))
    counter(img, CXR, E.fmt_dec(1.39 * ease_out(prog(t, t_14 - 0.4, 0.8)), 2) + " Mio. km", "Durchmesser", C_R,
            ease_out(prog(t, t_14 - 0.4, 0.3)), size=60)
    if t > t_14 + 0.6:
        text(img, "maßstabsgetreu", 30, SPLIT, 970, fill=(230, 230, 240), path=FONT_XB,
             alpha=ease_out(prog(t, t_14 + 0.6, 0.3)))


def sc_finale(img, sc, t, gt):
    t_k = wt(sc, "Klarer")
    header(img, gt, "FINALE · DAUER", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    if t < t_k:
        text(img, "Finale zählt doppelt!", 34, SPLIT, 350, fill=E.C_HI, stroke=4, path=FONT_XB,
             alpha=ease_out(prog(t, 0.3, 0.3)))
    t_b, t_17, t_s, t_45 = wt(sc, "Blitz"), wt(sc, "siebzehn"), wt(sc, "Sonne"), wt(sc, "viereinhalb")
    cy = 640
    # Blitz: stopwatch, 17 s compressed into ~1.4 s of screen time
    sw = clamp((t - t_b) / 1.4) * 17 if t > t_b else 0
    d = ImageDraw.Draw(img)
    a1 = ease_out(prog(t, t_b - 0.3, 0.4))
    if a1 > 0.02:
        R = 130
        d.ellipse((CXL - R, cy - R, CXL + R, cy + R), fill=(25, 20, 50), outline=C_L, width=10)
        d.rectangle((CXL - 18, cy - R - 34, CXL + 18, cy - R - 6), fill=C_L)
        if sw > 0:
            d.pieslice((CXL - R + 16, cy - R + 16, CXL + R - 16, cy + R - 16), -90, -90 + 360 * sw / 60,
                       fill=(120, 100, 220))
        ang = -math.pi / 2 + 2 * math.pi * sw / 60
        d.line((CXL, cy, CXL + (R - 30) * math.cos(ang), cy + (R - 30) * math.sin(ang)), fill=(255, 80, 80), width=8)
        if 0 < sw < 17:
            paste_c(img, bolt_sprite(120, 1.0), CXL + 150, cy - 120, flicker(gt, 3))
        counter(img, CXL, f"{int(sw)} s", "längster Blitz", C_L, a1)
    # Sonne: years counter
    a2 = ease_out(prog(t, t_s - 0.3, 0.4))
    if a2 > 0.02:
        paste_c(img, sun_sprite(230 * (1 + 0.03 * math.sin(gt * 4)), gt * 3), CXR, cy, a2)
        v = 4.6 * ease_out(prog(t, t_45 - 0.2, 1.0))
        counter(img, CXR, E.fmt_dec(v, 1) + " Mrd.", "Jahre", C_R, ease_out(prog(t, t_45 - 0.2, 0.3)), size=62)
    if t > t_k:
        crown(img, CXR, cy - 230, prog(t, t_k, 0.5), size=0.6)
        winner(img, t, t_k, "SONNE", cy=cy + 230)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, bolt_sprite(170, 1.0), x, y, a * flicker(g, 5))

    def mr(im, x, y, a, g):
        paste_c(im, sun_sprite(140, g), x, y, a)

    brand(img, t, gt)
    E.outro(img, sc, t, gt, ml, mr, line1="Richtig geraten?", line2="Schreib's uns!")


E.setup(
    here=HERE, out="blitz_vs_sonne.mp4",
    name_l="BLITZ", name_r="SONNE", col_l=C_L, col_r=C_R,
    bg_l=((14, 8, 34), (52, 30, 100)), bg_r=((40, 10, 4), (120, 50, 10)),
    scenes=["hook", "hitze", "oft", "groesse", "finale", "outro"],
    draw=dict(hook=sc_hook, hitze=sc_hitze, oft=sc_oft, groesse=sc_groesse, finale=sc_finale, outro=sc_outro),
    sub_map=[
        (("fünftausendfünfhundert",), "5.500"), (("dreißigtausend",), "30.000"),
        (("vierundvierzigmal",), "44-mal"), (("achthundertneunundzwanzig",), "829"),
        (("eins", "Komma", "vier"), "1,4"), (("siebzehn",), "17"), (("viereinhalb",), "4,5"),
        (("eins",), "1"), (("zwei",), "2"), (("drei",), "3"),
    ],
    score=[(1, "Punkt", 1, "L"), (2, "Punkt", 1, "L"), (3, "Punkt", 1, "R"), (4, "Sieger", 1, "R"),
           (4, "Sonne", 2, "R")],
    ticks=[(1, "dreißigtausend", 1, 1.2), (4, "viereinhalb", 1, 1.0)],
)

if __name__ == "__main__":
    E.main()

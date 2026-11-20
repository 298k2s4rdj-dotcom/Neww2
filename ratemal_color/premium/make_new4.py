#!/usr/bin/env python3
"""Premium 'Rate mal' Mythen-Check Shorts: Cent vom Wolkenkratzer, alle springen, Mentos in Cola, Goldfisch-Gedächtnis.

Usage: python3 make_new4.py [--stills] [--hd] [name ...]   names: cent, springen, mentos, goldfisch
"""
import math
import os
import random
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ARGS = sys.argv[1:]
import make_new3 as M3  # noqa: E402
import make_new2 as M2  # noqa: E402
import make_new as N  # noqa: E402
import make_hq as H  # noqa: E402
import fx  # noqa: E402
from fx import E as BX, P, place  # noqa: E402

E = H.E
text, ease_out, ease_io, back_out, prog = H.text, H.ease_out, H.ease_io, H.back_out, H.prog
FONT_XB = H.FONT_XB
W, H_ = H.W, H.H
YELLOW, WHITE, GREEN, NAVY = H.YELLOW, H.WHITE, H.GREEN, H.NAVY
RED = (255, 90, 90)
CX, CY, PW, PH, PX0, PY0 = H.CX, H.CY, H.PW, H.PH, H.PX0, H.PY0
W_, card, put_panel, layer, pill, qmark, cap, label, badge = H.W_, H.card, H.put_panel, H.layer, H.pill, H.qmark, \
    H.cap, H.label, H.badge
spline, poly_mask, clip, noise_tex, glow_dot = H.spline, H.poly_mask, H.clip, H.noise_tex, H.glow_dot
fade, pulse = M2.fade, N.pulse


def CAP(name, i, t):
    return SCRIPTS[name][i], t, HL[name][i]


def SEG():
    return H.M.SEG


def myth_pill(t, txt="MYTHOS?"):
    pill(H_IMG[0], txt, 420, RED, fade(t, 0.2, 0.3))


H_IMG = [None]


def widerlegt(img, t, t0, cy=CY + 110):
    if t > t0:
        E.stamp(img, "WIDERLEGT", t, t0, cx=CX, cy=cy, size=110, rot=-7, fill=(255, 80, 80), sfill=(110, 0, 0))


def overlay():
    return Image.new("RGBA", (W, H_))


# ================================================================== CENT
@lru_cache(None)
def coin(r=90):
    s = r * 2 + 20
    c = s / 2
    m = fx.mask(s, s, lambda d, k: d.ellipse(BX((c - r, c - r, c + r, c + r), k), fill=255))
    face = fx.shaded(m, fx.rad(s, s, c - 30, c - 30, r * 1.6, [(0, (255, 210, 160)), (0.5, (205, 120, 70)),
                                                             (1, (140, 70, 40))]), depth=0.08, hi_a=0.6)
    d = ImageDraw.Draw(face)
    d.ellipse((c - r * 0.82, c - r * 0.82, c + r * 0.82, c + r * 0.82), outline=(150, 80, 45, 255), width=4)
    for i in range(12):
        a = i / 12 * 2 * math.pi
        x, y = c + r * 0.68 * math.cos(a), c + r * 0.68 * math.sin(a)
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(170, 95, 55, 255))
    out = Image.alpha_composite(face, Image.new("RGBA", face.size))
    f = H.ImageFont.truetype(FONT_XB, int(r * 0.9))
    d.text((c + 3, c + 3), "1", font=f, fill=(120, 60, 30, 255), anchor="mm")
    d.text((c, c), "1", font=f, fill=(250, 190, 140, 255), anchor="mm")
    return face


def coin_flip(img, x, y, ph, scale=1.0, rot=0.0, a=1.0):
    c = coin()
    h = max(6, int(c.height * abs(math.cos(ph))))
    cc = c.resize((c.width, h), Image.BILINEAR)
    if abs(math.cos(ph)) < 0.25:
        ed = Image.new("RGBA", (c.width, 14))
        ImageDraw.Draw(ed).rounded_rectangle((10, 0, c.width - 10, 13), 6, fill=(170, 95, 55, 255))
        cc = ed
    place(img, cc, x, y, scale=scale, rot=rot, alpha=a)


@lru_cache(None)
def tower():
    w, h = 260, 640
    steps = [(110, 0, 150, 120), (95, 110, 165, 180), (80, 170, 180, 250), (60, 240, 200, 640)]
    m = fx.mask(w, h, lambda d, k: [d.rectangle(BX(s, k), fill=255) for s in steps] +
                [d.rectangle(BX((127, -40, 133, 10), k), fill=255)])
    t = fx.shaded(m, fx.lin(w, h, [(0, (190, 200, 230)), (0.5, (120, 130, 170)), (1, (70, 75, 110))], 0), depth=0.08)
    d = ImageDraw.Draw(t)
    r = random.Random(2)
    for y in range(260, 630, 18):
        for x in range(70, 192, 14):
            if r.random() < 0.55:
                d.rectangle((x, y, x + 7, y + 9), fill=(255, 220, 140, 230))
    for x in (100, 160):
        d.line((x, 250, x, 640), fill=(200, 210, 240, 120), width=3)
    return clip(t, m)


@lru_cache(None)
def city_base():
    sky = fx.lin(PW, PH, [(0, (30, 40, 100)), (0.6, (200, 110, 120)), (1, (255, 180, 120))])
    d = ImageDraw.Draw(sky)
    r = random.Random(5)
    x = 0
    while x < PW:
        bw, bh = r.uniform(50, 110), r.uniform(120, 300)
        d.rectangle((x, PH - bh, x + bw, PH), fill=(40, 40, 80, 255))
        for wy in range(int(PH - bh + 10), PH, 16):
            for wx in range(int(x + 8), int(x + bw - 8), 13):
                if r.random() < 0.35:
                    d.rectangle((wx, wy, wx + 5, wy + 7), fill=(255, 210, 130, 200))
        x += bw + r.uniform(4, 16)
    place(sky, tower(), PW / 2, PH - 320 + 40, scale=1.0)
    return sky


def ct_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    lay = city_base().copy()
    put_panel(img, lay)
    q = (t * 0.35) % 1
    x = CX + 30 + 40 * math.sin(q * 7)
    y = PY0 + 40 + q * (PH - 100)
    coin_flip(img, x, y, gt * 9, scale=0.45)
    qmark(img, t, gt, 900, 560)
    cap(img, *CAP("cent", 0, t))


@lru_cache(None)
def bullet():
    w, h = 300, 120
    m = fx.mask(w, h, lambda d, k: (d.rounded_rectangle(BX((20, 30, 200, 90), k), int(8 * k), fill=255),
                                    d.pieslice(BX((140, 30, 280, 90), k), -90, 90, fill=255)))
    return fx.drop_shadow(fx.shaded(m, fx.lin(w, h, [(0, (255, 230, 150)), (0.5, (210, 160, 60)), (1, (130, 90, 30))]),
                                    depth=0.25, hi_a=0.7), dy=8, blur=10)


def ct_c1(img, t, gt, d):
    H_IMG[0] = img
    myth_pill(t)
    card(img)
    put_panel(img, M3.space_base(7, (90, 40, 60)).copy() if False else city_base().copy(), a=0.35)
    tk = W_("Kugel", fallback=2.4) - 0.3
    coin_flip(img, CX - 220, CY - 20, 0.2 + 0.1 * math.sin(gt * 2), scale=1.1)
    text(img, "=", 120, CX, CY - 20, fill=WHITE, stroke=8, sfill=NAVY, alpha=fade(t, tk))
    place(img, bullet(), CX + 230, CY - 20, alpha=fade(t, tk))
    text(img, "?", 160, CX, CY - 200, fill=YELLOW, stroke=9, sfill=NAVY, alpha=fade(t, tk + 0.3))
    cap(img, *CAP("cent", 1, t))


def ct_c2(img, t, gt, d):
    pill(img, "LEICHT & FLACH", 420, (255, 200, 140), fade(t, 0.2, 0.3))
    card(img)
    lay = city_base().copy()
    put_panel(img, lay, a=0.5)
    coin_flip(img, CX - 80 + 60 * math.sin(gt * 1.3), CY - 40 + 20 * math.sin(gt * 2), gt * 4, scale=1.0,
              rot=25 * math.sin(gt * 1.7))
    tl = W_("Luft", fallback=3.0) - 0.4
    a = fade(t, tl)
    for k in range(5):
        q = (gt * 0.9 + k / 5) % 1
        x = CX - 260 + k * 110
        y = CY + 260 - 220 * q
        text(img, "↑", 64, x, y, fill=(150, 210, 255), stroke=5, sfill=NAVY, alpha=a * math.sin(q * math.pi))
    label(img, "≈ 2,5 g", PX0 + 780, PY0 + 90, CX + 20, CY - 80, col=YELLOW, a=fade(t, 0.6))
    label(img, "LUFTWIDERSTAND", PX0 + 260, PY0 + 610, CX - 120, CY + 140, col=(150, 210, 255), a=a)
    cap(img, *CAP("cent", 2, t))


def ct_c3(img, t, gt, d):
    pill(img, "HÖCHSTENS ≈ 80 KM/H", 420, YELLOW, fade(t, 0.2, 0.3), size=38)
    card(img)
    put_panel(img, city_base().copy(), a=0.3)
    base = CY + 240
    for k, (lab, v, col, x, t0) in enumerate((("CENT", 80, (230, 150, 90), CX - 200, 0.4),
                                              ("PISTOLENKUGEL", 1300, (230, 210, 140), CX + 200, 1.6))):
        p = ease_io(prog(t, t0, 0.9))
        hgt = max(4, 460 * v / 1300 * p)
        ov = overlay()
        dd = ImageDraw.Draw(ov)
        dd.rounded_rectangle((x - 80, base - hgt, x + 80, base), int(min(20, hgt / 2)), fill=col + (235,))
        img.alpha_composite(ov)
        text(img, f"≈ {v:,} km/h".replace(",", "."), 36, x, base - hgt - 36, fill=WHITE, stroke=5, sfill=NAVY,
             path=FONT_XB, alpha=fade(t, t0 + 0.3))
        text(img, lab, 30, x, base + 36, fill=col, stroke=4, sfill=NAVY, path=FONT_XB, alpha=fade(t, t0))
    cap(img, *CAP("cent", 3, t))


def ct_c4(img, t, gt, d):
    pill(img, "NUR EIN SCHNIPSER", 420, (255, 200, 140), fade(t, 0.2, 0.3))
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW / 2, PH / 2, PW * 0.6, [(0, (255, 210, 160, 60)), (1, (255, 210, 160, 0))]))
    put_panel(img, lay)
    place(img, N.hand_sprite(), CX, CY + 80, scale=0.9)
    th = W_("weh", fallback=1.2) - 0.4
    k = ease_io(prog(t, 0.2, max(0.4, th)))
    if t < th + 0.05:
        coin_flip(img, CX + 20, CY - 320 + 260 * k, gt * 9, scale=0.35)
    else:
        bq = ease_out(prog(t, th, 0.8))
        coin_flip(img, CX + 20 + 220 * bq, CY - 60 - 120 * math.sin(bq * math.pi), gt * 9, scale=0.35)
        N.knack_star(img, CX + 20, CY - 60, t, th, col=(255, 200, 120))
        text(img, "AUTSCH!", 50, CX - 200, CY - 200, fill=YELLOW, stroke=6, sfill=NAVY, path=FONT_XB,
             alpha=fade(t, th) * (1 - fade(t, th + 1.5)))
    widerlegt(img, t, W_("widerlegt", fallback=5.0) - 0.2)
    cap(img, *CAP("cent", 4, t))


# ================================================================== ALLE SPRINGEN
@lru_cache(None)
def person(col=(255, 220, 120)):
    s = 40
    lay = Image.new("RGBA", (s * 3, s * 3))
    d = ImageDraw.Draw(lay)
    k = 3
    d.ellipse((14 * k, 2 * k, 26 * k, 14 * k), fill=col + (255,))
    d.rounded_rectangle((13 * k, 15 * k, 27 * k, 30 * k), 5 * k, fill=col + (255,))
    d.line((16 * k, 29 * k, 13 * k, 39 * k), fill=col + (255,), width=4 * k)
    d.line((24 * k, 29 * k, 27 * k, 39 * k), fill=col + (255,), width=4 * k)
    d.line((13 * k, 18 * k, 5 * k, 8 * k), fill=col + (255,), width=4 * k)
    d.line((27 * k, 18 * k, 35 * k, 8 * k), fill=col + (255,), width=4 * k)
    return lay.resize((s, s), Image.LANCZOS)


def jumping_earth(lay, gt, cx, cy, scale=1.0, jump=1.0):
    place(lay, M3.earth("day"), cx, cy, scale=scale * 1.8)
    R = 110 * 1.8 * scale
    for i in range(36):
        a = i / 36 * 2 * math.pi
        hop = 18 * scale * max(0.0, math.sin(gt * 5)) * jump
        x, y = cx + (R + 14 * scale + hop) * math.cos(a), cy + (R + 14 * scale + hop) * math.sin(a)
        place(lay, person(), x, y, scale=0.8 * scale, rot=-math.degrees(a) - 90)


def sp_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    lay = M3.space_base(8, (40, 80, 150)).copy()
    jumping_earth(lay, gt, PW / 2, PH / 2, scale=1.1)
    put_panel(img, lay)
    qmark(img, t, gt, 900, 560)
    cap(img, *CAP("springen", 0, t))


def sp_c1(img, t, gt, d):
    pill(img, "8 MILLIARDEN MENSCHEN", 420, (150, 210, 255), fade(t, 0.2, 0.3), size=38)
    card(img)
    lay = M3.space_base(8, (40, 80, 150)).copy()
    put_panel(img, lay)
    tw = W_("wiegen", fallback=1.0) - 0.3
    n = int(160 * ease_io(prog(t, 0.2, 1.6)))
    r = random.Random(4)
    for i in range(n):
        x = CX - 360 + (i % 20) * 38 + r.uniform(-4, 4)
        y = CY + 200 - (i // 20) * 34 + 6 * math.sin(gt * 5 + i)
        place(img, person((255, 200 + (i % 3) * 20, 120)), x, y, scale=0.85)
    a = fade(t, tw + 0.6)
    text(img, "≈ 500.000.000 t", 72, CX, CY - 220, fill=YELLOW, stroke=8, sfill=NAVY, path=FONT_XB, alpha=a,
         scale=0.85 + 0.15 * back_out(a))
    cap(img, *CAP("springen", 1, t))


def sp_c2(img, t, gt, d):
    pill(img, "ERDE VS. MENSCHEN", 420, (150, 210, 255), fade(t, 0.2, 0.3))
    card(img)
    lay = M3.space_base(8, (40, 80, 150)).copy()
    place(lay, M3.earth("day"), 360, PH / 2, scale=2.2)
    put_panel(img, lay)
    ov = overlay()
    dd = ImageDraw.Draw(ov)
    dd.ellipse((PX0 + 770 - 3, CY - 3, PX0 + 770 + 3, CY + 3), fill=(255, 220, 120, 255))
    img.alpha_composite(ov)
    label(img, "ALLE MENSCHEN", PX0 + 760, PY0 + 140, PX0 + 770, CY, col=(255, 220, 120), a=fade(t, 0.5))
    tb = W_("Billionen", fallback=1.4) - 0.3
    a = fade(t, tb)
    text(img, "× 10.000.000.000.000", 50, CX + 130, CY + 230, fill=YELLOW, stroke=6, sfill=NAVY, path=FONT_XB, alpha=a)
    text(img, "schwerer", 34, CX + 130, CY + 290, fill=WHITE, stroke=4, sfill=NAVY, path=FONT_XB, alpha=a)
    cap(img, *CAP("springen", 2, t))


@lru_cache(None)
def atom_sprite():
    s = 420
    lay = layer(s, s)
    d = ImageDraw.Draw(lay)
    c = s / 2
    for k in range(3):
        el = Image.new("RGBA", (s, s))
        ImageDraw.Draw(el).ellipse((c - 180, c - 60, c + 180, c + 60), outline=(150, 210, 255, 220), width=5)
        lay.alpha_composite(el.rotate(k * 60, resample=Image.BICUBIC))
    nm = fx.mask(s, s, lambda dd, kk: dd.ellipse(BX((c - 34, c - 34, c + 34, c + 34), kk), fill=255))
    lay.alpha_composite(fx.shaded(nm, fx.rad(s, s, c - 10, c - 10, 60, [(0, (255, 160, 140)), (1, (200, 50, 60))]),
                                  depth=0.2, hi_a=0.6))
    return fx.glow(lay, (120, 180, 255), radius=16, strength=0.6)


def sp_c3(img, t, gt, d):
    pill(img, "KLEINER ALS EIN ATOM", 420, (150, 210, 255), fade(t, 0.2, 0.3), size=38)
    card(img)
    lay = M3.space_base(9, (40, 80, 150)).copy()
    put_panel(img, lay)
    ta = W_("Atoms", fallback=2.5) - 0.4
    place(img, atom_sprite(), CX, CY - 30, scale=0.4 + 0.6 * ease_out(prog(t, ta, 0.6)), rot=gt * 10,
          alpha=fade(t, ta))
    ov = overlay()
    dd = ImageDraw.Draw(ov)
    for i in range(3):
        a0 = gt * (2 + i) + i * 2
        rr = 180 * (0.4 + 0.6 * ease_out(prog(t, ta, 0.6)))
        glow_dot(dd, CX + rr * math.cos(a0), CY - 30 + rr * 0.35 * math.sin(a0), 6, (200, 230, 255), a=fade(t, ta))
    img.alpha_composite(ov)
    text(img, "Erde bewegt sich: < 1 Atom", 40, CX, CY + 250, fill=YELLOW, stroke=6, sfill=NAVY, path=FONT_XB,
         alpha=fade(t, ta + 0.4))
    cap(img, *CAP("springen", 3, t))


def sp_c4(img, t, gt, d):
    pill(img, "SEISMOGRAF", 420, (150, 210, 255), fade(t, 0.2, 0.3))
    card(img)
    lay = layer()
    paper = fx.lin(PW, PH, [(0, (236, 228, 205)), (1, (205, 195, 170))])
    dd = ImageDraw.Draw(paper)
    for y in range(40, PH, 40):
        dd.line((0, y, PW, y), fill=(200, 190, 175, 255), width=1)
    off = (gt * 160) % 40
    for x in np.arange(-off, PW, 40):
        dd.line((x, 0, x, PH), fill=(210, 200, 185, 255), width=1)
    tz = W_("Zittern", fallback=3.5) - 0.3
    pts = []
    for x in range(0, PW, 4):
        tt = t - (PW - x) / 300
        amp = 6 + 90 * max(0.0, math.exp(-((tt - tz) * 3) ** 2))
        pts.append((x, PH / 2 + amp * math.sin(x * 0.5 + gt * 30) * (0.6 + 0.4 * math.sin(x * 0.13))))
    dd.line(pts, fill=(200, 30, 40, 255), width=5)
    lay.alpha_composite(paper)
    put_panel(img, lay)
    widerlegt(img, t, W_("widerlegt", fallback=6.5) - 0.2)
    cap(img, *CAP("springen", 4, t))


# ================================================================== MENTOS
@lru_cache(None)
def bottle():
    w, h = 220, 560
    pts = [(80, 0), (140, 0), (140, 40), (150, 80), (190, 150), (196, 220), (190, 300), (196, 380), (196, 540),
           (180, 556), (40, 556), (24, 540), (24, 380), (30, 300), (24, 220), (30, 150), (70, 80), (80, 40)]
    m = poly_mask(w, h, pts, 6)
    body = fx.shaded(m, fx.lin(w, h, [(0, (120, 60, 40, 235)), (0.5, (70, 30, 20, 240)), (1, (40, 15, 10, 245))], 0),
                     depth=0.08, hi_a=0.4)
    d = ImageDraw.Draw(body)
    d.rectangle((24, 300, 196, 400), fill=(220, 40, 50, 255))
    d.line(spline([(24, 360), (80, 330), (140, 380), (196, 340)], 8, False), fill=(255, 255, 255, 255), width=8)
    d.rounded_rectangle((44, 120, 60, 520), 8, fill=(255, 255, 255, 70))
    d.rectangle((76, 0, 144, 30), fill=(230, 40, 50, 255))
    body = clip(body, m)
    out = fx.drop_shadow(body, dy=14, blur=16, alpha=0.45)
    return out


@lru_cache(None)
def candy(r=46):
    s = r * 2 + 16
    m = fx.mask(s, s, lambda d, k: d.ellipse(BX((8, 8, s - 8, s - 8), k), fill=255))
    c = fx.shaded(m, fx.rad(s, s, s * 0.4, s * 0.35, r * 1.4, [(0, (255, 255, 255)), (1, (220, 220, 225))]), depth=0.18,
                  hi_a=0.6, dark=(120, 120, 140))
    d = ImageDraw.Draw(c)
    r_ = random.Random(3)
    for _ in range(20):
        x, y = r_.uniform(s * 0.25, s * 0.75), r_.uniform(s * 0.25, s * 0.75)
        d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(200, 200, 210, 255))
    return fx.drop_shadow(c, dy=6, blur=6, alpha=0.4)


def mt_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW / 2, PH * 0.7, PW * 0.6, [(0, (255, 200, 150, 70)), (1, (255, 200, 150, 0))]))
    put_panel(img, lay)
    place(img, bottle(), CX - 40, CY + 60, scale=0.9)
    q = (t * 0.5) % 1
    place(img, candy(), CX - 40, CY - 330 + 120 * q, scale=0.8, alpha=1 - q * 0.8, rot=q * 200)
    qmark(img, t, gt, 900, 560)
    cap(img, *CAP("mentos", 0, t))


@lru_cache(None)
def pore_surface():
    s = 560
    base = fx.rad(s, s, s * 0.4, s * 0.35, s * 0.8, [(0, (250, 250, 252)), (1, (205, 205, 215))])
    d = ImageDraw.Draw(base)
    r = random.Random(6)
    for _ in range(140):
        x, y, rr = r.uniform(0, s), r.uniform(0, s), r.uniform(6, 22)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(170, 170, 185, 255))
        d.ellipse((x - rr * 0.7, y - rr * 0.7, x + rr * 0.5, y + rr * 0.5), fill=(130, 130, 150, 255))
        d.arc((x - rr, y - rr, x + rr, y + rr), 200, 340, fill=(255, 255, 255, 255), width=2)
    return base


def magnifier(img, cx, cy, R, content, a=1.0):
    m = Image.new("L", (W, H_))
    ImageDraw.Draw(m).ellipse((cx - R, cy - R, cx + R, cy + R), fill=int(255 * a))
    big = Image.new("RGBA", (W, H_))
    big.alpha_composite(content, (int(cx - content.width / 2), int(cy - content.height / 2)))
    ov = overlay()
    ov.paste(big, (0, 0), m)
    dd = ImageDraw.Draw(ov)
    dd.ellipse((cx - R - 10, cy - R - 10, cx + R + 10, cy + R + 10), outline=(60, 65, 80, int(255 * a)), width=20)
    dd.ellipse((cx - R - 10, cy - R - 10, cx + R + 10, cy + R + 10), outline=(220, 225, 240, int(255 * a)), width=5)
    dd.line((cx + R * 0.72, cy + R * 0.72, cx + R * 1.15, cy + R * 1.15), fill=(60, 50, 40, int(255 * a)), width=34)
    img.alpha_composite(ov)


def mt_c1(img, t, gt, d):
    pill(img, "UNTER DER LUPE", 420, (255, 200, 150), fade(t, 0.2, 0.3))
    card(img)
    put_panel(img, layer())
    place(img, candy(), CX - 260, CY + 120, scale=1.4)
    tp = W_("Poren", fallback=2.5) - 0.4
    magnifier(img, CX + 90, CY - 50, 230, pore_surface(), a=fade(t, 0.4))
    label(img, "WINZIGE POREN", PX0 + 220, PY0 + 70, CX + 30, CY - 80, col=YELLOW, a=fade(t, tp))
    cap(img, *CAP("mentos", 1, t))


def mt_c2(img, t, gt, d):
    pill(img, "CO₂-BLÄSCHEN", 420, (255, 200, 150), fade(t, 0.2, 0.3))
    card(img)
    lay = layer()
    lay.alpha_composite(fx.lin(PW, PH, [(0, (120, 60, 35)), (1, (50, 20, 12))]))
    put_panel(img, lay)
    sink = ease_io(prog(t, 0.3, 2.0))
    cx_, cy_ = CX, CY - 200 + 300 * sink
    tb = W_("Bläschen", fallback=3.5) - 1.0
    k = fade(t, W_("Kohlendioxid", fallback=1.5) - 0.3, 0.8)
    ov = overlay()
    dd = ImageDraw.Draw(ov)
    r = random.Random(7)
    nb = int(40 + 120 * fade(t, tb, 1.0))
    for i in range(nb):
        ph = r.random()
        q = (gt * r.uniform(0.6, 1.2) + ph) % 1
        a0 = r.uniform(0, 2 * math.pi)
        x0, y0 = cx_ + 60 * math.cos(a0), cy_ + 60 * math.sin(a0)
        x = x0 + 20 * math.sin(q * 8 + i)
        y = y0 - (y0 - PY0 - 20) * q
        rr = 3 + 6 * q
        dd.ellipse((x - rr, y - rr, x + rr, y + rr), outline=(255, 240, 220, int(220 * k * (1 - q * 0.6))), width=2)
    img.alpha_composite(ov)
    place(img, candy(), cx_, cy_, scale=1.3, rot=gt * 20)
    label(img, "CO₂", PX0 + 780, PY0 + 100, cx_ + 60, cy_ - 160, col=(255, 240, 200), a=k)
    cap(img, *CAP("mentos", 2, t))


def mt_c3(img, t, gt, d):
    pill(img, "FONTÄNE", 420, (255, 200, 150), fade(t, 0.2, 0.3))
    card(img)
    lay = layer()
    lay.alpha_composite(fx.lin(PW, PH, [(0, (120, 180, 240)), (1, (180, 220, 250))]))
    dg = ImageDraw.Draw(lay)
    dg.rectangle((0, PH - 60, PW, PH), fill=(90, 160, 80, 255))
    put_panel(img, lay)
    bx, by = CX - 120, CY + 210
    place(img, bottle(), bx, by, scale=0.55)
    h = 400 * ease_out(prog(t, 0.3, 0.8))
    ov = overlay()
    dd = ImageDraw.Draw(ov)
    r = random.Random(2)
    top = by - 160
    for i in range(160):
        q = r.random()
        y = top - h * q
        spread = 10 + 70 * q ** 1.5
        x = bx + r.uniform(-spread, spread) + 6 * math.sin(gt * 8 + i)
        rr = r.uniform(8, 18) * (0.6 + q)
        c = (255, 245, 225) if r.random() < 0.6 else (200, 150, 110)
        dd.ellipse((x - rr, y - rr, x + rr, y + rr), fill=c + (230,))
    img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(1)))
    tm = W_("Meter", fallback=2.2) - 0.4
    a = fade(t, tm)
    rx = CX + 200
    ov2 = overlay()
    d2 = ImageDraw.Draw(ov2)
    d2.line((rx, top, rx, top - 520), fill=(255, 255, 255, int(230 * a)), width=6)
    for k in range(5):
        y = top - k * 130
        d2.line((rx - 20, y, rx + 20, y), fill=(255, 255, 255, int(230 * a)), width=5)
    img.alpha_composite(ov2)
    text(img, "mehrere", 34, rx + 140, top - 300, fill=WHITE, stroke=5, sfill=NAVY, path=FONT_XB, alpha=a)
    text(img, "METER", 50, rx + 140, top - 250, fill=YELLOW, stroke=6, sfill=NAVY, path=FONT_XB, alpha=a)
    cap(img, *CAP("mentos", 3, t))


@lru_cache(None)
def stomach():
    w, h = 460, 400
    pts = [(120, 30), (170, 40), (180, 110), (260, 120), (380, 150), (430, 240), (380, 340), (250, 370), (160, 330),
           (110, 250), (100, 150)]
    m = poly_mask(w, h, pts, 8)
    s = fx.shaded(m, fx.rad(w, h, 220, 160, 300, [(0, (255, 190, 200)), (1, (220, 100, 130))]), depth=0.1, hi_a=0.5)
    d = ImageDraw.Draw(s)
    for k in range(6):
        d.arc((150 + k * 30, 170, 330 + k * 10, 330), 200, 330, fill=(200, 90, 120, 160), width=4)
    return fx.drop_shadow(clip(s, m), dy=12, blur=14)


def mt_c4(img, t, gt, d):
    H_IMG[0] = img
    myth_pill(t, "MYTHOS: MAGEN PLATZT?")
    card(img)
    put_panel(img, layer())
    place(img, stomach(), CX - 60, CY + 20)
    ov = overlay()
    dd = ImageDraw.Draw(ov)
    r = random.Random(3)
    for i in range(14):
        q = (gt * 0.5 + i / 14) % 1
        x = CX - 60 + r.uniform(-120, 140)
        y = CY + 120 - 200 * q
        dd.ellipse((x - 8, y - 8, x + 8, y + 8), outline=(255, 255, 255, int(200 * (1 - q))), width=2)
    img.alpha_composite(ov)
    ta = W_("aufstoßen", fallback=4.5) - 0.3
    if t > ta:
        a = fade(t, ta)
        text(img, "*RÜLPS*", 64, CX + 180, CY - 220, fill=YELLOW, stroke=7, sfill=NAVY, path=FONT_XB, alpha=a,
             rotate=8, scale=0.8 + 0.2 * back_out(a))
    widerlegt(img, t, W_("Falsch", fallback=3.2) - 0.1)
    cap(img, *CAP("mentos", 4, t))


# ================================================================== GOLDFISCH
@lru_cache(None)
def goldfish():
    w, h = 300, 200
    body = [(70, 100), (110, 60), (180, 56), (230, 80), (244, 100), (230, 122), (180, 144), (110, 140)]
    m = poly_mask(w, h, body, 8)
    tail = fx.mask(w, h, lambda d, k: d.polygon(P(spline([(80, 100), (20, 40), (6, 100), (20, 160)], 8), k), fill=255))
    fin = fx.mask(w, h, lambda d, k: d.polygon(P(spline([(140, 60), (170, 14), (200, 60)], 6), k), fill=255))
    g = [(0, (255, 210, 110)), (0.5, (255, 140, 40)), (1, (210, 80, 20))]
    out = fx.shaded(tail, fx.lin(w, h, [(0, (255, 180, 90, 220)), (1, (240, 110, 40, 200))], 0), depth=0.15)
    out = Image.alpha_composite(out, fx.shaded(fin, fx.lin(w, h, g), depth=0.2))
    out = Image.alpha_composite(out, fx.shaded(m, fx.lin(w, h, g), depth=0.15, hi_a=0.6))
    d = ImageDraw.Draw(out)
    for x in range(120, 200, 14):
        d.arc((x - 10, 80, x + 10, 110), 270, 90, fill=(240, 120, 30, 180), width=2)
    d.ellipse((206, 82, 224, 100), fill=(255, 255, 255, 255))
    d.ellipse((211, 86, 222, 98), fill=(20, 20, 30, 255))
    d.ellipse((213, 87, 216, 90), fill=(255, 255, 255, 255))
    for k in range(4):
        d.line((70, 100, 14, 60 + k * 26), fill=(255, 220, 160, 120), width=2)
    return out


@lru_cache(None)
def tank():
    lay = layer()
    lay.alpha_composite(fx.lin(PW, PH, [(0, (120, 200, 240)), (1, (40, 110, 180))]))
    d = ImageDraw.Draw(lay)
    r = random.Random(4)
    for _ in range(300):
        x, y = r.uniform(0, PW), r.uniform(PH - 70, PH)
        s = r.uniform(5, 11)
        c = r.choice([(220, 200, 160), (180, 150, 110), (240, 230, 210), (150, 120, 90)])
        d.ellipse((x - s, y - s * 0.7, x + s, y + s * 0.7), fill=c + (255,))
    for x in (80, 170, 760, 850):
        for j in range(3):
            pts = [(x + j * 16 + 14 * math.sin(i * 0.7 + j), PH - 60 - i * 26) for i in range(10)]
            d.line(pts, fill=(60, 160, 80, 230), width=9, joint="curve")
    rays = layer()
    dr = ImageDraw.Draw(rays)
    for x in (200, 420, 640):
        dr.polygon([(x - 30, 0), (x + 30, 0), (x + 120, PH), (x + 20, PH)], fill=(255, 255, 255, 22))
    lay.alpha_composite(rays.filter(ImageFilter.GaussianBlur(10)))
    return lay


def fish_at(lay, x, y, gt, scale=1.0, flip=False):
    f = goldfish()
    if flip:
        f = ImageOps.mirror(f)
    place(lay, f, x, y + 8 * math.sin(gt * 2.5), scale=scale, rot=4 * math.sin(gt * 3))


def gf_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    lay = tank().copy()
    x = (gt * 90) % (PW + 300) - 150
    fish_at(lay, x, 300, gt, 1.1)
    fish_at(lay, PW - (gt * 60 + 300) % (PW + 300) + 150, 450, gt, 0.7, flip=True)
    dd = ImageDraw.Draw(lay)
    for i in range(8):
        q = (gt * 0.4 + i / 8) % 1
        dd.ellipse((600 + i * 12 - 6, PH - 80 - 500 * q - 6, 600 + i * 12 + 6, PH - 80 - 500 * q + 6),
                   outline=(255, 255, 255, int(200 * (1 - q))), width=2)
    put_panel(img, lay)
    qmark(img, t, gt, 900, 560)
    cap(img, *CAP("goldfisch", 0, t))


def gf_c1(img, t, gt, d):
    H_IMG[0] = img
    myth_pill(t, "MYTHOS: 3 SEKUNDEN?")
    card(img)
    lay = tank().copy()
    fish_at(lay, 300, 330, gt, 1.3)
    put_panel(img, lay)
    td = W_("drei", fallback=2.0) - 0.4
    H.stopwatch(img, CX + 230, CY - 60, ease_io(prog(t, td, 1.0)) * 3 / 60, fade(t, td))
    text(img, "3 s", 60, CX + 230, CY + 140, fill=YELLOW, stroke=7, sfill=NAVY, path=FONT_XB, alpha=fade(t, td))
    text(img, "?", 120, CX - 150, CY - 220, fill=WHITE, stroke=8, sfill=NAVY, alpha=fade(t, 0.6))
    cap(img, *CAP("goldfisch", 1, t))


def lever_scene(img, t, gt, press, food=0.0, fish_x=None):
    lay = tank().copy()
    d = ImageDraw.Draw(lay)
    lx, ly = 700, 260
    ang = math.radians(-20 + 35 * press)
    d.line((lx, 60, lx, ly), fill=(200, 200, 210, 255), width=10)
    d.line((lx, ly, lx - 120 * math.cos(ang), ly + 120 * math.sin(ang)), fill=(255, 210, 60, 255), width=16)
    d.ellipse((lx - 14, ly - 14, lx + 14, ly + 14), fill=(120, 120, 140, 255))
    d.rounded_rectangle((lx - 40, 20, lx + 60, 64), 10, fill=(160, 160, 180, 255))
    if food > 0.01:
        r = random.Random(3)
        for i in range(10):
            fx_ = lx + r.uniform(-30, 50)
            fy = 70 + 300 * food * r.uniform(0.6, 1.0)
            d.ellipse((fx_ - 6, fy - 6, fx_ + 6, fy + 6), fill=(190, 110, 50, 255))
    fx0 = fish_x if fish_x is not None else 300
    fish_at(lay, fx0, 300, gt, 1.0)
    put_panel(img, lay)


def gf_c2(img, t, gt, d):
    pill(img, "DAS EXPERIMENT", 420, (255, 190, 90), fade(t, 0.2, 0.3))
    card(img)
    th = W_("Hebel", fallback=2.8) - 0.3
    tf = W_("Futter", fallback=2.0) - 0.3
    k = ease_io(prog(t, 0.4, max(0.6, th - 0.4)))
    press = pulse(t, th, 0.15, 0.6)
    lever_scene(img, t, gt, press, food=ease_out(prog(t, th + 0.1, 0.8)), fish_x=260 + 300 * k)
    label(img, "HEBEL", PX0 + 820, PY0 + 400, PX0 + 620, PY0 + 290, col=YELLOW, a=fade(t, th - 0.2))
    label(img, "FUTTER", PX0 + 820, PY0 + 130, PX0 + 720, PY0 + 90, col=(255, 200, 140), a=fade(t, tf))
    cap(img, *CAP("goldfisch", 2, t))


def gf_c3(img, t, gt, d):
    pill(img, "NACH MONATEN", 420, (255, 190, 90), fade(t, 0.2, 0.3))
    card(img)
    press = pulse(t, 1.6, 0.15, 0.6)
    lever_scene(img, t, gt, press, food=ease_out(prog(t, 1.7, 0.8)), fish_x=560)
    tm = W_("Monaten", fallback=2.0) - 0.4
    a = fade(t, tm)
    months = ["JAN", "FEB", "MÄR"]
    for i, mo in enumerate(months):
        aa = fade(t, tm + i * 0.25)
        x = PX0 + 110 + i * 130
        ov = overlay()
        dd = ImageDraw.Draw(ov)
        dd.rounded_rectangle((x - 54, PY0 + 40, x + 54, PY0 + 150), 16, fill=(255, 255, 255, int(235 * aa)))
        dd.rounded_rectangle((x - 54, PY0 + 40, x + 54, PY0 + 76), 16, fill=(220, 60, 60, int(255 * aa)))
        img.alpha_composite(ov)
        text(img, mo, 32, x, PY0 + 112, fill=(40, 34, 70), path=FONT_XB, alpha=aa)
    badge(img, "check", PX0 + PW - 120, PY0 + PH - 100, fade(t, tm + 0.9), r=50)
    del a
    cap(img, *CAP("goldfisch", 3, t))


def gf_c4(img, t, gt, d):
    pill(img, "SCHLAUER ALS GEDACHT", 420, (255, 190, 90), fade(t, 0.2, 0.3), size=38)
    card(img)
    lay = tank().copy()
    fish_at(lay, 260, 360, gt, 1.0)
    put_panel(img, lay)
    items = [("Farben", W_("Farben", fallback=1.4) - 0.3), ("Töne", W_("Töne", fallback=2.0) - 0.3),
             ("Formen", W_("Formen", fallback=2.6) - 0.3)]
    for i, (lab, t0) in enumerate(items):
        p = fade(t, t0)
        if p <= 0.02:
            continue
        x, y = CX + 200, PY0 + 120 + i * 150
        ov = overlay()
        dd = ImageDraw.Draw(ov)
        dd.rounded_rectangle((x - 150, y - 56, x + 150, y + 56), 26, fill=(14, 10, 34, int(210 * p)),
                             outline=(255, 255, 255, int(150 * p)), width=3)
        if i == 0:
            for j, c in enumerate(((255, 80, 80), (80, 160, 255), (90, 210, 120))):
                dd.ellipse((x - 130 + j * 34, y - 16, x - 100 + j * 34, y + 14), fill=c + (int(255 * p),))
        elif i == 2:
            dd.polygon([(x - 120, y + 18), (x - 98, y - 20), (x - 76, y + 18)], fill=(255, 210, 80, int(255 * p)))
            dd.rectangle((x - 66, y - 14, x - 40, y + 14), fill=(150, 210, 255, int(255 * p)))
        img.alpha_composite(ov)
        if i == 1:
            badge(img, "note", x - 105, y, p, r=26)
        text(img, lab, 40, x + 40, y, fill=WHITE, path=FONT_XB, alpha=p)
    widerlegt(img, t, W_("widerlegt", fallback=5.0) - 0.2)
    cap(img, *CAP("goldfisch", 4, t))


# ================================================================== registration
SCRIPTS = {
    "cent": ["Rate mal, was passiert, wenn ein Cent vom Empire State Building fällt.",
             "Viele glauben, er wäre tödlich wie eine Kugel.",
             "Doch der Cent ist leicht und flach. Er trudelt und wird von der Luft stark gebremst.",
             "Schneller als etwa achtzig Kilometer pro Stunde wird er nicht.",
             "Trifft er dich, tut es kurz weh wie ein Schnipser. Gefährlich ist er nicht. Mythos widerlegt."],
    "springen": ["Rate mal, was passiert, wenn alle Menschen auf der Erde gleichzeitig springen.",
                 "Zusammen wiegen wir etwa fünfhundert Millionen Tonnen. Das klingt nach sehr viel.",
                 "Doch die Erde ist über zehn Billionen Mal schwerer als wir alle zusammen.",
                 "Sie bewegt sich dabei weniger als die Breite eines Atoms.",
                 "Spüren würde das niemand. Höchstens Erdbebenmessgeräte würden ein kleines Zittern aufzeichnen. "
                 "Mythos widerlegt."],
    "mentos": ["Rate mal, was passiert, wenn du Mentos in Cola wirfst.",
               "Die Oberfläche der Mentos ist voller winziger Poren.",
               "An ihnen bildet das gelöste Kohlendioxid blitzschnell Millionen Bläschen.",
               "Der Schaum schießt als Fontäne mehrere Meter in die Luft.",
               "Und der Mythos, dass dein Magen platzt, wenn du beides isst? Falsch. Du musst höchstens aufstoßen."],
    "goldfisch": ["Rate mal, was passiert, wenn du einem Goldfisch einen Trick beibringst.",
                  "Angeblich hat er nur ein Gedächtnis von drei Sekunden.",
                  "Doch Forscher brachten Goldfischen bei, für Futter einen Hebel zu drücken.",
                  "Die Fische erinnerten sich noch nach Monaten daran.",
                  "Goldfische können sogar Farben, Töne und Formen unterscheiden lernen. Mythos widerlegt."],
}
HL = {
    "cent": [("RATE", "MAL,", "CENT"), ("TÖDLICH",), ("LEICHT", "FLACH.", "GEBREMST."), ("ACHTZIG",),
             ("WIDERLEGT.",)],
    "springen": [("RATE", "MAL,", "SPRINGEN."), ("FÜNFHUNDERT", "MILLIONEN"), ("BILLIONEN",), ("ATOMS.",),
                 ("WIDERLEGT.",)],
    "mentos": [("RATE", "MAL,", "MENTOS", "COLA"), ("POREN.",), ("MILLIONEN", "BLÄSCHEN."), ("METER",),
               ("FALSCH.", "AUFSTOSSEN.")],
    "goldfisch": [("RATE", "MAL,", "GOLDFISCH"), ("DREI", "SEKUNDEN."), ("HEBEL",), ("MONATEN",), ("WIDERLEGT.",)],
}
NEW = {
    "cent": dict(bg=((20, 16, 50), (110, 60, 90), (140, 90, 70)), out="mythos_cent_hq",
                 scenes=[ct_hook, ct_c1, ct_c2, ct_c3, ct_c4, H.outro]),
    "springen": dict(bg=((8, 14, 44), (40, 70, 140), (60, 90, 160)), out="mythos_alle_springen_hq",
                     scenes=[sp_hook, sp_c1, sp_c2, sp_c3, sp_c4, H.outro]),
    "mentos": dict(bg=((40, 12, 14), (150, 60, 40), (160, 90, 60)), out="mythos_mentos_cola_hq",
                   scenes=[mt_hook, mt_c1, mt_c2, mt_c3, mt_c4, H.outro]),
    "goldfisch": dict(bg=((8, 30, 50), (40, 110, 160), (200, 120, 40)), out="mythos_goldfisch_hq",
                      scenes=[gf_hook, gf_c1, gf_c2, gf_c3, gf_c4, H.outro]),
}
KEYS = {"ct_c4": ("widerlegt", "thump"), "sp_c4": ("widerlegt", "thump"), "mt_c4": ("Falsch", "thump"),
        "gf_c4": ("widerlegt", "thump"), "mt_c3": ("Schaum", "pop"), "sp_c3": ("Atoms", "ding"),
        "gf_c2": ("Hebel", "pop"), "gf_c3": ("Monaten", "ding"), "ct_c3": ("achtzig", "pop"),
        "sp_c1": ("Tonnen", "pop"), "mt_c1": ("Poren", "pop"), "ct_c1": ("Kugel", "pop")}
N.NEW.update(NEW)
N.SCRIPTS.update(SCRIPTS)
N.KEYS.update(KEYS)
_prev_events = N.events


def events():
    ev = _prev_events()
    for s in H.CUR["segs"]:
        st, nm = s["start"], s["fn"].__name__
        if nm == "ct_c4":
            ev.append((st + H.seg_word(s, "weh", 1.2) - 0.4, "tick", 0.12))
        if nm == "mt_c3":
            ev.append((st + 0.3, "whoosh", 0.14))
    return ev


N.events = events

if __name__ == "__main__":
    names = [a for a in ARGS if not a.startswith("--")] or list(NEW)
    for nm in names:
        if "--stills" in ARGS:
            N.stills(nm)
        else:
            N.make(nm, uhd="--hd" not in ARGS)

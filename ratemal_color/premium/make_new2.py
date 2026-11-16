#!/usr/bin/env python3
"""Four more premium 'Rate mal' Shorts: Blitz, Popcorn, Honig, zugefrorener See.

Reuses the premium engine (make_hq.py) and the voiced/synthetic timing + render pipeline in make_new.py.
Usage: python3 make_new2.py [--stills] [--hd] [name ...]   names: blitz, popcorn, honig, eis
"""
import math
import os
import random
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ARGS = sys.argv[1:]
import make_new as N  # noqa: E402
import make_hq as H  # noqa: E402
import fx  # noqa: E402
from fx import E as BX, P, place  # noqa: E402

E = H.E
text, text_w, ease_out, ease_io, back_out, prog = H.text, H.text_w, H.ease_out, H.ease_io, H.back_out, H.prog
FONT_XB = H.FONT_XB
W, H_ = H.W, H.H
YELLOW, WHITE, RED, BLUE, GREEN, NAVY = H.YELLOW, H.WHITE, H.RED, H.BLUE, H.GREEN, H.NAVY
CX, CY, PW, PH, PX0, PY0 = H.CX, H.CY, H.PW, H.PH, H.PX0, H.PY0
W_, card, put_panel, layer, pill, qmark, cap, label, badge = H.W_, H.card, H.put_panel, H.layer, H.pill, H.qmark, \
    H.cap, H.label, H.badge
spline, poly_mask, clip, noise_tex, ss_layer, glow_dot = H.spline, H.poly_mask, H.clip, H.noise_tex, H.ss_layer, \
    H.glow_dot
pulse = N.pulse


def fade(t, t0, d=0.4):
    return ease_out(prog(t, t0, d))


def sh_ellipse(w, h, box, stops, **kw):
    m = fx.mask(w, h, lambda d, k: d.ellipse(BX(box, k), fill=255))
    return fx.shaded(m, fx.lin(w, h, stops), **kw)


@lru_cache(None)
def thermo_glass():
    w, h = 120, 420
    m = fx.mask(w, h, lambda d, k: (d.rounded_rectangle(BX((40, 10, 80, 340), k), int(20 * k), fill=255),
                                    d.ellipse(BX((22, 320, 98, 396), k), fill=255)))
    g = fx.shaded(m, fx.lin(w, h, [(0, (255, 255, 255, 120)), (1, (220, 235, 255, 90))], 0), depth=0.2, hi_a=0.6,
                  outline=(255, 255, 255), ow=3)
    d = ImageDraw.Draw(g)
    for k in range(9):
        y = 40 + k * 32
        d.line((82, y, 98, y), fill=(255, 255, 255, 220), width=3)
    return fx.drop_shadow(g, dy=8, blur=10, alpha=0.4)


def thermo(img, x, y, frac, a=1.0, col=(255, 70, 60)):
    if a <= 0.02:
        return
    place(img, thermo_glass(), x, y, alpha=a)
    lay = Image.new("RGBA", (W, H_))
    d = ImageDraw.Draw(lay)
    top = y + 140 - 300 * frac
    d.rounded_rectangle((x - 10, top, x + 10, y + 150), 10, fill=col + (int(255 * a),))
    d.ellipse((x - 30, y + 122, x + 30, y + 182), fill=col + (int(255 * a),))
    d.ellipse((x - 18, y + 130, x - 4, y + 146), fill=(255, 255, 255, int(150 * a)))
    img.alpha_composite(lay)


# ================================================================== BLITZ
@lru_cache(None)
def house_sprite():
    w, h = 220, 200
    wall = fx.mask(w, h, lambda d, k: d.rectangle(BX((30, 90, 190, 196), k), fill=255))
    out = fx.shaded(wall, fx.lin(w, h, [(0, (90, 80, 110)), (1, (50, 44, 70))], 0), depth=0.1)
    roof = fx.mask(w, h, lambda d, k: d.polygon(P([(10, 96), (110, 14), (210, 96)], k), fill=255))
    out = Image.alpha_composite(out, fx.shaded(roof, fx.lin(w, h, [(0, (140, 60, 60)), (1, (70, 25, 30))]), depth=0.1))
    d = ImageDraw.Draw(out)
    for x0 in (52, 128):
        d.rectangle((x0, 112, x0 + 40, 150), fill=(255, 210, 110, 255))
        d.line((x0 + 20, 112, x0 + 20, 150), fill=(120, 80, 40, 255), width=3)
        d.line((x0, 131, x0 + 40, 131), fill=(120, 80, 40, 255), width=3)
    d.rectangle((96, 156, 124, 196), fill=(60, 40, 30, 255))
    return out


@lru_cache(None)
def storm_cloud(seed, w=420, h=170):
    r = random.Random(seed)
    m = Image.new("L", (w, h))
    d = ImageDraw.Draw(m)
    for _ in range(10):
        cx, cy = r.uniform(w * 0.18, w * 0.82), r.uniform(h * 0.4, h * 0.65)
        rr = r.uniform(h * 0.22, h * 0.38)
        d.ellipse((cx - rr * 1.3, cy - rr, cx + rr * 1.3, cy + rr), fill=255)
    d.rounded_rectangle((w * 0.1, h * 0.55, w * 0.9, h * 0.85), int(h * 0.14), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(3))
    return fx.shaded(m, fx.lin(w, h, [(0, (120, 125, 160)), (1, (45, 45, 70))]), depth=0.12, dark=(10, 10, 30),
                     dark_a=0.5, hi=(200, 210, 255), hi_a=0.35)


@lru_cache(None)
def storm_base():
    sky = fx.lin(PW, PH, [(0, (16, 18, 46)), (0.6, (50, 40, 90)), (1, (80, 60, 110))])
    d = ImageDraw.Draw(sky)
    d.polygon(spline([(-20, 520), (160, 470), (360, 500), (560, 460), (760, 490), (940, 470), (940, 700), (-20, 700)], 6),
              fill=(30, 34, 60, 255))
    d.polygon(spline([(-20, 580), (220, 548), (480, 570), (720, 545), (940, 565), (940, 700), (-20, 700)], 6),
              fill=(22, 40, 40, 255))
    # tree
    tr = layer()
    dt = ImageDraw.Draw(tr)
    dt.polygon([(232, 560), (246, 420), (258, 420), (270, 560)], fill=(40, 28, 24, 255))
    crown = spline([(250, 300), (310, 330), (330, 390), (300, 440), (200, 440), (170, 390), (190, 330)], 8)
    dt.polygon(crown, fill=(26, 52, 40, 255))
    sky.alpha_composite(tr)
    place(sky, house_sprite(), 640, 480, scale=0.9)
    return sky


def bolt_pts(seed, x0, y0, x1, y1, n=12, jit=36):
    r = random.Random(seed)
    pts = [(x0, y0)]
    for i in range(1, n):
        f = i / n
        pts.append((x0 + (x1 - x0) * f + r.uniform(-jit, jit), y0 + (y1 - y0) * f))
    pts.append((x1, y1))
    br = []
    for _ in range(3):
        k = r.randint(2, n - 4)
        b = [pts[k]]
        sd = r.choice((-1, 1))
        for _ in range(4):
            b.append((b[-1][0] + sd * r.uniform(18, 44), b[-1][1] + r.uniform(24, 44)))
        br.append(b)
    return pts, br


def draw_bolt(lay, pts, br, a=1.0, w=6):
    if a <= 0.02:
        return
    fx.line_glow(lay, pts, (190, 210, 255), w, glow_w=w * 8, alpha=a)
    ImageDraw.Draw(lay).line(pts, fill=(255, 255, 255, int(255 * a)), width=max(2, w // 2), joint="curve")
    for b in br:
        fx.line_glow(lay, b, (190, 210, 255), max(2, w // 2), glow_w=w * 4, alpha=a * 0.8)


def rain(lay, gt, n=70, a=1.0):
    d = ImageDraw.Draw(lay)
    r = random.Random(4)
    for _ in range(n):
        x0, y0, sp = r.uniform(0, PW + 200), r.uniform(0, PH), r.uniform(600, 900)
        y = (y0 + gt * sp) % (PH + 60) - 30
        x = (x0 - gt * sp * 0.25) % (PW + 200) - 100
        d.line((x, y, x - 8, y + 26), fill=(180, 200, 255, int(110 * a)), width=2)


def storm_scene(img, t, gt, strikes=(), cloud_y=90, extra=None, tree_hit=True):
    lay = storm_base().copy()
    fl = 0.0
    for s0 in strikes:
        p = t - s0
        if 0 <= p < 0.45:
            a = 1 - p / 0.45
            fl = max(fl, a)
            pts, br = bolt_pts(int(s0 * 10), 420 + (s0 * 97) % 160, cloud_y + 30, 250 if tree_hit else 460, 330)
            draw_bolt(lay, pts, br, a=min(1, a * 1.6))
    for k, (seed, y, sp, sc) in enumerate(((1, cloud_y, 10, 1.3), (2, cloud_y - 30, 16, 1.0), (3, cloud_y + 20, 6, 1.1))):
        x = (k * 340 + gt * sp) % (PW + 500) - 250
        place(lay, storm_cloud(seed), x, y, scale=sc)
    rain(lay, gt)
    if extra:
        extra(lay)
    if fl > 0:
        wl = Image.new("RGBA", lay.size, (230, 235, 255, int(110 * fl)))
        lay = Image.alpha_composite(lay, wl)
    put_panel(img, lay)
    return fl


def bz_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    storm_scene(img, t, gt, strikes=(1.0, 2.6))
    qmark(img, t, gt, 900, 560)
    cap(img, *CAP("blitz", 0, t))


def bz_c1(img, t, gt, d):
    pill(img, "BLITZKANAL", 420, (190, 210, 255), fade(t, 0.2, 0.3))
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, 330, PH / 2, 360, [(0, (255, 200, 120, 90)), (1, (255, 200, 120, 0))]))
    pts, br = bolt_pts(7 + int(gt * 6) % 3, 330, -20, 330, PH + 20, n=14, jit=26)
    draw_bolt(lay, pts, br, a=0.85 + 0.15 * math.sin(gt * 30), w=9)
    dd = ImageDraw.Draw(lay)
    heat = fade(t, W_("heizt", fallback=1.0) - 0.1, 1.5)
    r = random.Random(3)
    for i in range(60):
        y0 = r.uniform(20, PH - 20)
        side = r.choice((-1, 1))
        dist = r.uniform(30, 220)
        x = 330 + side * dist + 6 * math.sin(gt * 40 + i) * heat
        y = y0 + 6 * math.cos(gt * 37 + i) * heat
        hot = max(0.0, 1 - dist / 220) * heat
        col = (int(120 + 135 * hot), int(170 + 40 * hot - 100 * hot), int(255 - 200 * hot))
        glow_dot(dd, x, y, 5, col, a=0.7)
    put_panel(img, lay)
    td = W_("dreißigtausend", fallback=3.0) - 0.3
    k = ease_io(prog(t, td - 0.6, 1.2))
    thermo(img, PX0 + 720, CY - 120, k, a=fade(t, 0.5))
    val = int(round(30000 * k / 500) * 500)
    text(img, f"{val:,}".replace(",", ".") + " °C", 60, PX0 + 720, CY + 170, fill=YELLOW, stroke=7, sfill=NAVY,
         path=FONT_XB, alpha=fade(t, 0.5))
    cap(img, *CAP("blitz", 1, t))


@lru_cache(None)
def sun_sprite(r=150):
    s = r * 2 + 20
    m = fx.mask(s, s, lambda d, k: d.ellipse(BX((10, 10, s - 10, s - 10), k), fill=255))
    sp = fx.apply_mask(fx.rad(s, s, s * 0.45, s * 0.42, r * 1.1, [(0, (255, 255, 220)), (0.5, (255, 210, 80)),
                                                                  (1, (240, 120, 30))]), m)
    sp = Image.alpha_composite(sp, clip(noise_tex(s, s, (200, 90, 10), amt=6, blur=1.5, seed=3), m))
    return fx.glow(sp, (255, 170, 60), radius=40, strength=0.8)


def bz_c2(img, t, gt, d):
    pill(img, "HEISSER ALS DIE SONNE", 420, YELLOW, fade(t, 0.2, 0.3), size=38)
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW / 2, PH / 2, PW * 0.6, [(0, (255, 200, 120, 40)), (1, (255, 200, 120, 0))]))
    put_panel(img, lay)
    ts = W_("Sonne", fallback=2.8) - 0.3
    base = CY + 250
    # bars
    for k, (lab, val, col, x, t0) in enumerate((("SONNE", 5500, (255, 170, 60), CX - 220, ts),
                                                ("BLITZ", 30000, (170, 200, 255), CX + 220, 0.4))):
        p = ease_io(prog(t, t0, 1.0))
        hgt = 420 * val / 30000 * p
        bl = Image.new("RGBA", (W, H_))
        bd = ImageDraw.Draw(bl)
        if hgt > 2:
            bd.rounded_rectangle((x - 80, base - hgt, x + 80, base), min(20, int(hgt / 2)), fill=col + (230,))
        if hgt > 30:
            bd.rounded_rectangle((x - 70, base - hgt + 8, x - 50, base - 8), 10, fill=(255, 255, 255, 80))
        img.alpha_composite(bl)
        text(img, f"≈ {val:,}".replace(",", ".") + " °C", 36, x, base - hgt - 40, fill=WHITE, stroke=5, sfill=NAVY,
             path=FONT_XB, alpha=fade(t, t0 + 0.3))
        text(img, lab, 34, x, base + 40, fill=col, stroke=5, sfill=NAVY, path=FONT_XB, alpha=fade(t, t0))
    place(img, sun_sprite(), CX - 220, CY - 250, scale=0.55, alpha=fade(t, ts), rot=gt * 4)
    lay2 = Image.new("RGBA", (W, H_))
    pts, br = bolt_pts(5, CX + 220, CY - 330, CX + 200, CY - 170, n=6, jit=20)
    draw_bolt(lay2, pts, [], a=fade(t, 0.4), w=7)
    img.alpha_composite(lay2)
    tf = W_("fünfmal", fallback=0.8) - 0.1
    if t > tf:
        E.stamp(img, "× 5", t, tf, cx=CX, cy=CY - 60, size=150, rot=-6, fill=YELLOW, sfill=(170, 20, 0))
    cap(img, *CAP("blitz", 2, t))


def bz_c3(img, t, gt, d):
    td = W_("Donner", fallback=4.5) - 0.1
    pill(img, "DRUCKWELLE", 420, (190, 210, 255), fade(t, 0.2, 0.3))
    card(img)
    te = W_("explosionsartig", fallback=1.2) - 0.2

    def extra(lay):
        dd = ImageDraw.Draw(lay)
        for k in range(4):
            q = ((t - te) * 0.6 + k * 0.25) % 1 if t > te else -1
            if q < 0:
                continue
            rr = 40 + 520 * q
            dd.ellipse((250 - rr, 330 - rr * 0.7, 250 + rr, 330 + rr * 0.7), outline=(220, 230, 255, int(200 * (1 - q))),
                       width=6)
    strikes = [s for s in np.arange(0.2, 8, 2.2)]
    storm_scene(img, t, gt, strikes=strikes, extra=extra)
    if t > td:
        E.stamp(img, "DONNER!", t, td, cx=CX, cy=CY + 210, size=130, rot=-5, fill=YELLOW, sfill=(170, 20, 0))
    cap(img, *CAP("blitz", 3, t))


def bz_c4(img, t, gt, d):
    pill(img, "SEKUNDEN ZÄHLEN", 420, YELLOW, fade(t, 0.2, 0.3))
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW / 2, PH * 0.4, PW * 0.6, [(0, (170, 200, 255, 50)), (1, (170, 200, 255, 0))]))
    put_panel(img, lay)
    tsec = W_("Sekunden", fallback=1.0) - 0.2
    tdrei = W_("drei", fallback=4.0) - 0.2
    n = max(0, min(6, int((t - tsec) / 0.45) + 1)) if t > tsec else 0
    # big counter
    if n > 0:
        pl = pulse(t, tsec + (n - 1) * 0.45, 0.05, 0.25)
        ring = Image.new("RGBA", (W, H_))
        rd = ImageDraw.Draw(ring)
        rd.ellipse((CX - 150, CY - 290, CX + 150, CY + 10), fill=(14, 10, 34, 220), outline=(190, 210, 255, 255), width=8)
        rd.arc((CX - 150, CY - 290, CX + 150, CY + 10), -90, -90 + 360 * n / 6, fill=YELLOW + (255,), width=14)
        img.alpha_composite(ring)
        text(img, str(n), 170 * (1 + 0.08 * pl), CX, CY - 150, fill=WHITE, stroke=8, sfill=NAVY, path=FONT_XB)
        text(img, "Sekunden", 34, CX, CY - 40, fill=(190, 210, 255), path=FONT_XB)
    if t > tdrei:
        a = fade(t, tdrei)
        text(img, "6 s ÷ 3 = 2 km", 76, CX, CY + 110, fill=YELLOW, stroke=8, sfill=NAVY, path=FONT_XB, alpha=a,
             scale=0.85 + 0.15 * back_out(a))
    tk = W_("Kilometer", fallback=5.5) - 0.3
    if t > tk:
        a = fade(t, tk)
        y = CY + 250
        lay2 = Image.new("RGBA", (W, H_))
        dl = ImageDraw.Draw(lay2)
        dl.line((PX0 + 150, y, PX0 + PW - 170, y), fill=(255, 255, 255, int(200 * a)), width=5)
        for x in (PX0 + 150, PX0 + PW - 170):
            dl.line((x, y - 16, x, y + 16), fill=(255, 255, 255, int(220 * a)), width=5)
        img.alpha_composite(lay2)
        place(img, house_sprite(), PX0 + 120, y - 60, scale=0.45, alpha=a)
        place(img, storm_cloud(2), PX0 + PW - 150, y - 80, scale=0.45, alpha=a)
        text(img, "2 km", 40, CX, y - 34, fill=WHITE, stroke=5, sfill=NAVY, path=FONT_XB, alpha=a)
    cap(img, *CAP("blitz", 4, t))


# ================================================================== POPCORN
@lru_cache(None)
def pop_piece(seed, s=220):
    r = random.Random(seed)

    def fn(d, k):
        for i in range(8):
            a = i / 8 * 2 * math.pi + r.uniform(-0.3, 0.3)
            rr = r.uniform(30, 48)
            dist = r.uniform(30, 58)
            x, y = s / 2 + dist * math.cos(a), s / 2 + dist * math.sin(a)
            d.ellipse(BX((x - rr, y - rr, x + rr, y + rr), k), fill=255)
        d.ellipse(BX((s / 2 - 48, s / 2 - 48, s / 2 + 48, s / 2 + 48), k), fill=255)
    m = fx.mask(s, s, fn)
    pc = fx.shaded(m, fx.rad(s, s, s * 0.42, s * 0.38, s * 0.6, [(0, (255, 253, 240)), (0.7, (250, 236, 200)),
                                                                 (1, (230, 200, 140))]), depth=0.1, dark=(150, 110, 50),
                   dark_a=0.45, hi_a=0.5)
    d = ImageDraw.Draw(pc)
    for _ in range(3):
        x, y = r.uniform(s * 0.35, s * 0.65), r.uniform(s * 0.4, s * 0.7)
        d.polygon([(x, y), (x + 14, y + 4), (x + 6, y + 14)], fill=(230, 140, 40, 255))
    return fx.drop_shadow(pc, dy=8, blur=8, alpha=0.35)


@lru_cache(None)
def box_sprite():
    w, h = 380, 460
    top_l, top_r, bot_l, bot_r, ytop, ybot = 30, 350, 80, 300, 120, 450
    m = fx.mask(w, h, lambda d, k: d.polygon(P([(top_l, ytop), (top_r, ytop), (bot_r, ybot), (bot_l, ybot)], k),
                                             fill=255))
    st = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    d = ImageDraw.Draw(st)
    n = 7
    for i in range(n):
        if i % 2:
            continue
        f0, f1 = i / n, (i + 1) / n
        d.polygon([(top_l + (top_r - top_l) * f0, ytop), (top_l + (top_r - top_l) * f1, ytop),
                   (bot_l + (bot_r - bot_l) * f1, ybot), (bot_l + (bot_r - bot_l) * f0, ybot)], fill=(220, 40, 50, 255))
    box = fx.shaded(m, st, depth=0.08, dark_a=0.45, hi_a=0.3)
    rim = fx.mask(w, h, lambda dd, k: dd.rounded_rectangle(BX((22, 108, 358, 132), k), int(8 * k), fill=255))
    box = Image.alpha_composite(box, fx.shaded(rim, fx.lin(w, h, [(0, (255, 255, 255)), (1, (220, 220, 230))]),
                                               depth=0.3))
    heap = layer(w, h)
    for i, (x, y, sd) in enumerate(((90, 110, 1), (190, 90, 2), (290, 110, 3), (140, 60, 4), (240, 60, 5),
                                    (190, 30, 0))):
        place(heap, pop_piece(sd), x, y, scale=0.62, rot=i * 40)
    out = Image.alpha_composite(heap, box)
    return fx.drop_shadow(out, dy=14, blur=16, alpha=0.4)


def popping(img, t, gt, cx, cy, n=8, a=1.0):
    r = random.Random(9)
    for i in range(n):
        per = r.uniform(1.4, 2.2)
        ph = r.random() * per
        q = ((gt + ph) % per) / per
        vx, vy = r.uniform(-260, 260), r.uniform(-700, -520)
        tt = q * 1.2
        x = cx + vx * tt
        y = cy + vy * tt + 0.5 * 900 * tt * tt
        place(img, pop_piece(i % 6), x, y, scale=0.45, rot=q * 360 * (1 if i % 2 else -1), alpha=a * min(1, (1 - q) * 4))


KERNEL = [(460, 80), (590, 150), (650, 300), (620, 450), (540, 560), (460, 590), (380, 560), (300, 450), (270, 300),
          (330, 150)]


@lru_cache(None)
def kernel_section():
    lay = layer()
    m = poly_mask(PW, PH, KERNEL, 10)
    hull = fx.shaded(m, fx.rad(PW, PH, 400, 200, 460, [(0, (255, 214, 90)), (0.6, (240, 160, 30)), (1, (190, 100, 20))]),
                     depth=0.06, hi_a=0.5, dark=(110, 50, 0))
    lay = Image.alpha_composite(lay, hull)
    inner = m.filter(ImageFilter.MinFilter(29))
    endo = fx.lin(PW, PH, [(0, (255, 246, 200)), (1, (250, 226, 150))])
    d = ImageDraw.Draw(endo)
    r = random.Random(2)
    for _ in range(420):
        x, y = r.uniform(280, 640), r.uniform(90, 580)
        s = r.uniform(5, 11)
        d.ellipse((x - s, y - s, x + s, y + s), outline=(225, 195, 120, 160), width=2)
    lay = Image.alpha_composite(lay, fx.shaded(inner, endo, depth=0.05, dark=(150, 110, 40), dark_a=0.4))
    gm = fx.mask(PW, PH, lambda dd, k: dd.ellipse(BX((410, 440, 510, 560), k), fill=255))
    lay = Image.alpha_composite(lay, fx.shaded(gm, fx.lin(PW, PH, [(0, (255, 250, 230)), (1, (235, 215, 170))]),
                                               depth=0.2))
    hl = layer()
    ImageDraw.Draw(hl).line(spline([(350, 170), (420, 120), (500, 112)], 8, False), fill=(255, 255, 255, 170), width=12)
    lay.alpha_composite(hl.filter(ImageFilter.GaussianBlur(3)))
    return lay


@lru_cache(None)
def droplet_sprite():
    s = 110
    m = fx.mask(s, s, lambda d, k: d.polygon(P(spline([(55, 6), (80, 50), (85, 75), (55, 104), (25, 75), (30, 50)], 8),
                                                k), fill=255))
    return fx.glow(fx.shaded(m, fx.rad(s, s, 40, 50, 70, [(0, (200, 240, 255)), (1, (40, 120, 230))]), depth=0.2,
                             hi_a=0.7), (120, 200, 255), radius=14, strength=0.6)


def flames(img, x, y, gt, a=1.0, wdt=360):
    lay = Image.new("RGBA", (wdt + 80, 220))
    d = ImageDraw.Draw(lay)
    for i in range(7):
        fx0 = 40 + i * wdt / 6
        h = 120 + 40 * math.sin(gt * 9 + i * 1.7)
        pts = spline([(fx0 - 34, 210), (fx0 - 20, 130), (fx0 + 8 * math.sin(gt * 7 + i), 210 - h), (fx0 + 20, 130),
                      (fx0 + 34, 210)], 6, False)
        d.polygon(pts, fill=(255, 110, 30, int(220 * a)))
        pts2 = spline([(fx0 - 18, 210), (fx0 - 10, 160), (fx0, 210 - h * 0.6), (fx0 + 10, 160), (fx0 + 18, 210)], 6, False)
        d.polygon(pts2, fill=(255, 230, 90, int(240 * a)))
    lay = lay.filter(ImageFilter.GaussianBlur(2))
    img.alpha_composite(lay, (int(x - lay.width / 2), int(y - 210)))


def pressure_bar(img, x, y, frac, a=1.0):
    lay = Image.new("RGBA", (W, H_))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x - 40, y - 230, x + 40, y + 230), 30, fill=(14, 10, 34, int(220 * a)),
                        outline=(255, 255, 255, int(160 * a)), width=4)
    hgt = 420 * frac
    d.rounded_rectangle((x - 26, y + 214 - hgt, x + 26, y + 214), 20, fill=(255, 120 - int(60 * frac), 60, int(255 * a)))
    for k in range(11):
        yy = y + 214 - 42 * k
        d.line((x + 44, yy, x + 60, yy), fill=(255, 255, 255, int(200 * a)), width=3)
    img.alpha_composite(lay)
    text(img, "bar", 28, x, y + 262, fill=WHITE, stroke=4, sfill=NAVY, path=FONT_XB, alpha=a)
    text(img, f"{frac * 9.3:.0f}", 40, x, y - 268, fill=YELLOW, stroke=5, sfill=NAVY, path=FONT_XB, alpha=a)


def kernel_scene(img, t, gt, steam=0.0, shake=0.0, heat=0.0, crack=0.0, gone=0.0, labels=0.0):
    lay = layer()
    if heat > 0.02:
        lay.alpha_composite(fx.rad(PW, PH, PW / 2, PH, PW * 0.6, [(0, (255, 120, 40, int(120 * heat))),
                                                                    (1, (255, 120, 40, 0))]))
    put_panel(img, lay)
    if gone >= 0.999:
        return
    ks = kernel_section()
    sx = shake * 7 * math.sin(gt * 60)
    k2 = layer()
    k2.alpha_composite(ks)
    d = ImageDraw.Draw(k2)
    if steam < 0.95:
        place(k2, droplet_sprite(), 460, 320, scale=1.2 * (1 - steam), alpha=1 - steam)
    if steam > 0.05:
        r = random.Random(4)
        for i in range(30):
            a0 = r.uniform(0, 2 * math.pi)
            rr = (20 + 140 * r.random()) * steam
            x = 460 + rr * math.cos(a0 + gt * 1.5)
            y = 320 + rr * 1.2 * math.sin(a0 + gt * 1.5)
            glow_dot(d, x, y, 7, (220, 240, 255), a=0.7 * steam)
    if crack > 0.02:
        for pts in (((460, 80), (448, 140), (470, 190), (452, 240)), ((590, 150), (560, 200), (575, 240)),
                    ((330, 150), (360, 210), (345, 250))):
            n = max(2, int(len(pts) * crack + 0.5))
            d.line(pts[:n], fill=(80, 40, 10, 255), width=5, joint="curve")
    put_panel(img, k2, dy=0) if gone <= 0.01 else put_panel(img, k2, a=1 - gone)
    if abs(sx) > 0.5:
        pass
    if labels > 0.02:
        label(img, "SCHALE", PX0 + 140, PY0 + 120, PX0 + 320, PY0 + 180, col=(255, 190, 90), a=labels)
        label(img, "STÄRKE", PX0 + 780, PY0 + 140, PX0 + 560, PY0 + 230, col=(255, 240, 180), a=labels)
        label(img, "WASSER", PX0 + 780, PY0 + 450, PX0 + 490, PY0 + 330, col=(150, 210, 255), a=labels)


def pc_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW / 2, PH * 0.6, PW * 0.6, [(0, (255, 200, 120, 80)), (1, (255, 200, 120, 0))]))
    put_panel(img, lay)
    popping(img, t, gt, CX - 40, CY - 60, n=9, a=fade(t, 0.6))
    place(img, box_sprite(), CX - 40, CY + 60)
    qmark(img, t, gt, 900, 560)
    cap(img, *CAP("popcorn", 0, t))


def pc_c1(img, t, gt, d):
    pill(img, "IM MAISKORN", 420, (255, 200, 90), fade(t, 0.2, 0.3))
    card(img)
    kernel_scene(img, t, gt, labels=fade(t, 0.5, 0.5))
    tw = W_("Wasser", fallback=2.0) - 0.1
    if t > tw:
        rr = 70 + 30 * math.sin(gt * 4)
        lay = Image.new("RGBA", (W, H_))
        ImageDraw.Draw(lay).ellipse((PX0 + 460 - rr, PY0 + 320 - rr, PX0 + 460 + rr, PY0 + 320 + rr),
                                    outline=(150, 210, 255, int(200 * fade(t, tw))), width=5)
        img.alpha_composite(lay)
    cap(img, *CAP("popcorn", 1, t))


def pc_c2(img, t, gt, d):
    pill(img, "DAMPF & DRUCK", 420, (255, 140, 80), fade(t, 0.2, 0.3))
    card(img)
    td = W_("Dampf", fallback=1.4) - 0.2
    tp = W_("Druck", fallback=2.6) - 0.2
    steam = ease_io(prog(t, td, 1.0))
    pr = ease_io(prog(t, tp, max(0.8, SEGDUR() - tp - 0.6)))
    kernel_scene(img, t, gt, steam=steam, heat=1.0, shake=pr)
    flames(img, CX - 60, PY0 + PH - 6, gt)
    pressure_bar(img, PX0 + PW - 80, CY - 10, pr, a=fade(t, tp - 0.2))
    cap(img, *CAP("popcorn", 2, t))


def pc_c3(img, t, gt, d):
    tp = W_("Plopp", fallback=2.8) - 0.05
    tc = W_("platzt", fallback=1.8) - 0.1
    pill(img, "PLOPP!" if t > tp else "≈ 180 °C", 420, YELLOW if t > tp else (255, 140, 80), 1.0)
    card(img)
    gone = ease_out(prog(t, tp, 0.12))
    kernel_scene(img, t, gt, steam=1.0, heat=1.0, crack=ease_out(prog(t, tc, 0.6)), gone=gone)
    if t < tp:
        flames(img, CX - 60, PY0 + PH - 6, gt)
    t18 = W_("hundertachtzig", fallback=0.6) - 0.3
    thermo(img, PX0 + 90, CY - 110, ease_io(prog(t, t18 - 0.4, 0.9)) * 0.7, a=fade(t, 0.2))
    text(img, "180 °C", 44, PX0 + 90, CY + 140, fill=YELLOW, stroke=6, sfill=NAVY, path=FONT_XB, alpha=fade(t, t18))
    if t > tp:
        p = back_out(prog(t, tp, 0.45))
        place(img, pop_piece(0), CX, CY, scale=2.0 * p, rot=(t - tp) * 20)
        E.burst(img, CX, CY, t, tp, color=YELLOW, n=16, rad=260)
        E.stamp(img, "PLOPP!", t, tp, cx=CX, cy=CY + 250, size=130, rot=-6, fill=YELLOW, sfill=(170, 20, 0))
    cap(img, *CAP("popcorn", 3, t))


def pc_c4(img, t, gt, d):
    pill(img, "POPCORNFLOCKE", 420, YELLOW, fade(t, 0.2, 0.3))
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW / 2, PH / 2, PW * 0.6, [(0, (255, 220, 150, 70)), (1, (255, 220, 150, 0))]))
    put_panel(img, lay)
    place(img, pop_piece(0), CX + 90, CY - 10, scale=2.0, rot=4 * math.sin(gt))
    a = fade(t, 0.6)
    lay2 = Image.new("RGBA", (W, H_))
    ImageDraw.Draw(lay2).ellipse((PX0 + 70, CY + 30, PX0 + 150, CY + 130), fill=(240, 160, 30, int(255 * a)),
                                 outline=(150, 80, 10, int(255 * a)), width=4)
    img.alpha_composite(lay2)
    text(img, "vorher", 30, PX0 + 110, CY + 170, fill=WHITE, stroke=4, sfill=NAVY, path=FONT_XB, alpha=a)
    text(img, "nachher", 30, CX + 90, CY + 230, fill=WHITE, stroke=4, sfill=NAVY, path=FONT_XB, alpha=a)
    ts = W_("schäumt", fallback=1.0) - 0.2
    label(img, "AUFGESCHÄUMTE STÄRKE", PX0 + 470, PY0 + 70, CX + 60, CY - 120, col=(255, 240, 180), a=fade(t, ts),
          size=26)
    tf = W_("fest", fallback=2.5) - 0.2
    badge(img, "check", PX0 + PW - 110, CY + 160, fade(t, tf), r=46)
    cap(img, *CAP("popcorn", 4, t))


# ================================================================== HONIG
@lru_cache(None)
def jar_sprite():
    w, h = 360, 460
    body = fx.mask(w, h, lambda d, k: d.rounded_rectangle(BX((40, 100, 320, 450), k), int(64 * k), fill=255))
    glass = fx.shaded(body, fx.lin(w, h, [(0, (255, 255, 255, 90)), (1, (230, 240, 255, 70))], 0), depth=0.06,
                      hi_a=0.4)
    hm = fx.mask(w, h, lambda d, k: d.rounded_rectangle(BX((54, 150, 306, 436), k), int(54 * k), fill=255))
    honey = fx.shaded(hm, fx.lin(w, h, [(0, (255, 200, 60)), (0.5, (240, 150, 20)), (1, (190, 90, 10))], 0), depth=0.1,
                      dark=(120, 50, 0), dark_a=0.5, hi=(255, 240, 180), hi_a=0.5)
    out = Image.alpha_composite(honey, glass)
    d = ImageDraw.Draw(out)
    d.ellipse((60, 140, 300, 172), fill=(255, 210, 90, 255))
    hx = [(180 + 70 * math.cos(a), 300 + 70 * math.sin(a)) for a in np.linspace(math.pi / 6, 2 * math.pi + math.pi / 6, 7)]
    d.polygon(hx, fill=(255, 248, 225, 255), outline=(150, 90, 20, 255))
    for x in (78, 92):
        d.rounded_rectangle((x, 180, x + 8, 400), 4, fill=(255, 255, 255, 110))
    lid = fx.mask(w, h, lambda dd, k: dd.rounded_rectangle(BX((54, 50, 306, 112), k), int(16 * k), fill=255))
    lg = fx.lin(w, h, [(0, (255, 236, 150)), (0.5, (220, 170, 50)), (1, (150, 100, 20))], 0)
    dl = ImageDraw.Draw(lg)
    for x in range(64, 300, 10):
        dl.line((x, 54, x, 108), fill=(150, 100, 20, 120), width=2)
    out = Image.alpha_composite(out, fx.shaded(lid, lg, depth=0.2, hi_a=0.5))
    return fx.drop_shadow(out, dy=16, blur=18, alpha=0.45)


def bee_icon(d, x, y, s):
    d.ellipse((x - 9 * s, y - 6 * s, x + 9 * s, y + 6 * s), fill=(255, 200, 40, 255))
    for k in (-3, 2):
        d.rectangle((x + k * s, y - 6 * s, x + (k + 2) * s, y + 6 * s), fill=(40, 30, 20, 255))


@lru_cache(None)
def bee_body():
    w, h = 220, 160
    m = fx.mask(w, h, lambda d, k: d.ellipse(BX((50, 50, 180, 130), k), fill=255))
    st = fx.lin(w, h, [(0, (255, 220, 70)), (1, (220, 150, 20))])
    d = ImageDraw.Draw(st)
    for x in (88, 122, 154):
        d.rectangle((x, 0, x + 16, h), fill=(40, 30, 25, 255))
    b = fx.shaded(m, st, depth=0.15, hi_a=0.5)
    hm = fx.mask(w, h, lambda dd, k: dd.ellipse(BX((16, 60, 70, 114), k), fill=255))
    head = fx.shaded(hm, fx.lin(w, h, [(0, (80, 70, 60)), (1, (30, 25, 20))]), depth=0.2, hi_a=0.5)
    out = Image.alpha_composite(b, head)
    d = ImageDraw.Draw(out)
    d.ellipse((26, 72, 44, 92), fill=(10, 10, 10, 255))
    d.ellipse((30, 75, 36, 81), fill=(255, 255, 255, 255))
    d.line((40, 66, 30, 36, 18, 30), fill=(30, 25, 20, 255), width=4)
    d.line((52, 64, 52, 34, 42, 24), fill=(30, 25, 20, 255), width=4)
    d.polygon([(178, 86), (204, 92), (178, 98)], fill=(40, 30, 25, 255))
    for x in (90, 120, 150):
        d.line((x, 126, x - 8, 150), fill=(40, 30, 25, 255), width=4)
    return out


def bee(img, x, y, gt, scale=1.0, a=1.0):
    body = bee_body()
    lay = layer(body.width, body.height)
    d = ImageDraw.Draw(lay)
    fl = abs(math.sin(gt * 40))
    for dx, k in ((90, 1.0), (118, 0.85)):
        hh = 46 * (0.35 + 0.65 * fl) * k
        d.ellipse((dx - 30, 56 - hh, dx + 34, 64), fill=(220, 240, 255, 150), outline=(255, 255, 255, 220), width=2)
    comb = Image.alpha_composite(lay, body)
    place(img, comb, x, y + 6 * math.sin(gt * 3), scale=scale, alpha=a)


def drip(img, x, y, gt, a=1.0):
    q = (gt * 0.6) % 1
    lay = Image.new("RGBA", (W, H_))
    d = ImageDraw.Draw(lay)
    if q < 0.6:
        ln = 30 + 120 * (q / 0.6) ** 2
        d.rounded_rectangle((x - 7, y, x + 7, y + ln), 7, fill=(240, 160, 20, int(240 * a)))
        d.ellipse((x - 12, y + ln - 10, x + 12, y + ln + 16), fill=(240, 160, 20, int(240 * a)))
    else:
        yy = y + 150 + (q - 0.6) / 0.4 * 160
        d.ellipse((x - 12, yy - 12, x + 12, yy + 16), fill=(240, 160, 20, int(240 * a)))
    img.alpha_composite(lay)


@lru_cache(None)
def dipper():
    w, h = 140, 420
    m = fx.mask(w, h, lambda d, k: (d.rounded_rectangle(BX((60, 0, 80, 300), k), int(10 * k), fill=255),
                                    [d.ellipse(BX((24, 280 + i * 22, 116, 316 + i * 22), k), fill=255) for i in range(5)]))
    wood = fx.shaded(m, fx.lin(w, h, [(0, (220, 170, 110)), (1, (150, 100, 50))], 0), depth=0.2)
    hm = fx.mask(w, h, lambda d, k: d.rounded_rectangle(BX((26, 290, 114, 400), k), int(30 * k), fill=255))
    hn = fx.apply_mask(fx.lin(w, h, [(0, (255, 200, 60, 200)), (1, (220, 130, 10, 230))], 0), hm)
    return Image.alpha_composite(wood, hn)


def calendar(img, x, y, year, a=1.0, flip=0.0):
    lay = Image.new("RGBA", (W, H_))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x - 100, y - 90, x + 100, y + 110), 22, fill=(255, 255, 255, int(240 * a)))
    d.rounded_rectangle((x - 100, y - 90, x + 100, y - 30), 22, fill=(220, 60, 60, int(255 * a)))
    d.rectangle((x - 100, y - 50, x + 100, y - 30), fill=(220, 60, 60, int(255 * a)))
    for k in (-50, 50):
        d.rounded_rectangle((x + k - 6, y - 110, x + k + 6, y - 70), 6, fill=(120, 120, 140, int(255 * a)))
    img.alpha_composite(fx.drop_shadow(lay, dy=8, blur=10, alpha=0.4 * a).crop((32, 36, 32 + W, 36 + H_)) if False else lay)
    text(img, "JAHR", 26, x, y - 60, fill=WHITE, path=FONT_XB, alpha=a)
    text(img, str(year), 58, x, y + 40 - 10 * flip, fill=(40, 34, 70), path=FONT_XB, alpha=a)


def hn_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW * 0.4, PH * 0.55, PW * 0.55, [(0, (255, 190, 80, 90)), (1, (255, 190, 80, 0))]))
    put_panel(img, lay)
    place(img, jar_sprite(), CX - 120, CY + 60)
    place(img, dipper(), CX - 60, CY - 260, rot=-20)
    drip(img, CX - 10, CY - 80, gt)
    yr = 2026 + int(max(0, t - 0.8) * 6)
    calendar(img, CX + 250, CY - 80, yr, a=fade(t, 0.5))
    qmark(img, t, gt, 900, 560)
    cap(img, *CAP("honig", 0, t))


def hn_c1(img, t, gt, d):
    pill(img, "FAST NICHTS", 420, (255, 200, 90), fade(t, 0.2, 0.3))
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW * 0.4, PH * 0.55, PW * 0.55, [(0, (255, 190, 80, 90)), (1, (255, 190, 80, 0))]))
    put_panel(img, lay)
    place(img, jar_sprite(), CX - 120, CY + 60)
    yr = 2026 + int(t * 25)
    calendar(img, CX + 250, CY - 120, yr)
    tn = W_("nie", fallback=2.5) - 0.1
    badge(img, "check", CX + 250, CY + 140, fade(t, tn), r=70)
    H.sparkles(img, gt, 6, (PX0 + 60, PY0 + 60, PX0 + 520, PY0 + PH - 60), n=12, col=(255, 230, 160))
    cap(img, *CAP("honig", 1, t))


def hn_c2(img, t, gt, d):
    pill(img, "UNTER DEM MIKROSKOP", 420, (255, 200, 90), fade(t, 0.2, 0.3), size=38)
    card(img)
    tb = W_("Bakterien", fallback=3.0) - 0.2
    shr = ease_io(prog(t, tb, 1.6))
    R = 250
    cx, cy = CX - 120, CY + 30
    lay = Image.new("RGBA", (W, H_))
    m = Image.new("L", (W, H_))
    ImageDraw.Draw(m).ellipse((cx - R, cy - R, cx + R, cy + R), fill=255)
    bgh = fx.rad(W, H_, cx - 60, cy - 60, R * 1.4, [(0, (255, 210, 90)), (1, (210, 120, 20))])
    d2 = ImageDraw.Draw(bgh)
    r = random.Random(5)
    for _ in range(26):
        x, y = cx + r.uniform(-R, R), cy + r.uniform(-R, R)
        s = r.uniform(12, 22)
        a0 = r.uniform(0, 1.5)
        pts = [(x + s * math.cos(a0 + k * math.pi / 2), y + s * math.sin(a0 + k * math.pi / 2)) for k in range(4)]
        d2.polygon(pts, fill=(255, 245, 210, 220), outline=(220, 170, 80, 255))
    for i in range(5):
        x, y = cx + r.uniform(-160, 160), cy + r.uniform(-160, 160)
        sc = 1 - 0.55 * shr
        ln, wd = 70 * sc, 30 * sc
        an = r.uniform(0, math.pi)
        dx, dy = math.cos(an) * ln / 2, math.sin(an) * ln / 2
        d2.line((x - dx, y - dy, x + dx, y + dy), fill=(60, 140, 60, 255), width=int(wd) + 6)
        d2.line((x - dx, y - dy, x + dx, y + dy), fill=(110, 200, 100, 255), width=int(wd))
        for k in range(3):
            q = ((t - tb) * 0.8 + k / 3) % 1 if t > tb else 0
            if t > tb:
                ex, ey = x + math.cos(k * 2.1 + i) * (30 + 90 * q), y + math.sin(k * 2.1 + i) * (30 + 90 * q)
                glow_dot(d2, ex, ey, 6, (120, 190, 255), a=1 - q)
    lay.paste(bgh, (0, 0), m)
    rd = ImageDraw.Draw(lay)
    rd.ellipse((cx - R - 10, cy - R - 10, cx + R + 10, cy + R + 10), outline=(200, 205, 220, 255), width=16)
    rd.ellipse((cx - R - 10, cy - R - 10, cx + R + 10, cy + R + 10), outline=(255, 255, 255, 140), width=4)
    img.alpha_composite(lay)
    # composition bars
    tw = W_("Wasser", fallback=0.8) - 0.2
    tz = W_("Zucker", fallback=2.0) - 0.2
    for k, (lab, v, col, t0) in enumerate((("WASSER", 0.17, (120, 190, 255), tw), ("ZUCKER", 0.80, (255, 240, 200), tz))):
        a = fade(t, t0)
        x, y = PX0 + PW - 120, CY - 160 + k * 270
        hgt = 200 * v * ease_io(prog(t, t0, 0.8))
        bl = Image.new("RGBA", (W, H_))
        bd = ImageDraw.Draw(bl)
        bd.rounded_rectangle((x - 36, y - 100, x + 36, y + 100), 16, fill=(14, 10, 34, int(200 * a)))
        bd.rounded_rectangle((x - 28, y + 92 - hgt, x + 28, y + 92), 12, fill=col + (int(255 * a),))
        img.alpha_composite(bl)
        text(img, f"≈ {int(v * 100)} %", 32, x, y - 128, fill=WHITE, stroke=4, sfill=NAVY, path=FONT_XB, alpha=a)
        text(img, lab, 26, x, y + 128, fill=col, stroke=4, sfill=NAVY, path=FONT_XB, alpha=a)
    label(img, "BAKTERIE", cx - 150, cy - R - 20, cx - 40, cy - 80, col=(140, 230, 130), a=fade(t, tb))
    cap(img, *CAP("honig", 2, t))


def hn_c3(img, t, gt, d):
    pill(img, "SAUER + ENZYM", 420, (255, 200, 90), fade(t, 0.2, 0.3))
    card(img)
    lay = layer()
    put_panel(img, lay)
    ts = W_("sauer", fallback=1.0) - 0.2
    a = fade(t, ts)
    x0, x1, y = PX0 + 80, PX0 + PW - 80, PY0 + 150
    strip = fx.lin(int(x1 - x0), 60, [(0, (230, 40, 40)), (0.21, (255, 140, 30)), (0.36, (250, 220, 40)),
                                       (0.5, (90, 200, 80)), (0.7, (40, 120, 230)), (1, (130, 50, 180))], 0)
    m = fx.mask(int(x1 - x0), 60, lambda dd, k: dd.rounded_rectangle(BX((0, 0, x1 - x0 - 1, 59), k), int(30 * k),
                                                                     fill=255))
    place(img, fx.apply_mask(strip, m), (x0 + x1) / 2, y, alpha=a)
    for v in range(0, 15, 2):
        text(img, str(v), 26, x0 + (x1 - x0) * v / 14, y + 56, fill=WHITE, stroke=3, sfill=NAVY, path=FONT_XB, alpha=a)
    mx = x0 + (x1 - x0) * 3.9 / 14
    lay2 = Image.new("RGBA", (W, H_))
    ImageDraw.Draw(lay2).polygon([(mx - 18, y - 60), (mx + 18, y - 60), (mx, y - 34)], fill=YELLOW + (int(255 * a),))
    img.alpha_composite(lay2)
    text(img, "HONIG ≈ pH 4", 34, mx + 30, y - 88, fill=YELLOW, stroke=5, sfill=NAVY, path=FONT_XB, alpha=a)
    text(img, "SAUER", 26, x0 + 40, y + 100, fill=(255, 150, 140), stroke=4, sfill=NAVY, path=FONT_XB, alpha=a)
    te = W_("Enzym", fallback=2.6) - 0.3
    pb = fade(t, te)
    bx = PX0 + 260 + 40 * math.sin(gt * 1.2)
    bee(img, bx, CY + 110, gt, scale=1.25, a=pb)
    label(img, "ENZYM", PX0 + 160, PY0 + PH - 70, bx - 40, CY + 130, col=(255, 220, 120), a=pb)
    tw = W_("Wasserstoffperoxid", fallback=4.5) - 0.4
    if t > tw:
        r = random.Random(3)
        for i in range(5):
            q = ((t - tw) * 0.5 + i / 5) % 1
            x = PX0 + 560 + r.uniform(-80, 180)
            yy = CY + 220 - 300 * q
            lb = Image.new("RGBA", (W, H_))
            ImageDraw.Draw(lb).ellipse((x - 46, yy - 30, x + 46, yy + 30), fill=(230, 245, 255, int(150 * (1 - q))),
                                       outline=(255, 255, 255, int(230 * (1 - q))), width=3)
            img.alpha_composite(lb)
            text(img, "H₂O₂", 26, x, yy, fill=(40, 60, 120), path=FONT_XB, alpha=1 - q)
    cap(img, *CAP("honig", 3, t))


@lru_cache(None)
def desert_base():
    sky = fx.lin(PW, PH, [(0, (90, 60, 140)), (0.45, (240, 130, 110)), (0.7, (255, 200, 120)), (1, (255, 220, 150))])
    sky.alpha_composite(fx.rad(PW, PH, PW * 0.72, PH * 0.5, 180, [(0, (255, 250, 220, 255)), (0.25, (255, 230, 160, 200)),
                                                                  (1, (255, 200, 120, 0))]))
    for (bx, by, s, seed) in ((300, 470, 300, 1), (560, 490, 200, 2)):
        lit = [(bx, by - s), (bx - s * 1.1, by), (bx + s * 0.15, by)]
        dark = [(bx, by - s), (bx + s * 0.15, by), (bx + s * 0.9, by)]
        d = ImageDraw.Draw(sky)
        d.polygon(lit, fill=(240, 190, 120, 255))
        d.polygon(dark, fill=(180, 120, 70, 255))
        for k in range(1, 9):
            yy = by - s + s * k / 9
            f = k / 9
            d.line((bx - s * 1.1 * f, yy, bx + s * 0.9 * f, yy), fill=(200, 140, 80, 110), width=2)
    d = ImageDraw.Draw(sky)
    d.polygon(spline([(-20, 520), (200, 480), (420, 510), (640, 470), (940, 500), (940, 700), (-20, 700)], 6),
              fill=(240, 190, 120, 255))
    d.polygon(spline([(-20, 590), (300, 560), (600, 590), (940, 560), (940, 700), (-20, 700)], 6), fill=(225, 165, 95, 255))
    return sky


@lru_cache(None)
def amphora():
    w, h = 240, 320
    pts = [(120, 20), (160, 30), (150, 70), (200, 130), (210, 200), (180, 270), (140, 305), (100, 305), (60, 270),
           (30, 200), (40, 130), (90, 70), (80, 30)]
    m = poly_mask(w, h, pts, 8)
    pot = fx.shaded(m, fx.lin(w, h, [(0, (220, 130, 80)), (0.6, (180, 90, 50)), (1, (120, 55, 30))], 0), depth=0.1,
                    hi_a=0.45)
    d = ImageDraw.Draw(pot)
    for y in (130, 150, 230):
        d.line((40, y, 200, y), fill=(60, 30, 20, 200), width=4)
    for x in range(55, 190, 24):
        d.polygon([(x, 165), (x + 10, 185), (x + 20, 165)], fill=(60, 30, 20, 200))
    pot = clip(pot, m)
    return fx.drop_shadow(pot, dy=12, blur=14, alpha=0.45)


def hn_c4(img, t, gt, d):
    pill(img, "ALTES ÄGYPTEN", 420, (255, 200, 90), fade(t, 0.2, 0.3))
    card(img)
    lay = desert_base().copy()
    put_panel(img, lay)
    place(img, amphora(), CX - 200, CY + 130, alpha=fade(t, 0.5))
    tt = W_("Tausende", fallback=3.5) - 0.2
    if t > tt:
        E.stamp(img, "TAUSENDE JAHRE", t, tt, cx=CX + 70, cy=CY + 220, size=72, rot=-5, fill=YELLOW, sfill=(170, 20, 0))
    tf = W_("Honig", fallback=2.5) - 0.2
    badge(img, "check", CX - 120, CY + 30, fade(t, tf), r=40)
    H.sparkles(img, gt, 7, (PX0 + 60, PY0 + 40, PX0 + PW - 60, PY0 + 300), n=10, col=(255, 240, 200))
    cap(img, *CAP("honig", 4, t))


# ================================================================== EIS / SEE
@lru_cache(None)
def pine(h=200):
    w = int(h * 0.7)
    lay = layer(w, h)
    d = ImageDraw.Draw(lay)
    d.rectangle((w / 2 - 8, h * 0.8, w / 2 + 8, h), fill=(80, 50, 30, 255))
    for k, (y0, wd) in enumerate(((0.0, 0.25), (0.22, 0.38), (0.45, 0.5))):
        top, bot = h * y0, h * (y0 + 0.4)
        d.polygon([(w / 2, top), (w / 2 - w * wd, bot), (w / 2 + w * wd, bot)], fill=(30, 80, 60, 255))
        d.polygon([(w / 2, top), (w / 2 - w * wd * 0.45, top + (bot - top) * 0.45), (w / 2 + w * wd * 0.45,
                                                                                     top + (bot - top) * 0.45)],
                  fill=(240, 248, 255, 255))
    return lay


@lru_cache(None)
def winter_base():
    sky = fx.lin(PW, PH, [(0, (120, 160, 220)), (0.6, (200, 220, 245)), (1, (235, 242, 252))])
    d = ImageDraw.Draw(sky)
    d.polygon(spline([(-20, 330), (180, 260), (380, 310), (600, 250), (800, 300), (940, 280), (940, 700), (-20, 700)], 6),
              fill=(225, 235, 250, 255))
    for x, s in ((90, 200), (160, 160), (760, 220), (840, 170), (680, 150)):
        place(sky, pine(s), x, 330 - s / 2 + 20)
    lake = fx.mask(PW, PH, lambda dd, k: dd.ellipse(BX((80, 380, 840, 620), k), fill=255))
    ice = fx.shaded(lake, fx.lin(PW, PH, [(0, (200, 235, 250)), (1, (130, 190, 230))]), depth=0.06, hi_a=0.6)
    di = ImageDraw.Draw(ice)
    r = random.Random(3)
    for _ in range(9):
        x, y = r.uniform(200, 720), r.uniform(420, 580)
        pts = [(x, y)]
        for _ in range(4):
            pts.append((pts[-1][0] + r.uniform(-40, 40), pts[-1][1] + r.uniform(-14, 14)))
        di.line(pts, fill=(255, 255, 255, 200), width=2)
    di.ellipse((260, 420, 520, 450), fill=(255, 255, 255, 120))
    ice = clip(ice, lake)
    sky.alpha_composite(ice)
    return sky


def snow(img, gt, box, n=60, a=1.0):
    lay = Image.new("RGBA", (W, H_))
    d = ImageDraw.Draw(lay)
    r = random.Random(8)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, yy, sp, s = r.uniform(x0, x1), r.uniform(y0, y1), r.uniform(30, 70), r.uniform(2, 5)
        y = y0 + (yy - y0 + gt * sp) % (y1 - y0)
        x = x + 12 * math.sin(gt + yy)
        d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 255, 255, int(220 * a)))
    img.alpha_composite(lay)


def es_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    put_panel(img, winter_base())
    snow(img, gt, (PX0 + 20, PY0 + 20, PX0 + PW - 20, PY0 + PH - 20))
    qmark(img, t, gt, 900, 560)
    cap(img, *CAP("eis", 0, t))


@lru_cache(None)
def beaker():
    w, h = 240, 380
    m = fx.mask(w, h, lambda d, k: d.rounded_rectangle(BX((20, 20, 220, 370), k), int(26 * k), fill=255))
    g = fx.shaded(m, fx.lin(w, h, [(0, (255, 255, 255, 60)), (1, (220, 235, 255, 40))], 0), depth=0.08, hi_a=0.5,
                  outline=(255, 255, 255), ow=4)
    d = ImageDraw.Draw(g)
    for k in range(8):
        y = 340 - k * 40
        d.line((180, y, 210, y), fill=(255, 255, 255, 200), width=3)
    d.rounded_rectangle((40, 40, 54, 340), 7, fill=(255, 255, 255, 90))
    return g


@lru_cache(None)
def ice_cube(s=80):
    m = fx.mask(s, s, lambda d, k: d.rounded_rectangle(BX((4, 4, s - 4, s - 4), k), int(12 * k), fill=255))
    c = fx.shaded(m, fx.lin(s, s, [(0, (250, 255, 255)), (1, (170, 215, 245))]), depth=0.2, hi_a=0.7,
                  dark=(60, 110, 170), dark_a=0.4)
    d = ImageDraw.Draw(c)
    d.line((14, 18, 30, 14), fill=(255, 255, 255, 230), width=4)
    return c


def es_c1(img, t, gt, d):
    pill(img, "WASSER → EIS", 420, (170, 220, 255), fade(t, 0.2, 0.3))
    card(img)
    put_panel(img, layer())
    base = CY + 230
    bx1, bx2 = CX - 210, CX + 210
    tg = W_("Gefrieren", fallback=1.2) - 0.2
    lay = Image.new("RGBA", (W, H_))
    dl = ImageDraw.Draw(lay)
    lvl = 230
    dl.rounded_rectangle((bx1 - 96, base - lvl, bx1 + 96, base), 20, fill=(70, 150, 230, 220))
    dl.rectangle((bx1 - 96, base - lvl, bx1 + 96, base - lvl + 10), fill=(160, 210, 255, 255))
    img.alpha_composite(lay)
    place(img, beaker(), bx1, base - 165)
    text(img, "WASSER", 34, bx1, base + 50, fill=(150, 210, 255), stroke=5, sfill=NAVY, path=FONT_XB)
    pi = ease_io(prog(t, tg, 1.2))
    ice_l = lvl * (1 + 0.09 * pi * 2.2)
    for row in range(int(ice_l // 78) + 1):
        for col in range(2):
            y = base - 40 - row * 78
            if y < base - ice_l:
                continue
            place(img, ice_cube(), bx2 - 44 + col * 88, y, alpha=fade(t, tg + row * 0.1, 0.3))
    place(img, beaker(), bx2, base - 165)
    text(img, "EIS", 34, bx2, base + 50, fill=(220, 240, 255), stroke=5, sfill=NAVY, path=FONT_XB)
    lay2 = Image.new("RGBA", (W, H_))
    ImageDraw.Draw(lay2).line((bx1 - 120, base - lvl, bx2 + 120, base - lvl), fill=(255, 255, 255, 160), width=3)
    img.alpha_composite(lay2)
    tn = W_("neun", fallback=3.5) - 0.2
    if t > tn:
        E.stamp(img, "+ 9 %", t, tn, cx=CX, cy=CY - 220, size=120, rot=-5, fill=YELLOW, sfill=(170, 20, 0))
    cap(img, *CAP("eis", 1, t))


@lru_cache(None)
def molecule():
    s = 90
    lay = layer(s, s)
    o = sh_ellipse(s, s, (23, 20, 67, 64), [(0, (255, 110, 100)), (1, (190, 30, 40))], depth=0.25, hi_a=0.6)
    out = lay
    for ang in (-52, 52):
        a = math.radians(90 + ang)
        x, y = 45 + 30 * math.cos(a), 42 + 30 * math.sin(a)
        hsp = sh_ellipse(s, s, (x - 13, y - 13, x + 13, y + 13), [(0, (255, 255, 255)), (1, (200, 205, 220))],
                         depth=0.3, hi_a=0.6)
        out = Image.alpha_composite(out, hsp)
    return Image.alpha_composite(out, o)


def hex_lattice(cx, cy, w, h, sp=78):
    pts = []
    rows = int(h // (sp * 0.866)) + 1
    for r_ in range(rows):
        y = cy - h / 2 + r_ * sp * 0.866
        off = (sp / 2) if r_ % 2 else 0
        for c in range(int(w // sp) + 1):
            x = cx - w / 2 + off + c * sp
            if (c + (r_ % 2)) % 3 != 2:      # honeycomb: drop every third site -> open hexagons
                pts.append((x, y))
    return pts


def es_c2(img, t, gt, d):
    pill(img, "SECHSECK-GITTER", 420, (170, 220, 255), fade(t, 0.2, 0.3))
    card(img)
    put_panel(img, layer())
    th = W_("Sechseck-Gitter", fallback=1.6) - 0.3
    k = ease_io(prog(t, th, 1.2))
    # left: liquid
    lx, rx, yc = CX - 230, CX + 230, CY - 10
    lay = Image.new("RGBA", (W, H_))
    dl = ImageDraw.Draw(lay)
    dl.line((CX, PY0 + 40, CX, PY0 + PH - 40), fill=(255, 255, 255, 90), width=3)
    img.alpha_composite(lay)
    r = random.Random(2)
    for i in range(20):
        x = lx + r.uniform(-170, 170) + 12 * math.sin(gt * 3 + i)
        y = yc + r.uniform(-230, 230) + 12 * math.cos(gt * 2.7 + i)
        place(img, molecule(), x, y, rot=(gt * 60 + i * 40) % 360, scale=0.75)
    text(img, "WASSER", 36, lx, PY0 + PH - 40, fill=(150, 210, 255), stroke=5, sfill=NAVY, path=FONT_XB)
    # right: lattice forming
    latt = hex_lattice(rx, yc, 360, 460)
    r2 = random.Random(5)
    lay = Image.new("RGBA", (W, H_))
    dl = ImageDraw.Draw(lay)
    pos = []
    for (x, y) in latt:
        sx, sy = rx + r2.uniform(-170, 170), yc + r2.uniform(-230, 230)
        pos.append((sx + (x - sx) * k + 10 * (1 - k) * math.sin(gt * 3 + x), sy + (y - sy) * k))
    if k > 0.6:
        for i, (x, y) in enumerate(pos):
            for j in range(i + 1, len(pos)):
                x2, y2 = pos[j]
                if abs(math.hypot(x - x2, y - y2) - 78) < 8:
                    dl.line((x, y, x2, y2), fill=(200, 230, 255, int(200 * (k - 0.6) / 0.4)), width=3)
    img.alpha_composite(lay)
    for (x, y) in pos:
        place(img, molecule(), x, y, rot=0 if k > 0.95 else (gt * 60 + x) % 360 * (1 - k), scale=0.6)
    text(img, "EIS", 36, rx, PY0 + PH - 40, fill=(220, 240, 255), stroke=5, sfill=NAVY, path=FONT_XB)
    ts = W_("schwimmt", fallback=5.5) - 0.3
    if t > ts:
        a = fade(t, ts)
        bx, by = CX, CY + 215
        lay3 = Image.new("RGBA", (W, H_))
        d3 = ImageDraw.Draw(lay3)
        d3.rounded_rectangle((bx - 130, by - 120, bx + 130, by + 140), 30, fill=(14, 10, 34, int(220 * a)),
                             outline=(255, 255, 255, int(160 * a)), width=4)
        d3.rectangle((bx - 110, by - 10, bx + 110, by + 120), fill=(70, 150, 230, int(220 * a)))
        img.alpha_composite(lay3)
        place(img, ice_cube(100), bx, by - 22 + 5 * math.sin(gt * 2), alpha=a)
        badge(img, "check", bx + 110, by - 110, a, r=34)
    cap(img, *CAP("eis", 2, t))


@lru_cache(None)
def lake_section(snow_top=False):
    lay = layer()
    lay.alpha_composite(fx.lin(PW, PH, [(0, (170, 200, 240)), (0.15, (200, 225, 250)), (0.16, (0, 0, 0, 0)),
                                        (1, (0, 0, 0, 0))]))
    wm = Image.new("L", (PW, PH))
    ImageDraw.Draw(wm).rectangle((0, 150, PW, PH), fill=255)
    water = fx.lin(PW, PH, [(0, (120, 190, 240)), (0.4, (60, 130, 210)), (1, (20, 50, 120))])
    lay = Image.alpha_composite(lay, clip(water, wm))
    rays = layer()
    dr = ImageDraw.Draw(rays)
    for x in (150, 380, 620, 820):
        dr.polygon([(x - 30, 150), (x + 30, 150), (x + 120, PH), (x + 20, PH)], fill=(255, 255, 255, 18))
    lay.alpha_composite(rays.filter(ImageFilter.GaussianBlur(10)))
    im_ = fx.mask(PW, PH, lambda d, k: d.rectangle(BX((0, 80, PW, 158), k), fill=255))
    ice = fx.shaded(im_, fx.lin(PW, PH, [(0, (240, 250, 255)), (1, (170, 215, 240))]), depth=0.3, hi_a=0.6)
    di = ImageDraw.Draw(ice)
    r = random.Random(4)
    for _ in range(40):
        x, y = r.uniform(0, PW), r.uniform(92, 150)
        s = r.uniform(2, 5)
        di.ellipse((x - s, y - s, x + s, y + s), outline=(255, 255, 255, 200), width=1)
    lay.alpha_composite(clip(ice, im_))
    if snow_top:
        sm = fx.mask(PW, PH, lambda d, k: d.polygon(P(spline([(-10, 82), (200, 54), (420, 70), (650, 50), (930, 72),
                                                              (930, 86), (-10, 86)], 6), k), fill=255))
        lay.alpha_composite(fx.shaded(sm, fx.lin(PW, PH, [(0, (255, 255, 255)), (1, (220, 230, 245))]), depth=0.3))
    bm = fx.mask(PW, PH, lambda d, k: d.polygon(P(spline([(-10, 600), (240, 584), (500, 606), (760, 588), (930, 600),
                                                          (930, PH + 10), (-10, PH + 10)], 6), k), fill=255))
    lay.alpha_composite(fx.shaded(bm, fx.lin(PW, PH, [(0, (120, 100, 70)), (1, (70, 55, 40))]), depth=0.2))
    d = ImageDraw.Draw(lay)
    for x in (120, 300, 560, 760):
        for j in range(3):
            pts = [(x + j * 14 + 10 * math.sin(i * 0.8 + j), 600 - i * 18) for i in range(7)]
            d.line(pts, fill=(60, 140, 80, 220), width=6, joint="curve")
    return lay


@lru_cache(None)
def fish_sprite(col=(170, 200, 190)):
    w, h = 220, 120
    body = [(30, 60), (70, 30), (140, 28), (180, 50), (186, 62), (180, 74), (140, 92), (70, 90)]
    m = poly_mask(w, h, body, 8)
    tail = fx.mask(w, h, lambda d, k: d.polygon(P([(36, 60), (4, 26), (14, 60), (4, 94)], k), fill=255))
    c0 = tuple(min(255, v + 50) for v in col)
    c1 = tuple(int(v * 0.5) for v in col)
    out = fx.shaded(tail, fx.lin(w, h, [(0, c0), (1, c1)]), depth=0.2)
    out = Image.alpha_composite(out, fx.shaded(m, fx.lin(w, h, [(0, c0), (0.5, col), (1, c1)]), depth=0.15, hi_a=0.6))
    d = ImageDraw.Draw(out)
    d.ellipse((152, 46, 166, 60), fill=(20, 20, 30, 255))
    d.ellipse((155, 48, 159, 52), fill=(255, 255, 255, 255))
    d.polygon([(100, 30), (130, 8), (138, 30)], fill=c1 + (255,))
    d.arc((120, 40, 150, 80), 100, 260, fill=c1 + (200,), width=3)
    return out


def es_c3(img, t, gt, d):
    pill(img, "IM SEE", 420, (170, 220, 255), fade(t, 0.2, 0.3))
    card(img)
    put_panel(img, lake_section())
    tg = W_("Grund", fallback=0.4) - 0.2
    t4 = W_("vier", fallback=1.4) - 0.2
    label(img, "EIS · 0 °C", PX0 + 190, PY0 + 40, PX0 + 260, PY0 + 120, col=(220, 240, 255), a=fade(t, 0.4))
    label(img, "≈ 4 °C", PX0 + 690, PY0 + 520, PX0 + 600, PY0 + 560, col=YELLOW, a=fade(t, t4), size=34)
    # temperature gauge on the side
    lay = Image.new("RGBA", (W, H_))
    dd = ImageDraw.Draw(lay)
    a = fade(t, tg)
    gx = PX0 + PW - 60
    for i in range(40):
        f = i / 40
        c = (int(200 - 140 * f), int(230 - 120 * f), int(255 - 60 * f))
        dd.rectangle((gx - 16, PY0 + 160 + f * 440, gx + 16, PY0 + 171 + f * 440), fill=c + (int(230 * a),))
    img.alpha_composite(lay)
    text(img, "0°", 28, gx, PY0 + 140, fill=WHITE, stroke=4, sfill=NAVY, path=FONT_XB, alpha=a)
    text(img, "4°", 28, gx, PY0 + 630, fill=YELLOW, stroke=4, sfill=NAVY, path=FONT_XB, alpha=a)
    ts = W_("schwersten", fallback=4.5) - 0.3
    if t > ts:
        for k in range(3):
            q = ((t - ts) * 0.7 + k / 3) % 1
            text(img, "↓", 50, PX0 + 420 + k * 60, PY0 + 260 + 220 * q, fill=YELLOW, stroke=5, sfill=NAVY,
                 alpha=fade(t, ts) * (1 - q))
    cap(img, *CAP("eis", 3, t))


def es_c4(img, t, gt, d):
    pill(img, "EIS ALS DECKE", 420, (170, 220, 255), fade(t, 0.2, 0.3))
    card(img)
    lay = lake_section(True).copy()
    tf = W_("Fische", fallback=2.5) - 0.3
    fa = fade(t, tf)
    for i, (y, sp, sc, col) in enumerate(((330, 50, 1.0, (170, 200, 190)), (440, 34, 0.8, (220, 170, 120)),
                                          (520, 60, 0.7, (170, 200, 190)))):
        x = (gt * sp + i * 300) % (PW + 300) - 150
        fs = fish_sprite(col)
        if i == 1:
            fs = ImageOps.mirror(fs)
            x = PW - x
        place(lay, fs, x, y + 10 * math.sin(gt * 2 + i), scale=sc, alpha=fa)
    dd = ImageDraw.Draw(lay)
    for i in range(8):
        q = (gt * 0.3 + i / 8) % 1
        glow_dot(dd, 200 + i * 80, 600 - 440 * q, 4, (220, 240, 255), a=0.6 * (1 - q))
    put_panel(img, lay)
    td = W_("Decke", fallback=1.4) - 0.2
    label(img, "DECKE", PX0 + 760, PY0 + 40, PX0 + 680, PY0 + 110, col=(220, 240, 255), a=fade(t, td), size=32)
    snow(img, gt, (PX0 + 20, PY0 + 10, PX0 + PW - 20, PY0 + 90), n=20)
    badge(img, "check", PX0 + 120, PY0 + PH - 80, fade(t, tf + 0.8), r=40)
    cap(img, *CAP("eis", 4, t))


# ================================================================== registration
SCRIPTS = {
    "blitz": ["Rate mal, was passiert, wenn ein Blitz einschlägt.",
              "Ein Blitz heizt die Luft in einem Bruchteil einer Sekunde auf etwa dreißigtausend Grad auf.",
              "Das ist rund fünfmal heißer als die Oberfläche der Sonne.",
              "Die Luft dehnt sich dabei explosionsartig aus. Diese Druckwelle hörst du als Donner.",
              "Und der Trick: Zähl die Sekunden zwischen Blitz und Donner und teile durch drei. "
              "So viele Kilometer ist das Gewitter entfernt."],
    "popcorn": ["Rate mal, was passiert, wenn du Popcorn erhitzt.",
                "In jedem Maiskorn steckt ein winziger Tropfen Wasser, eingeschlossen in einer harten Schale.",
                "Beim Erhitzen wird das Wasser zu Dampf. Der Druck im Korn steigt immer weiter.",
                "Bei etwa hundertachtzig Grad platzt die Schale. Plopp.",
                "Die Stärke im Inneren schäumt auf und wird sofort fest. Fertig ist die Popcornflocke."],
    "honig": ["Rate mal, was passiert, wenn Honig jahrelang im Schrank steht.",
              "Fast nichts. Richtig gelagert wird Honig praktisch nie schlecht.",
              "Er enthält sehr wenig Wasser und sehr viel Zucker. Bakterien wird dadurch das Wasser entzogen.",
              "Außerdem ist Honig sauer, und ein Enzym der Bienen bildet kleine Mengen Wasserstoffperoxid.",
              "Forscher fanden in alten ägyptischen Gräbern Honig, der Tausende Jahre alt war."],
    "eis": ["Rate mal, was passiert, wenn ein See im Winter zufriert.",
            "Wasser wird beim Gefrieren nicht kleiner, sondern dehnt sich um etwa neun Prozent aus.",
            "Die Moleküle ordnen sich zu einem lockeren Sechseck-Gitter. Deshalb ist Eis leichter als Wasser und "
            "schwimmt oben.",
            "Am Grund bleibt das Wasser etwa vier Grad warm, denn bei vier Grad ist Wasser am schwersten.",
            "Die Eisschicht wirkt wie eine Decke. Darunter überleben Fische den ganzen Winter."],
}
HL = {
    "blitz": [("RATE", "MAL,", "BLITZ"), ("DREISSIGTAUSEND", "DREIßIGTAUSEND"), ("FÜNFMAL",), ("DONNER.",),
              ("DREI.", "KILOMETER")],
    "popcorn": [("RATE", "MAL,", "POPCORN"), ("WASSER,",), ("DAMPF.", "DRUCK"), ("HUNDERTACHTZIG", "PLOPP."),
                ("POPCORNFLOCKE.",)],
    "honig": [("RATE", "MAL,", "HONIG"), ("NIE",), ("ZUCKER.", "WASSER"), ("SAUER,", "WASSERSTOFFPEROXID."),
              ("TAUSENDE",)],
    "eis": [("RATE", "MAL,", "ZUFRIERT."), ("NEUN",), ("SECHSECK-GITTER.", "SCHWIMMT"), ("VIER",), ("FISCHE",)],
}


def CAP(name, i, t):
    return SCRIPTS[name][i], t, HL[name][i]


def SEGDUR():
    return M_SEG().get("dur", 5.0)


def M_SEG():
    return H.M.SEG


NEW = {
    "blitz": dict(bg=((10, 12, 40), (60, 50, 120), (60, 60, 120)), out="blitz_hq",
                  scenes=[bz_hook, bz_c1, bz_c2, bz_c3, bz_c4, H.outro]),
    "popcorn": dict(bg=((60, 16, 20), (190, 80, 40), (140, 70, 40)), out="popcorn_hq",
                    scenes=[pc_hook, pc_c1, pc_c2, pc_c3, pc_c4, H.outro]),
    "honig": dict(bg=((50, 26, 6), (200, 120, 30), (150, 90, 30)), out="honig_hq",
                  scenes=[hn_hook, hn_c1, hn_c2, hn_c3, hn_c4, H.outro]),
    "eis": dict(bg=((8, 30, 60), (60, 140, 200), (60, 120, 180)), out="see_zufrieren_hq",
                scenes=[es_hook, es_c1, es_c2, es_c3, es_c4, H.outro]),
}
KEYS = {"bz_c3": ("Donner", "thump"), "bz_c2": ("fünfmal", "pop"), "bz_c4": ("drei", "ding"),
        "pc_c3": ("Plopp", "thump"), "pc_c4": ("fest", "ding"), "pc_c2": ("Dampf", "pop"),
        "hn_c1": ("nie", "ding"), "hn_c4": ("Tausende", "thump"), "hn_c3": ("Enzym", "pop"),
        "es_c1": ("neun", "thump"), "es_c2": ("schwimmt", "ding"), "es_c4": ("Fische", "pop")}

N.NEW.update(NEW)
N.SCRIPTS.update(SCRIPTS)
N.KEYS.update(KEYS)
_orig_events = N.events


def events():
    ev = _orig_events()
    for s in H.CUR["segs"]:
        st, nm = s["start"], s["fn"].__name__
        if nm == "bz_hook":
            ev += [(st + x, "thump", 0.12) for x in (1.0, 2.6)]
        if nm == "bz_c3":
            ev += [(st + x, "thump", 0.08) for x in np.arange(0.2, s["dur"], 2.2)]
        if nm == "bz_c4":
            t0 = H.seg_word(s, "Sekunden", 1.0) - 0.2
            ev += [(st + t0 + k * 0.45, "tick", 0.09) for k in range(6)]
        if nm == "pc_hook":
            ev += [(st + x, "pop", 0.08) for x in (0.9, 1.6, 2.3, 3.0)]
    return ev


N.events = events

if __name__ == "__main__":
    names = [a for a in ARGS if not a.startswith("--")] or list(NEW)
    for nm in names:
        if "--stills" in ARGS:
            N.stills(nm)
        else:
            N.make(nm, uhd="--hd" not in ARGS)

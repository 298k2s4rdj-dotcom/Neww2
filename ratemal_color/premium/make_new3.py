#!/usr/bin/env python3
"""Premium 'Rate mal' Shorts, batch 3: Schwarzes Loch, Sonne verschwindet, Baertierchen, Tunnel durch die Erde.

Usage: python3 make_new3.py [--stills] [--hd] [name ...]   names: loch, sonne, baer, tunnel
"""
import math
import os
import random
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ARGS = sys.argv[1:]
import make_new2 as M2  # noqa: E402  (also registers batch 2; harmless)
import make_new as N  # noqa: E402
import make_hq as H  # noqa: E402
import fx  # noqa: E402
from fx import E as BX, P, place  # noqa: E402

E = H.E
text, ease_out, ease_io, back_out, prog = H.text, H.ease_out, H.ease_io, H.back_out, H.prog
FONT_XB = H.FONT_XB
W, H_ = H.W, H.H
YELLOW, WHITE, GREEN, NAVY = H.YELLOW, H.WHITE, H.GREEN, H.NAVY
CX, CY, PW, PH, PX0, PY0 = H.CX, H.CY, H.PW, H.PH, H.PX0, H.PY0
W_, card, put_panel, layer, pill, qmark, cap, label, badge = H.W_, H.card, H.put_panel, H.layer, H.pill, H.qmark, \
    H.cap, H.label, H.badge
spline, poly_mask, clip, noise_tex, glow_dot = H.spline, H.poly_mask, H.clip, H.noise_tex, H.glow_dot
fade, pulse = M2.fade, N.pulse


def CAP(name, i, t):
    return SCRIPTS[name][i], t, HL[name][i]


# ------------------------------------------------------------------ shared space pieces
@lru_cache(None)
def space_base(seed=1, tint=(70, 40, 120)):
    sp = fx.lin(PW, PH, [(0, (6, 5, 20)), (1, (16, 10, 40))])
    neb = Image.new("RGBA", (PW, PH))
    d = ImageDraw.Draw(neb)
    r = random.Random(seed)
    for _ in range(9):
        x, y, s = r.uniform(0, PW), r.uniform(0, PH), r.uniform(80, 220)
        c = r.choice([tint, (40, 80, 150), (140, 50, 110)])
        d.ellipse((x - s, y - s * 0.6, x + s, y + s * 0.6), fill=c + (60,))
    sp.alpha_composite(neb.filter(ImageFilter.GaussianBlur(50)))
    d = ImageDraw.Draw(sp)
    for _ in range(260):
        x, y, s = r.uniform(0, PW), r.uniform(0, PH), r.uniform(0.6, 2.2)
        v = int(r.uniform(140, 255))
        d.ellipse((x - s, y - s, x + s, y + s), fill=(v, v, 255, 255))
    for _ in range(6):
        x, y = r.uniform(0, PW), r.uniform(0, PH)
        d.line((x - 12, y, x + 12, y), fill=(255, 255, 255, 180), width=2)
        d.line((x, y - 12, x, y + 12), fill=(255, 255, 255, 180), width=2)
    return sp


@lru_cache(None)
def astronaut():
    w, h = 170, 260
    parts = []
    pack = fx.mask(w, h, lambda d, k: d.rounded_rectangle(BX((40, 70, 130, 170), k), int(16 * k), fill=255))
    parts.append(fx.shaded(pack, fx.lin(w, h, [(0, (190, 195, 210)), (1, (120, 125, 145))]), depth=0.15))
    limbs = [((30, 110), 26, (16, 175)), ((140, 110), 26, (154, 175)), ((66, 175), 30, (58, 248)),
             ((104, 175), 30, (112, 248))]
    for (a, wd, b) in limbs:
        m = fx.mask(w, h, lambda d, k, a=a, b=b, wd=wd: d.line(P([a, b], k), fill=255, width=int(wd * k)))
        parts.append(fx.shaded(m, fx.lin(w, h, [(0, (255, 255, 255)), (1, (190, 195, 215))], 0), depth=0.3))
    body = fx.mask(w, h, lambda d, k: d.rounded_rectangle(BX((36, 88, 134, 190), k), int(30 * k), fill=255))
    parts.append(fx.shaded(body, fx.lin(w, h, [(0, (255, 255, 255)), (1, (200, 205, 222))], 0), depth=0.12, hi_a=0.5))
    helm = fx.mask(w, h, lambda d, k: d.ellipse(BX((40, 6, 130, 96), k), fill=255))
    parts.append(fx.shaded(helm, fx.lin(w, h, [(0, (255, 255, 255)), (1, (200, 205, 222))]), depth=0.1, hi_a=0.5))
    vis = fx.mask(w, h, lambda d, k: d.ellipse(BX((52, 22, 120, 76), k), fill=255))
    parts.append(fx.shaded(vis, fx.lin(w, h, [(0, (255, 220, 120)), (0.5, (230, 150, 40)), (1, (120, 60, 20))], 120),
                           depth=0.2, hi_a=0.7))
    out = layer(w, h)
    for p_ in parts:
        out = Image.alpha_composite(out, p_)
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((66, 118, 104, 146), 6, fill=(60, 70, 100, 255))
    for i, c in enumerate(((255, 80, 80), (80, 220, 120), (90, 160, 255))):
        d.ellipse((72 + i * 11, 126, 80 + i * 11, 134), fill=c + (255,))
    d.ellipse((64, 30, 84, 44), fill=(255, 255, 255, 170))
    for x in (58, 112):
        d.rounded_rectangle((x - 16, 236, x + 16, 256), 8, fill=(110, 115, 135, 255))
    return out


@lru_cache(None)
def clock_face():
    s = 220
    m = fx.mask(s, s, lambda d, k: d.ellipse(BX((10, 10, s - 10, s - 10), k), fill=255))
    f = fx.shaded(m, fx.rad(s, s, 90, 80, 200, [(0, (255, 255, 255)), (1, (200, 210, 230))]), depth=0.06,
                  outline=(60, 70, 100), ow=6)
    d = ImageDraw.Draw(f)
    c = s / 2
    for i in range(12):
        a = i / 12 * 2 * math.pi
        d.line((c + 80 * math.sin(a), c - 80 * math.cos(a), c + 94 * math.sin(a), c - 94 * math.cos(a)),
               fill=(40, 40, 70, 255), width=5 if i % 3 == 0 else 3)
    return fx.drop_shadow(f, dy=10, blur=12, alpha=0.4)


def clock(img, x, y, ang, a=1.0, tint=None):
    place(img, clock_face(), x, y, alpha=a)
    lay = Image.new("RGBA", (W, H_))
    d = ImageDraw.Draw(lay)
    d.line((x, y, x + 72 * math.sin(ang), y - 72 * math.cos(ang)), fill=(220, 40, 60, int(255 * a)), width=7)
    d.line((x, y, x + 46 * math.sin(ang / 12), y - 46 * math.cos(ang / 12)), fill=(40, 40, 70, int(255 * a)), width=9)
    d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(40, 40, 70, int(255 * a)))
    if tint:
        d.ellipse((x - 100, y - 100, x + 100, y + 100), fill=tint + (int(70 * a),))
    img.alpha_composite(lay)


# ================================================================== SCHWARZES LOCH
@lru_cache(None)
def disk_ring(rx, ry, rin_x, rin_y, half=None):
    w, h = int(rx * 2 + 20), int(ry * 2 + 20)
    cx, cy = w / 2, h / 2
    sq = fx.rad(w, w, w / 2, w / 2, rx, [(0, (255, 255, 240)), (rin_x / rx, (255, 240, 200)), (0.7, (255, 150, 50)),
                                         (1, (200, 50, 30))]).resize((w, h))

    def fn(d, k):
        d.ellipse(BX((cx - rx, cy - ry, cx + rx, cy + ry), k), fill=255)
    m = fx.mask(w, h, fn)
    m = ImageChops.subtract(m, fx.mask(w, h, lambda d, k: d.ellipse(BX((cx - rin_x, cy - rin_y, cx + rin_x, cy + rin_y),
                                                                       k), fill=255)))
    if half:
        hm = Image.new("L", (w, h))
        ImageDraw.Draw(hm).rectangle((0, cy, w, h) if half == "front" else (0, 0, w, cy), fill=255)
        m = ImageChops.multiply(m, hm)
    return fx.apply_mask(sq, m)


@lru_cache(None)
def blackhole(r=120):
    w, h = 820, 560
    cx, cy = w / 2, h / 2
    out = layer(w, h)
    out.alpha_composite(fx.rad(w, h, cx, cy, 380, [(0, (255, 170, 80, 150)), (0.4, (200, 80, 60, 60)),
                                                     (1, (120, 40, 80, 0))]))
    back = disk_ring(380, 90, r * 1.25, 34, "back")
    out.alpha_composite(back, (int(cx - back.width / 2), int(cy - back.height / 2)))
    halo = layer(w, h)
    d = ImageDraw.Draw(halo)
    d.ellipse((cx - r * 1.55, cy - r * 1.55, cx + r * 1.55, cy + r * 1.55), outline=(255, 190, 90, 255), width=int(r * 0.4))
    out.alpha_composite(halo.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(out)
    d.ellipse((cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4), outline=(255, 240, 210, 255), width=4)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(0, 0, 0, 255))
    front = disk_ring(380, 90, r * 1.25, 34, "front")
    out.alpha_composite(front, (int(cx - front.width / 2), int(cy - front.height / 2)))
    return out


def bh(img_or_lay, x, y, gt, scale=1.0):
    place(img_or_lay, blackhole(), x, y, scale=scale)
    ov = Image.new("RGBA", img_or_lay.size)
    d = ImageDraw.Draw(ov)
    r = random.Random(2)
    for i in range(26):
        rr = r.uniform(170, 370) * scale
        a = r.uniform(0, 2 * math.pi) + gt * (2.2 * 170 / rr * scale)
        px, py = x + rr * math.cos(a), y + rr * 0.24 * math.sin(a)
        if math.sin(a) < 0 and abs(px - x) < 125 * scale:
            continue
        glow_dot(d, px, py, 3 * scale + 1, (255, 230, 180), a=0.8)
    img_or_lay.alpha_composite(ov)


def lc_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    lay = space_base(1).copy()
    bh(lay, PW / 2, PH / 2 + 40, gt, 0.9)
    k = (t * 0.12) % 1
    ang = 1.2 - 2.4 * k
    rr = 380 * (1 - 0.6 * k)
    place(lay, astronaut(), PW / 2 + rr * math.cos(ang), PH / 2 + 40 - rr * 0.5 * math.sin(ang), scale=0.5 * (1 - 0.4 * k),
          rot=gt * 40)
    put_panel(img, lay)
    qmark(img, t, gt, 900, 560)
    cap(img, *CAP("loch", 0, t))


def lc_c1(img, t, gt, d):
    pill(img, "SCHWARZES LOCH", 420, (255, 190, 110), fade(t, 0.2, 0.3))
    card(img)
    lay = space_base(1).copy()
    bh(lay, PW / 2 + 120, PH / 2, gt, 0.75)
    tl = W_("Licht", fallback=2.5) - 0.3
    a = fade(t, tl)
    ov = Image.new("RGBA", lay.size)
    dd = ImageDraw.Draw(ov)
    tx, ty = PW / 2 + 120, PH / 2
    for i, y0 in enumerate((150, 230, 300, 380, 450, 520)):
        pts = []
        for s in range(60):
            f = s / 59
            x = -20 + (tx - 20) * f
            pull = f ** 3
            pts.append((x + (tx - x) * pull * 0.9, y0 + (ty - y0) * pull))
        dd.line(pts, fill=(255, 240, 150, int(150 * a)), width=4, joint="curve")
        q = (gt * 0.45 + i / 6) % 1
        px, py = pts[int(q * 59)]
        glow_dot(dd, px, py, 6, (255, 250, 200), a=a * (1 - q ** 4))
    lay.alpha_composite(ov)
    put_panel(img, lay)
    label(img, "NICHT MAL LICHT", PX0 + 220, PY0 + 70, PX0 + 200, PY0 + 168, col=(255, 230, 150), a=a)
    cap(img, *CAP("loch", 1, t))


def stretched(img, x, y, sy, sx, rot, a=1.0, tint=None):
    sp = astronaut()
    w, h = max(1, int(sp.width * sx)), max(1, int(sp.height * sy))
    s2 = sp.resize((w, h), Image.BILINEAR)
    if tint is not None:
        tl = Image.new("RGBA", s2.size, tint[:3] + (0,))
        tl.putalpha(s2.getchannel("A").point(lambda v: int(v * tint[3] / 255)))
        s2 = Image.alpha_composite(s2, tl)
    place(img, s2, x, y, rot=rot, alpha=a)


def lc_c2(img, t, gt, d):
    pill(img, "GEZEITENKRÄFTE", 420, (255, 190, 110), fade(t, 0.2, 0.3))
    card(img)
    lay = space_base(1).copy()
    bh(lay, PW / 2, PH - 60, gt, 0.75)
    put_panel(img, lay)
    ax, ay = CX, CY - 120
    stretched(img, ax, ay, 0.62, 0.62, 180)
    tf = W_("Füßen", fallback=2.0) - 0.3
    tk = W_("Kopf", fallback=3.5) - 0.3
    lay2 = Image.new("RGBA", (W, H_))
    dd = ImageDraw.Draw(lay2)
    for (y0, ln, t0, col) in ((ay + 90, 150, tf, (255, 90, 90)), (ay - 90, 50, tk, (255, 200, 120))):
        a = fade(t, t0)
        if a > 0.02:
            x = ax + 130
            dd.line((x, y0, x, y0 + ln * a), fill=col + (int(255 * a),), width=14)
            dd.polygon([(x - 22, y0 + ln * a), (x + 22, y0 + ln * a), (x, y0 + ln * a + 30)], fill=col + (int(255 * a),))
    img.alpha_composite(lay2)
    label(img, "FÜSSE: STARK", PX0 + 190, CY + 10, ax - 20, ay + 80, col=(255, 120, 120), a=fade(t, tf))
    label(img, "KOPF: SCHWÄCHER", PX0 + 220, PY0 + 60, ax - 20, ay - 80, col=(255, 210, 140), a=fade(t, tk))
    cap(img, *CAP("loch", 2, t))


def lc_c3(img, t, gt, d):
    tl = W_("Länge", fallback=0.8) - 0.3
    ts = W_("Spaghettifizierung", fallback=3.5) - 0.2
    pill(img, "WIE EINE NUDEL", 420, (255, 190, 110), fade(t, 0.2, 0.3))
    card(img)
    lay = space_base(1).copy()
    bh(lay, PW / 2, PH - 40, gt, 0.75)
    put_panel(img, lay)
    k = ease_io(prog(t, tl, 2.6))
    stretched(img, CX, CY - 80 + 60 * k, 0.62 * (1 + 2.4 * k), 0.62 * (1 - 0.55 * k), 180)
    if t > ts:
        E.stamp(img, "SPAGHETTIFIZIERUNG", t, ts, cx=CX, cy=CY + 250, size=64, rot=-4, fill=YELLOW, sfill=(170, 20, 0))
    cap(img, *CAP("loch", 3, t))


def lc_c4(img, t, gt, d):
    pill(img, "ZEIT AM RAND", 420, (255, 190, 110), fade(t, 0.2, 0.3))
    card(img)
    lay = space_base(1).copy()
    bh(lay, PW / 2 + 140, PH / 2 + 60, gt, 0.8)
    put_panel(img, lay)
    tr = W_("Rand", fallback=3.0) - 0.3
    slow = ease_out(prog(t, 0.5, max(1.0, tr + 1.2)))
    stretched(img, CX + 140 - 150, CY + 60 - 60, 0.4, 0.4, 70, a=1 - 0.6 * slow, tint=(255, 60, 40, int(160 * slow)))
    ta = W_("außen", fallback=1.4) - 0.3
    clock(img, PX0 + 170, PY0 + 200, gt * 3.0, a=fade(t, ta))
    text(img, "DRAUSSEN", 30, PX0 + 170, PY0 + 330, fill=WHITE, stroke=4, sfill=NAVY, path=FONT_XB, alpha=fade(t, ta))
    # clock at the edge: angle integrates a slowing rate
    ang = 3.0 * (t - 0.0) * (1 - 0.5 * slow) - 1.5 * slow * slow * (t)
    ang = 3.0 * min(t, 0.5) + 3.0 * max(0.0, t - 0.5) * (1 - slow) * 0.6
    clock(img, PX0 + 170, PY0 + 500, ang, a=fade(t, tr - 0.4), tint=(255, 60, 40))
    text(img, "AM RAND", 30, PX0 + 170, PY0 + 630, fill=(255, 150, 140), stroke=4, sfill=NAVY, path=FONT_XB,
         alpha=fade(t, tr - 0.4))
    cap(img, *CAP("loch", 4, t))


# ================================================================== SONNE
@lru_cache(None)
def earth(state="day", r=110):
    s = r * 2 + 60
    c = s / 2
    m = fx.mask(s, s, lambda d, k: d.ellipse(BX((c - r, c - r, c + r, c + r), k), fill=255))
    if state == "ice":
        base = fx.rad(s, s, c - 30, c - 30, r * 1.5, [(0, (250, 255, 255)), (1, (170, 210, 240))])
    else:
        base = fx.rad(s, s, c - 30, c - 30, r * 1.5, [(0, (80, 170, 255)), (1, (20, 60, 150))])
    d = ImageDraw.Draw(base)
    rr = random.Random(3)
    land = (60, 160, 80) if state == "day" else ((30, 40, 60) if state == "night" else (235, 245, 255))
    lights = []
    for _ in range(7):
        x, y = c + rr.uniform(-r, r), c + rr.uniform(-r, r)
        pts = [(x + rr.uniform(20, 55) * math.cos(a), y + rr.uniform(20, 55) * math.sin(a)) for a in
               np.linspace(0, 2 * math.pi, 9)[:-1]]
        d.polygon(spline(pts, 6), fill=land + (255,))
        lights.append((x, y))
    if state == "night":
        base = Image.alpha_composite(base, Image.new("RGBA", (s, s), (0, 0, 20, 170)))
        d = ImageDraw.Draw(base)
        for (x, y) in lights:
            for _ in range(10):
                px, py = x + rr.uniform(-30, 30), y + rr.uniform(-30, 30)
                d.ellipse((px - 2, py - 2, px + 2, py + 2), fill=(255, 210, 120, 255))
    else:
        cl = layer(s, s)
        dc = ImageDraw.Draw(cl)
        for _ in range(9):
            x, y = c + rr.uniform(-r, r), c + rr.uniform(-r, r)
            dc.ellipse((x - 40, y - 10, x + 40, y + 10), fill=(255, 255, 255, 150))
        base = Image.alpha_composite(base, cl.filter(ImageFilter.GaussianBlur(4)))
    sh = fx.lin(s, s, [(0, (0, 0, 0, 0)), (0.45, (0, 0, 0, 0)), (1, (0, 0, 20, 200 if state != "night" else 80))], 0)
    ea = fx.shaded(m, Image.alpha_composite(base, sh), depth=0.05, hi_a=0.3)
    atm = (120, 190, 255) if state != "night" else (40, 60, 120)
    return fx.glow(ea, atm, radius=16, strength=0.6)


@lru_cache(None)
def moon(dark=False):
    s = 70
    m = fx.mask(s, s, lambda d, k: d.ellipse(BX((5, 5, s - 5, s - 5), k), fill=255))
    c0, c1 = ((230, 230, 235), (140, 140, 150)) if not dark else ((50, 50, 60), (25, 25, 32))
    mo = fx.shaded(m, fx.rad(s, s, 25, 22, 60, [(0, c0), (1, c1)]), depth=0.1)
    d = ImageDraw.Draw(mo)
    for x, y, r in ((24, 30, 6), (44, 22, 4), (40, 46, 7)):
        d.ellipse((x - r, y - r, x + r, y + r), fill=tuple(int(v * 0.8) for v in c1) + (255,))
    return mo


def solar(lay, gt, sun_a=1.0, sun_s=1.0, earth_state="day", earth_xy=(690, 330), moon_dark=False, orbit=True):
    if orbit:
        d = ImageDraw.Draw(lay)
        for k in range(0, 360, 6):
            a0, a1 = math.radians(k), math.radians(k + 3)
            r = 510
            d.line((150 + r * math.cos(a0), 330 + r * math.sin(a0), 150 + r * math.cos(a1), 330 + r * math.sin(a1)),
                   fill=(255, 255, 255, 60), width=3)
    if sun_a > 0.01:
        place(lay, M2.sun_sprite(), 150, 330, scale=0.9 * sun_s, alpha=sun_a, rot=gt * 3)
    ex, ey = earth_xy
    place(lay, earth(earth_state), ex, ey)
    ma = gt * 0.6
    place(lay, moon(moon_dark), ex + 170 * math.cos(ma), ey + 60 * math.sin(ma))


def sn_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    lay = space_base(3, (120, 70, 40)).copy()
    tv = 1.8
    vanish = ease_in = prog(t, tv, 0.35)
    solar(lay, gt, sun_a=1 - vanish, sun_s=1 + 0.3 * vanish)
    if 0 < t - tv < 0.6:
        fl = Image.new("RGBA", lay.size, (255, 240, 200, int(160 * (1 - (t - tv) / 0.6))))
        lay = Image.alpha_composite(lay, fl)
    put_panel(img, lay)
    qmark(img, t, gt, 900, 560)
    del ease_in
    cap(img, *CAP("sonne", 0, t))


def ghost_sun(lay):
    d = ImageDraw.Draw(lay)
    for k in range(0, 360, 12):
        a0, a1 = math.radians(k), math.radians(k + 6)
        d.line((150 + 120 * math.cos(a0), 330 + 120 * math.sin(a0), 150 + 120 * math.cos(a1), 330 + 120 * math.sin(a1)),
               fill=(255, 210, 120, 160), width=4)


def sn_c1(img, t, gt, d):
    pill(img, "LICHT IST UNTERWEGS", 420, (255, 200, 90), fade(t, 0.2, 0.3), size=38)
    card(img)
    lay = space_base(3, (120, 70, 40)).copy()
    solar(lay, gt, sun_a=0.0)
    ghost_sun(lay)
    tl = W_("Licht", fallback=2.0) - 0.4
    k = ease_io(prog(t, tl, max(1.5, SEG()["dur"] - tl - 0.6)))
    fx_ = 150 + (600 - 150) * k
    beam = layer()
    db = ImageDraw.Draw(beam)
    db.polygon([(fx_, 300), (600, 280), (600, 380), (fx_, 360)], fill=(255, 230, 150, 110))
    lay.alpha_composite(beam.filter(ImageFilter.GaussianBlur(8)))
    dd = ImageDraw.Draw(lay)
    dd.line((fx_, 290, fx_, 370), fill=(255, 255, 220, 230), width=5)
    put_panel(img, lay)
    secs = int(500 * k)
    a = fade(t, tl)
    text(img, f"{secs // 60}:{secs % 60:02d} min", 64, CX, PY0 + PH - 70, fill=YELLOW, stroke=7, sfill=NAVY,
         path=FONT_XB, alpha=a)
    label(img, "SONNE WEG", PX0 + 150, PY0 + 70, PX0 + 150, PY0 + 210, col=(255, 210, 120), a=fade(t, 0.4))
    cap(img, *CAP("sonne", 1, t))


def sn_c2(img, t, gt, d):
    td = W_("dunkel", fallback=1.0) - 0.2
    dk = ease_io(prog(t, td, 0.5))
    pill(img, "DUNKELHEIT", 420, (160, 170, 220), fade(t, 0.2, 0.3))
    card(img)
    lay = space_base(3, (120, 70, 40)).copy()
    ghost_sun(lay)
    solar(lay, gt, sun_a=0.0, earth_state="day", moon_dark=False)
    if dk > 0.01:
        l2 = layer()
        place(l2, earth("night"), 690, 330, alpha=dk)
        place(l2, moon(True), 690 + 170 * math.cos(gt * 0.6), 330 + 60 * math.sin(gt * 0.6), alpha=dk)
        lay.alpha_composite(l2)
    put_panel(img, lay)
    tm = W_("Mond", fallback=2.5) - 0.2
    mx, my = PX0 + 690 + 170 * math.cos(gt * 0.6), PY0 + 330 + 60 * math.sin(gt * 0.6)
    label(img, "MOND: DUNKEL", PX0 + 300, PY0 + 600, mx, my, col=(200, 200, 220), a=fade(t, tm))
    cap(img, *CAP("sonne", 2, t))


def sn_c3(img, t, gt, d):
    pill(img, "KEIN HALT MEHR", 420, (160, 170, 220), fade(t, 0.2, 0.3))
    card(img)
    lay = space_base(3, (120, 70, 40)).copy()
    ghost_sun(lay)
    tg = W_("geradeaus", fallback=2.5) - 0.4
    k = ease_io(prog(t, 0.6, max(1.5, SEG()["dur"] - 0.8)))
    ex, ey = 660, 330 - 420 * k
    d2 = ImageDraw.Draw(lay)
    for i in range(0, 60, 2):
        y = 330 - i * 8
        d2.line((660, y, 660, y - 8), fill=(255, 255, 255, 150), width=3)
    solar(lay, gt, sun_a=0.0, earth_state="night", earth_xy=(ex, ey), moon_dark=True)
    put_panel(img, lay)
    a = fade(t, tg)
    text(img, "↑", 90, PX0 + 760, CY - 40, fill=YELLOW, stroke=7, sfill=NAVY, alpha=a)
    label(img, "GERADEAUS", PX0 + 800, PY0 + 600, PX0 + 660, PY0 + 420, col=YELLOW, a=a)
    cap(img, *CAP("sonne", 3, t))


def sn_c4(img, t, gt, d):
    pill(img, "EISZEIT", 420, (180, 220, 255), fade(t, 0.2, 0.3))
    card(img)
    lay = space_base(4, (40, 80, 150)).copy()
    tw = W_("Woche", fallback=1.0) - 0.3
    k = ease_io(prog(t, tw, 1.6))
    place(lay, earth("night"), 360, 330, scale=1.5, alpha=1 - k)
    place(lay, earth("ice"), 360, 330, scale=1.5, alpha=k)
    put_panel(img, lay)
    M2.snow(img, gt, (PX0 + 30, PY0 + 30, PX0 + PW - 30, PY0 + PH - 30), n=40, a=k)
    tf = W_("fünfzehn", fallback=3.5) - 0.3
    M2.thermo(img, PX0 + 760, CY - 120, 0.75 - 0.6 * ease_io(prog(t, tf - 0.8, 1.2)), a=fade(t, 0.4),
              col=(90, 170, 255))
    text(img, "< −15 °C", 50, PX0 + 760, CY + 150, fill=(190, 225, 255), stroke=6, sfill=NAVY, path=FONT_XB,
         alpha=fade(t, tf))
    badge(img, "cold", PX0 + 120, PY0 + 90, fade(t, tw), r=46)
    text(img, "1 WOCHE", 32, PX0 + 240, PY0 + 90, fill=WHITE, stroke=4, sfill=NAVY, path=FONT_XB, alpha=fade(t, tw))
    cap(img, *CAP("sonne", 4, t))


# ================================================================== BÄRTIERCHEN
@lru_cache(None)
def tardi_body(dry=False):
    w, h = 460, 260
    pts = [(40, 130), (60, 90), (110, 66), (190, 56), (280, 58), (360, 70), (420, 100), (440, 140), (420, 180),
           (350, 196), (260, 200), (170, 198), (90, 186), (52, 164)]
    m = poly_mask(w, h, pts, 8)
    col = [(0, (240, 225, 190)), (0.6, (215, 190, 145)), (1, (170, 140, 95))] if not dry else \
        [(0, (200, 160, 110)), (1, (130, 95, 60))]
    b = fx.shaded(m, fx.lin(w, h, col), depth=0.12, dark=(90, 60, 30), dark_a=0.5, hi_a=0.5)
    b = Image.alpha_composite(b, clip(noise_tex(w, h, (120, 90, 50), amt=5, seed=7), m))
    d = ImageDraw.Draw(b)
    for x in (130, 200, 270, 340):
        d.arc((x - 40, 52, x + 40, 204), 300, 60, fill=(160, 130, 90, 160), width=4)
    r = random.Random(3)
    for _ in range(40):
        x, y = r.uniform(80, 410), r.uniform(80, 180)
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(255, 245, 220, 110))
    d.ellipse((70, 106, 82, 118), fill=(40, 30, 30, 255))
    d.rounded_rectangle((20, 118, 52, 138), 10, fill=(225, 205, 165, 255), outline=(150, 120, 80, 255), width=2)
    return clip(b, m)


def tardigrade(img, x, y, gt, scale=1.0, walk=1.0, a=1.0):
    w, h = 460, 300
    lay = layer(w, h)
    d = ImageDraw.Draw(lay)
    legs_x = (130, 210, 290, 380)

    def leg(lx, ph, col, back=False):
        sw = 14 * math.sin(gt * 6 * walk + ph)
        bx, by = lx + (8 if back else 0), 180
        ex, ey = bx + sw, 246
        d.line((bx, by, ex, ey), fill=col, width=36)
        d.ellipse((ex - 18, ey - 14, ex + 18, ey + 14), fill=col)
        for c in (-10, 0, 10):
            d.line((ex + c, ey + 10, ex + c + 6, ey + 24), fill=(80, 60, 40, 255), width=3)
    for i, lx in enumerate(legs_x):
        leg(lx, i * 1.3 + math.pi, (175, 150, 110, 255), back=True)
    lay.alpha_composite(tardi_body(), (0, 0))
    for i, lx in enumerate(legs_x):
        leg(lx, i * 1.3, (225, 205, 160, 255))
    place(img, lay, x, y, scale=scale, alpha=a)


@lru_cache(None)
def tun_sprite():
    w, h = 300, 200
    m = fx.mask(w, h, lambda d, k: d.ellipse(BX((20, 30, 280, 170), k), fill=255))
    b = fx.shaded(m, fx.lin(w, h, [(0, (215, 175, 120)), (1, (130, 95, 60))]), depth=0.15, hi_a=0.4)
    d = ImageDraw.Draw(b)
    for x in range(50, 260, 24):
        d.arc((x - 20, 30, x + 20, 170), 280, 80, fill=(110, 80, 50, 180), width=3)
    return fx.drop_shadow(clip(b, m), dy=8, blur=10, alpha=0.4)


@lru_cache(None)
def moss_scene():
    lay = fx.rad(PW, PH, PW / 2, PH / 2, PW * 0.6, [(0, (200, 230, 190)), (1, (120, 170, 120))])
    d = ImageDraw.Draw(lay)
    r = random.Random(6)
    for _ in range(26):
        x, y = r.uniform(0, PW), r.uniform(PH * 0.55, PH)
        a = r.uniform(-0.6, 0.6)
        ln = r.uniform(90, 180)
        for k in range(8):
            px = x + k * ln / 8 * math.sin(a)
            py = y - k * ln / 8 * math.cos(a)
            d.ellipse((px - 20, py - 8, px + 20, py + 8), fill=(60, 140, 70, 200))
    return lay.filter(ImageFilter.GaussianBlur(1.5))


def scope(img, content_fn, cx=CX, cy=CY + 10, R=320):
    lay = Image.new("RGBA", (W, H_))
    content = moss_scene().copy()
    content_fn(content)
    m = Image.new("L", (W, H_))
    ImageDraw.Draw(m).ellipse((cx - R, cy - R, cx + R, cy + R), fill=255)
    big = Image.new("RGBA", (W, H_))
    big.alpha_composite(content, (int(cx - PW / 2), int(cy - PH / 2)))
    lay.paste(big, (0, 0), m)
    d = ImageDraw.Draw(lay)
    vg = Image.new("RGBA", (W, H_))
    ImageDraw.Draw(vg).ellipse((cx - R, cy - R, cx + R, cy + R), outline=(0, 0, 0, 160), width=60)
    lay.alpha_composite(vg.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - R - 12, cy - R - 12, cx + R + 12, cy + R + 12), outline=(60, 65, 80, 255), width=24)
    d.ellipse((cx - R - 12, cy - R - 12, cx + R + 12, cy + R + 12), outline=(200, 205, 220, 255), width=6)
    img.alpha_composite(lay)


def bt_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)

    def cont(c):
        tardigrade(c, PW / 2 + 40 * math.sin(gt * 0.5), PH / 2 + 30, gt, scale=1.0)
    scope(img, cont)
    H.sparkles(img, gt, 2, (PX0 + 40, PY0 + 40, PX0 + PW - 40, PY0 + PH - 40), n=10, col=(220, 240, 255))
    qmark(img, t, gt, 900, 560)
    cap(img, *CAP("baer", 0, t))


def bt_c1(img, t, gt, d):
    pill(img, "BÄRTIERCHEN", 420, (170, 240, 170), fade(t, 0.2, 0.3))
    card(img)

    def cont(c):
        tardigrade(c, PW / 2 + 30 * math.sin(gt * 0.5), PH / 2 + 20, gt, scale=1.25)
    scope(img, cont)
    tm = W_("Millimeter", fallback=2.0) - 0.4
    a = fade(t, tm)
    lay = Image.new("RGBA", (W, H_))
    ImageDraw.Draw(lay).rounded_rectangle((CX - 120, CY + 250, CX + 120, CY + 262), 6, fill=(255, 255, 255, int(240 * a)))
    img.alpha_composite(lay)
    text(img, "< 1 mm", 40, CX, CY + 210, fill=WHITE, stroke=5, sfill=NAVY, path=FONT_XB, alpha=a)
    tb = W_("Beinchen", fallback=4.5) - 0.4
    label(img, "8 BEINE", PX0 + 800, PY0 + 560, CX + 160, CY + 160, col=YELLOW, a=fade(t, tb))
    cap(img, *CAP("baer", 1, t))


def bt_c2(img, t, gt, d):
    tt = W_("Tönnchen", fallback=2.5) - 0.3
    k = ease_io(prog(t, tt, 0.8))
    pill(img, "TÖNNCHEN" if k > 0.5 else "GEFAHR!", 420, (170, 240, 170) if k > 0.5 else (255, 140, 120), 1.0)
    card(img)

    def cont(c):
        if k < 0.99:
            tardigrade(c, PW / 2, PH / 2 + 20, gt, scale=1.2 * (1 - 0.35 * k), walk=1 - k, a=1 - k)
        if k > 0.01:
            place(c, tun_sprite(), PW / 2, PH / 2 + 30, scale=1.2 * (0.6 + 0.4 * k), alpha=k)
    scope(img, cont, cx=CX - 90)
    ts = W_("Stoffwechsel", fallback=4.0) - 0.3
    sm = ease_io(prog(t, ts, 1.2))
    a = fade(t, ts - 0.2)
    x, y = PX0 + PW - 80, CY
    lay = Image.new("RGBA", (W, H_))
    dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle((x - 36, y - 220, x + 36, y + 220), 26, fill=(14, 10, 34, int(220 * a)),
                         outline=(255, 255, 255, int(150 * a)), width=4)
    hgt = 420 * (1 - 0.98 * sm)
    dl.rounded_rectangle((x - 24, y + 208 - hgt, x + 24, y + 208), 18, fill=(110, 220, 120, int(255 * a)))
    img.alpha_composite(lay)
    text(img, "STOFFWECHSEL", 24, x, y - 250, fill=WHITE, stroke=4, sfill=NAVY, path=FONT_XB, alpha=a)
    text(img, "≈ 0,01 %", 30, x, y + 252, fill=YELLOW, stroke=4, sfill=NAVY, path=FONT_XB, alpha=fade(t, ts + 1.0))
    cap(img, *CAP("baer", 2, t))


def bt_c3(img, t, gt, d):
    tk = W_("Kälte", fallback=1.0) - 0.3
    tv = W_("Vakuum", fallback=4.5) - 0.3
    sp = ease_io(prog(t, tv, 0.6))
    pill(img, "IM WELTALL" if t > tv else "EXTREME KÄLTE", 420, (190, 210, 255), 1.0)
    card(img)
    lay = layer()
    ice = fx.lin(PW, PH, [(0, (210, 235, 255)), (1, (120, 170, 230))])
    lay.alpha_composite(ice)
    if sp > 0.01:
        sb = space_base(5).copy()
        place(sb, earth("day", 140), PW - 120, PH + 40, scale=1.6)
        sb.putalpha(sb.getchannel("A").point(lambda v: int(v * sp)))
        lay.alpha_composite(sb)
    place(lay, tun_sprite(), PW / 2 - 80, PH / 2 + 20 + 10 * math.sin(gt) * sp, scale=1.3, rot=gt * 8 * sp)
    put_panel(img, lay)
    fa = fade(t, tk) * (1 - sp)
    if fa > 0.02:
        M2.frost_crystals(img, gt, fa) if hasattr(M2, "frost_crystals") else H.frost(img, gt, CX - 80, CY, 260, n=30, a=fa)
        M2.thermo(img, PX0 + 780, CY - 120, 0.05, a=fa, col=(90, 170, 255))
        text(img, "−272 °C", 46, PX0 + 780, CY + 150, fill=(200, 230, 255), stroke=6, sfill=NAVY, path=FONT_XB, alpha=fa)
    if sp > 0.02:
        text(img, "VAKUUM", 50, PX0 + 760, PY0 + 120, fill=WHITE, stroke=6, sfill=NAVY, path=FONT_XB, alpha=sp)
    cap(img, *CAP("baer", 3, t))


@lru_cache(None)
def ice_block():
    w, h = 520, 380
    m = fx.mask(w, h, lambda d, k: d.rounded_rectangle(BX((10, 10, w - 10, h - 10), k), int(40 * k), fill=255))
    b = fx.shaded(m, fx.lin(w, h, [(0, (230, 250, 255, 200)), (1, (150, 200, 240, 170))]), depth=0.12, hi_a=0.7,
                  outline=(255, 255, 255), ow=3)
    d = ImageDraw.Draw(b)
    r = random.Random(4)
    for _ in range(30):
        x, y = r.uniform(40, w - 40), r.uniform(40, h - 40)
        s = r.uniform(3, 9)
        d.ellipse((x - s, y - s, x + s, y + s), outline=(255, 255, 255, 200), width=2)
    d.line((40, 40, 140, 30), fill=(255, 255, 255, 230), width=6)
    return b


def bt_c4(img, t, gt, d):
    tt = W_("tauten", fallback=1.0) - 0.2
    tl = W_("lebendig", fallback=5.5) - 0.3
    melt = ease_io(prog(t, tt + 0.6, 2.0))
    pill(img, "WIEDER LEBENDIG" if t > tl else "30 JAHRE IM EIS", 420, (170, 240, 170) if t > tl else (190, 220, 255),
         1.0, size=38)
    card(img)

    def cont(c):
        alive = ease_io(prog(t, tl - 0.6, 0.8))
        if alive < 0.99:
            place(c, tun_sprite(), PW / 2, PH / 2 + 30, scale=1.1, alpha=1 - alive)
        if alive > 0.01:
            tardigrade(c, PW / 2 + 60 * alive, PH / 2 + 20, gt, scale=1.0, walk=alive, a=alive)
        if melt < 0.99:
            place(c, ice_block(), PW / 2, PH / 2 + 20, scale=1.0, alpha=1 - melt)
    scope(img, cont)
    if 0.05 < melt < 0.95:
        lay = Image.new("RGBA", (W, H_))
        dl = ImageDraw.Draw(lay)
        for i in range(6):
            q = (gt * 0.8 + i / 6) % 1
            x = CX - 200 + i * 80
            dl.ellipse((x - 7, CY + 150 + 120 * q, x + 7, CY + 168 + 120 * q), fill=(150, 210, 255, int(220 * (1 - q))))
        img.alpha_composite(lay)
    tj = W_("dreißig", fallback=3.0) - 0.3
    M2.calendar(img, PX0 + PW - 110, PY0 + 120, 30, a=fade(t, tj))
    text(img, "JAHRE", 26, PX0 + PW - 110, PY0 + 250, fill=WHITE, stroke=4, sfill=NAVY, path=FONT_XB, alpha=fade(t, tj))
    badge(img, "check", PX0 + 110, PY0 + PH - 100, fade(t, tl), r=50)
    cap(img, *CAP("baer", 4, t))


# ================================================================== TUNNEL DURCH DIE ERDE
ER = 290


@lru_cache(None)
def earth_section():
    s = ER * 2 + 40
    c = s / 2
    out = layer(s, s)
    rings = [(ER, [(0, (60, 140, 220)), (1, (40, 100, 180))]),
             (ER - 12, [(0, (150, 110, 70)), (1, (110, 80, 50))]),
             (ER - 26, [(0, (250, 140, 60)), (0.8, (200, 70, 40)), (1, (160, 50, 30))]),
             (ER * 0.55, [(0, (255, 210, 90)), (1, (240, 140, 40))]),
             (ER * 0.25, [(0, (255, 255, 230)), (1, (255, 220, 120))])]
    for rr, st in rings:
        m = fx.mask(s, s, lambda d, k, rr=rr: d.ellipse(BX((c - rr, c - rr, c + rr, c + rr), k), fill=255))
        out = Image.alpha_composite(out, fx.shaded(m, fx.rad(s, s, c - rr * 0.3, c - rr * 0.3, rr * 1.4, st),
                                                   depth=0.04, hi_a=0.25))
    d = ImageDraw.Draw(out)
    r = random.Random(2)
    for _ in range(14):
        a = r.uniform(0, 2 * math.pi)
        a1 = a + r.uniform(0.1, 0.35)
        d.arc((c - ER, c - ER, c + ER, c + ER), math.degrees(a), math.degrees(a1), fill=(70, 160, 80, 255), width=10)
    g = layer(s, s)
    ImageDraw.Draw(g).ellipse((c - ER * 0.3, c - ER * 0.3, c + ER * 0.3, c + ER * 0.3), fill=(255, 240, 180, 120))
    out.alpha_composite(g.filter(ImageFilter.GaussianBlur(20)))
    d = ImageDraw.Draw(out)
    d.rectangle((c - 16, c - ER - 4, c + 16, c + ER + 4), fill=(20, 16, 30, 255))
    d.line((c - 17, c - ER, c - 17, c + ER), fill=(200, 200, 220, 200), width=3)
    d.line((c + 17, c - ER, c + 17, c + ER), fill=(200, 200, 220, 200), width=3)
    return fx.glow(out, (120, 180, 255), radius=20, strength=0.5)


def tunnel_scene(img, t, gt, pos, speed=0.0, labels=0.0):
    """pos: -1 top surface .. 0 center .. +1 bottom surface"""
    lay = space_base(6, (40, 80, 150)).copy()
    place(lay, earth_section(), PW / 2 - 120, PH / 2, scale=1.0 * (PH - 40) / (ER * 2 + 40))
    put_panel(img, lay)
    sc = (PH - 40) / (ER * 2 + 40)
    ex, ey = CX - 120, CY
    ay = ey + pos * ER * sc
    if speed > 0.05:
        lay2 = Image.new("RGBA", (W, H_))
        dd = ImageDraw.Draw(lay2)
        for k in range(6):
            off = (k - 2.5) * 6
            dd.line((ex + off, ay - 20 - 140 * speed, ex + off, ay - 20), fill=(255, 255, 255, int(150 * speed)), width=3)
        img.alpha_composite(lay2)
    place(img, astronaut(), ex, ay, scale=0.22, rot=180 if pos < 0.98 else 0)
    if labels > 0.02:
        label(img, "KRUSTE", PX0 + 780, PY0 + 70, ex + 120, CY - ER * sc + 10, col=(200, 230, 150), a=labels, size=24)
        label(img, "MANTEL", PX0 + 780, PY0 + 200, ex + 170, CY - 120, col=(255, 160, 100), a=labels, size=24)
        label(img, "KERN", PX0 + 780, PY0 + 330, ex + 50, CY, col=(255, 230, 140), a=labels, size=24)


def tn_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    tunnel_scene(img, t, gt, -1.0 - 0.04 * abs(math.sin(gt * 3)))
    text(img, "↓", 70, CX - 40, PY0 + 80, fill=YELLOW, stroke=6, sfill=NAVY, alpha=fade(t, 0.8))
    qmark(img, t, gt, 900, 560)
    cap(img, *CAP("tunnel", 0, t))


def tn_c1(img, t, gt, d):
    pill(img, "FREIER FALL", 420, (150, 200, 255), fade(t, 0.2, 0.3))
    card(img)
    k = prog(t, 0.3, SEG()["dur"] - 0.5)
    th = math.pi / 2 * k
    pos = -math.cos(th)
    tunnel_scene(img, t, gt, pos, speed=math.sin(th), labels=fade(t, 0.6))
    depth = int(6371 * (1 + pos))
    text(img, f"{depth:,} km tief".replace(",", "."), 52, PX0 + 760, PY0 + PH - 90, fill=YELLOW, stroke=6, sfill=NAVY,
         path=FONT_XB)
    cap(img, *CAP("tunnel", 1, t))


def tn_c2(img, t, gt, d):
    pill(img, "HÖCHSTES TEMPO", 420, (255, 200, 90), fade(t, 0.2, 0.3))
    card(img)
    k = prog(t, 0.0, SEG()["dur"])
    pos = 0.18 * (k - 0.5)
    tunnel_scene(img, t, gt, pos, speed=1.0)
    tk = W_("Kilometer", fallback=3.5) - 0.3
    a = fade(t, tk)
    text(img, "mehrere", 40, PX0 + 760, CY - 90, fill=WHITE, stroke=5, sfill=NAVY, path=FONT_XB, alpha=a)
    text(img, "km", 110, PX0 + 760, CY + 10, fill=YELLOW, stroke=8, sfill=NAVY, path=FONT_XB, alpha=a,
         scale=0.85 + 0.15 * back_out(a))
    text(img, "pro Sekunde", 40, PX0 + 760, CY + 110, fill=WHITE, stroke=5, sfill=NAVY, path=FONT_XB, alpha=a)
    cap(img, *CAP("tunnel", 2, t))


def tn_c3(img, t, gt, d):
    ts = W_("stehen", fallback=5.0) - 0.4
    pill(img, "BREMSEN", 420, (150, 200, 255), fade(t, 0.2, 0.3))
    card(img)
    k = prog(t, 0.3, max(1.0, ts - 0.3))
    th = math.pi / 2 + math.pi / 2 * k
    pos = -math.cos(th)
    tunnel_scene(img, t, gt, pos, speed=math.sin(th))
    if t > ts:
        E.stamp(img, "STOPP", t, ts, cx=CX + 200, cy=CY + 250, size=100, rot=-6, fill=YELLOW, sfill=(170, 20, 0))
    tl = W_("Luftwiderstand", fallback=0.6) - 0.2
    text(img, "ohne Luftwiderstand", 30, PX0 + 760, PY0 + 70, fill=(200, 220, 255), stroke=4, sfill=NAVY,
         path=FONT_XB, alpha=fade(t, tl))
    cap(img, *CAP("tunnel", 3, t))


def tn_c4(img, t, gt, d):
    pill(img, "REISEZEIT", 420, (255, 200, 90), fade(t, 0.2, 0.3))
    card(img)
    lay = space_base(6, (40, 80, 150)).copy()
    place(lay, earth_section(), 230, PH / 2, scale=0.62)
    put_panel(img, lay)
    tm = W_("achtunddreißig", fallback=1.6) - 0.5
    k = ease_io(prog(t, tm, 1.4))
    H.stopwatch(img, PX0 + 640, CY - 60, k * 38 / 60, fade(t, 0.3))
    text(img, f"≈ {int(round(38 * k))} MIN", 60, PX0 + 640, CY + 170, fill=YELLOW, stroke=7, sfill=NAVY, path=FONT_XB,
         alpha=fade(t, tm))
    q = (gt * 0.4) % 1
    pos = -math.cos(math.pi * q)
    place(img, astronaut(), PX0 + 230, CY + pos * ER * 0.62, scale=0.13, rot=180)
    cap(img, *CAP("tunnel", 4, t))


# ================================================================== registration
def SEG():
    return H.M.SEG


SCRIPTS = {
    "loch": ["Rate mal, was passiert, wenn du in ein Schwarzes Loch fällst.",
             "Seine Schwerkraft ist so stark, dass nicht einmal Licht ihm entkommen kann.",
             "Kommst du zu nah, zieht es an deinen Füßen viel stärker als an deinem Kopf.",
             "Du wirst in die Länge gezogen wie eine Nudel. Forscher nennen das Spaghettifizierung.",
             "Und für jemanden, der von außen zusieht, scheinst du am Rand fast stehen zu bleiben."],
    "sonne": ["Rate mal, was passiert, wenn die Sonne plötzlich verschwindet.",
              "Zuerst merkst du gar nichts. Ihr Licht braucht etwa acht Minuten bis zur Erde.",
              "Dann wird es schlagartig dunkel. Auch der Mond verschwindet, denn er leuchtet nur durch das Sonnenlicht.",
              "Gleichzeitig verliert die Erde ihren Halt und fliegt geradeaus ins All.",
              "Nach etwa einer Woche wäre es auf der Erde im Schnitt kälter als minus fünfzehn Grad."],
    "baer": ["Rate mal, was passiert, wenn man ein Bärtierchen einfriert.",
             "Bärtierchen sind winzige Tiere, kaum einen Millimeter groß, mit acht kleinen Beinchen.",
             "Bei Gefahr ziehen sie sich zu einem trockenen Tönnchen zusammen und fahren ihren Stoffwechsel fast ganz "
             "herunter.",
             "So überstehen sie extreme Kälte bis nahe dem absoluten Nullpunkt und sogar das Vakuum im Weltall.",
             "Japanische Forscher tauten Bärtierchen auf, die dreißig Jahre eingefroren waren. Sie wurden wieder "
             "lebendig."],
    "tunnel": ["Rate mal, was passiert, wenn du durch einen Tunnel quer durch die Erde springst.",
               "Du fällst immer schneller in Richtung Erdmitte, über sechstausend Kilometer tief.",
               "In der Mitte bist du so schnell, dass du jede Sekunde mehrere Kilometer zurücklegst.",
               "Ohne Luftwiderstand bremst dich die Schwerkraft danach wieder ab, bis du auf der anderen Seite kurz "
               "stehen bleibst.",
               "Die ganze Reise dauert nur etwa achtunddreißig Minuten."],
}
HL = {
    "loch": [("RATE", "MAL,", "SCHWARZES", "LOCH"), ("LICHT",), ("FÜSSEN", "KOPF."), ("SPAGHETTIFIZIERUNG.",),
             ("STEHEN",)],
    "sonne": [("RATE", "MAL,", "SONNE"), ("ACHT", "MINUTEN"), ("DUNKEL.", "MOND"), ("GERADEAUS",),
              ("FÜNFZEHN", "WOCHE")],
    "baer": [("RATE", "MAL,", "BÄRTIERCHEN"), ("MILLIMETER",), ("TÖNNCHEN",), ("KÄLTE", "VAKUUM"),
             ("DREISSIG", "LEBENDIG.")],
    "tunnel": [("RATE", "MAL,", "ERDE"), ("SECHSTAUSEND",), ("MEHRERE", "KILOMETER"), ("STEHEN",),
               ("ACHTUNDDREISSIG",)],
}
NEW = {
    "loch": dict(bg=((6, 4, 20), (50, 20, 70), (90, 40, 60)), out="schwarzes_loch_hq",
                 scenes=[lc_hook, lc_c1, lc_c2, lc_c3, lc_c4, H.outro]),
    "sonne": dict(bg=((20, 8, 20), (120, 50, 40), (140, 70, 40)), out="sonne_weg_hq",
                  scenes=[sn_hook, sn_c1, sn_c2, sn_c3, sn_c4, H.outro]),
    "baer": dict(bg=((6, 30, 24), (40, 120, 90), (60, 120, 80)), out="baertierchen_hq",
                 scenes=[bt_hook, bt_c1, bt_c2, bt_c3, bt_c4, H.outro]),
    "tunnel": dict(bg=((8, 12, 40), (60, 50, 110), (120, 70, 50)), out="tunnel_erde_hq",
                   scenes=[tn_hook, tn_c1, tn_c2, tn_c3, tn_c4, H.outro]),
}
KEYS = {"lc_c3": ("Spaghettifizierung", "thump"), "lc_c1": ("Licht", "pop"), "lc_c2": ("Füßen", "pop"),
        "sn_c2": ("dunkel", "thump"), "sn_c3": ("geradeaus", "pop"), "sn_c4": ("fünfzehn", "ding"),
        "bt_c2": ("Tönnchen", "pop"), "bt_c3": ("Vakuum", "pop"), "bt_c4": ("lebendig", "ding"),
        "tn_c3": ("stehen", "thump"), "tn_c4": ("achtunddreißig", "ding"), "tn_c2": ("Kilometer", "pop")}
N.NEW.update(NEW)
N.SCRIPTS.update(SCRIPTS)
N.KEYS.update(KEYS)
_prev_events = N.events


def events():
    ev = _prev_events()
    for s in H.CUR["segs"]:
        st, nm = s["start"], s["fn"].__name__
        if nm == "sn_hook":
            ev.append((st + 1.8, "thump", 0.12))
        if nm == "tn_c1":
            ev.append((st + 0.3, "whoosh", 0.12))
    return ev


N.events = events

if __name__ == "__main__":
    names = [a for a in ARGS if not a.startswith("--")] or list(NEW)
    for nm in names:
        if "--stills" in ARGS:
            N.stills(nm)
        else:
            N.make(nm, uhd="--hd" not in ARGS)

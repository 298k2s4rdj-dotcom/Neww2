#!/usr/bin/env python3
"""Three new premium 'Rate mal' Shorts: Fingerknacken, Schluckauf, eingeschlafener Fuss.

Uses the premium engine in make_hq.py (glass cards, bloom, grade, camera push-in).
If audio/<name>_<i>.mp3 + .words.json exist they are used (voiced); otherwise the captions run
on a calm synthetic reading pace and the mix is music + SFX only.

Usage: python3 make_new.py [--stills] [--hd] [name ...]   names: finger, schluckauf, fuss
"""
import json
import math
import os
import random
import subprocess
import sys
import wave
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ARGS = sys.argv[1:]
import make_hq as H  # noqa: E402
import fx  # noqa: E402
from fx import E as BX, P, place  # noqa: E402

M, E, LL = H.M, H.E, H.LL
text, text_w, ease_out, ease_io, back_out, prog = H.text, H.text_w, H.ease_out, H.ease_io, H.back_out, H.prog
FONT_XB = H.FONT_XB
W, H_, FPS, SR = H.W, H.H, H.FPS, H.SR
YELLOW, WHITE, RED, BLUE, GREEN, NAVY = H.YELLOW, H.WHITE, H.RED, H.BLUE, H.GREEN, H.NAVY
CX, CY, PW, PH, PX0, PY0 = H.CX, H.CY, H.PW, H.PH, H.PX0, H.PY0
W_, card, put_panel, layer, pill, qmark, cap, label, badge = H.W_, H.card, H.put_panel, H.layer, H.pill, H.qmark, \
    H.cap, H.label, H.badge
spline, poly_mask, clip, noise_tex, ss_layer, glow_dot = H.spline, H.poly_mask, H.clip, H.noise_tex, H.ss_layer, \
    H.glow_dot
AUDIO = os.path.join(HERE, "audio")
WPS = 2.9


def pulse(t, t0, att=0.08, dec=0.5):
    if t < t0:
        return 0.0
    x = t - t0
    return min(1.0, x / att) if x < att else math.exp(-(x - att) / dec)


def capsule(bx, by, ang, L, w, n=14, back=40):
    a = math.radians(ang)
    d = (math.sin(a), -math.cos(a))
    nr = (math.cos(a), math.sin(a))
    b = (bx - d[0] * back, by - d[1] * back)
    tip = (bx + d[0] * (L - w / 2), by + d[1] * (L - w / 2))
    pts = [(b[0] - nr[0] * w / 2, b[1] - nr[1] * w / 2), (tip[0] - nr[0] * w / 2, tip[1] - nr[1] * w / 2)]
    for k in range(1, n):
        th = math.pi * k / n
        v = (-nr[0] * math.cos(th) + d[0] * math.sin(th), -nr[1] * math.cos(th) + d[1] * math.sin(th))
        pts.append((tip[0] + v[0] * w / 2, tip[1] + v[1] * w / 2))
    pts += [(tip[0] + nr[0] * w / 2, tip[1] + nr[1] * w / 2), (b[0] + nr[0] * w / 2, b[1] + nr[1] * w / 2)]
    return pts, d, nr


SKIN = [(0, (255, 222, 192)), (0.6, (248, 190, 152)), (1, (226, 156, 120))]


# ================================================================== FINGERKNACKEN
FINGERS = [(150, 350, -9, 232, 64), (212, 338, -2, 262, 66), (274, 342, 5, 246, 62), (330, 362, 12, 196, 54)]
THUMB = (118, 470, -52, 178, 72)


@lru_cache(None)
def hand_sprite(mirror=False):
    w, h = 440, 600
    palm = [(118, 600), (96, 480), (100, 372), (132, 326), (332, 326), (366, 372), (358, 480), (340, 600)]

    def fn(d, k):
        d.polygon(P(spline(palm, 8), k), fill=255)
        for f in FINGERS + [THUMB]:
            d.polygon(P(capsule(*f)[0], k), fill=255)
    m = fx.mask(w, h, fn)
    sk = fx.shaded(m, fx.lin(w, h, SKIN, 20), depth=0.05, dark=(150, 60, 50), dark_a=0.5, hi_a=0.3)
    sk = Image.alpha_composite(sk, clip(noise_tex(w, h, (160, 90, 70), amt=3, seed=5), m))
    det = layer(w, h)
    d = ImageDraw.Draw(det)
    # finger separation shadows
    for f in FINGERS:
        pts, dd, nr = capsule(*f)
        for side in (-1, 1):
            a0 = (f[0] + nr[0] * side * f[4] / 2, f[1] + nr[1] * side * f[4] / 2)
            a1 = (a0[0] + dd[0] * f[3] * 0.7, a0[1] + dd[1] * f[3] * 0.7)
            d.line((a0, a1), fill=(170, 90, 70, 70), width=4)
    for (bx, by, ang, L, wd) in FINGERS + [THUMB]:
        _, dd, nr = capsule(bx, by, ang, L, wd)
        for f in ((0.36, 0.68) if (bx, by) != THUMB[:2] else (0.5,)):
            c = (bx + dd[0] * L * f, by + dd[1] * L * f)
            for j in (-5, 3):
                p0 = (c[0] - nr[0] * wd * 0.3 + dd[0] * j, c[1] - nr[1] * wd * 0.3 + dd[1] * j)
                p1 = (c[0] + nr[0] * wd * 0.3 + dd[0] * j, c[1] + nr[1] * wd * 0.3 + dd[1] * j)
                mid = ((p0[0] + p1[0]) / 2 - dd[0] * 4, (p0[1] + p1[1]) / 2 - dd[1] * 4)
                d.line([p0, mid, p1], fill=(185, 110, 85, 150), width=2, joint="curve")
        # knuckle highlight
        kc = (bx + dd[0] * 12, by + dd[1] * 12)
        d.ellipse((kc[0] - wd * 0.28, kc[1] - wd * 0.2, kc[0] + wd * 0.28, kc[1] + wd * 0.2), fill=(255, 235, 215, 90))
        # nail
        nc = (bx + dd[0] * (L - wd * 0.6), by + dd[1] * (L - wd * 0.6))
        npts = [(nc[0] + dd[0] * wd * 0.42 * math.sin(a) + nr[0] * wd * 0.33 * math.cos(a),
                 nc[1] + dd[1] * wd * 0.42 * math.sin(a) + nr[1] * wd * 0.33 * math.cos(a)) for a in
                np.linspace(0, 2 * math.pi, 28)]
        d.polygon(npts, fill=(255, 214, 205, 255), outline=(220, 150, 140, 255))
        hl = [(nc[0] - nr[0] * wd * 0.12 + dd[0] * wd * 0.25 * s, nc[1] - nr[1] * wd * 0.12 + dd[1] * wd * 0.25 * s)
              for s in (-1, 1)]
        d.line(hl, fill=(255, 255, 255, 200), width=4)
    # veins on the back of the hand
    for vx in (170, 240, 300):
        d.line(spline([(vx - 10, 590), (vx, 500), (vx + 6, 420), (vx + 4, 360)], 8, False), fill=(150, 150, 205, 60),
               width=7, joint="curve")
    sk = Image.alpha_composite(sk, clip(det, m))
    out = fx.drop_shadow(sk, dy=16, blur=18, alpha=0.4)
    return ImageOps.mirror(out) if mirror else out


def knack_star(img, x, y, t, t0, col=YELLOW):
    p = prog(t, t0, 0.5)
    if p <= 0 or p >= 1:
        return
    lay = Image.new("RGBA", (W, H_))
    d = ImageDraw.Draw(lay)
    for k in range(8):
        a = k * math.pi / 4
        r0, r1 = 20 + 60 * p, 50 + 80 * p
        d.line((x + r0 * math.cos(a), y + r0 * math.sin(a), x + r1 * math.cos(a), y + r1 * math.sin(a)),
               fill=col + (int(255 * (1 - p)),), width=8)
    img.alpha_composite(lay)


def fk_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW * 0.45, PH * 0.5, PW * 0.6, [(0, (120, 255, 230, 60)), (1, (120, 255, 230, 0))]))
    bend = 4 * math.sin(gt * 2)
    place(lay, hand_sprite(), 300, 380, scale=0.95, rot=8 + bend)
    place(lay, hand_sprite(True), 640, 380, scale=0.95, rot=-8 - bend)
    put_panel(img, lay)
    for k, t0 in enumerate((1.3, 2.4, 3.3)):
        x = PX0 + (300 if k % 2 == 0 else 640) + (k - 1) * 20
        knack_star(img, x, PY0 + 210, t, t0)
        a = 1 - prog(t, t0 + 0.3, 0.4)
        if t > t0 and a > 0:
            text(img, "KNACK", 44, x, PY0 + 130 - 30 * prog(t, t0, 0.6), fill=YELLOW, stroke=6, sfill=NAVY, alpha=a,
                 path=FONT_XB, rotate=8 * (1 if k % 2 else -1))
    qmark(img, t, gt, 900, 560)
    cap(img, CAPS["finger"][0][0], t, CAPS["finger"][0][1])


# --- joint cross-section (panel coordinates)
J, JY = 460, 330


@lru_cache(None)
def finger_tissue():
    lay = layer()
    m = fx.mask(PW, PH, lambda d, k: d.rounded_rectangle(BX((-60, 110, PW + 60, 550), k), int(210 * k), fill=255))
    sk = fx.shaded(m, fx.lin(PW, PH, SKIN), depth=0.04, dark=(150, 60, 50))
    inner = m.filter(ImageFilter.MinFilter(41))
    tis = fx.lin(PW, PH, [(0, (250, 170, 160)), (1, (215, 120, 120))])
    tis = Image.alpha_composite(tis, noise_tex(PW, PH, (150, 60, 70), amt=4, seed=8))
    out = Image.alpha_composite(sk, clip(tis, inner))
    d = ImageDraw.Draw(out)
    # tendon above, nerve + vessel below
    d.line(spline([(0, 178), (300, 172), (620, 176), (920, 170)], 8, False), fill=(255, 250, 240, 255), width=18)
    d.line(spline([(0, 172), (300, 166), (620, 170), (920, 164)], 8, False), fill=(255, 255, 255, 160), width=4)
    d.line(spline([(0, 486), (300, 494), (620, 484), (920, 490)], 8, False), fill=(205, 40, 60, 255), width=12)
    d.line(spline([(0, 506), (300, 512), (620, 504), (920, 510)], 8, False), fill=(255, 215, 80, 255), width=8)
    return clip(out, inner.filter(ImageFilter.MaxFilter(25)))


@lru_cache(None)
def capsule_layer(g):
    lay = layer()
    x0, x1 = J - 175, J + 175 + g
    fm = fx.mask(PW, PH, lambda d, k: d.ellipse(BX((x0 + 14, 214, x1 - 14, 446), k), fill=255))
    fl = fx.apply_mask(fx.rad(PW, PH, (x0 + x1) / 2, 300, 220, [(0, (255, 248, 200, 235)), (1, (250, 220, 140, 220))]), fm)
    om = fx.mask(PW, PH, lambda d, k: d.ellipse(BX((x0, 200, x1, 460), k), fill=255))
    ring = ImageChops.subtract(om, fm)
    mem = fx.shaded(ring, fx.lin(PW, PH, [(0, (250, 170, 185)), (1, (210, 110, 140))]), depth=0.3, hi_a=0.5)
    return Image.alpha_composite(Image.alpha_composite(lay, mem), fl)


def bone_fill(m, seed):
    b = fx.shaded(m, fx.lin(PW, PH, [(0, (252, 244, 226)), (0.5, (238, 224, 196)), (1, (206, 188, 156))]), depth=0.12,
                  dark=(120, 100, 70), dark_a=0.45, hi_a=0.4)
    sp = layer()
    d = ImageDraw.Draw(sp)
    r = random.Random(seed)
    bb = m.getbbox()
    for _ in range(420):
        x, y = r.uniform(bb[0], bb[2]), r.uniform(bb[1], bb[3])
        s = r.uniform(3, 8)
        d.ellipse((x - s, y - s * 0.7, x + s, y + s * 0.7), outline=(200, 175, 135, 140), width=2)
    inner = m.filter(ImageFilter.MinFilter(15))
    return Image.alpha_composite(b, clip(sp, inner))


@lru_cache(None)
def left_bone():
    def fn(d, k):
        d.rounded_rectangle(BX((-40, JY - 60, J - 70, JY + 60), k), int(20 * k), fill=255)
        d.ellipse(BX((J - 160, JY - 80, J, JY + 80), k), fill=255)
    m = fx.mask(PW, PH, fn)
    b = bone_fill(m, 1)
    cm = ImageChops.subtract(fx.mask(PW, PH, lambda d, k: d.ellipse(BX((J - 160, JY - 80, J, JY + 80), k), fill=255)),
                             fx.mask(PW, PH, lambda d, k: d.ellipse(BX((J - 146, JY - 68, J - 12, JY + 68), k), fill=255)))
    cm = ImageChops.multiply(cm, fx.mask(PW, PH, lambda d, k: d.rectangle(BX((J - 60, 0, PW, PH), k), fill=255)))
    cart = fx.shaded(cm, fx.lin(PW, PH, [(0, (230, 245, 255)), (1, (180, 210, 235))]), depth=0.4, hi_a=0.6)
    return Image.alpha_composite(b, cart)


@lru_cache(None)
def right_bone():
    def fn(d, k):
        d.rounded_rectangle(BX((J + 8, JY - 74, J + 110, JY + 74), k), int(30 * k), fill=255)
        d.rounded_rectangle(BX((J + 60, JY - 58, PW + 60, JY + 58), k), int(20 * k), fill=255)
    hole = fx.mask(PW, PH, lambda d, k: d.ellipse(BX((J - 172, JY - 92, J + 12, JY + 92), k), fill=255))
    m = ImageChops.subtract(fx.mask(PW, PH, fn), hole)
    b = bone_fill(m, 2)
    cm = ImageChops.subtract(fx.mask(PW, PH, lambda d, k: d.ellipse(BX((J - 186, JY - 104, J + 26, JY + 104), k),
                                                                    fill=255)), hole)
    cm = ImageChops.multiply(cm, m)
    cart = fx.shaded(cm, fx.lin(PW, PH, [(0, (230, 245, 255)), (1, (180, 210, 235))]), depth=0.4, hi_a=0.6)
    return Image.alpha_composite(b, cart)


@lru_cache(None)
def bubble_sprite(r=60):
    s = r * 2 + 8
    m = fx.mask(s, s, lambda d, k: d.ellipse(BX((4, 4, s - 4, s - 4), k), fill=255))
    b = fx.apply_mask(fx.rad(s, s, s * 0.5, s * 0.5, r, [(0, (220, 245, 255, 70)), (0.8, (190, 230, 255, 140)),
                                                         (1, (255, 255, 255, 230))]), m)
    d = ImageDraw.Draw(b)
    d.ellipse((s * 0.26, s * 0.2, s * 0.46, s * 0.34), fill=(255, 255, 255, 220))
    d.arc((s * 0.15, s * 0.15, s * 0.85, s * 0.85), 110, 170, fill=(255, 255, 255, 200), width=4)
    return b


def joint_scene(img, t, gt, g=0.0, conv=0.0, bub=0.0, dots=1.0, labels=0.0, shake=0.0):
    gi = int(round(g / 2) * 2)
    lay = finger_tissue().copy()
    lay.alpha_composite(capsule_layer(gi))
    d = ImageDraw.Draw(lay)
    cxg = J + 6 + gi / 2
    r = random.Random(3)
    for i in range(46):
        x0, y0 = r.uniform(J - 150, J + 150 + gi), r.uniform(230, 430)
        if ((x0 - (J + gi / 2)) / 160) ** 2 + ((y0 - 330) / 110) ** 2 > 1:
            continue
        x = x0 + 5 * math.sin(gt * 2 + i)
        y = y0 + 5 * math.cos(gt * 1.7 + i)
        x = x + (cxg - x) * conv
        y = y + (JY - y) * conv
        a = dots * (1 - conv * 0.95)
        if a > 0.03:
            glow_dot(d, x, y, 4, (120, 200, 255), a=a)
    if bub > 0.02:
        place(lay, bubble_sprite(), cxg, JY, scale=0.15 + 0.85 * bub)
    sh = shake * math.sin(gt * 70) * 4
    lay.alpha_composite(left_bone(), (int(sh), 0))
    lay.alpha_composite(right_bone(), (int(gi + sh), 0))
    put_panel(img, lay)
    if labels > 0.02:
        label(img, "KNOCHEN", PX0 + 150, PY0 + 70, PX0 + 200, PY0 + JY - 30, col=(255, 235, 200), a=labels)
        label(img, "KNORPEL", PX0 + 760, PY0 + 70, PX0 + J + 20, PY0 + JY - 60, col=(190, 225, 255), a=labels)
        label(img, "GELENKFLÜSSIGKEIT", PX0 + 470, PY0 + 610, PX0 + J + 30 + gi / 2, PY0 + 420,
              col=(255, 230, 140), a=labels)
        label(img, "GELENKKAPSEL", PX0 + 760, PY0 + 600, PX0 + J + 160 + gi, PY0 + 400, col=(255, 170, 190),
              a=labels, size=24)


def fk_c1(img, t, gt, d):
    pill(img, "IM FINGERGELENK", 420, (120, 255, 230), ease_out(prog(t, 0.2, 0.3)))
    card(img)
    joint_scene(img, t, gt, labels=ease_out(prog(t, 0.6, 0.5)))
    cap(img, CAPS["finger"][1][0], t, CAPS["finger"][1][1])


def fk_c2(img, t, gt, d):
    tz = W_("Ziehst", fallback=0.3)
    tg = W_("Gas", fallback=2.5)
    tb = W_("Blase", fallback=3.5)
    tk = W_("Knack", fallback=4.0)
    g = 34 * ease_io(prog(t, tz - 0.1, 0.9)) + 10 * ease_out(prog(t, tk - 0.05, 0.15))
    conv = ease_io(prog(t, tg - 0.1, max(0.4, tb - tg)))
    bub = ease_out(prog(t, tb - 0.15, 0.25))
    pill(img, "KNACK!" if t > tk else "ZUG AM FINGER", 420, YELLOW if t > tk else (120, 255, 230), 1.0)
    card(img)
    joint_scene(img, t, gt, g=g, conv=conv, bub=bub, shake=pulse(t, tk - 0.05, 0.05, 0.25))
    a = ease_out(prog(t, tz, 0.4)) * (1 - ease_out(prog(t, tk - 0.2, 0.2)))
    text(img, "ZUG  →", 50, PX0 + 760 + 20 * math.sin(gt * 4) * a, PY0 + 130, fill=WHITE, stroke=6, sfill=NAVY, alpha=a,
         path=FONT_XB)
    td = W_("Druck", fallback=1.5)
    if t > td - 0.1:
        label(img, "DRUCK ↓", PX0 + 190, PY0 + 600, PX0 + J - 60, PY0 + 420, col=(150, 210, 255),
              a=ease_out(prog(t, td - 0.1, 0.3)))
    if t > tb:
        label(img, "GASBLASE", PX0 + 760, PY0 + 600, PX0 + J + 30, PY0 + JY + 40, col=(190, 235, 255),
              a=ease_out(prog(t, tb, 0.3)))
    if t > tk - 0.05:
        E.stamp(img, "KNACK!", t, tk - 0.05, cx=540, cy=640, size=130, rot=-6, fill=YELLOW, sfill=(170, 20, 0))
        E.burst(img, PX0 + J + 25, PY0 + JY, t, tk - 0.05, color=YELLOW, n=14, rad=200)
    cap(img, CAPS["finger"][2][0], t, CAPS["finger"][2][1])


def fk_c3(img, t, gt, d):
    pill(img, "PAUSE", 420, (120, 255, 230), ease_out(prog(t, 0.2, 0.3)))
    card(img)
    sc = max(0.0, 1 - ease_io(prog(t, 0.6, 3.0)) * 0.75)
    joint_scene(img, t, gt, g=18 * sc, conv=0.6 * sc, bub=sc, dots=1.0)
    tm = W_("zwanzig", fallback=1.6) - 0.2
    pa = ease_out(prog(t, tm, 0.4))
    H.stopwatch(img, 860, 1030, ease_io(prog(t, tm + 0.1, 2.2)) * 0.33, pa)
    text(img, "≈ 20 MIN", 52, 860, 870, fill=WHITE, stroke=6, sfill=NAVY, alpha=pa, path=FONT_XB)
    cap(img, CAPS["finger"][3][0], t, CAPS["finger"][3][1])


def fk_c4(img, t, gt, d):
    pill(img, "60-JAHRE-SELBSTVERSUCH", 420, YELLOW, ease_out(prog(t, 0.2, 0.3)), size=36)
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW / 2, PH / 2, PW * 0.6, [(0, (255, 230, 150, 50)), (1, (255, 230, 150, 0))]))
    put_panel(img, lay)
    place(img, hand_sprite(True), CX - 210, CY + 40, scale=0.78)
    place(img, hand_sprite(), CX + 210, CY + 40, scale=0.78)
    tl = W_("einer", fallback=2.4)
    for k, (s, c) in enumerate((("GEKNACKT", YELLOW), ("NIE GEKNACKT", (190, 225, 255)))):
        a = ease_out(prog(t, tl - 0.2 + k * 0.3, 0.4))
        x = CX + (-210 if k == 0 else 210)
        place(img, H.pill_sprite(s, c, 32), x, PY0 + 60, alpha=a)
        text(img, s, 32, x, PY0 + 60, fill=c, alpha=a, path=FONT_XB)
        if k == 0 and t > tl:
            for j in range(3):
                knack_star(img, x - 40 + j * 40, CY - 120, t, tl + 0.2 + j * 0.45)
    tk = W_("keiner", fallback=4.5) - 0.1
    for k in range(2):
        badge(img, "check", CX + (-210 if k == 0 else 210), CY + 230, ease_out(prog(t, tk + k * 0.15, 0.4)), r=46)
    a = ease_out(prog(t, tk + 0.4, 0.4))
    text(img, "Ig-Nobelpreis 2009", 30, CX, PY0 + PH - 40, fill=(255, 240, 200), stroke=4, sfill=NAVY, alpha=a,
         path=FONT_XB)
    cap(img, CAPS["finger"][4][0], t, CAPS["finger"][4][1])


# ================================================================== SCHLUCKAUF
def hk_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW * 0.4, PH * 0.5, PW * 0.6, [(0, (255, 170, 120, 60)), (1, (255, 170, 120, 0))]))
    hops = [1.0, 2.6, 4.0]
    jump = sum(pulse(t, h0, 0.06, 0.18) for h0 in hops)
    place(lay, H.head_sprite(), 330, 360 - 22 * jump, scale=1.0, rot=-3 * jump)
    put_panel(img, lay)
    for k, h0 in enumerate(hops):
        p = prog(t, h0, 0.9)
        if 0 < p < 1:
            a = 1 - ease_io(max(0, (p - 0.6) / 0.4))
            text(img, "HICKS!", 64 * (0.6 + 0.4 * back_out(min(1, p * 3))), PX0 + 690 + 30 * k, PY0 + 240 - 120 * p,
                 fill=YELLOW, stroke=8, sfill=NAVY, alpha=a, path=FONT_XB, rotate=10 - 8 * k)
    qmark(img, t, gt, 170, 600, rot=-10)
    cap(img, CAPS["schluckauf"][0][0], t, CAPS["schluckauf"][0][1])


@lru_cache(None)
def torso_base():
    lay = layer()
    tor = [(120, 700), (140, 430), (120, 250), (210, 150), (380, 112), (460, 106), (540, 112), (710, 150), (800, 250),
           (780, 430), (800, 700)]
    tm = poly_mask(PW, PH, tor, 8)
    neck = fx.mask(PW, PH, lambda d, k: d.rectangle(BX((395, -20, 525, 140), k), fill=255))
    tm = ImageChops.lighter(tm, neck)
    sk = fx.shaded(tm, fx.lin(PW, PH, SKIN, 0), depth=0.04, dark=(150, 60, 50), dark_a=0.5)
    lay = Image.alpha_composite(lay, sk)
    win = fx.mask(PW, PH, lambda d, k: d.rounded_rectangle(BX((190, 150, 730, 700), k), int(80 * k), fill=255))
    tis = fx.lin(PW, PH, [(0, (150, 50, 60)), (1, (95, 25, 40))])
    tis = Image.alpha_composite(tis, noise_tex(PW, PH, (60, 10, 20), amt=4, seed=3))
    lay = Image.alpha_composite(lay, fx.shaded(win, tis, depth=0.05, dark_a=0.7))
    return lay


@lru_cache(None)
def lungs_sprite():
    lay = layer()
    L_ = [(440, 250), (380, 186), (300, 196), (240, 290), (218, 440), (228, 590), (300, 640), (400, 620), (444, 500)]
    R_ = [(480, 250), (540, 186), (620, 196), (680, 290), (702, 440), (692, 590), (620, 640), (560, 600), (500, 540)]
    for pts, seed in ((L_, 1), (R_, 2)):
        m = poly_mask(PW, PH, pts, 8)
        lu = fx.shaded(m, fx.rad(PW, PH, 380 if seed == 1 else 540, 300, 330,
                                 [(0, (255, 196, 205)), (1, (220, 120, 145))]), depth=0.07, dark=(120, 30, 60),
                       dark_a=0.5, hi_a=0.4)
        al = layer()
        d = ImageDraw.Draw(al)
        r = random.Random(seed)
        for _ in range(600):
            x, y = r.uniform(200, 720), r.uniform(180, 650)
            s = r.uniform(4, 9)
            d.ellipse((x - s, y - s, x + s, y + s), outline=(200, 110, 135, 110), width=2)
        lu = Image.alpha_composite(lu, clip(al, m))
        lay = Image.alpha_composite(lay, lu)
    # trachea + bronchial tree
    br = layer()
    d = ImageDraw.Draw(br)

    def tree(x, y, a, ln, w, depth):
        if depth == 0 or ln < 8:
            return
        x2, y2 = x + ln * math.cos(a), y + ln * math.sin(a)
        d.line((x, y, x2, y2), fill=(255, 235, 235, 230), width=max(2, int(w)))
        d.line((x + 1, y + 1, x2 + 1, y2 + 1), fill=(190, 90, 110, 120), width=max(1, int(w * 0.4)))
        tree(x2, y2, a - 0.42, ln * 0.74, w * 0.7, depth - 1)
        tree(x2, y2, a + 0.38, ln * 0.74, w * 0.7, depth - 1)
    tree(460, 250, math.radians(150), 90, 20, 6)
    tree(460, 250, math.radians(30), 90, 20, 6)
    for y in range(0, 252, 16):
        d.rounded_rectangle((440, y, 480, y + 12), 6, fill=(255, 225, 225, 255), outline=(200, 140, 150, 255), width=2)
    lay.alpha_composite(br)
    # heart
    hm = poly_mask(PW, PH, [(500, 440), (560, 420), (620, 460), (610, 540), (540, 590), (500, 540)], 8)
    lay.alpha_composite(fx.shaded(hm, fx.rad(PW, PH, 540, 450, 160, [(0, (240, 90, 100)), (1, (160, 20, 40))]),
                                  depth=0.15, hi_a=0.5))
    return lay


@lru_cache(None)
def ribs_layer():
    lay = layer()
    d = ImageDraw.Draw(lay)
    for k in range(7):
        y = 200 + k * 58
        for sgn in (-1, 1):
            pts = spline([(460 + sgn * 22, y), (460 + sgn * 150, y - 6), (460 + sgn * 250, y + 30),
                          (460 + sgn * 268, y + 90)], 8, False)
            d.line(pts, fill=(255, 246, 228, 150), width=16, joint="curve")
            d.line([(x, y_ - 4) for x, y_ in pts], fill=(255, 255, 255, 90), width=4, joint="curve")
    d.rounded_rectangle((440, 190, 480, 470), 16, fill=(255, 246, 228, 160))
    return lay


@lru_cache(None)
def abdomen_tex():
    t = fx.lin(PW, PH, [(0, (170, 70, 70)), (1, (120, 40, 50))])
    d = ImageDraw.Draw(t)
    d.ellipse((150, 520, 470, 760), fill=(150, 55, 50, 255))      # liver
    d.ellipse((480, 560, 700, 740), fill=(235, 160, 160, 255))    # stomach
    return Image.alpha_composite(t, noise_tex(PW, PH, (80, 20, 30), amt=5, seed=9))


def diaphragm(lay, h):
    base = 640
    pts = [(200 + i * 13, base - h * math.sin(math.pi * i / 40) ** 1.3) for i in range(41)]
    m = fx.mask(PW, PH, lambda d, k: d.polygon(P(pts + [(720, PH + 20), (200, PH + 20)], k), fill=255))
    m = ImageChops.multiply(m, fx.mask(PW, PH, lambda d, k: d.rounded_rectangle(BX((190, 150, 730, 700), k),
                                                                                int(80 * k), fill=255)))
    lay.alpha_composite(fx.apply_mask(abdomen_tex(), m))
    mm = fx.mask(PW, PH, lambda d, k: d.line(P(pts, k), fill=255, width=int(30 * k), joint="curve"))
    mus = fx.shaded(mm, fx.lin(PW, PH, [(0, (255, 110, 110)), (1, (190, 30, 50))]), depth=0.4, hi_a=0.5)
    d = ImageDraw.Draw(mus)
    for i in range(1, 40):
        x, y = pts[i]
        dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        n = math.hypot(dx, dy)
        nx, ny = -dy / n, dx / n
        d.line((x - nx * 13, y - ny * 13, x + nx * 13, y + ny * 13), fill=(150, 20, 40, 140), width=2)
    lay.alpha_composite(clip(mus, mm))
    return pts


def torso_scene(img, t, gt, h=150.0, labels=0.0, spasm=0.0):
    lay = torso_base().copy()
    lu = lungs_sprite()
    place(lay, lu, PW / 2, PH / 2 + 30 * spasm * 0.3, scale=1.0 + 0.03 * spasm)
    pts = diaphragm(lay, h)
    lay.alpha_composite(ribs_layer())
    put_panel(img, lay)
    if spasm > 0.1:
        for x in (320, 600):
            text(img, "↓", 60, PX0 + x, PY0 + pts[20][1] + 20, fill=YELLOW, stroke=6, sfill=NAVY, alpha=min(1, spasm))
    if labels > 0.02:
        label(img, "LUNGE", PX0 + 110, PY0 + 210, PX0 + 270, PY0 + 330, col=(255, 190, 210), a=labels)
        label(img, "ZWERCHFELL", PX0 + 770, PY0 + 610, PX0 + 640, PY0 + pts[32][1] + 8, col=(255, 130, 130), a=labels)
        label(img, "HERZ", PX0 + 800, PY0 + 400, PX0 + 600, PY0 + 480, col=(255, 140, 150), a=labels, size=24)


def hk_c1(img, t, gt, d):
    pill(img, "ZWERCHFELL", 420, (255, 140, 140), ease_out(prog(t, 0.2, 0.3)))
    card(img)
    tz = W_("zuckt", fallback=3.0)
    sp = max(pulse(t, tz - 0.05, 0.07, 0.35), pulse(t, tz + 1.9, 0.07, 0.35))
    torso_scene(img, t, gt, h=150 - 95 * sp, labels=ease_out(prog(t, 0.6, 0.5)), spasm=sp)
    cap(img, CAPS["schluckauf"][1][0], t, CAPS["schluckauf"][1][1])


def hk_c2(img, t, gt, d):
    tl = W_("Luft", fallback=0.3)
    ts = W_("Stimmritze", fallback=3.0)
    th = W_("Hicks", fallback=3.8)
    close = ease_out(prog(t, ts - 0.05, 0.2))
    pill(img, "HICKS!" if t > th else "LUFT STRÖMT EIN", 420, YELLOW if t > th else (150, 210, 255), 1.0)
    card(img)
    lay = H.section_base().copy()
    tx, ty = H.sx(404, 412)
    place(lay, H.tongue_sprite(), tx, ty, scale=0.72)
    d2 = ImageDraw.Draw(lay)
    # vocal folds (glottis)
    gx, gy = H.sx(337, 520)
    gap = 15 * (1 - close)
    for sgn in (-1, 1):
        d2.polygon([(gx + sgn * 20, gy - 16), (gx + sgn * 20, gy + 16), (gx + sgn * (gap + 1), gy + 4)],
                   fill=(255, 225, 225, 255), outline=(190, 110, 120, 255))
    # air particles: mouth -> throat -> down
    path = spline([H.sx(500, 395), H.sx(440, 395), H.sx(360, 395), H.sx(337, 430), H.sx(337, 500), H.sx(337, 600)],
                  8, False)
    flow = ease_out(prog(t, tl - 0.2, 0.3))
    for i in range(14):
        q = (gt * 0.9 + i / 14) % 1
        x, y = path[int(q * (len(path) - 1))]
        if close > 0.5 and y > gy - 10:
            continue
        glow_dot(d2, x, y, 6, (140, 200, 255), a=flow * math.sin(q * math.pi) * (1 - 0.6 * close))
    put_panel(img, lay)
    a = ease_out(prog(t, ts - 0.2, 0.4))
    label(img, "STIMMRITZE", PX0 + 650, PY0 + 600, PX0 + gx + 10, PY0 + gy, col=YELLOW, a=a)
    if t > th - 0.05:
        E.stamp(img, "HICKS!", t, th - 0.05, cx=780, cy=640, size=110, rot=8, fill=YELLOW, sfill=(170, 20, 0))
        E.burst(img, PX0 + gx, PY0 + gy, t, th - 0.05, color=YELLOW, n=12, rad=150)
    cap(img, CAPS["schluckauf"][2][0], t, CAPS["schluckauf"][2][1])


@lru_cache(None)
def burger_icon():
    s = 130
    out = layer(s, s)
    parts = [((14, 22, 116, 70), [(0, (255, 205, 120)), (1, (215, 130, 50))], "dome"),
             ((16, 66, 114, 80), [(0, (130, 220, 90)), (1, (60, 150, 40))], "lettuce"),
             ((18, 76, 112, 96), [(0, (150, 85, 50)), (1, (90, 45, 25))], "patty"),
             ((14, 94, 116, 116), [(0, (250, 195, 110)), (1, (205, 125, 50))], "bun")]
    for box, st, kind in parts:
        if kind == "dome":
            m = fx.mask(s, s, lambda d, k, b=box: d.pieslice(BX((b[0], b[1], b[2], b[3] + 46), k), 180, 360, fill=255))
        elif kind == "lettuce":
            pts = [(box[0] + i * 6, box[1] + 6 + 5 * math.sin(i * 1.4)) for i in range(17)]
            m = fx.mask(s, s, lambda d, k, pts=pts, b=box: d.polygon(P(pts + [(b[2], b[1]), (b[0], b[1])], k),
                                                                     fill=255))
        else:
            m = fx.mask(s, s, lambda d, k, b=box: d.rounded_rectangle(BX(b, k), int(9 * k), fill=255))
        out = Image.alpha_composite(out, fx.shaded(m, fx.lin(s, s, st), depth=0.25, hi_a=0.5))
    d = ImageDraw.Draw(out)
    d.polygon([(30, 76), (100, 76), (80, 92)], fill=(255, 210, 60, 255))
    r = random.Random(2)
    for _ in range(9):
        x, y = r.uniform(34, 96), r.uniform(32, 56)
        d.ellipse((x - 3, y - 2, x + 3, y + 2), fill=(255, 245, 210, 255))
    return fx.drop_shadow(out, dy=6, blur=8, alpha=0.4)


def hk_c3(img, t, gt, d):
    pill(img, "TYPISCHE AUSLÖSER", 420, YELLOW, ease_out(prog(t, 0.2, 0.3)), size=40)
    items = [("SCHNELL ESSEN", "burger", W_("Essen", fallback=1.4) - 0.3),
             ("KOHLENSÄURE", "glass", W_("Kohlensäure", fallback=2.6) - 0.3),
             ("AUFREGUNG", "heart", W_("Aufregung", fallback=3.6) - 0.3)]
    for k, (lab, ico, t0) in enumerate(items):
        p = ease_out(prog(t, t0, 0.45))
        if p <= 0.02:
            continue
        y = 600 + k * 190
        x = CX + 60 * (1 - p)
        place(img, H.row_sprite(860, 150), x, y, alpha=p)
        sc = 0.8 + 0.2 * back_out(p)
        if ico == "burger":
            place(img, burger_icon(), x - 320, y, scale=sc, alpha=p)
        elif ico == "glass":
            place(img, H.icon_sprite("glass"), x - 320, y, scale=sc, alpha=p)
            lay = Image.new("RGBA", (W, H_))
            dd = ImageDraw.Draw(lay)
            for j in range(6):
                q = (gt * 0.8 + j / 6) % 1
                bx = x - 330 + (j % 3) * 12
                dd.ellipse((bx - 3, y + 40 - 70 * q - 3, bx + 3, y + 40 - 70 * q + 3), outline=(255, 255, 255, int(230 * p)),
                           width=2)
            img.alpha_composite(lay)
        else:
            badge(img, "heart", x - 320, y, p * (1 + 0.08 * math.sin(gt * 9)), r=52)
        text(img, lab, 52, x + 60, y, fill=WHITE, stroke=5, sfill=NAVY, alpha=p, path=FONT_XB)
    cap(img, CAPS["schluckauf"][3][0], t, CAPS["schluckauf"][3][1])


@lru_cache(None)
def trophy_sprite():
    w, h = 260, 320
    gold = [(0, (255, 244, 170)), (0.45, (250, 200, 60)), (1, (190, 120, 20))]

    def cup_(d, k):
        d.pieslice(BX((40, -60, 220, 200), k), 0, 180, fill=255)
        d.rectangle(BX((112, 160, 148, 240), k), fill=255)
        d.rounded_rectangle(BX((70, 236, 190, 262), k), int(8 * k), fill=255)
    m = fx.mask(w, h, cup_)
    hm = fx.mask(w, h, lambda d, k: (d.ellipse(BX((4, 20, 80, 110), k), fill=255),
                                     d.ellipse(BX((180, 20, 256, 110), k), fill=255)))
    hm = ImageChops.subtract(hm, fx.mask(w, h, lambda d, k: (d.ellipse(BX((20, 36, 64, 94), k), fill=255),
                                                             d.ellipse(BX((196, 36, 240, 94), k), fill=255))))
    out = Image.alpha_composite(fx.shaded(hm, fx.lin(w, h, gold, 0), depth=0.3),
                                fx.shaded(m, fx.lin(w, h, gold, 0), depth=0.08, hi_a=0.6, dark=(120, 70, 0)))
    bm = fx.mask(w, h, lambda d, k: d.rounded_rectangle(BX((52, 262, 208, 316), k), int(10 * k), fill=255))
    out = Image.alpha_composite(out, fx.shaded(bm, fx.lin(w, h, [(0, (90, 60, 50)), (1, (50, 30, 25))]), depth=0.2))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((96, 276, 164, 302), 4, fill=(250, 210, 90, 255))
    d.polygon([(130, 40), (140, 66), (168, 66), (146, 82), (154, 108), (130, 92), (106, 108), (114, 82), (92, 66),
               (120, 66)], fill=(255, 250, 220, 255))
    return fx.glow(fx.drop_shadow(out, dy=12, blur=14), (255, 210, 80), radius=24, strength=0.45)


def hk_c4(img, t, gt, d):
    pill(img, "WELTREKORD", 420, YELLOW, ease_out(prog(t, 0.2, 0.3)))
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW / 2, PH * 0.45, PW * 0.55, [(0, (255, 210, 120, 70)), (1, (255, 210, 120, 0))]))
    put_panel(img, lay)
    tn = W_("achtundsechzig", fallback=1.5) - 0.3
    k = ease_io(prog(t, tn, 1.6))
    n = int(round(68 * k))
    text(img, str(n), 230, CX - 120, CY - 70, fill=YELLOW, stroke=12, sfill=NAVY, path=FONT_XB,
         alpha=ease_out(prog(t, tn, 0.3)))
    text(img, "JAHRE", 64, CX - 120, CY + 80, fill=WHITE, stroke=7, sfill=NAVY, path=FONT_XB,
         alpha=ease_out(prog(t, tn, 0.3)))
    place(img, trophy_sprite(), CX + 250, CY - 40 + 8 * math.sin(gt * 2), scale=0.85,
          alpha=ease_out(prog(t, tn + 1.4, 0.4)))
    # timeline
    x0, x1, y = PX0 + 90, PX0 + PW - 90, CY + 230
    lay2 = Image.new("RGBA", (W, H_))
    dd = ImageDraw.Draw(lay2)
    dd.rounded_rectangle((x0, y - 12, x1, y + 12), 12, fill=(255, 255, 255, 60))
    dd.rounded_rectangle((x0, y - 12, x0 + (x1 - x0) * k, y + 12), 12, fill=(255, 200, 60, 255))
    for j in range(8):
        xx = x0 + (x1 - x0) * j / 7
        dd.line((xx, y + 16, xx, y + 30), fill=(255, 255, 255, 140), width=3)
    img.alpha_composite(lay2)
    text(img, "1922", 34, x0, y + 58, fill=WHITE, stroke=4, sfill=NAVY, path=FONT_XB)
    text(img, "1990", 34, x1, y + 58, fill=WHITE, stroke=4, sfill=NAVY, path=FONT_XB, alpha=ease_out(prog(t, tn + 1.4, 0.3)))
    sparkles(img, gt, 5, (PX0 + 60, PY0 + 40, PX0 + PW - 60, PY0 + 400), n=12, col=(255, 230, 160))
    cap(img, CAPS["schluckauf"][4][0], t, CAPS["schluckauf"][4][1])


sparkles = H.sparkles


# ================================================================== EINGESCHLAFENER FUSS
@lru_cache(None)
def leg_sprite():
    w, h = PW, PH
    leg = [(372, -40), (548, -40), (566, 120), (536, 300), (514, 420), (526, 470), (640, 482), (724, 512), (742, 552),
           (706, 580), (424, 580), (382, 548), (396, 432), (382, 300), (352, 120)]
    m = poly_mask(w, h, leg, 8)
    sock_m = ImageChops.multiply(m, fx.mask(w, h, lambda d, k: d.rectangle(BX((0, 300, w, h), k), fill=255)))
    skin_m = ImageChops.subtract(m, sock_m)
    sk = fx.shaded(skin_m, fx.lin(w, h, SKIN, 0), depth=0.08, dark=(150, 60, 50), dark_a=0.5)
    sock = fx.lin(w, h, [(0, (250, 250, 255)), (1, (200, 205, 220))], 0)
    d = ImageDraw.Draw(sock)
    for y0, c in ((312, (230, 60, 80)), (338, (40, 70, 160)), (364, (230, 60, 80))):
        d.rectangle((0, y0, w, y0 + 14), fill=c + (255,))
    for y in range(390, 600, 7):
        d.line((0, y, w, y), fill=(180, 185, 200, 60), width=2)
    d.ellipse((610, 470, 760, 600), fill=(230, 60, 80, 255))        # toe patch
    d.ellipse((360, 500, 470, 610), fill=(230, 60, 80, 255))        # heel patch
    so = fx.shaded(sock_m, sock, depth=0.08, dark=(60, 60, 100), dark_a=0.5, hi_a=0.4)
    so = clip(Image.alpha_composite(so, layer(w, h)), sock_m)
    d = ImageDraw.Draw(sk)
    d.line(spline([(470, 0), (480, 120), (470, 240)], 8, False), fill=(150, 150, 205, 50), width=8)
    out = Image.alpha_composite(sk, so)
    sh = layer(w, h)
    ImageDraw.Draw(sh).ellipse((360, 560, 780, 610), fill=(10, 5, 30, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    return Image.alpha_composite(sh, out)


def zzz(img, t, gt, x, y, a=1.0):
    for k in range(3):
        q = (gt * 0.35 + k / 3) % 1
        s = 40 + 50 * q
        text(img, "Z", s, x + 70 * q + 12 * math.sin(gt * 2 + k), y - 200 * q, fill=(200, 225, 255), stroke=6,
             sfill=NAVY, alpha=a * math.sin(q * math.pi), path=FONT_XB, rotate=-12)


def fs_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW * 0.6, PH * 0.6, PW * 0.6, [(0, (140, 255, 200, 60)), (1, (140, 255, 200, 0))]))
    lay.alpha_composite(leg_sprite())
    put_panel(img, lay)
    zzz(img, t, gt, PX0 + 720, PY0 + 440, a=ease_out(prog(t, 0.8, 0.5)))
    if t > 1.8:
        H.sparkles(img, gt, 3, (PX0 + 560, PY0 + 440, PX0 + 760, PY0 + 600), n=10, col=(255, 240, 160))
    qmark(img, t, gt, 200, 640, rot=-10)
    cap(img, CAPS["fuss"][0][0], t, CAPS["fuss"][0][1])


SURF0 = 120


def dent(x, press):
    return 80 * press * math.exp(-((x - 460) / 150) ** 2)


@lru_cache(None)
def leg_deep():
    lay = layer()
    mus = fx.lin(PW, PH, [(0, (205, 70, 80)), (1, (150, 40, 55))])
    d = ImageDraw.Draw(mus)
    r = random.Random(4)
    for y in range(200, 520, 9):
        d.line([(x, y + 3 * math.sin(x / 60 + y)) for x in range(0, PW + 20, 20)], fill=(235, 110, 120, 120), width=2)
    for _ in range(30):
        y = r.uniform(220, 500)
        d.line((0, y, PW, y + r.uniform(-6, 6)), fill=(120, 25, 40, 90), width=3)
    mm = Image.new("L", (PW, PH))
    ImageDraw.Draw(mm).rectangle((0, 180, PW, 530), fill=255)
    lay = Image.alpha_composite(lay, clip(mus, mm))
    bm = fx.mask(PW, PH, lambda d, k: d.rounded_rectangle(BX((-60, 530, PW + 60, 720), k), int(60 * k), fill=255))
    bone = fx.shaded(bm, fx.lin(PW, PH, [(0, (252, 244, 226)), (1, (210, 192, 160))]), depth=0.06, hi_a=0.4)
    db = ImageDraw.Draw(bone)
    db.rectangle((0, 600, PW, 640), fill=(255, 220, 140, 200))
    return Image.alpha_composite(lay, bone)


@lru_cache(None)
def leg_top(level):
    press = level / 10
    lay = layer()
    top = [(x, SURF0 + dent(x, press)) for x in range(-20, PW + 21, 10)]
    fat_bot = [(x, 200 + 0.45 * dent(x, press)) for x in range(PW + 20, -21, -10)]
    fm = fx.mask(PW, PH, lambda d, k: d.polygon(P(top + fat_bot, k), fill=255))
    fat = fx.lin(PW, PH, [(0, (255, 230, 150)), (1, (240, 200, 110))])
    dc = ImageDraw.Draw(fat)
    r = random.Random(2)
    for _ in range(90):
        x, y = r.uniform(0, PW), r.uniform(130, 240)
        dc.ellipse((x - 18, y - 12, x + 18, y + 12), outline=(220, 175, 90, 200), width=2)
    lay = Image.alpha_composite(lay, fx.apply_mask(fat, fm))
    skin_b = [(x, y + 28) for x, y in reversed(top)]
    sm = fx.mask(PW, PH, lambda d, k: d.polygon(P(top + skin_b, k), fill=255))
    lay = Image.alpha_composite(lay, fx.shaded(sm, fx.lin(PW, PH, SKIN), depth=0.3, hi_a=0.5))
    return lay


def tube(d, k, y0, w0, press, col, hi):
    xs = list(range(-20, PW + 21, 10))
    up = [(x, y0 + 0.75 * dent(x, press) - w0 / 2 * (1 - 0.7 * press * math.exp(-((x - 460) / 120) ** 2))) for x in xs]
    dn = [(x, y0 + 0.75 * dent(x, press) + w0 / 2 * (1 - 0.7 * press * math.exp(-((x - 460) / 120) ** 2))) for x in xs]
    d.polygon(P(up + dn[::-1], k), fill=col)
    d.line(P([(x, y + 4) for x, y in up], k), fill=hi, width=int(3 * k))
    return [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(up, dn)]


@lru_cache(None)
def chair_sprite():
    w, h = 560, 150
    m = fx.mask(w, h, lambda d, k: d.rounded_rectangle(BX((10, 10, w - 10, h - 10), k), int(60 * k), fill=255))
    wood = fx.lin(w, h, [(0, (190, 130, 80)), (1, (120, 70, 40))])
    d = ImageDraw.Draw(wood)
    for y in range(20, h, 9):
        d.line([(x, y + 3 * math.sin(x / 40 + y)) for x in range(0, w, 12)], fill=(100, 60, 30, 110), width=2)
    return fx.drop_shadow(fx.shaded(m, wood, depth=0.15, hi_a=0.5), dy=10, blur=12)


def leg_scene(img, t, gt, press=0.0, imp=1.0, chaos=0.0, labels=0.0, flow=1.0):
    lay = leg_deep().copy()
    lv = int(round(press * 10))
    pr = lv / 10
    tubes = {}

    def draw_tubes(d, k):
        tubes["nerve"] = tube(d, k, 330, 34, pr, (255, 215, 70, 255), (255, 250, 200, 255))
        tubes["art"] = tube(d, k, 420, 30, pr, (210, 35, 55, 255), (255, 140, 150, 255))
        tubes["vein"] = tube(d, k, 462, 24, pr, (70, 90, 190, 255), (150, 170, 255, 255))
    lay.alpha_composite(ss_layer(PW, PH, draw_tubes))
    d = ImageDraw.Draw(lay)
    # fascicle lines on the nerve
    nv = tubes["nerve"]
    d.line([(x, y - 6) for x, y in nv], fill=(230, 180, 40, 200), width=2)
    d.line([(x, y + 6) for x, y in nv], fill=(230, 180, 40, 200), width=2)
    # blood cells
    art = tubes["art"]
    r = random.Random(5)
    for i in range(16):
        q = (gt * 0.12 * flow + i / 16) % 1
        x, y = art[int(q * (len(art) - 1))]
        sq = 1 - 0.6 * pr * math.exp(-((x - 460) / 120) ** 2)
        d.ellipse((x - 9, y - 6 * sq, x + 9, y + 6 * sq), fill=(255, 90, 100, 255), outline=(150, 20, 40, 255))
    # nerve impulses
    for i in range(6):
        q = (gt * 0.35 + i / 6) % 1
        x, y = nv[int(q * (len(nv) - 1))]
        a = imp
        if pr > 0.3 and x > 440:
            a *= max(0.0, 1 - (x - 440) / 60)
        if a > 0.03:
            glow_dot(d, x, y, 7, (255, 255, 200), a=a)
    if chaos > 0.02:
        for i in range(26):
            x = r.uniform(0, PW)
            ph = r.random()
            fl = 0.5 + 0.5 * math.sin(gt * (14 + 6 * ph) + ph * 6)
            idx = min(len(nv) - 1, max(0, int((x + 20) / 10)))
            glow_dot(d, x, nv[idx][1] + r.uniform(-12, 12), 5, (255, 250, 180), a=chaos * fl)
    lay.alpha_composite(leg_top(lv))
    if press > 0.01 or True:
        place(lay, chair_sprite(), 460, SURF0 - 78 + 80 * press, alpha=min(1, press * 3 + 0.0) if press > 0 else 0)
    put_panel(img, lay)
    if labels > 0.02:
        label(img, "NERV", PX0 + 120, PY0 + 270, PX0 + 150, PY0 + 330 + 0.75 * dent(150, pr), col=YELLOW, a=labels)
        label(img, "BLUTGEFÄSS", PX0 + 770, PY0 + 560, PX0 + 760, PY0 + 420 + 0.75 * dent(760, pr),
              col=(255, 130, 140), a=labels)
        label(img, "MUSKEL", PX0 + 560, PY0 + 615, PX0 + 600, PY0 + 505, col=(255, 160, 160), a=labels, size=24)


@lru_cache(None)
def foot_icon(state):
    s = 150
    col = {"ok": ((255, 214, 180), (230, 150, 120)), "numb": ((190, 200, 225), (120, 130, 170))}[state]
    m = fx.mask(s, s, lambda d, k: (d.ellipse(BX((40, 40, 110, 140), k), fill=255),
                                    [d.ellipse(BX((x - r, y - r, x + r, y + r), k), fill=255)
                                     for x, y, r in ((52, 26, 12), (74, 18, 10), (92, 22, 9), (105, 32, 8), (113, 46, 7))]))
    sp = fx.shaded(m, fx.lin(s, s, [(0, col[0]), (1, col[1])]), depth=0.15, hi_a=0.5)
    return fx.drop_shadow(sp, dy=6, blur=8, alpha=0.4)


def foot_status(img, x, y, numb, a=1.0):
    if a <= 0.02:
        return
    lay = Image.new("RGBA", (W, H_))
    ImageDraw.Draw(lay).rounded_rectangle((x - 95, y - 115, x + 95, y + 115), 30, fill=(14, 10, 34, int(200 * a)),
                                          outline=(255, 255, 255, int(120 * a)), width=3)
    img.alpha_composite(lay)
    place(img, foot_icon("ok"), x, y - 25, alpha=a * (1 - numb))
    place(img, foot_icon("numb"), x, y - 25, alpha=a * numb)
    # signal bars
    lay = Image.new("RGBA", (W, H_))
    d = ImageDraw.Draw(lay)
    lvl = 4 * (1 - numb)
    for k in range(4):
        on = k < lvl - 0.2
        d.rounded_rectangle((x - 50 + k * 26, y + 80 - k * 12, x - 34 + k * 26, y + 92), 4,
                            fill=((90, 220, 130) if on else (90, 90, 120)) + (int(255 * a),))
    img.alpha_composite(lay)


@lru_cache(None)
def ant_sprite():
    w, h = 64, 44
    lay = Image.new("RGBA", (w * 3, h * 3))
    d = ImageDraw.Draw(lay)
    k = 3
    for x0, rx, ry in ((10, 9, 7), (26, 7, 5), (44, 12, 8)):
        d.ellipse(((x0 - rx + 6) * k, (22 - ry) * k, (x0 + rx + 6) * k, (22 + ry) * k), fill=(30, 20, 20, 255))
    for j in (-1, 0, 1):
        lx = 32 + j * 6
        d.line((lx * k, 22 * k, (lx + j * 6) * k, 6 * k), fill=(30, 20, 20, 255), width=2 * k)
        d.line((lx * k, 22 * k, (lx + j * 6) * k, 38 * k), fill=(30, 20, 20, 255), width=2 * k)
    d.line((8 * k, 18 * k, 0, 6 * k), fill=(30, 20, 20, 255), width=2 * k)
    d.line((8 * k, 18 * k, 4 * k, 2 * k), fill=(30, 20, 20, 255), width=2 * k)
    d.ellipse((46 * k, 17 * k, 52 * k, 21 * k), fill=(120, 110, 110, 255))
    return lay.resize((w, h), Image.LANCZOS)


def ants(img, gt, n, box, a=1.0):
    r = random.Random(11)
    x0, y0, x1, y1 = box
    for i in range(n):
        sp, ph, yy = r.uniform(60, 120), r.random(), r.uniform(y0, y1)
        x = x0 + ((gt * sp + ph * (x1 - x0)) % (x1 - x0))
        y = yy + 10 * math.sin(gt * 6 + i)
        place(img, ant_sprite(), x, y, rot=180 + 8 * math.sin(gt * 10 + i), alpha=a, scale=0.9)


def fs_c1(img, t, gt, d):
    pill(img, "BEIM SITZEN", 420, (140, 255, 200), ease_out(prog(t, 0.2, 0.3)))
    card(img)
    tp = W_("drückst", fallback=0.6)
    press = ease_io(prog(t, tp - 0.2, 0.8))
    leg_scene(img, t, gt, press=press, labels=ease_out(prog(t, W_("Nerven", fallback=1.2) - 0.1, 0.4)),
              flow=1 - 0.7 * press)
    a = ease_out(prog(t, tp, 0.4))
    text(img, "DRUCK", 44, PX0 + 460, PY0 + 40 + 60 * press, fill=WHITE, stroke=6, sfill=NAVY, alpha=a, path=FONT_XB)
    cap(img, CAPS["fuss"][1][0], t, CAPS["fuss"][1][1])


def fs_c2(img, t, gt, d):
    pill(img, "SIGNALE STOCKEN", 420, (150, 200, 255), ease_out(prog(t, 0.2, 0.3)))
    card(img)
    leg_scene(img, t, gt, press=1.0, imp=1.0, labels=1.0, flow=0.3)
    tt = W_("taub", fallback=3.5) - 0.2
    numb = ease_io(prog(t, W_("Signale", fallback=2.0) - 0.3, 1.6))
    foot_status(img, PX0 + PW - 120, PY0 + 150, numb, a=ease_out(prog(t, 0.6, 0.4)))
    if t > tt:
        text(img, "TAUB", 40, PX0 + PW - 120, PY0 + 30, fill=(190, 210, 255), stroke=6, sfill=NAVY, path=FONT_XB,
             alpha=ease_out(prog(t, tt, 0.3)))
    to = W_("Sauerstoff", fallback=1.2)
    label(img, "WENIGER O₂", PX0 + 230, PY0 + 600, PX0 + 460, PY0 + 420 + 60, col=(255, 140, 150),
          a=ease_out(prog(t, to - 0.1, 0.4)), size=26)
    cap(img, CAPS["fuss"][2][0], t, CAPS["fuss"][2][1])


def fs_c3(img, t, gt, d):
    ts = W_("Stehst", fallback=0.3)
    tk = W_("kribbelt", fallback=4.0)
    rel = ease_io(prog(t, ts - 0.1, 0.7))
    chaos = ease_out(prog(t, W_("feuern", fallback=2.0) - 0.2, 0.5))
    pill(img, "KRIBBELN!" if t > tk else "DRUCK WEG", 420, YELLOW if t > tk else (140, 255, 200), 1.0)
    card(img)
    leg_scene(img, t, gt, press=1 - rel, imp=1.0, chaos=chaos, labels=0.0, flow=0.3 + 0.7 * rel)
    foot_status(img, PX0 + PW - 120, PY0 + 150, 1 - rel, a=1.0)
    if t > tk - 0.2:
        ants(img, gt, 7, (PX0 + 40, PY0 + 70, PX0 + PW - 260, PY0 + 140), a=ease_out(prog(t, tk - 0.2, 0.4)))
        E.stamp(img, "KRIBBEL!", t, tk - 0.05, cx=540, cy=1080, size=110, rot=-5, fill=YELLOW, sfill=(170, 20, 0))
    cap(img, CAPS["fuss"][3][0], t, CAPS["fuss"][3][1])


@lru_cache(None)
def footprint():
    s = 120
    m = fx.mask(s, s, lambda d, k: (d.ellipse(BX((34, 34, 84, 116), k), fill=255),
                                    [d.ellipse(BX((x - r, y - r, x + r, y + r), k), fill=255)
                                     for x, y, r in ((42, 20, 9), (58, 13, 8), (73, 15, 7), (85, 22, 6), (92, 33, 5))]))
    return fx.shaded(m, fx.lin(s, s, [(0, (255, 255, 255, 230)), (1, (200, 230, 255, 200))]), depth=0.2)


def fs_c4(img, t, gt, d):
    pill(img, "HARMLOS", 420, GREEN, ease_out(prog(t, 0.2, 0.3)))
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW / 2, PH / 2, PW * 0.6, [(0, (140, 255, 200, 60)), (1, (140, 255, 200, 0))]))
    put_panel(img, lay)
    tm = W_("Minuten", fallback=2.0) - 0.4
    pa = ease_out(prog(t, tm, 0.4))
    H.stopwatch(img, CX - 230, CY - 60, ease_io(prog(t, tm + 0.2, 2.0)) * 0.2, pa)
    text(img, "ein paar Minuten", 34, CX - 230, CY + 110, fill=WHITE, stroke=5, sfill=NAVY, alpha=pa, path=FONT_XB)
    badge(img, "check", CX - 120, CY - 170, ease_out(prog(t, W_("vorbei", fallback=2.6) - 0.1, 0.4)), r=46)
    tb = W_("bewegen", fallback=3.6) - 0.3
    for k in range(6):
        p = ease_out(prog(t, tb + k * 0.28, 0.25))
        if p > 0.02:
            x = CX + 120 + (40 if k % 2 else -40)
            y = CY + 230 - k * 85
            place(img, footprint(), x, y, rot=-10 if k % 2 else 10, alpha=p, scale=0.7 + 0.3 * p)
    text(img, "BEWEGEN", 46, CX + 120, CY + 300, fill=YELLOW, stroke=6, sfill=NAVY, path=FONT_XB,
         alpha=ease_out(prog(t, tb, 0.4)))
    cap(img, CAPS["fuss"][4][0], t, CAPS["fuss"][4][1])


# ================================================================== scripts + assembly
SCRIPTS = {
    "finger": ["Rate mal, was passiert, wenn du mit den Fingern knackst.",
               "In deinen Fingergelenken steckt eine Flüssigkeit, die die Knochen schmiert.",
               "Ziehst du am Finger, sinkt dort der Druck. Gelöstes Gas bildet plötzlich eine Blase. Knack.",
               "Danach dauert es etwa zwanzig Minuten, bis es wieder knacken kann.",
               "Und schädlich? Ein Arzt knackte sechzig Jahre lang nur die Finger einer Hand. "
               "Arthrose bekam er an keiner."],
    "schluckauf": ["Rate mal, was passiert, wenn du Schluckauf hast.",
                   "Dein Zwerchfell, der große Atemmuskel unter der Lunge, zuckt plötzlich zusammen.",
                   "Luft schießt in deine Lunge. Doch direkt danach schließt sich die Stimmritze. Hicks.",
                   "Auslöser sind oft zu schnelles Essen, Getränke mit Kohlensäure oder Aufregung.",
                   "Der Rekord: Ein Mann aus den USA hatte achtundsechzig Jahre lang Schluckauf."],
    "fuss": ["Rate mal, was passiert, wenn dein Fuß einschläft.",
             "Beim Sitzen drückst du Nerven und Blutgefäße in deinem Bein ab.",
             "Die Nerven bekommen weniger Sauerstoff und senden kaum noch Signale. Der Fuß fühlt sich taub an.",
             "Stehst du auf, ist der Druck weg. Die Nerven feuern wild durcheinander. Es kribbelt wie Ameisen.",
             "Keine Sorge: Meist ist das nach ein paar Minuten vorbei. Einfach bewegen."],
}
OUTRO_TXT = "Hättest du's gewusst? Schreib's in die Kommentare."
HL = {
    "finger": [("RATE", "MAL,", "KNACKST."), ("FLÜSSIGKEIT,",), ("BLASE.", "KNACK."), ("ZWANZIG",),
               ("SECHZIG", "KEINER.")],
    "schluckauf": [("RATE", "MAL,", "SCHLUCKAUF"), ("ZWERCHFELL,",), ("STIMMRITZE.", "HICKS."),
                   ("ESSEN,", "KOHLENSÄURE", "AUFREGUNG."), ("ACHTUNDSECHZIG",)],
    "fuss": [("RATE", "MAL,", "EINSCHLÄFT."), ("NERVEN",), ("TAUB",), ("KRIBBELT",), ("BEWEGEN.",)],
}
CAPS = {k: [(s, h) for s, h in zip(v, HL[k])] for k, v in SCRIPTS.items()}
NEW = {
    "finger": dict(bg=((6, 34, 46), (20, 100, 116), (30, 90, 100)), out="fingerknacken_hq",
                   scenes=[fk_hook, fk_c1, fk_c2, fk_c3, fk_c4, H.outro]),
    "schluckauf": dict(bg=((50, 12, 30), (150, 56, 60), (110, 50, 60)), out="schluckauf_hq",
                       scenes=[hk_hook, hk_c1, hk_c2, hk_c3, hk_c4, H.outro]),
    "fuss": dict(bg=((8, 30, 44), (30, 110, 90), (40, 90, 80)), out="fuss_eingeschlafen_hq",
                 scenes=[fs_hook, fs_c1, fs_c2, fs_c3, fs_c4, H.outro]),
}
KEYS = {"fk_c2": ("Knack", "thump"), "fk_c4": ("keiner", "ding"), "fk_c3": ("zwanzig", "tick"),
        "hk_c1": ("zuckt", "pop"), "hk_c2": ("Hicks", "thump"), "hk_c4": ("achtundsechzig", "ding"),
        "fs_c1": ("drückst", "pop"), "fs_c3": ("kribbelt", "thump"), "fs_c4": ("bewegen", "ding"),
        "hk_c3": ("Essen", "pop")}


def synth_words(txt, pre=0.25):
    out = []
    t = pre
    for w in txt.split():
        dur = 0.18 + 0.045 * len(w)
        out.append((w, t, t + dur))
        t += dur + (0.32 if w[-1] in ".!?" else 0.12 if w[-1] in ",:" else 0.07)
    return out


def init(name):
    spec = NEW[name]
    C = H.CUR
    C.clear()
    C.update(spec, name=name)
    C["BG"] = fx.background(W, H_, *spec["bg"], seed=len(name) + 3)
    t, segs = 0.0, []
    for i, fn in enumerate(spec["scenes"]):
        outro = fn is H.outro
        key = "outro" if outro else f"{name}_{i}"
        mp3 = os.path.join(AUDIO, key + ".mp3")
        pre = 0.25
        seg = dict(fn=fn, start=t, cap="", pre=pre)
        if os.path.exists(mp3):
            ws = json.load(open(os.path.join(AUDIO, key + ".words.json")))["words"]
            seg["words"] = [(w["text"], w["start"] + pre, w["end"] + pre) for w in ws]
            seg["mp3"] = mp3
            seg["dur"] = pre + ws[-1]["end"] + (1.8 if outro else 0.8)
        else:
            seg["words"] = synth_words(OUTRO_TXT if outro else SCRIPTS[name][i], pre)
            seg["dur"] = seg["words"][-1][2] + (2.0 if outro else 1.1)
        segs.append(seg)
        t += seg["dur"]
    C["segs"], C["total"] = segs, t


def events():
    ev = []
    for i, s in enumerate(H.CUR["segs"]):
        st = s["start"]
        nm = s["fn"].__name__
        if i > 0:
            ev.append((st - 0.1, "whoosh", 0.10))
        ev.append((st + 0.3, "pop", 0.08))
        if nm in KEYS:
            w, kind = KEYS[nm]
            ev.append((st + H.seg_word(s, w, 1.0) - 0.05, kind, 0.14 if kind == "thump" else 0.10))
        if nm == "fk_hook":
            ev += [(st + x, "tick", 0.09) for x in (1.3, 2.4, 3.3)]
        if nm == "hk_hook":
            ev += [(st + x, "pop", 0.10) for x in (1.0, 2.6, 4.0)]
        if nm == "hk_c3":
            for w in ("Kohlensäure", "Aufregung"):
                ev.append((st + H.seg_word(s, w, 1.0) - 0.3, "pop", 0.07))
        if nm == "outro":
            tr = H.seg_word(s, "Kommentare", 1.0) + 0.5
            ev += [(st + tr, "chime", 0.12), (st + tr, "thump", 0.12)]
    return ev


def make(name, uhd=True):
    init(name)
    C = H.CUR
    LL.TOTAL = C["total"]
    mix = LL.synth(events())
    voiced = any(sg.get("mp3") for sg in C["segs"])
    if voiced:
        voice = np.zeros(len(mix))
        for sg in C["segs"]:
            if not sg.get("mp3"):
                continue
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sg["mp3"], "-f", "s16le", "-ac", "1", "-ar", str(SR),
                                  "-"], capture_output=True, check=True).stdout
            v = np.frombuffer(raw, dtype=np.int16) / 32768.0
            a0 = int((sg["start"] + sg["pre"]) * SR)
            b0 = min(len(voice), a0 + len(v))
            voice[a0:b0] += v[:b0 - a0] / (np.abs(v).max() + 1e-9) * 0.89
        mix = np.clip(voice + mix * 1.2, -0.98, 0.98)
    else:
        mix = np.clip(mix * 2.2, -0.98, 0.98)
    bd = os.path.join(HERE, "build")
    os.makedirs(bd, exist_ok=True)
    wav = os.path.join(bd, f"{name}.wav")
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((mix[:int(C["total"] * SR)] * 32767).astype(np.int16).tobytes())
    tmp = os.path.join(bd, f"{name}_tmp.mp4")
    nfr = int(math.ceil(C["total"] * FPS))
    vf = ["-vf", "scale=2160:3840:flags=lanczos"] if uhd else []
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                           f"{W}x{H_}", "-r", str(FPS), "-i", "-", "-i", wav] + vf +
                          ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "14M", "-bufsize", "28M",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                           "-movflags", "+faststart", "-shortest", tmp], stdin=subprocess.PIPE)
    with Pool(4, initializer=init, initargs=(name,)) as pool:
        for k0 in range(0, nfr, 48):
            for b in pool.map(H.render_bytes, range(k0, min(nfr, k0 + 48)), chunksize=4):
                ff.stdin.write(b)
    ff.stdin.close()
    ff.wait()
    r = subprocess.run(["ffmpeg", "-nostats", "-i", tmp, "-af", "ebur128", "-f", "null", "-"], capture_output=True,
                       text=True).stderr
    lufs = float([ln for ln in r.splitlines() if ln.strip().startswith("I:")][-1].split()[1])
    out = os.path.join(HERE, C["out"] + ("_4k" if uhd else "") + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:v", "copy", "-af",
                    f"volume={-14 - lufs:.2f}dB,alimiter=limit=0.84:level=false", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", out], check=True)
    os.remove(tmp)
    print("wrote", out, round(C["total"], 1), "s", flush=True)


def stills(name, fracs=(0.85,)):
    init(name)
    qc = os.path.join(HERE, "qc")
    os.makedirs(qc, exist_ok=True)
    for i, s in enumerate(H.CUR["segs"]):
        for f in fracs:
            gt = s["start"] + s["dur"] * f
            H.render_frame(int(gt * FPS)).save(os.path.join(qc, f"new_{name}_{i}_{int(f * 100):02d}.png"))


if __name__ == "__main__":
    names = [a for a in ARGS if not a.startswith("--")] or list(NEW)
    for nm in names:
        if "--stills" in ARGS:
            stills(nm)
        else:
            make(nm, uhd="--hd" not in ARGS)

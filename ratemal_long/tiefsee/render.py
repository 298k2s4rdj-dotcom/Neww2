#!/usr/bin/env python3
"""Rate mal: Was passiert, wenn du immer tiefer ins Meer tauchst? – Erklärvideo im Querformat (4K-fähig)."""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import longlib as L  # noqa: E402
from longlib import (W, H, SS, NAVY, YELLOW, WHITE, GREEN, RED, BLUE, ORANGE, PURPLE, FONT_XB,  # noqa: E402
                     back_out, ease_io, ease_out, prog, paste_c, rrect, text, wt)

SP = dict(pre=0.25, post=0.9)
plan = [
    dict(key="o00", audio="o00", kind="speech", dd=(0, 0), **SP),
    dict(key="o01", audio="o01", kind="speech", dd=(0, 3), **SP),
    dict(key="c10", kind="card", dur=3.0, title="10 METER", dd=(3, 10)),
    dict(key="o02", audio="o02", kind="speech", dd=(10, 12), **SP),
    dict(key="o03", audio="o03", kind="speech", dd=(12, 26), **SP),
    dict(key="c30", kind="card", dur=3.0, title="30 METER", dd=(26, 30)),
    dict(key="o04", audio="o04", kind="speech", dd=(30, 34), **SP),
    dict(key="o05", audio="o05", kind="speech", dd=(34, 60), **SP),
    dict(key="c200", kind="card", dur=3.0, title="200 METER", dd=(60, 200)),
    dict(key="o06", audio="o06", kind="speech", dd=(200, 215), **SP),
    dict(key="o07", audio="o07", kind="speech", dd=(215, 253), **SP),
    dict(key="c1000", kind="card", dur=3.0, title="1.000 METER", dd=(253, 1000)),
    dict(key="o08", audio="o08", kind="speech", dd=(1000, 1100), **SP),
    dict(key="o09", audio="o09", kind="speech", dd=(1100, 2000), **SP),
    dict(key="c3800", kind="card", dur=3.0, title="3.800 METER", dd=(2000, 3800)),
    dict(key="o10", audio="o10", kind="speech", dd=(3800, 3800), **SP),
    dict(key="c11k", kind="card", dur=3.4, title="10.935 METER", dd=(3800, 10935)),
    dict(key="o11", audio="o11", kind="speech", dd=(10935, 10935), **SP),
    dict(key="o12", audio="o12", kind="speech", dd=(10935, 10935), **SP),
    dict(key="o13", audio="o13", kind="speech", dd=(10935, 10935), pre=0.3, post=2.6),
]
MAXD = 10935.0
_c = {}


def fmt(n):
    return f"{int(round(n)):,}".replace(",", ".")


def ap(seg, t, word, n=1, d=0.35, off=-0.1):
    try:
        return ease_out(prog(t, wt(seg, word, n) + off, d))
    except KeyError:
        return 0.0


def pop(seg, t, word, n=1):
    try:
        return back_out(prog(t, wt(seg, word, n) - 0.1, 0.45))
    except KeyError:
        return 0.0


def tw(seg, word, n=1):
    return wt(seg, word, n)


def chip(img, s, cx, cy, col, a, size=34):
    L.pill(img, s, cx, cy, col, a, size=size)


def label(img, s, cx, cy, a=1.0, col=WHITE, size=32):
    text(img, s, size, cx, cy, fill=col, path=FONT_XB, stroke=4, sfill=NAVY, alpha=a)


def depth_at(gt):
    i = L.seg_at(gt)
    s = L.SEGS[i]
    k = ease_io(prog(gt - s["start"], 0, s["dur"]))
    d0, d1 = s["dd"]
    if d0 > 100 and d1 > d0:       # log-ish interpolation for the big jumps
        return math.exp(math.log(d0) + (math.log(d1) - math.log(d0)) * k)
    return d0 + (d1 - d0) * k


def dark(d):
    return min(1.0, math.log10(1 + d) / math.log10(1 + 1500))


# ------------------------------------------------------------------ water background
def lerpc(a, b, k):
    return tuple(int(x + (y - x) * k) for x, y in zip(a, b))


def water_bg(img, gt):
    d = depth_at(gt)
    f = dark(d)
    stops = [(0.0, (90, 190, 240), (40, 120, 200)), (0.45, (30, 100, 185), (12, 55, 130)),
             (0.75, (10, 35, 95), (5, 18, 55)), (1.0, (4, 8, 26), (1, 3, 10))]
    for (f0, t0, b0), (f1, t1, b1) in zip(stops, stops[1:]):
        if f0 <= f <= f1:
            k = (f - f0) / (f1 - f0)
            top, bot = lerpc(t0, t1, k), lerpc(b0, b1, k)
            break
    col = np.linspace(np.array(top), np.array(bot), H).astype(np.uint8)[:, None, :]
    bg = Image.fromarray(np.repeat(col, 2, axis=1)).resize((W, H), Image.BILINEAR).convert("RGBA")
    img.paste(bg, (0, 0))
    dr = ImageDraw.Draw(img)
    # light rays near the surface
    ra = max(0.0, 1 - d / 120)
    if ra > 0.02:
        lay = Image.new("RGBA", (W, H))
        dl = ImageDraw.Draw(lay)
        for k in range(7):
            x = 200 + k * 260 + 60 * math.sin(gt * 0.4 + k)
            dl.polygon([(x, 0), (x + 90, 0), (x + 260, H), (x + 120, H)], fill=(255, 255, 255, int(28 * ra)))
        img.alpha_composite(lay)
    # marine snow drifting up while descending
    rr = random.Random(3)
    vy = 40 + 220 * min(1, abs(depth_speed(gt)) / 200)
    for k in range(70):
        x = rr.uniform(0, W) + 10 * math.sin(gt + k)
        y = (rr.uniform(0, H) - gt * vy * rr.uniform(0.6, 1.4)) % H
        s = rr.uniform(1.0, 3.0)
        v = int(150 + 80 * (1 - f)) if f < 0.9 else 120
        dr.ellipse((x - s, y - s, x + s, y + s), fill=(v, v, min(255, v + 30)))


def depth_speed(gt):
    return (depth_at(gt + 0.1) - depth_at(gt)) * 10


L.draw_bg = water_bg


# ------------------------------------------------------------------ HUD
TICKS = [0, 10, 30, 100, 200, 1000, 3800, 10935]


def gy(d):
    return 160 + 760 * math.log10(1 + d) / math.log10(1 + MAXD)


def hud(img, gt, a=1.0):
    d = depth_at(gt)
    dr = ImageDraw.Draw(img)
    x = 95
    dr.line((x, 160, x, 920), fill=(255, 255, 255, 160), width=6)
    for tk in TICKS:
        y = gy(tk)
        dr.line((x - 14, y, x + 14, y), fill=WHITE, width=4)
        text(img, f"{fmt(tk)} m", 22, x + 22, y, fill=(220, 230, 255), path=FONT_XB, anchor="lm")
    y = gy(d)
    dr.polygon([(x - 30, y - 16), (x - 30, y + 16), (x - 4, y)], fill=YELLOW)
    dr.ellipse((x - 10, y - 10, x + 10, y + 10), fill=YELLOW)
    p = 1 + d / 10
    rrect(img, (W / 2 - 330, 32, W / 2 + 330, 112), 40, (10, 15, 35, 200), outline=(255, 255, 255, 120), width=3)
    text(img, f"−{fmt(d)} m", 56, W / 2 - 140, 72, fill=YELLOW, stroke=5, sfill=NAVY)
    ptxt = f"{fmt(round(p, -1))} bar" if p > 1000 else (f"{fmt(p)} bar" if p >= 10 else f"{p:.1f} bar".replace(".", ","))
    text(img, ("≈ " if p > 1000 else "") + ptxt, 44, W / 2 + 170, 72, fill=WHITE, stroke=4, sfill=NAVY)
    L.brand(img, W - 220, 70, gt, 0.85)


# ------------------------------------------------------------------ sprites
def diver(h, kick=0.0, tilt=0.0):
    k = ("diver", h, round(kick, 1), round(tilt))
    if k in _c:
        return _c[k]
    s = SS(h * 1.6, h * 0.6)
    c, suit = (255, 150, 70, 255), (40, 50, 70, 255)
    cy = h * 0.3
    s.rect(h * 0.35, cy - h * 0.1, h * 1.05, cy + h * 0.1, h * 0.09, suit)
    s.rect(h * 0.5, cy - h * 0.16, h * 0.9, cy - h * 0.08, h * 0.04, (250, 200, 60, 255))   # tank
    for sg in (-1, 1):
        a = 0.25 * sg * math.sin(kick)
        s.thick([(h * 0.38, cy + sg * h * 0.04), (h * 0.12, cy + sg * h * 0.04 + h * 0.12 * math.sin(a))],
                [h * 0.08, h * 0.07], suit)
        fx, fy = h * 0.12, cy + sg * h * 0.04 + h * 0.12 * math.sin(a)
        s.poly([(fx, fy - h * 0.04), (fx - h * 0.16, fy - h * 0.07), (fx - h * 0.16, fy + h * 0.07),
                (fx, fy + h * 0.04)], (80, 200, 255, 255))
    s.thick([(h * 0.95, cy + h * 0.05), (h * 1.3, cy + h * 0.1)], [h * 0.06, h * 0.05], suit)
    s.ell(h * 1.15, cy - h * 0.02, h * 0.11, h * 0.11, c)
    s.rect(h * 1.12, cy - h * 0.08, h * 1.3, cy + h * 0.0, h * 0.03, (130, 210, 255, 255))
    img = s.img().rotate(tilt, resample=Image.BICUBIC, expand=True)
    if len(_c) > 300:
        _c.clear()
    _c[k] = img
    return img


def balloon(img, cx, cy, r, col=RED, a=1.0):
    d = ImageDraw.Draw(img)
    d.line((cx, cy + r, cx + 6, cy + r + 120), fill=WHITE, width=3)
    d.ellipse((cx - r, cy - r * 1.15, cx + r, cy + r), fill=col)
    d.polygon([(cx - 10, cy + r + 6), (cx + 10, cy + r + 6), (cx, cy + r - 6)], fill=col)
    d.ellipse((cx - r * 0.5, cy - r * 0.8, cx - r * 0.2, cy - r * 0.4), fill=(255, 255, 255, 120))


def lungs(img, cx, cy, k, a=1.0):
    d = ImageDraw.Draw(img)
    d.rectangle((cx - 12, cy - 170, cx + 12, cy - 40), fill=(240, 200, 210))
    for sg in (-1, 1):
        w, h = 120 * k, 190 * k
        d.ellipse((cx + sg * 30 - (w if sg < 0 else 0) - (0 if sg < 0 else 0) + (0 if sg < 0 else 0),
                   cy - h * 0.55, cx + sg * 30 + (0 if sg < 0 else w), cy + h * 0.55), fill=(255, 130, 160))


def fish(img, cx, cy, s, col, flip=False):
    sp = SS(220 * s, 120 * s)
    sp.ell(95 * s, 60 * s, 80 * s, 42 * s, col + (255,))
    sp.poly([(160 * s, 60 * s), (215 * s, 20 * s), (215 * s, 100 * s)], col + (255,))
    sp.ell(50 * s, 50 * s, 10 * s, 10 * s, WHITE + (255,))
    sp.ell(48 * s, 50 * s, 5 * s, 5 * s, NAVY + (255,))
    im = sp.img()
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    paste_c(img, im, cx, cy)


def whale(w):
    k = ("whale", w)
    if k in _c:
        return _c[k]
    h = w * 0.33
    s = SS(w, h)
    c = (90, 100, 125, 255)
    s.rect(w * 0.05, h * 0.15, w * 0.55, h * 0.85, h * 0.3, c)
    s.thick([(w * 0.5, h * 0.5), (w * 0.8, h * 0.5), (w * 0.92, h * 0.45)], [h * 0.65, h * 0.4, h * 0.15], c)
    s.poly([(w * 0.9, h * 0.45), (w * 1.0, h * 0.15), (w * 0.96, h * 0.45), (w * 1.0, h * 0.8)], c)
    s.ell(w * 0.2, h * 0.38, w * 0.012, h * 0.04, (20, 20, 30, 255))
    s.line([(w * 0.06, h * 0.72), (w * 0.3, h * 0.8)], (60, 65, 85, 255), h * 0.04)
    _c[k] = s.img()
    return _c[k]


def sub(w, gt):
    s = SS(w, w * 0.8)
    c = (255, 210, 60, 255)
    s.rect(w * 0.05, w * 0.05, w * 0.95, w * 0.35, w * 0.15, c)
    s.rect(w * 0.42, w * 0.0, w * 0.58, w * 0.08, w * 0.02, c)
    s.ell(w * 0.5, w * 0.52, w * 0.18, w * 0.18, (200, 205, 220, 255))
    s.ell(w * 0.5, w * 0.52, w * 0.07, w * 0.07, (120, 210, 255, 255))
    s.rect(w * 0.45, w * 0.33, w * 0.55, w * 0.38, 2, (120, 120, 140, 255))
    return s.img()


# ------------------------------------------------------------------ scenes
def sc_card(img, seg, t, gt):
    hud(img, gt)
    d = depth_at(gt)
    p = back_out(prog(t, seg["dur"] - 1.2, 0.5))
    paste_c(img, diver(260, kick=gt * 5, tilt=-60), 960, 520 + 20 * math.sin(gt * 3))
    rr = random.Random(int(t * 4))
    dr = ImageDraw.Draw(img)
    for k in range(8):
        x = 980 + rr.uniform(-80, 80)
        y = 420 - ((t * 300 + k * 60) % 380)
        r = rr.uniform(6, 16)
        dr.ellipse((x - r, y - r, x + r, y + r), outline=WHITE, width=3)
    text(img, f"−{fmt(d)} m", 150, 960, 800, fill=WHITE, stroke=12, sfill=NAVY)
    if p > 0.03:
        text(img, seg["title"], 120 * p, 960, 300, fill=YELLOW, stroke=12, sfill=NAVY, rotate=-3)


def sc_o00(img, seg, t, gt):
    dr = ImageDraw.Draw(img)
    dr.rectangle((0, 0, W, 360), fill=(150, 215, 255))
    dr.ellipse((1560, 70, 1720, 230), fill=(255, 230, 110))
    pts = [(x, 360 + 14 * math.sin(x / 70 + gt * 2)) for x in range(0, W + 20, 20)]
    dr.polygon(pts + [(W, 380), (0, 380)], fill=(60, 160, 230))
    dr.line(pts, fill=WHITE, width=6)
    L.brand(img, W / 2, 90, gt, back_out(prog(t, 0.0, 0.5)))
    a = ease_out(prog(t, 0.3, 0.5))
    text(img, "Wie tief kannst du tauchen?", 84, W / 2, 230, fill=NAVY, alpha=a, stroke=6, sfill=WHITE, rotate=-2)
    paste_c(img, diver(300, kick=gt * 3, tilt=-20 * ap(seg, t, "tauchst", d=1.0)),
            700, 470 + 150 * ap(seg, t, "Meter", d=2.0))
    p11 = pop(seg, t, "11")
    if p11 > 0.02:
        text(img, "11 KM", 160 * p11, 1350, 620, fill=YELLOW, stroke=12, sfill=NAVY, rotate=-6)
        label(img, "BIS ZUM TIEFSTEN PUNKT", 1350, 740, min(1, p11))
    pl = ap(seg, t, "anhalten")
    if pl > 0.02:
        chip(img, "LUFT ANHALTEN!", 1350, 860, WHITE, pl, size=40)


def sc_o01(img, seg, t, gt):
    hud(img, gt)
    pe = ap(seg, t, "Erdatmosphäre")
    if pe > 0.02:
        chip(img, "+1 bar ALLE 10 METER", W / 2, 200, YELLOW, pe, size=40)
    for k, (word, dd, bar, rad) in enumerate((("1", "0 m", "1 bar", 130), ("2", "10 m", "2 bar", 103),
                                               ("3", "20 m", "3 bar", 90))):
        p = pop(seg, t, word)
        if p <= 0.02:
            continue
        cx = 620 + k * 420
        balloon(img, cx, 500, rad * min(1.1, p))
        text(img, dd, 50, cx, 760, fill=WHITE, stroke=5, sfill=NAVY)
        text(img, bar, 44, cx, 830, fill=YELLOW, stroke=5, sfill=NAVY)
    if pop(seg, t, "3") > 0.5:
        label(img, "LUFT WIRD ZUSAMMENGEDRÜCKT", W / 2, 910, ap(seg, t, "3", off=0.6))


def sc_o02(img, seg, t, gt):
    hud(img, gt)
    dr = ImageDraw.Draw(img)
    # ear: canal + drum
    cx, cy = 700, 520
    dr.rounded_rectangle((cx - 380, cy - 60, cx, cy + 60), 30, fill=(255, 200, 170))
    push = ap(seg, t, "Trommelfell", d=0.6) * (1 - 0.8 * ap(seg, t, "ausgleichen", d=0.8))
    dr.arc((cx - 40 - 60 * push, cy - 110, cx + 40 + 60 * push, cy + 110), -90, 90, fill=(255, 120, 140), width=14)
    for k in range(3):
        x = cx - 330 + ((gt * 200 + k * 110) % 300)
        dr.line((x, cy, x + 50, cy), fill=WHITE, width=8)
        dr.polygon([(x + 50, cy - 16), (x + 50, cy + 16), (x + 72, cy)], fill=WHITE)
    label(img, "TROMMELFELL", cx + 20, cy + 160, ap(seg, t, "Trommelfell"), col=YELLOW)
    pa = ap(seg, t, "ausgleichen")
    if pa > 0.02:
        chip(img, "DRUCK AUSGLEICHEN", cx - 160, 300, GREEN, pa, size=36)
    pl = ap(seg, t, "Lunge", d=0.4)
    if pl > 0.02:
        k = 1 - 0.29 * ease_io(prog(t, tw(seg, "halb") - 0.3, 1.0))
        lungs(img, 1450, 560, k)
        label(img, "LUNGE", 1450, 300, pl, col=(255, 160, 180))
        if k < 0.9:
            text(img, "½ VOLUMEN", 60, 1450, 820, fill=YELLOW, stroke=6, sfill=NAVY)


def sc_o03(img, seg, t, gt):
    hud(img, gt)
    rows = [("Rot", (235, 50, 60), 10, "≈ 10 m"), ("Orange", (255, 150, 40), 40, "≈ 40 m"),
            ("Gelb", (255, 225, 60), 100, "< 100 m"), ("Blau", (60, 140, 255), 400, "bleibt")]
    x0 = 420
    for k, (w_, col, dmax, lab) in enumerate(rows):
        p = ap(seg, t, w_, d=0.6)
        if p <= 0.02:
            continue
        y = 280 + k * 150
        wbar = 1100 * min(1, math.log10(1 + dmax) / math.log10(401)) * p
        rrect(img, (x0, y - 45, x0 + wbar, y + 45), 30, col + (255,))
        text(img, lab, 44, x0 + wbar + 120, y, fill=WHITE, stroke=5, sfill=NAVY)
    label(img, "SO TIEF KOMMT DIE FARBE", 960, 200, ap(seg, t, "Farben"), col=YELLOW)
    # fish losing its red
    fade = ap(seg, t, "Rot", d=1.5)
    col = lerpc((235, 60, 60), (70, 90, 120), fade)
    fish(img, 1650, 860, 0.9, col)


def sc_o04(img, seg, t, gt):
    hud(img, gt)
    wob = ap(seg, t, "Rausch", d=1.0)
    paste_c(img, diver(330, kick=gt * 3, tilt=12 * math.sin(gt * 1.5) * wob), 820, 560 + 10 * math.sin(gt * 2))
    if wob > 0.02:
        for k in range(5):
            an = gt * 3 + k * 2 * math.pi / 5
            x, y = 960 + 120 * math.cos(an), 430 + 40 * math.sin(an)
            text(img, "★", 44, x, y, fill=YELLOW, alpha=wob)
    pn = ap(seg, t, "Stickstoff")
    if pn > 0.02:
        chip(img, "STICKSTOFF (N2)", 1450, 300, WHITE, pn, size=38)
    pt = ap(seg, t, "Tiefenrausch")
    if pt > 0.02:
        L.stamp(img, "TIEFENRAUSCH", t, tw(seg, "Tiefenrausch") - 0.1, 1450, 520, size=90, rot=-6)
    pg = pop(seg, t, "getrunken")
    if pg > 0.02:
        dr = ImageDraw.Draw(img)
        cx, cy, s = 1450, 760, min(1.2, pg)
        dr.polygon([(cx - 80 * s, cy - 70 * s), (cx + 80 * s, cy - 70 * s), (cx, cy + 20 * s)], fill=(120, 220, 255))
        dr.line((cx, cy + 20 * s, cx, cy + 90 * s), fill=WHITE, width=8)
        dr.line((cx - 50 * s, cy + 90 * s, cx + 50 * s, cy + 90 * s), fill=WHITE, width=8)
        dr.ellipse((cx + 30 * s, cy - 110 * s, cx + 60 * s, cy - 80 * s), fill=(90, 200, 90))


def sc_o05(img, seg, t, gt):
    hud(img, gt)
    sp = L.E.person_sprite(520, ORANGE)
    paste_c(img, sp, 760, 880, 1.0, anchor="b")
    pr = ap(seg, t, "Tauchreflex")
    if pr > 0.02:
        L.stamp(img, "TAUCHREFLEX", t, tw(seg, "Tauchreflex") - 0.1, 1400, 260, size=90, rot=-5)
    ph = ap(seg, t, "Herz")
    if ph > 0.02:
        rate = 6.0 - 3.2 * ease_io(prog(t, tw(seg, "langsamer") - 0.2, 1.5))
        beat = 1 + 0.25 * max(0, math.sin(gt * rate)) ** 10
        paste_c(img, L.E.heart_sprite(70 * beat), 775, 560)
        chip(img, "HERZ SCHLÄGT LANGSAMER", 1400, 480, RED, ph, size=34)
    pb = ap(seg, t, "Blut")
    if pb > 0.02:
        dr = ImageDraw.Draw(img)
        for (x0, y0) in ((640, 560), (900, 560), (720, 840), (800, 840)):
            ph2 = (gt * 0.8) % 1
            x = x0 + (775 - x0) * ph2
            y = y0 + (600 - y0) * ph2
            dr.ellipse((x - 14, y - 14, x + 14, y + 14), fill=(220, 40, 60))
        chip(img, "BLUT ZUR KÖRPERMITTE", 1400, 620, WHITE, pb, size=34)
    po = ap(seg, t, "Sauerstoff")
    if po > 0.02:
        chip(img, "O2 SPAREN", 1400, 760, GREEN, po, size=40)


def sc_o06(img, seg, t, gt):
    hud(img, gt)
    x0, x1 = 560, 1100
    zones = [("SONNENLICHT", 0, 200, (90, 190, 240)), ("DÄMMERUNG", 200, 1000, (25, 70, 150)),
             ("MITTERNACHT", 1000, 11000, (5, 10, 30))]
    for name, a_, b_, col in zones:
        y0, y1 = gy(a_), gy(b_)
        rrect(img, (x0, y0, x1, y1), 12, col + (255,), outline=(255, 255, 255, 120), width=3)
        text(img, name, 34, (x0 + x1) / 2, (y0 + y1) / 2, fill=WHITE, path=FONT_XB, stroke=4, sfill=NAVY)
    y = gy(200)
    ImageDraw.Draw(img).line((x0 - 40, y, x1 + 60, y), fill=YELLOW, width=6)
    label(img, "← DU BIST HIER", x1 + 200, y, col=YELLOW, size=34)
    pp = ap(seg, t, "Pflanzen")
    if pp > 0.02:
        dr = ImageDraw.Draw(img)
        for k in range(5):
            x = 1520 + k * 70
            dr.line([(x + 15 * math.sin(gt * 2 + j * 0.5 + k), 560 - j * 30) for j in range(8)], fill=(80, 200, 110),
                    width=10)
        label(img, "LICHT REICHT KAUM", 1660, 610, pp)
    pk = ap(seg, t, "kälter")
    if pk > 0.02:
        dr = ImageDraw.Draw(img)
        cx, top = 1520, 700
        dr.rounded_rectangle((cx - 22, top, cx + 22, top + 150), 22, fill=WHITE)
        dr.ellipse((cx - 40, top + 130, cx + 40, top + 210), fill=WHITE)
        dr.ellipse((cx - 28, top + 142, cx + 28, top + 198), fill=(90, 170, 255))
        lvl = 120 - 80 * ease_io(prog(t, tw(seg, "kälter"), 1.5))
        dr.rectangle((cx - 10, top + 150 - lvl, cx + 10, top + 160), fill=(90, 170, 255))
        label(img, "KÄLTER", cx + 130, top + 120, pk, col=(150, 210, 255))


def sc_o07(img, seg, t, gt):
    hud(img, gt)
    dr = ImageDraw.Draw(img)
    dr.line((960, 140, 960, 920), fill=(230, 230, 240), width=6)
    k = ease_io(prog(t, tw(seg, "Tauchgang") - 0.3, 6.0))
    y = 220 + 600 * k
    dr.rounded_rectangle((900, y - 40, 1020, y + 40), 14, fill=(200, 60, 60))
    paste_c(img, diver(200, kick=0, tilt=-90), 960, y + 110)
    p = pop(seg, t, "253")
    if p > 0.02:
        text(img, "253 m", 150 * p, 1450, 380, fill=YELLOW, stroke=12, sfill=NAVY, rotate=-5)
        label(img, "MIT 1 ATEMZUG (2012)", 1450, 500, min(1, p))
    ps = ap(seg, t, "Tauchschlitten")
    if ps > 0.02:
        chip(img, "TAUCHSCHLITTEN", 600, 300, WHITE, ps, size=36)
    pt = ap(seg, t, "Taucherkrankheit")
    if pt > 0.02:
        tx, ty, r = 1450, 720, 90
        dr.polygon([(tx, ty - r), (tx + r * 1.1, ty + r * 0.8), (tx - r * 1.1, ty + r * 0.8)], fill=RED,
                   outline=WHITE, width=6)
        text(img, "!", 100, tx, ty + 12, fill=WHITE)
        label(img, "TAUCHERKRANKHEIT", tx, ty + 140, pt, col=(255, 140, 140))


def glow(img, x, y, r, col, a):
    lay = Image.new("RGBA", (int(4 * r), int(4 * r)))
    dl = ImageDraw.Draw(lay)
    for k in range(6, 0, -1):
        rr = r * k / 3
        dl.ellipse((2 * r - rr, 2 * r - rr, 2 * r + rr, 2 * r + rr), fill=col + (int(40 * a),))
    dl.ellipse((2 * r - r * 0.4, 2 * r - r * 0.4, 2 * r + r * 0.4, 2 * r + r * 0.4), fill=(255, 255, 255, int(255 * a)))
    img.alpha_composite(lay, (int(x - 2 * r), int(y - 2 * r)))


def sc_o08(img, seg, t, gt):
    hud(img, gt)
    pl = ap(seg, t, "leuchten", d=0.8)
    # anglerfish
    ax, ay = 1150, 600
    dr = ImageDraw.Draw(img)
    dr.ellipse((ax - 170, ay - 120, ax + 170, ay + 120), fill=(40, 45, 70))
    dr.polygon([(ax + 150, ay), (ax + 280, ay - 90), (ax + 280, ay + 90)], fill=(40, 45, 70))
    dr.chord((ax - 175, ay - 30, ax - 30, ay + 100), 20, 200, fill=(15, 15, 25))
    for k in range(6):
        x = ax - 160 + k * 22
        dr.polygon([(x, ay + 10), (x + 8, ay + 40), (x + 16, ay + 10)], fill=WHITE)
    dr.ellipse((ax - 80, ay - 60, ax - 50, ay - 30), fill=(200, 230, 255))
    dr.line([(ax - 40, ay - 110), (ax - 120, ay - 260), (ax - 230, ay - 230)], fill=(60, 65, 90), width=8)
    glow(img, ax - 235, ay - 225, 26, (120, 255, 220), 0.4 + 0.6 * (0.5 + 0.5 * math.sin(gt * 3)))
    if pl > 0.02:
        rr = random.Random(5)
        for k in range(18):
            x, y = rr.uniform(500, 1850), rr.uniform(200, 880)
            tw_ = 0.5 + 0.5 * math.sin(gt * rr.uniform(1, 4) + k)
            glow(img, x, y, rr.uniform(6, 14), rr.choice([(120, 255, 220), (120, 160, 255), (255, 120, 220)]),
                 pl * tw_)
        # jellyfish
        jx, jy = 700, 420 + 20 * math.sin(gt)
        dr = ImageDraw.Draw(img)
        dr.chord((jx - 90, jy - 70, jx + 90, jy + 70), 180, 360, fill=(150, 120, 255))
        for k in range(5):
            x = jx - 70 + k * 35
            dr.line([(x + 10 * math.sin(gt * 2 + j * 0.6 + k), jy + j * 25) for j in range(8)], fill=(190, 160, 255),
                    width=5)
    pm = ap(seg, t, "Mitternachtszone")
    if pm > 0.02:
        chip(img, "MITTERNACHTSZONE", 960, 200, (150, 170, 255), pm, size=40)
    pk = ap(seg, t, "stockdunkel")
    if pk > 0.02 and pl < 0.02:
        label(img, "KEIN SONNENLICHT MEHR", 960, 880, pk, col=YELLOW)


def sc_o09(img, seg, t, gt):
    hud(img, gt)
    k = ease_io(prog(t, 0.2, seg["dur"]))
    wsp = whale(760).rotate(-28, resample=Image.BICUBIC, expand=True)
    paste_c(img, wsp, 900 + 200 * k, 380 + 260 * k)
    ps = ap(seg, t, "Tintenfischen")
    if ps > 0.02:
        dr = ImageDraw.Draw(img)
        sx, sy = 1500, 800
        dr.ellipse((sx - 50, sy - 90, sx + 50, sy + 40), fill=(220, 110, 90))
        for j in range(6):
            x = sx - 45 + j * 18
            dr.line([(x + 10 * math.sin(gt * 3 + i * 0.7 + j), sy + 30 + i * 20) for i in range(6)], fill=(220, 110, 90),
                    width=8)
        label(img, "TINTENFISCH", sx, sy - 130, ps)
    p2 = pop(seg, t, "2000")
    if p2 > 0.02:
        text(img, "> 2.000 m", 120 * p2, 1400, 300, fill=YELLOW, stroke=10, sfill=NAVY, rotate=-5)
        label(img, "POTTWAL · 1 ATEMZUG", 1400, 410, min(1, p2))


def sc_o10(img, seg, t, gt):
    hud(img, gt)
    dr = ImageDraw.Draw(img)
    dr.polygon([(0, 900), (W, 860), (W, H), (0, H)], fill=(40, 35, 30))
    # wreck bow
    pts = [(560, 880), (620, 640), (1160, 600), (1260, 760), (1240, 880)]
    dr.polygon(pts, fill=(70, 50, 45))
    dr.rectangle((760, 540, 900, 610), fill=(60, 45, 40))
    for k in range(6):
        dr.ellipse((680 + k * 80, 690, 700 + k * 80, 710), fill=(30, 25, 25))
    dr.line((1160, 600, 1060, 300), fill=(60, 45, 40), width=10)
    label(img, "TITANIC", 900, 470, ap(seg, t, "Titanic"), col=YELLOW, size=44)
    p380 = pop(seg, t, "380")
    if p380 > 0.02:
        text(img, "× 380", 130 * p380, 1500, 300, fill=YELLOW, stroke=10, sfill=NAVY, rotate=-5)
        label(img, "DRUCK WIE AN DER OBERFLÄCHE", 1500, 400, min(1, p380))
    p390 = ap(seg, t, "390")
    if p390 > 0.02:
        chip(img, "≈ 390 kg PRO cm²", 1500, 520, WHITE, p390, size=40)
    pk = pop(seg, t, "Konzertflügel")
    if pk > 0.02:
        cx, cy, s = 1500, 760, min(1.2, pk)
        dr.rounded_rectangle((cx - 40 * s, cy + 30 * s, cx + 40 * s, cy + 140 * s), int(30 * s), fill=(255, 200, 170))
        dr.rounded_rectangle((cx - 26 * s, cy + 36 * s, cx + 26 * s, cy + 80 * s), int(14 * s), fill=(255, 230, 220))
        dr.polygon([(cx - 120 * s, cy + 25 * s), (cx + 140 * s, cy + 25 * s), (cx + 100 * s, cy - 50 * s),
                    (cx - 40 * s, cy - 80 * s), (cx - 120 * s, cy - 40 * s)], fill=(20, 20, 25))
        for k2 in range(8):
            dr.rectangle((cx - 110 * s + k2 * 24 * s, cy + 5 * s, cx - 92 * s + k2 * 24 * s, cy + 22 * s), fill=WHITE)
        label(img, "KONZERTFLÜGEL AUF DEM DAUMEN", cx, cy + 190, min(1, pk))


def sc_o11(img, seg, t, gt):
    hud(img, gt)
    dr = ImageDraw.Draw(img)
    dr.polygon([(300, 300), (900, 900), (1100, 900), (1800, 300), (1800, H), (300, H)], fill=(30, 25, 30))
    label(img, "MARIANENGRABEN", 1000, 250, ap(seg, t, "Marianengraben"), col=YELLOW, size=44)
    p1000 = pop(seg, t, "1000")
    if p1000 > 0.02:
        text(img, "> 1.000 bar", 100 * p1000, 1530, 360, fill=YELLOW, stroke=10, sfill=NAVY, rotate=-5)
    pe = ap(seg, t, "Elefanten")
    if pe > 0.02:
        n = int(1 + 99 * ease_out(prog(t, tw(seg, "Elefanten") - 0.2, 1.4)))
        for i in range(n):
            x = 520 + (i % 20) * 34
            y = 520 - (i // 20) * 34
            dr.ellipse((x - 14, y - 10, x + 14, y + 10), fill=(170, 170, 190))
            dr.ellipse((x + 8, y - 14, x + 20, y), fill=(170, 170, 190))
        text(img, f"{n} ×", 70, 720, 600, fill=WHITE, stroke=6, sfill=NAVY)
        label(img, "ELEFANTEN AUF DEINEM KOPF", 880, 660, pe)
    pl = ap(seg, t, "Flohkrebse")
    if pl > 0.02:
        for k in range(5):
            x = 920 + k * 40 + 20 * math.sin(gt * 2 + k)
            y = 880 - 6 * abs(math.sin(gt * 5 + k))
            dr.ellipse((x - 16, y - 8, x + 16, y + 8), fill=(255, 200, 180))
            dr.line((x - 16, y, x - 26, y - 10), fill=(255, 200, 180), width=3)
        chip(img, "LEBEN! FLOHKREBSE", 1450, 760, GREEN, pl, size=36)


def sc_o12(img, seg, t, gt):
    hud(img, gt)
    dr = ImageDraw.Draw(img)
    dr.polygon([(0, 900), (W, 880), (W, H), (0, H)], fill=(30, 25, 30))
    k = ease_io(prog(t, 0.0, 3.0))
    sy = 300 + 330 * k
    for j in range(2):
        lay = Image.new("RGBA", (W, H))
        ImageDraw.Draw(lay).polygon([(1000 + j * 60, sy + 200), (900 + j * 60, sy + 600), (1150 + j * 60, sy + 600)],
                                    fill=(255, 250, 200, 40))
        img.alpha_composite(lay)
    paste_c(img, sub(420, gt), 1050, sy)
    p60 = pop(seg, t, "1960")
    if p60 > 0.02:
        text(img, "1960", 130 * p60, 1550, 330, fill=YELLOW, stroke=10, sfill=NAVY, rotate=-5)
        label(img, "ERSTE FAHRT GANZ NACH UNTEN", 1550, 430, min(1, p60))
    ps = ap(seg, t, "Stahl")
    if ps > 0.02:
        chip(img, "DICKE STAHLKUGEL", 1550, 560, WHITE, ps, size=38)
    pc = ap(seg, t, "Chance")
    if pc > 0.02:
        L.stamp(img, "KEINE CHANCE", t, tw(seg, "Chance") - 0.1, 560, 600, size=80, rot=-8)


def sc_o13(img, seg, t, gt):
    hud(img, gt)
    t_r = wt(seg, "Rate", 1)
    fo = 1 - ease_io(prog(t, t_r - 0.4, 0.35))
    for k, (w_, txt, col) in enumerate((("dunkler", "DUNKLER", (150, 170, 255)), ("kälter", "KÄLTER", (130, 210, 255)),
                                        ("brutaler", "BRUTALER", RED))):
        p = pop(seg, t, w_)
        if p > 0.02:
            text(img, txt, 92 * min(1.15, p), 500 + k * 470, 330, fill=col, stroke=10, sfill=NAVY, alpha=fo, rotate=-4)
    pk = pop(seg, t, "Kommentare")
    if pk > 0.02 and fo > 0.02:
        cx, cy, s = 960, 620, min(1.1, pk) * fo
        rrect(img, (cx - 330 * s, cy - 100 * s, cx + 330 * s, cy + 100 * s), int(50 * s), (255, 255, 255, 245))
        text(img, "Hättest du's gewusst?", 50 * s, cx, cy - 22 * s, fill=NAVY)
        text(img, "Ja / Nein", 50 * s, cx, cy + 45 * s, fill=(255, 120, 0))
    pa = ap(seg, t, "abonnier")
    if pa > 0.02:
        sc = back_out(prog(t, tw(seg, "abonnier") - 0.1, 0.5)) * (1 + 0.05 * math.sin(gt * 6))
        rrect(img, (W / 2 - 250 * sc, 860 - 62 * sc, W / 2 + 250 * sc, 860 + 62 * sc), int(62 * sc), (230, 30, 40, 255))
        text(img, "ABONNIEREN", 54 * sc, W / 2, 862, fill=WHITE)
    if t > t_r - 0.1:
        L.stamp(img, "RATE MAL!", t, t_r - 0.1, W / 2, 520, size=170, rot=-6)
        L.confetti(img, t, t_r)


DRAW = {k: v for k, v in globals().items() if k.startswith("sc_o")}


def draw(img, seg, t, gt):
    if seg["kind"] == "card":
        sc_card(img, seg, t, gt)
    else:
        DRAW["sc_" + seg["key"]](img, seg, t, gt)


SFX = {
    "o00": [("tauchst", "whoosh", 0.10), ("11", "thump", 0.15), ("anhalten", "pop", 0.10)],
    "o01": [("Erdatmosphäre", "pop", 0.10), ("1", "pop", 0.12), ("2", "pop", 0.12), ("3", "pop", 0.12)],
    "o02": [("Trommelfell", "thump", 0.12), ("ausgleichen", "ding", 0.08), ("Lunge", "pop", 0.10),
            ("halb", "rise", 0.08)],
    "o03": [("Farben", "pop", 0.08), ("Rot", "pop", 0.10), ("Orange", "pop", 0.10), ("Gelb", "pop", 0.10),
            ("Blau", "ding", 0.08)],
    "o04": [("Stickstoff", "pop", 0.10), ("Rausch", "glitch", 0.08), ("Tiefenrausch", "thump", 0.14),
            ("getrunken", "pop", 0.10)],
    "o05": [("Tauchreflex", "thump", 0.14), ("Herz", "heart", 0.16), ("Blut", "whoosh", 0.08),
            ("Sauerstoff", "ding", 0.08)],
    "o06": [("Sonnenlicht-Zone", "ding", 0.08), ("Pflanzen", "pop", 0.10), ("kälter", "pop", 0.10)],
    "o07": [("Tauchgang", "whoosh", 0.10), ("253", "thump", 0.15), ("Tauchschlitten", "pop", 0.10),
            ("Taucherkrankheit", "alarm", 0.08)],
    "o08": [("stockdunkel", "glitch", 0.06), ("Mitternachtszone", "thump", 0.12), ("leuchten", "ding", 0.10)],
    "o09": [("Pottwale", "whoosh", 0.10), ("Tintenfischen", "pop", 0.10), ("2000", "thump", 0.15)],
    "o10": [("Titanic", "thump", 0.14), ("380", "pop", 0.12), ("390", "pop", 0.10), ("Konzertflügel", "thump", 0.14)],
    "o11": [("Marianengraben", "thump", 0.15), ("1000", "pop", 0.12), ("Elefanten", "rise", 0.10),
            ("Flohkrebse", "ding", 0.10)],
    "o12": [("1960", "thump", 0.14), ("Stahl", "pop", 0.10), ("Chance", "thump", 0.14)],
    "o13": [("dunkler", "pop", 0.12), ("kälter", "pop", 0.12), ("brutaler", "thump", 0.14),
            ("Kommentare", "pop", 0.12), ("abonnier", "pop", 0.12), ("Rate", "chime", 0.12)],
}


def events():
    ev = []
    for s in L.SEGS:
        st = s["start"]
        if s["kind"] == "card":
            ev += [(st, "whoosh", 0.12), (st + 0.3, "pop", 0.06), (st + 0.8, "pop", 0.06), (st + 1.3, "pop", 0.06),
                   (st + s["dur"] - 1.2, "thump", 0.15)]
            continue
        for w, kind, g in SFX.get(s["key"], []):
            try:
                ev.append((st + wt(s, w) - 0.08, kind, g))
            except KeyError:
                print("SFX word missing:", s["key"], w)
    return ev


L.setup(here=HERE, out="rate_mal_tiefsee.mp4", plan=plan, draw=draw, events=events)

if __name__ == "__main__":
    L.main()

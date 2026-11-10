#!/usr/bin/env python3
"""Rate mal: Was passiert mit deinem Körper, wenn du ein Jahr im Weltall lebst? – 7 Fragen (Querformat, ~5 Min)."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import longlib as L  # noqa: E402
from longlib import (W, H, SS, NAVY, YELLOW, WHITE, GREEN, RED, BLUE, ORANGE, SKIN, PURPLE, FONT_XB,  # noqa: E402
                     back_out, ease_io, ease_out, prog, paste_c, rrect, text, text_w, wt)

QS = [
    dict(q="Wirst du im All größer, kleiner oder bleibst du gleich groß?",
         opts=["größer", "kleiner", "gleich groß"], right=0, ow=["größer", "kleiner", "gleich"],
         facts=[("BANDSCHEIBEN DEHNEN SICH", "Bandscheiben"), ("BIS ZU +3 %", "3"), ("≈ +5 cm BEI 1,80 m", "5")]),
    dict(q="Was passiert mit deinem Gesicht im All?",
         opts=["schmaler", "aufgedunsen", "bleibt gleich"], right=1, ow=["schmaler", "aufgedunsen", "bleibt"],
         facts=[("FLÜSSIGKEIT WANDERT NACH OBEN", "Flüssigkeit"), ("RUNDES GESICHT, DÜNNE BEINE", "rundes"),
                ("ESSEN SCHMECKT FAD", "fad")]),
    dict(q="Wie viel Knochenmasse verlierst du im All – pro Monat?",
         opts=["0 %", "1 – 1,5 %", "10 %"], right=1, ow=["Gar", "etwa", "ganze"],
         facts=[("1 – 1,5 % PRO MONAT", "Prozent"), ("VOR ALLEM BEINE & HÜFTE", "Beinen"),
                ("KEINE LAST = ABBAU", "tragen")]),
    dict(q="Wie lange machen Astronauten auf der Raumstation Sport?",
         opts=["10 Min.\npro Tag", "1 Std.\npro Woche", "ca. 2 Std.\ntäglich"], right=2, ow=["10", "1", "rund"],
         facts=[("CA. 2 STUNDEN TÄGLICH", "2"), ("LAUFBAND · RAD · KRAFT", "Laufband"),
                ("OHNE TRAINING: BIS −20 %", "20")]),
    dict(q="Wie viele Sonnenaufgänge siehst du auf der Raumstation an einem Tag?",
         opts=["1", "4", "16"], right=2, ow=["1", "4", "16"],
         facts=[("≈ 28.000 KM/H", "28.000"), ("1 RUNDE ≈ 90 MINUTEN", "90"), ("SCHLAF NACH FESTER UHRZEIT", "Uhrzeit")]),
    dict(q="Was sehen manche Astronauten, wenn sie im All die Augen schließen?",
         opts=["komplett\nschwarz", "Lichtblitze", "bunte\nFarben"], right=1, ow=["Komplett", "Lichtblitze", "bunte"],
         facts=[("SCHON BEI APOLLO", "Apollo-Astronauten"), ("VERMUTET: KOSMISCHE STRAHLUNG", "Kosmische"),
                ("BIS HEUTE NICHT GANZ GEKLÄRT", "geklärt")]),
    dict(q="340 Tage im All, der Zwilling auf der Erde: Haben sich die Gene dauerhaft verändert?",
         opts=["Ja,\nkomplett", "Nein,\ngar nicht", "das meiste\nging zurück"], right=2, ow=["Ja", "Nein", "Das"],
         facts=[("GEN-AKTIVITÄT VERÄNDERT", "Aktivität"), ("> 90 % NACH 6 MONATEN NORMAL", "90"),
                ("BRUDER MARK = VERGLEICH", "Mark")]),
]

CD = 6.0          # countdown seconds
REVEAL = 1.0      # silent reveal before the answer voice

plan = [dict(key="intro", kind="intro", audio="c00", pre=0.3, post=0.6)]
for i in range(7):
    n = i + 1
    plan += [dict(key=f"f{n}", kind="frage", qi=i, dur=1.6),
             dict(key=f"q{n}", kind="q", qi=i, audio=f"q{n}", pre=0.15, post=0.35, xf=False),
             dict(key=f"cd{n}", kind="cd", qi=i, dur=CD, xf=False),
             dict(key=f"a{n}", kind="a", qi=i, audio=f"a{n}", pre=REVEAL, post=1.4, xf=False)]
plan.append(dict(key="outro", kind="outro", audio="outro", pre=0.4, post=2.6))


# ------------------------------------------------------------------ sprites
_cache = {}


def astronaut(h, leg=0.0, arm=0.0, key=None):
    k = ("astro", int(h), round(leg, 2), round(arm, 2))
    if k in _cache:
        return _cache[k]
    w = h * 0.62
    s = SS(w + 8, h + 8)
    cx = (w + 8) / 2
    suit, shade = (245, 246, 252, 255), (200, 205, 222, 255)
    # backpack
    s.rect(cx - w * 0.34, h * 0.30, cx + w * 0.34, h * 0.62, w * 0.08, (170, 176, 196, 255))
    # legs (swing)
    for sgn in (-1, 1):
        a = sgn * leg * 0.5
        hip = (cx + sgn * w * 0.13, h * 0.66)
        foot = (hip[0] + math.sin(a) * h * 0.30, hip[1] + math.cos(a) * h * 0.30)
        s.thick([hip, foot], [w * 0.22, w * 0.20], suit)
        s.ell(foot[0] + w * 0.04, foot[1], w * 0.14, w * 0.08, (110, 116, 140, 255))
    # body
    s.rect(cx - w * 0.28, h * 0.32, cx + w * 0.28, h * 0.72, w * 0.14, suit)
    s.rect(cx - w * 0.14, h * 0.42, cx + w * 0.14, h * 0.52, w * 0.03, (90, 160, 255, 255))
    s.ell(cx - w * 0.07, h * 0.47, w * 0.025, w * 0.025, (255, 90, 90, 255))
    s.ell(cx + w * 0.05, h * 0.47, w * 0.025, w * 0.025, (255, 226, 60, 255))
    # arms
    for sgn in (-1, 1):
        a = 0.5 + arm * (0.9 if sgn > 0 else 0.6)
        sh = (cx + sgn * w * 0.27, h * 0.37)
        hand = (sh[0] + sgn * math.sin(a) * h * 0.22, sh[1] + math.cos(a) * h * 0.22)
        s.thick([sh, hand], [w * 0.17, w * 0.15], shade if sgn < 0 else suit)
        s.ell(hand[0], hand[1], w * 0.08, w * 0.08, (110, 116, 140, 255))
    # helmet
    s.ell(cx, h * 0.19, w * 0.30, h * 0.17, suit)
    s.ell(cx, h * 0.20, w * 0.22, h * 0.115, (40, 70, 140, 255))
    s.ell(cx - w * 0.08, h * 0.16, w * 0.06, h * 0.035, (160, 200, 255, 200))
    img = s.img()
    if len(_cache) > 400:
        _cache.clear()
    _cache[k] = img
    return img


def earth_sprite(r):
    k = ("earth", r)
    if k in _cache:
        return _cache[k]
    s = SS(2 * r + 40, 2 * r + 40)
    c = r + 20
    s.ell(c, c, r + 16, r + 16, (90, 170, 255, 70))
    s.ell(c, c, r, r, (40, 120, 230, 255))
    rr = random.Random(5)
    for _ in range(11):
        a, q = rr.uniform(0, 6.28), rr.uniform(0.1, 0.75) * r
        x, y = c + q * math.cos(a), c + q * math.sin(a)
        w_, h_ = rr.uniform(0.14, 0.3) * r, rr.uniform(0.09, 0.2) * r
        s.ell(x, y, w_, h_, (70, 185, 95, 255))
    for _ in range(6):
        a, q = rr.uniform(0, 6.28), rr.uniform(0.1, 0.8) * r
        x, y = c + q * math.cos(a), c + q * math.sin(a)
        s.ell(x, y, rr.uniform(0.1, 0.25) * r, 0.05 * r, (255, 255, 255, 170))
    img = s.img()
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse((20 - 16, 20 - 16, 20 + 2 * r + 16, 20 + 2 * r + 16), fill=255)
    a = Image.fromarray(__import__("numpy").minimum(__import__("numpy").array(img.getchannel("A")),
                                                     __import__("numpy").array(m)))
    img.putalpha(a)
    _cache[k] = img
    return img


def iss_sprite(s=1.0):
    k = ("iss", s)
    if k in _cache:
        return _cache[k]
    sp = SS(160 * s, 70 * s)
    sp.rect(10 * s, 8 * s, 55 * s, 62 * s, 3, (90, 150, 255, 255))
    sp.rect(105 * s, 8 * s, 150 * s, 62 * s, 3, (90, 150, 255, 255))
    sp.rect(50 * s, 31 * s, 110 * s, 39 * s, 2, (220, 220, 230, 255))
    sp.rect(68 * s, 22 * s, 92 * s, 48 * s, 6 * s, (240, 240, 250, 255))
    _cache[k] = sp.img()
    return _cache[k]


def person(h, col):
    k = ("p", int(h), col)
    if k not in _cache:
        _cache[k] = L.E.person_sprite(h, col)
    return _cache[k]


# ------------------------------------------------------------------ small helpers
def chip(img, s, cx, cy, col, a, size=30, maxw=520):
    w = text_w(s, size, FONT_XB) + 54
    if w > maxw:
        size = size * (maxw - 54) / (w - 54)
    L.pill(img, s, cx, cy, col, a, size=size)


def ap(seg, t, word, n=1, d=0.35, off=-0.1):
    try:
        return ease_out(prog(t, wt(seg, word, n) + off, d))
    except KeyError:
        return 0.0


def tw(seg, word, n=1):
    return wt(seg, word, n)


def dashed(d, x0, y, x1, col, w=4, dash=16):
    x = x0
    while x < x1:
        d.line((x, y, min(x1, x + dash), y), fill=col, width=w)
        x += dash * 2


def clock(img, cx, cy, r, frac, a=1.0, col=YELLOW):
    if a <= 0.02:
        return
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255), outline=NAVY, width=8)
    for k in range(12):
        an = k / 12 * 2 * math.pi
        d.line((cx + 0.78 * r * math.sin(an), cy - 0.78 * r * math.cos(an), cx + 0.9 * r * math.sin(an),
                cy - 0.9 * r * math.cos(an)), fill=NAVY, width=5)
    an = frac * 2 * math.pi
    d.line((cx, cy, cx + 0.72 * r * math.sin(an), cy - 0.72 * r * math.cos(an)), fill=RED, width=8)
    an2 = frac * 2 * math.pi / 12
    d.line((cx, cy, cx + 0.5 * r * math.sin(an2), cy - 0.5 * r * math.cos(an2)), fill=NAVY, width=10)
    d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=NAVY)


# ------------------------------------------------------------------ illustrations (answer side, x 640..1880)
def ill_height(img, seg, t, gt, a):
    d = ImageDraw.Draw(img)
    disc = ease_io(prog(t, tw(seg, "Bandscheiben") - 0.2, 1.4))
    back = ease_io(prog(t, tw(seg, "Zurück"), 1.2))
    disc *= (1 - back)
    # spine column
    x, y = 930, 830
    text(img, "WIRBELSÄULE", 34, x, 300, fill=YELLOW, path=FONT_XB, stroke=4, sfill=NAVY, alpha=a)
    gap = 10 + 18 * disc
    for k in range(7):
        h_ = 44
        rrect(img, (x - 85, y - h_, x + 85, y), 20, (240, 228, 205, int(255 * a)), outline=(170, 140, 110, 255),
              width=4)
        y -= h_
        if k < 6:
            rrect(img, (x - 70, y - gap, x + 70, y), int(gap / 2), (90, 170, 255, int(255 * a)))
            y -= gap
    if disc > 0.05:
        for k in (-1, 1):
            d.line((x + 130 * k, 430, x + 130 * k, 790), fill=YELLOW, width=6)
        d.polygon([(x - 130, 410), (x - 145, 440), (x - 115, 440)], fill=YELLOW)
        d.polygon([(x + 130, 410), (x + 115, 440), (x + 145, 440)], fill=YELLOW)
    # two astronauts: Erde vs All
    base = 820
    h0 = 470
    grow = ease_out(prog(t, tw(seg, "größer") - 0.2, 1.0)) * (1 - back)
    h1 = h0 * (1 + 0.03 * grow)
    for cx, hh, lab, col in ((1340, h0, "AUF DER ERDE", WHITE), (1640, h1, "IM ALL", YELLOW)):
        bob = 10 * math.sin(gt * 2) * (1 - back) if lab == "IM ALL" else 0
        paste_c(img, astronaut(hh), cx, base + bob, a, anchor="b")
        text(img, lab, 30, cx, base + 40, fill=col, path=FONT_XB, stroke=4, sfill=NAVY, alpha=a)
    d.line((1180, base + 4, 1800, base + 4), fill=(255, 255, 255, 120), width=3)
    if grow > 0.05:
        dashed(d, 1240, base - h0 - 4, 1760, (255, 255, 255), 3)
        dashed(d, 1240, base - h1 - 4 + 10 * math.sin(gt * 2) * (1 - back), 1760, YELLOW, 3)
        text(img, "+3 %", 46, 1810, base - h0 - 40, fill=YELLOW, stroke=6, sfill=NAVY, alpha=grow * a)
    if back > 0.05:
        L.stamp(img, "WIEDER NORMAL", t, tw(seg, "Zurück") + 0.3, 1490, 300, size=56, rot=-5)


def head(img, cx, cy, r, puff, a, stuffy=0.0):
    s = SS(2 * r * 1.35 + 20, 2 * r * 1.2 + 20)
    c = (r * 1.35 + 10, r * 1.2 + 10)
    rx, ry = r * (1 + 0.28 * puff), r * (1 + 0.06 * puff)
    s.ell(c[0], c[1], rx, ry, (255, 200, 160, 255))
    s.ell(c[0], c[1] - ry * 0.75, rx * 0.85, ry * 0.35, (90, 60, 50, 255))
    for k in (-1, 1):
        s.ell(c[0] + k * rx * 0.35, c[1] - r * 0.08, r * 0.09, r * 0.11, (40, 30, 50, 255))
        s.ell(c[0] + k * rx * 0.55, c[1] + r * 0.28, r * 0.17 * (0.6 + puff), r * 0.1 * (0.6 + puff),
              (255, 130, 130, int(200 * puff)))
    s.ell(c[0], c[1] + r * 0.18, r * 0.11, r * 0.09, (235, 160, 120, 255))
    s.line([(c[0] - r * 0.25, c[1] + r * 0.48), (c[0], c[1] + r * 0.56), (c[0] + r * 0.25, c[1] + r * 0.48)],
           (150, 60, 60, 255), r * 0.06)
    if stuffy > 0.02:
        for k in (-1, 1):
            s.ell(c[0] + k * r * 0.05, c[1] + r * 0.22, r * 0.03, r * 0.03, (120, 120, 140, int(255 * stuffy)))
    paste_c(img, s.img(), cx, cy, a)


def hot_sauce(img, cx, cy, p, gt):
    if p <= 0.02:
        return
    s = SS(130, 300)
    s.rect(30, 90, 100, 290, 26, (220, 40, 50, 255))
    s.rect(48, 40, 82, 100, 8, (220, 40, 50, 255))
    s.rect(44, 10, 86, 46, 8, (40, 160, 80, 255))
    s.rect(38, 160, 92, 230, 10, (255, 240, 220, 255))
    s.poly([(65, 172), (52, 208), (65, 222), (78, 208)], (255, 120, 30, 255))
    s.poly([(65, 186), (58, 210), (65, 218), (72, 210)], (255, 226, 60, 255))
    sp = s.img().rotate(12 * math.sin(gt * 3), resample=Image.BICUBIC, expand=True)
    sc = back_out(p)
    sp = sp.resize((max(1, int(sp.width * sc)), max(1, int(sp.height * sc))), Image.BILINEAR)
    paste_c(img, sp, cx, cy)


def ill_face(img, seg, t, gt, a):
    d = ImageDraw.Draw(img)
    puff = 0.5 * ap(seg, t, "aufgedunsen", d=0.8) + 0.5 * ap(seg, t, "rundes", d=0.8)
    stuffy = ap(seg, t, "Nase")
    head(img, 1060, 500, 190, puff, a, stuffy)
    if stuffy > 0.05:
        L.cross(img, 1060, 560, 34, stuffy, w=10)
        text(img, "NASE ZU", 32, 1060, 770, fill=WHITE, path=FONT_XB, stroke=4, sfill=NAVY, alpha=stuffy)
    # body with fluid
    bx, base = 1620, 840
    t_e, t_a = tw(seg, "Erde"), tw(seg, "All")
    thin = ap(seg, t, "dünne", d=0.6)
    sp = person(520, ORANGE)
    if thin > 0.05:
        sp = sp.resize((int(sp.width * (1 - 0.1 * thin)), sp.height))
    paste_c(img, sp, bx, base, a, anchor="b")
    if t > t_e - 0.2:
        up = t > t_a - 0.1
        rr = random.Random(3)
        for k in range(14):
            ph = (gt * 0.45 + rr.random()) % 1
            yy = (base - 60 - 400 * ph) if up else (base - 460 + 400 * ph)
            xx = bx + rr.uniform(-40, 40)
            d.ellipse((xx - 11, yy - 15, xx + 11, yy + 11), fill=(90, 180, 255))
        lab = "IM ALL: NACH OBEN" if up else "ERDE: NACH UNTEN"
        text(img, lab, 30, bx, 250, fill=YELLOW if up else WHITE, path=FONT_XB, stroke=4, sfill=NAVY, alpha=a)
        ax = bx + 150
        if up:
            d.line((ax, 760, ax, 380), fill=YELLOW, width=12)
            d.polygon([(ax - 26, 390), (ax + 26, 390), (ax, 340)], fill=YELLOW)
        else:
            d.line((ax, 380, ax, 760), fill=WHITE, width=12)
            d.polygon([(ax - 26, 750), (ax + 26, 750), (ax, 800)], fill=WHITE)
    hot_sauce(img, 800, 660, prog(t, tw(seg, "scharfe") - 0.2, 0.5), gt)
    L.burst(img, 800, 640, t, tw(seg, "scharfe"), color=RED, rad=170)


def bone(img, cx, cy, frac_lost, a):
    s = SS(700, 240)
    col = (245, 236, 215, 255)
    for x in (80, 620):
        for y in (70, 170):
            s.ell(x, y, 70, 62, col)
    s.rect(80, 70, 620, 170, 40, col)
    rr = random.Random(2)
    holes = []
    for _ in range(90):
        holes.append((rr.uniform(70, 630), rr.uniform(80, 160), rr.uniform(5, 13), rr.random()))
    for x, y, r, th in holes:
        if th < frac_lost:
            s.ell(x, y, r, r * 0.8, (120, 90, 150, 255))
        else:
            s.ell(x, y, 3, 3, (220, 205, 180, 255))
    paste_c(img, s.img(), cx, cy, a)


def ill_bone(img, seg, t, gt, a):
    t_m, t_g = tw(seg, "Monat"), tw(seg, "gewaltig")
    m = prog(t, t_m - 0.3, t_g - t_m + 0.6)
    month = 1 + int(11 * m)
    bone(img, 1150, 420, 0.08 + 0.55 * m, a)
    text(img, "KNOCHEN", 34, 1150, 270, fill=YELLOW, path=FONT_XB, stroke=4, sfill=NAVY, alpha=a)
    # calendar
    cx, cy = 1660, 430
    rrect(img, (cx - 120, cy - 120, cx + 120, cy + 120), 26, (255, 255, 255, int(255 * a)))
    rrect(img, (cx - 120, cy - 120, cx + 120, cy - 50), 26, (235, 60, 70, int(255 * a)))
    text(img, "MONAT", 34, cx, cy - 84, fill=WHITE, path=FONT_XB, alpha=a)
    text(img, str(month), 100, cx, cy + 32, fill=NAVY, alpha=a)
    # density bar
    bw = 900
    x0, y0 = 1290 - bw / 2, 700
    text(img, "KNOCHENDICHTE", 30, 1290, y0 - 50, fill=WHITE, path=FONT_XB, stroke=4, sfill=NAVY, alpha=a)
    rrect(img, (x0, y0, x0 + bw, y0 + 50), 25, (255, 255, 255, int(60 * a)))
    f = 1 - 0.18 * m
    rrect(img, (x0, y0, x0 + bw * f, y0 + 50), 25, (245, 236, 215, int(255 * a)))
    ImageDraw.Draw(img).polygon([(x0 + bw * f + 20, y0 + 25), (x0 + bw * f + 50, y0 + 5), (x0 + bw * f + 50, y0 + 45)],
                                fill=RED)
    text(img, "schematisch", 24, x0 + 80, y0 + 84, fill=(200, 200, 230), path=FONT_XB, alpha=a)
    p = ap(seg, t, "tragen")
    if p > 0.02:
        kx, ky = 1660, 860
        d = ImageDraw.Draw(img)
        d.ellipse((kx - 60, ky - 40, kx + 60, ky + 70), fill=(70, 70, 90))
        d.arc((kx - 40, ky - 85, kx + 40, ky - 5), 180, 360, fill=(70, 70, 90), width=16)
        text(img, "0 kg", 34, kx, ky + 18, fill=WHITE, alpha=p)
        L.cross(img, kx, ky + 10, 70, p, w=12)


def bike(img, cx, cy, a):
    d = ImageDraw.Draw(img)
    for x in (cx - 55, cx + 55):
        d.ellipse((x - 42, cy - 42, x + 42, cy + 42), outline=WHITE, width=9)
    d.line([(cx - 55, cy), (cx - 5, cy - 50), (cx + 55, cy), (cx + 5, cy), (cx - 55, cy)], fill=YELLOW, width=9)
    d.line((cx - 5, cy - 50, cx - 15, cy - 72), fill=YELLOW, width=9)
    d.line((cx + 40, cy - 60, cx + 55, cy), fill=YELLOW, width=9)


def barbell(img, cx, cy, a):
    d = ImageDraw.Draw(img)
    d.line((cx - 90, cy, cx + 90, cy), fill=(220, 220, 230), width=12)
    for k in (-1, 1):
        d.rounded_rectangle((cx + k * 70 - 12, cy - 45, cx + k * 70 + 12, cy + 45), 6, fill=RED)
        d.rounded_rectangle((cx + k * 95 - 9, cy - 32, cx + k * 95 + 9, cy + 32), 5, fill=RED)


def ill_sport(img, seg, t, gt, a):
    d = ImageDraw.Draw(img)
    # treadmill
    tx, ty = 1000, 760
    rrect(img, (tx - 260, ty, tx + 260, ty + 50), 25, (50, 50, 70, int(255 * a)))
    off = (gt * 300) % 60
    for k in range(10):
        x = tx - 250 + ((k * 60 + off) % 500)
        d.line((x, ty + 8, x, ty + 42), fill=(110, 110, 140), width=6)
    d.line((tx + 230, ty, tx + 200, ty - 300), fill=(170, 170, 190), width=10)
    rrect(img, (tx + 150, ty - 330, tx + 250, ty - 290), 12, (90, 90, 120, 255))
    leg = math.sin(gt * 9)
    paste_c(img, astronaut(430, leg=leg, arm=0.3 + 0.3 * leg), tx - 20, ty + 4, a, anchor="b")
    for k in (-1, 1):
        d.line((tx - 20 + k * 60, ty - 290, tx - 20 + k * 130, ty), fill=YELLOW, width=4)
    text(img, "LAUFBAND MIT GURTEN", 30, tx, ty + 90, fill=WHITE, path=FONT_XB, stroke=4, sfill=NAVY, alpha=a)
    # clock 2h
    cf = prog(t, 0.0, 6.0) * 2
    clock(img, 1640, 300, 95, cf % 1 if cf < 2 else 0.0, a)
    text(img, "≈ 2 h / TAG", 40, 1640, 440, fill=YELLOW, stroke=5, sfill=NAVY, alpha=a)
    p1, p2 = ap(seg, t, "Fahrrad"), ap(seg, t, "Kraftmaschine")
    if p1 > 0.02:
        bike(img, 1480, 580, p1)
    if p2 > 0.02:
        barbell(img, 1780, 570, p2)
    # muscle bar
    pm = ap(seg, t, "Muskeln", d=0.5)
    if pm > 0.02:
        x0, y0, bw = 1390, 770, 470
        text(img, "MUSKELN OHNE TRAINING", 28, x0 + bw / 2, y0 - 42, fill=WHITE, path=FONT_XB, stroke=4,
             sfill=NAVY, alpha=pm)
        rrect(img, (x0, y0, x0 + bw, y0 + 46), 23, (255, 255, 255, int(60 * pm)))
        f = 1 - 0.2 * ease_io(prog(t, tw(seg, "20") - 0.3, 1.0))
        rrect(img, (x0, y0, x0 + bw * f, y0 + 46), 23, (255, 120, 120, int(255 * pm)))
        if f < 0.99:
            text(img, "−20 %", 46, x0 + bw - 70, y0 + 100, fill=(255, 120, 120), stroke=6, sfill=NAVY)
            text(img, "in 5–11 Tagen", 26, x0 + 120, y0 + 100, fill=WHITE, path=FONT_XB, alpha=pm)


def ill_orbit(img, seg, t, gt, a):
    d = ImageDraw.Draw(img)
    ex, ey, er = 1150, 520, 220
    # sun
    sx, sy = 1730, 390
    for k in range(4, 0, -1):
        d.ellipse((sx - 60 - 18 * k, sy - 60 - 18 * k, sx + 60 + 18 * k, sy + 60 + 18 * k),
                  fill=(255, 220, 80, 0) if False else (255, 200 + 10 * k, 80))
    d.ellipse((sx - 70, sy - 70, sx + 70, sy + 70), fill=(255, 236, 120))
    # orbit path behind
    rx, ry = 340, 110
    tilt = -0.25
    def orb(u):
        x, y = rx * math.cos(u), ry * math.sin(u)
        return ex + x * math.cos(tilt) - y * math.sin(tilt), ey + x * math.sin(tilt) + y * math.cos(tilt)
    pts = [orb(k / 80 * 2 * math.pi) for k in range(81)]
    d.line(pts[40:], fill=(200, 210, 255), width=3)
    paste_c(img, earth_sprite(er), ex, ey, a)
    # night side (away from sun = left-bottom)
    lay = Image.new("RGBA", (2 * er, 2 * er))
    ImageDraw.Draw(lay).pieslice((0, 0, 2 * er - 1, 2 * er - 1), 105, 285, fill=(5, 5, 30, 150))
    m = Image.new("L", lay.size, 0)
    ImageDraw.Draw(m).ellipse((0, 0, 2 * er - 1, 2 * er - 1), fill=255)
    lay.putalpha(Image.fromarray(__import__("numpy").minimum(__import__("numpy").array(lay.getchannel("A")),
                                                              __import__("numpy").array(m))))
    img.paste(lay, (ex - er, ey - er), lay)
    d = ImageDraw.Draw(img)
    d.line(pts[:41], fill=(200, 210, 255), width=3)
    t0 = L.REVEAL_T if hasattr(L, "REVEAL_T") else REVEAL + 0.4
    u = 16 * min(1.0, max(0.0, t - t0) / 3.4) + max(0.0, t - t0 - 3.4) / 2.5
    n_sr = min(16, int(u + 0.15))
    if t < t0 + 3.6:
        text(img, "ZEITRAFFER: 24 STUNDEN", 30, ex, 840, fill=YELLOW, path=FONT_XB, stroke=4, sfill=NAVY, alpha=a)
    ang = (u % 1) * 2 * math.pi + math.pi * 0.95
    ix, iy = orb(ang)
    behind = math.sin(ang) < 0
    if not (behind and math.hypot(ix - ex, iy - ey) < er):
        paste_c(img, iss_sprite(0.8), ix, iy, a)
    # counter
    cx, cy = 1610, 700
    rrect(img, (cx - 230, cy - 90, cx + 230, cy + 90), 34, (15, 20, 40, int(220 * a)), outline=YELLOW + (255,),
          width=5)
    text(img, "SONNENAUFGÄNGE", 30, cx, cy - 48, fill=YELLOW, path=FONT_XB, alpha=a)
    text(img, str(max(1, n_sr)), 90, cx, cy + 25, fill=WHITE, alpha=a)
    frac_flash = (u % 1)
    if n_sr < 16 and t > t0 and frac_flash < 0.15:
        L.burst(img, ix, iy, frac_flash, 0.0, color=YELLOW, rad=60)
    p = ap(seg, t, "Uhrzeit")
    if p > 0.02:
        clock(img, 750, 760, 80, 0.92, p)
        text(img, "Zzz", 60, 860, 650, fill=WHITE, stroke=6, sfill=NAVY, alpha=p, rotate=10)


def ill_eye(img, seg, t, gt, a):
    px0, py0, px1, py1 = 740, 230, 1840, 870
    rrect(img, (px0, py0, px1, py1), 46, (6, 6, 18, int(245 * a)), outline=(90, 90, 140, 255), width=4)
    d = ImageDraw.Draw(img)
    cx, cy = (px0 + px1) / 2, (py0 + py1) / 2 + 30
    t_f = tw(seg, "Lichtblitze")
    rr = random.Random(int(gt * 7))
    if t > t_f:
        for k in range(3):
            if rr.random() < 0.55:
                x, y = rr.uniform(px0 + 60, px1 - 60), rr.uniform(py0 + 50, py1 - 50)
                ln = rr.uniform(20, 90)
                an = rr.uniform(0, math.pi)
                c = rr.choice([(255, 255, 255), (180, 220, 255), (255, 250, 200)])
                d.line((x - ln * math.cos(an), y - ln * math.sin(an), x + ln * math.cos(an), y + ln * math.sin(an)),
                       fill=c, width=rr.choice([3, 5, 7]))
                d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=c)
    # closed eye
    d.arc((cx - 230, cy - 170, cx + 230, cy + 110), 20, 160, fill=(255, 205, 165), width=18)
    for k in range(7):
        an = math.radians(40 + k * 16.6)
        x0, y0 = cx + 230 * math.cos(an), cy - 30 + 140 * math.sin(an)
        d.line((x0, y0, x0 + 34 * math.cos(an), y0 + 34 * math.sin(an)), fill=(255, 205, 165), width=9)
    text(img, "AUGEN ZU", 30, cx, py0 + 50, fill=(200, 200, 230), path=FONT_XB, alpha=a)
    t_s = tw(seg, "Kosmische")
    if t > t_s - 0.2:
        rr2 = random.Random(5)
        for k in range(6):
            ph = (gt * 0.9 + rr2.random()) % 1
            y0 = py0 + 40 + rr2.uniform(0, 200)
            x = px0 + 40 + ph * (px1 - px0 - 80)
            y = y0 + ph * 380
            d.line((x - 70, y - 24, x, y), fill=(120, 255, 200), width=5)
            d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(200, 255, 230))
        text(img, "TEILCHEN AUS DEM ALL", 30, cx, py1 - 50, fill=(120, 255, 200), path=FONT_XB, alpha=a)
    tg = tw(seg, "geklärt")
    if t > tg - 0.1:
        q = 1 + 0.08 * math.sin(gt * 6)
        text(img, "?", 230 * q * back_out(prog(t, tg - 0.1, 0.5)), px1 - 130, py0 + 150, fill=YELLOW, stroke=10,
             sfill=NAVY, rotate=12)


def helix(img, cx, y0, y1, gt, red_frac, a):
    d = ImageDraw.Draw(img)
    n = 16
    rr = random.Random(9)
    flags = [rr.random() for _ in range(n)]
    pts_a, pts_b = [], []
    for k in range(n):
        y = y0 + (y1 - y0) * k / (n - 1)
        ph = k * 0.55 + gt * 1.4
        xa, xb = cx + 110 * math.sin(ph), cx - 110 * math.sin(ph)
        pts_a.append((xa, y))
        pts_b.append((xb, y))
        col = (255, 80, 90) if flags[k] < red_frac else [(90, 200, 255), (255, 226, 60), (120, 230, 140)][k % 3]
        d.line((xa, y, xb, y), fill=col, width=10)
    d.line(pts_a, fill=(230, 230, 255), width=10, joint="curve")
    d.line(pts_b, fill=(190, 160, 255), width=10, joint="curve")


def ill_twins(img, seg, t, gt, a):
    d = ImageDraw.Draw(img)
    # Scott (astronaut) left, Mark right on Earth
    paste_c(img, astronaut(400, arm=0.4), 900, 640 + 12 * math.sin(gt * 2), a, anchor="b")
    text(img, "SCOTT", 40, 900, 680, fill=YELLOW, stroke=5, sfill=NAVY, alpha=a)
    text(img, "340 Tage im All", 28, 900, 722, fill=WHITE, path=FONT_XB, alpha=a)
    d.chord((1530, 600, 1830, 760), 180, 360, fill=(40, 120, 230))
    paste_c(img, person(330, BLUE), 1680, 615, a, anchor="b")
    text(img, "MARK", 40, 1680, 680, fill=(120, 200, 255), stroke=5, sfill=NAVY, alpha=a)
    text(img, "auf der Erde", 28, 1680, 722, fill=WHITE, path=FONT_XB, alpha=a)
    pm = ap(seg, t, "Mark")
    if pm > 0.02:
        L.pill(img, "GLEICHE GENE", 1290, 250, GREEN, pm, size=32)
    # helix: red = changed, back to normal at "90"
    ch = ap(seg, t, "verändert", d=0.6)
    back = ease_io(prog(t, tw(seg, "90") - 0.2, 1.4))
    red = 0.95 * ch * (1 - back) + 0.08 * back
    helix(img, 1290, 300, 600, gt, red, a)
    # bar
    pb = ap(seg, t, "90", d=0.4)
    if pb > 0.02:
        x0, y0, bw = 890, 800, 800
        rrect(img, (x0, y0, x0 + bw, y0 + 54), 27, (255, 255, 255, int(60 * pb)))
        f = 0.91 * ease_io(prog(t, tw(seg, "90") - 0.2, 1.2))
        rrect(img, (x0, y0, x0 + bw * f, y0 + 54), 27, GREEN + (int(255 * pb),))
        text(img, f"> {int(round(100 * f))} % wieder normal", 30, x0 + bw * f / 2 + 20, y0 + 27, fill=NAVY,
             path=FONT_XB, alpha=pb)
        ps = ap(seg, t, "kleiner")
        if ps > 0.02:
            rrect(img, (x0 + bw * 0.91 + 4, y0, x0 + bw, y0 + 54), 20, (255, 80, 90, int(255 * ps)))
            text(img, "Rest blieb länger", 26, x0 + bw - 40, y0 + 90, fill=(255, 140, 150), path=FONT_XB, alpha=ps)


ILL = [ill_height, ill_face, ill_bone, ill_sport, ill_orbit, ill_eye, ill_twins]


# ------------------------------------------------------------------ scenes
def draw_cards(img, qi, t_by_card, states, gt, base_a=1.0, skip=None):
    Q = QS[qi]
    for i in range(3):
        if skip is not None and i == skip:
            continue
        p = t_by_card[i]
        if p <= 0.01:
            continue
        L.card(img, i, Q["opts"][i], L.CARD_X[i], L.CARD_Y, s=back_out(p), a=min(1, p * 2) * base_a,
               state=states[i], gt=gt)


def sc_intro(img, seg, t, gt):
    d = ImageDraw.Draw(img)
    # Earth arc
    big = 900
    d.ellipse((W / 2 - big * 1.6, 860, W / 2 + big * 1.6, 860 + big * 2), fill=(40, 120, 230))
    d.ellipse((W / 2 - big * 1.6, 860, W / 2 + big * 1.6, 860 + big * 2), outline=(120, 190, 255), width=10)
    for x, y, w_ in ((420, 930, 160), (900, 900, 240), (1500, 935, 180)):
        d.ellipse((x - w_, y - 25, x + w_, y + 30), fill=(70, 185, 95))
    L.brand(img, W / 2, 90, gt, 1.0 * back_out(prog(t, 0.0, 0.5)))
    a = ease_out(prog(t, 0.3, 0.5))
    text(img, "Was passiert mit deinem Körper,", 70, W / 2, 230, alpha=a, stroke=8, sfill=NAVY)
    text(img, "wenn du 1 JAHR im Weltall lebst?", 82, W / 2, 330, fill=YELLOW, alpha=a, stroke=9, sfill=NAVY)
    sp = astronaut(360, arm=0.5 + 0.3 * math.sin(gt * 1.5))
    sp = sp.rotate(14 * math.sin(gt * 0.8), resample=Image.BICUBIC, expand=True)
    paste_c(img, sp, W / 2, 610 + 18 * math.sin(gt * 1.3), ease_out(prog(t, 0.0, 0.6)))
    p7 = prog(t, tw(seg, "7") - 0.1, 0.5)
    if p7 > 0:
        L.stamp(img, "7 FRAGEN", t, tw(seg, "7") - 0.1, 1480, 600, size=96, rot=-8)
        L.burst(img, 1480, 600, t, tw(seg, "7"), rad=230)
    pz = ap(seg, t, "zähl")
    if pz > 0.02:
        rrect(img, (300, 520, 660, 680), 36, (15, 20, 40, int(230 * pz)), outline=YELLOW + (255,), width=5)
        text(img, "DEINE PUNKTE", 32, 480, 560, fill=YELLOW, path=FONT_XB, alpha=pz)
        text(img, "0 / 7", 70, 480, 630, alpha=pz)


def sc_frage(img, seg, t, gt):
    qi = seg["qi"]
    L.top_bar(img, gt, qi + 1, ease_out(prog(t, 0, 0.3)))
    p = back_out(prog(t, 0.05, 0.5))
    x = W / 2 + (1 - ease_out(prog(t, 0.0, 0.45))) * 900
    lab = "LETZTE FRAGE" if qi == 6 else f"FRAGE {qi + 1}"
    text(img, lab, 190 * max(0.05, p), x, 470, fill=YELLOW, stroke=14, sfill=NAVY, rotate=-4)
    q = 1 + 0.15 * math.sin(gt * 7)
    text(img, "?", 150 * q * max(0.05, p), x + 520 * p + (90 if qi == 6 else 0), 380, fill=(255, 80, 90), stroke=10,
         sfill=NAVY, rotate=14)
    a = ease_out(prog(t, 0.3, 0.4))
    text(img, ["KÖRPERGRÖSSE", "GESICHT", "KNOCHEN", "SPORT", "SONNE", "AUGEN", "ZWILLINGE"][qi], 52, W / 2, 660,
         fill=WHITE, path=FONT_XB, stroke=6, sfill=NAVY, alpha=a)


def card_pops(seg, t, qi):
    out = []
    for i, w in enumerate(QS[qi]["ow"]):
        try:
            t0 = wt(seg, w) - 0.1
        except KeyError:
            t0 = 1.0 + i
        out.append(prog(t, t0, 0.45))
    return out


def sc_q(img, seg, t, gt):
    qi = seg["qi"]
    L.top_bar(img, gt, qi + 1)
    L.question_text(img, QS[qi]["q"], ease_out(prog(t, 0.0, 0.35)))
    draw_cards(img, qi, card_pops(seg, t, qi), [None] * 3, gt)


def sc_cd(img, seg, t, gt):
    qi = seg["qi"]
    L.top_bar(img, gt, qi + 1)
    L.question_text(img, QS[qi]["q"])
    wob = [1 + 0.02 * math.sin(gt * 5 + i) for i in range(3)]
    draw_cards(img, qi, [1.0] * 3, [None] * 3, gt)
    _ = wob
    L.countdown(img, t, seg["dur"], gt)


def sc_a(img, seg, t, gt):
    qi = seg["qi"]
    Q = QS[qi]
    r = Q["right"]
    L.top_bar(img, gt, qi + 1)
    u = ease_io(prog(t, REVEAL + 0.15, 0.7))
    # question text shrinks to the top
    qa = 1 - u
    if qa > 0.02:
        L.question_text(img, Q["q"], qa)
    if u > 0.02:
        L.question_text(img, Q["q"], u, y=165, size=40)
    rev = t > 0.12
    states = [("right" if i == r else "wrong") if rev else None for i in range(3)]
    for i in range(3):
        if i == r:
            continue
        L.card(img, i, Q["opts"][i], L.CARD_X[i], L.CARD_Y, s=1.0 - 0.15 * u, a=1 - u, state=states[i], gt=gt)
    cx = L.CARD_X[r] + (330 - L.CARD_X[r]) * u
    cy = L.CARD_Y + (400 - L.CARD_Y) * u
    s = 1.0 - 0.14 * u + 0.08 * back_out(prog(t, 0.12, 0.4)) * (1 - prog(t, 0.6, 0.3))
    L.card(img, r, Q["opts"][r], cx, cy, s=s, state=states[r], gt=gt)
    if t < REVEAL + 1.5:
        L.burst(img, L.CARD_X[r], L.CARD_Y, t, 0.12, color=GREEN, rad=260)
        pa = ease_out(prog(t, 0.25, 0.3)) * (1 - prog(t, REVEAL + 0.4, 0.3))
        text(img, "Richtig geraten? +1 Punkt!", 50, W / 2, 870, fill=YELLOW, stroke=7, sfill=NAVY, alpha=pa)
    # facts (left column)
    for k, (s_, w) in enumerate(Q["facts"]):
        p = ap(seg, t, w)
        if p > 0.02:
            chip(img, s_, 330, 640 + k * 92, [YELLOW, WHITE, GREEN][k], p)
    ia = ease_out(prog(t, REVEAL + 0.35, 0.5))
    if ia > 0.02:
        ILL[qi](img, seg, t, gt, ia)


RANKS = [("0 – 2", "Weltall-Tourist", WHITE), ("3 – 5", "Raumfahrer", BLUE), ("6 – 7", "Astronauten-Profi", YELLOW)]


def sc_outro(img, seg, t, gt):
    d = ImageDraw.Draw(img)
    L.brand(img, W / 2, 90, gt, back_out(prog(t, 0.0, 0.5)))
    t_r = wt(seg, "Rate", 1)
    fo = 1 - ease_io(prog(t, t_r - 0.4, 0.35))
    p = back_out(prog(t, 0.1, 0.5)) * fo
    if p > 0.05:
        cx, cy, bw, bh = 560, 380, 400 * p, 130 * p
        rrect(img, (cx - bw, cy - bh, cx + bw, cy + bh), 50, (255, 255, 255, 245))
        d.polygon([(cx - 60 * p, cy + bh - 2), (cx - 130 * p, cy + bh + 70 * p), (cx + 10 * p, cy + bh - 2)],
                  fill=(255, 255, 255))
        text(img, "Wie viele richtig?", 56 * p, cx, cy - 30, fill=NAVY)
        blink = "|" if int(gt * 3) % 2 == 0 else " "
        text(img, "_ / 7 " + blink, 60 * p, cx, cy + 50, fill=(255, 120, 0))
    paste_c(img, astronaut(330, arm=0.6 + 0.4 * math.sin(gt * 3)), 520, 900 + 10 * math.sin(gt * 2),
            ease_out(prog(t, 0.2, 0.4)) * fo, anchor="b")
    for k, (rng, name, col) in enumerate(RANKS):
        pk = ease_out(prog(t, 0.6 + 0.35 * k, 0.4)) * fo
        if pk <= 0.02:
            continue
        y = 300 + k * 130
        rrect(img, (1050, y - 52, 1760, y + 52), 30, (15, 20, 40, int(220 * pk)), outline=col + (255,), width=5)
        text(img, rng, 50, 1170, y, fill=col, alpha=pk)
        text(img, name, 46, 1490, y, fill=WHITE, path=FONT_XB, alpha=pk)
    ps = ap(seg, t, "Abonnieren")
    if ps > 0.02:
        q = 1 + 0.05 * math.sin(gt * 6)
        sc = back_out(prog(t, tw(seg, "Abonnieren") - 0.1, 0.5)) * q
        bx = 1405 + (W / 2 - 1405) * (1 - fo)
        rrect(img, (bx - 250 * sc, 760 - 62 * sc, bx + 250 * sc, 760 + 62 * sc), int(62 * sc), (230, 30, 40, 255))
        text(img, "ABONNIEREN", 54 * sc, bx, 762, fill=WHITE)
    if t > t_r - 0.1:
        L.stamp(img, "RATE MAL!", t, t_r - 0.1, W / 2, 470, size=170, rot=-6)
        L.confetti(img, t, t_r)


DRAW = dict(intro=sc_intro, frage=sc_frage, q=sc_q, cd=sc_cd, a=sc_a, outro=sc_outro)


def draw(img, seg, t, gt):
    DRAW[seg["kind"]](img, seg, t, gt)


def events():
    ev = []
    for s in L.SEGS:
        st, k = s["start"], s["kind"]
        if k == "frage":
            ev += [(st, "whoosh", 0.09), (st + 0.15, "thump", 0.14)]
        elif k == "q":
            for i, w in enumerate(QS[s["qi"]]["ow"]):
                try:
                    ev.append((st + wt(s, w) - 0.1, "pop", 0.10))
                except KeyError:
                    pass
        elif k == "cd":
            for j in range(int(s["dur"])):
                ev.append((st + j, "tick" if j < int(s["dur"]) - 1 else "tock", 0.14))
        elif k == "a":
            ev += [(st + 0.12, "chime", 0.12), (st + REVEAL + 0.15, "whoosh", 0.06)]
            for s_, w in QS[s["qi"]]["facts"]:
                try:
                    ev.append((st + wt(s, w) - 0.1, "pop", 0.07))
                except KeyError:
                    pass
        elif k == "intro":
            ev += [(st + wt(s, "7") - 0.1, "thump", 0.14)]
        elif k == "outro":
            ev += [(st + wt(s, "Rate") - 0.1, "chime", 0.12), (st + wt(s, "Abonnieren") - 0.1, "pop", 0.10)]
    return ev


L.setup(here=HERE, out="rate_mal_ein_jahr_im_weltall.mp4", plan=plan, draw=draw, events=events)

if __name__ == "__main__":
    L.main()

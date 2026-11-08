#!/usr/bin/env python3
""""The 9 to 5 loop" – wordless stick-figure short, dark cinematic style (English on-screen text).

Soft glowing figures with depth-shaded limbs, floor reflections, monospace HUD cards, camera moves.
Everything (figures, sets, music, SFX) is drawn / synthesised here. 1080x1920, 30 fps.
Usage: python3 render.py [--stills t1 t2 ...]
"""
import math
import os
import random
import subprocess
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, K = 1080, 1920, 30, 2
SR = 48000
INTER = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
INTER_XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
MONO_XB = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf"

BG = (8, 8, 12)
PROP = (30, 30, 40)
PROP2 = (42, 42, 54)
LINE = (66, 66, 82)
TXT = (236, 236, 242)
DIM = (128, 128, 144)
AMBER = (245, 184, 61)
CORAL = (255, 122, 107)
BLUE = (122, 162, 255)
NAVY = (20, 30, 62)

FLOOR = 1180          # stage floor (y, unzoomed)

# timeline
T_A, T_B, T_C, T_D, T_E, T_F, T_G, T_END = 0.0, 5.0, 9.0, 15.0, 18.5, 26.5, 32.0, 38.5
TOTAL = T_END
NFR = int(TOTAL * FPS)


# ------------------------------------------------------------------ math
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, t0, d):
    return clamp((t - t0) / d) if d > 0 else float(t >= t0)


def eo(x):
    return 1 - (1 - x) ** 3


def eio(x):
    return x * x * (3 - 2 * x)


def bo(x, s=1.7):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def mix(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(len(a)))


_fonts = {}


def F(size, path):
    key = (int(size), path)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, max(4, int(size)))
    return _fonts[key]


# ------------------------------------------------------------------ stage canvas (2x)
class Stage:
    def __init__(self):
        self.im = Image.new("RGB", (W * K, H * K), BG)
        self.d = ImageDraw.Draw(self.im)

    def rr(self, x0, y0, x1, y1, r=0, fill=PROP, outline=LINE, w=3):
        if x1 <= x0 or y1 <= y0:
            return
        self.d.rounded_rectangle((x0 * K, y0 * K, x1 * K, y1 * K), int(r * K), fill=fill,
                                 outline=outline, width=int(w * K) if outline else 0)

    def line(self, pts, w, col):
        p = [(x * K, y * K) for x, y in pts]
        self.d.line(p, fill=col, width=int(w * K), joint="curve")
        r = w * K / 2
        for x, y in p:
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=col)

    def circ(self, x, y, r, fill=None, outline=None, w=3):
        self.d.ellipse(((x - r) * K, (y - r) * K, (x + r) * K, (y + r) * K), fill=fill, outline=outline,
                       width=int(w * K) if outline else 0)

    def poly(self, pts, fill):
        self.d.polygon([(x * K, y * K) for x, y in pts], fill=fill)

    def glow(self, x, y, r, col, a):
        """soft radial light (additive-ish)"""
        if a <= 0.01:
            return
        n = int(r * 2 * K / 4) + 2
        g = Image.new("L", (n, n), 0)
        ImageDraw.Draw(g).ellipse((n * 0.2, n * 0.2, n * 0.8, n * 0.8), fill=int(255 * a))
        g = g.filter(ImageFilter.GaussianBlur(n * 0.14)).resize((n * 4, n * 4), Image.BILINEAR)
        lay = Image.new("RGB", g.size, col)
        self.im.paste(lay, (int(x * K - g.size[0] / 2), int(y * K - g.size[1] / 2)), g)

    def text(self, s, size, x, y, col=TXT, path=MONO, anchor="mm"):
        self.d.text((x * K, y * K), s, font=F(size * K, path), fill=col, anchor=anchor)


# ------------------------------------------------------------------ figure
TONE_COOL = dict(front=(226, 228, 236), back=(132, 134, 148), glow=(170, 190, 255), ga=0.35)
TONE_OLD = dict(front=(150, 150, 158), back=(92, 92, 104), glow=(120, 120, 130), ga=0.0)
TONE_WARM = dict(front=(255, 208, 80), back=(190, 136, 36), glow=(255, 190, 60), ga=0.85)
TONE_BLUE = dict(front=(176, 200, 255), back=(110, 130, 190), glow=(122, 162, 255), ga=0.75)


def tone_mix(a, b, k):
    return dict(front=mix(a["front"], b["front"], k), back=mix(a["back"], b["back"], k),
                glow=mix(a["glow"], b["glow"], k), ga=a["ga"] + (b["ga"] - a["ga"]) * k)


def pose(**kw):
    p = dict(torso=0, head=0, ba=(12, 8), fa=(-12, -8), bl=(5, 0), fl=(-5, 0), rot=0, eyes=0.0, closed=0.0,
             look=0.0)
    p.update(kw)
    return p


def walk(ph, slump=0.0, lean=4):
    s = math.sin(ph)
    s2 = math.sin(ph + math.pi)

    def leg(sv, phase):
        return (26 * sv, -(8 + 38 * max(0.0, math.sin(phase + 1.3))))

    return pose(torso=lean + 18 * slump, head=8 * slump - 4, bl=leg(s, ph), fl=leg(s2, ph + math.pi),
                ba=(-24 * s, 28), fa=(-24 * s2, 28))


def typing(gt, slump=0.0, speed=1.0):
    j = math.sin(gt * 26 * speed) * 5
    return pose(torso=8 + 24 * slump, head=-4 + 22 * slump, bl=(86, -80), fl=(80, -84),
                ba=(46 + j, 44), fa=(54 - j, 38), eyes=1)


def sitting(slump=0.0):
    return pose(torso=-12 + 14 * slump, head=10 * slump, bl=(86, -78), fl=(80, -86), ba=(24, 52), fa=(30, 60),
                eyes=1)


def figure(st, x, y, s, p, tone=TONE_COOL, alpha=1.0):
    """draws a soft, depth-shaded stick figure into the stage. (x, y) = hip, 1x coordinates."""
    L = 128 * s
    lw = 30 * s
    pad = int(3.2 * L)
    n = 2 * pad
    lay = Image.new("RGBA", (n * K, n * K))
    d = ImageDraw.Draw(lay)
    ox, oy = pad, pad          # hip in local coords
    rot = math.radians(p["rot"])

    def R(px, py):
        dx, dy = px - ox, py - oy
        return (ox + dx * math.cos(rot) - dy * math.sin(rot), oy + dx * math.sin(rot) + dy * math.cos(rot))

    def limb(o, ang, l1, l2):
        a1, a2 = math.radians(ang[0]), math.radians(ang[0] + ang[1])
        j = (o[0] + l1 * math.sin(a1), o[1] + l1 * math.cos(a1))
        e = (j[0] + l2 * math.sin(a2), j[1] + l2 * math.cos(a2))
        return [o, j, e]

    def stroke(pts, col, wd):
        q = [(R(*pt)[0] * K, R(*pt)[1] * K) for pt in pts]
        d.line(q, fill=col + (255,), width=int(wd * K), joint="curve")
        r = wd * K / 2
        for px, py in q:
            d.ellipse((px - r, py - r, px + r, py + r), fill=col + (255,))

    tr = math.radians(p["torso"])
    neck = (ox + 0.98 * L * math.sin(tr), oy - 0.98 * L * math.cos(tr))
    sh = (ox + 0.86 * L * math.sin(tr), oy - 0.86 * L * math.cos(tr))
    hr = math.radians(p["torso"] + p["head"])
    head = (neck[0] + 0.40 * L * math.sin(hr), neck[1] - 0.40 * L * math.cos(hr))
    hip_back = (ox - 0.05 * L * math.cos(tr), oy)
    # back limbs (darker), then torso, then front limbs
    stroke(limb(hip_back, p["bl"], 0.62 * L, 0.62 * L), tone["back"], lw)
    stroke(limb(sh, p["ba"], 0.52 * L, 0.5 * L), tone["back"], lw * 0.86)
    stroke([(ox, oy), sh], tone["front"], lw * 1.12)
    stroke(limb((ox, oy), p["fl"], 0.62 * L, 0.62 * L), tone["front"], lw)
    stroke(limb(sh, p["fa"], 0.52 * L, 0.5 * L), tone["front"], lw * 0.86)
    hx, hy = R(*head)
    hrad = 0.30 * L
    d.ellipse(((hx - hrad) * K, (hy - hrad) * K, (hx + hrad) * K, (hy + hrad) * K), fill=tone["front"] + (255,))
    # soft shading on head
    d.ellipse(((hx - hrad * 0.6) * K, (hy - hrad * 0.75) * K, (hx + hrad * 0.15) * K, (hy - hrad * 0.05) * K),
              fill=mix(tone["front"], (255, 255, 255), 0.35) + (255,))
    ex = hx + p["look"] * hrad * 0.35
    if p["closed"] > 0:
        for k in (-1, 1):
            d.line(((ex + k * hrad * 0.32 - hrad * 0.14) * K, hy * K, (ex + k * hrad * 0.32 + hrad * 0.14) * K, hy * K),
                   fill=(40, 40, 50, 255), width=int(4 * s * K))
    elif p["eyes"] > 0:
        er = hrad * 0.1 * p["eyes"]
        for k in (-1, 1):
            d.ellipse(((ex + k * hrad * 0.3 - er) * K, (hy - er) * K, (ex + k * hrad * 0.3 + er) * K, (hy + er) * K),
                      fill=(30, 30, 40, 255))
    if alpha < 0.99:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    px, py = int((x - pad) * K), int((y - pad) * K)
    if tone["ga"] > 0.02:
        small = lay.getchannel("A").resize((n // 2, n // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(10 * s))
        g = small.resize(lay.size, Image.BILINEAR).point(lambda v: int(v * tone["ga"] * alpha))
        st.im.paste(Image.new("RGB", lay.size, tone["glow"]), (px, py), g)
    st.im.paste(lay, (px, py), lay)
    return hx - ox + x, hy - oy + y


# ------------------------------------------------------------------ HUD / captions (2x overlay)
class Over:
    def __init__(self):
        self.im = Image.new("RGBA", (W * K, H * K))
        self.d = ImageDraw.Draw(self.im)

    def card(self, x0, y0, x1, y1, label, value, col, a=1.0, bar=None, pop=1.0):
        if a <= 0.01:
            return
        A = int(255 * a)
        self.d.rounded_rectangle((x0 * K, y0 * K, x1 * K, y1 * K), 22 * K, fill=(14, 14, 18, int(235 * a)),
                                 outline=col + (int(110 * a),), width=3 * K)
        cx = (x0 + x1) / 2
        self.d.text((cx * K, (y0 + 36) * K), label, font=F(28 * K, MONO), fill=(170, 170, 185, A), anchor="mm")
        self.d.text((cx * K, (y0 + 86) * K), value, font=F(58 * pop * K, MONO_XB), fill=col + (A,), anchor="mm")
        if bar is not None:
            bx0, bx1, by = x0 + 30, x1 - 30, y1 - 16
            self.d.rounded_rectangle((bx0 * K, (by - 4) * K, bx1 * K, (by + 4) * K), 4 * K, fill=(40, 40, 50, A))
            self.d.rounded_rectangle((bx0 * K, (by - 4) * K, (bx0 + (bx1 - bx0) * clamp(bar)) * K, (by + 4) * K),
                                     4 * K, fill=col + (A,))

    def text(self, s, size, x, y, col=TXT, path=INTER, a=1.0, anchor="mm", sc=1.0, maxw=840):
        if a <= 0.01:
            return
        tw = F(size * K, path).getlength(s) / K
        if tw > maxw:
            size = size * maxw / tw
        self.d.text((x * K, y * K), s, font=F(size * sc * K, path), fill=col + (int(255 * a),), anchor=anchor)

    def chip(self, s, x, y, col, a=1.0):
        if a <= 0.01:
            return
        f = F(24 * K, MONO)
        bb = f.getbbox(s)
        w = (bb[2] - bb[0]) / K + 30
        self.d.rounded_rectangle(((x - w / 2) * K, (y - 22) * K, (x + w / 2) * K, (y + 22) * K), 12 * K,
                                 fill=(14, 14, 18, int(240 * a)), outline=col + (int(255 * a),), width=2 * K)
        self.d.text((x * K, y * K), s, font=f, fill=col + (int(255 * a),), anchor="mm")
        self.d.polygon([((x - 9) * K, (y + 21) * K), ((x + 9) * K, (y + 21) * K), (x * K, (y + 32) * K)],
                       fill=(14, 14, 18, int(240 * a)))

    def caption(self, l1, l2, t, t_in, col2=AMBER, size=68):
        p = prog(t, t_in, 0.35)
        if p <= 0:
            return
        a = eo(p)
        dy = 20 * (1 - eo(p))
        self.text(l1, size, 540, 1355 + dy, TXT, a=a)
        if l2:
            p2 = prog(t, t_in + 0.25, 0.35)
            self.text(l2, size, 540, 1440 + 20 * (1 - eo(p2)), col2, a=eo(p2))


def hud(o, t, clock, hours, day, a=1.0, t_in=0.0, hours_bar=None, left_label="TIME", hours_label="HOURS AT WORK",
        pop_r=1.0):
    k = eo(prog(t, t_in, 0.4)) * a
    o.card(80, 250, 500, 400, left_label, clock, AMBER, k)
    o.card(520, 250, 940, 400, hours_label, hours, CORAL, k, bar=hours_bar, pop=pop_r)
    if day:
        o.text(day, 30, 540, 450, DIM, path=MONO, a=k)


# ------------------------------------------------------------------ props
def floor_line(st):
    st.line([(60, FLOOR), (1020, FLOOR)], 3, LINE)


def window(st, x0=640, y0=600, lit=0.0):
    st.rr(x0, y0, x0 + 230, y0 + 190, 14, fill=mix(NAVY, (90, 80, 110), lit), outline=(10, 10, 14), w=6)
    st.circ(x0 + 180, y0 + 45, 13, fill=(200, 200, 210))


def bed(st):
    st.rr(120, 1010, 640, 1080, 22, fill=PROP2)
    st.line([(150, 1080), (150, FLOOR)], 12, PROP2)
    st.line([(610, 1080), (610, FLOOR)], 12, PROP2)
    st.rr(110, 900, 160, 1080, 18, fill=PROP)
    st.rr(170, 975, 280, 1012, 16, fill=(70, 72, 88), outline=None)


def blanket(st, cover=1.0):
    if cover > 0.02:
        st.rr(250, 1010 - 40 * cover, 640, 1060, 24, fill=(52, 60, 96), outline=(80, 92, 140), w=3)


def alarm(st, t, ring):
    st.rr(700, 1060, 860, FLOOR, 12, fill=PROP)
    sh = math.sin(t * 55) * 6 if ring else 0
    x, y = 780 + sh, 1010
    if ring:
        st.glow(x, y, 120, CORAL, 0.5 + 0.2 * math.sin(t * 20))
    st.circ(x, y, 44, fill=(24, 24, 30), outline=CORAL if ring else LINE, w=5)
    st.line([(x, y), (x, y - 24)], 5, TXT)
    st.line([(x, y), (x + 16, y + 8)], 5, TXT)
    if ring:
        for k in (1, 2):
            r = 60 + 22 * k + 10 * ((t * 4) % 1)
            for sgn in (-1, 1):
                a0 = -40 if sgn > 0 else 180 + 40
                st.d.arc(((x - r) * K, (y - r) * K, (x + r) * K, (y + r) * K), a0 - 30 if sgn > 0 else a0 - 30,
                         a0 + 30 if sgn > 0 else a0 + 30, fill=CORAL, width=5 * K)


def city(st, t, speed=220):
    for layer, (sp, col, hs, wl) in enumerate([(0.35, (16, 16, 24), (420, 560, 380, 620, 500), 0.6),
                                               (1.0, (26, 26, 36), (300, 380, 260, 420, 340), 1.0)]):
        off = (t * speed * sp) % 330
        rr = random.Random(5 + layer)
        for i in range(-1, 5):
            x0 = i * 330 - off + (60 if layer == 0 else 0)
            h = hs[(i + 7) % len(hs)]
            st.rr(x0, FLOOR - h, x0 + 220, FLOOR, 8, fill=col, outline=None)
            for wy in range(int(FLOOR - h + 40), FLOOR - 50, 64):
                for wx in (x0 + 40, x0 + 130):
                    if rr.random() < 0.3:
                        st.rr(wx, wy, wx + 46, wy + 34, 4, fill=mix(col, AMBER, 0.55 * wl), outline=None)
    # street lamps
    off = (t * speed * 1.3) % 540
    for i in range(-1, 3):
        x = i * 540 - off + 300
        st.glow(x, 840, 170, AMBER, 0.28)
        st.line([(x, 820), (x, FLOOR)], 8, PROP2)
        st.rr(x - 26, 806, x + 26, 826, 8, fill=AMBER, outline=None)
    # rain
    rr = random.Random(9)
    for k in range(80):
        x = rr.uniform(0, 1080)
        y = (rr.uniform(0, 700) + t * 1100) % 700 + 520
        st.line([(x, y), (x - 6, y + 22)], 2, (70, 84, 120))


def office(st, t, papers=0.0, screen=1.0):
    st.rr(60, 640, 1020, FLOOR, 18, fill=(14, 14, 20), outline=None)
    # desk
    st.rr(370, 1000, 960, 1030, 10, fill=PROP2)
    st.line([(400, 1030), (400, FLOOR)], 12, PROP2)
    st.line([(930, 1030), (930, FLOOR)], 12, PROP2)
    # monitor + glow
    st.glow(650, 860, 300, BLUE, 0.22 * screen)
    st.rr(540, 780, 780, 940, 14, fill=mix((20, 28, 50), (40, 60, 110), screen), outline=(70, 90, 140), w=4)
    for k in range(4):
        st.line([(570, 815 + k * 30), (570 + 110 + 60 * math.sin(t * 2.5 + k), 815 + k * 30)], 6,
                mix((40, 50, 80), (150, 180, 240), screen))
    st.line([(660, 940), (660, 1000)], 12, PROP2)
    st.rr(450, 988, 580, 1000, 4, fill=(60, 60, 74), outline=None)
    # paper stack
    n = int(papers * 24)
    for k in range(n):
        y = 994 - k * 8
        st.rr(820 + (k % 2) * 5, y - 7, 920 + (k % 2) * 5, y, 2, fill=(200, 200, 205), outline=None)
    # chair
    st.rr(230, 1000, 380, 1028, 10, fill=(50, 50, 62), outline=None)
    st.line([(305, 1028), (305, 1150)], 10, (50, 50, 62))
    st.line([(250, 1160), (360, 1160)], 10, (50, 50, 62))


def couch(st):
    st.rr(110, 1010, 590, 1110, 26, fill=(56, 56, 72), outline=None)
    st.rr(110, 940, 180, 1110, 26, fill=(64, 64, 82), outline=None)
    st.rr(530, 990, 600, 1110, 26, fill=(64, 64, 82), outline=None)
    st.line([(150, 1110), (150, FLOOR)], 10, (56, 56, 72))
    st.line([(560, 1110), (560, FLOOR)], 10, (56, 56, 72))


def tv(st, t):
    fl = 0.6 + 0.4 * math.sin(t * 13) * math.sin(t * 4.3)
    st.glow(830, 900, 260, BLUE, 0.2 * fl)
    st.rr(720, 840, 940, 980, 10, fill=mix((20, 30, 60), (80, 110, 180), fl), outline=(70, 90, 140), w=4)
    st.line([(830, 980), (830, FLOOR)], 8, PROP2)


def door(st, op, x0=760, x1=940, y0=760):
    if op > 0:
        # light spill on the floor + rays
        lay = Image.new("L", st.im.size, 0)
        d = ImageDraw.Draw(lay)
        d.polygon([(x0 * K, FLOOR * K), (x1 * K, FLOOR * K), ((x1 - 40) * K, (FLOOR + 140) * K),
                   ((x0 - 480 * op) * K, (FLOOR + 140) * K)], fill=int(120 * op))
        d.polygon([(x0 * K, y0 * K), (x0 * K, FLOOR * K), ((x0 - 520 * op) * K, (FLOOR + 30) * K),
                   ((x0 - 360 * op) * K, (y0 - 60) * K)], fill=int(34 * op))
        lay = lay.filter(ImageFilter.GaussianBlur(30))
        st.im.paste(Image.new("RGB", st.im.size, AMBER), (0, 0), lay)
        st.d = ImageDraw.Draw(st.im)
        st.rr(x0, y0, x1, FLOOR, 6, fill=mix((60, 50, 30), (255, 226, 150), op), outline=None)
    w = (x1 - x0) * (1 - 0.82 * op)
    st.poly([(x0, y0 - 4), (x0 + w, y0 + 24 * op), (x0 + w, FLOOR - 24 * op), (x0, FLOOR)], PROP2)
    if op < 0.2:
        st.circ(x0 + w - 26, (y0 + FLOOR) / 2, 8, fill=AMBER)
    st.rr(x0 - 10, y0 - 12, x1 + 10, y0, 4, fill=PROP, outline=None)


# ------------------------------------------------------------------ scenes → (stage, overlay, zoom, focus)
def sc_wake(t):
    u = t - T_A
    st, o = Stage(), Over()
    window(st, lit=0.4 * eio(prog(u, 2.4, 2.0)))
    floor_line(st)
    bed(st)
    ring = u < 3.0
    alarm(st, u, ring)
    sit = eio(prog(u, 2.6, 1.0))
    stand = eio(prog(u, 3.8, 0.9))
    if stand <= 0:
        p = pose(rot=-90 + 76 * sit, ba=(170, -10), fa=(10, 0), bl=(4, 0), fl=(-4, 0),
                 closed=1 - prog(u, 2.0, 0.2), eyes=1)
        if sit > 0:
            p.update(bl=(86 * sit, -80 * sit), fl=(80 * sit, -84 * sit), ba=(30 + 140 * (1 - sit), 30), fa=(20, 40))
        figure(st, 470 - 150 * sit, 985, 1.0, p)
        blanket(st, 1 - sit)
    else:
        x = 320 + 80 * stand
        p = pose(torso=-6 * (1 - stand), ba=(-150 * stand + 20, 0), fa=(150 * stand - 20, 0), eyes=1,
                 bl=(86 * (1 - stand), -80 * (1 - stand)), fl=(80 * (1 - stand), -84 * (1 - stand)))
        figure(st, x, 985 + 70 * stand, 1.0, p)
    hud(o, u, "06:30", "0000", "DAY 001 · MONDAY", hours_bar=0.0)
    o.caption("WAKE UP. WORK. SLEEP.", "FOR 40 YEARS?", u, 0.15)
    return st, o, 1.0 + 0.05 * eio(prog(u, 0, 5)), (540, 1000)


def sc_commute(t):
    u = t - T_B
    st, o = Stage(), Over()
    city(st, u)
    floor_line(st)
    ph = u * 8.5
    bob = 6 * math.cos(2 * ph)
    hx, hy = figure(st, 470, 990 - bob, 1.0, walk(ph))
    # umbrella
    st.line([(hx + 70, hy + 60), (hx + 70, hy - 110)], 6, (120, 120, 135))
    st.poly([(hx - 90, hy - 100), (hx + 70, hy - 170), (hx + 230, hy - 100)], (60, 62, 80))
    clock = f"07:{15 + int(30 * prog(u, 0, 4)):02d}"
    hud(o, u, clock, "0000", "DAY 001 · MONDAY", hours_bar=0.0)
    o.caption("SAME ROAD.", "SAME RAIN.", u, 0.2)
    return st, o, 1.03, (540, 1000)


def sc_work(t):
    u = t - T_C
    d = T_D - T_C
    st, o = Stage(), Over()
    k = eio(prog(u, 0.4, d - 1.2))
    office(st, u, papers=k)
    floor_line(st)
    figure(st, 305, 990, 1.0, typing(u, slump=0.45 * k), tone=tone_mix(TONE_COOL, TONE_BLUE, 0.25))
    hrs = 9 + 8 * k
    hud(o, u, f"{int(hrs):02d}:{int((hrs % 1) * 60) // 15 * 15:02d}", f"{int(8 * k):04d}", "DAY 001 · MONDAY",
        hours_bar=8 * k / 76800 * 40)
    n = 3 + int(44 * k)
    o.chip(f"{n} UNREAD", 660, 740, CORAL, eo(prog(u, 0.6, 0.3)))
    o.caption("9 TO 5.", "EIGHT HOURS. EVERY DAY.", u, 0.2)
    return st, o, 1.0 + 0.06 * eio(prog(u, 0, d)), (600, 950)


def sc_evening(t):
    u = t - T_D
    st, o = Stage(), Over()
    if u < 2.0:
        window(st)
        floor_line(st)
        couch(st)
        tv(st, u)
        hx, hy = figure(st, 340, 1000, 1.0, sitting(slump=0.7))
        st.glow(hx + 40, hy + 120, 70, BLUE, 0.4)
        st.rr(hx + 26, hy + 96, hx + 56, hy + 146, 6, fill=(150, 180, 255), outline=None)
        hud(o, u, f"{19 + int(2 * prog(u, 0, 2)):02d}:00", "0008", "DAY 001 · MONDAY", hours_bar=8 / 76800 * 40)
        o.caption("2 HOURS FOR YOURSELF.", "TOO TIRED TO USE THEM.", u, 0.1)
    else:
        window(st)
        floor_line(st)
        bed(st)
        alarm(st, u, False)
        figure(st, 470, 985, 1.0, pose(rot=-90, ba=(170, -10), fa=(10, 0), closed=1))
        blanket(st, 1.0)
        hud(o, u, "23:30", "0008", "DAY 001 · MONDAY", hours_bar=8 / 76800 * 40)
        o.caption("SLEEP.", "AND THEN…", u, 2.0)
    return st, o, 1.02, (540, 1000)


DAYS = ["TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]


def sc_loop(t):
    u = t - T_E
    st, o = Stage(), Over()
    per = 0.62
    n_days = len(DAYS)
    if u < n_days * per:
        di = int(u / per)
        k = int((u % per) / (per / 4))
        if k == 0:
            window(st)
            floor_line(st)
            bed(st)
            alarm(st, u, True)
            figure(st, 470, 985, 1.0, pose(rot=-90, ba=(170, -10), closed=1))
            blanket(st)
        elif k == 1:
            city(st, u * 3)
            floor_line(st)
            figure(st, 470, 990, 1.0, walk(u * 22))
        elif k == 2:
            office(st, u, papers=0.6)
            floor_line(st)
            figure(st, 305, 990, 1.0, typing(u * 2, 0.3), tone=tone_mix(TONE_COOL, TONE_BLUE, 0.25))
        else:
            couch(st)
            tv(st, u)
            floor_line(st)
            figure(st, 340, 1000, 1.0, sitting(0.7))
        hrs = 8 * (di + 2) - (8 if k < 2 else (4 if k == 2 else 0))
        hud(o, 9, ["06:30", "07:45", "13:00", "21:00"][k], f"{hrs:04d}", f"DAY {di + 2:03d} · {DAYS[di]}",
            hours_bar=hrs / 76800 * 40)
        o.caption("REPEAT.", "", 9, 0, )
        return st, o, 1.02, (540, 1000)
    u2 = u - n_days * per
    if u2 < 0.75:
        couch(st)
        tv(st, u)
        floor_line(st)
        figure(st, 380, 1000, 1.0, pose(rot=-78, ba=(170, 0), closed=1))
        o.text("WEEKEND", 120, 540, 700, AMBER, a=1 - prog(u2, 0.5, 0.25), sc=0.9 + 0.1 * bo(prog(u2, 0, 0.3)))
        o.text("(ALREADY OVER)", 34, 540, 790, DIM, path=MONO, a=prog(u2, 0.3, 0.1))
        hud(o, 9, "SUN 23:59", "0040", "DAY 007", hours_bar=40 / 76800 * 40)
        o.caption("REPEAT.", "", 9, 0)
        return st, o, 1.02, (540, 1000)
    u3 = u2 - 0.75
    d3 = T_F - T_E - n_days * per - 0.75
    age = eio(prog(u3, 0.0, d3 - 0.4))
    office(st, u3 * 4, papers=1.0, screen=1.0)
    floor_line(st)
    figure(st, 305, 990, 1.0, typing(u3 * 1.4, slump=0.4 + 0.6 * age),
           tone=tone_mix(tone_mix(TONE_COOL, TONE_BLUE, 0.25), TONE_OLD, age))
    # flying calendar pages
    rr = random.Random(int(u3 * 10))
    for k in range(6):
        ph = (u3 * 1.8 + k / 6) % 1
        x = 120 + k * 140 + ph * 160
        y = 700 - ph * 180
        a = math.sin(ph * math.pi)
        st.rr(x, y, x + 90, y + 100, 8, fill=mix(BG, (210, 210, 215), a), outline=None)
        st.rr(x, y, x + 90, y + 26, 8, fill=mix(BG, CORAL, a), outline=None)
        st.text(str(rr.randint(1, 31)), 36, x + 45, y + 64, col=mix(BG, (30, 30, 40), a), path=MONO_XB)
    year = 1 + int(39 * age)
    hours = int(76800 * age)
    hud(o, 9, f"YEAR {year:02d}", f"{hours:,}", "8 H × 5 DAYS × 48 WEEKS", left_label="CAREER",
        hours_bar=age, pop_r=1.0 + 0.05 * math.sin(u3 * 30) * (age < 1))
    o.caption("REPEAT.", "76,800 HOURS." if age >= 0.99 else "", 9, 0, col2=CORAL)
    return st, o, 1.0 + 0.06 * age, (600, 950)


def sc_question(t):
    u = t - T_F
    st, o = Stage(), Over()
    office(st, 0, papers=1.0, screen=0.35)
    floor_line(st)
    turn = eio(prog(u, 2.8, 0.9))
    p = typing(0, slump=1.0 - 0.3 * turn)
    p.update(ba=(10, 6), fa=(14, 8), head=22 * (1 - turn), look=-turn, eyes=1)
    figure(st, 305, 990, 1.0, p, tone=TONE_OLD)
    hud(o, 9, "YEAR 40", "76,800", "", left_label="CAREER", hours_bar=1.0, a=1 - prog(u, 0, 0.6))
    o.text("DO YOU WANT", 74, 540, 330, TXT, a=eo(prog(u, 0.7, 0.4)))
    o.text("TO DO THIS", 74, 540, 420, TXT, a=eo(prog(u, 1.1, 0.4)))
    p2 = prog(u, 2.0, 0.45)
    o.text("FOREVER?", 150, 540, 1400, CORAL, a=eo(p2), sc=0.85 + 0.15 * bo(p2))
    return st, o, 1.0 + 0.12 * eio(prog(u, 0, 5.5)), (380, 900)


def sc_answer(t):
    u = t - T_G
    st, o = Stage(), Over()
    op = eio(prog(u, 1.6, 0.9))
    office(st, 0, papers=1.0, screen=0.35)
    door(st, op)
    floor_line(st)
    young = eo(prog(u, 0.5, 0.7))
    warm = eio(prog(u, 1.8, 1.4))
    tone = tone_mix(tone_mix(TONE_OLD, TONE_COOL, young), TONE_WARM, warm)
    if u < 1.0:
        figure(st, 305, 990, 1.0, typing(0, slump=1.0 - young), tone=tone)
    else:
        wp = prog(u, 1.0, 3.0)
        x = 330 + 520 * eio(wp)
        ph = u * 8.5
        a = 1 - prog(u, 4.0, 0.6)
        figure(st, x, 990 - 6 * math.cos(2 * ph), 1.0, walk(ph, lean=6), tone=tone, alpha=a)
    o.text("I DON'T THINK SO.", 78, 540, 340, AMBER, a=eo(prog(u, 0.0, 0.4)),
           sc=0.9 + 0.1 * bo(prog(u, 0.0, 0.4)))
    if u > 4.6:
        a = eo(prog(u, 4.6, 0.4))
        o.text("WHAT WOULD YOU", 64, 540, 1360, TXT, a=a)
        o.text("DO INSTEAD?", 64, 540, 1440, AMBER, a=eo(prog(u, 4.85, 0.4)))
        ax = 860 + 16 * math.sin(u * 8)
        o.d.line(((ax - 90) * K, 1505 * K, ax * K, 1505 * K), fill=AMBER + (int(255 * a),), width=10 * K)
        o.d.polygon([((ax + 30) * K, 1505 * K), ((ax - 4) * K, 1482 * K), ((ax - 4) * K, 1528 * K)],
                    fill=AMBER + (int(255 * a),))
    return st, o, 1.06 - 0.04 * eio(prog(u, 0, 4)), (640, 950)


SCENES = [(T_A, sc_wake), (T_B, sc_commute), (T_C, sc_work), (T_D, sc_evening), (T_E, sc_loop),
          (T_F, sc_question), (T_G, sc_answer)]


# ------------------------------------------------------------------ compositing
def compose(t):
    fn = SCENES[0][1]
    for t0, f in SCENES:
        if t >= t0:
            fn = f
    st, o, z, (fx, fy) = fn(t)
    # camera zoom around focus (stage only)
    cw, ch = W * K / z, H * K / z
    x0 = clamp(fx * K - cw / 2, 0, W * K - cw)
    y0 = clamp(fy * K - ch / 2, 0, H * K - ch)
    img = st.im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    arr = np.asarray(img).astype(np.float32)
    # floor reflection
    fl = int((FLOOR * K - y0) / (ch / H))
    depth = 240
    if 0 < fl < H - depth:
        src = arr[fl - depth:fl][::-1]
        fade = np.linspace(0.22, 0.0, depth)[:, None, None]
        dst = arr[fl + 4:fl + 4 + depth]
        arr[fl + 4:fl + 4 + depth] = dst * (1 - fade) + src * fade
    # spotlight / dimming in the question scene
    if T_F <= t < T_G + 0.6:
        u = t - T_F
        dim = 0.75 * eo(prog(u, 0.0, 1.0)) * (1 - prog(t, T_G, 0.6))
        yy, xx = np.mgrid[0:H, 0:W]
        sx = (305 * K - x0) / (ch / H)
        spot = np.exp(-(((xx - sx) / 300) ** 2 + ((yy - 900) / 520) ** 2))
        arr *= (1 - dim * (1 - spot))[..., None]
    # vignette
    arr *= VIGN[..., None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    ov = o.im.resize((W, H), Image.LANCZOS)
    img.paste(ov, (0, 0), ov)
    return img


_yy, _xx = np.mgrid[0:H, 0:W]
VIGN = (1 - 0.45 * (((_xx - W / 2) / (W * 0.8)) ** 2 + ((_yy - H * 0.48) / (H * 0.62)) ** 2)).clip(0.4, 1).astype(
    np.float32)
CUTS = [T_B, T_C, T_D, T_E, T_F, T_G]


def frame(fi):
    t = fi / FPS
    img = compose(t)
    for c in CUTS:          # short dip-through-black at scene cuts
        dt = t - c
        if -0.12 <= dt < 0.12:
            k = 1 - abs(dt) / 0.12
            img = Image.blend(img, Image.new("RGB", img.size, BG), 0.85 * k)
    return img


def frame_bytes(fi):
    return frame(fi).tobytes()


# ------------------------------------------------------------------ audio (synthesised, licence-free)
def synth():
    n = int(TOTAL * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    r = np.random.default_rng(4)

    def add(sig, t0, g):
        a = int(t0 * SR)
        if a >= n or a < 0:
            return
        b = min(n, a + len(sig))
        out[a:b] += sig[:b - a] * g

    def env(m, atk=0.004, dec=8.0):
        x = np.arange(m) / SR
        return np.minimum(1, x / atk) * np.exp(-x * dec)

    # minor-key pad until the question
    chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7), (164.8, 207.7, 246.9)]
    for i in range(int(T_F / 2.4) + 1):
        a, b = int(i * 2.4 * SR), min(int(T_F * SR) + int(0.6 * SR), int((i + 1) * 2.4 * SR) + int(0.3 * SR), n)
        if a >= n:
            break
        x = tt[a:b] - tt[a]
        seg = sum(np.sin(2 * np.pi * f * x) + 0.25 * np.sin(2 * np.pi * f * 2.003 * x) for f in chords[i % 4])
        out[a:b] += seg * np.minimum(1, x / 0.4) * np.exp(-np.maximum(0, x - 2.2) * 6) * 0.03
    # pulse beat (soft kick), double time in the loop
    t0 = 0.4
    while t0 < T_F:
        m = int(0.25 * SR)
        x = np.arange(m) / SR
        kick = np.sin(2 * np.pi * np.cumsum(50 + 80 * np.exp(-x * 30)) / SR) * env(m, dec=12)
        add(kick, t0, 0.2)
        if t0 > T_E:
            hm = int(0.04 * SR)
            add(r.standard_normal(hm) * env(hm, dec=90), t0 + 0.12, 0.03)
        t0 += 0.42 if t0 < T_E else 0.24
    # alarm
    for k in range(int(3.0 / 0.16)):
        m = int(0.08 * SR)
        x = np.arange(m) / SR
        add(np.sign(np.sin(2 * np.pi * 1250 * x)) * env(m, dec=5), 0.05 + k * 0.16, 0.07)
    # rain + footsteps
    rain = np.convolve(r.standard_normal(n), np.ones(6) / 6, "same")
    out += rain * 0.012 * ((tt > T_B) & (tt < T_C))
    for k in range(int((T_C - T_B) / 0.37)):
        m = int(0.07 * SR)
        add(r.standard_normal(m) * env(m, dec=45), T_B + 0.15 + k * 0.37, 0.06)
    # typing
    tk = T_C + 0.3
    while tk < T_D - 0.2:
        m = int(0.018 * SR)
        add(r.standard_normal(m) * env(m, dec=320), tk, 0.05)
        tk += r.uniform(0.06, 0.15)
    # TV hum
    out += np.sin(2 * np.pi * 120 * tt) * 0.006 * ((tt > T_D) & (tt < T_D + 2))
    # page flips during the years
    for k in range(20):
        m = int(0.12 * SR)
        y = np.convolve(r.standard_normal(m), np.ones(28) / 28, "same") * np.sin(np.linspace(0, np.pi, m))
        add(y, T_E + 3.3 + k * 0.2, 0.22)
    # question: silence, ticking clock, drone, hit
    for k in range(int((T_G - T_F) / 0.5)):
        m = int(0.02 * SR)
        x = np.arange(m) / SR
        add(np.sin(2 * np.pi * 2500 * x) * env(m, dec=200), T_F + 0.3 + k * 0.5, 0.14 if k % 2 == 0 else 0.09)
    out += (np.sin(2 * np.pi * 55 * tt) * 0.5 + np.sin(2 * np.pi * 82.4 * tt) * 0.3) * 0.045 * \
        np.clip((tt - T_F) / 1.0, 0, 1) * np.clip((T_G - tt) / 0.3, 0, 1)
    m = int(1.4 * SR)
    x = np.arange(m) / SR
    add((np.sin(2 * np.pi * 42 * x) + 0.3 * r.standard_normal(m) * np.exp(-x * 25)) * np.exp(-x * 2.5), T_F + 2.0,
        0.35)
    # answer: warm major swell + shimmer + birds
    for f in (261.6, 329.6, 392.0, 523.3, 659.3):
        out += np.sin(2 * np.pi * f * tt) * 0.022 * np.clip((tt - T_G - 1.4) / 1.6, 0, 1) * \
            np.clip((TOTAL - tt) / 1.0, 0, 1)
    for k in range(7):
        m = int(0.16 * SR)
        x = np.arange(m) / SR
        f = 3200 + 1400 * np.sin(2 * np.pi * 10 * x)
        add(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(m, atk=0.01, dec=12), T_G + 2.2 + k * 0.5, 0.035)
    # whooshes at cuts
    for c in CUTS:
        m = int(0.35 * SR)
        y = np.convolve(r.standard_normal(m), np.ones(40) / 40, "same") * np.sin(np.linspace(0, np.pi, m)) ** 2
        add(y / (np.abs(y).max() + 1e-9), c - 0.15, 0.08)
    out = out / (np.abs(out).max() + 1e-9) * 0.9
    path = os.path.join(HERE, "build", "audio.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((out * 32767).astype(np.int16).tobytes())
    return path


def main():
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    if "--stills" in sys.argv:
        qc = os.path.join(HERE, "qc")
        os.makedirs(qc, exist_ok=True)
        for f in os.listdir(qc):
            os.remove(os.path.join(qc, f))
        args = [float(a) for a in sys.argv[sys.argv.index("--stills") + 1:]]
        times = args or [x * TOTAL / 24 + 0.5 for x in range(24)]
        for t in times:
            frame(int(t * FPS)).save(os.path.join(qc, f"f_{t:06.2f}.png"))
        print("stills", len(times))
        return
    wav = synth()
    out = os.path.join(HERE, "the_9_to_5_loop.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                           f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium",
                           "-crf", "18", "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest", "-movflags",
                           "+faststart", out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, b in enumerate(pool.imap(frame_bytes, range(NFR), chunksize=4)):
            ff.stdin.write(b)
            if i % 150 == 0:
                print("frame", i, "/", NFR, flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()

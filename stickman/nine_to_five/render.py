#!/usr/bin/env python3
""""9 to 5 forever?" – wordless animated stick-figure short (English on-screen text).

Everything (figure, sets, music, SFX) is drawn / synthesised here. Output: 1080x1920, 30 fps, H.264/AAC.
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
W, H, FPS, K = 1080, 1920, 30, 2          # K = supersampling factor
SR = 48000
FONT_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"

PAPER = (246, 242, 233)
INK = (28, 28, 34)
RED = (226, 58, 48)
YEL = (255, 200, 40)
BLUE = (70, 130, 220)
GREY = (150, 150, 160)

# ------------------------------------------------------------------ timeline (seconds)
T_A, T_B, T_C, T_D, T_E, T_F, T_G, T_END = 0.0, 4.0, 8.0, 14.0, 17.5, 25.0, 30.5, 36.0
TOTAL = T_END
NFR = int(TOTAL * FPS)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, t0, d):
    return clamp((t - t0) / d) if d > 0 else float(t >= t0)


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_io(x):
    return 3 * x * x - 2 * x * x * x


def back_out(x, s=1.7):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


_fonts = {}


def F(size, path=FONT_BLACK):
    key = (int(size * K), path)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, max(4, int(size * K)))
    return _fonts[key]


# ------------------------------------------------------------------ canvas helpers (all coords in 1x px)
class C:
    def __init__(self, bg=PAPER):
        self.im = Image.new("RGB", (W * K, H * K), bg)
        self.d = ImageDraw.Draw(self.im)

    def line(self, pts, w=10, col=INK):
        p = [(x * K, y * K) for x, y in pts]
        self.d.line(p, fill=col, width=int(w * K), joint="curve")
        r = w * K / 2
        for x, y in (p[0], p[-1]):
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=col)

    def circ(self, x, y, r, fill=None, outline=INK, w=10):
        self.d.ellipse(((x - r) * K, (y - r) * K, (x + r) * K, (y + r) * K), fill=fill,
                       outline=outline, width=int(w * K) if outline else 0)

    def rect(self, x0, y0, x1, y1, fill=None, outline=INK, w=8, r=0):
        if x1 <= x0 or y1 <= y0:
            return
        self.d.rounded_rectangle((x0 * K, y0 * K, x1 * K, y1 * K), int(r * K), fill=fill,
                                 outline=outline, width=int(w * K) if outline else 0)

    def poly(self, pts, fill, outline=None, w=6):
        self.d.polygon([(x * K, y * K) for x, y in pts], fill=fill, outline=outline,
                       width=int(w * K) if outline else 1)

    def text(self, s, size, x, y, col=INK, path=FONT_BLACK, anchor="mm", stroke=0, scol=PAPER, alpha=1.0,
             rot=0.0):
        if alpha <= 0.01:
            return
        f = F(size, path)
        if alpha >= 0.99 and not rot:
            self.d.text((x * K, y * K), s, font=f, fill=col, anchor=anchor, stroke_width=int(stroke * K),
                        stroke_fill=scol)
            return
        bb = f.getbbox(s, stroke_width=int(stroke * K))
        lw, lh = bb[2] - bb[0] + 20, bb[3] - bb[1] + 20
        layer = Image.new("RGBA", (lw, lh))
        ImageDraw.Draw(layer).text((10 - bb[0], 10 - bb[1]), s, font=f, fill=col + (255,),
                                   stroke_width=int(stroke * K), stroke_fill=scol + (255,))
        if rot:
            layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
        if alpha < 0.99:
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
        lw, lh = layer.size
        px = x * K - (lw / 2 if anchor[0] == "m" else (0 if anchor[0] == "l" else lw))
        self.im.paste(layer, (int(px), int(y * K - lh / 2)), layer)

    def overlay(self, col, a):
        if a <= 0.01:
            return
        ov = Image.new("RGB", self.im.size, col)
        self.im = Image.blend(self.im, ov, a)
        self.d = ImageDraw.Draw(self.im)

    def out(self):
        return self.im.resize((W, H), Image.LANCZOS)


# ------------------------------------------------------------------ stick figure
def pose(**kw):
    p = dict(torso=0, head=0, la=(15, 10), ra=(-15, -10), ll=(6, 0), rl=(-6, 0), rot=0, eyes=0.0)
    p.update(kw)
    return p


def stick(c, x, y, s, p, col=INK, w=11):
    """(x, y) = hip. angles in degrees: limbs measured from straight down, torso from straight up."""
    L = 100 * s

    def R(px, py):
        a = math.radians(p["rot"])
        dx, dy = px - x, py - y
        return (x + dx * math.cos(a) - dy * math.sin(a), y + dx * math.sin(a) + dy * math.cos(a))

    def limb(o, ang, l1, l2):
        a1, a2 = math.radians(ang[0]), math.radians(ang[0] + ang[1])
        j = (o[0] + l1 * math.sin(a1), o[1] + l1 * math.cos(a1))
        e = (j[0] + l2 * math.sin(a2), j[1] + l2 * math.cos(a2))
        return [o, j, e]

    tr = math.radians(p["torso"])
    neck = (x + L * math.sin(tr), y - L * math.cos(tr))
    sh = (x + 0.88 * L * math.sin(tr), y - 0.88 * L * math.cos(tr))
    hr = math.radians(p["torso"] + p["head"])
    head = (neck[0] + 0.34 * L * math.sin(hr), neck[1] - 0.34 * L * math.cos(hr))
    parts = [[(x, y), neck], limb(sh, p["la"], 0.5 * L, 0.48 * L), limb(sh, p["ra"], 0.5 * L, 0.48 * L),
             limb((x, y), p["ll"], 0.58 * L, 0.58 * L), limb((x, y), p["rl"], 0.58 * L, 0.58 * L)]
    for seg in parts:
        c.line([R(*q) for q in seg], w * s, col)
    hx, hy = R(*head)
    c.circ(hx, hy, 0.27 * L, fill=PAPER, outline=col, w=w * s)
    if p["eyes"] > 0:
        e = p["eyes"]
        for k in (-1, 1):
            c.circ(hx + k * 0.09 * L, hy - 0.02 * L, 0.035 * L * e, fill=col, outline=None)
    return (hx, hy)


def walk_pose(ph, slump=0.0):
    s = math.sin(ph)
    return pose(torso=4 + 20 * slump, head=10 * slump, ll=(26 * s, max(0, -30 * s)), rl=(-26 * s, max(0, 30 * s)),
                la=(-22 * s, -15), ra=(22 * s, -15))


def type_pose(gt, slump=0.0, speed=1.0):
    j = math.sin(gt * 28 * speed) * 6
    return pose(torso=6 + 26 * slump, head=-6 + 22 * slump, ll=(90, -85), rl=(84, -88),
                la=(48 + j, 42), ra=(56 - j, 36))


def sit_pose(slump=0.0):
    return pose(torso=-14 + 10 * slump, head=12 * slump, ll=(88, -80), rl=(80, -85), la=(30, 40), ra=(24, 50))


# ------------------------------------------------------------------ shared UI
def time_badge(c, label, t_in, t, y=250, col=INK):
    a = ease_out(prog(t, t_in, 0.25))
    if a <= 0.01:
        return
    sc = 0.8 + 0.2 * back_out(prog(t, t_in, 0.35))
    w = 220 * sc
    c.rect(540 - w, y - 58 * sc, 540 + w, y + 58 * sc, fill=INK, outline=None, r=58 * sc)
    c.text(label, 70 * sc, 540, y + 2, col=PAPER, alpha=a)


def day_label(c, label, t, t_in=-1, y=360):
    c.text(label, 46, 540, y, col=RED, path=FONT_XB, alpha=ease_out(prog(t, t_in, 0.2)))


def caption(c, word, t, t_in, y=1330, size=120, col=INK):
    p = prog(t, t_in, 0.3)
    if p <= 0:
        return
    c.text(word, size * (0.85 + 0.15 * back_out(p)), 540, y, col=col, alpha=ease_out(p))


def floor(c, y=1080):
    c.line([(40, y), (1040, y)], 8)


# ------------------------------------------------------------------ sets
def set_bedroom(c, t, wake_t=1.4, dawn=0.0):
    # window
    c.rect(600, 520, 900, 780, fill=(40 + int(140 * dawn), 50 + int(120 * dawn), 90 + int(100 * dawn)), w=8)
    c.line([(750, 520), (750, 780)], 6)
    c.line([(600, 650), (900, 650)], 6)
    if dawn < 0.5:
        c.circ(820, 590, 26, fill=(250, 245, 210), outline=None)
    floor(c)
    # bed
    c.rect(120, 900, 640, 990, fill=(200, 210, 235), w=8, r=14)
    c.line([(130, 990), (130, 1080)], 10)
    c.line([(630, 990), (630, 1080)], 10)
    c.rect(110, 820, 150, 990, fill=INK, outline=None, r=8)
    # nightstand + alarm clock
    c.rect(700, 960, 860, 1080, fill=(220, 190, 150), w=8)
    ring = t < wake_t + 1.2
    sh = math.sin(t * 60) * 6 if ring else 0
    c.circ(780 + sh, 900, 52, fill=PAPER, w=8)
    c.line([(780 + sh, 900), (780 + sh, 870)], 6)
    c.line([(780 + sh, 900), (800 + sh, 912)], 6)
    c.line([(740 + sh, 860), (726 + sh, 846)], 8)
    c.line([(820 + sh, 860), (834 + sh, 846)], 8)
    if ring and int(t * 6) % 2 == 0:
        c.text("BEEP!", 54, 780, 800, col=RED, rot=8)
        for k in (-1, 1):
            c.line([(780 + k * 70, 870), (780 + k * 95, 850)], 6, RED)


def city(c, t, speed=260, rain=True, y_ground=1080):
    off = (t * speed) % 300
    rr = random.Random(3)
    for i in range(-1, 6):
        x0 = i * 300 - off + 20
        h = rr.choice([300, 380, 260, 420, 340])
        c.rect(x0, y_ground - h, x0 + 200, y_ground, fill=(215, 212, 205), w=7)
        for wy in range(int(y_ground - h + 40), y_ground - 60, 70):
            for wx in (x0 + 35, x0 + 115):
                c.rect(wx, wy, wx + 45, wy + 40, fill=(190, 200, 215), w=4)
    c.line([(0, y_ground), (1080, y_ground)], 8)
    for k in range(0, 1080, 120):
        x = (k - t * speed * 1.4) % 1080
        c.line([(x, y_ground + 50), (x + 60, y_ground + 50)], 6, GREY)
    if rain:
        rr2 = random.Random(9)
        for k in range(70):
            x = rr2.uniform(0, 1080)
            y = (rr2.uniform(0, 900) + t * 900) % 900 + 420
            c.line([(x, y), (x - 8, y + 26)], 3, BLUE)
        # cloud
        for dx, r in ((-60, 60), (0, 80), (70, 60)):
            c.circ(300 + dx, 470, r, fill=(170, 170, 180), outline=None)


def set_office(c, t, papers=0.0, clock_h=9.0, dim=0.0):
    floor(c, 1120)
    # cubicle wall
    c.rect(60, 560, 1020, 1120, fill=(225, 222, 212), w=0, outline=None)
    c.line([(60, 560), (1020, 560)], 6, GREY)
    # wall clock
    cx, cy, r = 800, 480, 62
    c.circ(cx, cy, r, fill=PAPER, w=8)
    hh = (clock_h % 12) / 12 * 2 * math.pi
    mm = (clock_h % 1) * 2 * math.pi
    c.line([(cx, cy), (cx + 36 * math.sin(hh), cy - 36 * math.cos(hh))], 9)
    c.line([(cx, cy), (cx + 56 * math.sin(mm), cy - 56 * math.cos(mm))], 5, RED)
    # desk
    c.rect(330, 900, 960, 940, fill=(200, 160, 110), w=8)
    c.line([(360, 940), (360, 1120)], 10)
    c.line([(930, 940), (930, 1120)], 10)
    # monitor
    c.rect(560, 700, 800, 860, fill=(70, 90, 120), w=8, r=8)
    c.line([(680, 860), (680, 900)], 10)
    for k in range(4):
        c.line([(585, 730 + k * 30), (585 + (120 + 60 * math.sin(t * 3 + k)) , 730 + k * 30)], 5, (190, 210, 240))
    # paper stacks
    n = int(papers * 22)
    for k in range(n):
        y = 892 - k * 9
        c.rect(840 + (k % 2) * 4, y - 8, 940 + (k % 2) * 4, y, fill=PAPER, w=3)
    # chair
    c.rect(225, 900, 375, 930, fill=(80, 80, 95), outline=None, r=8)
    c.line([(300, 930), (300, 1080)], 10)
    c.line([(245, 1100), (355, 1100)], 10)
    c.rect(420, 884, 540, 900, fill=(90, 90, 105), outline=None, r=4)


def set_home(c, t, tv=True):
    floor(c)
    # couch
    c.rect(120, 900, 560, 1000, fill=(200, 110, 90), w=8, r=20)
    c.rect(120, 820, 170, 1000, fill=(200, 110, 90), w=8, r=14)
    c.line([(150, 1000), (150, 1080)], 10)
    c.line([(530, 1000), (530, 1080)], 10)
    # TV
    flick = 0.5 + 0.5 * math.sin(t * 17) * math.sin(t * 5)
    c.rect(720, 740, 960, 900, fill=(int(90 + 80 * flick), int(110 + 60 * flick), int(170 + 40 * flick)), w=8, r=8)
    c.line([(840, 900), (840, 1080)], 10)
    c.line([(780, 1080), (900, 1080)], 10)


def door(c, x0, y0, x1, y1, open_=0.0, glow=0.0):
    if glow > 0:
        img = Image.new("RGBA", c.im.size)
        d = ImageDraw.Draw(img)
        cx = (x0 + x1) / 2
        for k in range(12):
            a = k / 11 * math.pi - math.pi / 2 - math.pi / 2
            d.polygon([(cx * K, (y0 + y1) / 2 * K), ((cx + 900 * math.cos(a - 0.08)) * K,
                       ((y0 + y1) / 2 + 900 * math.sin(a - 0.08)) * K),
                       ((cx + 900 * math.cos(a + 0.08)) * K, ((y0 + y1) / 2 + 900 * math.sin(a + 0.08)) * K)],
                      fill=(255, 220, 120, int(70 * glow)))
        c.im.paste(img, (0, 0), img)
        c.d = ImageDraw.Draw(c.im)
    c.rect(x0, y0, x1, y1, fill=(255, 236, 170) if open_ > 0 else (170, 120, 80), w=8)
    if open_ > 0:
        w = (x1 - x0) * (1 - open_ * 0.85)
        c.poly([(x0, y0), (x0 + w, y0 + 30 * open_), (x0 + w, y1 - 30 * open_), (x0, y1)], (170, 120, 80), INK, 6)
    else:
        c.circ(x1 - 30, (y0 + y1) / 2, 9, fill=INK, outline=None)


# ------------------------------------------------------------------ scenes
def scene_A(c, t):                       # wake up
    u = t - T_A
    dawn = ease_io(prog(u, 1.5, 2.0))
    set_bedroom(c, u, wake_t=1.4, dawn=dawn)
    sit = ease_io(prog(u, 1.6, 1.0))
    if sit < 1:
        stick(c, 300 + 200 * (1 - sit), 880 + 10 * (1 - sit), 1.6, pose(rot=-90 + 75 * sit, la=(170, 0), ra=(10, 0),
                                                         ll=(4, 0), rl=(-4, 0)))
    else:
        yawn = math.sin(prog(u, 2.6, 1.0) * math.pi)
        stick(c, 300, 890, 1.6, pose(torso=-15 + 5 * yawn, head=-10 * yawn, ll=(88, -75), rl=(82, -80),
                                         la=(160 * yawn + 10, 10), ra=(-160 * yawn - 10, -10)))
        if yawn > 0.3:
            c.text("*yawn*", 44, 430, 560, col=GREY, path=FONT_XB, alpha=yawn)
    time_badge(c, "6:30 AM", -1, u)
    day_label(c, "MONDAY", u, 0.3)
    caption(c, "Wake up.", u, 1.6)


def scene_B(c, t):                       # commute
    u = t - T_B
    city(c, u)
    stick(c, 520, 895, 1.6, walk_pose(u * 9))
    # umbrella
    c.line([(560, 800), (560, 590)], 7)
    c.poly([(400, 600), (560, 520), (720, 600)], (60, 60, 75))
    time_badge(c, "7:45 AM", 0.0, u)
    day_label(c, "MONDAY", u)
    caption(c, "Commute.", u, 0.3)


def scene_C(c, t):                       # work
    u = t - T_C
    d = T_D - T_C
    hrs = 9 + 8 * ease_io(prog(u, 0.6, d - 1.4))
    set_office(c, u, papers=prog(u, 0.6, d - 1.4), clock_h=hrs)
    stick(c, 300, 890, 1.6, type_pose(u, slump=0.4 * prog(u, 0.6, d - 1.2)))
    h = int(hrs)
    label = f"{(h - 1) % 12 + 1}:00 {'AM' if h < 12 else 'PM'}"
    time_badge(c, label, 0.0, u)
    day_label(c, "MONDAY", u)
    caption(c, "Work.", u, 0.3)
    # unread mails counter
    n = int(3 + 44 * prog(u, 0.8, d - 1.6))
    c.rect(100, 450, 470, 530, fill=PAPER, w=6, r=12)
    c.rect(120, 465, 210, 518, fill=None, w=5)
    c.poly([(120, 465), (165, 495), (210, 465)], None, INK, 5)
    c.text(f"{n} unread", 36, 340, 492, col=RED, path=FONT_XB)


def scene_D(c, t):                       # evening + sleep
    u = t - T_D
    d = T_E - T_D
    if u < 2.0:
        set_home(c, u)
        stick(c, 300, 900, 1.6, sit_pose(slump=0.6))
        time_badge(c, "8:00 PM", 0.0, u)
    else:
        set_bedroom(c, 99, wake_t=-9)
        stick(c, 500, 880, 1.6, pose(rot=-90, la=(170, 0), ra=(10, 0)))
        c.text("z", 60, 230, 760 - (u * 40 % 60), col=GREY)
        c.text("Z", 80, 290, 690 - (u * 40 % 60), col=GREY)
        time_badge(c, "11:30 PM", 2.0, u)
        c.overlay((10, 12, 30), 0.35 * prog(u, 2.0, 0.8))
    day_label(c, "MONDAY", u)
    caption(c, "Sleep.", u, 0.3 if u < 2 else 2.0, col=INK if u < 2 else PAPER)
    _ = d


DAYS = ["TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]


def scene_E(c, t):                       # repeat montage → years pass
    u = t - T_E
    per_day = 0.6
    if u < len(DAYS) * per_day:
        di = int(u / per_day)
        k = int((u % per_day) / (per_day / 4))
        sub = [lambda: (set_bedroom(c, 0.5, wake_t=0.0), stick(c, 500, 880, 1.6, pose(rot=-90, la=(170, 0)))),
               lambda: (city(c, u * 3), stick(c, 520, 895, 1.6, walk_pose(u * 20))),
               lambda: (set_office(c, u, papers=0.6, clock_h=9 + 32 * (u % 0.15)),
                        stick(c, 300, 890, 1.6, type_pose(u * 2))),
               lambda: (set_home(c, u), stick(c, 300, 900, 1.6, sit_pose(0.6)))][k]
        sub()
        day_label(c, DAYS[di], 1.0)
        time_badge(c, ["6:30 AM", "7:45 AM", "9 – 5", "11:30 PM"][k], -1, 1.0)
        caption(c, "Repeat.", 1.0, 0.0, col=RED)
        return
    u2 = u - len(DAYS) * per_day
    if u2 < 0.7:                      # the weekend flashes by
        set_home(c, u)
        stick(c, 380, 880, 1.6, pose(rot=-80, la=(170, 0)))
        c.text("WEEKEND", 110, 540, 560, col=YEL, stroke=6, scol=INK, rot=-6, alpha=1 - prog(u2, 0.45, 0.25))
        c.text("(already over)", 46, 540, 660, col=INK, path=FONT_XB, alpha=prog(u2, 0.25, 0.1))
        caption(c, "Repeat.", 1.0, 0.0, col=RED)
        return
    u3 = u2 - 0.7                     # years
    d3 = T_F - T_E - len(DAYS) * per_day - 0.7
    age = ease_io(prog(u3, 0.0, d3))
    set_office(c, u3, papers=1.0, clock_h=9 + u3 * 20)
    col = tuple(int(INK[i] * (1 - age) + GREY[i] * age) for i in range(3))
    stick(c, 300, 890, 1.6, type_pose(u3, slump=0.4 + 0.6 * age), col=col)
    # flying calendar pages
    rr = random.Random(int(u3 * 12))
    for k in range(5):
        ph = (u3 * 2.2 + k * 0.2) % 1
        x = 200 + k * 150 + ph * 220
        y = 600 - ph * 140
        c.rect(x, y, x + 90, y + 100, fill=PAPER, w=5, r=6)
        c.rect(x, y, x + 90, y + 26, fill=RED, outline=None, r=6)
        c.text(str(rr.randint(1, 31)), 40, x + 45, y + 64, path=FONT_XB)
    year = 1 + int(39 * age)
    time_badge(c, f"YEAR {year}", -1, 1.0)
    caption(c, "Repeat.", 1.0, 0.0, col=RED)


def scene_F(c, t):                       # the question
    u = t - T_F
    set_office(c, 0, papers=1.0, clock_h=17.0 + u * 0.02)
    turn = ease_io(prog(u, 2.6, 1.0))
    p = type_pose(0, slump=1.0)
    p["head"] = 16 * (1 - turn)
    p["eyes"] = turn
    p["la"], p["ra"] = (-20, -10), (-15, -5)
    stick(c, 300, 890, 1.6, p, col=GREY)
    c.overlay((15, 15, 25), 0.55 * ease_out(prog(u, 0.0, 0.8)))
    c.text("Do you want", 92, 540, 260, col=PAPER, alpha=ease_out(prog(u, 0.7, 0.4)))
    c.text("to do this", 92, 540, 365, col=PAPER, alpha=ease_out(prog(u, 1.1, 0.4)))
    p2 = prog(u, 2.0, 0.45)
    if p2 > 0:
        c.text("FOREVER?", 128 * (0.8 + 0.2 * back_out(p2)), 540, 1330, col=RED, alpha=ease_out(p2))


def scene_G(c, t):                       # I don't think so.
    u = t - T_G
    # set: office on the left, a door on the right
    set_office(c, 0, papers=1.0, clock_h=17.0)
    op = ease_io(prog(u, 1.8, 0.8))
    door(c, 760, 640, 940, 1120, open_=op, glow=op)
    young = ease_out(prog(u, 0.4, 0.6))
    col = tuple(int(GREY[i] * (1 - young) + INK[i] * young) for i in range(3))
    if u < 1.0:
        stick(c, 300, 890, 1.6, type_pose(0, slump=1.0 - young), col=col)
    else:
        # stands up and walks to the door, then into the light
        wp = prog(u, 1.0, 2.6)
        x = 300 + 560 * ease_io(wp)
        a = 1 - prog(u, 3.5, 0.6)
        if a > 0.02:
            stick(c, x, 930, 1.6, walk_pose(u * 9) if wp < 1 else pose(), col=col)
    c.overlay((15, 15, 25), 0.55 * (1 - prog(u, 0.0, 0.5)))
    c.text("I don't think so.", 96, 540, 300, col=INK, alpha=ease_out(prog(u, 0.0, 0.4)))
    if u > 3.9:
        a = ease_out(prog(u, 3.9, 0.4))
        c.text("What would you", 70, 540, 1290, col=INK, alpha=a)
        c.text("do instead?", 70, 540, 1375, col=RED, alpha=a)
        ax = 840 + 18 * math.sin(u * 8)
        c.line([(ax - 90, 1470), (ax, 1470)], 12, RED)
        c.poly([(ax + 34, 1470), (ax - 4, 1442), (ax - 4, 1498)], RED)


SCENES = [(T_A, scene_A), (T_B, scene_B), (T_C, scene_C), (T_D, scene_D), (T_E, scene_E), (T_F, scene_F),
          (T_G, scene_G)]


def draw(t):
    fn = SCENES[0][1]
    for t0, f in SCENES:
        if t >= t0:
            fn = f
    c = C()
    fn(c, t)
    return c


def frame(fi):
    t = fi / FPS
    img = draw(t).out()
    # quick whip transition at scene cuts (except inside the montage)
    for t0, _ in SCENES[1:]:
        if 0 <= t - t0 < 0.18 and t0 not in (T_F,):
            k = 1 - (t - t0) / 0.18
            img = img.filter(ImageFilter.BoxBlur(int(14 * k))) if k > 0.05 else img
    return img


def frame_bytes(fi):
    return frame(fi).tobytes()


# ------------------------------------------------------------------ audio (all synthesised)
def synth():
    n = int(TOTAL * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    r = np.random.default_rng(2)

    def add(sig, t0, g):
        a = int(t0 * SR)
        if a >= n:
            return
        b = min(n, a + len(sig))
        out[a:b] += sig[:b - a] * g

    def env(m, atk=0.005, dec=8.0):
        x = np.arange(m) / SR
        return np.minimum(1, x / atk) * np.exp(-x * dec)

    # music: soft chord pad, Am F C G (2 s each) until the question, then silence + ticking, then major swell
    chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (261.6, 329.6, 392.0), (196.0, 246.9, 293.7)]
    pad = np.zeros(n)
    for i in range(int(T_F / 2) + 1):
        a, b = int(i * 2 * SR), min(n, int((i + 1) * 2 * SR))
        if a >= int(T_F * SR):
            break
        x = tt[a:b] - tt[a]
        for f in chords[i % 4]:
            pad[a:b] += np.sin(2 * np.pi * f * x) * 0.5 + 0.2 * np.sin(2 * np.pi * 2 * f * x)
        pad[a:b] *= np.minimum(1, x / 0.3) * np.minimum(1, (2 - x) / 0.3)
    pad *= np.where(tt < T_F, 1.0, np.exp(-(tt - T_F) * 6))
    out += pad * 0.035
    # beat: kick + hat; montage plays double time
    t0 = 0.0
    while t0 < T_F:
        dt = 0.333 if t0 < T_E else 0.18
        kick = np.sin(2 * np.pi * np.cumsum(60 + 90 * np.exp(-np.arange(int(0.25 * SR)) / SR * 30)) / SR)
        add(kick * env(len(kick), dec=14), t0, 0.22)
        hat = r.standard_normal(int(0.05 * SR)) * env(int(0.05 * SR), dec=80)
        add(hat, t0 + dt / 2, 0.035)
        t0 += dt
    # alarm beeps
    for k in range(10):
        m = int(0.09 * SR)
        x = np.arange(m) / SR
        add(np.sign(np.sin(2 * np.pi * 1300 * x)) * 0.5 * env(m, dec=4), 0.05 + k * 0.15, 0.12)
    # footsteps (commute)
    for k in range(int((T_C - T_B) / 0.35)):
        m = int(0.08 * SR)
        add(r.standard_normal(m) * env(m, dec=40), T_B + 0.1 + k * 0.35, 0.08)
    # typing (work)
    tk = T_C + 0.3
    while tk < T_D - 0.3:
        m = int(0.02 * SR)
        add(r.standard_normal(m) * env(m, dec=300), tk, 0.06)
        tk += r.uniform(0.06, 0.16)
    # page flips (years)
    for k in range(18):
        m = int(0.12 * SR)
        y = np.convolve(r.standard_normal(m), np.ones(30) / 30, "same") * np.sin(np.linspace(0, np.pi, m))
        add(y, T_E + 3.2 + k * 0.22, 0.25)
    # clock ticking in the question
    for k in range(int((T_G - T_F) / 0.5)):
        m = int(0.025 * SR)
        x = np.arange(m) / SR
        add(np.sin(2 * np.pi * 2600 * x) * env(m, dec=180), T_F + 0.3 + k * 0.5, 0.18 if k % 2 == 0 else 0.12)
    # low drone under the question
    dr = np.sin(2 * np.pi * 55 * tt) * 0.5 + np.sin(2 * np.pi * 82.4 * tt) * 0.3
    out += dr * 0.05 * np.clip((tt - T_F) / 1.0, 0, 1) * np.clip((T_G - tt) / 0.3, 0, 1)
    # hit on "FOREVER?"
    m = int(1.2 * SR)
    x = np.arange(m) / SR
    add((np.sin(2 * np.pi * 45 * x) + 0.4 * r.standard_normal(m) * np.exp(-x * 20)) * np.exp(-x * 3), T_F + 2.0, 0.4)
    # door + swell: C major, rising
    for f in (261.6, 329.6, 392.0, 523.3):
        seg = (tt >= T_G + 1.6)
        out += seg * np.sin(2 * np.pi * f * tt) * 0.03 * np.clip((tt - T_G - 1.6) / 1.5, 0, 1) * \
            np.clip((TOTAL - tt) / 0.8, 0, 1)
    # birds
    for k in range(6):
        m = int(0.18 * SR)
        x = np.arange(m) / SR
        f = 3000 + 1500 * np.sin(2 * np.pi * 9 * x)
        add(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(m, atk=0.01, dec=12), T_G + 2.4 + k * 0.45, 0.05)
    # whooshes at cuts
    for t0 in (T_B, T_C, T_D, T_E, T_G):
        m = int(0.35 * SR)
        y = np.convolve(r.standard_normal(m), np.ones(40) / 40, "same") * np.sin(np.linspace(0, np.pi, m)) ** 2
        add(y / (np.abs(y).max() + 1e-9), t0 - 0.12, 0.12)
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
        times = args or [x * TOTAL / 24 + 0.4 for x in range(24)]
        for t in times:
            frame(int(t * FPS)).save(os.path.join(qc, f"f_{t:06.2f}.png"))
        print("stills", len(times))
        return
    wav = synth()
    out = os.path.join(HERE, "nine_to_five_forever.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                           f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium",
                           "-crf", "19", "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
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

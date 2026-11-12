#!/usr/bin/env python3
"""High-detail ('premium') versions of the three voiced 'Rate mal' Shorts.

Same voice, words and timing as ../textshorts, but with shaded, detailed illustrations,
glass panels, glow, particles. Renders 1080x1920 and encodes as 2160x3840 (4K portrait).

Usage: python3 make_hq.py [--stills] [--hd] [name ...]   names: hirnfrost, ohren, gaensehaut
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
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
TS = os.path.join(os.path.dirname(HERE), "textshorts")
sys.path.insert(0, HERE)
sys.path.insert(0, TS)
ARGS = sys.argv[1:]
import fx  # noqa: E402
import make as M  # noqa: E402  (textshorts: captions, word timing, engine imports)
from fx import E as BX, P, place  # noqa: E402

E = M.E
LL = M.LL
text, text_w, ease_out, ease_io, back_out, prog = M.text, M.text_w, M.ease_out, M.ease_io, M.back_out, M.prog
FONT_XB = M.FONT_XB
W, H, FPS, SR = 1080, 1920, 30, 48000
YELLOW, WHITE, RED, BLUE, GREEN = M.YELLOW, M.WHITE, M.RED, M.BLUE, M.GREEN
NAVY = (26, 16, 52)
CX, CY, CW, CH = 540, 830, 960, 700          # glass card
PW, PH = 920, 660                            # inner illustration area
PX0, PY0 = CX - PW // 2, CY - PH // 2
W_ = M.W_
CAP_Y = M.CAP_Y + 20


def spline(pts, n=10, closed=True):
    pts = list(pts)
    m = len(pts)
    out = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = pts[(i - 1) % m] if closed or i > 0 else pts[0]
        p1, p2 = pts[i], pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if closed or i + 2 < m else pts[-1]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    if not closed:
        out.append(pts[-1])
    return out


def poly_mask(w, h, pts, n=10):
    sp = spline(pts, n)
    return fx.mask(w, h, lambda d, k: d.polygon(P(sp, k), fill=255))


def clip(img, m):
    return fx.apply_mask(img, m)


def layer(w=PW, h=PH):
    return Image.new("RGBA", (int(w), int(h)))


def noise_tex(w, h, col, amt=10, blur=1.2, seed=1):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    im = Image.fromarray(np.clip(128 + n * 40, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    a = np.abs(np.array(im, np.float32) - 128) / 128 * amt * 6
    out = Image.new("RGBA", (w, h), tuple(col) + (0,))
    out.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    return out


def stroke_line(d, pts, col, w):
    d.line(pts, fill=col, width=max(1, int(w)), joint="curve")
    r = w / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=col)


def ss_layer(w, h, fn, ss=2):
    """draw fn(draw, k) on a 2x RGBA layer and downsample (anti-aliased colour drawing)."""
    big = Image.new("RGBA", (int(w) * ss, int(h) * ss))
    fn(ImageDraw.Draw(big), ss)
    return big.resize((int(w), int(h)), Image.LANCZOS)


# ------------------------------------------------------------------ shared UI
@lru_cache(None)
def card_sprite():
    g = fx.glass(CW, CH, 48, a0=34, a1=14, border=120)
    return fx.drop_shadow(g, dy=24, blur=30, alpha=0.5)


def card(img, a=1.0):
    place(img, card_sprite(), CX, CY + 12, alpha=a)


@lru_cache(None)
def inner_mask():
    return fx.mask(PW, PH, lambda d, k: d.rounded_rectangle(BX((0, 0, PW - 1, PH - 1), k), int(36 * k), fill=255))


def put_panel(img, lay, a=1.0, dy=0):
    lay = clip(lay, inner_mask())
    place(img, lay, CX, CY + dy, alpha=a)


@lru_cache(None)
def pill_sprite(s, col, size):
    tw = text_w(s, size, FONT_XB)
    w, h = tw + 76, int(size * 1.9)
    m = fx.mask(w, h, lambda d, k: d.rounded_rectangle(BX((0, 0, w - 1, h - 1), k), int(h / 2 * k), fill=255))
    body = fx.apply_mask(fx.lin(w, h, [(0, (34, 26, 72, 240)), (1, (14, 10, 34, 245))]), m)
    ring = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(7)))
    ol = Image.new("RGBA", (w, h), tuple(col) + (0,))
    ol.putalpha(ring)
    body = Image.alpha_composite(body, ol)
    hl = fx.mask(w, h, lambda d, k: d.rounded_rectangle(BX((h * 0.4, 5, w - h * 0.4, h * 0.42), k), int(h * 0.2 * k),
                                                        fill=255))
    hk = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    hk.putalpha(hl.point(lambda v: int(v * 0.10)))
    body = Image.alpha_composite(body, hk)
    return fx.glow(body, col, radius=18, strength=0.55)


def pill(img, s, cy, col, a, size=40):
    if a <= 0.02:
        return
    sc = 0.85 + 0.15 * back_out(min(1, a))
    place(img, pill_sprite(s, col, size), CX, cy, scale=sc, alpha=min(1, a))
    text(img, s, size * sc, CX, cy, fill=col, alpha=min(1, a), path=FONT_XB)


@lru_cache(None)
def qmark_sprite(size=230):
    f = ImageFont.truetype(M.E.FONT_BLACK, size)
    bb = f.getbbox("?")
    w, h = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
    m = Image.new("L", (w, h))
    ImageDraw.Draw(m).text((20 - bb[0], 20 - bb[1]), "?", font=f, fill=255)
    sp = fx.shaded(m, fx.lin(w, h, [(0, (255, 244, 140)), (0.55, (255, 210, 40)), (1, (240, 140, 20))]),
                   depth=0.08, outline=NAVY, ow=7, dark_a=0.5)
    return fx.drop_shadow(fx.glow(sp, (255, 200, 60), radius=26, strength=0.5), dy=14, blur=14)


def qmark(img, t, gt, x, y, rot=10):
    a = ease_out(prog(t, 0.5, 0.3))
    place(img, qmark_sprite(), x, y + 10 * math.sin(gt * 2.4), scale=(0.7 + 0.3 * back_out(a)) *
          (1 + 0.04 * math.sin(gt * 5)), rot=rot + 4 * math.sin(gt * 1.7), alpha=a)


def sparkles(img, gt, seed, box, n=18, col=(255, 255, 255), size=1.0):
    r = random.Random(seed)
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y, ph, sp = r.uniform(x0, x1), r.uniform(y0, y1), r.random(), r.uniform(0.5, 1.4)
        tw = 0.5 + 0.5 * math.sin(gt * 3 * sp + ph * 6.28)
        s = (3 + 7 * tw) * size
        a = int(200 * tw)
        d.line((x - s, y, x + s, y), fill=col + (a,), width=2)
        d.line((x, y - s, x, y + s), fill=col + (a,), width=2)
        d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=col + (min(255, a + 40),))
    img.alpha_composite(lay)


@lru_cache(None)
def caption_shade():
    lay = Image.new("RGBA", (W, 420))
    d = ImageDraw.Draw(lay)
    d.ellipse((60, 90, W - 60, 330), fill=(8, 4, 24, 150))
    return lay.filter(ImageFilter.GaussianBlur(50))


CAPQ = []


def cap(img, s, t, hl=()):
    """captions are drawn after the camera move (see draw_seg) so they stay sharp and still"""
    CAPQ.append((s, t, hl))


def draw_caption(img, s, t, hl):
    img.alpha_composite(caption_shade(), (0, CAP_Y - 210))
    lay = Image.new("RGBA", (W, 520))
    off = CAP_Y - 260
    M.caption(lay, s, t, size=70, hl=hl, y=260)
    a = lay.getchannel("A")
    sh = Image.new("RGBA", lay.size, (6, 2, 20, 0))
    sh.putalpha(a.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.75)))
    img.alpha_composite(sh, (0, off + 8))
    gl = Image.new("RGBA", lay.size, (255, 220, 80, 0))
    yel = np.array(lay, np.int16)
    ym = ((yel[..., 0] > 200) & (yel[..., 1] > 180) & (yel[..., 2] < 140) & (yel[..., 3] > 100)).astype(np.uint8) * 255
    gl.putalpha(Image.fromarray(ym).filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.8)))
    img.alpha_composite(gl, (0, off))
    img.alpha_composite(lay, (0, off))


@lru_cache(None)
def badge_sprite(kind, r=58):
    s = int(r * 2 + 20)
    cols = {"check": ((120, 240, 150), (30, 160, 80)), "warn": ((255, 120, 120), (190, 30, 50)),
            "cold": ((170, 230, 255), (40, 120, 220)), "heart": ((255, 140, 170), (200, 30, 80)),
            "note": ((220, 180, 255), (120, 60, 200)), "warm": ((255, 210, 120), (230, 100, 30))}[kind]
    m = fx.mask(s, s, lambda d, k: d.ellipse(BX((10, 10, s - 10, s - 10), k), fill=255))
    sp = fx.shaded(m, fx.rad(s, s, s * 0.38, s * 0.32, s * 0.8, [(0, cols[0]), (1, cols[1])]), depth=0.1,
                   outline=(255, 255, 255), ow=4)

    def ico(d, k):
        c = s / 2
        W_ = (255, 255, 255, 255)
        if kind == "check":
            d.line(P([(c - r * 0.45, c + 2), (c - r * 0.1, c + r * 0.35), (c + r * 0.5, c - r * 0.35)], k), fill=W_,
                   width=int(r * 0.22 * k), joint="curve")
        elif kind == "warn":
            d.rounded_rectangle(BX((c - 7, c - r * 0.55, c + 7, c + r * 0.15), k), int(6 * k), fill=W_)
            d.ellipse(BX((c - 8, c + r * 0.3, c + 8, c + r * 0.3 + 16), k), fill=W_)
        elif kind == "cold":
            for a in range(6):
                an = a * math.pi / 3
                ex, ey = c + r * 0.6 * math.cos(an), c + r * 0.6 * math.sin(an)
                d.line(P([(c, c), (ex, ey)], k), fill=W_, width=int(6 * k))
                for sgn in (-1, 1):
                    bx, by = c + r * 0.38 * math.cos(an), c + r * 0.38 * math.sin(an)
                    d.line(P([(bx, by), (bx + r * 0.2 * math.cos(an + sgn * 0.8), by + r * 0.2 * math.sin(an + sgn * 0.8))],
                             k), fill=W_, width=int(5 * k))
        elif kind == "heart":
            hr = r * 0.26
            d.ellipse(BX((c - 2 * hr, c - hr * 1.3, c, c + hr * 0.7), k), fill=W_)
            d.ellipse(BX((c, c - hr * 1.3, c + 2 * hr, c + hr * 0.7), k), fill=W_)
            d.polygon(P([(c - 1.95 * hr, c - 0.1 * hr), (c + 1.95 * hr, c - 0.1 * hr), (c, c + 2.0 * hr)], k), fill=W_)
        elif kind == "note":
            d.ellipse(BX((c - r * 0.42, c + r * 0.12, c - r * 0.02, c + r * 0.44), k), fill=W_)
            d.line(P([(c - r * 0.05, c + r * 0.28), (c - r * 0.05, c - r * 0.5)], k), fill=W_, width=int(7 * k))
            d.polygon(P([(c - r * 0.08, c - r * 0.5), (c + r * 0.38, c - r * 0.3), (c + r * 0.38, c - r * 0.12),
                         (c - r * 0.08, c - r * 0.3)], k), fill=W_)
        elif kind == "warm":
            d.polygon(P(spline([(c, c - r * 0.6), (c + r * 0.35, c - r * 0.05), (c + r * 0.3, c + r * 0.35),
                                (c, c + r * 0.5), (c - r * 0.3, c + r * 0.35), (c - r * 0.35, c)], 8), k), fill=W_)
    ic = ss_layer(s, s, ico, 3)
    sp = Image.alpha_composite(sp, ic)
    return fx.drop_shadow(sp, dy=8, blur=10, alpha=0.5)


def badge(img, kind, x, y, p, r=58):
    if p <= 0.02:
        return
    place(img, badge_sprite(kind, r), x, y, scale=0.4 + 0.6 * back_out(min(1, p)), alpha=min(1, p * 2))


def glow_dot(d, x, y, r, col, a=1.0):
    for k, aa in ((2.6, 40), (1.7, 90), (1.0, 255)):
        d.ellipse((x - r * k, y - r * k, x + r * k, y + r * k), fill=col + (int(aa * a),))


# ------------------------------------------------------------------ HEAD (profile, facing right)
HEAD = [(160, 610), (150, 520), (112, 440), (84, 350), (86, 250), (126, 160), (200, 100), (300, 76), (392, 104),
        (444, 168), (458, 228), (466, 268), (482, 296), (512, 334), (500, 352), (474, 362), (482, 386), (472, 400),
        (484, 418), (466, 440), (456, 470), (420, 494), (372, 500), (350, 540), (346, 610)]
HAIR = [(84, 330), (80, 240), (110, 158), (180, 92), (280, 58), (380, 76), (440, 130), (456, 190), (430, 160),
        (380, 140), (330, 146), (280, 170), (238, 216), (210, 280), (180, 330), (140, 380), (104, 392)]
SKIN_ST = [(0, (255, 222, 192)), (0.6, (248, 190, 152)), (1, (226, 156, 120))]


@lru_cache(None)
def head_sprite(section=False):
    w, h = 540, 620
    m = poly_mask(w, h, HEAD, 8)
    sk = fx.shaded(m, fx.lin(w, h, SKIN_ST, 20), depth=0.07, dark=(150, 60, 50), dark_a=0.5, hi_a=0.25)
    sk = Image.alpha_composite(sk, clip(noise_tex(w, h, (160, 90, 70), amt=3, seed=4), m))
    # cheek blush + jaw shade
    bl = layer(w, h)
    ImageDraw.Draw(bl).ellipse((360, 320, 450, 400), fill=(255, 120, 120, 70))
    ImageDraw.Draw(bl).ellipse((250, 430, 430, 560), fill=(170, 80, 60, 50))
    sk = Image.alpha_composite(sk, clip(bl.filter(ImageFilter.GaussianBlur(18)), m))
    if not section:
        # ear
        em = fx.mask(w, h, lambda d, k: d.ellipse(BX((214, 250, 290, 372), k), fill=255))
        ear = fx.shaded(em, fx.lin(w, h, SKIN_ST, 0), depth=0.04, dark=(160, 70, 60), dark_a=0.6)
        sk = Image.alpha_composite(sk, ear)
        d = ImageDraw.Draw(sk)
        d.arc((228, 266, 278, 356), 100, 300, fill=(200, 110, 90, 255), width=7)
        d.ellipse((246, 300, 262, 322), fill=(170, 85, 70, 255))
        # eye
        ey = ss_layer(w, h, lambda d, k: (
            d.ellipse(BX((398, 232, 446, 262), k), fill=(255, 255, 255, 255)),
            d.ellipse(BX((418, 233, 446, 261), k), fill=(70, 130, 200, 255)),
            d.ellipse(BX((425, 240, 440, 255), k), fill=(15, 15, 30, 255)),
            d.ellipse(BX((427, 241, 433, 247), k), fill=(255, 255, 255, 255)),
            d.arc(BX((394, 222, 450, 266), k), 190, 340, fill=(90, 50, 40, 255), width=int(5 * k)),
            d.arc(BX((390, 196, 458, 236), k), 200, 330, fill=(80, 50, 35, 255), width=int(9 * k))), 3)
        sk = Image.alpha_composite(sk, ey)
        # lips
        lp = ss_layer(w, h, lambda d, k: (
            d.polygon(P(spline([(470, 384), (484, 386), (481, 398), (468, 398)], 6), k), fill=(214, 100, 100, 255)),
            d.polygon(P(spline([(468, 404), (482, 404), (485, 418), (468, 418)], 6), k), fill=(200, 86, 90, 255)),
            d.line(P([(472, 360), (478, 340)], k), fill=(190, 110, 90, 200), width=int(3 * k))), 3)
        sk = Image.alpha_composite(sk, lp)
    # hair
    hm = poly_mask(w, h, HAIR, 8)
    hm = ImageChops.multiply(hm, m.filter(ImageFilter.MaxFilter(9)))
    hair = fx.shaded(hm, fx.lin(w, h, [(0, (110, 70, 45)), (1, (50, 30, 22))], 60), depth=0.06, hi=(255, 210, 160),
                     hi_a=0.25)
    hd = ImageDraw.Draw(hair)
    rr = random.Random(9)
    for _ in range(70):
        x0, y0 = rr.uniform(110, 430), rr.uniform(70, 200)
        pts = [(x0 + i * 14, y0 + i * (6 + rr.uniform(-2, 4)) + (i * i) * 0.8) for i in range(5)]
        hd.line(pts, fill=(160, 110, 70, 90) if rr.random() < 0.6 else (30, 18, 12, 110), width=2)
    hair = clip(hair, hm)
    sk = Image.alpha_composite(sk, hair)
    return sk


def head_xy(x, y, ox, oy, s):
    return ox + x * s, oy + y * s


# ------------------------------------------------------------------ ice cream
@lru_cache(None)
def icecream_sprite():
    w, h = 280, 460
    cone = [(66, 190), (214, 190), (140, 452)]
    cm = fx.mask(w, h, lambda d, k: d.polygon(P(cone, k), fill=255))
    cn = fx.shaded(cm, fx.lin(w, h, [(0, (246, 196, 120)), (1, (200, 130, 60))], 0), depth=0.1, dark=(110, 60, 20))
    hatch = layer(w, h)
    d = ImageDraw.Draw(hatch)
    for k in range(-6, 12):
        d.line((40 + k * 28, 190, 140 + k * 28 - 120, 470), fill=(170, 100, 40, 200), width=4)
        d.line((240 - k * 28, 190, 140 - k * 28 + 120, 470), fill=(170, 100, 40, 200), width=4)
    cn = Image.alpha_composite(cn, clip(hatch, cm))
    out = cn
    scoops = [(84, 160, 70, (255, 190, 210), (225, 110, 150)), (196, 160, 70, (190, 245, 220), (90, 190, 150)),
              (140, 96, 76, (255, 246, 222), (226, 200, 150))]
    for x, y, r, c0, c1 in scoops:
        def f(dd, k, x=x, y=y, r=r):
            pts = [(x + r * math.cos(a) * (1 + 0.06 * math.sin(a * 5)), y + r * math.sin(a) * (1 + 0.06 * math.sin(a * 5)))
                   for a in np.linspace(0, 2 * math.pi, 50)]
            dd.polygon(P(pts, k), fill=255)
            for dx in (-0.6, -0.1, 0.5):
                dd.ellipse(BX((x + dx * r - 12, y + r * 0.6, x + dx * r + 12, y + r * 1.1 + abs(dx) * 14), k), fill=255)
        sm = fx.mask(w, h, f)
        sc = fx.shaded(sm, fx.rad(w, h, x - r * 0.4, y - r * 0.5, r * 1.8, [(0, c0), (1, c1)]), depth=0.12,
                       dark=tuple(int(v * 0.5) for v in c1), dark_a=0.5, hi_a=0.5)
        out = Image.alpha_composite(fx.drop_shadow(sc, dy=6, blur=6, alpha=0.3).crop((18, 24, 18 + w, 24 + h)), out) \
            if False else Image.alpha_composite(out, sc)
    d = ImageDraw.Draw(out)
    rr = random.Random(3)
    for _ in range(26):
        x, y = rr.uniform(70, 210), rr.uniform(40, 200)
        if (x - 140) ** 2 / 80 ** 2 + (y - 120) ** 2 / 90 ** 2 > 1:
            continue
        an = rr.uniform(0, math.pi)
        c = rr.choice([(255, 80, 120), (90, 170, 255), (255, 220, 60), (120, 220, 120), (255, 255, 255)])
        d.line((x, y, x + 9 * math.cos(an), y + 9 * math.sin(an)), fill=c + (255,), width=5)
    for x, y, r in ((112, 70, 18), (60, 130, 12), (172, 130, 12)):
        d.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=(255, 255, 255, 150))
    return fx.drop_shadow(out, dy=16, blur=16, alpha=0.4)


def frost(img, gt, cx, cy, rad, n=14, a=1.0):
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    r = random.Random(7)
    for _ in range(n):
        ph = r.random()
        k = (gt * 0.35 + ph) % 1
        an = r.uniform(0, 2 * math.pi)
        x = cx + math.cos(an) * rad * (0.3 + k)
        y = cy + math.sin(an) * rad * 0.6 * (0.3 + k) - 40 * k
        s = r.uniform(3, 7)
        aa = int(220 * a * math.sin(k * math.pi))
        d.line((x - s, y, x + s, y), fill=(220, 245, 255, aa), width=2)
        d.line((x, y - s, x, y + s), fill=(220, 245, 255, aa), width=2)
    img.alpha_composite(lay)


@lru_cache(None)
def bolt_sprite(col=(255, 220, 60)):
    w, h = 130, 190
    pts = [(78, 6), (16, 104), (60, 104), (34, 184), (116, 72), (70, 72), (100, 6)]
    m = fx.mask(w, h, lambda d, k: d.polygon(P(pts, k), fill=255))
    c1 = tuple(int(v * 0.75) for v in col)
    sp = fx.shaded(m, fx.lin(w, h, [(0, (255, 255, 230)), (0.4, col), (1, c1)]), depth=0.1, outline=NAVY, ow=4)
    return fx.glow(sp, col, radius=20, strength=0.7)


# ------------------------------------------------------------------ HIRNFROST scenes
def hf_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    lay = layer()
    # soft spotlight inside the card
    sp = fx.rad(PW, PH, PW * 0.45, PH * 0.45, PW * 0.6, [(0, (120, 190, 255, 70)), (1, (120, 190, 255, 0))])
    lay.alpha_composite(sp)
    place(lay, head_sprite(), 320, 350, scale=1.0)
    ic_y = 330 + 12 * math.sin(gt * 2.2)
    place(lay, icecream_sprite(), 700, ic_y, scale=1.0, rot=18)
    put_panel(img, lay)
    frost(img, gt, PX0 + 700, PY0 + ic_y - 80, 140, a=1.0)
    if t > 1.0:
        a = ease_out(prog(t, 1.0, 0.3))
        place(img, bolt_sprite(), PX0 + 210, PY0 + 120, scale=0.9 + 0.08 * math.sin(gt * 9), rot=12, alpha=a)
        place(img, bolt_sprite(), PX0 + 110, PY0 + 210, scale=0.6 + 0.06 * math.sin(gt * 8 + 1), rot=-8, alpha=a)
    qmark(img, t, gt, 880, 560)
    cap(img, "Rate mal, was passiert, wenn du Eis zu schnell isst!", t, hl=("RATE", "MAL,", "EIS"))


# sagittal section geometry (panel coordinates)
SX, SY, SS = 150, 20, 1.0


def sx(x, y):
    return SX + x * SS, SY + y * SS


BRAIN_PTS = [(120, 250), (110, 180), (150, 120), (230, 92), (320, 96), (392, 130), (420, 190), (412, 246), (360, 268),
             (300, 262), (230, 280), (160, 280)]


def gyri(w, h, m, seed, n=60, col=(196, 90, 130, 200), hi=(255, 210, 225, 140), step=9, ln=9):
    lay = layer(w, h)
    d = ImageDraw.Draw(lay)
    r = random.Random(seed)
    bb = m.getbbox()
    for _ in range(n):
        x, y = r.uniform(bb[0], bb[2]), r.uniform(bb[1], bb[3])
        a = r.uniform(0, 2 * math.pi)
        pts = []
        for _ in range(ln):
            pts.append((x, y))
            a += r.uniform(-1.1, 1.1)
            x += step * math.cos(a)
            y += step * math.sin(a)
        d.line([(p[0] + 2, p[1] + 2) for p in pts], fill=hi, width=3, joint="curve")
        d.line(pts, fill=col, width=4, joint="curve")
    return clip(lay, m.filter(ImageFilter.MinFilter(5)))


@lru_cache(None)
def section_base():
    """sagittal head section without tongue / vessels / nerve."""
    lay = layer()
    hs = head_sprite(True)
    place(lay, hs, SX + hs.width / 2, SY + hs.height / 2)
    hm = Image.new("L", (PW, PH))
    hm.paste(poly_mask(540, 620, HEAD, 8), (SX, SY))
    # cut surface: inner tissue
    inner = hm.filter(ImageFilter.MinFilter(17))
    tis = fx.lin(PW, PH, [(0, (232, 140, 130)), (1, (190, 90, 90))], 70)
    tis = Image.alpha_composite(tis, noise_tex(PW, PH, (120, 40, 50), amt=4, seed=11))
    lay = Image.alpha_composite(lay, clip(tis, inner))
    # skull bone
    sk_pts = [(p[0] + SX, p[1] + SY) for p in [(100, 270), (96, 180), (140, 110), (230, 76), (330, 80), (410, 120),
                                              (446, 190), (440, 262), (380, 292), (300, 286), (220, 300), (140, 300)]]
    bm = poly_mask(PW, PH, sk_pts, 8)
    bone = fx.shaded(bm, fx.lin(PW, PH, [(0, (250, 240, 220)), (1, (220, 205, 180))]), depth=0.03, dark=(140, 120, 90))
    lay = Image.alpha_composite(lay, bone)
    # brain
    br = [(p[0] + SX, p[1] + SY) for p in BRAIN_PTS]
    brm = poly_mask(PW, PH, br, 8)
    brain = fx.shaded(brm, fx.lin(PW, PH, [(0, (255, 196, 210)), (1, (232, 140, 170))]), depth=0.05,
                      dark=(140, 40, 80), dark_a=0.55)
    brain = Image.alpha_composite(brain, gyri(PW, PH, brm, 5, n=90))
    lay = Image.alpha_composite(lay, brain)
    # nasal cavity
    nm = poly_mask(PW, PH, [sx(360, 300), sx(452, 290), sx(490, 330), sx(470, 352), sx(360, 350)], 6)
    lay = Image.alpha_composite(lay, fx.shaded(nm, fx.lin(PW, PH, [(0, (120, 40, 60)), (1, (80, 20, 40))]),
                                               depth=0.05, dark_a=0.6))
    # throat (pharynx)
    pm = poly_mask(PW, PH, [sx(318, 330), sx(352, 330), sx(356, 450), sx(348, 585), sx(318, 585), sx(312, 450)], 6)
    lay = Image.alpha_composite(lay, fx.shaded(pm, fx.lin(PW, PH, [(0, (110, 30, 50)), (1, (60, 10, 30))]),
                                               depth=0.1, dark_a=0.6))
    # mouth cavity
    mm = poly_mask(PW, PH, [sx(336, 372), sx(420, 366), sx(470, 376), sx(474, 410), sx(450, 446), sx(380, 456),
                            sx(336, 440)], 8)
    lay = Image.alpha_composite(lay, fx.shaded(mm, fx.lin(PW, PH, [(0, (110, 20, 40)), (1, (70, 10, 30))]),
                                               depth=0.1, dark_a=0.7))
    # palate band
    pal = [sx(330, 360), sx(380, 352), sx(440, 350), sx(470, 360), sx(472, 376), sx(440, 372), sx(380, 376),
           sx(334, 380)]
    plm = poly_mask(PW, PH, pal, 8)
    lay = Image.alpha_composite(lay, fx.shaded(plm, fx.lin(PW, PH, [(0, (255, 170, 180)), (1, (230, 110, 130))]),
                                               depth=0.25, hi_a=0.6))
    # teeth
    for (x0, y0, x1, y1) in ((458, 370, 476, 392), (452, 422, 470, 444)):
        a0, b0 = sx(x0, y0)
        a1, b1 = sx(x1, y1)
        tm = fx.mask(PW, PH, lambda d, k, a0=a0, b0=b0, a1=a1, b1=b1: d.rounded_rectangle(BX((a0, b0, a1, b1), k),
                                                                                           int(6 * k), fill=255))
        lay = Image.alpha_composite(lay, fx.shaded(tm, fx.lin(PW, PH, [(0, (255, 255, 250)), (1, (220, 220, 210))]),
                                                   depth=0.3, outline=(150, 140, 130), ow=1))
    # labels anchors drawn per frame
    return lay


@lru_cache(None)
def tongue_sprite():
    w, h = 200, 110
    pts = [(10, 100), (12, 50), (50, 18), (110, 10), (160, 22), (190, 50), (180, 80), (120, 96), (60, 104)]
    m = poly_mask(w, h, pts, 8)
    tg = fx.shaded(m, fx.lin(w, h, [(0, (255, 150, 165)), (1, (220, 90, 110))]), depth=0.15, hi_a=0.5,
                   dark=(120, 20, 40))
    tg = Image.alpha_composite(tg, clip(noise_tex(w, h, (180, 60, 80), amt=6, seed=2), m))
    ImageDraw.Draw(tg).line(spline([(40, 40), (100, 30), (170, 44)], 6, False), fill=(200, 80, 100, 160), width=3)
    return tg


def vessels(lay, w_scale, cold, warm=0.0):
    d = ImageDraw.Draw(lay)
    base = [sx(336, 366), sx(370, 362), sx(410, 360), sx(450, 362), sx(468, 368)]
    col = (int(220 - 60 * cold), int(40 + 40 * cold), int(60 + 100 * cold), 255)
    stroke_line(d, base, col, 6 * w_scale + 2)
    r = random.Random(4)
    for i in range(1, 4):
        x, y = base[i]
        for sgn in (-1, 1):
            pts = [(x, y)]
            for k in range(3):
                pts.append((pts[-1][0] + r.uniform(-14, 14), pts[-1][1] + sgn * r.uniform(4, 7)))
            d.line(pts, fill=col, width=max(1, int(3 * w_scale)))
    if cold > 0.02:
        fr = fx.rad(260, 260, 130, 130, 130, [(0, (150, 220, 255, int(170 * cold))), (1, (150, 220, 255, 0))]).resize((260, 120))
        lay.alpha_composite(fr, (int(sx(400, 360)[0] - 130), int(sx(400, 360)[1] - 60)))
    if warm > 0.02:
        fr = fx.rad(260, 260, 130, 130, 130, [(0, (255, 170, 80, int(170 * warm))), (1, (255, 170, 80, 0))]).resize((260, 120))
        lay.alpha_composite(fr, (int(sx(400, 366)[0] - 130), int(sx(400, 366)[1] - 60)))


NERVE = [(470, 352), (440, 330), (410, 290), (420, 250), (440, 200), (452, 160)]


def label(img, s, x, y, lx, ly, col=WHITE, a=1.0, size=28):
    """label at (x,y) with leader line to (lx,ly), canvas coordinates"""
    if a <= 0.02:
        return
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    d.line((x, y, lx, ly), fill=(255, 255, 255, int(200 * a)), width=3)
    d.ellipse((lx - 7, ly - 7, lx + 7, ly + 7), fill=(255, 255, 255, int(230 * a)))
    tw = text_w(s, size, FONT_XB) + 30
    d.rounded_rectangle((x - tw / 2, y - size * 0.85, x + tw / 2, y + size * 0.85), int(size * 0.85),
                        fill=(14, 10, 34, int(225 * a)), outline=col + (int(255 * a),), width=3)
    img.alpha_composite(lay)
    text(img, s, size, x, y, fill=col, alpha=a, path=FONT_XB)


def section(img, t, gt, cold=0.0, vessel=1.0, nerve=0.0, up=0.0, warm=0.0, ice=0.0, labels=True):
    lay = section_base().copy()
    tg = tongue_sprite()
    tx, ty = sx(404, 412 - 30 * up)
    place(lay, tg, tx, ty, scale=0.72)
    vessels(lay, vessel, cold, warm)
    if ice > 0.02:
        place(lay, icecream_sprite(), sx(560, 380)[0] + 40 * (1 - ice), sx(560, 380)[1], scale=0.55, rot=72,
              alpha=ice)
    put_panel(img, lay)
    if cold > 0.05:
        x, y = sx(400, 362)
        frost(img, gt, PX0 + x, PY0 + y, 70, n=10, a=cold)
    if nerve > 0.02:
        pts = [(PX0 + p[0], PY0 + p[1]) for p in (sx(*q) for q in spline(NERVE, 6, False))]
        k = max(2, int(len(pts) * min(1, nerve)))
        fx.line_glow(img, pts[:k], (255, 220, 60), 8, glow_w=34)
        lay2 = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(lay2)
        ph = (gt * 1.6) % 1
        px, py = pts[int(ph * (k - 1))]
        glow_dot(d, px, py, 9, (255, 255, 200))
        img.alpha_composite(lay2)
        if nerve >= 1.0:
            fx_, fy_ = PX0 + sx(440, 160)[0], PY0 + sx(440, 160)[1]
            pul = (gt * 1.5) % 1
            ring = Image.new("RGBA", (W, H))
            rd = ImageDraw.Draw(ring)
            for k2 in range(2):
                q = (pul + k2 * 0.5) % 1
                rr = 30 + 110 * q
                rd.ellipse((fx_ - rr, fy_ - rr, fx_ + rr, fy_ + rr), outline=(255, 80, 80, int(230 * (1 - q))), width=8)
            img.alpha_composite(ring)
            place(img, bolt_sprite((255, 120, 80)), fx_ + 70, fy_ - 70, scale=0.75 + 0.06 * math.sin(gt * 9), rot=-14)
    return lay


def hf_c1(img, t, gt, d):
    pill(img, "GAUMEN", 420, BLUE, ease_out(prog(t, 0.3, 0.3)))
    card(img)
    c = ease_out(prog(t, 0.6, 0.8))
    section(img, t, gt, cold=c, ice=ease_out(prog(t, 0.2, 0.5)))
    a = ease_out(prog(t, 1.0, 0.4))
    x, y = sx(400, 360)
    label(img, "GAUMEN", PX0 + 220, PY0 + 520, PX0 + x - 30, PY0 + y + 4, col=(150, 210, 255), a=a)
    label(img, "BLUTGEFÄSSE", PX0 + 690, PY0 + 600, PX0 + x + 40, PY0 + y + 2, col=(255, 130, 140),
          a=ease_out(prog(t, W_("Blutgefäße", fallback=2.0) - 0.1, 0.4)))
    label(img, "GEHIRN", PX0 + 200, PY0 + 80, PX0 + sx(250, 170)[0], PY0 + sx(250, 170)[1], col=(255, 190, 210), a=a)
    cap(img, "Das kalte Eis trifft deinen Gaumen – die Blutgefäße dort kühlen blitzschnell ab.", t,
        hl=("KALTE", "GAUMEN"))


def hf_c2(img, t, gt, d):
    tz, tw_ = W_("zusammen", fallback=0.5), W_("weiten", fallback=2.0)
    v = 1.0 - 0.7 * ease_io(prog(t, tz - 0.2, 0.6)) + 1.5 * ease_io(prog(t, tw_ - 0.1, 0.5))
    pill(img, "ZUSAMMEN …" if t < tw_ else "… UND WIEDER WEIT", 420, RED, 1.0)
    card(img)
    section(img, t, gt, cold=1.0, vessel=v)
    # zoom loupe on the vessel
    x, y = sx(410, 362)
    lx, ly = PX0 + 740, PY0 + 520
    lay = Image.new("RGBA", (W, H))
    dd = ImageDraw.Draw(lay)
    dd.line((PX0 + x, PY0 + y, lx, ly), fill=(255, 255, 255, 150), width=3)
    dd.ellipse((lx - 120, ly - 120, lx + 120, ly + 120), fill=(40, 10, 30, 235), outline=(255, 255, 255, 230), width=6)
    vw = 34 * v
    dd.rounded_rectangle((lx - 110, ly - vw / 2 - 10, lx + 110, ly + vw / 2 + 10), int(vw / 2 + 10),
                         fill=(255, 170, 170, 255))
    dd.rounded_rectangle((lx - 110, ly - vw / 2, lx + 110, ly + vw / 2), int(max(2, vw / 2)), fill=(200, 30, 50, 255))
    for k in range(6):
        xx = lx - 100 + ((gt * 90 * v + k * 40) % 200)
        dd.ellipse((xx - 9, ly - 6, xx + 9, ly + 6), fill=(255, 90, 100, 255))
    mk = Image.new("L", (W, H))
    ImageDraw.Draw(mk).ellipse((lx - 114, ly - 114, lx + 114, ly + 114), fill=255)
    inner = Image.new("RGBA", (W, H))
    inner.paste(lay, (0, 0), mk)
    ring = Image.new("RGBA", (W, H))
    ImageDraw.Draw(ring).line((PX0 + x, PY0 + y, lx - 85, ly - 85), fill=(255, 255, 255, 150), width=3)
    ImageDraw.Draw(ring).ellipse((lx - 120, ly - 120, lx + 120, ly + 120), outline=(255, 255, 255, 230), width=6)
    img.alpha_composite(ring)
    img.alpha_composite(inner)
    arr = "→ ←" if t < tw_ else "← →"
    text(img, arr, 54, lx, ly - 160, fill=YELLOW, stroke=6, sfill=NAVY)
    cap(img, "Sie ziehen sich zusammen – und weiten sich gleich danach wieder stark.", t, hl=("ZUSAMMEN", "WEITEN"))


def hf_c3(img, t, gt, d):
    pill(img, "GESICHTSNERV", 420, YELLOW, ease_out(prog(t, 0.2, 0.3)))
    card(img)
    nv = ease_out(prog(t, W_("Nerv", fallback=0.4) - 0.1, 1.4))
    section(img, t, gt, cold=1.0, vessel=1.5, nerve=nv)
    ts = W_("Stirn", fallback=3.5)
    if t > ts - 0.1:
        label(img, "STIRN", PX0 + 760, PY0 + 70, PX0 + sx(452, 150)[0], PY0 + sx(452, 150)[1], col=(255, 120, 120),
              a=ease_out(prog(t, ts - 0.1, 0.3)), size=34)
    label(img, "NERV", PX0 + 760, PY0 + 330, PX0 + sx(414, 280)[0], PY0 + sx(414, 280)[1], col=YELLOW,
          a=ease_out(prog(t, W_("Nerv", fallback=0.4), 0.4)))
    cap(img, "Ein Gesichtsnerv meldet das ans Gehirn – und du spürst den Schmerz in der STIRN!", t, hl=("STIRN!",))


@lru_cache(None)
def brain_sprite():
    w, h = 640, 480
    cer = [(60, 250), (50, 160), (110, 80), (220, 36), (360, 30), (480, 70), (570, 150), (600, 240), (560, 300),
           (470, 320), (380, 330), (290, 350), (200, 340), (110, 310)]
    m = poly_mask(w, h, cer, 10)
    br = fx.shaded(m, fx.rad(w, h, 260, 120, 420, [(0, (255, 214, 226)), (1, (226, 128, 160))]), depth=0.06,
                   dark=(130, 30, 70), dark_a=0.55, hi_a=0.4)
    br = Image.alpha_composite(br, gyri(w, h, m, 3, n=170, step=11, ln=10))
    # lobes separation lines
    d = ImageDraw.Draw(br)
    d.line(spline([(300, 330), (340, 260), (420, 210), (520, 190)], 8, False), fill=(170, 60, 100, 230), width=7)
    d.line(spline([(330, 40), (320, 120), (300, 200)], 8, False), fill=(170, 60, 100, 200), width=6)
    # cerebellum
    cm = poly_mask(w, h, [(380, 330), (470, 310), (560, 320), (590, 370), (540, 420), (440, 420), (390, 390)], 8)
    cb = fx.shaded(cm, fx.lin(w, h, [(0, (240, 150, 180)), (1, (200, 100, 140))]), depth=0.08, dark_a=0.5)
    dc = ImageDraw.Draw(cb)
    for k in range(9):
        y = 330 + k * 10
        dc.arc((390, y - 40, 590, y + 40), 10, 170, fill=(170, 70, 110, 160), width=3)
    cb = clip(cb, cm)
    # stem
    sm = poly_mask(w, h, [(330, 330), (380, 330), (400, 400), (390, 470), (350, 470), (340, 400)], 6)
    st = fx.shaded(sm, fx.lin(w, h, [(0, (240, 170, 190)), (1, (200, 120, 150))], 0), depth=0.2)
    out = Image.alpha_composite(Image.alpha_composite(st, cb), br)
    return fx.drop_shadow(out, dy=18, blur=22, alpha=0.45)


@lru_cache(None)
def stopwatch_face():
    s = 240
    m = fx.mask(s, s, lambda d, k: d.ellipse(BX((20, 30, s - 20, s - 10), k), fill=255))
    body = fx.shaded(m, fx.rad(s, s, 90, 90, 220, [(0, (250, 252, 255)), (1, (170, 180, 200))]), depth=0.06,
                     outline=(60, 70, 90), ow=5)
    d = ImageDraw.Draw(body)
    c = (s / 2, s / 2 + 10)
    for i in range(60):
        an = i / 60 * 2 * math.pi
        r0 = 82 if i % 5 else 72
        d.line((c[0] + r0 * math.sin(an), c[1] - r0 * math.cos(an), c[0] + 92 * math.sin(an),
                c[1] - 92 * math.cos(an)), fill=(40, 40, 60, 255), width=4 if i % 5 == 0 else 2)
    top = fx.mask(s, s, lambda d2, k: d2.rounded_rectangle(BX((s / 2 - 18, 0, s / 2 + 18, 34), k), int(6 * k),
                                                           fill=255))
    btn = fx.shaded(top, fx.lin(s, s, [(0, (240, 90, 90)), (1, (170, 30, 40))]), depth=0.3)
    return fx.drop_shadow(Image.alpha_composite(btn, body), dy=12, blur=14)


def stopwatch(img, x, y, frac, a):
    if a <= 0.02:
        return
    place(img, stopwatch_face(), x, y, alpha=a)
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    sp = stopwatch_face()
    c = (x, y + 10)
    d.pieslice((c[0] - 80, c[1] - 80, c[0] + 80, c[1] + 80), -90, -90 + 360 * frac, fill=(90, 220, 130, int(120 * a)))
    an = frac * 2 * math.pi
    d.line((c[0], c[1], c[0] + 78 * math.sin(an), c[1] - 78 * math.cos(an)), fill=(220, 40, 60, int(255 * a)), width=6)
    d.ellipse((c[0] - 9, c[1] - 9, c[0] + 9, c[1] + 9), fill=(40, 40, 60, int(255 * a)))
    img.alpha_composite(lay)
    del sp


def hf_c4(img, t, gt, d):
    pill(img, "KEIN EINFRIEREN", 420, GREEN, ease_out(prog(t, 0.3, 0.3)))
    card(img)
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW / 2, PH * 0.45, PW * 0.5, [(0, (255, 160, 200, 60)), (1, (255, 160, 200, 0))]))
    put_panel(img, lay)
    place(img, brain_sprite(), CX - 40, CY - 20 + 8 * math.sin(gt * 1.8), scale=1.12)
    sparkles(img, gt, 4, (PX0 + 60, PY0 + 40, PX0 + PW - 60, PY0 + PH - 60), n=14, col=(255, 230, 240))
    tn = W_("nicht", fallback=1.2) - 0.1
    badge(img, "check", 830, 600, ease_out(prog(t, tn, 0.4)), r=70)
    tm = W_("Sekunden", fallback=3.5) - 0.6
    pa = ease_out(prog(t, tm, 0.4))
    stopwatch(img, 830, 1030, ease_io(prog(t, tm + 0.2, 1.6)) * 0.5, pa)
    text(img, "37 °C", 50, 250, 1060, fill=WHITE, stroke=6, sfill=NAVY, alpha=ease_out(prog(t, tn + 0.3, 0.4)),
         path=FONT_XB)
    text(img, "bleibt warm", 30, 250, 1110, fill=(200, 230, 255), stroke=4, sfill=NAVY,
         alpha=ease_out(prog(t, tn + 0.3, 0.4)), path=FONT_XB)
    cap(img, "Keine Sorge: Dein Gehirn friert NICHT ein. Meist ist es nach wenigen Sekunden vorbei.", t, hl=("NICHT",))


@lru_cache(None)
def mug_sprite():
    w, h = 300, 300
    m = fx.mask(w, h, lambda d, k: (d.rounded_rectangle(BX((30, 60, 220, 280), k), int(30 * k), fill=255),
                                    d.ellipse(BX((30, 40, 220, 80), k), fill=255)))
    body = fx.shaded(m, fx.lin(w, h, [(0, (255, 120, 110)), (0.5, (230, 70, 80)), (1, (150, 30, 50))], 0), depth=0.08,
                     hi_a=0.5)
    hm = fx.mask(w, h, lambda d, k: d.ellipse(BX((180, 110, 280, 230), k), fill=255))
    hm = ImageChops.subtract(hm, fx.mask(w, h, lambda d, k: d.ellipse(BX((204, 136, 256, 204), k), fill=255)))
    hd = fx.shaded(hm, fx.lin(w, h, [(0, (240, 90, 90)), (1, (150, 30, 50))]), depth=0.2)
    out = Image.alpha_composite(hd, body)
    tm = fx.mask(w, h, lambda d, k: d.ellipse(BX((40, 46, 210, 76), k), fill=255))
    tea = fx.apply_mask(fx.lin(w, h, [(0, (190, 110, 50)), (1, (120, 60, 20))]), tm)
    out = Image.alpha_composite(out, tea)
    d = ImageDraw.Draw(out)
    d.ellipse((70, 52, 130, 62), fill=(255, 220, 170, 160))
    d.rounded_rectangle((52, 110, 72, 240), 10, fill=(255, 255, 255, 70))
    # heart on mug
    d.ellipse((100, 150, 130, 178), fill=(255, 240, 240, 230))
    d.ellipse((126, 150, 156, 178), fill=(255, 240, 240, 230))
    d.polygon([(101, 168), (155, 168), (128, 200)], fill=(255, 240, 240, 230))
    return fx.drop_shadow(out, dy=14, blur=16)


def steam(img, x, y, gt, a=1.0):
    lay = Image.new("RGBA", (220, 260))
    d = ImageDraw.Draw(lay)
    for k in range(3):
        ph = (gt * 0.5 + k / 3) % 1
        pts = [(60 + k * 45 + 16 * math.sin(i * 0.9 + gt * 3 + k), 240 - i * 22 - ph * 30) for i in range(9)]
        d.line(pts, fill=(255, 255, 255, int(150 * a * (1 - ph * 0.5))), width=12, joint="curve")
    lay = lay.filter(ImageFilter.GaussianBlur(4))
    img.alpha_composite(lay, (int(x - 110), int(y - 260)))


def hf_tip(img, t, gt, d):
    pill(img, "DER TRICK", 420, YELLOW, ease_out(prog(t, 0.2, 0.3)), size=46)
    card(img)
    up = ease_io(prog(t, W_("Zunge", fallback=0.8) - 0.1, 0.6))
    warm_t = W_("Warmes", fallback=2.2)
    warm = max(0.6 * up, ease_out(prog(t, warm_t, 0.8)))
    section(img, t, gt, cold=max(0, 0.8 - warm), vessel=1.0, up=up, warm=warm)
    x, y = sx(404, 380)
    lay = Image.new("RGBA", (W, H))
    dd = ImageDraw.Draw(lay)
    ax, ay = PX0 + x, PY0 + y + 70
    a = up
    dd.line((ax, ay + 90, ax, ay + 10), fill=YELLOW + (int(255 * a),), width=12)
    dd.polygon([(ax - 24, ay + 18), (ax + 24, ay + 18), (ax, ay - 16)], fill=YELLOW + (int(255 * a),))
    img.alpha_composite(lay)
    label(img, "ZUNGE", PX0 + 160, PY0 + 560, ax - 10, ay + 50, col=(255, 160, 180), a=up)
    p = back_out(prog(t, warm_t - 0.2, 0.5))
    if p > 0.03:
        place(img, mug_sprite(), 860, 1010, scale=0.8 * p)
        steam(img, 845, 920, gt, a=min(1, p))
    cap(img, "Zunge fest gegen den Gaumen drücken – oder etwas Warmes trinken!", t, hl=("ZUNGE", "WARMES"))


# ------------------------------------------------------------------ OHREN: sky, plane, ear
@lru_cache(None)
def sky_base(dusk=0.0):
    sky = fx.lin(PW, PH, [(0, (70, 120, 210)), (0.55, (150, 190, 240)), (0.8, (255, 200, 170)), (1, (255, 170, 130))])
    sun = fx.rad(PW, PH, PW * 0.78, PH * 0.62, 260, [(0, (255, 245, 210, 255)), (0.15, (255, 230, 170, 200)),
                                                     (1, (255, 200, 150, 0))])
    sky.alpha_composite(sun)
    # far hills + city
    d = ImageDraw.Draw(sky)
    d.polygon(spline([(-20, 560), (120, 520), (260, 540), (420, 510), (600, 535), (760, 515), (940, 540), (940, 700),
                      (-20, 700)], 6), fill=(110, 120, 170, 255))
    r = random.Random(2)
    x = 0
    while x < PW:
        bw, bh = r.uniform(20, 46), r.uniform(20, 80)
        d.rectangle((x, 570 - bh, x + bw, 600), fill=(80, 85, 130, 255))
        for wy in range(int(575 - bh), 595, 10):
            for wx in range(int(x + 5), int(x + bw - 5), 9):
                if r.random() < 0.3:
                    d.rectangle((wx, wy, wx + 3, wy + 4), fill=(255, 220, 140, 200))
        x += bw + r.uniform(2, 10)
    # ground + runway (perspective)
    d.rectangle((0, 590, PW, PH), fill=(80, 110, 80, 255))
    d.polygon([(380, 590), (540, 590), (760, PH), (160, PH)], fill=(70, 72, 82, 255))
    for k in range(6):
        y0 = 596 + k * 12
        f = (y0 - 590) / (PH - 590)
        cxr = 460 + 0 * f
        d.rectangle((cxr - 3 - 4 * f, y0, cxr + 3 + 4 * f, y0 + 6 + 3 * f), fill=(240, 240, 240, 255))
    for k in range(10):
        f = k / 9
        y0 = 590 + f * (PH - 590)
        xl = 380 - 220 * f
        xr = 540 + 220 * f
        for xx in (xl, xr):
            d.ellipse((xx - 3 - 3 * f, y0 - 3 - 3 * f, xx + 3 + 3 * f, y0 + 3 + 3 * f), fill=(255, 230, 120, 255))
    return sky.filter(ImageFilter.GaussianBlur(0.6))


@lru_cache(None)
def cloud_sprite(seed, w=360, h=150):
    r = random.Random(seed)
    m = Image.new("L", (w, h))
    d = ImageDraw.Draw(m)
    for _ in range(9):
        cx, cy = r.uniform(w * 0.2, w * 0.8), r.uniform(h * 0.45, h * 0.7)
        rr = r.uniform(h * 0.22, h * 0.38)
        d.ellipse((cx - rr * 1.3, cy - rr, cx + rr * 1.3, cy + rr), fill=255)
    d.rounded_rectangle((w * 0.12, h * 0.6, w * 0.88, h * 0.86), int(h * 0.13), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(3))
    c = fx.shaded(m, fx.lin(w, h, [(0, (255, 255, 255)), (1, (205, 215, 240))]), depth=0.12, dark=(120, 130, 180),
                  dark_a=0.35, hi_a=0.4)
    return c


@lru_cache(None)
def plane_sprite():
    w, h = 560, 240
    fus = [(40, 118), (70, 96), (150, 88), (420, 88), (490, 94), (530, 108), (540, 122), (520, 136), (470, 142),
           (150, 142), (70, 136)]
    fm = poly_mask(w, h, fus, 8)
    body = fx.shaded(fm, fx.lin(w, h, [(0, (255, 255, 255)), (0.55, (230, 234, 245)), (1, (160, 170, 195))]),
                     depth=0.12, dark=(60, 70, 100), dark_a=0.45, hi_a=0.6)
    d = ImageDraw.Draw(body)
    d.line(spline([(70, 124), (300, 124), (500, 122), (536, 118)], 6, False), fill=(30, 60, 140, 255), width=6)
    d.line(spline([(70, 132), (300, 132), (490, 130)], 6, False), fill=(240, 120, 40, 255), width=3)
    for k in range(17):
        x = 140 + k * 19
        d.rounded_rectangle((x, 102, x + 9, 113), 4, fill=(40, 60, 100, 255))
        d.point((x + 2, 104), fill=(200, 230, 255, 255))
    d.rounded_rectangle((115, 98, 129, 128), 4, outline=(150, 160, 180, 255), width=2)     # door
    d.polygon([(492, 100), (520, 106), (528, 114), (498, 112)], fill=(30, 50, 90, 255))   # cockpit
    d.line((496, 103, 520, 108), fill=(160, 210, 255, 255), width=2)
    body = clip(body, fm)
    # tail
    tm = fx.mask(w, h, lambda dd, k: dd.polygon(P([(50, 100), (20, 18), (56, 18), (130, 92)], k), fill=255))
    tail = fx.shaded(tm, fx.lin(w, h, [(0, (40, 80, 180)), (1, (20, 40, 110))]), depth=0.1, hi_a=0.4)
    ImageDraw.Draw(tail).polygon([(28, 36), (52, 36), (82, 66), (40, 62)], fill=(255, 150, 50, 255))
    tail = clip(tail, tm)
    # far wing + stabilizer
    wfar = fx.mask(w, h, lambda dd, k: dd.polygon(P([(250, 96), (300, 96), (230, 50), (210, 50)], k), fill=255))
    wf = fx.shaded(wfar, fx.lin(w, h, [(0, (190, 196, 215)), (1, (150, 158, 180))]), depth=0.1)
    stab = fx.mask(w, h, lambda dd, k: dd.polygon(P([(36, 112), (110, 112), (60, 146), (30, 146)], k), fill=255))
    sb = fx.shaded(stab, fx.lin(w, h, [(0, (220, 225, 240)), (1, (160, 170, 195))]), depth=0.15)
    # near wing + engine
    wn = fx.mask(w, h, lambda dd, k: dd.polygon(P([(220, 128), (330, 128), (250, 222), (210, 222)], k), fill=255))
    wing = fx.shaded(wn, fx.lin(w, h, [(0, (235, 238, 248)), (1, (150, 160, 185))], 0), depth=0.1, dark_a=0.5)
    em = fx.mask(w, h, lambda dd, k: dd.rounded_rectangle(BX((240, 160, 320, 192), k), int(16 * k), fill=255))
    eng = fx.shaded(em, fx.lin(w, h, [(0, (250, 250, 255)), (1, (130, 140, 165))]), depth=0.3, hi_a=0.6)
    de = ImageDraw.Draw(eng)
    de.ellipse((308, 160, 324, 192), fill=(40, 45, 60, 255))
    de.ellipse((312, 168, 320, 184), fill=(120, 130, 150, 255))
    # gear
    gear = layer(w, h)
    dg = ImageDraw.Draw(gear)
    for gx in (180, 440):
        dg.line((gx, 140, gx, 166), fill=(90, 90, 100, 255), width=5)
        dg.ellipse((gx - 9, 160, gx + 9, 178), fill=(30, 30, 35, 255))
    out = wf
    for part in (gear, tail, body, sb, wing, eng):
        out = Image.alpha_composite(out, part)
    ImageDraw.Draw(out).ellipse((262, 214, 270, 222), fill=(255, 60, 60, 255))
    return out


@lru_cache(None)
def plane_shadowed():
    return fx.drop_shadow(plane_sprite(), dy=10, blur=10, alpha=0.25)


def sky_scene(img, t, gt, px, py, scale, ang, a=1.0, extra=None):
    lay = sky_base().copy()
    for k, (seed, y, sp, sc) in enumerate(((1, 120, 18, 1.0), (2, 260, 30, 0.8), (3, 70, 12, 0.6), (4, 380, 45, 1.2))):
        x = (k * 300 - gt * sp) % (PW + 500) - 250
        place(lay, cloud_sprite(seed), x, y, scale=sc, alpha=0.95)
    # speed lines
    d = ImageDraw.Draw(lay)
    r = random.Random(3)
    for _ in range(10):
        y0 = r.uniform(40, 520)
        x0 = (r.uniform(0, PW) - gt * 600) % (PW + 200) - 100
        d.line((x0, y0, x0 + 80, y0), fill=(255, 255, 255, 70), width=3)
    place(lay, plane_shadowed(), px, py, scale=scale, rot=ang)
    if extra:
        extra(lay)
    put_panel(img, lay, a=a)


def oh_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    k = (t * 0.18) % 1
    sky_scene(img, t, gt, 240 + 420 * k, 200 + 180 * k, 0.95, -10)
    qmark(img, t, gt, 180, 640, rot=-10)
    cap(img, "Rate mal, was passiert, wenn ein Flugzeug landet!", t, hl=("RATE", "MAL,", "LANDET!"))


# ear section geometry (panel coordinates)
DRUM_X, DRUM_Y0, DRUM_Y1 = 430, 250, 400


@lru_cache(None)
def ear_base():
    lay = layer()
    # temporal bone background
    bg = fx.lin(PW, PH, [(0, (236, 214, 190)), (1, (200, 170, 145))], 60)
    bg = Image.alpha_composite(bg, noise_tex(PW, PH, (150, 110, 80), amt=5, blur=2, seed=6))
    lay = Image.alpha_composite(lay, bg)
    # skin / soft tissue band left
    sm = poly_mask(PW, PH, [(-40, -40), (330, -40), (300, 200), (310, 460), (340, PH + 40), (-40, PH + 40)], 6)
    lay = Image.alpha_composite(lay, fx.shaded(sm, fx.lin(PW, PH, [(0, (255, 214, 186)), (1, (236, 170, 140))], 0),
                                               depth=0.02, dark=(170, 90, 70)))
    # pinna (outer ear) cross-section
    pm = poly_mask(PW, PH, [(60, 120), (130, 60), (190, 120), (200, 250), (170, 280), (170, 420), (200, 470),
                            (150, 560), (80, 520), (40, 400), (30, 240)], 10)
    pin = fx.shaded(pm, fx.lin(PW, PH, [(0, (255, 205, 175)), (1, (230, 150, 125))], 0), depth=0.1,
                    dark=(160, 70, 60), dark_a=0.6, hi_a=0.45)
    ImageDraw.Draw(pin).arc((70, 110, 190, 520), 110, 250, fill=(200, 110, 90, 200), width=8)
    lay = Image.alpha_composite(lay, pin)
    # ear canal
    cm = poly_mask(PW, PH, [(150, 270), (300, 262), (430, 246), (436, 404), (300, 384), (150, 380)], 8)
    can = fx.shaded(cm, fx.lin(PW, PH, [(0, (255, 190, 170)), (0.5, (240, 150, 140)), (1, (210, 120, 120))]),
                    depth=0.18, dark=(120, 40, 50), dark_a=0.6, hi_a=0.3)
    dc = ImageDraw.Draw(can)
    r = random.Random(1)
    for _ in range(28):
        x = r.uniform(160, 270)
        top = r.random() < 0.5
        y = (272 if top else 378) + r.uniform(-2, 2)
        dc.line((x, y, x + r.uniform(6, 14), y + (12 if top else -12)), fill=(120, 80, 60, 200), width=2)
    lay = Image.alpha_composite(lay, clip(can, cm))
    # middle ear cavity (air)
    mm = poly_mask(PW, PH, [(436, 200), (540, 170), (620, 200), (640, 300), (610, 430), (540, 470), (450, 440)], 10)
    cav = fx.shaded(mm, fx.rad(PW, PH, 530, 300, 200, [(0, (220, 240, 255)), (1, (150, 190, 230))]), depth=0.08,
                    dark=(60, 80, 120), dark_a=0.5)
    lay = Image.alpha_composite(lay, cav)
    # inner ear: semicircular canals + cochlea
    ie = layer()
    di = ImageDraw.Draw(ie)
    for (bx, by, rx, ry, a0, a1) in ((700, 150, 60, 50, 180, 360), (760, 190, 56, 46, 270, 450),
                                     (690, 230, 50, 60, 90, 270)):
        di.arc((bx - rx, by - ry, bx + rx, by + ry), a0, a1, fill=(255, 220, 210, 255), width=22)
        di.arc((bx - rx, by - ry, bx + rx, by + ry), a0, a1, fill=(230, 150, 170, 255), width=12)
    ie = ie.filter(ImageFilter.GaussianBlur(0.8))
    lay = Image.alpha_composite(lay, ie)
    vm = fx.mask(PW, PH, lambda d, k: d.ellipse(BX((630, 220, 720, 320), k), fill=255))
    lay = Image.alpha_composite(lay, fx.shaded(vm, fx.lin(PW, PH, [(0, (255, 210, 220)), (1, (210, 130, 160))]),
                                               depth=0.15))
    # cochlea spiral
    cx0, cy0 = 735, 380
    cm2 = fx.mask(PW, PH, lambda d, k: d.ellipse(BX((cx0 - 92, cy0 - 84, cx0 + 92, cy0 + 84), k), fill=255))
    coch = fx.shaded(cm2, fx.rad(PW, PH, cx0 - 30, cy0 - 30, 140, [(0, (255, 210, 225)), (1, (200, 110, 150))]),
                     depth=0.12, dark=(110, 30, 70), dark_a=0.55, hi_a=0.4)
    dd = ImageDraw.Draw(coch)
    sp = [(cx0 + (6 + 80 * (1 - i / 160)) * math.cos(i * 0.12), cy0 + (6 + 72 * (1 - i / 160)) * math.sin(i * 0.12))
          for i in range(160)]
    dd.line(sp, fill=(150, 50, 100, 255), width=6, joint="curve")
    dd.line([(x + 3, y + 3) for x, y in sp], fill=(255, 230, 240, 150), width=2)
    lay = Image.alpha_composite(lay, coch)
    # auditory nerve
    nerve = layer()
    dn = ImageDraw.Draw(nerve)
    for k in range(5):
        dn.line(spline([(780, 360 + k * 6), (840, 330 + k * 5), (900, 300 + k * 4), (950, 290 + k * 4)], 6, False),
                fill=(255, 220, 90, 255), width=5)
    lay = Image.alpha_composite(lay, nerve)
    return lay


@lru_cache(None)
def tube_sprite(open_=False):
    lay = layer()
    pts = [(540, 466), (600, 520), (680, 580), (780, 640), (860, 700)]
    sp = spline(pts, 8, False)
    w0 = 46 if open_ else 30
    outer = fx.mask(PW, PH, lambda d, k: d.line(P(sp, k), fill=255, width=int(w0 * k), joint="curve"))
    tube = fx.shaded(outer, fx.lin(PW, PH, [(0, (255, 200, 190)), (1, (220, 130, 130))]), depth=0.25)
    inner_w = 26 if open_ else 4
    im = fx.mask(PW, PH, lambda d, k: d.line(P(sp, k), fill=255, width=int(inner_w * k), joint="curve"))
    col = (190, 220, 250) if open_ else (150, 60, 70)
    tube = Image.alpha_composite(tube, fx.apply_mask(Image.new("RGBA", (PW, PH), col + (255,)), im))
    return lay if False else tube


@lru_cache(None)
def ossicles(off=0):
    lay = layer()
    o = off
    parts = [
        ([(DRUM_X + 4 + o, 330), (DRUM_X + 26 + o, 300), (DRUM_X + 40 + o, 250), (DRUM_X + 66 + o, 236),
          (DRUM_X + 80 + o, 256), (DRUM_X + 56 + o, 270), (DRUM_X + 34 + o, 320)], (250, 240, 215)),   # malleus
        ([(DRUM_X + 70 + o, 240), (DRUM_X + 110, 232), (DRUM_X + 130, 260), (DRUM_X + 120, 300),
          (DRUM_X + 104, 300), (DRUM_X + 100, 270), (DRUM_X + 80, 268)], (240, 228, 200)),               # incus
    ]
    for pts, c in parts:
        m = poly_mask(PW, PH, pts, 6)
        lay = Image.alpha_composite(lay, fx.shaded(m, fx.lin(PW, PH, [(0, c), (1, (190, 175, 140))]), depth=0.3,
                                                   outline=(120, 100, 70), ow=2))
    # stapes (stirrup)
    st = layer()
    d = ImageDraw.Draw(st)
    d.line([(DRUM_X + 116, 300), (DRUM_X + 150, 318), (DRUM_X + 196, 300)], fill=(120, 100, 70, 255), width=9,
           joint="curve")
    d.line([(DRUM_X + 116, 300), (DRUM_X + 150, 318), (DRUM_X + 196, 300)], fill=(245, 232, 205, 255), width=6,
           joint="curve")
    d.line([(DRUM_X + 116, 300), (DRUM_X + 150, 290), (DRUM_X + 196, 300)], fill=(245, 232, 205, 255), width=6)
    d.rounded_rectangle((DRUM_X + 192, 282, DRUM_X + 204, 320), 4, fill=(245, 232, 205, 255),
                        outline=(120, 100, 70, 255), width=2)
    return Image.alpha_composite(lay, st)


def drum(lay, push):
    bend = 46 * push
    pts = [(DRUM_X - 6, DRUM_Y0), (DRUM_X + bend * 0.6, (DRUM_Y0 + DRUM_Y1) / 2 - 30),
           (DRUM_X + bend, (DRUM_Y0 + DRUM_Y1) / 2 + 10), (DRUM_X + bend * 0.6, DRUM_Y1 - 30), (DRUM_X - 6, DRUM_Y1)]
    sp = spline(pts, 8, False)
    m = fx.mask(PW, PH, lambda d, k: d.line(P(sp, k), fill=255, width=int(14 * k), joint="curve"))
    dm = fx.shaded(m, fx.lin(PW, PH, [(0, (255, 160, 170)), (1, (220, 90, 110))]), depth=0.4, hi_a=0.7)
    lay.alpha_composite(dm)
    return bend


def ear_scene(img, t, gt, push=0.0, tube=0.0, labels=1.0, air_in=0.0):
    lay = ear_base().copy()
    if tube < 0.99:
        lay.alpha_composite(tube_sprite(False))
    if tube > 0.01:
        ts = tube_sprite(True)
        if tube < 0.999:
            ts = ts.copy()
            ts.putalpha(ts.getchannel("A").point(lambda v: int(v * tube)))
        lay.alpha_composite(ts)
    bend = drum(lay, push)
    lay.alpha_composite(ossicles(int(round(bend * 0.6 / 4) * 4)))
    d = ImageDraw.Draw(lay)
    # outside pressure particles in the ear canal
    if push > 0.05:
        r = random.Random(5)
        for i in range(26):
            ph = r.random()
            x = 160 + ((gt * 120 * (0.6 + push) + ph * 280) % (DRUM_X - 170 + bend * 0.5))
            y = r.uniform(285, 365)
            glow_dot(d, x, y, 5, (90, 160, 255), a=min(1, push * 1.3))
    # air flowing up the open tube into the middle ear
    if air_in > 0.02:
        sp = spline([(860, 700), (780, 640), (680, 580), (600, 520), (540, 466), (530, 400)], 6, False)
        for i in range(10):
            q = (gt * 0.6 + i / 10) % 1
            x, y = sp[int(q * (len(sp) - 1))]
            glow_dot(d, x, y, 6, (120, 190, 255), a=air_in * math.sin(q * math.pi))
    # middle-ear air dots (calm)
    r2 = random.Random(8)
    for i in range(10):
        x = r2.uniform(470, 600) + 6 * math.sin(gt * 1.5 + i)
        y = r2.uniform(220, 430) + 6 * math.cos(gt * 1.3 + i)
        glow_dot(d, x, y, 4, (255, 255, 255), a=0.6)
    put_panel(img, lay)
    return bend


def oh_labels(img, a, which=("TROMMELFELL", "LUFT", "GEHÖRGANG")):
    if "TROMMELFELL" in which:
        label(img, "TROMMELFELL", PX0 + 380, PY0 + 110, PX0 + DRUM_X, PY0 + DRUM_Y0 + 20, col=YELLOW, a=a)
    if "LUFT" in which:
        label(img, "MITTELOHR: LUFT", PX0 + 560, PY0 + 560, PX0 + 540, PY0 + 400, col=(160, 210, 255), a=a)
    if "GEHÖRGANG" in which:
        label(img, "GEHÖRGANG", PX0 + 200, PY0 + 470, PX0 + 250, PY0 + 330, col=(255, 200, 180), a=a)
    if "SCHNECKE" in which:
        label(img, "SCHNECKE", PX0 + 770, PY0 + 520, PX0 + 740, PY0 + 440, col=(255, 170, 210), a=a)


def oh_c1(img, t, gt, d):
    pill(img, "IM OHR", 420, BLUE, ease_out(prog(t, 0.2, 0.3)))
    card(img)
    ear_scene(img, t, gt)
    oh_labels(img, ease_out(prog(t, 0.5, 0.4)), ("TROMMELFELL", "GEHÖRGANG", "SCHNECKE"))
    oh_labels(img, ease_out(prog(t, W_("Luft", fallback=2.5) - 0.2, 0.4)), ("LUFT",))
    cap(img, "Hinter deinem Trommelfell sitzt ein kleiner Raum voller Luft.", t, hl=("TROMMELFELL", "LUFT."))


@lru_cache(None)
def gauge_face():
    s = 330
    c = s / 2
    m = fx.mask(s, s, lambda d, k: d.ellipse(BX((10, 10, s - 10, s - 10), k), fill=255))
    bez = fx.shaded(m, fx.lin(s, s, [(0, (250, 252, 255)), (0.5, (170, 178, 195)), (1, (90, 96, 115))], 45),
                    depth=0.05, hi_a=0.6)
    fm = fx.mask(s, s, lambda d, k: d.ellipse(BX((34, 34, s - 34, s - 34), k), fill=255))
    face = fx.apply_mask(fx.rad(s, s, c, c * 0.8, c, [(0, (40, 50, 90)), (1, (12, 14, 34))]), fm)
    out = Image.alpha_composite(bez, face)
    d = ImageDraw.Draw(out)
    f = ImageFont.truetype(FONT_XB, 20)
    for i in range(36):
        v = 700 + i * 10
        fr = (v - 700) / 350
        an = math.radians(135 + 270 * fr)
        big = v % 50 == 0
        r0 = 102 if big else 112
        col = (255, 110, 110, 255) if v >= 980 else (230, 235, 255, 255)
        d.line((c + r0 * math.cos(an), c + r0 * math.sin(an), c + 124 * math.cos(an), c + 124 * math.sin(an)),
               fill=col, width=4 if big else 2)
        if big and v % 100 == 0:
            d.text((c + 82 * math.cos(an), c + 82 * math.sin(an)), str(v), font=f, fill=(230, 235, 255, 255),
                   anchor="mm")
    d.text((c, c + 56), "hPa", font=ImageFont.truetype(FONT_XB, 22), fill=(170, 190, 230, 255), anchor="mm")
    return fx.drop_shadow(out, dy=16, blur=18, alpha=0.5)


def gauge(img, cx, cy, val, a=1.0):
    place(img, gauge_face(), cx, cy, alpha=a)
    fr = (val - 700) / 350
    an = math.radians(135 + 270 * fr)
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    d.line((cx + 4, cy + 6, cx + 110 * math.cos(an) + 4, cy + 110 * math.sin(an) + 6), fill=(0, 0, 0, int(110 * a)),
           width=9)
    d.line((cx - 24 * math.cos(an), cy - 24 * math.sin(an), cx + 112 * math.cos(an), cy + 112 * math.sin(an)),
           fill=(255, 70, 70, int(255 * a)), width=7)
    d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=(220, 225, 240, int(255 * a)))
    d.ellipse((cx - 72, cy - 72 - 20, cx + 30, cy - 40), fill=(255, 255, 255, int(28 * a)))
    img.alpha_composite(lay)
    text(img, f"{int(val)}", 40, cx, cy + 96, fill=WHITE, alpha=a, path=FONT_XB)


def oh_c2(img, t, gt, d):
    pill(img, "SINKFLUG", 420, YELLOW, ease_out(prog(t, 0.2, 0.3)))
    card(img)
    k = ease_io(prog(t, 0.3, 3.8))
    sky_scene(img, t, gt, 200 + 300 * k, 140 + 260 * k, 0.7, -12)
    gauge(img, 820, 1000, 760 + 253 * k)
    text(img, "KABINENDRUCK", 30, 820, 818, fill=WHITE, stroke=5, sfill=NAVY, path=FONT_XB)
    text(img, "↑", 70, 640, 1000, fill=YELLOW, stroke=6, sfill=NAVY, alpha=ease_out(prog(t, 1.0, 0.4)))
    cap(img, "Beim Sinkflug steigt der Luftdruck in der Kabine – und drückt auf dein Trommelfell.", t,
        hl=("STEIGT", "TROMMELFELL."))


def oh_c3(img, t, gt, d):
    ta = W_("Druck", fallback=1.2)
    if t > ta:
        pill(img, "AUA!", 420, RED, ease_out(prog(t, ta, 0.3)), size=54)
    card(img)
    push = ease_out(prog(t, W_("wölbt", fallback=0.3) - 0.3, 0.8))
    bend = ear_scene(img, t, gt, push=max(push, 0.25))
    oh_labels(img, 1.0, ("TROMMELFELL",))
    if push > 0.5:
        x, y = PX0 + DRUM_X + bend, PY0 + (DRUM_Y0 + DRUM_Y1) / 2
        lay = Image.new("RGBA", (W, H))
        dd = ImageDraw.Draw(lay)
        q = (gt * 1.4) % 1
        for k in range(2):
            qq = (q + k * 0.5) % 1
            rr = 30 + 90 * qq
            dd.ellipse((x - rr, y - rr, x + rr, y + rr), outline=(255, 70, 90, int(220 * (1 - qq))), width=7)
        img.alpha_composite(lay)
    text(img, "→ → →", 50, PX0 + 270, PY0 + 210, fill=(140, 190, 255), stroke=6, sfill=NAVY,
         alpha=ease_out(prog(t, 0.4, 0.4)))
    cap(img, "Die Luft dahinter kommt nicht hinterher: Das Trommelfell wölbt sich nach innen – das drückt!", t,
        hl=("INNEN",))


def oh_c4(img, t, gt, d):
    op = ease_out(prog(t, W_("Ohrtrompete", fallback=0.6) - 0.2, 0.6))
    tp = W_("Plopp", fallback=1.6)
    eq = ease_out(prog(t, W_("Druck", fallback=1.0) - 0.2, 0.8))
    card(img)
    ear_scene(img, t, gt, push=1 - eq, tube=op, air_in=op)
    label(img, "OHRTROMPETE", PX0 + 690, PY0 + 560, PX0 + 680, PY0 + 585, col=(150, 220, 255), a=op)
    label(img, "→ RACHEN", PX0 + 800, PY0 + 630, PX0 + 860, PY0 + 690, col=WHITE, a=op, size=24)
    if t > tp - 0.05:
        E.stamp(img, "PLOPP!", t, tp - 0.05, cx=540, cy=420, size=150, rot=-6, fill=YELLOW, sfill=(170, 20, 0))
        E.burst(img, PX0 + DRUM_X, PY0 + 325, t, tp - 0.05, color=YELLOW, n=14, rad=160)
    cap(img, "Die Ohrtrompete öffnet sich, der Druck gleicht sich aus – PLOPP!", t, hl=("OHRTROMPETE", "PLOPP!"))


@lru_cache(None)
def row_sprite(w=860, h=136):
    return fx.drop_shadow(fx.glass(w, h, 34, a0=60, a1=26), dy=10, blur=14, alpha=0.35)


@lru_cache(None)
def icon_sprite(kind):
    s = 130
    out = layer(s, s)
    if kind == "glass":
        m = fx.mask(s, s, lambda d, k: d.polygon(P([(30, 14), (100, 14), (92, 120), (38, 120)], k), fill=255))
        gl = fx.apply_mask(fx.lin(s, s, [(0, (220, 240, 255, 120)), (1, (180, 210, 240, 160))], 0), m)
        wm = fx.mask(s, s, lambda d, k: d.polygon(P([(36, 50), (96, 50), (92, 116), (40, 116)], k), fill=255))
        wa = fx.apply_mask(fx.lin(s, s, [(0, (110, 190, 255, 230)), (1, (40, 110, 220, 240))]), wm)
        out = Image.alpha_composite(Image.alpha_composite(out, gl), wa)
        d = ImageDraw.Draw(out)
        d.line((30, 14, 38, 120), fill=(255, 255, 255, 230), width=4)
        d.line((100, 14, 92, 120), fill=(255, 255, 255, 230), width=4)
        d.line((44, 24, 48, 110), fill=(255, 255, 255, 160), width=6)
        for bx, by in ((60, 90), (74, 72), (66, 64)):
            d.ellipse((bx - 4, by - 4, bx + 4, by + 4), outline=(255, 255, 255, 200), width=2)
    elif kind == "yawn":
        m = fx.mask(s, s, lambda d, k: d.ellipse(BX((8, 8, s - 8, s - 8), k), fill=255))
        out = fx.shaded(m, fx.rad(s, s, 45, 40, 110, [(0, (255, 236, 120)), (1, (240, 170, 30))]), depth=0.1)
        d = ImageDraw.Draw(out)
        d.arc((28, 40, 56, 60), 200, 340, fill=(90, 50, 20, 255), width=5)
        d.arc((74, 40, 102, 60), 200, 340, fill=(90, 50, 20, 255), width=5)
        d.ellipse((46, 66, 84, 112), fill=(110, 30, 40, 255))
        d.ellipse((54, 90, 76, 110), fill=(240, 110, 120, 255))
        d.ellipse((100, 28, 116, 50), fill=(140, 200, 255, 230))
    elif kind == "gum":
        m = fx.mask(s, s, lambda d, k: d.ellipse(BX((10, 10, s - 10, s - 10), k), fill=255))
        out = fx.shaded(m, fx.rad(s, s, 45, 40, 120, [(0, (255, 200, 230)), (1, (230, 90, 160))]), depth=0.12,
                        hi_a=0.5)
        d = ImageDraw.Draw(out)
        d.ellipse((34, 28, 62, 50), fill=(255, 255, 255, 170))
        d.ellipse((70, 76, 80, 84), fill=(255, 255, 255, 100))
    elif kind == "bottle":
        m = fx.mask(s, s, lambda d, k: (d.rounded_rectangle(BX((38, 40, 92, 124), k), int(16 * k), fill=255)))
        bt = fx.apply_mask(fx.lin(s, s, [(0, (240, 248, 255, 200)), (1, (200, 220, 240, 220))], 0), m)
        mk = fx.mask(s, s, lambda d, k: d.rounded_rectangle(BX((40, 66, 90, 122), k), int(14 * k), fill=255))
        milk = fx.apply_mask(Image.new("RGBA", (s, s), (255, 252, 240, 255)), mk)
        tm = fx.mask(s, s, lambda d, k: (d.ellipse(BX((52, 4, 78, 30), k), fill=255),
                                         d.rectangle(BX((50, 16, 80, 34), k), fill=255)))
        teat = fx.shaded(tm, fx.lin(s, s, [(0, (255, 220, 160)), (1, (230, 170, 90))]), depth=0.2)
        ring = fx.mask(s, s, lambda d, k: d.rounded_rectangle(BX((34, 30, 96, 44), k), int(5 * k), fill=255))
        rg = fx.shaded(ring, fx.lin(s, s, [(0, (140, 200, 255)), (1, (60, 120, 220))]), depth=0.3)
        out = Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(out, bt), milk),
                                                          teat), rg)
        d = ImageDraw.Draw(out)
        for k in range(3):
            d.line((80, 80 + k * 14, 88, 80 + k * 14), fill=(90, 140, 200, 255), width=2)
        d.line((46, 50, 46, 114), fill=(255, 255, 255, 200), width=4)
    return fx.drop_shadow(out, dy=6, blur=8, alpha=0.4)


def oh_tip(img, t, gt, d):
    pill(img, "SO HILFST DU NACH", 420, YELLOW, ease_out(prog(t, 0.2, 0.3)), size=42)
    items = [("SCHLUCKEN", "glass", W_("Schlucken", fallback=0.4) - 0.1),
             ("GÄHNEN", "yawn", W_("gähnen", fallback=1.1) - 0.1),
             ("KAUGUMMI KAUEN", "gum", W_("Kaugummi", fallback=1.8) - 0.1),
             ("BABYS: TRINKEN", "bottle", W_("Babys", fallback=3.0) - 0.1)]
    for k, (lab, ico, t0) in enumerate(items):
        p = ease_out(prog(t, t0, 0.45))
        if p <= 0.02:
            continue
        y = 560 + k * 165
        x = CX + 60 * (1 - p)
        place(img, row_sprite(), x, y, alpha=p)
        place(img, icon_sprite(ico), x - 320, y + 2, scale=0.75 + 0.25 * back_out(p), alpha=p,
              rot=(6 * math.sin(gt * 3) if ico == "yawn" else 0))
        text(img, lab, 50, x + 60, y, fill=WHITE, stroke=5, sfill=NAVY, alpha=p, path=FONT_XB)
        badge(img, "check", x + 360, y, ease_out(prog(t, t0 + 0.25, 0.4)), r=30)
    cap(img, "Schlucken, gähnen oder Kaugummi kauen. Babys hilft Trinken beim Landen.", t,
        hl=("SCHLUCKEN,", "GÄHNEN", "KAUGUMMI"))


# ------------------------------------------------------------------ GÄNSEHAUT
AW, AH = PW, PH


@lru_cache(None)
def arm_base():
    lay = layer()
    lay.alpha_composite(fx.lin(PW, PH, [(0, (110, 150, 220, 90)), (1, (60, 80, 160, 40))]))
    pts = [(-60, 170), (300, 150), (600, 160), (980, 140), (980, 520), (600, 500), (300, 510), (-60, 500)]
    m = poly_mask(PW, PH, pts, 8)
    arm = fx.shaded(m, fx.lin(PW, PH, [(0, (255, 226, 200)), (0.45, (250, 196, 160)), (1, (205, 140, 110))]),
                    depth=0.1, dark=(150, 70, 60), dark_a=0.45, hi_a=0.35)
    arm = Image.alpha_composite(arm, clip(noise_tex(PW, PH, (160, 90, 70), amt=4, blur=0.8, seed=12), m))
    d = ImageDraw.Draw(arm)
    r = random.Random(14)
    for _ in range(14):
        y = r.uniform(200, 470)
        x = r.uniform(0, PW)
        d.arc((x - 90, y - 10, x + 90, y + 10), 200, 340, fill=(200, 140, 120, 60), width=2)
    vein = spline([(0, 380), (200, 360), (420, 390), (640, 350), (920, 370)], 8, False)
    d.line(vein, fill=(150, 150, 200, 60), width=10, joint="curve")
    d.line(spline([(300, 420), (480, 400), (700, 430), (920, 410)], 8, False), fill=(150, 150, 200, 45), width=7,
           joint="curve")
    # freckles / pores
    for _ in range(260):
        x, y = r.uniform(0, PW), r.uniform(170, 500)
        s_ = r.uniform(0.8, 2.2)
        d.ellipse((x - s_, y - s_, x + s_, y + s_), fill=(190, 120, 95, int(r.uniform(40, 110))))
    for _ in range(10):
        x, y = r.uniform(0, PW), r.uniform(220, 460)
        d.ellipse((x - 4, y - 3, x + 4, y + 3), fill=(170, 100, 70, 90))
    arm = clip(arm, m)
    # rim light on the upper edge + soft cast shadow below the arm
    rim = layer()
    ImageDraw.Draw(rim).line(spline([(-60, 172), (300, 152), (600, 162), (980, 142)], 8, False),
                             fill=(255, 245, 230, 200), width=8)
    rim = clip(rim.filter(ImageFilter.GaussianBlur(4)), m)
    sh = layer()
    ImageDraw.Draw(sh).polygon([(-60, 505), (300, 515), (600, 505), (980, 525), (980, 600), (-60, 590)],
                               fill=(20, 10, 40, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    out = Image.alpha_composite(lay, sh)
    return Image.alpha_composite(Image.alpha_composite(out, arm), rim)


FOLL = [(random.Random(i).uniform(30, PW - 30), random.Random(i * 7 + 3).uniform(200, 480)) for i in range(70)]


@lru_cache(None)
def bump_sprite():
    s = 40
    m = fx.mask(s, s, lambda d, k: d.ellipse(BX((4, 4, s - 4, s - 4), k), fill=255)).filter(ImageFilter.GaussianBlur(2))
    return fx.shaded(m, fx.rad(s, s, 14, 12, 34, [(0, (255, 232, 210)), (1, (230, 160, 130))]), depth=0.25,
                     dark=(150, 70, 50), dark_a=0.7, hi_a=0.7)


def arm_scene(img, gt, bumps, cold=0.0):
    lay = arm_base().copy()
    d = ImageDraw.Draw(lay)
    for i, (x, y) in enumerate(FOLL):
        if bumps > 0.02:
            place(lay, bump_sprite(), x, y, scale=0.45 + 0.55 * bumps)
        ang = math.radians(18 + 62 * bumps + 4 * math.sin(gt * 2 + i))
        ln = 34 + (i % 5) * 4
        x2, y2 = x + ln * math.cos(ang), y - ln * math.sin(ang)
        mx, my = (x + x2) / 2 + 3, (y + y2) / 2 + 2
        d.line([(x, y), (mx, my), (x2, y2)], fill=(80, 50, 35, 220), width=2, joint="curve")
    if cold > 0.02:
        lay.alpha_composite(fx.lin(PW, PH, [(0, (150, 210, 255, int(90 * cold))), (1, (150, 210, 255, 0))]))
    put_panel(img, lay)
    if cold > 0.02:
        frost(img, gt, CX, CY - 200, 380, n=26, a=cold)


def gh_hook(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    card(img)
    b = ease_out(prog(t, 1.2, 0.8))
    arm_scene(img, gt, b, cold=b)
    qmark(img, t, gt, 880, 560)
    cap(img, "Rate mal, was passiert, wenn du Gänsehaut bekommst!", t, hl=("RATE", "MAL,", "GÄNSEHAUT"))


SURF = 190
EXIT = (420, SURF)


@lru_cache(None)
def skin_base():
    lay = layer()
    lay.alpha_composite(fx.lin(PW, PH, [(0, (160, 200, 255, 70)), (0.3, (160, 200, 255, 0)), (1, (0, 0, 0, 0))]))
    # subcutis (fat)
    fat = fx.lin(PW, PH, [(0, (255, 226, 140)), (1, (240, 196, 100))])
    fm = Image.new("L", (PW, PH))
    ImageDraw.Draw(fm).rectangle((0, 480, PW, PH), fill=255)
    lay = Image.alpha_composite(lay, clip(fat, fm))
    cells = layer()
    d = ImageDraw.Draw(cells)
    r = random.Random(3)
    for row in range(5):
        for col in range(14):
            x = col * 70 + (35 if row % 2 else 0) + r.uniform(-6, 6)
            y = 500 + row * 44 + r.uniform(-4, 4)
            d.ellipse((x - 33, y - 22, x + 33, y + 22), fill=(255, 238, 170, 255), outline=(220, 170, 80, 255), width=3)
            d.ellipse((x - 18, y - 14, x - 2, y - 6), fill=(255, 255, 230, 160))
    lay = Image.alpha_composite(lay, clip(cells, fm))
    # dermis
    dm = Image.new("L", (PW, PH))
    ImageDraw.Draw(dm).rectangle((0, SURF + 50, PW, 482), fill=255)
    der = fx.lin(PW, PH, [(0, (255, 196, 180)), (1, (240, 160, 150))])
    fib = layer()
    d = ImageDraw.Draw(fib)
    for _ in range(60):
        y = r.uniform(SURF + 70, 470)
        x = r.uniform(-50, PW)
        pts = [(x + i * 22, y + 8 * math.sin(i * 0.9 + x)) for i in range(8)]
        d.line(pts, fill=(255, 235, 225, 120), width=4, joint="curve")
        d.line([(p[0], p[1] + 4) for p in pts], fill=(210, 120, 120, 70), width=2, joint="curve")
    der = Image.alpha_composite(der, fib)
    # capillary loops + vessel
    cap_ = layer()
    d = ImageDraw.Draw(cap_)
    d.line(spline([(0, 440), (300, 430), (600, 450), (920, 436)], 8, False), fill=(200, 40, 60, 255), width=12)
    d.line(spline([(0, 458), (300, 452), (600, 468), (920, 456)], 8, False), fill=(70, 90, 200, 255), width=10)
    for x in range(40, PW, 90):
        d.line(spline([(x, 440), (x + 10, 330), (x + 22, SURF + 60), (x + 34, 330), (x + 44, 452)], 6, False),
               fill=(220, 60, 80, 200), width=4)
    der = Image.alpha_composite(der, cap_)
    # nerve
    nv = layer()
    dn = ImageDraw.Draw(nv)
    dn.line(spline([(PW, 400), (760, 380), (640, 350), (560, 320)], 8, False), fill=(255, 220, 80, 255), width=8)
    der = Image.alpha_composite(der, nv)
    lay = Image.alpha_composite(lay, clip(der, dm))
    # epidermis
    em = Image.new("L", (PW, PH))
    ImageDraw.Draw(em).rectangle((0, SURF, PW, SURF + 52), fill=255)
    ep = fx.lin(PW, PH, [(0, (255, 226, 205)), (1, (246, 186, 160))])
    et = layer()
    d = ImageDraw.Draw(et)
    for row in range(4):
        y = SURF + 7 + row * 12
        x = (row % 2) * 12
        while x < PW:
            d.rounded_rectangle((x, y, x + 22, y + 10), 4, outline=(220, 150, 130, 140), width=1)
            x += 24
    ep = Image.alpha_composite(ep, et)
    lay = Image.alpha_composite(lay, clip(ep, em))
    d = ImageDraw.Draw(lay)
    d.line((0, SURF, PW, SURF), fill=(210, 130, 110, 255), width=4)
    d.line((0, SURF + 52, PW, SURF + 52), fill=(220, 140, 130, 160), width=2)
    return lay


def skin_scene(img, t, gt, contract=0.0, labels=1.0, signal=0.0):
    lay = skin_base().copy()
    d = ImageDraw.Draw(lay)
    a = math.radians(30 + 50 * contract)
    ex, ey = EXIT
    fl = 250
    fdir = (-math.cos(a), math.sin(a))
    bulb = (ex + fdir[0] * fl, ey + fdir[1] * fl)
    # sebaceous gland
    gx, gy = ex + fdir[0] * fl * 0.35, ey + fdir[1] * fl * 0.35
    for k in range(5):
        an = k * 1.2
        d.ellipse((gx + 18 + 16 * math.cos(an) - 15, gy + 6 + 16 * math.sin(an) - 15,
                   gx + 18 + 16 * math.cos(an) + 15, gy + 6 + 16 * math.sin(an) + 15),
                  fill=(255, 230, 150, 255), outline=(220, 170, 80, 255), width=2)
    # follicle sheath + hair root
    sp = [(ex, ey), (bulb[0], bulb[1])]
    stroke_line(d, sp, (220, 150, 130, 255), 38)
    stroke_line(d, sp, (245, 190, 170, 255), 28)
    stroke_line(d, sp, (80, 50, 35, 255), 10)
    d.ellipse((bulb[0] - 26, bulb[1] - 22, bulb[0] + 26, bulb[1] + 26), fill=(170, 100, 80, 255),
              outline=(120, 60, 50, 255), width=3)
    d.ellipse((bulb[0] - 10, bulb[1] - 2, bulb[0] + 10, bulb[1] + 18), fill=(240, 120, 120, 255))
    # arrector pili muscle
    mp = (ex + fdir[0] * fl * 0.6, ey + fdir[1] * fl * 0.6)
    anchor = (640 - 50 * contract, SURF + 56 + 10 * contract)
    mw = 20 + 16 * contract
    ux, uy = anchor[0] - mp[0], anchor[1] - mp[1]
    ln = math.hypot(ux, uy)
    nx, ny = -uy / ln, ux / ln
    musc = [(mp[0] + nx * 6, mp[1] + ny * 6), ((mp[0] + anchor[0]) / 2 + nx * mw / 2, (mp[1] + anchor[1]) / 2 + ny * mw / 2),
            (anchor[0] + nx * 4, anchor[1] + ny * 4), (anchor[0] - nx * 4, anchor[1] - ny * 4),
            ((mp[0] + anchor[0]) / 2 - nx * mw / 2, (mp[1] + anchor[1]) / 2 - ny * mw / 2),
            (mp[0] - nx * 6, mp[1] - ny * 6)]
    mm = fx.mask(PW, PH, lambda dd, k: dd.polygon(P(spline(musc, 6), k), fill=255))
    mus = fx.shaded(mm, fx.lin(PW, PH, [(0, (255, 110, 120)), (1, (190, 30, 60))]), depth=0.3, hi_a=0.5)
    ds = ImageDraw.Draw(mus)
    for i in range(1, 9):
        f = i / 9
        cx_, cy_ = mp[0] + ux * f, mp[1] + uy * f
        ds.line((cx_ - nx * mw * 0.45, cy_ - ny * mw * 0.45, cx_ + nx * mw * 0.45, cy_ + ny * mw * 0.45),
                fill=(150, 20, 50, 160), width=2)
    lay.alpha_composite(clip(mus, mm))
    # nerve signal to the muscle
    if signal > 0.02:
        npts = spline([(PW, 400), (760, 380), (640, 350), (560, 320), anchor], 8, False)
        q = (gt * 0.9) % 1
        x, y = npts[int(q * (len(npts) - 1))]
        glow_dot(d, x, y, 8, (255, 240, 140), a=signal)
    # surface bump around the exit
    bump = 34 * contract
    if bump > 0.5:
        pts = [(x, SURF - bump * math.exp(-((x - ex) / 80) ** 2)) for x in range(ex - 220, ex + 221, 6)]
        bm = fx.mask(PW, PH, lambda dd, k: dd.polygon(P(pts + [(ex + 220, SURF + 3), (ex - 220, SURF + 3)], k),
                                                       fill=255))
        lay.alpha_composite(fx.apply_mask(fx.lin(PW, PH, [(0, (255, 232, 212)), (1, (250, 200, 176))]), bm))
        d.line(pts, fill=(210, 130, 110, 255), width=4)
    # hair shaft
    hx, hy = ex, ey - bump
    hair = [(hx, hy)]
    for i in range(1, 12):
        f = i / 11
        hair.append((hx + math.cos(a) * 230 * f + 8 * f * f, hy - math.sin(a) * 230 * f + 6 * f * f))
    d.line(hair, fill=(60, 36, 26, 255), width=10, joint="curve")
    d.line([(x - 2, y - 2) for x, y in hair[:9]], fill=(140, 100, 80, 200), width=3, joint="curve")
    put_panel(img, lay)
    if labels > 0.02:
        label(img, "HAAR", PX0 + 690, PY0 + 70, PX0 + hair[7][0], PY0 + hair[7][1], col=YELLOW, a=labels)
        label(img, "MUSKEL", PX0 + 770, PY0 + 300, PX0 + (mp[0] + anchor[0]) / 2, PY0 + (mp[1] + anchor[1]) / 2,
              col=(255, 130, 140), a=labels)
        label(img, "HAUT", PX0 + 120, PY0 + 120, PX0 + 140, PY0 + SURF + 20, col=(255, 210, 190), a=labels, size=24)
        label(img, "FETT", PX0 + 120, PY0 + 600, PX0 + 200, PY0 + 540, col=(255, 230, 140), a=labels, size=24)


def gh_c1(img, t, gt, d):
    pill(img, "UNTER DER HAUT", 420, BLUE, ease_out(prog(t, 0.2, 0.3)))
    card(img)
    skin_scene(img, t, gt, labels=ease_out(prog(t, 0.8, 0.4)))
    cap(img, "An jedem Haar sitzt ein winziger Muskel.", t, hl=("MUSKEL.",))


def gh_c2(img, t, gt, d):
    pill(img, "KÄLTE · GEFÜHLE · MUSIK", 420, YELLOW, ease_out(prog(t, 0.2, 0.3)), size=36)
    card(img)
    c = ease_io(prog(t, W_("zusammen", fallback=1.0) - 0.3, 0.6))
    skin_scene(img, t, gt, contract=c, labels=1.0, signal=ease_out(prog(t, 0.4, 0.4)))
    for k, kind in enumerate(("cold", "heart", "note")):
        badge(img, kind, PX0 + 560 + k * 125, PY0 + 590, ease_out(prog(t, 0.4 + k * 0.25, 0.4)), r=48)
    cap(img, "Bei Kälte oder starken Gefühlen zieht er sich zusammen – das Haar stellt sich auf.", t,
        hl=("ZUSAMMEN", "AUF."))


def gh_c3(img, t, gt, d):
    card(img)
    arm_scene(img, gt, 1.0)
    # magnifier on one bump
    E.stamp(img, "GÄNSEHAUT!", t, W_("Gänsehaut", fallback=0.4) - 0.1, cx=540, cy=420, size=120, rot=-5, fill=YELLOW,
            sfill=(170, 20, 0))
    th = W_("Hügel", fallback=3.0) - 0.2
    p = back_out(prog(t, th, 0.5))
    if p > 0.03:
        x, y = PX0 + FOLL[3][0], PY0 + FOLL[3][1]
        lay = Image.new("RGBA", (W, H))
        dd = ImageDraw.Draw(lay)
        rr = 26 + 20 * p
        dd.ellipse((x - rr, y - rr, x + rr, y + rr), outline=(255, 226, 60, 255), width=6)
        img.alpha_composite(lay)
    cap(img, "Um jedes Haar wölbt sich die Haut – fertig sind die kleinen Hügel.", t, hl=("HÜGEL.",))


@lru_cache(None)
def cat_sprite(level):
    fluff = level / 5
    w, h = 720, 660
    cx, cy = 360, 380
    lay = layer(w, h)
    sc = 1 + 0.28 * fluff
    # tail (puffed)
    tail = spline([(cx + 150, cy + 200), (cx + 260, cy + 150), (cx + 290, cy + 20), (cx + 250, cy - 90)], 8, False)
    tw = int(44 + 70 * fluff)
    tm = fx.mask(w, h, lambda d, k: d.line(P(tail, k), fill=255, width=int(tw * k), joint="curve"))
    # body + head silhouette
    def body(d, k, ex=0):
        d.ellipse(BX((cx - 170 * sc - ex, cy - 20 * sc - ex, cx + 170 * sc + ex, cy + 250 * sc / 1.15 + ex), k),
                  fill=255)
        d.ellipse(BX((cx - 130 * sc - ex, cy - 230 - ex, cx + 130 * sc + ex, cy + 10 + ex), k), fill=255)
        for sgn in (-1, 1):
            d.polygon(P([(cx + sgn * 120 * sc, cy - 150), (cx + sgn * 105 * sc, cy - 300 - 10 * fluff),
                         (cx + sgn * 40 * sc, cy - 210)], k), fill=255)
    bm = ImageChops.lighter(fx.mask(w, h, body), tm)
    fur = fx.lin(w, h, [(0, (150, 150, 165)), (1, (80, 80, 96))])
    base = fx.shaded(bm, fur, depth=0.06, dark=(20, 20, 30), dark_a=0.55, hi_a=0.3)
    # fur strands along edge + body
    st = layer(w, h)
    d = ImageDraw.Draw(st)
    r = random.Random(level)
    edge = np.array(bm.filter(ImageFilter.FIND_EDGES))
    ys, xs = np.nonzero(edge > 80)
    idx = r.sample(range(len(xs)), min(len(xs), 900))
    for i in idx:
        x, y = xs[i], ys[i]
        vx, vy = x - cx, y - (cy + 40)
        n = math.hypot(vx, vy) + 1e-6
        ln = r.uniform(8, 18) + 30 * fluff * r.uniform(0.4, 1.0)
        an = math.atan2(vy, vx) + r.uniform(-0.3, 0.3)
        c = r.choice([(170, 170, 185), (120, 120, 135), (90, 90, 105), (200, 200, 210)])
        d.line((x - 6 * vx / n, y - 6 * vy / n, x + ln * math.cos(an), y + ln * math.sin(an)), fill=c + (230,), width=3)
    for _ in range(500):
        x, y = r.uniform(cx - 170, cx + 170), r.uniform(cy - 200, cy + 230)
        if bm.getpixel((int(x), int(y))) < 200:
            continue
        an = math.atan2(y - cy, x - cx) + r.uniform(-0.4, 0.4)
        ln = r.uniform(6, 12) * (1 + fluff)
        d.line((x, y, x + ln * math.cos(an), y + ln * math.sin(an)), fill=(r.choice([200, 110, 140]),) * 3 + (120,),
               width=2)
    out = Image.alpha_composite(base, st)
    # tabby stripes on forehead
    d = ImageDraw.Draw(out)
    for k in (-1, 0, 1):
        d.line((cx + k * 22, cy - 210, cx + k * 16, cy - 160), fill=(60, 60, 75, 200), width=8)
    # inner ears
    for sgn in (-1, 1):
        d.polygon([(cx + sgn * 108 * sc, cy - 160), (cx + sgn * 98 * sc, cy - 270 - 10 * fluff),
                   (cx + sgn * 56 * sc, cy - 200)], fill=(250, 170, 180, 255))
    # face
    face = ss_layer(w, h, lambda dd, k: [
        dd.ellipse(BX((cx + sgn * 52 - 30, cy - 130, cx + sgn * 52 + 30, cy - 80), k), fill=(170, 220, 90, 255))
        for sgn in (-1, 1)] + [
        dd.ellipse(BX((cx + sgn * 52 - 7 + (2 if fluff < 0.5 else 0) - (6 * fluff), cy - 128,
                       cx + sgn * 52 + 7 + 6 * fluff, cy - 82), k), fill=(15, 15, 20, 255)) for sgn in (-1, 1)] + [
        dd.ellipse(BX((cx + sgn * 52 - 14, cy - 122, cx + sgn * 52 - 4, cy - 112), k), fill=(255, 255, 255, 255))
        for sgn in (-1, 1)] + [
        dd.polygon(P([(cx - 14, cy - 64), (cx + 14, cy - 64), (cx, cy - 48)], k), fill=(240, 130, 150, 255)),
        dd.line(P([(cx, cy - 48), (cx, cy - 34), (cx - 18, cy - 24)], k), fill=(60, 40, 50, 255), width=int(3 * k)),
        dd.line(P([(cx, cy - 34), (cx + 18, cy - 24)], k), fill=(60, 40, 50, 255), width=int(3 * k))] + [
        dd.line(P([(cx + sgn * 30, cy - 46 + j * 10), (cx + sgn * (150 + 30 * fluff), cy - 70 + j * 22)], k),
                fill=(255, 255, 255, 220), width=int(2 * k)) for sgn in (-1, 1) for j in range(3)], 3)
    out = Image.alpha_composite(out, face)
    return fx.drop_shadow(out, dy=18, blur=20, alpha=0.45)


def gh_c4(img, t, gt, d):
    pill(img, "ERBE UNSERER VORFAHREN", 420, YELLOW, ease_out(prog(t, 0.2, 0.3)), size=36)
    card(img)
    f = ease_out(prog(t, W_("aufgeplusterte", fallback=0.6) - 0.2, 0.6))
    lay = layer()
    lay.alpha_composite(fx.rad(PW, PH, PW / 2, PH * 0.55, PW * 0.55, [(0, (255, 200, 140, 70)), (1, (255, 200, 140, 0))]))
    put_panel(img, lay)
    lv = int(round(f * 5))
    place(img, cat_sprite(lv), CX - 60, CY + 30 + 4 * math.sin(gt * 2), scale=0.92)
    # ghost outline of normal size
    if f > 0.2:
        lay2 = Image.new("RGBA", (W, H))
        dd = ImageDraw.Draw(lay2)
        for k in range(0, 360, 12):
            a0 = math.radians(k)
            a1 = math.radians(k + 6)
            dd.line((CX - 60 + 170 * math.cos(a0), CY + 120 + 150 * math.sin(a0), CX - 60 + 170 * math.cos(a1),
                     CY + 120 + 150 * math.sin(a1)), fill=(255, 255, 255, int(160 * f)), width=4)
        img.alpha_composite(lay2)
    tw_ = W_("warm", fallback=2.5) - 0.1
    badge(img, "warm", 850, 640, ease_out(prog(t, tw_, 0.4)), r=56)
    text(img, "WARM", 34, 850, 730, fill=WHITE, stroke=5, sfill=NAVY, alpha=ease_out(prog(t, tw_, 0.4)), path=FONT_XB)
    tg = W_("größer", fallback=4.0) - 0.1
    pg = ease_out(prog(t, tg, 0.4))
    text(img, "↔", 90, 850, 900, fill=YELLOW, stroke=7, sfill=NAVY, alpha=pg, scale=0.8 + 0.2 * back_out(pg))
    text(img, "GRÖSSER", 34, 850, 980, fill=WHITE, stroke=5, sfill=NAVY, alpha=pg, path=FONT_XB)
    cap(img, "Ein Erbe unserer Vorfahren: Aufgeplustertes Fell hält warm – und lässt Tiere größer wirken.", t,
        hl=("WARM", "GRÖSSER"))


# ------------------------------------------------------------------ outro
@lru_cache(None)
def bubble_sprite():
    w, h = 820, 420
    m = fx.mask(w, h, lambda d, k: (d.rounded_rectangle(BX((10, 10, w - 10, h - 90), k), int(60 * k), fill=255),
                                    d.polygon(P([(250, h - 100), (180, h - 10), (360, h - 100)], k), fill=255)))
    b = fx.shaded(m, fx.lin(w, h, [(0, (255, 255, 255)), (1, (225, 230, 245))]), depth=0.04, hi_a=0.5,
                  dark=(80, 80, 140), dark_a=0.3)
    return fx.drop_shadow(b, dy=20, blur=24, alpha=0.45)


@lru_cache(None)
def button_sprite(s, c0, c1):
    w, h = 300, 110
    m = fx.mask(w, h, lambda d, k: d.rounded_rectangle(BX((4, 4, w - 4, h - 4), k), int(50 * k), fill=255))
    b = fx.shaded(m, fx.lin(w, h, [(0, c0), (1, c1)]), depth=0.2, hi_a=0.5)
    return fx.drop_shadow(b, dy=10, blur=12, alpha=0.45)


def outro(img, t, gt, d):
    E.brand(img, t, gt, y=300)
    p = back_out(prog(t, 0.1, 0.5))
    if p > 0.05:
        place(img, bubble_sprite(), 540, 700, scale=p)
        text(img, "Hättest du's gewusst?", 58 * p, 540, 620, fill=(40, 34, 80), path=FONT_XB)
        for k, (s, c0, c1) in enumerate((("JA", (120, 240, 150), (30, 160, 80)), ("NEIN", (255, 130, 130), (200, 40, 60)))):
            q = back_out(prog(t, 0.4 + k * 0.15, 0.4))
            if q > 0.05:
                x = 390 + k * 300
                place(img, button_sprite(s, c0, c1), x, 730, scale=q * p)
                text(img, s, 52 * q * p, x, 730, fill=WHITE, stroke=4, sfill=(20, 40, 30), path=FONT_XB)
    tr = W_("Kommentare", fallback=1.0) + 0.5
    if t > tr:
        E.stamp(img, "RATE MAL!", t, tr, cx=540, cy=1030, size=150, rot=-6, fill=YELLOW, sfill=(170, 20, 0))
        E.confetti(img, t, tr)
    sparkles(img, gt, 9, (60, 450, 1020, 1150), n=16, col=(255, 240, 180))
    cap(img, "Schreib's in die Kommentare!", t, hl=("KOMMENTARE!",))


# ------------------------------------------------------------------ assembly (same timing as textshorts)
SHORTS = {
    "hirnfrost": dict(bg=((8, 30, 80), (40, 100, 180), (40, 60, 110)), out="hirnfrost_eis_hq",
                      scenes=[hf_hook, hf_c1, hf_c2, hf_c3, hf_c4, hf_tip, outro]),
    "ohren": dict(bg=((14, 20, 70), (80, 50, 140), (60, 50, 120)), out="ohren_flugzeug_hq",
                  scenes=[oh_hook, oh_c1, oh_c2, oh_c3, oh_c4, oh_tip, outro]),
    "gaensehaut": dict(bg=((40, 10, 56), (130, 40, 90), (90, 40, 90)), out="gaensehaut_hq",
                       scenes=[gh_hook, gh_c1, gh_c2, gh_c3, gh_c4, outro]),
}
CUR = {}


def init(name):
    spec = SHORTS[name]
    CUR.clear()
    CUR.update(spec, name=name)
    CUR["BG"] = fx.background(W, H, *spec["bg"], seed=len(name))
    t, segs = 0.0, []
    caps = {fn.__name__: c for fn, _, c in M.SHORTS[name]["scenes"]}
    caps["outro"] = ""
    for i, fn in enumerate(spec["scenes"]):
        key = "outro" if fn is outro else f"{name}_{i}"
        ws = json.load(open(os.path.join(TS, "audio", key + ".words.json")))["words"]
        pre = 0.25
        seg = dict(fn=fn, start=t, cap=caps.get(fn.__name__, ""), mp3=os.path.join(TS, "audio", key + ".mp3"), pre=pre,
                   words=[(w["text"], w["start"] + pre, w["end"] + pre) for w in ws])
        seg["dur"] = pre + ws[-1]["end"] + (1.8 if fn is outro else 0.55)
        segs.append(seg)
        t += seg["dur"]
    CUR["segs"], CUR["total"] = segs, t


def seg_at(gt):
    for s in CUR["segs"]:
        if gt < s["start"] + s["dur"]:
            return s
    return CUR["segs"][-1]


def drift(img, gt):
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    r = random.Random(21)
    for _ in range(26):
        x0, y0, sp, s = r.uniform(0, W), r.uniform(0, H), r.uniform(10, 30), r.uniform(2, 5)
        y = (y0 - gt * sp) % H
        x = x0 + 14 * math.sin(gt * 0.6 + y0)
        d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 255, 255, 70))
    img.alpha_composite(lay)


@lru_cache(None)
def rays_sprite():
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    ox, oy = W * 0.5, -700
    for k, (a, w) in enumerate(((-0.55, 0.07), (-0.3, 0.05), (-0.08, 0.09), (0.18, 0.06), (0.42, 0.08))):
        a0, a1 = math.pi / 2 + a - w, math.pi / 2 + a + w
        L = 2600
        d.polygon([(ox, oy), (ox + L * math.cos(a0), oy + L * math.sin(a0)), (ox + L * math.cos(a1), oy + L * math.sin(a1))],
                  fill=(255, 245, 220, 20 if k % 2 else 26))
    lay = lay.filter(ImageFilter.GaussianBlur(70))
    fade = fx.lin(W, H, [(0, (255, 255, 255, 255)), (0.75, (255, 255, 255, 60)), (1, (255, 255, 255, 0))])
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), fade.getchannel("A")))
    return lay


@lru_cache(None)
def bokeh_sprite(r, col):
    s = int(r * 2 + 60)
    lay = Image.new("RGBA", (s, s))
    d = ImageDraw.Draw(lay)
    d.ellipse((30, 30, s - 30, s - 30), fill=col + (60,), outline=col + (90,), width=3)
    return lay.filter(ImageFilter.GaussianBlur(7))


def fg_bokeh(img, gt):
    r = random.Random(77)
    for _ in range(7):
        rad = r.uniform(30, 70)
        col = r.choice([(255, 230, 170), (170, 210, 255), (255, 180, 230)])
        x0, y0, sp = r.uniform(0, W), r.uniform(0, H), r.uniform(8, 22)
        y = (y0 - gt * sp) % (H + 300) - 150
        x = x0 + 30 * math.sin(gt * 0.4 + x0)
        place(img, bokeh_sprite(int(rad), col), x, y, alpha=0.5 + 0.3 * math.sin(gt + x0))


def draw_seg(s, t, gt):
    img = CUR["BG"].copy()
    place(img, rays_sprite(), W / 2, H / 2, alpha=0.75 + 0.25 * math.sin(gt * 0.7))
    drift(img, gt)
    M.SEG.clear()
    M.SEG.update(s)
    CAPQ.clear()
    s["fn"](img, t, gt, None)
    fg_bokeh(img, gt)
    # slow camera push-in (captions excluded)
    z = 1.0 + 0.035 * ease_io(min(1.0, t / max(1.0, s["dur"])))
    if z > 1.001:
        zw, zh = int(W * z), int(H * z)
        big = img.resize((zw, zh), Image.BILINEAR)
        cy0 = int((zh - H) * 0.42)
        img = big.crop(((zw - W) // 2, cy0, (zw - W) // 2 + W, cy0 + H))
    for c in CAPQ:
        draw_caption(img, *c)
    return img


# grade: gentle S-curve, cool shadows, warm highlights (no grain)
_x = np.arange(256) / 255.0
_s = _x + 0.10 * np.sin(2 * math.pi * _x) * -0.5 * 1.0
_s = np.clip(_x + 0.06 * np.sin(2 * math.pi * (_x - 0.5)) * -1, 0, 1)
LUT = np.stack([np.clip(_s * 255 + 6 * _x ** 2, 0, 255), np.clip(_s * 255, 0, 255),
                np.clip(_s * 255 + 8 * (1 - _x) ** 2 - 4 * _x ** 2, 0, 255)]).astype(np.uint8)
_GR = None


def grain(i):
    global _GR
    if _GR is None:
        rng = np.random.default_rng(5)
        _GR = [rng.normal(0, 3.2, (H, W, 1)).astype(np.float32) for _ in range(6)]
    return _GR[i % 6]


def post(img, fi):
    rgb = img.convert("RGB")
    small = rgb.resize((W // 4, H // 4), Image.BILINEAR)
    a = np.asarray(small, np.float32)
    lum = a.mean(axis=2, keepdims=True)
    br = np.clip((lum - 195) / 60, 0, 1) * a
    bl = Image.fromarray(br.astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
    out = np.asarray(rgb, np.float32) + np.asarray(bl, np.float32) * 0.28   # no film grain: clean image
    out = np.clip(out, 0, 255).astype(np.uint8)
    out = np.stack([LUT[c][out[..., c]] for c in range(3)], axis=2)
    return Image.fromarray(out)


def render_frame(fi):
    gt = fi / FPS
    s = seg_at(gt)
    t = gt - s["start"]
    img = draw_seg(s, t, gt)
    TR = 0.35
    if t < TR and s is not CUR["segs"][0]:
        k = ease_io(t / TR)
        prev = CUR["segs"][CUR["segs"].index(s) - 1]
        pimg = draw_seg(prev, prev["dur"] - 0.01, gt)
        z = 1 + 0.08 * k
        pb = pimg.resize((int(W * z), int(H * z)), Image.BILINEAR)
        pimg = pb.crop(((pb.width - W) // 2, (pb.height - H) // 2, (pb.width - W) // 2 + W, (pb.height - H) // 2 + H))
        z2 = 0.94 + 0.06 * k
        nb = img.resize((int(W * z2), int(H * z2)), Image.BILINEAR)
        base = CUR["BG"].copy()
        base.alpha_composite(nb, ((W - nb.width) // 2, (H - nb.height) // 2))
        img = Image.blend(pimg, base, k)
    return post(img, fi)


def render_bytes(fi):
    return render_frame(fi).tobytes()


def seg_word(sg, word, fallback):
    for tx, st, en in sg.get("words", []):
        if tx.strip(".,!?:;").lower() == word.lower():
            return st
    return fallback


def events():
    ev = []
    keys = {"hf_c3": ("Stirn", "thump"), "oh_c4": ("Plopp", "thump"), "gh_c3": ("Gänsehaut", "thump"),
            "hf_c4": ("nicht", "ding"), "oh_tip": ("Kaugummi", "ding"), "hf_c2": ("weiten", "pop"),
            "oh_c3": ("wölbt", "pop"), "gh_c2": ("zusammen", "pop"), "gh_c4": ("aufgeplusterte", "pop"),
            "hf_tip": ("Warmes", "pop")}
    for i, s in enumerate(CUR["segs"]):
        st = s["start"]
        nm = s["fn"].__name__
        if i > 0:
            ev += [(st - 0.1, "whoosh", 0.10)]
        ev += [(st + 0.3, "pop", 0.08)]
        if nm in keys:
            w, kind = keys[nm]
            ev.append((st + seg_word(s, w, 1.0) - 0.05, kind, 0.14 if kind == "thump" else 0.10))
        if nm == "oh_tip":
            for w in ("Schlucken", "gähnen", "Babys"):
                ev.append((st + seg_word(s, w, 1.0) - 0.05, "pop", 0.07))
        if nm == "outro":
            tr = seg_word(s, "Kommentare", 1.0) + 0.5
            ev += [(st + tr, "chime", 0.12), (st + tr, "thump", 0.12)]
    return ev


def make(name, uhd=True):
    init(name)
    LL.TOTAL = CUR["total"]
    mix = LL.synth(events())
    voice = np.zeros(len(mix))
    for sg in CUR["segs"]:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sg["mp3"], "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                             capture_output=True, check=True).stdout
        v = np.frombuffer(raw, dtype=np.int16) / 32768.0
        a0 = int((sg["start"] + sg["pre"]) * SR)
        b0 = min(len(voice), a0 + len(v))
        voice[a0:b0] += v[:b0 - a0] / (np.abs(v).max() + 1e-9) * 0.89
    mix = np.clip(voice + mix * 1.2, -0.98, 0.98)
    bd = os.path.join(HERE, "build")
    os.makedirs(bd, exist_ok=True)
    wav = os.path.join(bd, f"{name}.wav")
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((mix[:int(CUR["total"] * SR)] * 32767).astype(np.int16).tobytes())
    tmp = os.path.join(bd, f"{name}_tmp.mp4")
    nfr = int(math.ceil(CUR["total"] * FPS))
    vf = ["-vf", "scale=2160:3840:flags=lanczos"] if uhd else []
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                           f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav] + vf +
                          ["-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac",
                           "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", "-shortest", tmp],
                          stdin=subprocess.PIPE)
    with Pool(4, initializer=init, initargs=(name,)) as pool:
        for k0 in range(0, nfr, 48):
            for b in pool.map(render_bytes, range(k0, min(nfr, k0 + 48)), chunksize=4):
                ff.stdin.write(b)
    ff.stdin.close()
    ff.wait()
    r = subprocess.run(["ffmpeg", "-nostats", "-i", tmp, "-af", "ebur128", "-f", "null", "-"], capture_output=True,
                       text=True).stderr
    lufs = float([ln for ln in r.splitlines() if ln.strip().startswith("I:")][-1].split()[1])
    out = os.path.join(HERE, CUR["out"] + ("_4k" if uhd else "") + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:v", "copy", "-af",
                    f"volume={-14 - lufs:.2f}dB,alimiter=limit=0.84:level=false", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", out], check=True)
    os.remove(tmp)
    print("wrote", out, round(CUR["total"], 1), "s")


def stills(name, fracs=(0.85,)):
    init(name)
    qc = os.path.join(HERE, "qc")
    os.makedirs(qc, exist_ok=True)
    for i, s in enumerate(CUR["segs"]):
        for f in fracs:
            gt = s["start"] + s["dur"] * f
            render_frame(int(gt * FPS)).save(os.path.join(qc, f"{name}_{i}_{int(f * 100):02d}.png"))


if __name__ == "__main__":
    names = [a for a in ARGS if not a.startswith("--")] or list(SHORTS)
    for nm in names:
        if "--stills" in ARGS:
            stills(nm)
        else:
            make(nm, uhd="--hd" not in ARGS)

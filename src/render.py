#!/usr/bin/env python3
"""Procedural silhouette-style horror Short: "The Girl on Route Nine".

All visuals are drawn here with Pillow + NumPy and encoded with ffmpeg.
Only the narration audio comes from ElevenLabs (src/narration_raw.mp3).

Usage: python3 src/render.py [--preview SECONDS]
"""
import math
import os
import random
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
W, H = 1080, 1920
FPS = 30
OVER = 1.2                      # background oversize for camera moves
BW, BH = int(W * OVER), int(H * OVER)
LEAD = 0.3                      # silence before narration starts (s)
TEMPO = 1.06                    # narration speed-up
TAIL = 1.3
VOICE_LEN = 44.56
DUR = LEAD + VOICE_LEN / TEMPO + TAIL
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_TITLE = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

# Phrase timings in the raw narration (seconds), measured with silencedetect.
PHRASES = [
    (0.00, 1.75, "Late one rainy night,"),
    (2.32, 4.67, "my father was driving home on Route Nine."),
    (5.69, 6.49, "Through the fog..."),
    (7.13, 10.34, "he saw a girl in a white dress, standing by the road."),
    (10.99, 11.56, "Soaked."),
    (12.36, 13.03, "Silent."),
    (13.58, 14.89, "He offered her a ride."),
    (15.54, 18.22, "She sat in the back seat, whispered an address..."),
    (18.61, 19.52, "...and said nothing more."),
    (20.28, 22.75, "When he pulled up to the old house, he turned around."),
    (23.54, 24.75, "The back seat was empty."),
    (25.38, 27.05, "Just a puddle of cold rainwater."),
    (27.80, 29.20, "An old woman opened the door."),
    (29.70, 30.78, "She looked at him and said:"),
    (31.34, 32.19, "\"That was my daughter.\""),
    (32.77, 33.95, "\"She died on Route Nine...\""),
    (34.55, 35.86, "\"...forty years ago tonight.\""),
    (36.48, 38.44, "\"You're the seventh driver to bring her home.\""),
    (39.28, 40.91, "He never drove that road again."),
    (41.61, 42.82, "Because on rainy nights..."),
    (43.32, 44.18, "she's still waiting."),
]


def v(ta):
    """Raw narration time -> video time."""
    return LEAD + ta / TEMPO


SCENES = [  # (name, start video time)
    ("road", 0.0),
    ("girl", v(5.55)),
    ("car", v(13.45)),
    ("house", v(20.1)),
    ("seat", v(23.4)),
    ("door", v(27.65)),
    ("end", v(39.1)),
]
LIGHTNING = [v(11.0), v(20.15), v(23.5), v(34.5), v(43.3)]

# ----------------------------------------------------------------- helpers


def smooth_noise(w, h, scale, seed, blur=0):
    rng = np.random.default_rng(seed)
    small = rng.random((max(2, h // scale), max(2, w // scale))) * 255
    img = Image.fromarray(small.astype(np.uint8), "L").resize((w, h), Image.BICUBIC)
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    return img


def vgrad(w, h, top, bottom, y0=0.0, y1=1.0):
    t = np.clip((np.linspace(0, 1, h) - y0) / max(1e-6, y1 - y0), 0, 1)[:, None, None]
    a = np.array(top, np.float32)[None, None]
    b = np.array(bottom, np.float32)[None, None]
    col = a * (1 - t) + b * t
    return np.repeat(col, w, axis=1)


def add_glow(arr, cx, cy, radius, color, strength):
    h, w, _ = arr.shape
    yy, xx = np.ogrid[:h, :w]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / radius
    g = np.exp(-d * d * 2.2) * strength
    arr += g[..., None] * np.array(color, np.float32)[None, None]
    return arr


def to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


INK = (6, 7, 10)


def pine(draw, x, base, h, rng, col=INK):
    w = h * 0.38
    tiers = 7
    draw.polygon([(x - h * 0.02, base), (x + h * 0.02, base), (x, base - h)], fill=col)
    for i in range(tiers):
        ty = base - h * 0.12 - i * h * 0.12
        tw = w * (1 - i / tiers) * rng.uniform(0.85, 1.1)
        draw.polygon([(x - tw, ty), (x + tw, ty), (x + rng.uniform(-3, 3), ty - h * 0.26)], fill=col)


def dead_tree(draw, x, y, length, angle, width, rng, depth=0, col=INK):
    if depth > 7 or length < 6:
        return
    x2 = x + math.cos(angle) * length
    y2 = y - math.sin(angle) * length
    draw.line([(x, y), (x2, y2)], fill=col, width=max(1, int(width)))
    n = 2 if depth < 2 else rng.choice([1, 2, 2, 3])
    for _ in range(n):
        dead_tree(draw, x2, y2, length * rng.uniform(0.6, 0.78),
                  angle + rng.uniform(-0.75, 0.75), width * 0.66, rng, depth + 1, col)


def figure_layers(height, kind="girl"):
    """Return (rgba_figure, glow_L) for a standing figure of given pixel height."""
    s = height
    pad = int(s * 0.5)
    w = int(s * 0.7) + pad * 2
    h = int(s * 1.05) + pad * 2
    fig = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(fig)
    cx = w / 2
    top = pad
    if kind == "girl":
        dress = (196, 204, 216, 255)
        dark = (12, 12, 16, 255)
        head_r = s * 0.065
        hy = top + head_r
        # hair behind (long, wet)
        d.polygon([(cx - head_r * 1.1, hy), (cx + head_r * 1.1, hy),
                   (cx + head_r * 1.3, hy + s * 0.27), (cx - head_r * 1.35, hy + s * 0.28)], fill=dark)
        # dress
        sh_y = top + s * 0.16
        d.polygon([(cx - s * 0.09, sh_y), (cx + s * 0.09, sh_y),
                   (cx + s * 0.13, top + s * 0.45), (cx + s * 0.2, top + s * 0.78),
                   (cx + s * 0.05, top + s * 0.8), (cx - s * 0.04, top + s * 0.77),
                   (cx - s * 0.21, top + s * 0.79), (cx - s * 0.13, top + s * 0.45)], fill=dress)
        # arms hanging
        d.line([(cx - s * 0.09, sh_y + 5), (cx - s * 0.15, top + s * 0.52)], fill=dress, width=max(2, int(s * 0.035)))
        d.line([(cx + s * 0.09, sh_y + 5), (cx + s * 0.15, top + s * 0.52)], fill=dress, width=max(2, int(s * 0.035)))
        # legs
        d.line([(cx - s * 0.04, top + s * 0.78), (cx - s * 0.045, top + s)], fill=dress, width=max(2, int(s * 0.03)))
        d.line([(cx + s * 0.04, top + s * 0.78), (cx + s * 0.045, top + s)], fill=dress, width=max(2, int(s * 0.03)))
        # head (face hidden by hair) + hair strands over front
        d.ellipse([cx - head_r, hy - head_r, cx + head_r, hy + head_r], fill=dark)
        d.polygon([(cx - head_r * 0.9, hy), (cx + head_r * 0.9, hy),
                   (cx + head_r * 0.6, hy + s * 0.2), (cx - head_r * 0.7, hy + s * 0.21)], fill=dark)
    else:  # old woman: hunched black silhouette with shawl and bun
        dark = (4, 4, 6, 255)
        head_r = s * 0.06
        hx, hy = cx + s * 0.05, top + s * 0.13
        d.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=dark)
        d.ellipse([hx - head_r * 0.2, hy - head_r * 1.7, hx + head_r * 0.9, hy - head_r * 0.8], fill=dark)
        d.polygon([(hx - s * 0.02, hy + head_r * 0.6), (cx - s * 0.17, top + s * 0.3),
                   (cx - s * 0.2, top + s * 1.0), (cx + s * 0.18, top + s * 1.0),
                   (cx + s * 0.15, top + s * 0.32), (hx + s * 0.05, hy + head_r * 0.4)], fill=dark)
        # cane
        d.line([(cx + s * 0.16, top + s * 0.5), (cx + s * 0.25, top + s)], fill=dark, width=max(2, int(s * 0.02)))
        # shawl fringe
        for i in range(12):
            fx = cx - s * 0.2 + i * s * 0.034
            d.line([(fx, top + s * 0.55), (fx - 3, top + s * 0.6)], fill=dark, width=3)
    alpha = fig.split()[3]
    glow = alpha.filter(ImageFilter.GaussianBlur(s * 0.08))
    return fig, glow, (cx, top + s)  # anchor = feet


def paste_figure(img, layers, fx, fy, alpha=1.0, glow_col=(150, 175, 210), glow_amt=0.8):
    fig, glow, (ax, ay) = layers
    x0, y0 = int(fx - ax), int(fy - ay)
    if glow_amt > 0 and alpha > 0:
        g = glow.point(lambda p: int(p * glow_amt * alpha))
        light = Image.new("RGB", glow.size, glow_col)
        base = img.crop((x0, y0, x0 + glow.size[0], y0 + glow.size[1]))
        lit = Image.fromarray(np.clip(np.asarray(base, np.float32) +
                                      np.asarray(light, np.float32) * (np.asarray(g, np.float32)[..., None] / 255.0) * 0.6,
                                      0, 255).astype(np.uint8))
        img.paste(lit, (x0, y0))
    if alpha >= 0.999:
        img.paste(fig, (x0, y0), fig)
    elif alpha > 0:
        a = fig.split()[3].point(lambda p: int(p * alpha))
        img.paste(fig.convert("RGB"), (x0, y0), a)


# ----------------------------------------------------------------- scene builds

HORIZON = int(BH * 0.47)
VPX = BW // 2


def build_road(seed=1):
    rng = random.Random(seed)
    arr = vgrad(BW, BH, (6, 9, 16), (46, 58, 72), 0.0, 0.47)
    low = vgrad(BW, BH, (22, 26, 32), (8, 9, 12), 0.47, 1.0)
    arr[HORIZON:] = low[HORIZON:]
    add_glow(arr, BW * 0.78, BH * 0.14, BW * 0.22, (60, 70, 90), 0.9)   # moon behind clouds
    add_glow(arr, BW * 0.78, BH * 0.14, BW * 0.05, (120, 130, 150), 0.9)
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    # road
    d.polygon([(VPX - 14, HORIZON), (VPX + 14, HORIZON), (BW * 1.05, BH), (-BW * 0.05, BH)], fill=(14, 16, 20))
    # shoulders / grass
    d.polygon([(0, HORIZON), (VPX - 14, HORIZON), (-BW * 0.05, BH), (0, BH)], fill=(9, 10, 12))
    d.polygon([(BW, HORIZON), (VPX + 14, HORIZON), (BW * 1.05, BH), (BW, BH)], fill=(9, 10, 12))
    # tree lines receding
    for side in (-1, 1):
        for i in range(26):
            k = (i / 25) ** 1.8
            depth = 1 - k
            th = 90 + k * 1300
            x = VPX + side * (60 + k * BW * 0.75) + rng.uniform(-30, 30)
            base = HORIZON + k * (BH - HORIZON) * 0.55 + 10
            shade = int(26 * depth)
            pine(d, x, base, th, rng, col=(INK[0] + shade, INK[1] + shade + 2, INK[2] + shade + 6))
    # telephone poles
    for i, k in enumerate([0.1, 0.3, 0.62]):
        x = VPX + 90 + k * BW * 0.5
        top = HORIZON - 40 - k * 900
        base = HORIZON + k * 500
        d.line([(x, top), (x, base)], fill=INK, width=int(3 + k * 14))
        d.line([(x - 20 - k * 80, top + 20), (x + 20 + k * 80, top + 20)], fill=INK, width=int(2 + k * 8))
    # road sign "9"
    sx, sy = BW * 0.83, HORIZON + 260
    d.line([(sx, sy), (sx, sy + 260)], fill=INK, width=10)
    d.rectangle([sx - 70, sy - 120, sx + 70, sy], fill=(20, 24, 28), outline=(70, 78, 84), width=5)
    f = ImageFont.truetype(FONT_BOLD, 96)
    d.text((sx, sy - 60), "9", font=f, fill=(150, 156, 160), anchor="mm")
    return img


def draw_road_dashes(img, phase, headlights=True):
    d = ImageDraw.Draw(img)
    for i in range(14):
        z = ((i + phase) % 14) / 14.0
        k0 = z ** 2.2
        k1 = min(1, (z + 0.035)) ** 2.2
        y0 = HORIZON + k0 * (BH - HORIZON)
        y1 = HORIZON + k1 * (BH - HORIZON)
        w0, w1 = 1 + k0 * 22, 1 + k1 * 22
        d.polygon([(VPX - w0, y0), (VPX + w0, y0), (VPX + w1, y1), (VPX - w1, y1)], fill=(110, 104, 70))


def headlight_cone(arr, strength=1.0):
    h, w, _ = arr.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ny = (yy - HORIZON) / (h - HORIZON)
    ny = np.clip(ny, 0, 1)
    spread = 0.08 + ny * 0.55
    nx = np.abs(xx - w / 2) / (w * spread + 1)
    cone = np.exp(-nx * nx * 3) * (ny > 0) * np.clip(1.2 - ny * 0.4, 0, 1) * np.clip(ny * 6, 0, 1)
    return cone * strength


def build_house(seed=4):
    rng = random.Random(seed)
    arr = vgrad(BW, BH, (8, 10, 18), (52, 58, 70), 0.0, 0.62)
    add_glow(arr, BW * 0.25, BH * 0.18, BW * 0.18, (90, 96, 110), 0.8)
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    d.ellipse([BW * 0.25 - 70, BH * 0.18 - 70, BW * 0.25 + 70, BH * 0.18 + 70], fill=(170, 172, 178))
    # hill
    pts = [(0, BH)]
    for i in range(41):
        x = BW * i / 40
        y = BH * 0.66 - math.sin(i / 40 * math.pi) * 230 + rng.uniform(-8, 8)
        pts.append((x, y))
    pts.append((BW, BH))
    d.polygon(pts, fill=INK)
    # victorian house
    hx, hy = BW * 0.52, BH * 0.56
    d.rectangle([hx - 260, hy - 360, hx + 220, hy + 40], fill=INK)
    d.polygon([(hx - 300, hy - 350), (hx - 20, hy - 640), (hx + 260, hy - 350)], fill=INK)
    d.rectangle([hx + 40, hy - 760, hx + 150, hy - 420], fill=INK)                 # tower
    d.polygon([(hx + 20, hy - 750), (hx + 95, hy - 940), (hx + 170, hy - 750)], fill=INK)
    d.line([(hx + 95, hy - 940), (hx + 95, hy - 1010)], fill=INK, width=6)
    d.rectangle([hx - 200, hy - 700, hx - 150, hy - 520], fill=INK)                # chimney
    # dead tree + fence
    dead_tree(d, BW * 0.12, BH * 0.70, 260, math.pi / 2 + 0.08, 34, rng)
    for i in range(22):
        fx = BW * 0.02 + i * 58
        fy = BH * 0.84 + math.sin(i * 0.6) * 10
        d.polygon([(fx, fy), (fx + 18, fy), (fx + 18, fy - 120), (fx + 9, fy - 145), (fx, fy - 120)], fill=INK)
    d.line([(0, BH * 0.84 - 90), (BW, BH * 0.84 - 80)], fill=INK, width=10)
    return img, (hx, hy)


def house_windows(img, hx, hy, flick):
    d = ImageDraw.Draw(img)
    for (x0, y0, x1, y1, lit) in [(-200, -300, -120, -170, False), (-60, -300, 20, -170, True),
                                  (90, -300, 170, -170, False), (65, -700, 125, -600, True),
                                  (-200, -120, -120, 0, False)]:
        if lit:
            c = (int(220 * flick), int(160 * flick), int(80 * flick))
        else:
            c = (18, 20, 24)
        d.rectangle([hx + x0, hy + y0, hx + x1, hy + y1], fill=c)
        d.line([(hx + (x0 + x1) / 2, hy + y0), (hx + (x0 + x1) / 2, hy + y1)], fill=INK, width=6)
        d.line([(hx + x0, hy + (y0 + y1) / 2), (hx + x1, hy + (y0 + y1) / 2)], fill=INK, width=6)


def build_car():
    """Driver's view through the windshield; static parts."""
    road = build_road(seed=9)
    arr = np.asarray(road, np.float32) * 0.75
    arr += headlight_cone(arr, 1.0)[..., None] * np.array([60, 55, 40], np.float32)
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    # dashboard and frame
    d.polygon([(0, BH * 0.70), (BW * 0.3, BH * 0.66), (BW * 0.7, BH * 0.66), (BW, BH * 0.70), (BW, BH), (0, BH)], fill=INK)
    d.polygon([(0, 0), (BW * 0.12, 0), (BW * 0.0, BH * 0.70), (0, BH * 0.70)], fill=INK)          # A-pillar left
    d.polygon([(BW, 0), (BW * 0.88, 0), (BW, BH * 0.70)], fill=INK)
    d.rectangle([0, 0, BW, BH * 0.06], fill=INK)                                                    # roof
    # steering wheel
    cx, cy = BW * 0.3, BH * 0.86
    d.ellipse([cx - 330, cy - 330, cx + 330, cy + 330], outline=(14, 15, 18), width=46)
    d.line([(cx - 300, cy), (cx + 300, cy)], fill=(14, 15, 18), width=40)
    d.line([(cx, cy), (cx, cy + 320)], fill=(14, 15, 18), width=40)
    # dash glow (gauges)
    for gx in (BW * 0.22, BW * 0.38):
        d.ellipse([gx - 50, BH * 0.74 - 50, gx + 50, BH * 0.74 + 50], outline=(30, 70, 80), width=4)
    # mirror mount + mirror frame
    d.line([(BW / 2, BH * 0.06), (BW / 2, BH * 0.12)], fill=INK, width=16)
    mx0, my0, mx1, my1 = BW / 2 - 230, BH * 0.115, BW / 2 + 230, BH * 0.215
    d.rounded_rectangle([mx0 - 14, my0 - 14, mx1 + 14, my1 + 14], radius=40, fill=INK)
    return img, (mx0, my0, mx1, my1)


def mirror_content(w, h, girl_alpha, eyes):
    m = Image.fromarray(vgrad(w, h, (18, 22, 30), (8, 10, 14)).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(m)
    d.rectangle([0, int(h * 0.75), w, h], fill=(6, 6, 9))      # back seat top
    if girl_alpha > 0:
        lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        cx = w * 0.62
        ld.ellipse([cx - 52, h * 0.18, cx + 52, h * 0.18 + 120], fill=(170, 178, 190, 255))      # pale face
        ld.polygon([(cx - 70, h * 0.15), (cx + 70, h * 0.15), (cx + 85, h * 1.0), (cx + 40, h),
                    (cx + 30, h * 0.35), (cx - 30, h * 0.35), (cx - 40, h), (cx - 85, h)], fill=(8, 8, 10, 255))  # hair
        ld.polygon([(cx - 140, h), (cx - 60, h * 0.72), (cx + 60, h * 0.72), (cx + 140, h)], fill=(190, 196, 206, 255))
        if eyes:
            ld.ellipse([cx - 30, h * 0.18 + 45, cx - 12, h * 0.18 + 58], fill=(0, 0, 0, 255))
            ld.ellipse([cx + 12, h * 0.18 + 45, cx + 30, h * 0.18 + 58], fill=(0, 0, 0, 255))
        a = lay.split()[3].point(lambda p: int(p * girl_alpha))
        m.paste(lay.convert("RGB"), (0, 0), a)
    return m


def build_seat():
    arr = vgrad(BW, BH, (10, 13, 20), (4, 5, 8))
    # rear window light
    add_glow(arr, BW * 0.5, BH * 0.3, BW * 0.45, (40, 55, 75), 1.0)
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    # rear window shape
    d.rounded_rectangle([BW * 0.14, BH * 0.16, BW * 0.86, BH * 0.42], radius=120, outline=INK, width=60)
    d.rectangle([0, 0, BW, BH * 0.14], fill=INK)
    # back seat
    d.rounded_rectangle([BW * 0.04, BH * 0.40, BW * 0.96, BH * 0.70], radius=90, fill=(16, 18, 24))
    d.line([(BW * 0.5, BH * 0.42), (BW * 0.5, BH * 0.69)], fill=(8, 9, 12), width=10)
    d.rounded_rectangle([BW * 0.02, BH * 0.66, BW * 0.98, BH * 0.80], radius=60, fill=(20, 22, 28))
    d.rounded_rectangle([BW * 0.18, BH * 0.37, BW * 0.32, BH * 0.43], radius=30, fill=(14, 16, 22))   # headrests
    d.rounded_rectangle([BW * 0.68, BH * 0.37, BW * 0.82, BH * 0.43], radius=30, fill=(14, 16, 22))
    # front seat silhouettes framing
    d.rounded_rectangle([-BW * 0.15, BH * 0.55, BW * 0.30, BH * 1.1], radius=120, fill=INK)
    d.rounded_rectangle([BW * 0.70, BH * 0.55, BW * 1.15, BH * 1.1], radius=120, fill=INK)
    return img


def build_door():
    arr = vgrad(BW, BH, (10, 12, 18), (24, 28, 34), 0.0, 1.0)
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    # facade
    d.rectangle([0, 0, BW, BH], fill=(14, 15, 19))
    for i in range(0, BH, 46):  # siding
        d.line([(0, i), (BW, i)], fill=(10, 11, 14), width=4)
    dx0, dy0, dx1, dy1 = BW * 0.33, BH * 0.30, BW * 0.67, BH * 0.78
    d.rectangle([dx0 - 50, dy0 - 80, dx1 + 50, dy1], fill=INK)  # frame
    # warm hallway gradient
    hall = vgrad(int(dx1 - dx0), int(dy1 - dy0), (150, 100, 50), (90, 55, 25))
    hall = add_glow(hall, (dx1 - dx0) * 0.5, (dy1 - dy0) * 0.2, (dx1 - dx0) * 0.6, (100, 70, 30), 1.0)
    img.paste(to_img(hall), (int(dx0), int(dy0)))
    d = ImageDraw.Draw(img)
    # stairs inside (silhouette)
    for i in range(7):
        y = dy0 + (dy1 - dy0) * (0.45 + i * 0.07)
        d.rectangle([dx0 + (dx1 - dx0) * (0.65 - i * 0.05), y, dx1, dy1], fill=(40, 24, 12))
    # open door slab
    d.polygon([(dx0, dy0), (dx0 - 140, dy0 - 40), (dx0 - 140, dy1 + 40), (dx0, dy1)], fill=(20, 16, 14))
    # light spill onto porch
    d.polygon([(dx0, dy1), (dx1, dy1), (dx1 + 260, BH), (dx0 - 260, BH)], fill=(70, 46, 24))
    # porch
    d.rectangle([0, dy1, BW, dy1 + 20], fill=INK)
    for x in (BW * 0.08, BW * 0.92):
        d.rectangle([x - 30, BH * 0.15, x + 30, dy1], fill=INK)
    d.rectangle([0, BH * 0.12, BW, BH * 0.16], fill=INK)
    # porch lamp
    d.line([(BW * 0.75, BH * 0.30), (BW * 0.75, BH * 0.34)], fill=INK, width=8)
    return img, (dx0, dy0, dx1, dy1)


# ----------------------------------------------------------------- global state

G = {}


def init_worker():
    G["road"] = build_road()
    G["house"], G["house_pos"] = build_house()
    G["car"], G["mirror"] = build_car()
    G["seat"] = build_seat()
    G["door"], G["door_rect"] = build_door()
    G["girl_far"] = figure_layers(330, "girl")
    G["girl_mid"] = figure_layers(620, "girl")
    G["girl_hall"] = figure_layers(400, "girl")
    G["woman"] = figure_layers(760, "woman")
    G["fog1"] = np.asarray(smooth_noise(W * 2, H, 160, 11, 30), np.float32) / 255.0
    G["fog2"] = np.asarray(smooth_noise(W * 2, H, 60, 12, 12), np.float32) / 255.0
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2)
    G["vign"] = np.clip(1.15 - r * r * 0.75, 0.15, 1)[..., None]
    rng = np.random.default_rng(5)
    G["grain"] = [rng.normal(0, 5, (H, W, 1)).astype(np.float32) for _ in range(6)]
    drops = Image.new("L", (BW, BH), 0)
    dd = ImageDraw.Draw(drops)
    rr = random.Random(3)
    for _ in range(700):
        x, y, s = rr.uniform(0, BW), rr.uniform(0, BH * 0.68), rr.uniform(3, 11)
        dd.ellipse([x - s, y - s * 1.2, x + s, y + s * 1.2], fill=rr.randint(60, 140))
    G["drops"] = np.asarray(drops.filter(ImageFilter.GaussianBlur(1.5)), np.float32)[..., None] / 255.0
    G["captions"] = [caption_img(p[2]) for p in PHRASES]
    G["title"] = title_img()


def wrap(text, font, maxw, draw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    lines.append(cur)
    return lines


def caption_img(text):
    font = ImageFont.truetype(FONT_BOLD, 66)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines = wrap(text, font, 900, tmp)
    lh = 84
    img = Image.new("RGBA", (W, lh * len(lines) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        d.text((W / 2, 20 + i * lh + lh / 2), ln, font=font, fill=(240, 236, 228, 255),
               anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0, 255))
    return img


def title_img():
    img = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f1 = ImageFont.truetype(FONT_TITLE, 104)
    f2 = ImageFont.truetype(FONT_BOLD, 40)
    d.text((W / 2, 150), "THE GIRL ON", font=f1, fill=(225, 220, 210, 255), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 255))
    d.text((W / 2, 270), "ROUTE NINE", font=f1, fill=(200, 40, 36, 255), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 255))
    d.text((W / 2, 370), "an urban legend", font=f2, fill=(170, 170, 170, 255), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, 255))
    return img


# ----------------------------------------------------------------- per-frame


def ease(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def scene_at(t):
    idx = 0
    for i, (_, st) in enumerate(SCENES):
        if t >= st:
            idx = i
    st = SCENES[idx][1]
    en = SCENES[idx + 1][1] if idx + 1 < len(SCENES) else DUR
    return SCENES[idx][0], t - st, (t - st) / (en - st), st, en


def render_scene(name, lt, p, t, rng):
    """Returns (bg PIL image, camera (zoom, cx, cy) in bg coords, fog density, rain amount)."""
    ta = (t - LEAD) * TEMPO
    if name == "road":
        img = G["road"].copy()
        draw_road_dashes(img, lt * 5.0)
        arr = np.asarray(img, np.float32)
        arr += headlight_cone(arr, 0.9)[..., None] * np.array([70, 62, 45], np.float32)
        img = to_img(arr)
        z = 1.0 + 0.12 * ease(p)
        cx = BW / 2 + math.sin(lt * 1.3) * 10
        cy = BH / 2 + math.sin(lt * 7) * 3
        return img, (z, cx, cy), 0.55, 1.0
    if name == "girl":
        img = G["road"].copy()
        draw_road_dashes(img, 0.4 + lt * 0.6 * max(0, 1 - lt / 3))
        arr = np.asarray(img, np.float32)
        arr += headlight_cone(arr, 1.0)[..., None] * np.array([70, 62, 45], np.float32)
        img = to_img(arr)
        fx, fy = BW * 0.66, HORIZON + 330
        a = 1.0
        if v(10.99) < t < v(11.6) or v(12.36) < t < v(13.05):
            a = 0.35 + 0.65 * (rng.random() > 0.4)
        a *= ease(lt / 1.2)
        paste_figure(img, G["girl_far"], fx, fy, a, glow_amt=0.9)
        z = 1.0 + 0.55 * ease(p)
        cx = BW / 2 + (fx - BW / 2) * ease(p) * 0.9
        cy = BH / 2 + (fy - 200 - BH / 2) * ease(p) * 0.8
        return img, (z, cx, cy), 0.6, 1.0
    if name == "car":
        img = G["car"].copy()
        arr = np.asarray(img, np.float32)
        arr = arr * (1 - G["drops"] * 0.5) + G["drops"] * 70
        img = to_img(arr)
        d = ImageDraw.Draw(img)
        # wipers
        for px, ph in ((BW * 0.25, 0.0), (BW * 0.62, 0.15)):
            ang = math.pi * (0.12 + 0.62 * (0.5 - 0.5 * math.cos((lt * 1.6 + ph) * math.pi)))
            L = BW * 0.62
            d.line([(px, BH * 0.68), (px + math.cos(ang) * L, BH * 0.68 - math.sin(ang) * L)], fill=INK, width=18)
        mx0, my0, mx1, my1 = [int(q) for q in G["mirror"]]
        ga = ease((ta - 15.4) / 0.8)
        if ta > 18.3:
            ga *= 0.6 + 0.4 * (rng.random() > 0.25)
        m = mirror_content(mx1 - mx0, my1 - my0, ga, eyes=ta > 18.6)
        mask = Image.new("L", m.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, m.size[0] - 1, m.size[1] - 1], radius=36, fill=255)
        img.paste(m, (mx0, my0), mask)
        k = ease((ta - 15.0) / 4.0)
        z = 1.0 + 0.7 * k
        cx = BW / 2
        cy = BH / 2 + ((my0 + my1) / 2 - BH / 2) * k
        cx += math.sin(lt * 9) * 3
        return img, (z, cx, cy), 0.25 * (1 - k), 0.5 * (1 - k)
    if name == "house":
        img = G["house"].copy()
        hx, hy = G["house_pos"]
        fl = 1.0 if rng.random() > 0.08 else 0.25
        house_windows(img, hx, hy, fl)
        z = 1.15 - 0.1 * ease(p)
        cx = BW / 2 + 40 * ease(p)
        cy = BH / 2 - 120 + 80 * ease(p)
        return img, (z, cx, cy), 0.5, 1.0
    if name == "seat":
        img = G["seat"].copy()
        d = ImageDraw.Draw(img)
        # puddle with ripples
        px, py = BW * 0.70, BH * 0.725
        d.ellipse([px - 170, py - 34, px + 170, py + 34], fill=(40, 52, 66))
        for k in range(3):
            rr = ((lt * 0.9 + k / 3) % 1)
            d.ellipse([px - 160 * rr, py - 30 * rr, px + 160 * rr, py + 30 * rr],
                      outline=(int(90 * (1 - rr)) + 20, int(110 * (1 - rr)) + 25, int(130 * (1 - rr)) + 30), width=3)
        # drip from seat edge
        dy = (lt * 1.4) % 1
        d.ellipse([px + 40 - 5, BH * 0.66 + dy * 90, px + 40 + 5, BH * 0.66 + dy * 90 + 14], fill=(100, 120, 140))
        punch = ease(lt / 0.35)
        z = 1.35 - 0.25 * punch + 0.08 * ease(p)
        cx = BW / 2 + 120 * ease(p)
        cy = BH * 0.56
        return img, (z, cx, cy), 0.2, 0.0
    if name == "door":
        img = G["door"].copy()
        dx0, dy0, dx1, dy1 = G["door_rect"]
        # ghost girl appears in the hallway behind her on "seventh driver"
        ga = ease((ta - 36.4) / 0.6) * (1 - ease((ta - 38.6) / 0.3))
        if ga > 0:
            ga *= 0.55 + 0.45 * (rng.random() > 0.3)
            paste_figure(img, G["girl_hall"], dx0 + (dx1 - dx0) * 0.80, dy1 - 330, ga * 0.6, glow_amt=0.7)
        wa = ease((ta - 27.6) / 0.7)
        paste_figure(img, G["woman"], (dx0 + dx1) / 2 - 30, dy1 + 6, wa, glow_amt=0)
        z = 1.0 + 0.45 * ease(p)
        cx = BW / 2
        cy = BH / 2 + (dy0 + 200 - BH / 2) * ease(p)
        return img, (z, cx, cy), 0.3, 0.6
    # end: girl standing in the middle of the road, waiting
    img = G["road"].copy()
    draw_road_dashes(img, 0.2)
    arr = np.asarray(img, np.float32)
    arr += headlight_cone(arr, 0.8)[..., None] * np.array([70, 62, 45], np.float32)
    img = to_img(arr)
    ga = ease(lt / 1.0)
    if ta > 43.3:
        ga *= 1 - ease((ta - 43.9) / 0.4)
        ga *= 0.4 + 0.6 * (rng.random() > 0.35)
    paste_figure(img, G["girl_mid"], VPX, HORIZON + 520, ga, glow_amt=1.0)
    z = 1.0 + 0.5 * ease(p)
    return img, (z, BW / 2, BH / 2 + 60 * ease(p)), 0.6, 1.0


def camera(img, z, cx, cy):
    cw, ch = min(BW, W / z), min(BH, H / z)
    cx = min(max(cx, cw / 2), BW - cw / 2)
    cy = min(max(cy, ch / 2), BH - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return img.transform((W, H), Image.EXTENT, box, Image.BILINEAR)


def render_frame(fi):
    t = fi / FPS
    rng = random.Random(fi * 7919)
    name, lt, p, st, en = scene_at(t)
    img, (z, cx, cy), fog, rain = render_scene(name, lt, p, t, rng)
    img = camera(img, z, cx, cy)
    arr = np.asarray(img, np.float32)

    # fog: two scrolling layers
    if fog > 0:
        o1 = int((t * 40) % W)
        o2 = int((t * 95) % W)
        f = G["fog1"][:, o1:o1 + W] * 0.65 + G["fog2"][:, o2:o2 + W] * 0.35
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        band = 0.5 + 0.5 * np.exp(-((yy - 0.55) / 0.25) ** 2)
        a = np.clip((f - 0.25) * 1.4, 0, 1) * band * fog
        arr = arr * (1 - a[..., None] * 0.8) + np.array([95, 105, 118], np.float32) * (a[..., None] * 0.8)

    # rain streaks
    if rain > 0:
        mask = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(mask)
        rr = random.Random(fi)
        n = int(320 * rain)
        for _ in range(n):
            x = rr.uniform(-100, W)
            y = rr.uniform(-200, H)
            L = rr.uniform(40, 120)
            md.line([(x, y), (x + L * 0.18, y + L)], fill=rr.randint(50, 150), width=rr.choice([1, 2, 2, 3]))
        m = np.asarray(mask, np.float32)[..., None] / 255.0
        arr = arr + m * np.array([150, 160, 175], np.float32) * 0.55

    # flicker + lightning
    flick = 1.0 - 0.07 * rng.random()
    if rng.random() < 0.03:
        flick *= 0.6
    for lt0 in LIGHTNING:
        dt = t - lt0
        if 0 <= dt < 0.5:
            pulse = (math.exp(-dt * 14) + 0.6 * math.exp(-max(0, dt - 0.18) * 18) * (dt > 0.18))
            arr = arr + pulse * 140
            flick *= 1 + pulse * 0.6
    arr = arr * flick

    # scene cut dips
    dip = 1.0
    for _, sst in SCENES[1:]:
        d = abs(t - sst)
        if d < 0.18:
            dip = min(dip, d / 0.18)
    if t < 0.4:
        dip = min(dip, t / 0.4)
    if t > DUR - 0.9:
        dip = min(dip, max(0, (DUR - t) / 0.9))
    # color grade: crush + cold tint
    arr = arr * G["vign"] * dip
    arr = arr * np.array([0.92, 0.98, 1.08], np.float32)
    arr += G["grain"][fi % 6]
    img = to_img(arr)

    # title card
    if t < 3.0:
        a = ease(t / 0.6) * (1 - ease((t - 2.3) / 0.7))
        ti = G["title"]
        al = ti.split()[3].point(lambda q: int(q * a))
        img.paste(ti, (0, 230), al)
    # captions
    ta = (t - LEAD) * TEMPO
    for i, (s0, s1, _) in enumerate(PHRASES):
        nxt = PHRASES[i + 1][0] if i + 1 < len(PHRASES) else s1 + 0.9
        if s0 - 0.05 <= ta < min(nxt - 0.05, s1 + 0.6):
            c = G["captions"][i]
            img.paste(c, (0, int(H * 0.64)), c)
            break
    return img.tobytes()


def main():
    preview = None
    if "--preview" in sys.argv:
        preview = float(sys.argv[sys.argv.index("--preview") + 1])
    out_dir = os.path.join(ROOT, "shorts")
    os.makedirs(out_dir, exist_ok=True)
    narr = os.path.join(HERE, "narration_raw.mp3")
    out = os.path.join(out_dir, "girl_on_route_nine.mp4")
    nframes = int(DUR * FPS)
    if preview is not None:
        # single still for inspection
        init_worker()
        fi = int(preview * FPS)
        Image.frombytes("RGB", (W, H), render_frame(fi)).save(os.path.join(out_dir, f"preview_{preview:05.2f}.png"))
        return
    delay_ms = int(LEAD * 1000)
    afilter = (
        f"[1:a]atempo={TEMPO},adelay={delay_ms}|{delay_ms},highpass=f=60,"
        f"acompressor=threshold=-20dB:ratio=3:attack=5:release=120,volume=1.6[vo];"
        # self-synthesised ambience: rain (filtered noise) + low drone
        f"anoisesrc=color=pink:amplitude=0.5:d={DUR:.2f},lowpass=f=5000,highpass=f=400,volume=0.10[rain];"
        f"sine=f=55:d={DUR:.2f},volume=0.05[d1];sine=f=82.4:d={DUR:.2f},volume=0.025,tremolo=f=0.2:d=0.7[d2];"
        f"[rain][d1][d2]amix=inputs=3:normalize=0,afade=t=in:d=0.8,afade=t=out:st={DUR - 1.2:.2f}:d=1.2[amb];"
        f"[vo][amb]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=11,"
        f"atrim=0:{DUR:.2f}[a]"
    )
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", narr, "-filter_complex", afilter,
           "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-movflags", "+faststart",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-t", f"{DUR:.2f}", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=init_worker) as pool:
        for i, fr in enumerate(pool.imap(render_frame, range(nframes), chunksize=4)):
            proc.stdin.write(fr)
            if i % 150 == 0:
                print(f"frame {i}/{nframes}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("wrote", out, f"{DUR:.2f}s")


if __name__ == "__main__":
    main()

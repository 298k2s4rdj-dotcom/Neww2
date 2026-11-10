#!/usr/bin/env python3
"""Catchy 4K YouTube thumbnail (3840x2160) for '1 Woche ohne Schlaf' – red headline, Rate-mal style."""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tiere"))
from engine import text, text_w, FONT_XB  # noqa: E402

W, H = 3840, 2160
K = 4            # shapes: design units (1920x1080) -> 2x supersampled 4K
T = 2            # text: design units -> 4K
NAVY = (40, 20, 60)
RED = (240, 30, 45)
YELLOW = (255, 226, 60)
WHITE = (255, 255, 255)
SKIN = (255, 214, 170)
FX, FY, FR = 1430, 610, 390      # big face


def P(*v):
    return tuple(x * K for x in v)


def background():
    y = np.linspace(0, 1, H)[:, None, None]
    bg = np.array([12, 12, 48]) * (1 - y) + np.array([70, 26, 110]) * y
    bg = np.repeat(bg, W, axis=1)
    yy, xx = np.mgrid[0:H, 0:W]
    g = np.exp(-(((xx - FX * T) / 1300) ** 2 + ((yy - FY * T) / 1100) ** 2))[..., None]
    bg = bg + g * np.array([190, 20, 40])
    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")
    rays = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(rays)
    n = 22
    for k in range(n):
        a0 = k / n * 2 * math.pi + 0.1
        a1 = a0 + math.pi / n
        d.polygon([(FX * T, FY * T), (FX * T + 5000 * math.cos(a0), FY * T + 5000 * math.sin(a0)),
                   (FX * T + 5000 * math.cos(a1), FY * T + 5000 * math.sin(a1))], fill=(255, 255, 255, 22))
    img.alpha_composite(rays)
    d = ImageDraw.Draw(img)
    r = random.Random(4)
    for _ in range(420):
        x, yv, s = r.uniform(0, W), r.uniform(0, H), r.uniform(1.5, 5)
        v = int(r.uniform(120, 255))
        d.ellipse((x - s, yv - s, x + s, yv + s), fill=(v, v, v))
    return img


def tired_face(d, cx, cy, r):
    # messy hair
    rr = random.Random(2)
    for k in range(15):
        a = math.pi + 0.15 + k / 14 * (math.pi - 0.3)
        tip = r * rr.uniform(1.12, 1.38)
        d.polygon([P(cx + r * 0.9 * math.cos(a - 0.14), cy + r * 0.9 * math.sin(a - 0.14)),
                   P(cx + tip * math.cos(a + rr.uniform(-0.1, 0.1)), cy + tip * math.sin(a)),
                   P(cx + r * 0.9 * math.cos(a + 0.14), cy + r * 0.9 * math.sin(a + 0.14))], fill=(95, 60, 45))
    d.ellipse(P(cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10), fill=NAVY)
    d.ellipse(P(cx - r, cy - r, cx + r, cy + r), fill=SKIN)
    d.chord(P(cx - r, cy - r, cx + r, cy + r), 200, 340, fill=(95, 60, 45))
    for k in (-1, 1):
        ex, ey = cx + k * r * 0.42, cy - r * 0.08
        rx, ry = r * 0.33, r * 0.30
        # bags
        d.ellipse(P(ex - rx * 1.05, ey + ry * 0.35, ex + rx * 1.05, ey + ry * 1.55), fill=(150, 95, 150))
        d.ellipse(P(ex - rx * 0.8, ey + ry * 0.75, ex + rx * 0.8, ey + ry * 1.35), fill=(120, 70, 125))
        # eyeball
        d.ellipse(P(ex - rx - 5, ey - ry - 5, ex + rx + 5, ey + ry + 5), fill=NAVY)
        d.ellipse(P(ex - rx, ey - ry, ex + rx, ey + ry), fill=(255, 240, 240))
        rv = random.Random(5 + k)
        for j in range(11):
            a = j / 11 * 2 * math.pi + rv.uniform(0, 0.4)
            pts = []
            for q in (1.0, 0.8, 0.62, 0.45):
                a += rv.uniform(-0.18, 0.18)
                pts.append(P(ex + rx * q * math.cos(a), ey + ry * q * math.sin(a)))
            d.line(pts, fill=(235, 40, 55), width=int(2.6 * K))
        ir = r * 0.11
        d.ellipse(P(ex - ir * 1.5, ey - ir * 1.5 + ry * 0.2, ex + ir * 1.5, ey + ir * 1.5 + ry * 0.2), fill=(90, 150, 220))
        d.ellipse(P(ex - ir * 0.7, ey - ir * 0.7 + ry * 0.2, ex + ir * 0.7, ey + ir * 0.7 + ry * 0.2), fill=NAVY)
        # heavy eyelid
        d.chord(P(ex - rx - 5, ey - ry - 5, ex + rx + 5, ey + ry + 5), 195 - 8 * k, 345 - 8 * k, fill=(235, 180, 150))
        d.line([P(ex - rx * 0.98, ey - ry * 0.28 + 12 * k), P(ex + rx * 0.98, ey - ry * 0.28 - 12 * k)], fill=NAVY,
               width=int(5 * K))
        # worried brow
        d.line([P(ex - k * rx * 1.0, ey - ry * 1.25), P(ex + k * rx * 0.6, ey - ry * 1.7)], fill=(95, 60, 45),
               width=int(13 * K))
    # wobbly mouth
    pts = [P(cx - r * 0.34 + i * r * 0.68 / 24, cy + r * 0.56 + r * 0.045 * math.sin(i * 1.05)) for i in range(25)]
    d.line(pts, fill=NAVY, width=int(9 * K), joint="curve")
    # sweat drop
    sx, sy = cx + r * 0.78, cy - r * 0.52
    d.polygon([P(sx, sy - 55), P(sx - 26, sy), P(sx + 26, sy)], fill=(140, 215, 255))
    d.ellipse(P(sx - 26, sy - 22, sx + 26, sy + 30), fill=(140, 215, 255))


def fresh_face(d, cx, cy, r):
    d.ellipse(P(cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6), fill=NAVY)
    d.ellipse(P(cx - r, cy - r, cx + r, cy + r), fill=SKIN)
    d.chord(P(cx - r, cy - r, cx + r, cy + r), 200, 340, fill=(95, 60, 45))
    for k in (-1, 1):
        d.ellipse(P(cx + k * r * 0.38 - 11, cy - r * 0.1 - 13, cx + k * r * 0.38 + 11, cy - r * 0.1 + 13), fill=NAVY)
    d.arc(P(cx - r * 0.42, cy - r * 0.05, cx + r * 0.42, cy + r * 0.62), 20, 160, fill=NAVY, width=int(7 * K))


def big_text(img, s, size, cx, cy, fill, rot=0.0, inner=WHITE):
    text(img, s, size * T, cx * T + 10 * T, cy * T + 12 * T, fill=NAVY, stroke=int(size * 0.13 * T), sfill=NAVY,
         rotate=rot)
    text(img, s, size * T, cx * T, cy * T, fill=fill, stroke=int(size * 0.075 * T), sfill=inner, rotate=rot)


def main():
    img = background()
    lay = Image.new("RGBA", (W * 2, H * 2))
    d = ImageDraw.Draw(lay)
    tired_face(d, FX, FY, FR)
    fresh_face(d, 190, 880, 105)
    # arrow fresh -> tired
    d.line([P(330, 880), P(560, 880)], fill=YELLOW, width=int(22 * K))
    d.polygon([P(545, 835), P(545, 925), P(630, 880)], fill=YELLOW)
    # empty battery
    bx, by, bw, bh = 815, 880, 200, 104
    d.rounded_rectangle(P(bx - bw / 2, by - bh / 2, bx + bw / 2, by + bh / 2), 18 * K, fill=NAVY, outline=WHITE,
                        width=int(9 * K))
    d.rounded_rectangle(P(bx + bw / 2, by - 22, bx + bw / 2 + 18, by + 22), 5 * K, fill=WHITE)
    d.rounded_rectangle(P(bx - bw / 2 + 16, by - bh / 2 + 16, bx - bw / 2 + 44, by + bh / 2 - 16), 5 * K, fill=RED)
    # 168 h badge
    badge = Image.new("RGBA", (int(430 * K), int(215 * K)))
    ImageDraw.Draw(badge).rounded_rectangle((0, 0, 430 * K - 1, 215 * K - 1), 40 * K, fill=YELLOW + (255,),
                                            outline=NAVY + (255,), width=int(9 * K))
    badge = badge.rotate(7, resample=Image.BICUBIC, expand=True)
    lay.alpha_composite(badge, (int(1470 * K), int(790 * K)))
    # brand pill
    d.rounded_rectangle(P(60, 40, 480, 140), 50 * K, fill=YELLOW, outline=NAVY, width=int(7 * K))
    lay = lay.resize((W, H), Image.LANCZOS)
    glow = Image.new("RGBA", (W, H))
    glow.paste((255, 40, 60, 150), mask=lay.getchannel("A").filter(ImageFilter.MaxFilter(9)))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30)))
    img.alpha_composite(lay)
    # texts
    for s, size, cy in (("1 WOCHE", 215, 300), ("OHNE", 190, 500), ("SCHLAF?!", 190, 690)):
        size = min(size, size * 900 / text_w(s, size))
        big_text(img, s, size, 500, cy, RED, rot=-3)
    text(img, "168 h", 100 * T, 1690 * T, 893 * T, fill=RED, stroke=5 * T, sfill=NAVY, rotate=7)
    text(img, "WACH", 48 * T, 1700 * T, 978 * T, fill=NAVY, path=FONT_XB, rotate=7)
    text(img, "RATE MAL", 58 * T, 238 * T, 92 * T, fill=NAVY)
    text(img, "?", 78 * T, 428 * T, 92 * T, fill=RED, stroke=5 * T, sfill=NAVY, rotate=10)
    text(img, "TAG 1", 46 * T, 190 * T, 1025 * T, fill=WHITE, stroke=6 * T, sfill=NAVY)
    text(img, "1 %", 46 * T, 815 * T, 1025 * T, fill=RED, stroke=6 * T, sfill=WHITE)
    text(img, "TAG 7", 70 * T, 1790 * T, 180 * T, fill=YELLOW, stroke=8 * T, sfill=NAVY, rotate=8)
    out = img.convert("RGB")
    out.save(os.path.join(HERE, "thumbnail_4k.png"), optimize=True)
    out.save(os.path.join(HERE, "thumbnail_4k.jpg"), quality=90)      # < 2 MB for the YouTube upload
    out.resize((1280, 720), Image.LANCZOS).save(os.path.join(HERE, "thumbnail.png"))
    print("ok")


if __name__ == "__main__":
    main()

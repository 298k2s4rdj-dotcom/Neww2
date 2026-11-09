#!/usr/bin/env python3
"""YouTube banner (2560x1440) for the "Rate mal" channel – colourful starry style of the videos.

Safe area for all devices: 1546x423 centred (x 507–2053, y 508–931). Text stays inside it;
figures sit in the desktop band (2560x423) to the left/right of the safe area.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "ratemal_color"))
import col as C  # noqa: E402
from col import E, paste_c, text, FONT_XB  # noqa: E402

W, H = 2560, 1440
SX0, SX1, SY0, SY1 = 507, 2053, 508, 931


def background():
    y = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([10, 14, 50]), np.array([70, 34, 120])
    bg = top * (1 - y) + bot * y
    bg = np.repeat(bg, W, axis=1)
    yy, xx = np.mgrid[0:H, 0:W]
    glow = np.exp(-(((xx - W / 2) / 900) ** 2 + ((yy - H / 2) / 380) ** 2))[..., None]
    bg = bg + glow * np.array([40, 60, 120])
    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    r = random.Random(4)
    for _ in range(420):
        x, yv, s = r.uniform(0, W), r.uniform(0, H), r.uniform(1, 3.2)
        v = int(r.uniform(120, 255))
        d.ellipse((x - s, yv - s, x + s, yv + s), fill=(v, v, v))
    return img


def brand_pill(img, cx, cy, scale=1.0):
    w, h = 560 * scale, 130 * scale
    sh = Image.new("RGBA", img.size)
    ImageDraw.Draw(sh).rounded_rectangle((cx - w + 10, cy - h + 18, cx + w + 10, cy + h + 18), int(h),
                                         fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(sh)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((cx - w, cy - h, cx + w, cy + h), int(h), fill=C.YELLOW + (255,), outline=(40, 20, 60),
                        width=int(10 * scale))
    text(img, "RATE MAL", 165 * scale, cx - 95 * scale, cy + 4, fill=(40, 20, 60))
    text(img, "?", 210 * scale, cx + 430 * scale, cy + 4, fill=(235, 50, 70), stroke=int(10 * scale),
         sfill=(40, 20, 60), rotate=10)


def earth(img, cx, cy, r):
    lay = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - r - 20, cy - r - 20, cx + r + 20, cy + r + 20), fill=(80, 160, 255, 60))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(40, 120, 230, 255))
    land = Image.new("RGBA", img.size)
    dl = ImageDraw.Draw(land)
    rr = random.Random(5)
    for _ in range(9):
        a, q = rr.uniform(0, 6.28), rr.uniform(0.1, 0.85) * r
        x, y = cx + q * math.cos(a), cy + q * math.sin(a)
        w, h = rr.uniform(0.15, 0.35) * r, rr.uniform(0.1, 0.22) * r
        dl.ellipse((x - w, y - h, x + w, y + h), fill=(70, 180, 90, 255))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    land.putalpha(Image.fromarray(np.minimum(np.array(land.getchannel("A")), np.array(mask))))
    lay.alpha_composite(land)
    img.alpha_composite(lay)


def main():
    img = background()
    d = ImageDraw.Draw(img)
    # --- centre (safe area) ---
    brand_pill(img, W / 2, 655, 0.86)
    text(img, "Was passiert, wenn …?", 96, W / 2, 815, fill=(255, 255, 255), stroke=8, sfill=(30, 20, 60))
    text(img, "KÖRPER  ·  WELTALL  ·  NATUR  ·  MYTHEN", 46, W / 2, 900, fill=C.YELLOW, path=FONT_XB, stroke=5,
         sfill=(30, 20, 60))
    # --- left desktop band ---
    paste_c(img, E.person_sprite(330, C.ORANGE, arms_up=0.9), 300, 880, anchor="b")
    text(img, "?", 210, 150, 610, fill=C.YELLOW, stroke=10, sfill=(40, 20, 60), rotate=-12)
    C.cloud(img, 380, 470, 0.7, (150, 155, 180))
    C.bolt(img, 400, 520, 470, 720, seed=3, w=14)
    paste_c(img, C.duck(1.0), 140, 860)
    # --- right desktop band ---
    earth(img, 2300, 760, 150)
    sp = E.SS(140, 260)
    sp.rect(40, 60, 100, 210, 30, (240, 240, 250, 255))
    sp.poly([(40, 80), (70, 5), (100, 80)], (235, 60, 70, 255))
    sp.ell(70, 120, 18, 18, (90, 170, 255, 255))
    sp.poly([(40, 170), (10, 230), (40, 210)], (235, 60, 70, 255))
    sp.poly([(100, 170), (130, 230), (100, 210)], (235, 60, 70, 255))
    sp.poly([(52, 210), (70, 255), (88, 210)], (255, 180, 40, 255))
    rocket = sp.img().rotate(-25, resample=Image.BICUBIC, expand=True)
    paste_c(img, rocket, 2140, 560)
    text(img, "?", 190, 2440, 560, fill=C.YELLOW, stroke=10, sfill=(40, 20, 60), rotate=12)
    paste_c(img, E.heart_sprite(130), 2470, 900)
    _ = d
    out = os.path.join(HERE, "youtube_banner_ratemal.png")
    img.convert("RGB").save(out, optimize=True)
    # previews: desktop band + mobile safe area
    full = img.convert("RGB")
    full.crop((0, 508, W, 931)).save(os.path.join(HERE, "vorschau_banner_ratemal_desktop.png"))
    full.crop((SX0, SY0, SX1, SY1)).save(os.path.join(HERE, "vorschau_banner_ratemal_handy.png"))
    print("wrote", out)


if __name__ == "__main__":
    main()

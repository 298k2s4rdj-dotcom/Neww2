#!/usr/bin/env python3
"""4K thumbnail (3840x2160) for the deep-sea video – red headline, Rate-mal style."""
import importlib.util
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.argv = [sys.argv[0]]


def load(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


T = load("thumbkit", os.path.join(ROOT, "schlaf_woche", "make_thumb.py"))
Z = load("tiefsee_render", os.path.join(HERE, "render.py"))
from engine import text  # noqa: E402

W, H = 3840, 2160
y = np.linspace(0, 1, H)[:, None, None]
bg = np.array([40, 140, 225]) * (1 - y) ** 1.6 + np.array([3, 8, 30]) * (1 - (1 - y) ** 1.6)
img = Image.fromarray(np.repeat(np.clip(bg, 0, 255).astype(np.uint8), W, axis=1)).convert("RGBA")
lay = Image.new("RGBA", (W, H))
dl = ImageDraw.Draw(lay)
for k in range(9):
    x = 300 + k * 430
    dl.polygon([(x, 0), (x + 160, 0), (x + 520, H), (x + 260, H)], fill=(255, 255, 255, 26))
img.alpha_composite(lay)
d = ImageDraw.Draw(img)
r = random.Random(3)
for _ in range(300):
    x, yy, s = r.uniform(0, W), r.uniform(0, H), r.uniform(2, 6)
    d.ellipse((x - s, yy - s, x + s, yy + s), fill=(200, 220, 255))
# diver heading down + bubbles
Z.paste_c(img, Z.diver(1000, kick=0.5, tilt=-60), 2700, 900)
for k in range(10):
    x, yy, rr = 2900 + r.uniform(-120, 120), 420 - k * 38, r.uniform(14, 34)
    d.ellipse((x - rr, yy - rr, x + rr, yy + rr), outline=(230, 240, 255), width=8)
# anglerfish glow bottom right
for k in range(8, 0, -1):
    rr = 30 * k
    lay = Image.new("RGBA", (W, H))
    ImageDraw.Draw(lay).ellipse((3350 - rr, 1800 - rr, 3350 + rr, 1800 + rr), fill=(120, 255, 220, 22))
    img.alpha_composite(lay)
d = ImageDraw.Draw(img)
d.ellipse((3330, 1780, 3370, 1820), fill=(255, 255, 255))
# headline
for s, size, cy in (("11 KM", 300, 300), ("TIEF?!", 220, 540)):
    T.big_text(img, s, size, 470, cy, T.RED, rot=-3)
text(img, "WAS PASSIERT MIT DIR?", 120, 940, 1560, fill=(255, 255, 255), stroke=12, sfill=T.NAVY, rotate=-3)
badge = Image.new("RGBA", (960, 380))
ImageDraw.Draw(badge).rounded_rectangle((0, 0, 959, 379), 80, fill=T.YELLOW + (255,), outline=T.NAVY + (255,),
                                        width=18)
badge = badge.rotate(-6, resample=Image.BICUBIC, expand=True)
img.alpha_composite(badge, (2600, 1620))
text(img, "1.090 bar", 140, 3090, 1820, fill=T.RED, stroke=10, sfill=T.NAVY, rotate=-6)
d.rounded_rectangle((120, 1840, 960, 2040), 100, fill=T.YELLOW, outline=T.NAVY, width=14)
text(img, "RATE MAL", 116, 476, 1944, fill=T.NAVY)
text(img, "?", 156, 856, 1944, fill=T.RED, stroke=10, sfill=T.NAVY, rotate=10)
out = img.convert("RGB")
out.save(os.path.join(HERE, "thumbnail_4k.jpg"), quality=90)
out.resize((1280, 720), Image.LANCZOS).save(os.path.join(HERE, "thumbnail.png"))
print("ok")

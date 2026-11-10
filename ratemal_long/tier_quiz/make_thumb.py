#!/usr/bin/env python3
"""4K thumbnail (3840x2160) for '7 Tier-Fakten' – red headline, Rate-mal style (shared look with schlaf_woche)."""
import importlib.util
import math
import os
import sys

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
Z = load("tierquiz", os.path.join(HERE, "render.py"))
from engine import text  # noqa: E402

T.FX, T.FY = 1440, 560
img = T.background()
paste = Z.paste_c
paste(img, Z.octopus(330, 0.6), 2880, 1260)
for x, y, s in ((2560, 1290, 170), (3200, 1290, 170), (2880, 700, 240)):
    paste(img, Z.L.E.heart_sprite(s), x, y)
d = ImageDraw.Draw(img)
for k in range(3):
    x, y = 300 + k * 150, 1960
    d.rectangle((x - 60, y - 60, x + 60, y + 60), fill=(110, 80, 55), outline=(60, 40, 30), width=8)
paste(img, Z.wombat(420), 1080, 2080, anchor="b")
for s, size, cy in (("7 TIER-FAKTEN", 150, 250), ("DIE DU NICHT", 120, 420), ("GLAUBST?!", 170, 590)):
    size = min(size, size * 880 / Z.L.text_w(s, size))
    T.big_text(img, s, size, 520, cy, T.RED, rot=-3)
badge = Image.new("RGBA", (900, 380))
ImageDraw.Draw(badge).rounded_rectangle((0, 0, 899, 379), 80, fill=T.YELLOW + (255,), outline=T.NAVY + (255,),
                                        width=18)
badge = badge.rotate(7, resample=Image.BICUBIC, expand=True)
img.alpha_composite(badge, (2880, 1600))
text(img, "3 HERZEN?!", 120, 3345, 1835, fill=T.RED, stroke=10, sfill=T.NAVY, rotate=7)
d.rounded_rectangle((120, 80, 960, 280), 100, fill=T.YELLOW, outline=T.NAVY, width=14)
text(img, "RATE MAL", 116, 476, 184, fill=T.NAVY)
text(img, "?", 156, 856, 184, fill=T.RED, stroke=10, sfill=T.NAVY, rotate=10)
out = img.convert("RGB")
out.save(os.path.join(HERE, "thumbnail_4k.jpg"), quality=90)
out.resize((1280, 720), Image.LANCZOS).save(os.path.join(HERE, "thumbnail.png"))
print("ok")

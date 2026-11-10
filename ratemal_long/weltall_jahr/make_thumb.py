#!/usr/bin/env python3
"""YouTube thumbnail 1280x720 for the 'Ein Jahr im Weltall' quiz."""
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0]]
import render as R  # noqa: E402
import longlib as L  # noqa: E402
from longlib import text, NAVY, YELLOW, paste_c  # noqa: E402

img = L.make_bg()
d = ImageDraw.Draw(img)
d.ellipse((960 - 1500, 880, 960 + 1500, 880 + 3000), fill=(40, 120, 230), outline=(120, 190, 255), width=12)
for x, y, w in ((300, 920, 200), (1000, 900, 260), (1650, 930, 200)):
    d.ellipse((x - w, y - 28, x + w, y + 34), fill=(70, 185, 95))
R.head(img, 1430, 520, 230, 1.0, 1.0)
sp = R.astronaut(560, arm=0.8).rotate(12, resample=Image.BICUBIC, expand=True)
paste_c(img, sp, 470, 560)
text(img, "1 JAHR", 190, 960, 170, fill=YELLOW, stroke=16, sfill=NAVY, rotate=-3)
text(img, "IM WELTALL?", 120, 960, 330, fill=(255, 255, 255), stroke=12, sfill=NAVY, rotate=-3)
L.brand(img, 1600, 900, 0.3, 1.5)
text(img, "7 FRAGEN", 80, 1430, 820, fill=(255, 255, 255), stroke=10, sfill=(200, 30, 50), rotate=6)
img.convert("RGB").resize((1280, 720), Image.LANCZOS).save(os.path.join(HERE, "thumbnail.png"))
print("ok")

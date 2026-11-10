#!/usr/bin/env python3
"""YouTube thumbnail 1280x720 (also 4K-ready 3840x2160) for '1 Woche ohne Schlaf'."""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0]]
import render as R  # noqa: E402
import longlib as L  # noqa: E402
from longlib import text, NAVY, YELLOW, RED  # noqa: E402

img = L.make_bg()
R.bed(img, 560, 760, eyes_open=True)
from PIL import ImageDraw
d = ImageDraw.Draw(img)
cx, cy, r = 1450, 560, 220
d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 205, 160), outline=NAVY, width=8)
for k in (-1, 1):
    ex, ey = cx + k * 85, cy - 30
    d.ellipse((ex - 70, ey + 20, ex + 70, ey + 95), fill=(150, 100, 140))
    d.ellipse((ex - 62, ey - 55, ex + 62, ey + 60), fill=(255, 255, 255), outline=NAVY, width=5)
    for j in range(6):
        import math
        a = j * 1.05
        d.line((ex + 58 * math.cos(a), ey + 52 * math.sin(a), ex + 30 * math.cos(a + 0.3), ey + 28 * math.sin(a + 0.3)),
               fill=(230, 50, 60), width=4)
    d.ellipse((ex - 12, ey - 12, ex + 12, ey + 12), fill=NAVY)
d.arc((cx - 70, cy + 90, cx + 70, cy + 150), 200, 340, fill=NAVY, width=9)
R.clock(img, 1020, 520, 120, 3.0)
text(img, "1 WOCHE", 190, 760, 170, fill=YELLOW, stroke=16, sfill=NAVY, rotate=-3)
text(img, "OHNE SCHLAF?", 120, 760, 330, fill=(255, 255, 255), stroke=12, sfill=NAVY, rotate=-3)
text(img, "168 h", 120, 1450, 880, fill=RED, stroke=12, sfill=(255, 255, 255), rotate=6)
L.brand(img, 1580, 140, 0.3, 1.4)
im = img.convert("RGB")
im.resize((1280, 720), Image.LANCZOS).save(os.path.join(HERE, "thumbnail.png"))
print("ok")

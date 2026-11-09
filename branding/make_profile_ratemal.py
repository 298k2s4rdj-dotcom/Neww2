#!/usr/bin/env python3
"""Eye-catching YouTube profile picture (800x800, shown as a circle) for "Rate mal" – no channel name."""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "ratemal_color"))
import col as C  # noqa: E402
from col import text  # noqa: E402

S = 800
K = 2            # supersampling
N = S * K
CX = CY = N / 2
NAVY = (40, 20, 60)


def main():
    img = Image.new("RGBA", (N, N), (70, 34, 140, 255))
    d = ImageDraw.Draw(img)
    # radial gradient
    for r in range(int(N * 0.75), 0, -6):
        k = r / (N * 0.75)
        col = (int(150 - 80 * k), int(60 - 26 * k), int(220 - 80 * k), 255)
        d.ellipse((CX - r, CY - r, CX + r, CY + r), fill=col)
    # sunburst rays
    rays = Image.new("RGBA", (N, N))
    dr = ImageDraw.Draw(rays)
    n = 18
    for k in range(n):
        a0 = k / n * 2 * math.pi
        a1 = a0 + math.pi / n
        dr.polygon([(CX, CY), (CX + N * math.cos(a0), CY + N * math.sin(a0)),
                    (CX + N * math.cos(a1), CY + N * math.sin(a1))], fill=(255, 255, 255, 34))
    img.alpha_composite(rays)
    # glow + yellow disc
    glow = Image.new("RGBA", (N, N))
    ImageDraw.Draw(glow).ellipse((CX - 340 * K, CY - 340 * K, CX + 340 * K, CY + 340 * K), fill=(255, 220, 60, 170))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40 * K)))
    d = ImageDraw.Draw(img)
    R = 285 * K
    d.ellipse((CX - R - 14 * K, CY - R - 14 * K, CX + R + 14 * K, CY + R + 14 * K), fill=NAVY + (255,))
    d.ellipse((CX - R, CY - R, CX + R, CY + R), fill=C.YELLOW + (255,))
    d.ellipse((CX - R * 0.75, CY - R * 0.85, CX - R * 0.15, CY - R * 0.45), fill=(255, 245, 170, 255))
    # sparkles
    for (x, y, s) in ((150, 170, 34), (660, 150, 26), (680, 640, 30), (120, 600, 22)):
        x, y, s = x * K, y * K, s * K
        d.polygon([(x, y - s), (x + s * 0.28, y - s * 0.28), (x + s, y), (x + s * 0.28, y + s * 0.28), (x, y + s),
                   (x - s * 0.28, y + s * 0.28), (x - s, y), (x - s * 0.28, y - s * 0.28)], fill=(255, 255, 255, 255))
    out = img.resize((S, S), Image.LANCZOS)
    # big question mark (drawn at final size; engine text is anti-aliased)
    text(out, "?", 560, S / 2 + 8, S / 2 + 18, fill=(40, 20, 60), rotate=8)          # shadow
    text(out, "?", 560, S / 2, S / 2 + 6, fill=(235, 50, 70), stroke=16, sfill=NAVY, rotate=8)
    out.convert("RGB").save(os.path.join(HERE, "youtube_profilbild_ratemal.png"), optimize=True)
    # circular preview
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse((0, 0, S, S), fill=255)
    prev = Image.new("RGB", (S, S), (24, 24, 24))
    prev.paste(out.convert("RGB"), (0, 0), m)
    prev.save(os.path.join(HERE, "vorschau_profilbild_ratemal_rund.png"))
    print("ok")


if __name__ == "__main__":
    main()

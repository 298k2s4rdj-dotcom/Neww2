#!/usr/bin/env python3
"""YouTube profile picture (800x800) and channel banner (2560x1440) for the
"X vs. Y" comparison channel. Reuses the self-drawn figures from the videos."""
import importlib.util
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
HI = (255, 226, 60)


def load(name, path):
    cwd = os.getcwd()
    argv = sys.argv
    sys.argv = [path]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.argv = argv
    os.chdir(cwd)
    return mod


print("loading figures …")
erde = load("erde", os.path.join(ROOT, "erde_vs_sonne", "render.py"))
wal = load("wal", os.path.join(ROOT, "tiere", "blauwal", "render.py"))
gir = load("gir", os.path.join(ROOT, "tiere", "giraffe", "render.py"))
ele = load("ele", os.path.join(ROOT, "tiere", "elefant", "render.py"))
kaf = load("kaf", os.path.join(ROOT, "mix", "kaffee", "render.py"))
lic = load("lic", os.path.join(ROOT, "mix", "licht", "render.py"))
eni = load("eni", os.path.join(ROOT, "mix", "eniac", "render.py"))


def font(sz, path=FONT):
    return ImageFont.truetype(path, int(sz))


def text_c(img, s, sz, cx, cy, fill=(255, 255, 255), stroke=0, sfill=(0, 0, 0), path=FONT, rotate=0):
    f = font(sz, path)
    bb = f.getbbox(s, stroke_width=stroke)
    w, h = bb[2] - bb[0] + 10, bb[3] - bb[1] + 10
    layer = Image.new("RGBA", (w, h))
    ImageDraw.Draw(layer).text((5 - bb[0], 5 - bb[1]), s, font=f, fill=fill + (255,), stroke_width=stroke,
                               stroke_fill=sfill + (255,))
    if rotate:
        layer = layer.rotate(rotate, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(layer, (int(cx - layer.size[0] / 2), int(cy - layer.size[1] / 2)))


def paste(img, spr, cx, cy, scale=1.0):
    if scale != 1.0:
        spr = spr.resize((max(1, int(spr.size[0] * scale)), max(1, int(spr.size[1] * scale))), Image.LANCZOS)
    img.alpha_composite(spr, (int(cx - spr.size[0] / 2), int(cy - spr.size[1] / 2)))


def split_bg(w, h, angle_dx, left=((40, 10, 30), (150, 50, 20)), right=((5, 15, 50), (10, 90, 150)), stars=200):
    y, x = np.mgrid[0:h, 0:w]
    yy = (y / h)[..., None]
    L = np.array(left[0]) * (1 - yy) + np.array(left[1]) * yy
    R = np.array(right[0]) * (1 - yy) + np.array(right[1]) * yy
    split = w / 2 + angle_dx * (0.5 - y / h)
    m = np.clip((x - split + 4) / 8, 0, 1)[..., None]
    bg = L * (1 - m) + R * m
    v = 1 - 0.35 * (((x - w / 2) / (w * 0.75)) ** 2 + ((y - h / 2) / (h * 0.8)) ** 2)
    img = Image.fromarray(np.clip(bg * v[..., None], 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(img)
    r = random.Random(4)
    for _ in range(stars):
        sx, sy, s = r.uniform(0, w), r.uniform(0, h), r.uniform(1, 3.2) * w / 1080
        b = int(r.uniform(120, 255))
        d.ellipse((sx - s, sy - s, sx + s, sy + s), fill=(b, b, b, 255))
    # glowing split line
    glow = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(glow)
    gd.line((w / 2 + angle_dx / 2, 0, w / 2 - angle_dx / 2, h), fill=(255, 255, 255, 180), width=int(w / 180))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(w / 300)))
    return img


def vs_badge(size):
    s = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(s)
    k = size
    d.ellipse((k * 0.04, k * 0.04, k * 0.96, k * 0.96), fill=(255, 255, 255, 255), outline=HI + (255,),
              width=int(k * 0.07))
    f = font(k * 0.42)
    bb = f.getbbox("VS")
    d.text((k / 2 - (bb[0] + bb[2]) / 2, k / 2 - (bb[1] + bb[3]) / 2 - k * 0.01), "VS", font=f, fill=(30, 20, 60))
    sh = Image.new("RGBA", (int(size * 1.3), int(size * 1.3)))
    sh.alpha_composite(s.filter(ImageFilter.GaussianBlur(0)), (int(size * 0.15), int(size * 0.15)))
    return sh


def profile():
    W = 800
    img = split_bg(W, W, 260, stars=120)
    # figures peeking from both sides (inside the circle crop)
    paste(img, erde.earth_sprite(250, 1.0), 200, 560)
    paste(img, erde.sun_sprite(250, 0.0), 610, 250)
    paste(img, vs_badge(330), 400, 405)
    text_c(img, "?", 120, 400, 660, fill=HI, stroke=10, sfill=(120, 30, 0))
    img = img.convert("RGB")
    img.save(os.path.join(HERE, "youtube_profilbild.png"))
    # circle preview
    m = Image.new("L", (W, W), 0)
    ImageDraw.Draw(m).ellipse((0, 0, W, W), fill=255)
    prev = Image.new("RGB", (W, W), (24, 24, 24))
    prev.paste(img, (0, 0), m)
    prev.save(os.path.join(HERE, "vorschau_profilbild_rund.png"))


def banner():
    W, H = 2560, 1440
    img = split_bg(W, H, 420, stars=380)
    t = 1.0
    # decorative figures (outside the central safe area are only visible on TV/desktop)
    figs_l = [
        (erde.earth_sprite(240, 0.8), 330, 400, 1.0),
        (lic.speaker_sprite(140), 110, 760, 1.0),
        (kaf.cup_sprite(170, 1.0), 340, 780, 1.0),
        (wal.whale_sprite(520, 1.3), 380, 1070, 1.0),
        (eni.eniac_sprite(280, 220, t, panels=3), 790, 1200, 1.0),
    ]
    figs_r = [
        (erde.sun_sprite(220, 0.0), 2230, 400, 1.0),
        (kaf.can_sprite(220, 1.0), 2230, 770, 1.0),
        (lic.bulb_sprite(150), 2460, 760, 1.0),
        (eni.phone_sprite(220, t), 1800, 1190, 1.0),
        (gir.giraffe_sprite(420, 0.5), 2130, 1170, 1.0),
        (ele.elephant_sprite(140, 0.5), 2440, 1310, 1.0),
    ]
    for spr, x, y, sc in figs_l + figs_r:
        paste(img, spr, x, y, sc)
    # central safe area 1546 x 423 (centered) – everything important lives here
    cx, cy = W / 2, H / 2
    plate = Image.new("RGBA", (W, H))
    pd = ImageDraw.Draw(plate)
    pd.rounded_rectangle((cx - 760, cy - 205, cx + 760, cy + 205), 60, fill=(0, 0, 0, 120))
    img.alpha_composite(plate.filter(ImageFilter.GaussianBlur(6)))
    paste(img, vs_badge(230), cx - 640, cy - 5)
    text_c(img, "WER GEWINNT?", 130, cx + 95, cy - 65, fill=(255, 255, 255), stroke=10, sfill=(30, 10, 40))
    text_c(img, "Verblüffende Vergleiche in unter 45 Sekunden", 50, cx + 95, cy + 70, fill=HI, path=FONT_XB,
           stroke=4, sfill=(30, 10, 40))
    text_c(img, "Tiere · Weltall · Technik · Alltag", 42, cx + 95, cy + 145, fill=(230, 235, 250), path=FONT_XB,
           stroke=3, sfill=(30, 10, 40))
    img = img.convert("RGB")
    img.save(os.path.join(HERE, "youtube_banner.png"))
    # preview with safe zones marked
    prev = img.copy()
    d = ImageDraw.Draw(prev)
    d.rectangle((cx - 773, cy - 211.5, cx + 773, cy + 211.5), outline=(0, 255, 0), width=6)
    d.rectangle((cx - 1235, cy - 211.5, cx + 1235, cy + 211.5), outline=(255, 200, 0), width=4)
    prev.resize((1280, 720), Image.LANCZOS).save(os.path.join(HERE, "vorschau_banner_sicherheitsbereich.png"))
    # what phones show (safe area only)
    img.crop((int(cx - 773), int(cy - 211.5), int(cx + 773), int(cy + 211.5))).save(
        os.path.join(HERE, "vorschau_banner_handy.png"))


profile()
banner()
print("done")

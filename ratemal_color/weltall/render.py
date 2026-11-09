#!/usr/bin/env python3
"""Rate mal, was passiert, wenn du ohne Raumanzug ins All gehst? – colourful full-frame style."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import col as C  # noqa: E402
from col import E, prog, ease_out, ease_io, back_out, paste_c, text, wt, rrect, FONT_XB  # noqa: E402


_EARTH = {}


def earth(img, gt, cy=2260, r=920):
    key = (cy, r)
    if key not in _EARTH:
        lay = Image.new("RGBA", img.size)
        d = ImageDraw.Draw(lay)
        d.ellipse((540 - r - 34, cy - r - 34, 540 + r + 34, cy + r + 34), fill=(80, 160, 255, 50))
        d.ellipse((540 - r, cy - r, 540 + r, cy + r), fill=(40, 120, 230, 255))
        land = Image.new("RGBA", img.size)
        dl = ImageDraw.Draw(land)
        rr = random.Random(5)
        for _ in range(14):
            a = rr.uniform(-2.3, -0.8)
            q = rr.uniform(0.82, 0.99) * r
            x, y = 540 + q * math.cos(a), cy + q * math.sin(a)
            w, h = rr.uniform(60, 150), rr.uniform(25, 60)
            dl.ellipse((x - w, y - h, x + w, y + h), fill=(70, 180, 90, 255))
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).ellipse((540 - r, cy - r, 540 + r, cy + r), fill=255)
        land.putalpha(Image.fromarray(__import__("numpy").minimum(__import__("numpy").array(land.getchannel("A")),
                                                                   __import__("numpy").array(mask))))
        lay.paste(land, (0, 0), land)
        _EARTH[key] = lay
    img.paste(_EARTH[key], (0, 0), _EARTH[key])


def floater(img, cx, cy, gt, scale=1.0, a=1.0, rot=None, h=380, eyes_closed=False):
    spr = E.person_sprite(h * scale, C.ORANGE, arms_up=0.6 + 0.3 * math.sin(gt * 2))
    ang = rot if rot is not None else 18 * math.sin(gt * 0.9)
    spr = spr.rotate(ang, resample=Image.BICUBIC, expand=True)
    paste_c(img, spr, cx, cy, a)


def boom(img, cx, cy, r, a=1.0):
    if a <= 0.02:
        return
    pts = []
    for k in range(24):
        ang = k / 24 * 2 * math.pi
        rad = r * (1.0 if k % 2 == 0 else 0.62)
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    lay = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(lay)
    d.polygon(pts, fill=(255, 200, 40, int(240 * a)), outline=(255, 90, 40, int(255 * a)))
    img.paste(lay, (0, 0), lay)


def rocket(s=1.0):
    sp = E.SS(140 * s, 260 * s)
    sp.rect(40 * s, 60 * s, 100 * s, 210 * s, 30 * s, (240, 240, 250, 255))
    sp.poly([(40 * s, 80 * s), (70 * s, 5 * s), (100 * s, 80 * s)], (235, 60, 70, 255))
    sp.ell(70 * s, 120 * s, 18 * s, 18 * s, (90, 170, 255, 255))
    sp.poly([(40 * s, 170 * s), (10 * s, 230 * s), (40 * s, 210 * s)], (235, 60, 70, 255))
    sp.poly([(100 * s, 170 * s), (130 * s, 230 * s), (100 * s, 210 * s)], (235, 60, 70, 255))
    sp.poly([(52 * s, 210 * s), (70 * s, 255 * s), (88 * s, 210 * s)], (255, 180, 40, 255))
    return sp.img()


def sc_hook(img, sc, t, gt):
    earth(img, gt)
    E.brand(img, t, gt, y=300)
    floater(img, 540, 800 + 20 * math.sin(gt * 1.3), gt, a=ease_out(prog(t, 0.0, 0.3)))
    paste_c(img, rocket(1.0), 230, 640 + 30 * math.sin(gt), ease_out(prog(t, 0.3, 0.3)))
    q = 1 + 0.1 * math.sin(gt * 6)
    text(img, "?", 200 * q, 820, 620, fill=C.YELLOW, stroke=10, sfill=(40, 20, 60), rotate=10,
         alpha=ease_out(prog(t, 0.5, 0.3)))
    C.pill(img, "KEIN RAUMANZUG", 540, 1120, C.RED, ease_out(prog(t, wt(sc, "Raumanzug") - 0.2, 0.3)))


def sc_explode(img, sc, t, gt):
    earth(img, gt)
    te, tn, th = wt(sc, "Explodierst"), wt(sc, "Nein"), wt(sc, "Haut")
    puff = ease_out(prog(t, te, 0.8)) * (1 - ease_io(prog(t, tn, 0.6)))
    boom(img, 540, 800, 330 * puff, a=puff)
    if puff > 0.05:
        text(img, "BOOM?", 90 * (0.8 + 0.4 * puff), 540, 450, fill=C.RED, stroke=8, sfill=(255, 255, 255),
             alpha=puff, rotate=-8)
    floater(img, 540, 800, gt, scale=1 + 0.35 * puff + 0.04 * math.sin(gt * 20) * puff)
    C.cross(img, 540, 800, 200 * ease_out(prog(t, tn, 0.3)), a=1 - prog(t, th - 0.4, 0.3))
    E.stamp(img, "MYTHOS!", t, tn + 0.1, cx=540, cy=520, size=110, rot=-6, hold=1.2)
    if t > th - 0.2:
        a = ease_out(prog(t, th - 0.2, 0.3))
        d = ImageDraw.Draw(img)
        r = 190 + 10 * math.sin(gt * 4)
        d.ellipse((540 - r, 800 - r * 1.3, 540 + r, 800 + r * 1.3), outline=C.GREEN, width=8)
        C.pill(img, "HAUT HÄLT DICH ZUSAMMEN", 540, 470, C.GREEN, a, size=36)


def sc_breathe(img, sc, t, gt):
    earth(img, gt)
    ta, t15, tb = wt(sc, "ausatmen"), wt(sc, "15"), wt(sc, "bewusstlos")
    part1 = 1 - prog(t, t15 - 0.6, 0.3)
    if part1 > 0.02:
        puff = 1.0 - 0.3 * ease_io(prog(t, ta, 0.8))
        paste_c(img, C.lungs(1.6, puff=puff), 540, 820, part1)
        if t > ta - 0.1:
            d = ImageDraw.Draw(img)
            for k in range(3):
                ph = ((t - ta) * 1.4 + k / 3) % 1
                y = 600 - 220 * ph
                d.line((540 + (k - 1) * 50, y + 60, 540 + (k - 1) * 50, y), fill=(255, 255, 255), width=10)
                d.polygon([(540 + (k - 1) * 50 - 22, y), (540 + (k - 1) * 50 + 22, y),
                           (540 + (k - 1) * 50, y - 30)], fill=(255, 255, 255))
            C.pill(img, "SOFORT AUSATMEN!", 540, 1150, C.YELLOW, ease_out(prog(t, ta - 0.1, 0.3)) * part1)
    if t > t15 - 0.6:
        a = ease_out(prog(t, t15 - 0.6, 0.3))
        s = 15 * ease_io(prog(t, t15 - 0.6, 1.4))
        C.ring(img, 540, 800, 200, s / 15, C.RED, f"{int(s)} s", "BIS BEWUSSTLOS", a)
    if t > tb - 0.2:
        E.stamp(img, "BEWUSSTLOS", t, tb - 0.1, cx=540, cy=520, size=100, rot=-6, fill=C.RED, sfill=(255, 255, 255))


def tongue(img, cx, cy, gt, a=1.0):
    sp = E.SS(420, 330)
    sp.ell(210, 165, 200, 150, (120, 30, 50, 255))
    sp.ell(210, 210, 150, 100, (255, 120, 140, 255))
    sp.line([(210, 140), (210, 260)], (220, 90, 110, 255), 6)
    paste_c(img, sp.img(), cx, cy, a)
    C.bubbles(img, cx, cy + 40, gt * 2, n=14, spread=120, rise=260, seed=8, col=(255, 230, 240))


def chamber(img, cx, cy, gt, inside_a=1.0, wake=0.0):
    rrect(img, (cx - 260, cy - 230, cx + 260, cy + 230), 60, (140, 145, 165, 255), outline=(220, 225, 235, 255),
          width=8)
    d = ImageDraw.Draw(img)
    d.ellipse((cx - 150, cy - 150, cx + 150, cy + 150), fill=(20, 30, 60), outline=(220, 225, 235), width=10)
    spr = E.person_sprite(220, C.ORANGE, arms_up=wake)
    spr = spr.rotate(70 * (1 - wake), resample=Image.BICUBIC, expand=True)
    paste_c(img, spr, cx, cy + 20, inside_a)
    for k in range(6):
        a = k / 6 * 2 * math.pi
        d.ellipse((cx + 205 * math.cos(a) - 10, cy + 205 * math.sin(a) - 10, cx + 205 * math.cos(a) + 10,
                   cy + 205 * math.sin(a) + 10), fill=(90, 95, 110))


def sc_tongue(img, sc, t, gt):
    earth(img, gt)
    tb, th, t66 = wt(sc, "blubbern"), wt(sc, "heiß"), wt(sc, "1966")
    p1 = 1 - prog(t, t66 - 0.7, 0.3)
    if p1 > 0.02:
        tongue(img, 470, 800, gt, p1)
        if t > th - 0.6:
            a = ease_out(prog(t, th - 0.6, 0.3)) * p1
            C.thermometer(img, 830, 640, 960, 0.18, (90, 170, 255))
            C.pill(img, "NICHT HEISS!", 540, 1150, C.BLUE, a)
        C.pill(img, "BLUBBERT WIE KOCHEND", 540, 470, C.SKIN, ease_out(prog(t, tb - 0.3, 0.3)) * p1, size=36)
    if t > t66 - 0.7:
        a = ease_out(prog(t, t66 - 0.7, 0.3))
        chamber(img, 540, 820, gt, a)
        text(img, "1966", 120, 540, 470, fill=C.YELLOW, stroke=8, sfill=(40, 20, 60), alpha=a,
             scale=0.9 + 0.1 * back_out(prog(t, t66 - 0.7, 0.4)))
        C.pill(img, "VAKUUMKAMMER", 540, 1150, C.WHITE, a)


def gauge(img, cx, cy, r, frac, a=1.0):
    d = ImageDraw.Draw(img)
    d.pieslice((cx - r, cy - r, cx + r, cy + r), 180, 360, fill=(25, 30, 55))
    d.arc((cx - r, cy - r, cx + r, cy + r), 180, 360, fill=(255, 255, 255), width=8)
    d.arc((cx - r + 18, cy - r + 18, cx + r - 18, cy + r - 18), 180, 180 + 180 * frac, fill=C.GREEN, width=22)
    ang = math.pi + math.pi * frac
    d.line((cx, cy, cx + (r - 30) * math.cos(ang), cy + (r - 30) * math.sin(ang)), fill=C.RED, width=10)
    d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=(255, 255, 255))
    text(img, "LUFTDRUCK", 32, cx, cy + 50, path=FONT_XB, alpha=a)


def sc_saved(img, sc, t, gt):
    earth(img, gt)
    tu, tl = wt(sc, "überlebt"), wt(sc, "Luftdruck")
    wake = ease_io(prog(t, tu - 0.3, 0.8))
    chamber(img, 540, 760, gt, 1.0, wake)
    gauge(img, 540, 1160, 150, 0.1 + 0.9 * ease_io(prog(t, 0.1, tu)))
    if t > tu - 0.1:
        E.stamp(img, "ÜBERLEBT!", t, tu, cx=540, cy=470, size=120, rot=-6, fill=C.GREEN, sfill=(20, 80, 40))
        E.confetti(img, t, tu, y0=420)
    if t > tl - 0.3:
        C.pill(img, "SCHNELL ZURÜCK IN LUFTDRUCK", 540, 1300 - 100, C.GREEN, ease_out(prog(t, tl - 0.3, 0.3)) *
               (1 - prog(t, tl + 2.5, 0.3)), size=32)


def sc_outro(img, sc, t, gt):
    earth(img, gt)

    def ml(im, x, y, a, g):
        paste_c(im, rocket(0.8), x, y, a)

    def mr(im, x, y, a, g):
        spr = E.person_sprite(170, C.ORANGE, arms_up=0.8).rotate(20 * math.sin(g), expand=True,
                                                                    resample=Image.BICUBIC)
        paste_c(im, spr, x, y, a)

    E.brand(img, t, gt, y=300)
    E.outro(img, sc, t, gt, ml, mr, line1="Ins All? Ja / Nein", line2="Schreib's uns!")


E.setup(
    here=HERE, out="ohne_raumanzug_ins_all.mp4",
    name_l="", name_r="", col_l=C.YELLOW, col_r=C.YELLOW,
    bg_l=((4, 6, 28), (54, 26, 100)), bg_r=((4, 6, 28), (54, 26, 100)),
    scenes=["hook", "explode", "breathe", "tongue", "saved", "outro"],
    draw=dict(hook=sc_hook, explode=sc_explode, breathe=sc_breathe, tongue=sc_tongue, saved=sc_saved,
              outro=sc_outro),
    sub_map=[], score=[], ticks=[(2, "15", 1, 1.4)], tempo=1.08, chimes=[],
)

if __name__ == "__main__":
    E.main()

#!/usr/bin/env python3
"""Rate mal: 7 Tier-Fakten – Quiz im Querformat (4K-fähig). Re-uses the quiz flow of weltall_jahr/render.py."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import longlib as L  # noqa: E402
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "weltall_render", os.path.join(os.path.dirname(HERE), "weltall_jahr", "render.py"))
Q = importlib.util.module_from_spec(_spec)   # weltall quiz: scenes, cards, countdown, events
_spec.loader.exec_module(Q)
from longlib import (W, H, SS, NAVY, YELLOW, WHITE, GREEN, RED, BLUE, ORANGE, PURPLE, FONT_XB,  # noqa: E402
                     back_out, ease_io, ease_out, prog, paste_c, rrect, text, wt)

QS = [
    dict(q="Wie viele Herzen hat ein Oktopus?", opts=["1", "3", "8"], right=1, ow=["Eins", "drei", "acht"],
         facts=[("3 HERZEN", "drei"), ("BLAUES BLUT", "blau"), ("KUPFER STATT EISEN", "Kupfer")]),
    dict(q="Welche Farbe hat die Haut unter dem Fell eines Eisbären?", opts=["schwarz", "weiß", "rosa"], right=0,
         ow=["Schwarz", "weiß", "rosa"],
         facts=[("HAUT: SCHWARZ", "schwarz"), ("FELL: DURCHSICHTIG", "durchsichtig"), ("NASE AUCH SCHWARZ", "Nase")]),
    dict(q="Warum sind Flamingos pink?", opts=["wegen der\nSonne", "wegen ihres\nEssens", "schon so\ngeboren"],
         right=1, ow=["Sonne", "Essens", "geboren"],
         facts=[("CAROTINOIDE IM FUTTER", "Carotinoide"), ("KÜKEN SIND GRAU", "Küken"),
                ("OHNE FUTTER: BLASS", "blass")]),
    dict(q="Wie lange schläft ein Koala am Tag?", opts=["8 Std.", "12 Std.", "bis zu\n22 Std."], right=2,
         ow=["8", "12", "bis"],
         facts=[("BIS ZU 22 H SCHLAF", "22"), ("FAST NUR EUKALYPTUS", "Eukalyptusblätter"),
                ("KAUM ENERGIE", "Energie")]),
    dict(q="Wie viele Augen hat eine Honigbiene?", opts=["2", "5", "8"], right=1, ow=["Zwei", "fünf", "acht"],
         facts=[("2 FACETTENAUGEN", "Facettenaugen"), ("3 PUNKTAUGEN", "Punktaugen"),
                ("HELFEN BEI ORIENTIERUNG", "Orientierung")]),
    dict(q="Welche Form hat das Häufchen eines Wombats?", opts=["würfel-\nförmig", "rund", "flach"], right=0,
         ow=["Würfelförmig", "rund", "flach"],
         facts=[("WÜRFEL-KACKE!", "würfelförmig"), ("FORM ENTSTEHT IM DARM", "Darm"),
                ("IG-NOBELPREIS 2019", "Ig-Nobelpreis")]),
    dict(q="Wie lange kann ein Faultier unter Wasser die Luft anhalten?",
         opts=["1 Min.", "10 Min.", "bis zu\n40 Min."], right=2, ow=["1", "10", "bis"],
         facts=[("BIS ZU 40 MINUTEN", "40"), ("HERZSCHLAG LANGSAMER", "Herzschlag"), ("GUTE SCHWIMMER", "Schwimmer")]),
]
TOPICS = ["OKTOPUS", "EISBÄR", "FLAMINGO", "KOALA", "HONIGBIENE", "WOMBAT", "FAULTIER"]
ap, tw, chip = Q.ap, Q.tw, Q.chip
_c = {}


# ------------------------------------------------------------------ sprites
def octopus(r, gt, col=(235, 95, 120)):
    s = SS(4.2 * r, 3.6 * r)
    cx, cy = 2.1 * r, 1.2 * r
    for k in range(8):
        x0 = cx - 0.85 * r + k * 0.243 * r
        pts, ws = [], []
        for j in range(12):
            u = j / 11
            x = x0 + (x0 - cx) * 1.4 * u + 0.25 * r * math.sin(gt * 2.4 + k + u * 5) * u
            y = cy + 0.7 * r + 1.6 * r * u
            pts.append((x, y))
            ws.append(0.2 * r * (1 - 0.8 * u))
        s.thick(pts, ws, col + (255,))
    s.ell(cx, cy, 0.95 * r, 1.05 * r, col + (255,))
    s.ell(cx - 0.3 * r, cy - 0.35 * r, 0.22 * r, 0.16 * r, (255, 170, 190, 255))
    for k in (-1, 1):
        s.ell(cx + k * 0.38 * r, cy + 0.35 * r, 0.2 * r, 0.22 * r, WHITE + (255,))
        s.ell(cx + k * 0.38 * r, cy + 0.38 * r, 0.09 * r, 0.12 * r, NAVY + (255,))
    return s.img()


def polar_bear(h):
    k = ("bear", h)
    if k in _c:
        return _c[k]
    w = h * 1.7
    s = SS(w, h)
    c = (245, 248, 255, 255)
    s.ell(w * 0.48, h * 0.5, w * 0.36, h * 0.3, c)
    for x in (0.25, 0.38, 0.6, 0.72):
        s.rect(w * x - w * 0.05, h * 0.55, w * x + w * 0.05, h * 0.97, w * 0.04, c)
    s.ell(w * 0.82, h * 0.38, w * 0.15, h * 0.17, c)
    s.ell(w * 0.95, h * 0.42, w * 0.06, h * 0.08, c)
    s.ell(w * 0.77, h * 0.22, w * 0.04, h * 0.05, c)
    s.ell(w * 0.99, h * 0.4, w * 0.03, h * 0.035, (20, 20, 30, 255))
    s.ell(w * 0.86, h * 0.32, w * 0.014, h * 0.02, (20, 20, 30, 255))
    _c[k] = s.img()
    return _c[k]


def flamingo(h, pink):
    k = ("fl", h, round(pink, 2))
    if k in _c:
        return _c[k]
    g = (170, 170, 180)
    p = (255, 120, 170)
    col = tuple(int(a + (b - a) * pink) for a, b in zip(g, p)) + (255,)
    w = h * 0.7
    s = SS(w, h)
    leg = (230, 110, 140, 255) if pink > 0.5 else (140, 140, 150, 255)
    s.line([(w * 0.45, h * 0.55), (w * 0.45, h * 0.98)], leg, h * 0.02)
    s.line([(w * 0.52, h * 0.55), (w * 0.6, h * 0.75), (w * 0.48, h * 0.78)], leg, h * 0.02)
    s.ell(w * 0.5, h * 0.48, w * 0.32, h * 0.12, col)
    s.thick([(w * 0.72, h * 0.45), (w * 0.82, h * 0.3), (w * 0.7, h * 0.18), (w * 0.75, h * 0.08)],
            [h * 0.06, h * 0.05, h * 0.045, h * 0.04], col)
    s.ell(w * 0.78, h * 0.07, w * 0.08, h * 0.05, col)
    s.poly([(w * 0.84, h * 0.05), (w * 0.98, h * 0.1), (w * 0.86, h * 0.12)], (40, 40, 50, 255))
    s.ell(w * 0.79, h * 0.06, w * 0.015, h * 0.012, (20, 20, 30, 255))
    _c[k] = s.img()
    return _c[k]


def koala(h, sleep=True):
    k = ("ko", h, sleep)
    if k in _c:
        return _c[k]
    s = SS(h * 1.1, h)
    g, dg = (170, 170, 185, 255), (120, 120, 135, 255)
    cx = h * 0.55
    s.ell(cx, h * 0.68, h * 0.34, h * 0.3, g)
    for kk in (-1, 1):
        s.ell(cx + kk * h * 0.3, h * 0.2, h * 0.17, h * 0.15, g)
        s.ell(cx + kk * h * 0.3, h * 0.2, h * 0.1, h * 0.09, (235, 225, 230, 255))
    s.ell(cx, h * 0.32, h * 0.3, h * 0.25, g)
    s.ell(cx, h * 0.38, h * 0.08, h * 0.1, (50, 45, 55, 255))
    for kk in (-1, 1):
        if sleep:
            s.line([(cx + kk * h * 0.15 - h * 0.05, h * 0.28), (cx + kk * h * 0.15 + h * 0.05, h * 0.28)], dg,
                   h * 0.018)
        else:
            s.ell(cx + kk * h * 0.15, h * 0.27, h * 0.03, h * 0.03, (30, 30, 40, 255))
    _c[k] = s.img()
    return _c[k]


def leaf(img, cx, cy, s, ang):
    sp = SS(80 * s, 200 * s)
    sp.ell(40 * s, 100 * s, 30 * s, 90 * s, (90, 170, 110, 255))
    sp.line([(40 * s, 15 * s), (40 * s, 190 * s)], (60, 130, 80, 255), 4 * s)
    paste_c(img, sp.img().rotate(ang, resample=Image.BICUBIC, expand=True), cx, cy)


def wombat(h):
    k = ("wo", h)
    if k in _c:
        return _c[k]
    w = h * 1.6
    s = SS(w, h)
    c = (140, 105, 80, 255)
    s.ell(w * 0.48, h * 0.55, w * 0.4, h * 0.38, c)
    for x in (0.25, 0.68):
        s.rect(w * x - w * 0.06, h * 0.7, w * x + w * 0.06, h * 0.98, w * 0.04, c)
    s.ell(w * 0.84, h * 0.45, w * 0.15, h * 0.2, c)
    s.ell(w * 0.92, h * 0.5, w * 0.07, h * 0.08, (70, 50, 40, 255))
    s.ell(w * 0.82, h * 0.25, w * 0.04, h * 0.06, c)
    s.ell(w * 0.86, h * 0.4, w * 0.018, h * 0.025, (20, 15, 15, 255))
    _c[k] = s.img()
    return _c[k]


def sloth(h, arm=0.0):
    s = SS(h * 1.2, h)
    c, f = (165, 135, 100, 255), (235, 215, 180, 255)
    cx = h * 0.6
    s.ell(cx, h * 0.6, h * 0.32, h * 0.3, c)
    for kk in (-1, 1):
        a = kk * (0.6 + 0.5 * arm * kk)
        s.thick([(cx + kk * h * 0.25, h * 0.5), (cx + kk * h * 0.5, h * 0.5 - h * 0.3 * math.sin(a))],
                [h * 0.1, h * 0.08], c)
    s.ell(cx, h * 0.3, h * 0.23, h * 0.2, c)
    s.ell(cx, h * 0.32, h * 0.17, h * 0.14, f)
    for kk in (-1, 1):
        s.ell(cx + kk * h * 0.08, h * 0.3, h * 0.06, h * 0.035, (80, 55, 40, 255))
        s.ell(cx + kk * h * 0.08, h * 0.3, h * 0.018, h * 0.018, (20, 15, 15, 255))
    s.ell(cx, h * 0.37, h * 0.03, h * 0.02, (60, 40, 30, 255))
    s.line([(cx - h * 0.05, h * 0.41), (cx, h * 0.43), (cx + h * 0.05, h * 0.41)], (60, 40, 30, 255), h * 0.012)
    return s.img()


def bee_head(img, cx, cy, r, glow_c=0.0, glow_o=0.0, gt=0.0):
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r * 0.9, cx + r, cy + r * 1.05), fill=(60, 45, 30))
    for kk in (-1, 1):
        ex = cx + kk * r * 0.72
        er = r * 0.42
        col = (255, 200, 60) if glow_c > 0.5 and int(gt * 4) % 2 == 0 else (40, 30, 25)
        d.ellipse((ex - er * 0.7, cy - er * 1.3, ex + er * 0.7, cy + er * 1.3), fill=col, outline=YELLOW if glow_c else (90, 70, 50), width=6)
        for i in range(-3, 4):
            for j in range(-5, 6):
                hx = ex + i * er * 0.2 + (j % 2) * er * 0.1
                hy = cy + j * er * 0.22
                if ((hx - ex) / (er * 0.65)) ** 2 + ((hy - cy) / (er * 1.25)) ** 2 < 1:
                    d.regular_polygon((hx, hy, er * 0.09), 6, fill=(90, 80, 70) if not glow_c else (255, 230, 120))
    for k in range(3):
        a = -math.pi / 2 + (k - 1) * 0.5
        ox, oy = cx + r * 0.35 * math.cos(a), cy - r * 0.45 + r * 0.25 * (1 + math.sin(a))
        rr = r * 0.09
        col = YELLOW if glow_o > 0.5 else (20, 15, 15)
        d.ellipse((ox - rr, oy - rr, ox + rr, oy + rr), fill=col, outline=WHITE if glow_o else (90, 70, 50), width=4)
    for kk in (-1, 1):
        d.line((cx + kk * r * 0.15, cy - r * 0.8, cx + kk * r * 0.55, cy - r * 1.5), fill=(40, 30, 25), width=10)
        d.ellipse((cx + kk * r * 0.55 - 14, cy - r * 1.5 - 14, cx + kk * r * 0.55 + 14, cy - r * 1.5 + 14),
                  fill=(40, 30, 25))
    d.rectangle((cx - r * 0.2, cy + r * 0.75, cx + r * 0.2, cy + r * 1.05), fill=(255, 200, 40))


# ------------------------------------------------------------------ illustrations
def ill_octopus(img, seg, t, gt, a):
    paste_c(img, octopus(170, gt), 1220, 600, a)
    beat = 1 + 0.18 * max(0, math.sin(gt * 7)) ** 8
    p3 = ap(seg, t, "drei")
    if p3 > 0.02:
        for x, y, s_ in ((1060, 640, 70), (1380, 640, 70), (1220, 330, 95)):
            paste_c(img, L.E.heart_sprite(s_ * beat * p3), x, y)
    pg = ap(seg, t, "Kiemen")
    if pg > 0.02:
        Q.L.pill(img, "2 KIEMEN-HERZEN", 1220, 250, WHITE, pg, size=30)
    pd = ap(seg, t, "dritte")
    if pd > 0.02:
        Q.L.pill(img, "1 KÖRPER-HERZ", 1640, 420, YELLOW, pd, size=30)
    pb = ap(seg, t, "blau", d=0.6)
    if pb > 0.02:
        d = ImageDraw.Draw(img)
        rr = random.Random(2)
        for k in range(10):
            ph = (gt * 0.6 + rr.random()) % 1
            x = 1560 + 220 * ph
            y = 620 + 40 * math.sin(ph * 6 + k)
            d.ellipse((x - 16, y - 22, x + 16, y + 16), fill=(70, 120, 255))
        Q.L.pill(img, "BLAUES BLUT", 1680, 760, BLUE, pb, size=32)
    pk = ap(seg, t, "Kupfer")
    if pk > 0.02:
        text(img, "Cu", 90 * back_out(prog(t, tw(seg, "Kupfer") - 0.1, 0.4)), 1720, 330, fill=(230, 140, 70), stroke=8,
             sfill=NAVY)


def ill_bear(img, seg, t, gt, a):
    zoom = ap(seg, t, "durchsichtig", d=0.6)
    d = ImageDraw.Draw(img)
    d.rectangle((640, 760, 1880, 900), fill=(230, 240, 255))
    paste_c(img, polar_bear(380), 1050 - 120 * zoom, 790, a, anchor="b")
    if zoom > 0.02:
        cx, cy, r = 1560, 470, int(250 * zoom)
        lay = Image.new("RGBA", (2 * r, 2 * r), (20, 20, 30, 255))
        dl = ImageDraw.Draw(lay)
        dl.rectangle((0, int(1.35 * r), 2 * r, 2 * r), fill=(25, 25, 30))
        for i in range(9):
            x = 20 + i * (2 * r - 40) / 8
            dl.line((x, 1.35 * r, x + 30 * math.sin(i), 0.15 * r), fill=(220, 235, 255, 120), width=max(2, r // 14))
            dl.line((x + 3, 1.35 * r, x + 3 + 30 * math.sin(i), 0.15 * r), fill=(255, 255, 255, 220), width=2)
        pl = ap(seg, t, "Licht", d=0.5)
        if pl > 0.02:
            for k in range(6):
                y0 = 0.2 * r + k * 0.18 * r
                dl.line((0, y0, 0.8 * r, y0 + 0.2 * r), fill=YELLOW, width=5)
                dl.line((0.8 * r, y0 + 0.2 * r, 1.4 * r, y0 - 0.1 * r), fill=YELLOW, width=5)
        m = Image.new("L", lay.size, 0)
        ImageDraw.Draw(m).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
        img.paste(lay, (cx - r, cy - r), m)
        ImageDraw.Draw(img).ellipse((cx - r, cy - r, cx + r, cy + r), outline=WHITE, width=8)
        text(img, "FELL (VERGRÖSSERT)", 30, cx, cy + r + 36, fill=WHITE, path=FONT_XB, stroke=4, sfill=NAVY,
             alpha=zoom)
        text(img, "SCHWARZE HAUT", 26, cx, cy + 0.6 * r, fill=(200, 200, 220), path=FONT_XB, alpha=zoom)
    pn = ap(seg, t, "Nase")
    if pn > 0.02:
        nx = 1050 - 120 * zoom + 380 * 1.7 * 0.49
        ny = 790 - 380 + 380 * 0.4
        ImageDraw.Draw(img).ellipse((nx - 50, ny - 50, nx + 50, ny + 50), outline=RED, width=8)


def ill_flamingo(img, seg, t, gt, a):
    pink = 0.3 + 0.7 * ease_io(prog(t, tw(seg, "Algen") - 0.3, 2.5)) * (1 - 0.6 * ap(seg, t, "blass", d=1.0))
    paste_c(img, flamingo(560, round(pink * 20) / 20), 1000, 880, a, anchor="b")
    d = ImageDraw.Draw(img)
    d.rectangle((640, 840, 1880, 900), fill=(90, 160, 220))
    pf = ap(seg, t, "Algen")
    if pf > 0.02:
        rr = random.Random(4)
        for k in range(16):
            ph = (gt * 0.5 + rr.random()) % 1
            x = 1700 - 520 * ph
            y = 820 - 250 * ph * ph
            if k % 2:
                d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(80, 200, 110))
            else:
                d.arc((x - 18, y - 12, x + 18, y + 12), 200, 340, fill=(255, 140, 80), width=8)
        Q.L.pill(img, "ALGEN + KREBSE", 1560, 300, ORANGE, pf, size=32)
    pk = ap(seg, t, "Küken")
    if pk > 0.02:
        paste_c(img, flamingo(220, 0.0), 1450, 840, pk, anchor="b")
        text(img, "KÜKEN: GRAU", 30, 1450, 560, fill=WHITE, path=FONT_XB, stroke=4, sfill=NAVY, alpha=pk)


def ill_koala(img, seg, t, gt, a):
    d = ImageDraw.Draw(img)
    d.line((660, 640, 1300, 560), fill=(110, 80, 60), width=34)
    paste_c(img, koala(300), 980, 590, a, anchor="b")
    for j in range(3):
        ph = (gt * 0.5 + j / 3) % 1
        text(img, "Z", 40 + 30 * ph, 1080 + ph * 120, 300 - ph * 140, fill=WHITE, alpha=(1 - ph) * a, stroke=4,
             sfill=NAVY)
    # 24 h ring
    p22 = ease_io(prog(t, tw(seg, "22") - 0.3, 1.3))
    cx, cy, r = 1580, 430, 170
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(15, 20, 40), outline=WHITE, width=6)
    if p22 > 0:
        d.pieslice((cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10), -90, -90 + 360 * 22 / 24 * p22,
                   fill=(110, 90, 220))
    text(img, f"{int(round(22 * p22))} h", 70, cx, cy, fill=WHITE, stroke=6, sfill=NAVY)
    text(img, "VON 24 STUNDEN", 28, cx, cy + r + 36, fill=WHITE, path=FONT_XB, stroke=4, sfill=NAVY)
    pe = ap(seg, t, "Eukalyptusblätter")
    if pe > 0.02:
        for k, (x, y, an) in enumerate(((760, 520, 20), (840, 500, -15), (1200, 470, 30), (1260, 510, -25))):
            leaf(img, x, y - 30 * (1 - pe), pe, an + 5 * math.sin(gt * 2 + k))
    pen = ap(seg, t, "Energie")
    if pen > 0.02:
        bx, by = 1580, 780
        d.rounded_rectangle((bx - 100, by - 45, bx + 100, by + 45), 12, outline=WHITE, width=6)
        d.rectangle((bx + 102, by - 16, bx + 114, by + 16), fill=WHITE)
        if int(gt * 3) % 2 == 0:
            d.rectangle((bx - 88, by - 33, bx - 66, by + 33), fill=RED)
        text(img, "WENIG ENERGIE", 28, bx, by + 80, fill=RED, path=FONT_XB, stroke=4, sfill=WHITE, alpha=pen)


def ill_bee(img, seg, t, gt, a):
    pc, po = ap(seg, t, "Facettenaugen"), ap(seg, t, "Punktaugen")
    bee_head(img, 1240, 600, 210, glow_c=pc if po < 0.5 else 0.0, glow_o=po, gt=gt)
    if pc > 0.02:
        for kk in (-1, 1):
            text(img, "FACETTENAUGE", 28, 1240 + kk * 330, 840, fill=YELLOW, path=FONT_XB, stroke=4, sfill=NAVY,
                 alpha=pc)
    if po > 0.02:
        ImageDraw.Draw(img).line((1300, 470, 1520, 330), fill=YELLOW, width=5)
        text(img, "3 PUNKTAUGEN", 34, 1600, 310, fill=YELLOW, path=FONT_XB, stroke=4, sfill=NAVY, alpha=po)
    por = ap(seg, t, "Orientierung")
    if por > 0.02:
        d = ImageDraw.Draw(img)
        cx, cy = 1720, 420
        d.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), fill=WHITE, outline=NAVY, width=6)
        an = gt * 1.5
        d.polygon([(cx + 55 * math.sin(an), cy - 55 * math.cos(an)), (cx + 14 * math.cos(an), cy + 14 * math.sin(an)),
                   (cx - 14 * math.cos(an), cy - 14 * math.sin(an))], fill=RED)


def ill_wombat(img, seg, t, gt, a):
    paste_c(img, wombat(300), 900, 820, a, anchor="b")
    d = ImageDraw.Draw(img)
    pw = ap(seg, t, "würfelförmig")
    if pw > 0.02:
        for k in range(4):
            q = ease_out(prog(t, tw(seg, "würfelförmig") + 0.15 * k, 0.3))
            if q <= 0:
                continue
            x, y = 640 + (k % 2) * 70, 800 - (k // 2) * 66
            d.rectangle((x - 30 * q, y - 30 * q, x + 30 * q, y + 30 * q), fill=(110, 80, 55), outline=(70, 50, 35),
                        width=4)
    pdm = ap(seg, t, "Darm", d=0.5)
    if pdm > 0.02:
        x0, x1, y = 1250, 1820, 420
        for i in range(8):
            xs = x0 + i * (x1 - x0) / 8
            stiff = i % 2 == 0 and ap(seg, t, "steifer") > 0.02
            d.rounded_rectangle((xs, y - 70, xs + (x1 - x0) / 8 - 6, y + 70), 30,
                                fill=(200, 110, 120) if stiff else (255, 170, 180))
        text(img, "DARM", 32, (x0 + x1) / 2, y - 110, fill=WHITE, path=FONT_XB, stroke=4, sfill=NAVY, alpha=pdm)
        ps = ap(seg, t, "steifer")
        if ps > 0.02:
            text(img, "steif / dehnbar", 28, (x0 + x1) / 2, y + 110, fill=YELLOW, path=FONT_XB, stroke=4, sfill=NAVY,
                 alpha=ps)
            cube_x = x0 + ((gt * 160) % (x1 - x0))
            r = 40 * (0.6 + 0.4 * min(1, (cube_x - x0) / (x1 - x0) * 2))
            d.rounded_rectangle((cube_x - r, y - r, cube_x + r, y + r), int(40 - r * 0.8) + 4, fill=(110, 80, 55))
    pi = pop_s(seg, t, "Ig-Nobelpreis")
    if pi > 0.02:
        cx, cy = 1540, 700
        d.polygon([(cx - 70 * pi, cy - 90 * pi), (cx + 70 * pi, cy - 90 * pi), (cx + 40 * pi, cy + 10 * pi),
                   (cx - 40 * pi, cy + 10 * pi)], fill=YELLOW)
        d.rectangle((cx - 12 * pi, cy + 10 * pi, cx + 12 * pi, cy + 60 * pi), fill=YELLOW)
        d.rectangle((cx - 60 * pi, cy + 60 * pi, cx + 60 * pi, cy + 85 * pi), fill=(200, 160, 40))
        text(img, "IG-NOBELPREIS 2019", 30, cx, cy + 130, fill=YELLOW, path=FONT_XB, stroke=4, sfill=NAVY,
             alpha=min(1, pi))


def pop_s(seg, t, w):
    try:
        return back_out(prog(t, wt(seg, w) - 0.1, 0.45))
    except KeyError:
        return 0.0


def ill_sloth(img, seg, t, gt, a):
    rrect(img, (660, 220, 1860, 880), 40, (40, 110, 190, int(230 * a)))
    d = ImageDraw.Draw(img)
    for k in range(3):
        y = 250 + k * 14
        d.line([(x, y + 8 * math.sin(x / 40 + gt * 2 + k)) for x in range(680, 1841, 20)], fill=(150, 210, 255), width=4)
    sw = ap(seg, t, "Schwimmer")
    paste_c(img, sloth(300, arm=math.sin(gt * 3) if sw > 0.02 else 0.0), 1000 + 80 * math.sin(gt * 0.5) * sw, 600, a)
    rr = random.Random(int(gt * 2))
    for k in range(4):
        x = 1000 + rr.uniform(-40, 40)
        y = 420 - ((gt * 80 + k * 50) % 180)
        d.ellipse((x - 10, y - 10, x + 10, y + 10), outline=WHITE, width=3)
    p40 = ease_io(prog(t, tw(seg, "40") - 0.3, 1.5))
    cx, cy, r = 1560, 470, 160
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(15, 20, 40), outline=WHITE, width=6)
    if p40 > 0:
        d.pieslice((cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10), -90, -90 + 360 * 40 / 60 * p40,
                   fill=(80, 215, 115))
    text(img, f"{int(round(40 * p40))} min", 64, cx, cy, fill=WHITE, stroke=6, sfill=NAVY)
    text(img, "LUFT ANHALTEN", 28, cx, cy + r + 36, fill=WHITE, path=FONT_XB, stroke=4, sfill=NAVY)
    ph = ap(seg, t, "Herzschlag")
    if ph > 0.02:
        beat = 1 + 0.2 * max(0, math.sin(gt * 2.2)) ** 10
        paste_c(img, L.E.heart_sprite(90 * beat * ph), 1560, 770)
        text(img, "LANGSAMER", 26, 1670, 770, fill=WHITE, path=FONT_XB, stroke=3, sfill=NAVY, alpha=ph, anchor="lm")


ILL = [ill_octopus, ill_bear, ill_flamingo, ill_koala, ill_bee, ill_wombat, ill_sloth]


# ------------------------------------------------------------------ intro / frage / outro
def sc_intro(img, seg, t, gt):
    L.brand(img, W / 2, 90, gt, back_out(prog(t, 0.0, 0.5)))
    a = ease_out(prog(t, 0.3, 0.5))
    text(img, "Wie gut kennst du Tiere?", 92, W / 2, 240, fill=YELLOW, alpha=a, stroke=10, sfill=NAVY, rotate=-2)
    items = [(octopus(90, gt), 330, 720), (polar_bear(170), 720, 800), (flamingo(300, 1.0), 1110, 850),
             (koala(190, sleep=False), 1440, 800), (wombat(140), 1700, 850)]
    for k, (sp, x, y) in enumerate(items):
        p = back_out(prog(t, 0.4 + 0.25 * k, 0.5))
        if p > 0.03:
            sp2 = sp.resize((max(1, int(sp.width * p)), max(1, int(sp.height * p))), Image.BILINEAR)
            paste_c(img, sp2, x, y + 12 * math.sin(gt * 2 + k), anchor="b")
    p7 = prog(t, tw(seg, "7") - 0.1, 0.5)
    if p7 > 0:
        L.stamp(img, "7 FRAGEN", t, tw(seg, "7") - 0.1, W / 2 - 200, 420, size=100, rot=-6)
        L.burst(img, W / 2 - 200, 420, t, tw(seg, "7"), rad=230)
    pz = ap(seg, t, "Punkte")
    if pz > 0.02:
        rrect(img, (1420, 350, 1780, 490), 36, (15, 20, 40, int(230 * pz)), outline=YELLOW + (255,),
              width=5)
        text(img, "DEINE PUNKTE", 30, 1600, 385, fill=YELLOW, path=FONT_XB, alpha=pz)
        text(img, "0 / 7", 64, 1600, 445, alpha=pz)


def sc_frage(img, seg, t, gt):
    qi = seg["qi"]
    L.top_bar(img, gt, qi + 1, ease_out(prog(t, 0, 0.3)))
    p = back_out(prog(t, 0.05, 0.5))
    x = W / 2 + (1 - ease_out(prog(t, 0.0, 0.45))) * 900
    lab = "LETZTE FRAGE" if qi == 6 else f"FRAGE {qi + 1}"
    text(img, lab, 190 * max(0.05, p), x, 470, fill=YELLOW, stroke=14, sfill=NAVY, rotate=-4)
    q = 1 + 0.15 * math.sin(gt * 7)
    text(img, "?", 150 * q * max(0.05, p), x + 520 * p + (90 if qi == 6 else 0), 380, fill=(255, 80, 90), stroke=10,
         sfill=NAVY, rotate=14)
    text(img, TOPICS[qi], 52, W / 2, 660, fill=WHITE, path=FONT_XB, stroke=6, sfill=NAVY,
         alpha=ease_out(prog(t, 0.3, 0.4)))


def sc_outro(img, seg, t, gt):
    Q.sc_outro(img, seg, t, gt)


Q.QS[:] = QS
Q.ILL[:] = ILL
Q.RANKS[:] = [("0 – 2", "Tier-Anfänger", WHITE), ("3 – 5", "Tier-Kenner", BLUE), ("6 – 7", "Tier-Profi", YELLOW)]
Q.astronaut = lambda h, arm=0.0, leg=0.0, key=None: koala(int(h * 0.75), sleep=False)
Q.DRAW.update(intro=sc_intro, frage=sc_frage)

L.setup(here=HERE, out="rate_mal_7_tier_fakten.mp4", plan=Q.plan, draw=Q.draw, events=Q.events)

if __name__ == "__main__":
    L.main()

#!/usr/bin/env python3
"""Rate mal: Was passiert, wenn du 1 Woche nicht schläfst? – Erklärvideo im Querformat (~5 Min, 4K-fähig)."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import longlib as L  # noqa: E402
from longlib import (W, H, SS, NAVY, YELLOW, WHITE, GREEN, RED, BLUE, ORANGE, PURPLE, FONT_XB,  # noqa: E402
                     back_out, ease_io, ease_out, prog, paste_c, rrect, text, wt)

SKIN = (255, 200, 160)
DARK = (15, 20, 40)

# ------------------------------------------------------------------ plan
# key, audio/None, label, hours (h0,h1), battery (b0,b1)
SP = dict(pre=0.25, post=0.9)
plan = [
    dict(key="s00", audio="s00", kind="speech", label=None, **SP),
    dict(key="cw", kind="card", dur=1.8, title="WARUM SCHLAFEN?", sub="DIE GRUNDLAGEN", label="GRUNDLAGEN"),
    dict(key="s01", audio="s01", kind="speech", label="GRUNDLAGEN", **SP),
    dict(key="s02", audio="s02", kind="speech", label="GRUNDLAGEN", **SP),
    dict(key="c1", kind="card", dur=2.4, title="TAG 1", sub="DER COUNTDOWN STARTET", day=1, label="TAG 1", hh=(0, 0),
         bb=(100, 100)),
    dict(key="s03", audio="s03", kind="speech", label="TAG 1", hh=(0, 17), bb=(100, 85), **SP),
    dict(key="s04", audio="s04", kind="speech", label="TAG 1", hh=(17, 24), bb=(85, 70), **SP),
    dict(key="s06", audio="s06", kind="speech", label="TAG 2", hh=(24, 27), bb=(70, 74), **SP),
    dict(key="c2", kind="card", dur=2.4, title="TAG 2", sub="30 STUNDEN WACH", day=2, label="TAG 2", hh=(27, 30),
         bb=(74, 66)),
    dict(key="s05", audio="s05", kind="speech", label="TAG 2", hh=(30, 33), bb=(66, 60), **SP),
    dict(key="s07", audio="s07", kind="speech", label="TAG 2", hh=(33, 36), bb=(60, 55), **SP),
    dict(key="s08", audio="s08", kind="speech", label="TAG 2", hh=(36, 38), bb=(55, 50), **SP),
    dict(key="c3", kind="card", dur=2.4, title="TAG 3", sub="48 STUNDEN WACH", day=3, label="TAG 3", hh=(38, 48),
         bb=(50, 40)),
    dict(key="s09", audio="s09", kind="speech", label="TAG 3", hh=(48, 56), bb=(40, 34), **SP),
    dict(key="c4", kind="card", dur=2.4, title="TAG 4", sub="72 STUNDEN WACH", day=4, label="TAG 4", hh=(56, 72),
         bb=(34, 28)),
    dict(key="s10", audio="s10", kind="speech", label="TAG 4", hh=(72, 78), bb=(28, 25), **SP),
    dict(key="s11", audio="s11", kind="speech", label="TAG 4", hh=(78, 84), bb=(25, 22), **SP),
    dict(key="c5", kind="card", dur=2.4, title="TAG 5 + 6", sub="96 STUNDEN WACH", day=5, label="TAG 5–6",
         hh=(84, 96), bb=(22, 15)),
    dict(key="s12", audio="s12", kind="speech", label="TAG 5–6", hh=(96, 140), bb=(15, 1), **SP),
    dict(key="c7", kind="card", dur=2.4, title="TAG 7", sub="168 STUNDEN WACH", day=7, label="TAG 7", hh=(140, 168),
         bb=(1, 1)),
    dict(key="s13", audio="s13", kind="speech", label="TAG 7", hh=(168, 168), bb=(1, 1), **SP),
    dict(key="cr", kind="card", dur=1.8, title="ENDLICH SCHLAF", sub="DIE ERHOLUNG", label="ERHOLUNG"),
    dict(key="s14", audio="s14", kind="speech", label="ERHOLUNG", bb=(1, 100), **SP),
    dict(key="s15", audio="s15", kind="speech", label="ERHOLUNG", bb=(100, 100), **SP),
    dict(key="s16", audio="s16", kind="speech", label=None, pre=0.3, post=2.6),
]

_cache = {}


def ap(seg, t, word, n=1, d=0.35, off=-0.1):
    try:
        return ease_out(prog(t, wt(seg, word, n) + off, d))
    except KeyError:
        return 0.0


def tw(seg, word, n=1):
    return wt(seg, word, n)


def lerp(a, b, k):
    return a + (b - a) * k


def chip(img, s, cx, cy, col, a, size=34):
    L.pill(img, s, cx, cy, col, a, size=size)


def label(img, s, cx, cy, a=1.0, col=WHITE, size=32):
    text(img, s, size, cx, cy, fill=col, path=FONT_XB, stroke=4, sfill=NAVY, alpha=a)


def pop_scale(seg, t, word, n=1):
    try:
        return back_out(prog(t, wt(seg, word, n) - 0.1, 0.45))
    except KeyError:
        return 0.0


def scaled(sp, s):
    if s <= 0.02:
        return None
    return sp.resize((max(1, int(sp.width * s)), max(1, int(sp.height * s))), Image.BILINEAR)


# ------------------------------------------------------------------ sprites
def brain_sprite(w, front_col=None, amy=0.0):
    k = ("brain", int(w), front_col, round(amy, 2))
    if k in _cache:
        return _cache[k]
    h = w * 0.72
    s = SS(w + 20, h + 20)
    pink, dk = (255, 160, 190, 255), (215, 110, 150, 255)
    for cx, cy, rx, ry in ((0.30, 0.42, 0.26, 0.30), (0.55, 0.32, 0.30, 0.30), (0.75, 0.48, 0.24, 0.30),
                           (0.50, 0.58, 0.40, 0.28)):
        s.ell(10 + cx * w, 10 + cy * h, rx * w, ry * h, pink)
    s.ell(10 + 0.78 * w, 10 + 0.86 * h, 0.16 * w, 0.10 * h, (240, 140, 170, 255))  # cerebellum
    s.rect(10 + 0.58 * w, 10 + 0.78 * h, 10 + 0.68 * w, 10 + 1.0 * h, 0.04 * w, (230, 130, 160, 255))  # stem
    if front_col:
        s.ell(10 + 0.24 * w, 10 + 0.42 * h, 0.2 * w, 0.24 * h, front_col + (170,))
    rr = random.Random(3)
    for _ in range(14):
        x0, y0 = rr.uniform(0.15, 0.85) * w + 10, rr.uniform(0.15, 0.75) * h + 10
        pts = [(x0 + j * 0.04 * w, y0 + 0.03 * h * math.sin(j * 1.7 + rr.random() * 3)) for j in range(4)]
        s.line(pts, dk, max(2, w * 0.012))
    if amy > 0:
        r = 0.06 * w * (1 + 0.6 * amy)
        s.ell(10 + 0.55 * w, 10 + 0.62 * h, r * 1.3, r, (235, 40, 60, 255))
    img = s.img()
    if len(_cache) > 300:
        _cache.clear()
    _cache[k] = img
    return img


def face(img, cx, cy, r, mood, a=1.0):
    col = {"angry": (255, 110, 90), "sad": (110, 170, 255), "tired": (255, 210, 150)}[mood]
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col, outline=NAVY, width=6)
    for k in (-1, 1):
        d.ellipse((cx + k * r * 0.35 - 10, cy - r * 0.15 - 10, cx + k * r * 0.35 + 10, cy - r * 0.15 + 10), fill=NAVY)
    if mood == "angry":
        for k in (-1, 1):
            d.line((cx + k * r * 0.15, cy - r * 0.35, cx + k * r * 0.55, cy - r * 0.5), fill=NAVY, width=8)
        d.arc((cx - r * 0.4, cy + r * 0.25, cx + r * 0.4, cy + r * 0.75), 200, 340, fill=NAVY, width=8)
    elif mood == "sad":
        d.arc((cx - r * 0.4, cy + r * 0.25, cx + r * 0.4, cy + r * 0.75), 200, 340, fill=NAVY, width=8)
        d.ellipse((cx + r * 0.3, cy + r * 0.05, cx + r * 0.45, cy + r * 0.3), fill=(200, 240, 255))
    else:
        d.line((cx - r * 0.3, cy + r * 0.45, cx + r * 0.3, cy + r * 0.45), fill=NAVY, width=8)


def bed(img, cx, cy, eyes_open=True, gt=0.0, a=1.0):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((cx - 330, cy - 60, cx + 330, cy + 40), 18, fill=(150, 95, 60))
    d.rounded_rectangle((cx - 360, cy - 200, cx - 320, cy + 110), 12, fill=(130, 80, 50))
    d.rounded_rectangle((cx + 320, cy - 120, cx + 360, cy + 110), 12, fill=(130, 80, 50))
    d.rounded_rectangle((cx - 320, cy - 110, cx + 320, cy - 40), 30, fill=(245, 245, 255))
    d.rounded_rectangle((cx - 300, cy - 175, cx - 170, cy - 105), 30, fill=(255, 255, 255))
    d.ellipse((cx - 280, cy - 230, cx - 180, cy - 130), fill=SKIN)
    d.rounded_rectangle((cx - 190, cy - 160, cx + 320, cy - 70), 40, fill=(90, 120, 230))
    if eyes_open:
        for k in (0, 1):
            ex = cx - 255 + k * 42
            d.ellipse((ex - 11, cy - 197, ex + 11, cy - 175), fill=WHITE)
            d.ellipse((ex - 5, cy - 191, ex + 5, cy - 181), fill=NAVY)
    else:
        for k in (0, 1):
            ex = cx - 255 + k * 42
            d.arc((ex - 12, cy - 196, ex + 12, cy - 176), 20, 160, fill=NAVY, width=5)
        for j in range(3):
            ph = (gt * 0.5 + j / 3) % 1
            text(img, "Z", 40 + 30 * ph, cx - 150 + ph * 160, cy - 260 - ph * 180, fill=WHITE, alpha=1 - ph,
                 stroke=4, sfill=NAVY)


def clock(img, cx, cy, r, hours, a=1.0):
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE, outline=NAVY, width=10)
    for k in range(12):
        an = k / 12 * 2 * math.pi
        d.line((cx + 0.8 * r * math.sin(an), cy - 0.8 * r * math.cos(an), cx + 0.92 * r * math.sin(an),
                cy - 0.92 * r * math.cos(an)), fill=NAVY, width=6)
    an = (hours % 1) * 2 * math.pi
    d.line((cx, cy, cx + 0.75 * r * math.sin(an), cy - 0.75 * r * math.cos(an)), fill=RED, width=8)
    an2 = (hours % 12) / 12 * 2 * math.pi
    d.line((cx, cy, cx + 0.5 * r * math.sin(an2), cy - 0.5 * r * math.cos(an2)), fill=NAVY, width=14)
    d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=NAVY)


def battery(img, cx, cy, level, w=74, h=36, a=1.0, gt=0.0):
    d = ImageDraw.Draw(img)
    col = GREEN if level > 50 else (YELLOW if level > 20 else RED)
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 8, outline=WHITE, width=4)
    d.rectangle((cx + w / 2 + 2, cy - h / 5, cx + w / 2 + 8, cy + h / 5), fill=WHITE)
    if level < 5 and int(gt * 3) % 2 == 0:
        return
    fw = (w - 12) * max(0.04, level / 100)
    d.rectangle((cx - w / 2 + 6, cy - h / 2 + 6, cx - w / 2 + 6 + fw, cy + h / 2 - 6), fill=col)


def glass(img, cx, cy, fill, a=1.0):
    d = ImageDraw.Draw(img)
    top, bot, wt_, wb = cy - 200, cy + 200, 150, 115
    if fill > 0:
        y = bot - (bot - top - 30) * fill
        k = (y - top) / (bot - top)
        wy = wt_ + (wb - wt_) * k
        d.polygon([(cx - wy, y), (cx + wy, y), (cx + wb, bot), (cx - wb, bot)], fill=(255, 190, 40))
        d.ellipse((cx - wy, y - 24, cx + wy, y + 14), fill=(255, 250, 235))
    d.line([(cx - wt_, top), (cx - wb, bot), (cx + wb, bot), (cx + wt_, top)], fill=WHITE, width=8)
    d.arc((cx + wt_ - 20, cy - 100, cx + wt_ + 90, cy + 80), 270, 90, fill=WHITE, width=12)


def stage_bar(img, hl, a=1.0):
    """Waters et al. 2018: 24 h / 48 h / 72 h stages."""
    stages = [("ab 24 h: Wahrnehmung verzerrt", 0), ("ab 48 h: Halluzinationen", 1), ("ab 72 h: Wahn", 2)]
    x0, w = 240, 480
    for txt, i in stages:
        cx = x0 + i * w + w / 2 - 0
        on = i <= hl
        col = (YELLOW if i == hl else (255, 160, 120)) if on else (120, 120, 150)
        rrect(img, (cx - w / 2 + 8, 852, cx + w / 2 - 8, 912), 30, DARK + (int(220 * a),), outline=col + (255,),
              width=4)
        text(img, txt, 28, cx, 882, fill=col, path=FONT_XB, alpha=a)


def masked_panel(img, cx, cy, r, draw_fn):
    lay = Image.new("RGBA", (2 * r, 2 * r), DARK + (255,))
    draw_fn(lay, r)
    m = Image.new("L", lay.size, 0)
    ImageDraw.Draw(m).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
    img.paste(lay, (int(cx - r), int(cy - r)), m)
    ImageDraw.Draw(img).ellipse((cx - r, cy - r, cx + r, cy + r), outline=WHITE, width=8)


# ------------------------------------------------------------------ HUD + cards
def hud(img, seg, t, gt):
    lab = seg.get("label")
    if lab:
        L.pill(img, lab, 165 if len(lab) < 9 else 200, 70, YELLOW, 1.0, size=38, path=L.FONT_BLACK)
    L.brand(img, W - 230, 70, gt, 0.9)
    k = prog(t, 0, seg["dur"])
    if "hh" in seg:
        h = lerp(seg["hh"][0], seg["hh"][1], ease_io(k))
        x0, x1 = 560, 1080
        d = ImageDraw.Draw(img)
        rrect(img, (x0, 58, x1, 82), 12, (255, 255, 255, 50))
        fx = x0 + (x1 - x0) * min(1, h / 168)
        rrect(img, (x0, 58, max(x0 + 24, fx), 82), 12, (255, 120, 90, 255))
        for dd in range(1, 7):
            x = x0 + (x1 - x0) * dd / 7
            d.line((x, 54, x, 86), fill=(30, 25, 60), width=3)
        text(img, f"{int(round(h))} h WACH", 38, 1220, 70, fill=WHITE, stroke=5, sfill=NAVY)
    if "bb" in seg:
        b = lerp(seg["bb"][0], seg["bb"][1], ease_io(k))
        battery(img, 1395, 70, b, gt=gt)
        text(img, f"{int(round(b))} %", 26, 1395, 112, fill=WHITE, path=FONT_XB, stroke=3, sfill=NAVY)


def sc_card(img, seg, t, gt):
    hud(img, seg, t, gt)
    p = back_out(prog(t, 0.05, 0.5))
    x = W / 2 + (1 - ease_out(prog(t, 0.0, 0.45))) * 900
    text(img, seg["title"], 170 * max(0.05, p), x, 440, fill=YELLOW, stroke=14, sfill=NAVY, rotate=-3)
    label(img, seg["sub"], W / 2, 610, ease_out(prog(t, 0.35, 0.4)), size=54)
    if "day" in seg:
        n = seg["day"]
        for i in range(7):
            cx = W / 2 - 3 * 110 + i * 110
            done = i < n
            cur = i == n - 1 or (n == 5 and i == 5)
            q = ease_out(prog(t, 0.2 + 0.05 * i, 0.3))
            col = (255, 120, 90) if done else (90, 90, 130)
            if cur:
                col = YELLOW
            ImageDraw.Draw(img).ellipse((cx - 34 * q, 760 - 34 * q, cx + 34 * q, 760 + 34 * q), fill=col)
            text(img, str(i + 1), 34 * max(0.05, q), cx, 760, fill=NAVY)
    # moon / sun swap
    ph = prog(t, 0.0, seg["dur"])
    d = ImageDraw.Draw(img)
    mx, my = 1640, 300 - 40 * math.sin(ph * math.pi)
    d.ellipse((mx - 60, my - 60, mx + 60, my + 60), fill=(250, 240, 200))
    d.ellipse((mx - 30, my - 75, mx + 90, my + 45), fill=(30, 26, 70))


# ------------------------------------------------------------------ scenes
def sc_s00(img, seg, t, gt):
    L.brand(img, W / 2, 90, gt, back_out(prog(t, 0.0, 0.5)))
    a = ease_out(prog(t, 0.2, 0.5))
    text(img, "1 WOCHE OHNE SCHLAF?", 104, W / 2, 235, fill=YELLOW, stroke=11, sfill=NAVY, alpha=a, rotate=-2)
    bed(img, 640, 690, eyes_open=True, gt=gt)
    # alarm clock shaking
    sh = 6 * math.sin(gt * 40) if (t % 2.0) < 0.6 else 0
    cx, cy = 1020 + sh, 470
    d = ImageDraw.Draw(img)
    for k in (-1, 1):
        d.ellipse((cx + k * 55 - 30, cy - 105, cx + k * 55 + 30, cy - 45), fill=RED)
    clock(img, cx, cy, 80, 3.0 + t / 3600)
    p7 = pop_scale(seg, t, "7")
    if p7 > 0.02:
        chip(img, "7 TAGE = 168 STUNDEN", 1450, 420, YELLOW, min(1, p7), size=40)
    pn = ap(seg, t, "Nickerchen")
    if pn > 0.02:
        chip(img, "0 MINUTEN SCHLAF", 1450, 540, WHITE, pn, size=40)
    pa = pop_scale(seg, t, "Achtung")
    if pa > 0.02:
        tx, ty, r = 1450, 700, 90 * pa
        d.polygon([(tx, ty - r), (tx + r * 1.1, ty + r * 0.8), (tx - r * 1.1, ty + r * 0.8)], fill=YELLOW,
                  outline=NAVY, width=8)
        text(img, "!", 110 * pa, tx, ty + 10, fill=NAVY)
        L.stamp(img, "NICHT NACHMACHEN!", t, tw(seg, "nachmachen") - 0.2, 1450, 860, size=58, rot=-4)


def sc_s01(img, seg, t, gt):
    hud(img, seg, t, gt)
    paste_c(img, brain_sprite(520), 520, 520)
    label(img, "DEIN GEHIRN", 520, 230, col=YELLOW)
    grow = ease_io(prog(t, tw(seg, "größer") - 0.3, 1.2))
    flow = ap(seg, t, "spült", d=0.5)
    junk = ap(seg, t, "Müll", d=0.5)
    pz = ease_out(prog(t, tw(seg, "Raum") - 0.4, 0.5))
    if pz <= 0.02:
        return
    d = ImageDraw.Draw(img)
    d.line((660, 450, 1080, 380), fill=WHITE, width=4)
    d.ellipse((620, 420, 700, 500), outline=WHITE, width=6)

    def draw(lay, r):
        dd = ImageDraw.Draw(lay)
        gap = 1.0 + 0.26 * grow
        sp = 92 * gap
        rr = random.Random(4)
        for i in range(-4, 5):
            for j in range(-4, 5):
                x, y = r + i * sp, r + j * sp
                dd.ellipse((x - 38, y - 38, x + 38, y + 38), fill=(255, 160, 190), outline=(215, 110, 150), width=4)
        for k in range(40):
            x0, y0 = rr.uniform(0, 2 * r), r + (rr.randint(-4, 4) + 0.5) * sp
            vx = (gt * 160 + x0) % (2 * r + 200) - 100 if flow > 0 and junk < 0.5 else x0
            if flow > 0 and junk < 0.5:
                dd.ellipse((vx - 8, y0 - 8, vx + 8, y0 + 8), fill=(110, 200, 255))
            if k % 2 == 0:
                jx = vx + 30 if (flow > 0 and junk < 0.5) else x0
                ja = 1.0 if (flow == 0 or junk > 0.5) else max(0.0, 1 - (jx / (2 * r)))
                if ja > 0.05:
                    dd.ellipse((jx - 11, y0 - 11, jx + 11, y0 + 11), fill=(110, 70, 40))
    masked_panel(img, 1340, 520, int(300 * pz), draw)
    label(img, "ZWISCHEN DEN ZELLEN", 1340, 870 - 40, pz)
    pg = ap(seg, t, "60")
    if pg > 0.02:
        chip(img, "+60 % PLATZ (MÄUSE)", 1340, 180, YELLOW, pg, size=34)
    if flow > 0.02 and junk < 0.5:
        chip(img, "HIRNWASSER SPÜLT", 520, 840, BLUE, flow, size=34)
    if junk > 0.02:
        chip(img, "OHNE SCHLAF: MÜLL BLEIBT", 520, 840, RED, junk, size=34)


def sc_s02(img, seg, t, gt):
    hud(img, seg, t, gt)
    t_s, t_d = tw(seg, "Solange"), tw(seg, "Schlafdruck")
    fill = ease_io(prog(t, t_s, t_d - t_s + 0.5))
    cx, top, bot = 560, 230, 820
    rrect(img, (cx - 100, top, cx + 100, bot), 50, (255, 255, 255, 40), outline=(255, 255, 255, 200), width=6)
    n = int(34 * fill)
    rr = random.Random(2)
    d = ImageDraw.Draw(img)
    for i in range(n):
        x = cx - 60 + (i % 4) * 40 + rr.uniform(-4, 4)
        y = bot - 40 - (i // 4) * 38 + 3 * math.sin(gt * 3 + i)
        d.ellipse((x - 17, y - 17, x + 17, y + 17), fill=PURPLE, outline=WHITE, width=2)
    label(img, "SCHLAFDRUCK", cx, top - 40, col=YELLOW)
    pa = ap(seg, t, "Adenosin")
    if pa > 0.02:
        chip(img, "ADENOSIN", cx, bot + 50, PURPLE, pa)
    # receptor panel
    pr = ease_out(prog(t, tw(seg, "Koffein") - 0.4, 0.5))
    if pr > 0.02:
        px, py = 1250, 600
        d.rounded_rectangle((px - 420, py, px + 420, py + 140), 40, fill=(255, 160, 190))
        label(img, "NERVENZELLE", px, py + 100, pr)
        caf = ap(seg, t, "Andockstellen", d=0.6)
        for i in range(4):
            x = px - 300 + i * 200
            d.rectangle((x - 40, py - 10, x + 40, py + 30), fill=(215, 110, 150))
            d.rectangle((x - 22, py - 10, x + 22, py + 10), fill=(255, 160, 190))
            yy = py - 10 - 160 * (1 - caf)
            d.ellipse((x - 22, yy - 26, x + 22, yy + 18), fill=(130, 80, 40), outline=WHITE, width=2)
            # adenosine bouncing off
            if caf > 0.5:
                bx = x + 60 * math.sin(gt * 3 + i)
                by = py - 140 - 30 * abs(math.sin(gt * 4 + i))
                d.ellipse((bx - 17, by - 17, bx + 17, by + 17), fill=PURPLE, outline=WHITE, width=2)
        # coffee cup
        q = pop_scale(seg, t, "Koffein")
        cx2, cy2 = 1550, 330
        if q > 0.02:
            s_ = q
            d.rounded_rectangle((cx2 - 70 * s_, cy2 - 60 * s_, cx2 + 70 * s_, cy2 + 70 * s_), int(20 * s_),
                                fill=WHITE)
            d.arc((cx2 + 40 * s_, cy2 - 30 * s_, cx2 + 110 * s_, cy2 + 40 * s_), 270, 90, fill=WHITE,
                  width=max(2, int(14 * s_)))
            d.ellipse((cx2 - 60 * s_, cy2 - 70 * s_, cx2 + 60 * s_, cy2 - 46 * s_), fill=(110, 60, 30))
            for k in range(3):
                ph = (gt + k / 3) % 1
                d.arc((cx2 - 40 + k * 30, cy2 - 150 - ph * 40, cx2 - 10 + k * 30, cy2 - 90 - ph * 40), 90, 270,
                      fill=(255, 255, 255), width=4)
            label(img, "KOFFEIN", 1250, 330, q, col=(255, 200, 140))
    pw = ap(seg, t, "Kaffee")
    if pw > 0.02:
        chip(img, "KAFFEE = WACH", 1250, 210, GREEN, pw)
    pn = ap(seg, t, "baut")
    if pn > 0.02:
        chip(img, "DRUCK BLEIBT!", cx, 170, RED, pn)


def sc_s03(img, seg, t, gt):
    hud(img, seg, t, gt)
    t_m = tw(seg, "Mitternacht")
    hours = 7 + 17 * ease_io(prog(t, 0.6, t_m + 0.6))
    clock(img, 560, 520, 230, hours)
    hh = int(hours) % 24
    text(img, f"{hh:02d}:{int((hours % 1) * 60):02d}", 64, 560, 830, fill=YELLOW, stroke=6, sfill=NAVY)
    p17 = pop_scale(seg, t, "17")
    if p17 > 0.02:
        text(img, "17 h", 120 * p17, 1000, 300, fill=WHITE, stroke=10, sfill=NAVY, rotate=-5)
    pg = ease_io(prog(t, tw(seg, "0,5") - 0.3, 0.9))
    if ap(seg, t, "Tests") > 0.02:
        glass(img, 1380, 520, 0.5 * pg)
        label(img, "TEST-LEISTUNG WIE MIT", 1380, 230, ap(seg, t, "Tests"))
        if pg > 0.05:
            text(img, "≈ 0,5 ‰", 90, 1380, 820, fill=YELLOW, stroke=9, sfill=NAVY, alpha=min(1, pg * 2))


def road(img, gt, a=1.0, blink=0.0):
    d = ImageDraw.Draw(img)
    d.polygon([(860, 300), (1060, 300), (1700, 900), (220, 900)], fill=(60, 62, 80))
    for k in range(8):
        ph = ((gt * 1.6) + k / 8) % 1
        y0 = 300 + 600 * ph ** 2
        y1 = 300 + 600 * min(1, (ph + 0.05)) ** 2
        w0, w1 = 4 + 16 * ph, 4 + 16 * min(1, ph + 0.05)
        d.polygon([(960 - w0, y0), (960 + w0, y0), (960 + w1, y1), (960 - w1, y1)], fill=WHITE)
    if blink > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, int(235 * blink)))
        img.alpha_composite(lay)


def sc_s04(img, seg, t, gt):
    hud(img, seg, t, gt)
    t_s = tw(seg, "Sekundenschlaf")
    sw = ease_io(prog(t, t_s - 0.5, 0.5))
    if sw < 0.99:
        a = 1 - sw
        hours = 24 + 7 * ease_io(prog(t, 0.3, 3.0))
        clock(img, 560, 520, 230, hours)
        text(img, f"{int(hours) % 24:02d}:00", 64, 560, 830, fill=YELLOW, stroke=6, sfill=NAVY, alpha=a)
        pg = ease_io(prog(t, tw(seg, "1") - 0.3, 0.9))
        glass(img, 1380, 520, 0.5 + 0.5 * pg)
        label(img, "NACH 24 STUNDEN", 1380, 230)
        text(img, "≈ 0,5 ‰" if pg < 0.5 else "≈ 1 ‰", 90, 1380, 820, fill=YELLOW if pg < 0.5 else RED, stroke=9,
             sfill=NAVY)
        if sw > 0.01:
            lay = Image.new("RGBA", (W, H), (20, 18, 50, int(255 * sw)))
            img.alpha_composite(lay)
    if sw > 0.01:
        cyc = (t - t_s) % 2.4
        blink = 1.0 if 1.4 < cyc < 2.1 else 0.0
        road(img, gt, sw, blink)
        hud(img, seg, t, gt)
        chip(img, "SEKUNDENSCHLAF", W / 2, 200, YELLOW, sw, size=46)
        if blink:
            text(img, "… 1 … 2 … 3 …", 70, W / 2, 560, fill=(200, 200, 230))
        pst = ap(seg, t, "Steuer")
        if pst > 0.02:
            d = ImageDraw.Draw(img)
            tx, ty, r = 1660, 560, 110
            d.polygon([(tx, ty - r), (tx + r * 1.1, ty + r * 0.8), (tx - r * 1.1, ty + r * 0.8)], fill=RED,
                      outline=WHITE, width=8)
            text(img, "!", 120, tx, ty + 12, fill=WHITE)


def sc_s06(img, seg, t, gt):
    hud(img, seg, t, gt)
    x0, x1, y0, y1 = 300, 1620, 270, 800
    rrect(img, (x0 - 40, y0 - 40, x1 + 40, y1 + 60), 40, DARK + (200,))
    d = ImageDraw.Draw(img)

    def X(h):
        return x0 + (x1 - x0) * h / 48

    def press(h):  # sleep pressure
        return 0.15 + 0.8 * h / 48

    def circ(h):  # circadian alerting, peak late evening, trough early morning
        return 0.5 + 0.35 * math.sin((h - 4) / 24 * 2 * math.pi)

    def alert(h):
        return max(0.03, min(1.0, 0.75 + circ(h) * 0.55 - press(h)))

    def Y(v):
        return y1 - (y1 - y0) * v
    for h in range(0, 49, 6):
        x = X(h)
        d.line((x, y1, x, y1 + 12), fill=WHITE, width=3)
        text(img, f"{h} h", 24, x, y1 + 34, fill=(200, 200, 230), path=FONT_XB)
    pts = [(X(h / 2), Y(alert(h / 2))) for h in range(0, 97)]
    d.line(pts, fill=GREEN, width=10, joint="curve")
    label(img, "WACHHEIT", x0 + 120, y0 - 10, col=GREEN, size=30)
    mh = lerp(24, 27, prog(t, 0, seg["dur"]))
    pm = ap(seg, t, "zweiten")
    if pm > 0.02:
        mx, my = X(26), Y(alert(26))
        d.ellipse((mx - 20, my - 20, mx + 20, my + 20), fill=YELLOW)
        d.ellipse((X(26) - 40, y0 + 10, X(26) + 40, y0 + 90), fill=(255, 220, 90))
        label(img, "MORGEN-BOOST", X(26), y0 + 125, pm, col=YELLOW, size=28)
    pu = ap(seg, t, "Uhr")
    if pu > 0.02:
        chip(img, "INNERE UHR: WACH-SIGNAL", 960, 150, YELLOW, pu, size=32)
    pa = ap(seg, t, "Absturz")
    if pa > 0.02:
        ax, ay = X(40), Y(alert(40))
        d.line((ax, ay - 200, ax, ay - 30), fill=RED, width=12)
        d.polygon([(ax - 28, ay - 50), (ax + 28, ay - 50), (ax, ay - 5)], fill=RED)
        label(img, "ABSTURZ", ax, ay - 230, pa, col=RED, size=34)
    _ = mh


def sc_s05(img, seg, t, gt):
    hud(img, seg, t, gt)
    amy = ap(seg, t, "Amygdala", d=0.6) * (0.6 + 0.4 * ap(seg, t, "60", d=0.5))
    pulse = amy * (0.85 + 0.15 * math.sin(gt * 8))
    front = BLUE if ap(seg, t, "Stirnhirn") > 0.02 else None
    paste_c(img, brain_sprite(720, front, round(pulse, 2)), 760, 520)
    d = ImageDraw.Draw(img)
    if front:
        fx, fy, ax_, ay_ = 760 - 360 + 0.24 * 720, 520 - 260 + 0.42 * 518, 760 - 360 + 0.55 * 720, 520 - 260 + 0.62 * 518
        br = ap(seg, t, "Kontakt", d=0.4)
        mx_, my_ = (fx + ax_) / 2, (fy + ay_) / 2
        gap = 40 * br
        dx, dy = ax_ - fx, ay_ - fy
        n = math.hypot(dx, dy)
        ux, uy = dx / n, dy / n
        d.line((fx, fy, mx_ - ux * gap, my_ - uy * gap), fill=YELLOW, width=10)
        d.line((mx_ + ux * gap, my_ + uy * gap, ax_, ay_), fill=YELLOW, width=10)
        if br > 0.3:
            L.cross(img, mx_, my_, 26, br, w=10)
        label(img, "STIRNHIRN = BREMSE", 420, 200, ap(seg, t, "Stirnhirn"), col=BLUE)
    if amy > 0.02:
        label(img, "AMYGDALA", 1000, 820, min(1, amy * 2), col=(255, 120, 130))
    p6 = pop_scale(seg, t, "60")
    if p6 > 0.02:
        text(img, "+60 %", 130 * p6, 1450, 300, fill=RED, stroke=10, sfill=WHITE, rotate=-6)
        label(img, "STÄRKERE REAKTION", 1450, 400, min(1, p6))
    pw = pop_scale(seg, t, "wütend")
    if pw > 0.02:
        face(img, 1350, 640, 100 * pw, "angry")
    pt = pop_scale(seg, t, "traurig")
    if pt > 0.02:
        face(img, 1610, 640, 100 * pt, "sad")


def food(img, kind, cx, cy, s):
    if s <= 0.02:
        return
    d = ImageDraw.Draw(img)
    if kind == "cake":
        d.rounded_rectangle((cx - 110 * s, cy - 40 * s, cx + 110 * s, cy + 80 * s), int(14 * s), fill=(240, 200, 150))
        d.rounded_rectangle((cx - 110 * s, cy - 70 * s, cx + 110 * s, cy - 20 * s), int(20 * s), fill=(255, 150, 190))
        d.rectangle((cx - 110 * s, cy + 15 * s, cx + 110 * s, cy + 30 * s), fill=(150, 80, 50))
        d.ellipse((cx - 22 * s, cy - 120 * s, cx + 22 * s, cy - 76 * s), fill=RED)
    elif kind == "chips":
        d.polygon([(cx - 80 * s, cy - 110 * s), (cx + 80 * s, cy - 110 * s), (cx + 95 * s, cy + 100 * s),
                   (cx - 95 * s, cy + 100 * s)], fill=(255, 200, 40))
        d.ellipse((cx - 45 * s, cy - 40 * s, cx + 45 * s, cy + 40 * s), fill=RED)
        text(img, "CHIPS", 30 * s, cx, cy + 70 * s, fill=NAVY)
    else:
        d.polygon([(cx - 120 * s, cy - 40 * s), (cx - 70 * s, cy), (cx - 120 * s, cy + 40 * s)], fill=(150, 220, 255))
        d.polygon([(cx + 120 * s, cy - 40 * s), (cx + 70 * s, cy), (cx + 120 * s, cy + 40 * s)], fill=(150, 220, 255))
        d.ellipse((cx - 75 * s, cy - 55 * s, cx + 75 * s, cy + 55 * s), fill=(255, 90, 160))
        d.arc((cx - 50 * s, cy - 35 * s, cx + 50 * s, cy + 35 * s), 200, 340, fill=WHITE, width=max(2, int(8 * s)))


def sc_s07(img, seg, t, gt):
    hud(img, seg, t, gt)
    base = 820
    pg = ease_io(prog(t, tw(seg, "28") - 0.3, 0.9))
    pl = ease_io(prog(t, tw(seg, "18") - 0.3, 0.9))
    ag, al = ap(seg, t, "Ghrelin"), ap(seg, t, "Leptin")
    for cx, a, f, col, name, sub, val in ((480, ag, 1 + 0.28 * pg, ORANGE, "GHRELIN", "HUNGER", "+28 %"),
                                          (800, al, 1 - 0.18 * pl, BLUE, "LEPTIN", "SATT", "−18 %")):
        if a <= 0.02:
            continue
        h = 360 * f * a
        rrect(img, (cx - 90, base - 360, cx + 90, base), 20, (255, 255, 255, 40))
        rrect(img, (cx - 90, base - h, cx + 90, base), 20, col + (255,))
        label(img, name, cx, base + 40, a, col=col)
        label(img, sub, cx, base + 80, a, size=26)
        k = pg if name == "GHRELIN" else pl
        if k > 0.05:
            text(img, val, 64, cx, base - h - 50, fill=col, stroke=7, sfill=NAVY)
    for w_, kind, x in (("Kuchen", "cake", 1200), ("Chips", "chips", 1480), ("Süßigkeiten", "candy", 1730)):
        s = pop_scale(seg, t, w_)
        food(img, kind, x, 560 + 10 * math.sin(gt * 3 + x), s)
    if ap(seg, t, "Heißhunger") > 0.02:
        chip(img, "HEISSHUNGER", 1470, 260, ORANGE, ap(seg, t, "Heißhunger"), size=44)


def sc_s08(img, seg, t, gt):
    hud(img, seg, t, gt)
    paste_c(img, brain_sprite(720), 760, 520)
    d = ImageDraw.Draw(img)
    k = ease_io(prog(t, tw(seg, "Forscher") - 0.3, 3.5))
    rr = random.Random(12)
    for i in range(int(36 * k)):
        x, y = 760 + rr.uniform(-280, 260), 520 + rr.uniform(-170, 150)
        r = rr.uniform(7, 15)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 220, 70), outline=(200, 140, 0), width=2)
    p5 = pop_scale(seg, t, "5")
    if p5 > 0.02:
        text(img, "+5 %", 140 * p5, 1450, 380, fill=YELLOW, stroke=10, sfill=NAVY, rotate=-5)
    pb = ap(seg, t, "Beta-Amyloid")
    if pb > 0.02:
        chip(img, "BETA-AMYLOID", 1450, 540, YELLOW, pb, size=40)
        label(img, "nach ~31 h wach (Studie, 20 Personen)", 1450, 610, pb, size=24)
    pa = ap(seg, t, "Alzheimer")
    if pa > 0.02:
        chip(img, "MIT ALZHEIMER VERKNÜPFT", 1450, 720, WHITE, pa, size=32)
    pm = ap(seg, t, "Müll")
    if pm > 0.02:
        label(img, "MÜLL IM GEHIRN", 760, 200, pm, col=YELLOW)


def sc_s09(img, seg, t, gt):
    hud(img, seg, t, gt)
    wob = ap(seg, t, "Wände", d=1.0)
    flick = ap(seg, t, "flimmern", d=0.6)
    x0, x1, y0, y1 = 280, 1640, 170, 820
    d = ImageDraw.Draw(img)
    d.rectangle((x0, y0, x1, y1), fill=(70, 60, 120))
    d.polygon([(x0, 680), (x1, 680), (x1, y1), (x0, y1)], fill=(120, 80, 60))
    for i in range(30):
        xs = x0 + 20 + i * 46
        pts = []
        for y in range(y0, 681, 20):
            pts.append((xs + 22 * wob * math.sin(y / 55 + gt * 3 + i * 0.3), y))
        d.line(pts, fill=(95, 85, 150), width=8)
    # window & door & picture
    wx = 520 + 18 * wob * math.sin(gt * 2)
    d.rectangle((wx - 120, 260, wx + 120, 480), fill=(20, 24, 60), outline=WHITE, width=8)
    d.line((wx, 260, wx, 480), fill=WHITE, width=6)
    d.ellipse((wx + 30, 290, wx + 80, 340), fill=(250, 240, 200))
    d.rectangle((1300, 380, 1460, 680), fill=(150, 95, 60), outline=(100, 60, 40), width=6)
    d.ellipse((1420, 520, 1440, 540), fill=YELLOW)
    if flick > 0.02:
        rr = random.Random(int(gt * 10))
        for k in range(12):
            x, y = rr.uniform(x0, x1), rr.uniform(y0, 680)
            s = rr.uniform(20, 60)
            d.rectangle((x, y, x + s, y + s / 3), fill=rr.choice([(255, 90, 160), (90, 255, 200), (255, 230, 90)]))
        # ghost shadow
        gx = 960 + 300 * math.sin(gt * 0.7)
        g = person_shadow(300)
        paste_c(img, g, gx, 680, 0.35 * flick, anchor="b")
    pg = ap(seg, t, "Geräusche")
    if pg > 0.02:
        for k in range(3):
            r = 60 + k * 45 + 20 * ((gt * 2) % 1)
            d.arc((1380 - r, 300 - r, 1380 + r, 300 + r), -50, 50, fill=WHITE, width=6)
        text(img, "?", 110, 1580, 300, fill=YELLOW, stroke=8, sfill=NAVY, alpha=pg)
    p48 = ap(seg, t, "48")
    if p48 > 0.02:
        stage_bar(img, 1, p48)
    if ap(seg, t, "unheimlich") > 0.02:
        L.stamp(img, "HALLUZINATIONEN", t, tw(seg, "Halluzinationen") - 0.1, 960, 520, size=96, rot=-5)


def person_shadow(h):
    k = ("shadow", h)
    if k not in _cache:
        sp = L.E.person_sprite(h, (10, 10, 20))
        _cache[k] = sp
    return _cache[k]


def sc_s10(img, seg, t, gt):
    hud(img, seg, t, gt)
    rrect(img, (220, 170, 1700, 830), 40, (8, 8, 20, 240))
    d = ImageDraw.Draw(img)
    rr = random.Random(7)
    pe = ap(seg, t, "beobachtet", d=0.8)
    n = int(3 + 9 * pe)
    for i in range(n):
        x, y = rr.uniform(300, 1620), rr.uniform(220, 520)
        bl = (gt * 0.7 + rr.random()) % 1 < 0.08
        for k in (-1, 1):
            if bl:
                d.line((x + k * 26 - 14, y, x + k * 26 + 14, y), fill=(255, 230, 120), width=4)
            else:
                d.ellipse((x + k * 26 - 14, y - 9, x + k * 26 + 14, y + 9), fill=(255, 230, 120))
                d.ellipse((x + k * 26 - 5, y - 5, x + k * 26 + 5, y + 5), fill=(20, 10, 10))
    look = 1 if math.sin(gt * 1.5) > 0 else -1
    sp = L.E.person_sprite(330, ORANGE)
    if look < 0:
        sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
    paste_c(img, sp, 560, 820, 1.0, anchor="b")
    if ap(seg, t, "72") > 0.02:
        stage_bar(img, 2, ap(seg, t, "72"))
    pg = ap(seg, t, "Gedächtnis")
    if pg > 0.02:
        bx, by = 1200, 640
        rrect(img, (bx - 380, by - 90, bx + 380, by + 90), 45, (255, 255, 255, int(245 * pg)))
        d.polygon([(bx - 300, by + 80), (bx - 380, by + 150), (bx - 230, by + 80)], fill=WHITE)
        msg = "Ich wollte sagen, dass …"
        fade = prog(t, tw(seg, "Mitten") - 0.2, 2.0)
        x = bx - 330
        rr2 = random.Random(1)
        for ch in msg:
            dy = 120 * max(0, fade * 1.6 - rr2.random()) ** 2
            a = max(0.0, 1 - dy / 120)
            text(img, ch, 50, x + 12, by + dy, fill=NAVY, alpha=a * pg)
            x += L.text_w(ch if ch != " " else "n", 50) + 2


def sc_s11(img, seg, t, gt):
    hud(img, seg, t, gt)
    p = ease_out(prog(t, 0.0, 0.5))
    lay = Image.new("RGBA", (760, 560))
    ld = ImageDraw.Draw(lay)
    ld.rectangle((0, 0, 759, 559), fill=(245, 238, 220), outline=(120, 100, 80), width=6)
    text(lay, "DIE ZEITUNG · 1964", 34, 380, 50, fill=(80, 60, 40), path=FONT_XB)
    ld.line((30, 85, 730, 85), fill=(80, 60, 40), width=4)
    text(lay, "Schüler bleibt", 62, 380, 150, fill=NAVY)
    text(lay, "11 Tage wach!", 72, 380, 235, fill=RED)
    for k in range(5):
        ld.line((40, 320 + k * 40, 420, 320 + k * 40), fill=(170, 160, 140), width=10)
    sp = L.E.person_sprite(230, (90, 80, 70))
    lay.paste(sp, (560, 250), sp)
    text(lay, "Randy Gardner, 17", 30, 560, 520, fill=(80, 60, 40), path=FONT_XB)
    lay = lay.rotate(-3, resample=Image.BICUBIC, expand=True)
    paste_c(img, lay, 620, 500, p)
    t264 = tw(seg, "264")
    h = int(264 * ease_io(prog(t, t264 - 1.5, 1.6)))
    if t > t264 - 1.5:
        text(img, f"{h} h", 130, 1420, 300, fill=YELLOW, stroke=10, sfill=NAVY)
        label(img, "OHNE SCHLAF (REKORD-VERSUCH)", 1420, 400)
    t11 = tw(seg, "11")
    if t > t11 - 0.2:
        d = ImageDraw.Draw(img)
        for i in range(11):
            x = 1100 + (i % 6) * 110
            y = 520 + (i // 6) * 110
            q = ease_out(prog(t, t11 - 0.2 + i * 0.08, 0.25))
            if q <= 0.02:
                continue
            d.rounded_rectangle((x - 45, y - 45, x + 45, y + 45), 12, fill=WHITE)
            text(img, str(i + 1), 40, x, y, fill=NAVY)
            L.cross(img, x, y, 30 * q, q, w=8)
    ps = ap(seg, t, "Straßenschild", d=0.5)
    if ps > 0.02:
        lay2 = Image.new("RGBA", (W, H), (20, 18, 50, int(230 * ps)))
        img.alpha_composite(lay2)
        d = ImageDraw.Draw(img)
        m = ease_io(prog(t, tw(seg, "Menschen") - 0.3, 1.0))
        sx, sy = 960, 800
        d.rectangle((sx - 10, sy - 420, sx + 10, sy), fill=(180, 180, 190))
        rrect(img, (sx - 180, sy - 520, sx + 180, sy - 400), 14, (40, 140, 70, int(255 * (1 - m))))
        text(img, "MAIN ST", 54, sx, sy - 460, fill=WHITE, alpha=1 - m)
        if m > 0.02:
            paste_c(img, person_shadow(560), sx, sy, m * 0.9, anchor="b")
            text(img, "?", 160, sx + 260, sy - 420, fill=YELLOW, stroke=10, sfill=NAVY, alpha=m)
        hud(img, seg, t, gt)
        label(img, "TAG 4: SCHILD ODER MENSCH?", 960, 200, ps, col=YELLOW, size=44)


def shield(img, cx, cy, s, crack, a=1.0):
    d = ImageDraw.Draw(img)
    pts = [(cx - 110 * s, cy - 120 * s), (cx + 110 * s, cy - 120 * s), (cx + 110 * s, cy + 10 * s),
           (cx, cy + 140 * s), (cx - 110 * s, cy + 10 * s)]
    d.polygon(pts, fill=(80, 200, 120), outline=WHITE)
    d.line(pts + [pts[0]], fill=WHITE, width=8)
    if crack > 0.02:
        c = [(cx - 10, cy - 120 * s), (cx + 20, cy - 60 * s), (cx - 15, cy - 10 * s), (cx + 25, cy + 50 * s),
             (cx, cy + 140 * s * crack)]
        d.line(c[:2 + int(3 * crack)], fill=NAVY, width=10)


def thermo(img, cx, cy, s, frac, a=1.0):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((cx - 30, cy - 150, cx + 30, cy + 80), 30, fill=WHITE)
    d.ellipse((cx - 55, cy + 50, cx + 55, cy + 160), fill=WHITE)
    col = (90, 170, 255)
    d.ellipse((cx - 40, cy + 65, cx + 40, cy + 145), fill=col)
    d.rectangle((cx - 15, cy + 80 - 200 * frac, cx + 15, cy + 90), fill=col)


def snow(img, cx, cy, gt, a):
    d = ImageDraw.Draw(img)
    rr = random.Random(5)
    for k in range(14):
        x = cx + rr.uniform(-170, 170)
        y = cy - 200 + ((gt * 60 + rr.uniform(0, 380)) % 380)
        for an in range(3):
            q = an * math.pi / 3
            d.line((x - 10 * math.cos(q), y - 10 * math.sin(q), x + 10 * math.cos(q), y + 10 * math.sin(q)),
                   fill=WHITE, width=3)


def phone(img, cx, cy, s, gt, a=1.0):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((cx - 110 * s, cy - 200 * s, cx + 110 * s, cy + 200 * s), int(30 * s), fill=(30, 30, 40),
                        outline=WHITE, width=max(2, int(6 * s)))
    d.rounded_rectangle((cx - 90 * s, cy - 170 * s, cx + 90 * s, cy + 170 * s), int(14 * s), fill=(20, 20, 30))
    bw, bh = 120 * s, 56 * s
    d.rounded_rectangle((cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), 8, outline=WHITE,
                        width=max(2, int(5 * s)))
    d.rectangle((cx + bw / 2 + 2, cy - bh / 5, cx + bw / 2 + 10 * s, cy + bh / 5), fill=WHITE)
    if int(gt * 3) % 2 == 0:
        d.rectangle((cx - bw / 2 + 6, cy - bh / 2 + 6, cx - bw / 2 + 14, cy + bh / 2 - 6), fill=RED)
    text(img, "1 %", 56 * s, cx, cy + 90 * s, fill=RED)


def sc_s12(img, seg, t, gt):
    hud(img, seg, t, gt)
    ps = pop_scale(seg, t, "Abwehrkräfte")
    if ps > 0.02:
        shield(img, 340, 480, ps, ap(seg, t, "schwächer", d=0.6))
        label(img, "ABWEHR", 340, 690, min(1, ps))
    pf = pop_scale(seg, t, "frierst")
    if pf > 0.02:
        thermo(img, 760, 470, pf, 0.5 - 0.3 * ap(seg, t, "ständig", d=1.0))
        snow(img, 760, 470, gt, pf)
        label(img, "FRIEREN", 760, 690, min(1, pf))
    pw = ap(seg, t, "Worte")
    if pw > 0.02:
        word = "W  o  r  t  e …"
        n = int(len(word) * prog(t, tw(seg, "Worte"), 2.6))
        text(img, word[:n], 60, 1180, 470, fill=WHITE, stroke=6, sfill=NAVY, anchor="mm")
        label(img, "LANGSAM", 1180, 690, pw)
    pk = ap(seg, t, "Konzentration")
    if pk > 0.02:
        d = ImageDraw.Draw(img)
        for r, c in ((90, RED), (60, WHITE), (30, RED)):
            d.ellipse((1180 - r, 300 - r - 40, 1180 + r, 300 + r - 40), fill=c)
        L.cross(img, 1180, 260, 70, pk, w=12)
    pp = pop_scale(seg, t, "Handy")
    if pp > 0.02:
        phone(img, 1580, 480, pp, gt)
        label(img, "GEHIRN-AKKU", 1580, 720, min(1, pp), col=RED)


def rat(img, cx, cy, s=1.0):
    d = ImageDraw.Draw(img)
    col = (190, 190, 205)
    d.ellipse((cx - 120 * s, cy - 60 * s, cx + 80 * s, cy + 60 * s), fill=col)
    d.polygon([(cx + 60 * s, cy - 40 * s), (cx + 160 * s, cy + 10 * s), (cx + 60 * s, cy + 40 * s)], fill=col)
    d.ellipse((cx + 30 * s, cy - 80 * s, cx + 80 * s, cy - 30 * s), fill=(255, 180, 200))
    d.ellipse((cx + 105 * s, cy - 12 * s, cx + 121 * s, cy + 4 * s), fill=NAVY)
    d.ellipse((cx + 150 * s, cy, cx + 168 * s, cy + 18 * s), fill=(255, 140, 170))
    d.line([(cx - 120 * s, cy + 10 * s), (cx - 200 * s, cy - 30 * s), (cx - 260 * s, cy + 20 * s)],
           fill=(255, 170, 190), width=max(2, int(8 * s)), joint="curve")


def sc_s13(img, seg, t, gt):
    hud(img, seg, t, gt)
    p = pop_scale(seg, t, "168")
    if p > 0.02:
        text(img, "168 h", 170 * p, W / 2, 300, fill=RED, stroke=12, sfill=WHITE, rotate=-3)
    pc = ap(seg, t, "Versuche")
    if pc > 0.02:
        cx, cy = 620, 620
        rrect(img, (cx - 210, cy - 230, cx + 210, cy + 230), 26, (240, 240, 245, int(255 * pc)))
        rrect(img, (cx - 70, cy - 260, cx + 70, cy - 210), 12, (150, 150, 170, 255))
        text(img, "FORSCHUNG", 40, cx, cy - 160, fill=NAVY, alpha=pc)
        text(img, "> 48 h", 90, cx, cy - 40, fill=NAVY, alpha=pc)
        L.stamp(img, "UNETHISCH", t, tw(seg, "unethisch") - 0.1, cx, cy + 120, size=70, rot=-12, sfill=(120, 0, 0),
                fill=RED)
    pr = pop_scale(seg, t, "Ratten")
    if pr > 0.02:
        rat(img, 1320, 600, pr)
        chip(img, "TÖDLICH NACH 2–3 WOCHEN", 1320, 780, RED, min(1, pr), size=36)


def sc_s14(img, seg, t, gt):
    hud(img, seg, t, gt)
    bed(img, 640, 690, eyes_open=False, gt=gt)
    p15 = ease_io(prog(t, tw(seg, "15") - 1.2, 1.5))
    clock(img, 1180, 360, 140, 21 + 14.67 * p15)
    if p15 > 0.05:
        hh = 14.67 * p15
        text(img, f"{int(hh)} h {int((hh % 1) * 60):02d} min", 54, 1180, 550, fill=YELLOW, stroke=6, sfill=NAVY)
    pt = ap(seg, t, "Tiefschlaf", d=0.5)
    if pt > 0.02:
        x0, y0, w = 1260, 700, 560
        label(img, "SCHLAF-PHASEN", 1540, 650, pt)
        rr = random.Random(3)
        x = x0
        while x < x0 + w:
            ww = rr.uniform(30, 70)
            deep = rr.random() < 0.55
            col = (40, 60, 200) if deep else (130, 160, 255)
            hh = 120 if deep else 60
            d = ImageDraw.Draw(img)
            d.rectangle((x, y0 + 140 - hh * pt, x + ww - 4, y0 + 140), fill=col)
            x += ww
        chip(img, "TIEFSCHLAF ZUERST", 1540, 900 - 30, BLUE, pt, size=32)
    battery(img, 1560, 360, 100 * ease_io(prog(t, tw(seg, "durfte"), 6.0)), w=220, h=110, gt=gt)
    label(img, "AKKU LÄDT", 1560, 460, ease_out(prog(t, tw(seg, "durfte"), 0.4)), col=GREEN)


def sc_s15(img, seg, t, gt):
    hud(img, seg, t, gt)
    for w_, x, col, hh, lab, n in (("Erwachsene", 640, ORANGE, 420, "ERWACHSENE", 7),
                                    ("Jugendliche", 1280, BLUE, 340, "JUGENDLICHE", 10)):
        p = pop_scale(seg, t, w_)
        if p <= 0.02:
            continue
        paste_c(img, L.E.person_sprite(int(hh * min(1, p)) + 4, col), x - 170, 800, 1.0, anchor="b")
        label(img, lab, x - 170, 850, min(1, p), col=col)
        d = ImageDraw.Draw(img)
        k = ease_out(prog(t, tw(seg, w_) + 0.3, 1.4))
        for i in range(10):
            yy = 780 - i * 52
            on = i < n * k
            fill = (col if i < (7 if n == 7 else 8) else (255, 220, 120)) if on else (60, 60, 90)
            d.rounded_rectangle((x + 20, yy - 44, x + 170, yy), 10, fill=fill)
        txt = "≥ 7 h" if n == 7 else "8–10 h"
        text(img, txt, 70, x + 95, 230, fill=WHITE, stroke=7, sfill=NAVY, alpha=k)
    pm = ap(seg, t, "Schlafmedizinern")
    if pm > 0.02:
        label(img, "EMPFEHLUNG DER SCHLAFMEDIZIN (AASM)", 1560, 520, pm, size=28)


def sc_s16(img, seg, t, gt):
    L.brand(img, W / 2, 90, gt, back_out(prog(t, 0.0, 0.5)))
    t_r = wt(seg, "Rate", 1)
    fo = 1 - ease_io(prog(t, t_r - 0.4, 0.35))
    if fo > 0.02:
        paste_c(img, brain_sprite(520), 600, 500, fo)
        d = ImageDraw.Draw(img)
        an = 0.4 * math.sin(gt * 4)
        wx, wy = 820, 320
        d.line((wx, wy, wx + 160 * math.cos(an + 0.8), wy + 160 * math.sin(an + 0.8)), fill=(200, 200, 215), width=26)
        d.ellipse((wx - 40, wy - 40, wx + 40, wy + 40), fill=(200, 200, 215))
        d.ellipse((wx - 16, wy - 16, wx + 16, wy + 16), fill=(30, 26, 70))
        pw = ap(seg, t, "Wartung")
        if pw > 0.02:
            chip(img, "SCHLAF = WARTUNG", 600, 820, GREEN, pw * fo, size=44)
        pk = pop_scale(seg, t, "Kommentare")
        if pk > 0.02:
            cx, cy = 1380, 380
            s = min(1.2, pk) * fo
            rrect(img, (cx - 330 * s, cy - 110 * s, cx + 330 * s, cy + 110 * s), int(50 * s), (255, 255, 255, 245))
            text(img, "Hättest du's gewusst?", 50 * s, cx, cy - 25 * s, fill=NAVY)
            text(img, "Ja / Nein", 50 * s, cx, cy + 45 * s, fill=(255, 120, 0))
    pa = ap(seg, t, "abonnier")
    if pa > 0.02:
        sc = back_out(prog(t, tw(seg, "abonnier") - 0.1, 0.5)) * (1 + 0.05 * math.sin(gt * 6))
        bx = 1380 + (W / 2 - 1380) * (1 - fo)
        rrect(img, (bx - 250 * sc, 740 - 62 * sc, bx + 250 * sc, 740 + 62 * sc), int(62 * sc), (230, 30, 40, 255))
        text(img, "ABONNIEREN", 54 * sc, bx, 742, fill=WHITE)
    if t > t_r - 0.1:
        L.stamp(img, "RATE MAL!", t, t_r - 0.1, W / 2, 470, size=170, rot=-6)
        L.confetti(img, t, t_r)


DRAW = {k: v for k, v in globals().items() if k.startswith("sc_s")}


def draw(img, seg, t, gt):
    if seg["kind"] == "card":
        sc_card(img, seg, t, gt)
    else:
        DRAW["sc_" + seg["key"]](img, seg, t, gt)


# ------------------------------------------------------------------ sound design
SFX = {
    "s00": [("Woche", "alarm", 0.10), ("7", "thump", 0.14), ("Nickerchen", "pop", 0.10), ("Achtung", "beep", 0.08),
            ("nachmachen", "thump", 0.14)],
    "s01": [("Gehirn", "pop", 0.10), ("Raum", "whoosh", 0.08), ("größer", "rise", 0.10), ("60", "ding", 0.08),
            ("spült", "whoosh", 0.10), ("Müll", "thump", 0.12)],
    "s02": [("Adenosin", "pop", 0.10), ("Schlafdruck", "rise", 0.08), ("Koffein", "pop", 0.12),
            ("Andockstellen", "ding", 0.08), ("Kaffee", "pop", 0.08), ("baut", "thump", 0.12)],
    "s03": [("7", "tick", 0.12), ("Mitternacht", "ding", 0.08), ("17", "thump", 0.12), ("Tests", "pop", 0.10),
            ("0,5", "rise", 0.10)],
    "s04": [("24", "ding", 0.08), ("1", "rise", 0.10), ("Sekundenschlaf", "whoosh", 0.10), ("Augen", "glitch", 0.06),
            ("Steuer", "alarm", 0.10)],
    "s06": [("zweiten", "ding", 0.10), ("Uhr", "pop", 0.10), ("Absturz", "thump", 0.14)],
    "s05": [("Amygdala", "heart", 0.16), ("60", "thump", 0.14), ("Stirnhirn", "pop", 0.10), ("Kontakt", "glitch", 0.08),
            ("wütend", "pop", 0.12), ("traurig", "pop", 0.12)],
    "s07": [("Heißhunger", "pop", 0.10), ("Ghrelin", "rise", 0.10), ("Leptin", "pop", 0.10), ("Kuchen", "pop", 0.12),
            ("Chips", "pop", 0.12), ("Süßigkeiten", "pop", 0.12)],
    "s08": [("Müll", "pop", 0.10), ("5", "thump", 0.14), ("Beta-Amyloid", "pop", 0.10), ("Alzheimer", "pop", 0.08)],
    "s09": [("unheimlich", "glitch", 0.08), ("Wände", "rise", 0.08), ("flimmern", "glitch", 0.10),
            ("Geräusche", "glitch", 0.08), ("48", "thump", 0.12), ("Halluzinationen", "thump", 0.14)],
    "s10": [("72", "thump", 0.12), ("beobachtet", "heart", 0.16), ("Gedächtnis", "pop", 0.10),
            ("Mitten", "glitch", 0.06)],
    "s11": [("Randy", "pop", 0.10), ("11", "tick", 0.12), ("264", "rise", 0.12), ("Straßenschild", "whoosh", 0.10),
            ("Menschen", "glitch", 0.10)],
    "s12": [("Abwehrkräfte", "pop", 0.12), ("schwächer", "glitch", 0.06), ("frierst", "pop", 0.12),
            ("Worte", "pop", 0.08), ("Konzentration", "pop", 0.08), ("Handy", "beep", 0.10), ("Akku", "beep", 0.10)],
    "s13": [("168", "thump", 0.16), ("Versuche", "pop", 0.10), ("unethisch", "thump", 0.14), ("Ratten", "pop", 0.10)],
    "s14": [("gute", "chime", 0.10), ("durfte", "rise", 0.08), ("15", "ding", 0.10), ("Tiefschlaf", "pop", 0.10)],
    "s15": [("Erwachsene", "pop", 0.12), ("Jugendliche", "pop", 0.12)],
    "s16": [("Wartung", "ding", 0.10), ("Kommentare", "pop", 0.12), ("abonnier", "pop", 0.12), ("Rate", "chime", 0.12)],
}


def events():
    ev = []
    for s in L.SEGS:
        st = s["start"]
        if s["kind"] == "card":
            ev += [(st, "whoosh", 0.10), (st + 0.18, "thump", 0.15)]
            continue
        for w, kind, g in SFX.get(s["key"], []):
            try:
                ev.append((st + wt(s, w) - 0.08, kind, g))
            except KeyError:
                print("SFX word missing:", s["key"], w)
    return ev


L.setup(here=HERE, out="rate_mal_1_woche_ohne_schlaf.mp4", plan=plan, draw=draw, events=events)

if __name__ == "__main__":
    L.main()

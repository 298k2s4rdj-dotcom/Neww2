#!/usr/bin/env python3
"""Rate mal, was passiert, wenn … du durch die Erde springst? – animated German TikTok (situation format)."""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tiere"))
import engine as E  # noqa: E402
from engine import (SPLIT, SS, back_out, clamp, counter, ease_io, ease_out, paste_c, person_sprite,  # noqa: E402
                    prog, stamp, burst, text, wt, rrect, brand, FONT_XB)

CX, CY, R = 540, 760, 340          # Earth on screen
TOP, BOT = CY - R, CY + R
HI = E.C_HI
SKIN = (240, 240, 250)


# ------------------------------------------------------------------ sprites
_cache = {}


def globe_img():
    if "globe" not in _cache:
        s = SS(2 * R + 4, 2 * R + 4)
        c = R + 2
        s.ell(c, c, R, R, (40, 120, 230, 255))
        rr = random.Random(7)
        for _ in range(16):
            a = rr.uniform(0, 6.28)
            q = rr.uniform(0, 0.75) * R
            s.ell(c + q * math.cos(a), c + q * math.sin(a), R * rr.uniform(0.08, 0.22), R * rr.uniform(0.06, 0.16),
                  (70, 180, 90, 255))
        _cache["globe"] = s.img()
    return _cache["globe"]


def section_img():
    """cross-section with real layer radii: crust/mantle, outer core (3.480 km), inner core (1.220 km)"""
    if "sec" not in _cache:
        n = 2 * R + 4
        yy, xx = np.mgrid[0:n, 0:n]
        r = np.hypot(xx - n / 2, yy - n / 2) / R
        img = np.zeros((n, n, 4), np.float32)
        # mantle gradient
        k = np.clip((1 - r) / (1 - 0.546), 0, 1)[..., None]
        mantle = np.array([170, 60, 30]) * (1 - k) + np.array([235, 110, 30]) * k
        col = mantle
        col = np.where((r < 0.546)[..., None], np.array([255, 150, 30]), col)
        col = np.where((r < 0.19)[..., None], np.array([255, 235, 140]), col)
        col = np.where((r > 0.975)[..., None], np.array([110, 80, 55]), col)
        img[..., :3] = col
        img[..., 3] = np.clip((1.0 - r) * R + 0.5, 0, 1) * 255
        _cache["sec"] = Image.fromarray(img.astype(np.uint8), "RGBA")
    return _cache["sec"]


def draw_earth(img, cut=1.0, gt=0.0):
    """cut: 0 = globe surface, 1 = full cross-section (wipe left→right)"""
    g = globe_img()
    if cut < 1:
        paste_c(img, g, CX, CY)
    if cut > 0:
        sec = section_img()
        if cut < 1:
            m = Image.new("L", sec.size, 0)
            ImageDraw.Draw(m).rectangle((0, 0, int(sec.size[0] * cut), sec.size[1]), fill=255)
            a = sec.getchannel("A")
            sec = sec.copy()
            sec.putalpha(Image.fromarray(np.minimum(np.array(a), np.array(m))))
        paste_c(img, sec, CX, CY)
    # sky glow / atmosphere ring
    d = ImageDraw.Draw(img)
    d.ellipse((CX - R - 6, CY - R - 6, CX + R + 6, CY + R + 6), outline=(120, 190, 255), width=3)


def labels(img, a):
    if a <= 0.02:
        return
    for txt, y in (("Kruste", TOP + 30), ("Mantel", CY - R * 0.75), ("äußerer Kern", CY - R * 0.36),
                   ("innerer Kern", CY)):
        text(img, txt, 30, CX + 110 if y != CY else CX + 150, y, fill=(255, 255, 255), stroke=4, path=FONT_XB,
             alpha=a, anchor="lm")


def tunnel(img, dig=1.0, a=1.0):
    if dig <= 0 or a <= 0.02:
        return
    layer = Image.new("RGBA", (E.W, E.H))
    d = ImageDraw.Draw(layer)
    y1 = TOP - 4 + (2 * R + 8) * dig
    d.rectangle((CX - 13, TOP - 4, CX + 13, y1), fill=(14, 10, 22, int(255 * a)))
    d.line((CX - 13, TOP - 4, CX - 13, y1), fill=(200, 200, 220, int(200 * a)), width=2)
    d.line((CX + 13, TOP - 4, CX + 13, y1), fill=(200, 200, 220, int(200 * a)), width=2)
    img.paste(layer, (0, 0), layer)
    if dig < 1:      # drill bit
        dd = ImageDraw.Draw(img)
        dd.polygon([(CX - 18, y1 - 10), (CX + 18, y1 - 10), (CX, y1 + 22)], fill=(200, 200, 210))


def faller(img, y, gt, spin=0.0, a=1.0, h=96):
    spr = person_sprite(h, SKIN, arms_up=1.0)
    if spin:
        spr = spr.rotate(spin, resample=Image.BICUBIC, expand=True)
    paste_c(img, spr, CX, y, a)


def speed_lines(img, y, v, gt, up=False):
    if v < 0.05:
        return
    d = ImageDraw.Draw(img)
    for k in range(4):
        x = CX + (k - 1.5) * 22
        o = (gt * 900 + k * 37) % 60
        L = 30 + 90 * v
        y0 = y - 40 - o if not up else y + 40 + o
        y1 = y0 - L if not up else y0 + L
        d.line((x, y0, x, y1), fill=(255, 255, 255), width=3)


def timer(img, minutes, a=1.0, suffix=""):
    if a <= 0.02:
        return
    rrect(img, (CX - 200, 1150, CX + 200, 1260), 30, (0, 0, 0, int(160 * a)), outline=(255, 255, 255, int(90 * a)),
          width=2)
    text(img, f"{int(minutes)} min{suffix}", 64, CX, 1205, alpha=a, stroke=5)


# ------------------------------------------------------------------ scenes
def sc_hook(img, sc, t, gt):
    brand(img, t, gt)
    p = back_out(prog(t, 0.0, 0.5))
    g = globe_img()
    if p > 0.03:
        gs = g.resize((max(1, int(g.size[0] * p)), max(1, int(g.size[1] * p))), Image.BILINEAR)
        paste_c(img, gs, CX, CY)
    bob = abs(math.sin(gt * 4)) * 14
    faller(img, TOP - 36 - bob, gt, a=ease_out(prog(t, 0.3, 0.3)))
    t_s = wt(sc, "springst")
    q = 1 + 0.1 * math.sin(gt * 6)
    text(img, "?", 220 * q, CX + 260, CY - 240, fill=HI, stroke=10, sfill=(30, 20, 60),
         alpha=ease_out(prog(t, 0.6, 0.3)), rotate=12)
    if t > t_s - 0.4:
        text(img, "Was passiert?", 64, CX, 1205, fill=HI, stroke=7, alpha=ease_out(prog(t, t_s - 0.4, 0.3)),
             scale=back_out(prog(t, t_s - 0.4, 0.4)))


def sc_loch(img, sc, t, gt):
    t_l, t_q, t_13, t_luft, t_sp = (wt(sc, "Loch"), wt(sc, "quer"), wt(sc, "13.000"), wt(sc, "Luft"),
                                    wt(sc, "springst"))
    cut = ease_io(prog(t, t_l - 0.3, 0.9))
    draw_earth(img, cut, gt)
    labels(img, ease_out(prog(t, t_l + 0.4, 0.4)) * (1 - prog(t, t_13 - 0.2, 0.4)))
    dig = ease_io(prog(t, t_q - 0.1, 1.6))
    tunnel(img, dig)
    if dig >= 1:
        d = ImageDraw.Draw(img)
        xb = CX + R + 40
        d.line((xb, TOP, xb, BOT), fill=HI, width=5)
        d.line((xb - 14, TOP, xb + 14, TOP), fill=HI, width=5)
        d.line((xb - 14, BOT, xb + 14, BOT), fill=HI, width=5)
    counter(img, CX, E.fmt_int(12742 * ease_out(prog(t, t_13 - 0.3, 1.0))) + " km", "einmal quer durch die Erde",
            HI, ease_out(prog(t, t_13 - 0.3, 0.3)) * (1 - prog(t, t_sp - 0.2, 0.3)), y=1190)
    if t > t_luft - 0.2:
        a = ease_out(prog(t, t_luft - 0.2, 0.3))
        rrect(img, (CX - 300, TOP - 120, CX - 60, TOP - 66), 27, (40, 40, 70, int(230 * a)),
              outline=(255, 255, 255, int(200 * a)), width=2)
        text(img, "keine Luft", 34, CX - 180, TOP - 93, alpha=a, path=FONT_XB)
    # person: stands, then jumps in
    if t < t_sp:
        faller(img, TOP - 36 - abs(math.sin(gt * 4)) * 6, gt)
    else:
        u = t - t_sp
        y = TOP - 36 - 80 * math.sin(min(u, 0.5) / 0.5 * math.pi) + max(0, u - 0.5) ** 2 * 120
        faller(img, y, gt, spin=-30 * min(1, u * 2))
        stamp(img, "SPRUNG!", t, t_sp + 0.05, cx=CX + 240, cy=TOP - 90, size=64, rot=-8)


def fall_y(phase):
    """position in the tunnel for the oscillation phase (0 = top, pi = bottom)"""
    return CY - R * math.cos(phase)


def sc_fall(img, sc, t, gt):
    draw_earth(img, 1.0, gt)
    tunnel(img, 1.0)
    dur = sc["dur"]
    ph = math.pi / 2 * clamp(t / dur) ** 1.0
    y = fall_y(ph)
    v = math.sin(ph)
    speed_lines(img, y, v, gt)
    faller(img, y, gt, spin=math.sin(gt * 3) * 25 - 30)
    t_s = wt(sc, "schwerelos")
    if t > t_s - 0.3:
        a = ease_out(prog(t, t_s - 0.3, 0.3))
        fl = 10 * math.sin(gt * 4)
        rrect(img, (CX + 50, y - 50 + fl, CX + 330, y + 4 + fl), 27, (255, 255, 255, int(235 * a)))
        text(img, "schwerelos!", 36, CX + 190, y - 23 + fl, fill=(30, 20, 60), alpha=a, path=FONT_XB)
    t_i = wt(sc, "immer")
    if t > t_i - 0.2:
        text(img, "immer schneller", 40, CX - 220, y, fill=HI, stroke=5, path=FONT_XB,
             alpha=ease_out(prog(t, t_i - 0.2, 0.3)) * (1 - prog(t, t_s - 0.6, 0.3)))
    timer(img, 19 * clamp(t / dur), ease_out(prog(t, 0.0, 0.3)))


def sc_ankunft(img, sc, t, gt):
    draw_earth(img, 1.0, gt)
    tunnel(img, 1.0)
    t_an, t_st, t_z, t_h = wt(sc, "an"), wt(sc, "stehen"), wt(sc, "zurück"), wt(sc, "hin")
    arr = t_an + 0.2
    if t < arr:
        ph = math.pi / 2 + math.pi / 2 * clamp(t / arr)
        y = fall_y(ph)
        speed_lines(img, y, math.sin(ph), gt)
        faller(img, y, gt, spin=-30 + 10 * math.sin(gt * 3))
        mins = 19 + 19 * clamp(t / arr)
    elif t < t_z:
        y = BOT + 36
        faller(img, y + 4 * math.sin(gt * 3), gt, spin=180)
        mins = 38
        text(img, "kurz Stopp!", 40, CX + 190, BOT + 10, fill=HI, stroke=5, path=FONT_XB,
             alpha=ease_out(prog(t, t_st - 0.3, 0.3)))
    else:
        # back and forth: fast-forwarded oscillation (one full cycle ≈ 1.8 s on screen)
        u = t - t_z
        ph = math.pi + u * 2 * math.pi / 1.8
        y = fall_y(ph)
        up = math.sin(ph) < 0
        speed_lines(img, y, abs(math.sin(ph)), gt, up=up)
        faller(img, y, gt, spin=180 * (0.5 + 0.5 * math.cos(ph)))
        mins = 38
    timer(img, mins, 1.0, suffix=" " if t < t_h else "")
    if t > t_an - 0.1:
        burst(img, CX, BOT, t, t_an, color=HI, rad=160)
    if t > t_h - 0.2:
        a = ease_out(prog(t, t_h - 0.2, 0.3))
        q = 1 + 0.08 * math.sin(gt * 6)
        text(img, "∞", 150 * q, CX + 260, CY, fill=HI, stroke=8, sfill=(30, 20, 60), alpha=a)
        text(img, "hin & her", 40, CX + 260, CY + 110, fill=(255, 255, 255), stroke=5, path=FONT_XB, alpha=a)


def thermo(img, x, y, frac, a=1.0):
    if a <= 0.02:
        return
    d = ImageDraw.Draw(img)
    rrect(img, (x - 18, y - 120, x + 18, y + 20), 18, (255, 255, 255, int(230 * a)))
    rrect(img, (x - 9, y - 110 + 110 * (1 - frac), x + 9, y + 10), 9, (255, 70, 50, int(255 * a)))
    d.ellipse((x - 28, y, x + 28, y + 56), fill=(255, 70, 50))


def sun_icon(img, x, y, d, gt, a=1.0):
    s = SS(d * 1.6, d * 1.6)
    c = d * 0.8
    for i in range(10):
        ang = i / 10 * 2 * math.pi + gt
        s.poly([(c + d * 0.5 * math.cos(ang - 0.15), c + d * 0.5 * math.sin(ang - 0.15)),
                (c + d * 0.78 * math.cos(ang), c + d * 0.78 * math.sin(ang)),
                (c + d * 0.5 * math.cos(ang + 0.15), c + d * 0.5 * math.sin(ang + 0.15))], (255, 190, 40, 255))
    s.ell(c, c, d * 0.48, d * 0.48, (255, 160, 20, 255))
    paste_c(img, s.img(), x, y, a)


def sc_echt(img, sc, t, gt):
    t_t, t_12, t_180, t_k, t_s = (wt(sc, "tiefste"), wt(sc, "12"), wt(sc, "180"), wt(sc, "Erdkern"),
                                  wt(sc, "Sonne"))
    draw_earth(img, 1.0, gt)
    tunnel(img, 1.0, a=1 - prog(t, 0.0, 0.5))
    # real borehole: 12,3 km of 12.742 km → about 0,1 % of the way (0,3 px at this scale)
    d = ImageDraw.Draw(img)
    if t > t_t - 0.3:
        a = ease_out(prog(t, t_t - 0.3, 0.4))
        d.line((CX, TOP - 2, CX, TOP + 3), fill=(255, 60, 60), width=4)
        r = 26 + 4 * math.sin(gt * 6)
        d.ellipse((CX - r, TOP - r, CX + r, TOP + r), outline=HI, width=5)
        # magnifier box
        bx0, by0, bx1, by1 = CX - 330, 250, CX + 330, 400
        rrect(img, (bx0, by0, bx1, by1), 30, (0, 0, 0, int(190 * a)), outline=(255, 226, 60, int(255 * a)), width=4)
        d.line((CX, TOP - r, CX - 60, by1), fill=HI, width=3)
        text(img, "tiefstes Bohrloch: 12,3 km", 40, CX, 300, alpha=a, path=FONT_XB)
        text(img, "= nur 0,1 % des Weges", 34, CX, 352, fill=HI, alpha=a, path=FONT_XB)
    # temperatures
    if t > t_180 - 0.4 and t < t_k - 0.1:
        a = ease_out(prog(t, t_180 - 0.4, 0.3))
        thermo(img, CX + R + 30, TOP + 80, ease_out(prog(t, t_180 - 0.4, 0.8)) * 0.35, a)
        counter(img, CX, E.fmt_int(180 * ease_out(prog(t, t_180 - 0.4, 0.8))) + " °C", "unten im Bohrloch", HI, a,
                y=1190)
    if t > t_k - 0.2:
        a = ease_out(prog(t, t_k - 0.2, 0.4))
        pul = 1 + 0.1 * math.sin(gt * 8)
        glow = Image.new("RGBA", (E.W, E.H))
        gd = ImageDraw.Draw(glow)
        for k in range(6):
            rr = R * 0.19 * pul * (1 + k * 0.25)
            gd.ellipse((CX - rr, CY - rr, CX + rr, CY + rr), fill=(255, 240, 160, int(60 * a)))
        img.paste(glow, (0, 0), glow)
        burst(img, CX, CY, t, t_k, color=HI, rad=200)
        counter(img, CX, "5.000–6.000 °C", "im Erdkern (geschätzt)", HI, a, y=1190, size=60)
    if t > t_s - 0.9:
        a = ease_out(prog(t, t_s - 0.9, 0.4))
        sun_icon(img, CX + 250, CY - 40, 150, gt, a)
        text(img, "≈ wie die", 32, CX + 250, CY + 70, fill=(255, 255, 255), stroke=4, path=FONT_XB, alpha=a)
        text(img, "Sonnenoberfläche", 32, CX + 250, CY + 108, fill=(255, 255, 255), stroke=4, path=FONT_XB, alpha=a)


def sc_outro(img, sc, t, gt):
    brand(img, t, gt)
    p = back_out(prog(t, 0.0, 0.5))
    cx, cy = CX, 620
    if p > 0.05:
        layer = Image.new("RGBA", (E.W, E.H))
        d = ImageDraw.Draw(layer)
        bw, bh = 380 * p, 150 * p
        d.rounded_rectangle((cx - bw, cy - bh, cx + bw, cy + bh), 50, fill=(255, 255, 255, 245))
        d.polygon([(cx - 60 * p, cy + bh - 2), (cx - 130 * p, cy + bh + 80 * p), (cx + 10 * p, cy + bh - 2)],
                  fill=(255, 255, 255, 245))
        img.paste(layer, (0, 0), layer)
        text(img, "Würdest du springen?", 52, cx, cy - 40, fill=(40, 40, 70), scale=p)
        blink = "|" if int(gt * 3) % 2 == 0 else " "
        text(img, "Ja / Nein " + blink, 56, cx, cy + 50, fill=(255, 120, 0), scale=p)
    g = globe_img().resize((220, 220), Image.BILINEAR)
    paste_c(img, g, CX - 180, 1010 + 10 * math.sin(gt * 3), ease_out(prog(t, 0.2, 0.4)))
    faller(img, 1010 - 10 * math.sin(gt * 3), gt, spin=20 * math.sin(gt * 4), a=ease_out(prog(t, 0.3, 0.4)), h=110)
    t_s = wt(sc, "Schreib's")
    if t > t_s:
        a = ease_out(prog(t, t_s, 0.4))
        ax = 830 + 20 * math.sin(gt * 8)
        dd = ImageDraw.Draw(img)
        dd.line((ax - 110, 1190, ax, 1190), fill=HI, width=14)
        dd.polygon([(ax + 40, 1190), (ax - 5, 1155), (ax - 5, 1225)], fill=HI)
        text(img, "Schreib's uns!", 40, ax - 140, 1190, alpha=a, stroke=5, path=FONT_XB, anchor="rm")


E.setup(
    here=HERE, out="durch_die_erde_springen.mp4",
    name_l="", name_r="", col_l=HI, col_r=HI,
    bg_l=((4, 6, 20), (16, 26, 64)), bg_r=((4, 6, 20), (16, 26, 64)),
    scenes=["hook", "loch", "fall", "ankunft", "echt", "outro"],
    draw=dict(hook=sc_hook, loch=sc_loch, fall=sc_fall, ankunft=sc_ankunft, echt=sc_echt, outro=sc_outro),
    sub_map=[],
    score=[],
    ticks=[(1, "13.000", 1, 1.0), (3, "38", 1, 0.8)],
    chimes=[],
)

if __name__ == "__main__":
    E.main()

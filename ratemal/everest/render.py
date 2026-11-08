#!/usr/bin/env python3
"""Rate mal: Mount Everest vs. Marianengraben – animated German TikTok comparison."""
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tiere"))
import engine as E  # noqa: E402
from engine import (CXL, CXR, SPLIT, NUM_Y, SS, back_out, clamp, counter, ease_io, ease_out,  # noqa: E402
                    header, panel_labels, paste_c, prog, stamp, burst, text, vs_badge, wt, rrect, crown, winner,
                    brand, person_icon, FONT_XB)

C_L = (225, 235, 250)     # Everest (Eis)
C_R = (40, 175, 255)      # Graben (Tiefsee)
ROCK = (110, 105, 120)
SNOW = (245, 248, 255)
WATER = (20, 90, 170)
DEEP = (6, 30, 70)

# cross-section (to scale): 0.03 px per metre
K = 0.03
SEA_Y = 700
H_EV = 8849 * K          # 265 px
D_TR = 10935 * K         # 328 px
FLOOR_Y = SEA_Y + 4000 * K   # surrounding sea floor (≈ 4 km)
BOT_Y = SEA_Y + D_TR


def mountain_sprite(w, h, snow=True):
    s = SS(w + 4, h + 4)
    s.poly([(2, h + 2), (w * 0.52 + 2, 2), (w + 2, h + 2)], ROCK + (255,))
    s.poly([(w * 0.52 + 2, 2), (w * 0.78 + 2, h * 0.55), (w + 2, h + 2), (w * 0.6, h + 2)], (90, 85, 100, 255))
    s.poly([(w * 0.08, h + 2), (w * 0.25, h * 0.45), (w * 0.42, h + 2)], (125, 120, 135, 255))
    if snow:
        s.poly([(w * 0.52 + 2, 2), (w * 0.62, h * 0.2), (w * 0.56, h * 0.17), (w * 0.5, h * 0.24),
                (w * 0.45, h * 0.18), (w * 0.4, h * 0.22)], SNOW + (255,))
    return s.img()


def sub_sprite(w):
    h = w * 0.5
    s = SS(w + 4, h + 4)
    s.ell(w * 0.5, h * 0.62, w * 0.45, h * 0.32, (255, 200, 40, 255))
    s.rect(w * 0.42, h * 0.12, w * 0.62, h * 0.4, 6, (255, 200, 40, 255))
    for k in range(3):
        s.ell(w * (0.3 + 0.18 * k), h * 0.62, w * 0.06, w * 0.06, (60, 160, 230, 255))
    s.poly([(w * 0.02, h * 0.5), (w * 0.12, h * 0.62), (w * 0.02, h * 0.75)], (230, 150, 30, 255))
    return s.img()


def water_panel(img, top, a=1.0):
    """right panel: water from `top` downwards"""
    layer = Image.new("RGBA", (E.W - SPLIT, E.H - int(top)))
    d = ImageDraw.Draw(layer)
    hgt = layer.size[1]
    for y in range(0, hgt, 6):
        k = y / max(1, 640)
        c = tuple(int(WATER[i] * (1 - min(1, k)) + DEEP[i] * min(1, k)) for i in range(3))
        d.rectangle((0, y, E.W, y + 6), fill=c + (int(230 * a),))
    img.paste(layer, (SPLIT, int(top)), layer)


def waves(img, y, gt, a=1.0):
    d = ImageDraw.Draw(img)
    pts = [(x, y + 6 * math.sin(x / 40 + gt * 3)) for x in range(SPLIT, E.W + 1, 10)]
    d.line(pts, fill=(160, 220, 255), width=int(6 * a) or 1)


def section(img, gt, ev=1.0, tr=1.0, show_mountain=True):
    """to-scale cross-section: Everest (left) and trench (right); ev/tr = grow factors 0..1"""
    d = ImageDraw.Draw(img)
    # left: ground below sea level
    d.rectangle((0, SEA_Y, SPLIT, 1045), fill=(70, 50, 40))
    # right: water + sea floor with trench
    water_panel(img, SEA_Y)
    waves(img, SEA_Y, gt)
    fl = SEA_Y + (FLOOR_Y - SEA_Y)
    bot = fl + (BOT_Y - fl) * tr
    floor = [(SPLIT, fl), (CXR - 220, fl), (CXR - 165, bot), (CXR + 165, bot), (CXR + 220, fl), (E.W, fl),
             (E.W, 1045), (SPLIT, 1045)]
    d.polygon(floor, fill=(40, 34, 40))
    d.line([(SPLIT, fl), (CXR - 220, fl), (CXR - 165, bot), (CXR + 165, bot), (CXR + 220, fl), (E.W, fl)],
           fill=(90, 80, 90), width=5)
    # sea level line across both panels
    for x in range(20, SPLIT, 34):
        d.line((x, SEA_Y, x + 18, SEA_Y), fill=(200, 230, 255), width=3)
    text(img, "Meeresspiegel", 26, 110, SEA_Y + 26, fill=(200, 230, 255), path=FONT_XB)
    if show_mountain and ev > 0.01:
        h = H_EV * ev
        paste_c(img, mountain_sprite(330, max(4, h)), CXL, SEA_Y + 2, anchor="b")
    return bot


def sc_hook(img, sc, t, gt):
    header(img, gt, "", t)
    brand(img, t, gt)
    panel_labels(img, t)
    p = back_out(prog(t, 0.0, 0.45))
    d = ImageDraw.Draw(img)
    # right: ocean with a deep dark trench + diving submarine
    water_panel(img, 560, ease_out(prog(t, 0.05, 0.3)))
    waves(img, 560, gt)
    q = ease_out(prog(t, 0.1, 0.8))
    d.polygon([(CXR - 150, 1000), (CXR - 40, 560 + 440 * (1 - q) + 0), (CXR + 40, 560 + 440 * (1 - q)),
               (CXR + 150, 1000)], fill=(30, 26, 34))
    d.polygon([(CXR - 60, 1000), (CXR, 1000 - 380 * q), (CXR + 60, 1000)], fill=(4, 8, 20))
    paste_c(img, sub_sprite(110), CXR + 40, 600 + 250 * ease_io(prog(t, 0.2, 2.6)), ease_out(prog(t, 0.2, 0.3)))
    if p > 0.05:
        paste_c(img, mountain_sprite(400 * p, 420 * p), CXL, 1000, anchor="b")
    vs_badge(img, t, ease_out(prog(t, 0.35, 0.3)), y=760)
    t_g = wt(sc, "größer")
    if t > t_g:
        text(img, "Was ist größer?", 52, SPLIT, 1080, fill=E.C_HI, stroke=6, alpha=ease_out(prog(t, t_g, 0.3)),
             scale=back_out(prog(t, t_g, 0.4)))


def sc_besucher(img, sc, t, gt):
    header(img, gt, "RUNDE 1 · BESUCHER", t)
    panel_labels(img, t)
    t_7, t_d = wt(sc, "siebentausend"), wt(sc, "Dutzend")
    # left: 70 icons = 7.000 people (1 icon = 100)
    n = int(70 * ease_out(prog(t, t_7 - 0.3, 1.2)))
    ic = person_icon(56, C_L)
    for k in range(n):
        r, c = divmod(k, 10)
        paste_c(img, ic, 72 + c * 44, 470 + r * 66)
    # right: dark water, submarine, only a fraction of one icon (a few dozen people)
    water_panel(img, 440, ease_out(prog(t, 0.1, 0.3)))
    paste_c(img, sub_sprite(140), CXR, 520 + 260 * ease_io(prog(t, 0.3, 3.5)), ease_out(prog(t, 0.3, 0.3)))
    if t > t_d - 0.3:
        a = ease_out(prog(t, t_d - 0.3, 0.4))
        big = person_icon(120, (255, 255, 255))
        w, h = big.size
        ghost = big.copy()
        ghost.putalpha(ghost.getchannel("A").point(lambda v: v // 5))
        paste_c(img, ghost, CXR, 880, a)
        part = big.crop((0, int(h * 0.7), w, h))
        paste_c(img, part, CXR, 880 + h * 0.35, a)
    if t > t_7:
        text(img, "1 Figur = 100 Menschen", 30, SPLIT, 990, fill=(230, 230, 240), path=FONT_XB, stroke=4,
             alpha=ease_out(prog(t, t_7, 0.3)))
    counter(img, CXL, "über " + E.fmt_int(7000 * ease_out(prog(t, t_7 - 0.3, 1.2))), "auf dem Gipfel", C_L,
            ease_out(prog(t, t_7 - 0.3, 0.3)), size=60)
    counter(img, CXR, "paar Dutzend", "ganz unten", C_R, ease_out(prog(t, t_d - 0.3, 0.3)), size=54)


def arrows(img, cx, cy, r, length, width, color, gt, wob=0.0):
    d = ImageDraw.Draw(img)
    for i in range(8):
        a = i / 8 * 2 * math.pi + 0.39
        ca, sa = math.cos(a), math.sin(a)
        r0 = r + 14 + 6 * math.sin(gt * 8 + i) * wob
        x0, y0 = cx + (r0 + length) * ca, cy + (r0 + length) * sa
        x1, y1 = cx + r0 * ca, cy + r0 * sa
        d.line((x0, y0, x1 + width * 0.8 * ca, y1 + width * 0.8 * sa), fill=color, width=int(width))
        px, py = -sa, ca
        d.polygon([(x1, y1), (x1 + width * 1.6 * ca + width * 1.3 * px, y1 + width * 1.6 * sa + width * 1.3 * py),
                   (x1 + width * 1.6 * ca - width * 1.3 * px, y1 + width * 1.6 * sa - width * 1.3 * py)],
                  fill=color)


def sc_druck(img, sc, t, gt):
    header(img, gt, "RUNDE 2 · DRUCK", t)
    panel_labels(img, t)
    t_d, t_1000 = wt(sc, "Drittel"), wt(sc, "tausendmal")
    cy = 690
    water_panel(img, 440, ease_out(prog(t, 0.1, 0.3)))
    paste_c(img, mountain_sprite(260, 200), CXL, 1000, ease_out(prog(t, 0.1, 0.3)), anchor="b")
    # left: thin air → small arrows, a relaxed ball
    pl = ease_out(prog(t, t_d - 0.3, 0.6))
    d = ImageDraw.Draw(img)
    rl = 70 + 4 * math.sin(gt * 3)
    d.ellipse((CXL - rl, cy - rl, CXL + rl, cy + rl), fill=(255, 120, 120), outline=(255, 255, 255), width=5)
    if pl > 0.02:
        arrows(img, CXL, cy, rl, 40 * pl, 6, (230, 240, 255), gt)
    # right: crushing pressure → huge arrows, squeezed ball
    pr = ease_out(prog(t, t_1000 - 0.3, 0.7))
    sq = 1 - 0.25 * pr + 0.03 * math.sin(gt * 20) * pr
    rr = 70 * sq
    d.ellipse((CXR - rr * 1.1, cy - rr * 0.9, CXR + rr * 1.1, cy + rr * 0.9), fill=(255, 120, 120),
              outline=(255, 255, 255), width=5)
    if pr > 0.02:
        arrows(img, CXR, cy, rr, 120 * pr, 16, (255, 226, 60), gt, wob=1.0)
    counter(img, CXL, "1/3", "vom Luftdruck bei uns", C_L, ease_out(prog(t, t_d - 0.3, 0.3)))
    counter(img, CXR, "über 1.000×", "Druck wie bei uns", C_R, ease_out(prog(t, t_1000 - 0.3, 0.3)), size=60)
    burst(img, CXR, cy, t, t_1000 + 0.2, color=E.C_HI, rad=200)


def sc_groesse(img, sc, t, gt):
    header(img, gt, "RUNDE 3 · GRÖSSE", t)
    panel_labels(img, t)
    t_e, t_11 = wt(sc, "achttausendachthundertneunundvierzig"), wt(sc, "elftausend")
    ev = ease_out(prog(t, t_e - 0.4, 1.4))
    tr = ease_out(prog(t, t_11 - 0.4, 1.2))
    bot = section(img, gt, ev=max(0.02, ev), tr=tr)
    d = ImageDraw.Draw(img)
    if ev > 0.02:
        y = SEA_Y - H_EV * ev
        d.line((CXL + 190, SEA_Y, CXL + 190, y), fill=C_L, width=5)
        d.line((CXL + 175, y, CXL + 205, y), fill=C_L, width=5)
    if tr > 0.02:
        d.line((CXR + 195, SEA_Y, CXR + 195, bot), fill=C_R, width=5)
        d.line((CXR + 180, bot, CXR + 210, bot), fill=C_R, width=5)
    counter(img, CXL, E.fmt_int(8849 * ev) + " m", "hoch", C_L, ease_out(prog(t, t_e - 0.4, 0.3)))
    counter(img, CXR, "≈ " + E.fmt_int(10935 * tr) + " m", "tief", C_R, ease_out(prog(t, t_11 - 0.4, 0.3)),
            size=62)
    if t > t_11 + 1.0:
        text(img, "maßstabsgetreu", 30, SPLIT, 1012, fill=(230, 230, 240), path=FONT_XB, stroke=4,
             alpha=ease_out(prog(t, t_11 + 1.0, 0.3)))


def sc_finale(img, sc, t, gt):
    t_k = wt(sc, "Klarer")
    header(img, gt, "FINALE · PASST ER REIN?", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    panel_labels(img, t, a=1 - prog(t, t_k - 0.1, 0.3))
    t_ev, t_2 = wt(sc, "Everest"), wt(sc, "Kilometer")
    section(img, gt, show_mountain=False)
    # move the mountain into the trench (to scale)
    p = ease_io(prog(t, t_ev - 0.1, 1.8))
    x = CXL + (CXR - CXL) * p
    yb = SEA_Y + 2 + (BOT_Y - SEA_Y) * p - math.sin(p * math.pi) * 120
    paste_c(img, mountain_sprite(300, H_EV), x, yb, anchor="b")
    d = ImageDraw.Draw(img)
    if t > t_2 - 0.6:
        a = ease_out(prog(t, t_2 - 0.6, 0.4))
        peak = BOT_Y - H_EV
        xb = CXR + 190
        d.line((xb, SEA_Y, xb, peak), fill=E.C_HI, width=6)
        d.line((xb - 16, SEA_Y, xb + 16, SEA_Y), fill=E.C_HI, width=6)
        d.line((xb - 16, peak, xb + 16, peak), fill=E.C_HI, width=6)
        text(img, "über 2 km Wasser!", 42, CXR - 20, SEA_Y - 70, fill=E.C_HI, stroke=5, alpha=a,
             scale=back_out(prog(t, t_2 - 0.6, 0.4)))
        counter(img, CXR, "2.086 m", "Wasser über dem Gipfel", C_R, a, size=62)
    counter(img, CXL, "8.849 m", "Everest", C_L, ease_out(prog(t, 0.2, 0.3)) * (1 - prog(t, t_k - 0.1, 0.3)))
    if t > t_k:
        crown(img, CXR, 520, prog(t, t_k, 0.5), size=0.6)
        winner(img, t, t_k, "MARIANENGRABEN", cy=420)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, mountain_sprite(170, 150), x, y, a)

    def mr(im, x, y, a, g):
        paste_c(im, sub_sprite(150), x, y, a)

    brand(img, t, gt)
    E.outro(img, sc, t, gt, ml, mr, line1="Richtig geraten?", line2="Schreib's uns!")


E.setup(
    here=HERE, out="everest_vs_marianengraben.mp4",
    name_l="EVEREST", name_r="MARIANENGRABEN", short_r="GRABEN", col_l=C_L, col_r=C_R,
    bg_l=((16, 30, 66), (70, 110, 170)), bg_r=((2, 8, 26), (4, 40, 90)),
    scenes=["hook", "besucher", "druck", "groesse", "finale", "outro"],
    draw=dict(hook=sc_hook, besucher=sc_besucher, druck=sc_druck, groesse=sc_groesse, finale=sc_finale,
              outro=sc_outro),
    sub_map=[
        (("siebentausend",), "7.000"), (("tausendmal",), "1.000-mal"),
        (("achttausendachthundertneunundvierzig",), "8.849"), (("elftausend",), "11.000"),
        (("eins",), "1"), (("zwei",), "2"), (("drei",), "3"),
    ],
    score=[(1, "Punkt", 1, "L"), (2, "Punkt", 1, "R"), (3, "Punkt", 1, "R"), (4, "Sieger", 1, "R")],
    ticks=[(1, "siebentausend", 1, 1.2), (3, "elftausend", 1, 1.2)],
)

if __name__ == "__main__":
    E.main()

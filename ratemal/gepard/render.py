#!/usr/bin/env python3
"""Rate mal: Mensch vs. Gepard – animated German TikTok comparison."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tiere"))
import engine as E  # noqa: E402
from engine import (CXL, CXR, SPLIT, NUM_Y, SS, back_out, clamp, counter, ease_io, ease_out,  # noqa: E402
                    header, panel_labels, paste_c, person_sprite, person_icon, prog, stamp, burst, text, vs_badge,
                    wt, rrect, crown, winner, brand, FONT_XB)

C_L = (80, 190, 255)      # Mensch
C_R = (255, 190, 60)      # Gepard
FUR = (232, 178, 70, 255)
FUR_L = (248, 222, 160, 255)
SPOT = (55, 35, 20, 255)
HUMAN = (230, 235, 245)


def cheetah_sprite(h, phase=0.0, run=1.0, lie=0.0):
    """side view facing right; phase drives the gallop, lie=1 → lying down"""
    w = h * 2.0
    s = SS(w, h * 1.1)
    by = h * (0.42 + 0.3 * lie)            # body centre y
    sw = math.sin(phase) * run * (1 - lie)
    # tail
    s.thick([(w * 0.2, by - h * 0.02), (w * 0.09, by + h * 0.08 - 0.1 * h * sw), (w * 0.02, by - h * 0.05)],
            [h * 0.07, h * 0.055, h * 0.05], FUR)
    s.ell(w * 0.025, by - h * 0.05, h * 0.04, h * 0.04, SPOT)
    # legs (back pair + front pair, swinging opposite)
    if lie < 0.5:
        for x, sgn, col in ((0.3, 1, FUR), (0.36, -1, FUR), (0.68, -1, FUR), (0.74, 1, FUR)):
            ang = 0.55 * sw * sgn
            x0, y0 = w * x, by + h * 0.1
            L = h * 0.5
            s.thick([(x0, y0), (x0 + L * 0.5 * math.sin(ang), y0 + L * 0.5 * math.cos(ang)),
                     (x0 + L * math.sin(ang * 1.4), y0 + L * math.cos(ang * 1.4))],
                    [h * 0.09, h * 0.06, h * 0.05], col)
    else:
        s.rect(w * 0.62, by + h * 0.1, w * 0.92, by + h * 0.18, h * 0.04, FUR)
    # body
    s.ell(w * 0.5, by, w * 0.3, h * 0.17, FUR)
    s.ell(w * 0.52, by + h * 0.07, w * 0.22, h * 0.08, FUR_L)
    rr = random.Random(4)
    for _ in range(22):
        sx = w * rr.uniform(0.25, 0.75)
        sy = by + h * rr.uniform(-0.13, 0.08)
        if ((sx - w * 0.5) / (w * 0.3)) ** 2 + ((sy - by) / (h * 0.17)) ** 2 < 0.85:
            s.ell(sx, sy, h * 0.025, h * 0.022, SPOT)
    # head
    hx, hy = w * 0.85, by - h * 0.12 + (0.06 * h * abs(sw))
    s.ell(hx, hy, h * 0.14, h * 0.12, FUR)
    s.ell(hx - h * 0.08, hy - h * 0.11, h * 0.04, h * 0.045, FUR)          # ear
    s.ell(hx + h * 0.1, hy + h * 0.04, h * 0.065, h * 0.05, FUR_L)        # muzzle
    s.ell(hx + h * 0.15, hy + h * 0.02, h * 0.025, h * 0.02, SPOT)        # nose
    s.ell(hx + h * 0.03, hy - h * 0.03, h * 0.022, h * 0.026, (20, 15, 10, 255))   # eye
    s.line([(hx + h * 0.04, hy - h * 0.0), (hx + h * 0.07, hy + h * 0.08)], SPOT, h * 0.02)  # tear mark
    return s.img()


def runner(img, cx, cy_bottom, h, gt, speed=1.0, a=1.0):
    bob = abs(math.sin(gt * 9 * speed)) * h * 0.06
    paste_c(img, person_sprite(h, HUMAN, arms_up=0.5 + 0.5 * math.sin(gt * 9 * speed)), cx, cy_bottom - bob, a,
            anchor="b")


def speed_lines(img, x, y, length, gt, color=(255, 255, 255), n=4):
    d = ImageDraw.Draw(img)
    for k in range(n):
        o = (gt * 600 + k * 70) % length
        yy = y + (k - n / 2) * 22
        d.line((x - o, yy, x - o - 50, yy), fill=color, width=4)


def sc_hook(img, sc, t, gt):
    header(img, gt, "", t)
    brand(img, t, gt)
    panel_labels(img, t)
    a = ease_out(prog(t, 0.0, 0.3))
    runner(img, CXL, 860, 300, gt, 1.0, a)
    paste_c(img, cheetah_sprite(200, gt * 14), CXR, 760, ease_out(prog(t, 0.1, 0.3)))
    speed_lines(img, CXR - 170, 760, 180, gt, (255, 220, 150))
    speed_lines(img, CXL - 90, 760, 120, gt, (180, 220, 255), n=3)
    vs_badge(img, t, ease_out(prog(t, 0.35, 0.3)), y=600)
    t_s = wt(sc, "schlagen")
    if t > t_s - 0.3:
        text(img, "Wer gewinnt?", 56, SPLIT, 1040, fill=E.C_HI, stroke=6, alpha=ease_out(prog(t, t_s - 0.3, 0.3)),
             scale=back_out(prog(t, t_s - 0.3, 0.4)))


def ground(img, cx, y, offset, w=400):
    d = ImageDraw.Draw(img)
    d.rectangle((cx - w / 2, y, cx + w / 2, y + 22), fill=(190, 80, 60))
    for k in range(-1, int(w / 60) + 2):
        x = cx - w / 2 + ((k * 60 - offset) % (w + 60)) - 30
        if cx - w / 2 <= x <= cx + w / 2 - 30:
            d.line((x, y + 11, x + 30, y + 11), fill=(255, 255, 255), width=3)


def progress(img, cx, y, f, color, w=380):
    d = ImageDraw.Draw(img)
    rrect(img, (cx - w / 2, y, cx + w / 2, y + 16), 8, (255, 255, 255, 70))
    rrect(img, (cx - w / 2, y, cx - w / 2 + max(16, w * f), y + 16), 8, color + (255,))
    for r in range(4):     # finish flag
        for c in range(2):
            col = (255, 255, 255) if (r + c) % 2 else (20, 20, 20)
            d.rectangle((cx + w / 2 - 8 + c * 8, y - 40 + r * 10, cx + w / 2 + c * 8, y - 30 + r * 10), fill=col)
    d.line((cx + w / 2 - 8, y - 40, cx + w / 2 - 8, y + 16), fill=(255, 255, 255), width=3)
    text(img, "0 m", 24, cx - w / 2 + 20, y + 40, path=FONT_XB)
    text(img, "100 m", 24, cx + w / 2 - 34, y + 40, path=FONT_XB)


def sc_sprint(img, sc, t, gt):
    header(img, gt, "RUNDE 1 · 100 METER", t)
    panel_labels(img, t)
    t0 = wt(sc, "Usain")
    k = 3.2 / 9.58                         # screen seconds per real second
    el = max(0.0, (t - t0) / k)
    fb, fc = clamp(el / 9.58), clamp(el / 5.95)
    gy = 800
    run_b, run_c = 0 < fb < 1, 0 < fc < 1
    ground(img, CXL, gy, (t - t0) * 330 if run_b else (3.2 * 330 if fb >= 1 else 0))
    ground(img, CXR, gy, (t - t0) * 530 if run_c else (1.99 * 530 if fc >= 1 else 0))
    runner(img, CXL, gy, 230, gt, 1.0 if run_b else 0.0)
    paste_c(img, cheetah_sprite(150, gt * 16 if run_c else 0, run=1.0 if run_c else 0.2), CXR, gy - 78)
    if run_c:
        speed_lines(img, CXR - 140, gy - 90, 110, gt, (255, 220, 150), 3)
    if run_b:
        speed_lines(img, CXL - 70, gy - 120, 90, gt, (180, 220, 255), 3)
    progress(img, CXL, 900, fb, C_L)
    progress(img, CXR, 900, fc, C_R)
    counter(img, CXL, E.fmt_dec(min(el, 9.58), 2) + " s", "Usain Bolt (Weltrekord)", C_L,
            ease_out(prog(t, t0, 0.3)), size=62)
    counter(img, CXR, E.fmt_dec(min(el, 5.95), 2) + " s", "Gepard (Rekord)", C_R, ease_out(prog(t, t0, 0.3)),
            size=62)
    if fc >= 1:
        burst(img, CXR + 190, 880, t, t0 + 5.95 * k, color=C_R, rad=120)
    if fb >= 1:
        burst(img, CXL + 190, 880, t, t0 + 9.58 * k, color=C_L, rad=120)


def gauge(img, cx, cy, R, frac, color):
    d = ImageDraw.Draw(img)
    d.pieslice((cx - R, cy - R, cx + R, cy + R), 180, 360, fill=(25, 25, 40))
    d.arc((cx - R, cy - R, cx + R, cy + R), 180, 360, fill=(255, 255, 255), width=8)
    if frac > 0:
        d.arc((cx - R + 14, cy - R + 14, cx + R - 14, cy + R - 14), 180, 180 + 180 * frac, fill=color, width=20)
    for i in range(11):
        a = math.pi + math.pi * i / 10
        d.line((cx + (R - 40) * math.cos(a), cy + (R - 40) * math.sin(a), cx + (R - 24) * math.cos(a),
                cy + (R - 24) * math.sin(a)), fill=(255, 255, 255), width=4)
    for v in (0, 50, 100):
        a = math.pi + math.pi * v / 100
        text(img, str(v), 26, cx + (R - 66) * math.cos(a), cy + (R - 66) * math.sin(a) + 6, path=FONT_XB)
    a = math.pi + math.pi * frac
    d.line((cx, cy, cx + (R - 30) * math.cos(a), cy + (R - 30) * math.sin(a)), fill=(255, 70, 70), width=9)
    d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=(255, 255, 255))


def sc_tempo(img, sc, t, gt):
    header(img, gt, "RUNDE 2 · HÖCHSTTEMPO", t)
    panel_labels(img, t)
    t_45, t_93 = wt(sc, "fünfundvierzig"), wt(sc, "dreiundneunzig")
    vb = 44.7 * ease_out(prog(t, t_45 - 0.4, 1.0))
    vc = 93 * ease_out(prog(t, t_93 - 0.4, 1.0))
    jit = 0.6 * math.sin(gt * 30)
    gauge(img, CXL, 690, 200, (vb + (jit if vb > 1 else 0)) / 100, C_L)
    gauge(img, CXR, 690, 200, (vc + (jit if vc > 1 else 0)) / 100, C_R)
    runner(img, CXL, 930, 170, gt, 0.6 + vb / 50)
    paste_c(img, cheetah_sprite(110, gt * (6 + vc / 6)), CXR, 880)
    if vc > 5:
        speed_lines(img, CXR - 120, 880, 100, gt, (255, 220, 150), 3)
    counter(img, CXL, "≈ " + str(int(round(vb))) + " km/h", "Bolt (Spitze)", C_L, ease_out(prog(t, t_45 - 0.4, 0.3)),
            size=62)
    counter(img, CXR, str(int(round(vc))) + " km/h", "wilder Gepard", C_R, ease_out(prog(t, t_93 - 0.4, 0.3)),
            size=62)
    stamp(img, "2× so schnell!", t, wt(sc, "Punkt"), cx=SPLIT, cy=520, size=80, rot=-6)


def sc_anzahl(img, sc, t, gt):
    header(img, gt, "RUNDE 3 · WIE VIELE?", t)
    panel_labels(img, t)
    t_7, t_8 = wt(sc, "siebentausend"), wt(sc, "Milliarden")
    # right: one cheetah + endangered note
    paste_c(img, cheetah_sprite(150, 0, run=0), CXR, 690, ease_out(prog(t, 0.2, 0.4)))
    if t > t_7 - 0.3:
        a = ease_out(prog(t, t_7 - 0.3, 0.3))
        rrect(img, (CXR - 120, 820, CXR + 120, 870), 25, (200, 40, 40, int(230 * a)))
        text(img, "gefährdet", 32, CXR, 845, alpha=a, path=FONT_XB)
    # left: crowd that keeps multiplying
    p = 0.12 * ease_out(prog(t, 0.3, 4.0)) + 0.88 * ease_out(prog(t, t_8 - 0.8, 1.2))
    n = int(4 + 236 * p)
    ic = person_icon(34, C_L)
    for k in range(n):
        r, c = divmod(k, 16)
        paste_c(img, ic, 50 + c * 28 + (r % 2) * 8, 470 + r * 34)
    counter(img, CXR, "≈ " + E.fmt_int(7000 * ease_out(prog(t, t_7 - 0.3, 1.0))), "in freier Wildbahn", C_R,
            ease_out(prog(t, t_7 - 0.3, 0.3)))
    counter(img, CXL, "über 8 Mrd.", "Menschen", C_L, ease_out(prog(t, t_8 - 0.3, 0.3)))


def sc_finale(img, sc, t, gt):
    t_k = wt(sc, "Klarer")
    header(img, gt, "FINALE · AUSDAUER", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    if t < t_k:
        text(img, "Finale zählt doppelt!", 34, SPLIT, 350, fill=E.C_HI, stroke=4, path=FONT_XB,
             alpha=ease_out(prog(t, 0.3, 0.3)))
    t_g, t_170, t_m, t_42 = wt(sc, "Gepard"), wt(sc, "hundertsiebzig"), wt(sc, "Marathon"), wt(sc, "zweiundvierzig")
    d = ImageDraw.Draw(img)
    # distance bars, same scale: 380 px = 42,195 km
    W = 380
    by = 900
    for cx in (CXL, CXR):
        rrect(img, (cx - W / 2, by, cx + W / 2, by + 30), 15, (255, 255, 255, 60))
    pc = ease_out(prog(t, t_g, 1.0))
    wc = max(3, W * 170 / 42195 * pc)
    rrect(img, (CXR - W / 2, by, CXR - W / 2 + wc, by + 30), 2, C_R + (255,))
    pm = ease_io(prog(t, t_m - 0.2, 2.0))
    rrect(img, (CXL - W / 2, by, CXL - W / 2 + max(3, W * pm), by + 30), 15, C_L + (255,))
    # cheetah: sprints, then lies down panting
    lie = ease_out(prog(t, t_g + 1.1, 0.5))
    paste_c(img, cheetah_sprite(150, gt * 16, run=1 - lie, lie=lie), CXR - 30, 740)
    if lie > 0.5:
        text(img, "puh …", 44, CXR + 120, 600, fill=(255, 255, 255), stroke=4, alpha=lie,
             scale=1 + 0.05 * math.sin(gt * 6))
        for k in range(3):
            yy = 640 + ((gt * 60 + k * 30) % 80)
            d.ellipse((CXR + 150 + k * 18, yy, CXR + 160 + k * 18, yy + 14), fill=(120, 200, 255))
    if t > t_170:
        d.ellipse((CXR - W / 2 - 22, by - 7, CXR - W / 2 + 22, by + 37), outline=E.C_HI, width=5)
    runner(img, CXL - 140 + 280 * pm, 860, 200, gt, 1.0)
    counter(img, CXR, "≈ " + E.fmt_int(170 * ease_out(prog(t, t_170 - 0.3, 0.6))) + " m", "Sprint bei der Jagd",
            C_R, ease_out(prog(t, t_170 - 0.3, 0.3)))
    counter(img, CXL, "über " + E.fmt_int(42 * ease_out(prog(t, t_42 - 0.6, 0.8))) + " km", "Marathon", C_L,
            ease_out(prog(t, t_42 - 0.6, 0.3)))
    if t > t_k:
        crown(img, CXL, 590, prog(t, t_k, 0.5), size=0.6)
        winner(img, t, t_k, "MENSCH", cy=430)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        runner(im, x, y + 90, 170, g, 1.0, a)

    def mr(im, x, y, a, g):
        paste_c(im, cheetah_sprite(90, g * 12), x, y, a)

    brand(img, t, gt)
    E.outro(img, sc, t, gt, ml, mr, line1="Richtig geraten?", line2="Schreib's uns!")


E.setup(
    here=HERE, out="mensch_vs_gepard.mp4",
    name_l="MENSCH", name_r="GEPARD", col_l=C_L, col_r=C_R,
    bg_l=((6, 18, 52), (14, 56, 120)), bg_r=((40, 26, 6), (140, 96, 30)),
    scenes=["hook", "sprint", "tempo", "anzahl", "finale", "outro"],
    draw=dict(hook=sc_hook, sprint=sc_sprint, tempo=sc_tempo, anzahl=sc_anzahl, finale=sc_finale,
              outro=sc_outro),
    sub_map=[
        (("neun", "Komma", "fünf", "acht"), "9,58"), (("hundert",), "100"), (("sechs",), "6"),
        (("fünfundvierzig",), "45"), (("dreiundneunzig",), "93"), (("siebentausend",), "7.000"),
        (("acht",), "8"), (("hundertsiebzig",), "170"), (("zweiundvierzig",), "42"),
        (("eins",), "1"), (("zwei",), "2"), (("drei",), "3"),
    ],
    score=[(1, "Punkt", 1, "R"), (2, "Punkt", 1, "R"), (3, "Punkt", 1, "L"), (4, "Sieger", 1, "L"),
           (4, "Mensch", 1, "L")],
    ticks=[(1, "Usain", 1, 3.2), (4, "zweiundvierzig", 1, 0.8)],
)

if __name__ == "__main__":
    E.main()

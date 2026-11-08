#!/usr/bin/env python3
"""Blauwal vs. Mensch – animated German TikTok comparison.

Usage: python3 render.py [--stills [t1 t2 ...]]
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import engine as E  # noqa: E402
from engine import (CXL, CXR, SPLIT, VIS_Y, NUM_Y, GROUND, SS, back_out, clamp, counter, ease_io,  # noqa: E402
                    ease_out, fmt_int, header, heart_sprite, panel_labels, paste_c, person_icon, person_sprite,
                    prog, stamp, burst, text, vs_badge, wt, rrect, crown, winner, FONT_XB)

C_L = (255, 128, 80)      # Mensch
C_R = (70, 200, 255)      # Blauwal


def whale_sprite(L, t, flip=False):
    L = max(20, L)
    Hh = L * 0.34
    s = SS(L + 8, Hh + 8)
    cy = Hh / 2 + 4
    dark, belly, groove = (55, 92, 140, 255), (125, 165, 200, 255), (85, 120, 165, 255)
    N = 70
    top, bot, mid = [], [], []
    for i in range(N + 1):
        u = i / N * 0.9
        x = 4 + u * L
        if u < 0.10:
            th = 0.085 * (u / 0.10) ** 0.5
        else:
            th = 0.085 * (1 - ((u - 0.10) / 0.82) ** 1.6)
        th = max(th, 0.011) * L
        yc = cy + 0.035 * L * math.sin(t * 2.2 - u * 4) * u ** 2
        top.append((x, yc - th * 0.85))
        bot.append((x, yc + th * 1.1))
        mid.append((x, yc + th * 0.15))
    s.poly(top + bot[::-1], dark)
    k = int(N * 0.62)
    s.poly(mid[:k] + bot[:k][::-1], belly)
    for j in range(7):
        y0 = 0.25 + j * 0.1
        pts = [(mid[i][0], mid[i][1] + (bot[i][1] - mid[i][1]) * y0) for i in range(1, int(N * 0.38))]
        s.line(pts, groove, max(1, L * 0.0025))
    r = random.Random(3)
    for _ in range(40):
        i = r.randint(3, int(N * 0.85))
        x, y0 = top[i]
        y1 = mid[i][1]
        yy = r.uniform(y0, y1)
        rr = L * r.uniform(0.003, 0.007)
        s.ell(x, yy, rr * 1.6, rr, (110, 145, 185, 200))
    # flipper
    i = int(N * 0.3)
    fx, fy = bot[i]
    s.poly([(fx - L * 0.02, fy - L * 0.01), (fx + L * 0.11, fy + L * 0.07), (fx + L * 0.04, fy)], dark)
    # dorsal fin
    i = int(N * 0.78)
    dx, dy = top[i]
    s.poly([(dx - L * 0.02, dy + 2), (dx + L * 0.02, dy - L * 0.025), (dx + L * 0.03, dy + 2)], dark)
    # flukes
    xe, ye = (top[-1][0] + bot[-1][0]) / 2, (top[-1][1] + bot[-1][1]) / 2
    sw = 0.02 * L * math.sin(t * 2.2 - 3.6)
    s.poly([(xe - 4, ye - L * 0.012), (xe + L * 0.05, ye - L * 0.03 + sw), (xe + L * 0.105, ye - L * 0.045 + sw),
            (xe + L * 0.085, ye + sw * 0.5), (xe + L * 0.105, ye + L * 0.03 + sw), (xe + L * 0.05, ye + L * 0.02 + sw),
            (xe - 4, ye + L * 0.012)], dark)
    # eye + mouth line
    ex, ey = mid[int(N * 0.08)]
    s.ell(ex, ey - L * 0.004, L * 0.006, L * 0.006, (15, 25, 40, 255))
    s.line([(4 + L * 0.005, mid[2][1]), (4 + L * 0.06, mid[int(N * 0.07)][1] + L * 0.004)], (30, 50, 80, 255),
           max(1, L * 0.003))
    im = s.img()
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def beam(img, tilt, lx_off=300, py=760, a=1.0):
    px = SPLIT
    lx, ly = px - lx_off * math.cos(tilt), py - lx_off * math.sin(tilt)
    rx, ry = px + lx_off * math.cos(tilt), py + lx_off * math.sin(tilt)
    layer = Image.new("RGBA", (E.W, E.H))
    d = ImageDraw.Draw(layer)
    al = int(255 * a)
    d.polygon([(px, py), (px - 60, py + 230), (px + 60, py + 230)], fill=(220, 220, 235, al))
    d.line((lx, ly, rx, ry), fill=(240, 240, 250, al), width=16)
    d.ellipse((px - 16, py - 16, px + 16, py + 16), fill=(255, 226, 60, al))
    for (x, y) in ((lx, ly), (rx, ry)):
        d.line((x, y, x - 80, y + 110), fill=(220, 220, 235, al), width=4)
        d.line((x, y, x + 80, y + 110), fill=(220, 220, 235, al), width=4)
        d.rounded_rectangle((x - 110, y + 108, x + 110, y + 124), 8, fill=(220, 220, 235, al))
    img.paste(layer, (0, 0), layer)
    return (lx, ly + 108), (rx, ry + 108)


def sc_hook(img, sc, t, gt):
    header(img, gt, "", t)
    panel_labels(img, t, right="???")
    t_h, t_s, t_z, t_m = wt(sc, "Herz"), wt(sc, "schwerer"), wt(sc, "zwei"), wt(sc, "Menschen")
    tilt = 0.22 * ease_out(prog(t, t_s, 0.6)) + 0.03 * math.sin(gt * 8) * (1 - prog(t, t_s + 0.5, 0.6)) * (t > t_s)
    (lx, ly), (rx, ry) = beam(img, tilt, a=ease_out(prog(t, 0.0, 0.3)))
    for k, tt in enumerate((t_z, t_m)):
        p = back_out(prog(t, tt - 0.1, 0.35))
        if p > 0.02:
            spr = person_sprite(150 * p, C_L)
            paste_c(img, spr, lx - 45 + 90 * k, ly, anchor="b")
    beat = max(0, math.sin(gt * 2 * math.pi * 0.8)) ** 8
    hp = back_out(prog(t, 0.05, 0.4)) * (1 + 0.15 * ease_out(prog(t, t_h, 0.25)) * (1 - prog(t, t_h + 0.25, 0.3)))
    if hp > 0.02:
        paste_c(img, heart_sprite(230 * hp, beat=beat), rx, ry - 105)
    text(img, "?", 120, CXR, 520, fill=C_R, scale=1 + 0.1 * math.sin(gt * 9), alpha=ease_out(prog(t, t_s, 0.3)),
         stroke=8, sfill=(0, 0, 0))


def sc_laenge(img, sc, t, gt):
    header(img, gt, "RUNDE 1 · LÄNGE", t)
    panel_labels(img, t)
    t_du, t_180 = wt(sc, "Du"), wt(sc, "eins")
    t_bw, t_33, t_l, t_18 = wt(sc, "Blauwal"), wt(sc, "dreiunddreißig"), wt(sc, "Länger"), wt(sc, "achtzehn")
    g = ease_io(prog(t, t_bw, 1.2))
    Lw = 860
    ppm = Lw / 33.5
    # whale swims in from the right
    wx = 40 + Lw / 2 + (1 - ease_out(prog(t, t_bw - 0.2, 1.4))) * 1000
    if t > t_bw - 0.3:
        paste_c(img, whale_sprite(Lw, gt), wx, VIS_Y - 40)
    # the person: big first, then true scale under the whale
    ph = 180 * (1 - g) + 1.8 * ppm * g
    px = CXL * (1 - g) + 60 * g
    py = GROUND * (1 - g) + (VIS_Y + 190) * g
    if g < 0.98:
        E.ruler(img, CXL - 110, GROUND, 100, 2, a=(1 - g) * ease_out(prog(t, t_du, 0.3)), step=0.5)
    if t_l > t or g < 1:
        pa = ease_out(prog(t, t_du - 0.1, 0.3))
        if pa > 0.02:
            paste_c(img, person_sprite(ph, C_L), px, py, alpha=pa, anchor="b")
    vs_badge(img, gt, (1 - prog(t, t_bw - 0.3, 0.3)) * ease_out(prog(t, 0.2, 0.3)), y=VIS_Y + 100)
    counter(img, CXL, "1,80 m", "du (Beispiel)", C_L, ease_out(prog(t, t_180, 0.3)))
    m = 33.5 * ease_out(prog(t, t_33, 1.0))
    counter(img, CXR, E.fmt_dec(m, 1) + " m", "Blauwal (bis zu)", C_R, ease_out(prog(t, t_33, 0.3)))
    # 18 people lying head to toe under the whale
    if t > t_18 - 0.1:
        n = int(clamp((t - (t_18 - 0.1)) / 0.9) * 18 + 0.999)
        lying = person_icon(int(1.8 * ppm), C_L).rotate(90, expand=True)
        for k in range(n):
            x = 40 + k * 1.8 * ppm + 1.8 * ppm / 2
            paste_c(img, lying, x, VIS_Y + 175)
        text(img, f"{n} ×", 64, SPLIT, VIS_Y + 250, fill=C_L, stroke=6, sfill=(0, 0, 0))
    burst(img, SPLIT, VIS_Y + 175, t, t_18 + 0.9, color=C_L, rad=200)


def sc_herz(img, sc, t, gt):
    header(img, gt, "RUNDE 2 · HERZ", t)
    panel_labels(img, t)
    t_d, t_300 = wt(sc, "Deins"), wt(sc, "dreihundert")
    t_h2, t_180, t_x = wt(sc, "Herz", 2), wt(sc, "hundertachtzig"), wt(sc, "Sechshundertmal")
    g = ease_io(prog(t, t_h2, 1.2))
    beat_l = max(0, math.sin(gt * 2 * math.pi * 1.2)) ** 8
    beat_r = max(0, math.sin(gt * 2 * math.pi * 0.25)) ** 8
    big = 400
    small = big / 600 ** (1 / 3)              # same shape, 1/600 of the volume
    sl = 180 * (1 - g) + small * g
    pa = back_out(prog(t, t_d - 0.1, 0.4))
    if pa > 0.02:
        paste_c(img, heart_sprite(sl * pa, beat=beat_l), CXL, VIS_Y)
    pr = back_out(prog(t, t_h2 - 0.1, 0.5))
    if pr > 0.02:
        paste_c(img, heart_sprite(big * pr * (0.55 + 0.45 * g), color=(220, 30, 60), beat=beat_r), CXR, VIS_Y)
    if g > 0.9:
        text(img, "maßstabsgetreu", 30, SPLIT, VIS_Y + 250, fill=(230, 230, 240), alpha=prog(g, 0.9, 0.1),
             path=FONT_XB)
    vs_badge(img, gt, (1 - prog(t, t_h2, 0.3)) * ease_out(prog(t, 0.3, 0.3)))
    counter(img, CXL, "≈ " + fmt_int(300 * ease_out(prog(t, t_300, 0.8))) + " g", "dein Herz", C_L,
            ease_out(prog(t, t_300, 0.3)))
    counter(img, CXR, "≈ " + fmt_int(180 * ease_out(prog(t, t_180, 0.9))) + " kg", "Blauwal-Herz", C_R,
            ease_out(prog(t, t_180, 0.3)))
    burst(img, CXR, VIS_Y, t, t_x)
    stamp(img, "600×", t, t_x, cx=SPLIT, cy=VIS_Y - 230)


def ecg(img, box, t, beats, color, a=1.0):
    """scrolling ECG trace. beats: list of beat times (s); window 3 s"""
    x0, y0, x1, y1 = box
    rrect(img, box, 24, (5, 15, 20, int(230 * a)), outline=color + (int(200 * a),), width=4)
    layer = Image.new("RGBA", (E.W, E.H))
    d = ImageDraw.Draw(layer)
    for gx in range(x0 + 20, x1, 40):
        d.line((gx, y0 + 10, gx, y1 - 10), fill=(40, 80, 60, int(120 * a)), width=1)
    for gy in range(y0 + 20, y1, 40):
        d.line((x0 + 10, gy, x1 - 10, gy), fill=(40, 80, 60, int(120 * a)), width=1)
    win = 3.0
    pts = []
    cy = (y0 + y1) / 2 + 30
    amp = (y1 - y0) * 0.38
    n = 220
    for i in range(n + 1):
        u = i / n
        tt = t - win + u * win
        v = 0.0
        for b in beats:
            dt = tt - b
            if -0.2 < dt < 0.4:
                v += 0.12 * math.exp(-((dt + 0.12) / 0.03) ** 2)     # P
                v += -0.15 * math.exp(-((dt + 0.02) / 0.008) ** 2)  # Q
                v += 1.0 * math.exp(-((dt) / 0.012) ** 2)           # R
                v += -0.25 * math.exp(-((dt - 0.03) / 0.012) ** 2)  # S
                v += 0.22 * math.exp(-((dt - 0.22) / 0.05) ** 2)    # T
        pts.append((x0 + 16 + u * (x1 - x0 - 32), cy - v * amp))
    d.line(pts, fill=(80, 255, 140, int(255 * a)), width=5, joint="curve")
    hx, hy = pts[-1]
    d.ellipse((hx - 8, hy - 8, hx + 8, hy + 8), fill=(200, 255, 220, int(255 * a)))
    img.paste(layer, (0, 0), layer)


def sc_puls(img, sc, t, gt):
    header(img, gt, "RUNDE 3 · HERZSCHLAG", t)
    panel_labels(img, t)
    t_dh, t_60 = wt(sc, "Dein"), wt(sc, "sechzig")
    t_bt, t_2 = wt(sc, "Beim"), wt(sc, "zweimal")
    period = 60 / 75
    beats_l = [k * period for k in range(-5, 40)]
    beats_r = [t_2 + 0.15]
    al = ease_out(prog(t, 0.2, 0.4))
    ecg(img, (30, 450, 440, 740), t, beats_l, C_L, al)
    ar = ease_out(prog(t, t_bt - 0.3, 0.4))
    ecg(img, (500, 450, 910, 740), t, beats_r, C_R, ar if ar > 0 else 0.0001)
    # hearts that pulse with the trace
    bl = max([math.exp(-((t - b) / 0.08) ** 2) for b in beats_l])
    br = math.exp(-((t - beats_r[0]) / 0.12) ** 2)
    paste_c(img, heart_sprite(120, beat=bl * 1.5), CXL, 860, al)
    paste_c(img, heart_sprite(120, color=(220, 30, 60), beat=br * 1.5), CXR, 860, ar)
    counter(img, CXL, "60–100", "pro Minute (Ruhe)", C_L, ease_out(prog(t, t_60, 0.3)))
    counter(img, CXR, "2", "pro Minute (Tauchen)", C_R, ease_out(prog(t, t_2, 0.3)))
    burst(img, CXR, 860, t, beats_r[0], color=(255, 80, 100))


DOT = None


def crowd_pts(n, x0, y0, x1, y1):
    cols = 62
    rows = int(math.ceil(n / cols))
    cw = (x1 - x0) / cols
    rh = (y1 - y0) / rows
    pts = []
    r = random.Random(4)
    for i in range(n):
        c, rw = i % cols, i // cols
        pts.append((x0 + (c + 0.5) * cw, y0 + (rw + 0.5) * rh, r.random()))
    return pts, cw, rh


CROWD = None


def sc_finale(img, sc, t, gt):
    t_k = wt(sc, "Klarer")
    header(img, gt, "FINALE · GEWICHT", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    t_bw, t_150 = wt(sc, "Blauwal"), wt(sc, "hundertfünfzig")
    t_u, t_2k = wt(sc, "über"), wt(sc, "zweitausend")
    g = ease_io(prog(t, t_u - 0.2, 0.6))
    wl = 760 * (1 - g) + 520 * g
    wy = (VIS_Y - 40) * (1 - g) + 470 * g
    wa = ease_out(prog(t, t_bw - 0.3, 0.5))
    if wa > 0:
        paste_c(img, whale_sprite(wl, gt), SPLIT, wy, wa)
    # scale display under the whale
    if g < 1:
        a = (1 - g) * ease_out(prog(t, t_bw, 0.3))
        rrect(img, (SPLIT - 230, VIS_Y + 120, SPLIT + 230, VIS_Y + 150), 10, (230, 230, 240, int(255 * a)))
        rrect(img, (SPLIT - 170, VIS_Y + 170, SPLIT + 170, VIS_Y + 270), 16, (15, 20, 30, int(255 * a)),
              outline=C_R + (int(255 * a),), width=5)
        v = 150 * ease_out(prog(t, t_150, 1.2))
        text(img, f"{int(round(v))} t", 66, SPLIT, VIS_Y + 220, fill=(120, 255, 140), alpha=a)
    global CROWD
    if CROWD is None:
        CROWD = crowd_pts(2000, 60, 640, 880, 1040)
    if g > 0:
        pts, cw, rh = CROWD
        icon = person_icon(int(rh * 0.95), C_L)
        f = ease_io(prog(t, t_2k - 0.2, 1.3))
        for (x, y, r) in pts:
            if r < f:
                paste_c(img, icon, x, y)
        n = 2000 * f
        if f < 1:
            counter(img, SPLIT, fmt_int(n), "Menschen à 70 kg", C_L, g, y=NUM_Y + 40)
        else:
            counter(img, SPLIT, "über 2.000", "Menschen à 70 kg", C_L, 1.0, y=NUM_Y + 40)
    if t > t_k:
        crown(img, SPLIT - 20, wy - wl * 0.17 - 60, prog(t, t_k, 0.5), size=0.7)
        winner(img, t, t_k, "BLAUWAL", cy=595)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, person_sprite(170, C_L), x, y + 85, a, anchor="b")

    def mr(im, x, y, a, g):
        paste_c(im, whale_sprite(300, g), x, y, a)

    E.outro(img, sc, t, gt, ml, mr, line1="Wer als Nächstes?")


def extra_sfx():
    sc = E.SCENES[3]
    return [(sc["start"] + wt(sc, "zweimal") + 0.15, "beat")]


E.setup(
    here=HERE, out="blauwal_vs_mensch.mp4",
    name_l="MENSCH", name_r="BLAUWAL", col_l=C_L, col_r=C_R,
    bg_l=((42, 10, 22), (120, 36, 34)), bg_r=((2, 14, 42), (0, 70, 120)),
    scenes=["hook", "laenge", "herz", "puls", "finale", "outro"],
    draw=dict(hook=sc_hook, laenge=sc_laenge, herz=sc_herz, puls=sc_puls, finale=sc_finale, outro=sc_outro),
    sub_map=[
        (("eins", "achtzig"), "1,80"), (("dreiunddreißig",), "33"), (("achtzehn",), "18"),
        (("dreihundert",), "300"), (("hundertachtzig",), "180"), (("Sechshundertmal",), "600-mal"),
        (("sechzig",), "60"), (("hundertmal",), "100-mal"), (("zweimal",), "2-mal"),
        (("hundertfünfzig",), "150"), (("zweitausend",), "2.000"),
        (("eins",), "1"), (("zwei",), "2"), (("drei",), "3"),
    ],
    score=[(1, "Länger", 1, "R"), (2, "Sechshundertmal", 1, "R"), (3, "zweimal", 1, "R"), (4, "Sieger", 1, "R")],
    ticks=[(1, "dreiunddreißig", 1, 1.0), (2, "hundertachtzig", 1, 0.9), (4, "hundertfünfzig", 1, 1.2),
           (4, "zweitausend", 1, 1.3)],
    extra_sfx=extra_sfx,
)

if __name__ == "__main__":
    E.main()

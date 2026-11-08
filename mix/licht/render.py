#!/usr/bin/env python3
"""Schall vs. Licht – animated German TikTok comparison."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tiere"))
import engine as E  # noqa: E402
from engine import (CXL, CXR, SPLIT, VIS_Y, NUM_Y, GROUND, SS, back_out, clamp, counter, ease_io,  # noqa: E402
                    ease_out, header, panel_labels, paste_c, person_sprite, prog, stamp, burst, text, wt, rrect,
                    crown, winner, FONT_XB)

C_L = (255, 110, 200)     # Schall
C_R = (255, 228, 70)      # Licht


def cloud_sprite(w):
    s = SS(w, w * 0.55)
    for cx, cy, r in ((0.3, 0.6, 0.2), (0.5, 0.45, 0.26), (0.72, 0.58, 0.2), (0.5, 0.68, 0.22), (0.2, 0.72, 0.13),
                      (0.82, 0.72, 0.13)):
        s.ell(cx * w, cy * w * 0.55 + 0.0, r * w, r * w * 0.8, (120, 125, 150, 255))
    for cx, cy, r in ((0.45, 0.4, 0.15), (0.62, 0.45, 0.12)):
        s.ell(cx * w, cy * w * 0.55, r * w, r * w * 0.6, (150, 155, 180, 255))
    return s.img()


def bolt(img, x0, y0, x1, y1, a=1.0, seed=1):
    if a <= 0.02:
        return
    r = random.Random(seed)
    pts = [(x0, y0)]
    n = 7
    for i in range(1, n):
        u = i / n
        pts.append((x0 + (x1 - x0) * u + r.uniform(-40, 40), y0 + (y1 - y0) * u))
    pts.append((x1, y1))
    layer = Image.new("RGBA", (E.W, E.H))
    d = ImageDraw.Draw(layer)
    d.line(pts, fill=(255, 240, 150, int(110 * a)), width=34, joint="curve")
    d.line(pts, fill=(255, 255, 230, int(255 * a)), width=10, joint="curve")
    img.paste(layer, (0, 0), layer)


def rings(img, cx, cy, radius, color, n=4, spacing=50, a=1.0, max_r=2000):
    layer = Image.new("RGBA", (E.W, E.H))
    d = ImageDraw.Draw(layer)
    for k in range(n):
        r = radius - k * spacing
        if 4 < r < max_r:
            al = int(220 * a * (1 - k / n))
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color + (al,), width=8)
    img.paste(layer, (0, 0), layer)


def glow_dot(img, x, y, r, color):
    layer = Image.new("RGBA", (int(r * 6), int(r * 6)))
    d = ImageDraw.Draw(layer)
    c = r * 3
    for k, al in ((3.0, 40), (2.0, 80), (1.3, 150), (1.0, 255)):
        d.ellipse((c - r * k, c - r * k, c + r * k, c + r * k), fill=color + (al,))
    d.ellipse((c - r * 0.5, c - r * 0.5, c + r * 0.5, c + r * 0.5), fill=(255, 255, 255, 255))
    paste_c(img, layer, x, y)


def beam(img, x0, y0, x1, y1, color, a=1.0):
    layer = Image.new("RGBA", (E.W, E.H))
    d = ImageDraw.Draw(layer)
    d.line((x0, y0, x1, y1), fill=color + (int(80 * a),), width=30)
    d.line((x0, y0, x1, y1), fill=color + (int(255 * a),), width=10)
    d.line((x0, y0, x1, y1), fill=(255, 255, 255, int(255 * a)), width=3)
    img.paste(layer, (0, 0), layer)


def earth_sprite(r):
    s = SS(2 * r + 4, 2 * r + 4)
    s.ell(r + 2, r + 2, r, r, (40, 120, 230, 255))
    rr = random.Random(3)
    for _ in range(9):
        a = rr.uniform(0, 6.28)
        d = rr.uniform(0, 0.6) * r
        s.ell(r + 2 + d * math.cos(a), r + 2 + d * math.sin(a), r * rr.uniform(0.12, 0.3), r * rr.uniform(0.1, 0.22),
              (70, 180, 90, 255))
    s.ell(r + 2 - r * 0.35, r + 2 - r * 0.35, r * 0.25, r * 0.18, (255, 255, 255, 50))
    return s.img()


def moon_sprite(r):
    s = SS(2 * r + 4, 2 * r + 4)
    s.ell(r + 2, r + 2, r, r, (200, 200, 210, 255))
    for x, y, q in ((0.6, 0.7, 0.2), (1.3, 0.8, 0.15), (1.0, 1.4, 0.25), (0.6, 1.3, 0.1)):
        s.ell(x * r + 2, y * r + 2, q * r, q * r, (165, 165, 180, 255))
    return s.img()


def speaker_sprite(h):
    s = SS(h * 1.3, h)
    s.rect(h * 0.05, h * 0.32, h * 0.32, h * 0.68, h * 0.05, C_L + (255,))
    s.poly([(h * 0.3, h * 0.32), (h * 0.62, h * 0.08), (h * 0.62, h * 0.92), (h * 0.3, h * 0.68)], C_L + (255,))
    for k, rr in enumerate((0.22, 0.36)):
        s.d.arc(((0.7 - rr) * h * s.k, (0.5 - rr) * h * s.k, (0.7 + rr) * h * s.k, (0.5 + rr) * h * s.k), -50, 50,
                fill=C_L + (255,), width=int(h * 0.06 * s.k))
    return s.img()


def bulb_sprite(h):
    s = SS(h * 0.8, h)
    s.ell(h * 0.4, h * 0.38, h * 0.36, h * 0.36, C_R + (255,))
    s.poly([(h * 0.2, h * 0.55), (h * 0.6, h * 0.55), (h * 0.52, h * 0.78), (h * 0.28, h * 0.78)], C_R + (255,))
    s.rect(h * 0.26, h * 0.78, h * 0.54, h * 0.95, h * 0.04, (170, 170, 185, 255))
    s.ell(h * 0.3, h * 0.28, h * 0.08, h * 0.1, (255, 255, 255, 160))
    return s.img()


def sc_hook(img, sc, t, gt):
    header(img, gt, "", t)
    panel_labels(img, t)
    t_d = wt(sc, "Donner")
    sx, sy = SPLIT + 120, 1000
    paste_c(img, cloud_sprite(400), SPLIT + 120, 580, ease_out(prog(t, 0.0, 0.3)))
    flash = math.exp(-((t - 0.12) / 0.08) ** 2) if t > 0.05 else 0
    if 0.08 < t < 0.6:
        bolt(img, SPLIT + 120, 620, sx, sy, a=1 - prog(t, 0.35, 0.25))
    paste_c(img, person_sprite(200, (230, 230, 240)), 130, GROUND, anchor="b")
    rings(img, sx, sy, (t - 0.12) * 260, C_L, n=3, spacing=60, a=1.0 if t > 0.12 else 0)
    if t > t_d:
        text(img, "BUMM!", 90, 160, 720, fill=C_L, stroke=8, scale=back_out(prog(t, t_d, 0.3)), rotate=8)
    if flash > 0.02:
        ov = Image.new("RGB", (E.W, E.H), (255, 255, 240))
        img.paste(Image.blend(img, ov, 0.7 * flash))


def sc_kilometer(img, sc, t, gt):
    header(img, gt, "RUNDE 1 · EIN KILOMETER", t)
    t_s, t_sek, t_l, t_m = wt(sc, "Schall"), wt(sc, "Sekunden", 1, "e"), wt(sc, "Licht"), wt(sc, "Millionstel")
    x0, x1 = 80, 860
    lanes = ((560, C_R, "LICHT"), (820, C_L, "SCHALL"))
    a = ease_out(prog(t, 0.1, 0.4))
    d = ImageDraw.Draw(img)
    for y, col, nm in lanes:
        rrect(img, (x0 - 20, y - 40, x1 + 20, y + 40), 40, (255, 255, 255, int(30 * a)))
        text(img, nm, 36, x0 + 60, y - 72, fill=col, alpha=a, stroke=4)
    for x, lab in ((x0, "0"), (x1, "1 km")):
        d.line((x, 500, x, 880), fill=(255, 255, 255), width=4)
        text(img, lab, 34, x, 920, alpha=a, path=FONT_XB)
    # sound runner
    ps = ease_io(prog(t, t_s, max(0.5, t_sek - t_s)))
    xs = x0 + (x1 - x0) * ps
    rings(img, xs, 820, 30 + 20 * math.sin(gt * 12), C_L, n=2, spacing=14)
    glow_dot(img, xs, 820, 14, C_L)
    # light runner: instant
    if t >= t_l:
        pl = prog(t, t_l, 0.08)
        xl = x0 + (x1 - x0) * pl
        beam(img, x0, 560, xl, 560, C_R, a=1 - 0.6 * prog(t, t_l + 0.3, 0.6))
        glow_dot(img, xl, 560, 16, C_R)
    else:
        glow_dot(img, x0, 560, 16, C_R)
    tl = 2.9 * ps
    counter(img, CXL, E.fmt_dec(tl, 1) + " s", "Schall (rund 3 s)", C_L, ease_out(prog(t, t_s, 0.3)))
    counter(img, CXR, "0,0000033 s", "Licht", C_R, ease_out(prog(t, t_l, 0.3)), size=56)
    burst(img, x1, 560, t, t_l + 0.08, color=C_R, rad=150)


def sc_gewitter(img, sc, t, gt):
    header(img, gt, "RUNDE 2 · GEWITTER", t)
    panel_labels(img, t)
    t_z, t_b, t_d = wt(sc, "Zähl"), wt(sc, "Blitz"), wt(sc, "Donner")
    t_3, t_km = wt(sc, "drei"), wt(sc, "Kilometer")
    paste_c(img, cloud_sprite(360), CXR + 20, 590, ease_out(prog(t, 0.0, 0.4)))
    flash = math.exp(-((t - t_b) / 0.07) ** 2)
    if t_b - 0.05 < t < t_b + 0.5:
        bolt(img, CXR + 20, 630, CXR + 60, 1000, a=1 - prog(t, t_b + 0.25, 0.25), seed=3)
    paste_c(img, person_sprite(190, (230, 230, 240)), CXL - 40, GROUND, anchor="b")
    if t > t_d:
        rings(img, CXR + 60, 1000, 120 + (t - t_d) * 500, C_L, n=3, spacing=60, max_r=900)
        text(img, "BUMM!", 70, CXL + 20, 700, fill=C_L, stroke=7, scale=back_out(prog(t, t_d, 0.3)), rotate=8)
    # stopwatch counting
    if t > t_z:
        n = int(min(9, (t - t_z) / max(0.2, (t_d - t_z)) * 9)) if t < t_d else 9
        rrect(img, (CXL - 120, 470, CXL + 120, 600), 30, (255, 255, 255, 235))
        text(img, f"{n} s", 80, CXL, 535, fill=(40, 30, 60))
    a1 = ease_out(prog(t, t_z + 0.3, 0.3))
    parts = [("9 s", t_d), ("÷ 3", t_3), ("= 3 km", t_km)]
    xs = [SPLIT - 250, SPLIT, SPLIT + 250]
    for (s_, tt), x in zip(parts, xs):
        if t > tt:
            text(img, s_, 80, x, NUM_Y + 20, fill=E.C_HI if s_.startswith("=") else E.WHITE, stroke=7,
                 scale=back_out(prog(t, tt, 0.3)))
    text(img, "Beispiel", 34, SPLIT, NUM_Y + 100, fill=(220, 220, 230), alpha=a1 * (t > t_d), path=FONT_XB)
    if flash > 0.02:
        ov = Image.new("RGB", (E.W, E.H), (255, 255, 240))
        img.paste(Image.blend(img, ov, 0.6 * flash))


def sc_mond(img, sc, t, gt):
    header(img, gt, "RUNDE 3 · BIS ZUM MOND", t)
    t_l, t_s, t_13 = wt(sc, "Licht"), wt(sc, "Schall"), wt(sc, "dreizehn")
    ex, ey, mx, my = 170, 900, 780, 470
    paste_c(img, earth_sprite(95), ex, ey, ease_out(prog(t, 0.1, 0.4)))
    paste_c(img, moon_sprite(60), mx, my, ease_out(prog(t, 0.3, 0.4)))
    text(img, "384.400 km", 40, (ex + mx) / 2 + 40, (ey + my) / 2 + 40, fill=(230, 230, 240), rotate=35,
         alpha=ease_out(prog(t, 0.5, 0.4)), path=FONT_XB)
    if t > t_l:
        p = prog(t, t_l, 0.45)
        bx, by = ex + (mx - ex) * p, ey + (my - ey) * p
        beam(img, ex, ey, bx, by, C_R, a=1 - 0.5 * prog(t, t_l + 0.8, 0.6))
        glow_dot(img, bx, by, 16, C_R)
    if t > t_s:
        p = 0.04 * ease_out(prog(t, t_s, 3.0))
        sx, sy = ex + (mx - ex) * p + 70, ey + (my - ey) * p - 50
        rings(img, sx, sy, 24 + 10 * math.sin(gt * 10), C_L, n=2, spacing=12)
        glow_dot(img, sx, sy, 12, C_L)
        text(img, "…", 60, sx + 50, sy - 10, fill=C_L, alpha=0.8)
    counter(img, CXL, "≈ 13 Tage", "wenn es Luft gäbe", C_L, ease_out(prog(t, t_13, 0.3)))
    counter(img, CXR, "1,28 s", "Licht", C_R, ease_out(prog(t, t_l + 0.4, 0.3)))
    burst(img, mx, my, t, t_l + 0.45, color=C_R, rad=150)


def sc_finale(img, sc, t, gt):
    t_k = wt(sc, "Klarer")
    header(img, gt, "FINALE · UM DIE ERDE", t, title_a=1 - prog(t, t_k - 0.1, 0.3))
    t_l, t_75, t_s, t_32 = wt(sc, "Licht"), wt(sc, "siebeneinhalbmal"), wt(sc, "Schall"), wt(sc, "zweiunddreißig")
    cx, cy = SPLIT, 700
    paste_c(img, earth_sprite(150), cx, cy, ease_out(prog(t, 0.0, 0.4)))
    R1, R2 = 215, 265
    layer = Image.new("RGBA", (E.W, E.H))
    d = ImageDraw.Draw(layer)
    d.ellipse((cx - R1, cy - R1, cx + R1, cy + R1), outline=C_R + (60,), width=3)
    d.ellipse((cx - R2, cy - R2, cx + R2, cy + R2), outline=C_L + (60,), width=3)
    img.paste(layer, (0, 0), layer)
    laps = 7.5 * ease_io(prog(t, t_75 - 0.2, 1.4)) if t > t_l else 0
    if t > t_l:
        ang = laps * 2 * math.pi - math.pi / 2
        trail = Image.new("RGBA", (E.W, E.H))
        td = ImageDraw.Draw(trail)
        for k in range(14):
            a2 = ang - k * 0.12
            td.ellipse((cx + R1 * math.cos(a2) - 9, cy + R1 * math.sin(a2) - 9, cx + R1 * math.cos(a2) + 9,
                        cy + R1 * math.sin(a2) + 9), fill=C_R + (int(200 * (1 - k / 14)),))
        img.paste(trail, (0, 0), trail)
        glow_dot(img, cx + R1 * math.cos(ang), cy + R1 * math.sin(ang), 15, C_R)
    if t > t_s:
        a3 = -math.pi / 2 + 0.03 * ease_out(prog(t, t_s, 2.0))
        glow_dot(img, cx + R2 * math.cos(a3), cy + R2 * math.sin(a3), 12, C_L)
    counter(img, CXR, E.fmt_dec(laps, 1) + " Runden", "Licht pro Sekunde", C_R, ease_out(prog(t, t_l, 0.3)), size=58)
    counter(img, CXL, "über 32 h", "Schall für 1 Runde", C_L, ease_out(prog(t, t_32, 0.3)), size=58)
    if t > t_k:
        paste_c(img, bulb_sprite(170), cx, cy, ease_out(prog(t, t_k, 0.3)))
        crown(img, cx, cy - 150, prog(t, t_k, 0.5), size=0.5)
        winner(img, t, t_k, "LICHT", cy=cy + 270)


def sc_outro(img, sc, t, gt):
    def ml(im, x, y, a, g):
        paste_c(im, speaker_sprite(140), x, y, a)

    def mr(im, x, y, a, g):
        paste_c(im, bulb_sprite(160), x, y, a)

    E.outro(img, sc, t, gt, ml, mr, line1="Wie viele Sekunden?", line2="Schreib's uns!")


E.setup(
    here=HERE, out="schall_vs_licht.mp4",
    name_l="SCHALL", name_r="LICHT", col_l=C_L, col_r=C_R,
    bg_l=((24, 6, 34), (84, 20, 92)), bg_r=((8, 10, 34), (34, 44, 100)),
    scenes=["hook", "kilometer", "gewitter", "mond", "finale", "outro"],
    draw=dict(hook=sc_hook, kilometer=sc_kilometer, gewitter=sc_gewitter, mond=sc_mond, finale=sc_finale,
              outro=sc_outro),
    sub_map=[
        (("dreizehn",), "13"), (("siebeneinhalbmal",), "7,5-mal"), (("zweiunddreißig",), "32"),
        (("eins",), "1"), (("zwei",), "2"), (("drei",), "3"),
    ],
    score=[(1, "Millionstel", 1, "R"), (3, "Sekunde", 1, "R"), (4, "Sieger", 1, "R")],
    ticks=[(1, "Schall", 1, 1.6), (4, "siebeneinhalbmal", 1, 1.2)],
)

if __name__ == "__main__":
    E.main()

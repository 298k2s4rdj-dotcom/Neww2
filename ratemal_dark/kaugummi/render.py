#!/usr/bin/env python3
"""Rate mal, was passiert, wenn du einen Kaugummi verschluckst? – dark stick-figure style, German voice-over."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import lib as L  # noqa: E402
from lib import (Stage, Over, figure, pose, prog, eo, eio, bo, mix, wt, brand, question, outro_cta, K, chip,  # noqa: E402
                 TXT, DIM, AMBER, CORAL, BLUE, PINK, GREEN, TONE_COOL, MONO, MONO_XB, INTER, F)

XR_FILL = (18, 26, 48)
XR_LINE = (110, 150, 230)

# ------------------------------------------------------------------ x-ray bust + digestive tract
GUT = [(540, 610), (540, 760), (545, 860), (585, 900), (640, 905), (650, 950), (600, 985), (470, 985), (455, 1015),
       (470, 1040), (620, 1040), (640, 1070), (620, 1100), (460, 1100), (445, 1130), (470, 1160), (600, 1160),
       (560, 1190), (540, 1240)]
STOMACH = (595, 905)


def _cum(path):
    d = [0.0]
    for a, b in zip(path, path[1:]):
        d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return d


CUM = _cum(GUT)


def along(f):
    s = max(0.0, min(1.0, f)) * CUM[-1]
    for i in range(len(GUT) - 1):
        if CUM[i + 1] >= s:
            k = (s - CUM[i]) / max(1e-6, CUM[i + 1] - CUM[i])
            return (GUT[i][0] + (GUT[i + 1][0] - GUT[i][0]) * k, GUT[i][1] + (GUT[i + 1][1] - GUT[i][1]) * k)
    return GUT[-1]


F_STOMACH = CUM[4] / CUM[-1]


def xray(st, a=1.0, gt=0.0, wave=None, alarm=0.0):
    if a <= 0.01:
        return
    lay = Image.new("RGBA", st.im.size)
    d = ImageDraw.Draw(lay)
    A = int(255 * a)

    def rr(box, r, fill, outline, w=4):
        d.rounded_rectangle([v * K for v in box], int(r * K), fill=fill, outline=outline, width=int(w * K))

    # body
    rr((380, 690, 700, 1260), 130, XR_FILL + (int(200 * a),), XR_LINE + (A,), 5)
    rr((300, 720, 390, 1180), 45, XR_FILL + (int(200 * a),), XR_LINE + (A,), 5)
    rr((690, 720, 780, 1180), 45, XR_FILL + (int(200 * a),), XR_LINE + (A,), 5)
    rr((505, 630, 575, 720), 20, XR_FILL + (int(220 * a),), XR_LINE + (A,), 5)
    d.ellipse(((540 - 100) * K, (540 - 100) * K, (540 + 100) * K, (540 + 100) * K), fill=XR_FILL + (int(220 * a),),
              outline=XR_LINE + (A,), width=5 * K)
    # stomach
    col = mix((150, 70, 95), CORAL, alarm)
    d.ellipse(((STOMACH[0] - 80) * K, (STOMACH[1] - 55) * K, (STOMACH[0] + 80) * K, (STOMACH[1] + 60) * K),
              fill=col + (int(170 * a),), outline=(230, 140, 160, A), width=4 * K)
    # gut tube
    pts = [(x * K, y * K) for x, y in GUT]
    d.line(pts, fill=(170, 80, 110, int(200 * a)), width=34 * K, joint="curve")
    d.line(pts, fill=(235, 150, 175, int(220 * a)), width=4 * K, joint="curve")
    if wave is not None:          # peristalsis rings
        for k in range(4):
            f = (wave - k * 0.08)
            if 0 < f < 1:
                x, y = along(f)
                d.ellipse(((x - 26) * K, (y - 26) * K, (x + 26) * K, (y + 26) * K), outline=(255, 210, 225, A),
                          width=4 * K)
    # eyes on the head (friendly)
    for kx in (-1, 1):
        d.ellipse(((540 + kx * 32 - 8) * K, (530 - 8) * K, (540 + kx * 32 + 8) * K, (530 + 8) * K),
                  fill=XR_LINE + (A,))
    st.im.paste(lay, (0, 0), lay)
    st.d = ImageDraw.Draw(st.im)


def gum(st, x, y, r=17, a=1.0):
    if a <= 0.01:
        return
    st.glow(x, y, r * 4, PINK, 0.5 * a)
    st.circ(x, y, r, fill=mix((40, 20, 30), PINK, a))
    st.circ(x - r * 0.35, y - r * 0.35, r * 0.3, fill=mix((40, 20, 30), (255, 210, 235), a))


def card(o, t, t_in, label, value, col, side="L", a=1.0, bar=None):
    k = eo(prog(t, t_in, 0.35)) * a
    x0, x1 = (80, 500) if side == "L" else (520, 940)
    o.card(x0, 250, x1, 400, label, value, col, k, bar=bar)


# ------------------------------------------------------------------ scenes
def s_hook(t, sc, gt):
    st, o = Stage(), Over()
    L.S.floor_line(st)
    chew = math.sin(gt * 9) * 4
    hx, hy = figure(st, 540, 975, 1.3, pose(head=chew, eyes=1, ba=(18, 20), fa=(-10, 30)))
    t_v = wt(sc, "verschluckst")
    # bubble grows, pops, then the gum drops down the throat
    t_pop = t_v - 0.45
    if t < t_pop:
        r = 18 + 70 * eo(prog(t, 0.1, t_pop - 0.1))
        st.glow(hx + 50 + r * 0.6, hy + 16, r * 2.2, PINK, 0.35)
        st.circ(hx + 50 + r * 0.6, hy + 16, r, fill=(255, 140, 200))
        st.circ(hx + 40 + r * 0.4, hy + 4 - r * 0.3, r * 0.25, fill=(255, 210, 235))
    else:
        u = prog(t, t_pop, 0.25)
        for k in range(8):
            ang = k / 8 * 2 * math.pi
            rr = 40 + 80 * u
            st.circ(hx + 70 + rr * math.cos(ang), hy + 16 + rr * math.sin(ang), 8 * (1 - u), fill=PINK)
        f = prog(t, t_v, 0.7)
        if f > 0:
            gum(st, hx + 5, hy + 30 + 230 * eio(f), 12, 1 - prog(t, t_v + 0.6, 0.2))
            chip(o, "GLUCK!", hx + 160, hy - 40, PINK, eo(prog(t, t_v, 0.2)) * (1 - prog(t, t_v + 0.9, 0.2)))
    brand(o, t)
    question(o, "WAS PASSIERT JETZT?", t, 0.4, y=320, size=60)
    return st, o, 1.0 + 0.04 * eio(prog(t, 0, sc["dur"])), (540, 900)


def s_myth(t, sc, gt):
    st, o = Stage(), Over()
    a = eo(prog(t, 0.0, 0.5))
    xray(st, a, gt)
    gum(st, STOMACH[0] - 10, STOMACH[1] + 10 + 4 * math.sin(gt * 2), 17, a)
    t7, ts = wt(sc, "7"), wt(sc, "stimmt")
    y = int(7 * eo(prog(t, t7 - 0.2, 0.8)))
    card(o, t, t7 - 0.3, "MYTHOS", f"{y} JAHRE", CORAL, "L")
    card(o, t, ts - 0.2, "STIMMT DAS?", "???", AMBER, "R")
    chip(o, "IM MAGEN", STOMACH[0] + 170, STOMACH[1] - 70, PINK, eo(prog(t, 0.6, 0.3)))
    return st, o, 1.0, (540, 900)


def s_enzyme(t, sc, gt):
    st, o = Stage(), Over()
    xray(st, 1.0, gt)
    gx, gy = STOMACH[0] - 10, STOMACH[1] + 10
    gum(st, gx, gy + 4 * math.sin(gt * 2), 17)
    t_e = wt(sc, "Enzym")
    rr = random.Random(5)
    n = int(14 * eo(prog(t, 0.3, 1.5)))
    for k in range(n):
        ph = rr.uniform(0, 6.28)
        sp = rr.uniform(1.5, 3.0)
        rad = 32 + 26 * abs(math.sin(gt * sp + ph))      # dart in, bounce off
        ang = ph + gt * 0.6
        x, y = gx + rad * math.cos(ang) * 1.3, gy + rad * math.sin(ang)
        st.circ(x, y, 6, fill=GREEN)
    if t > t_e - 0.3:
        chip(o, "ENZYME", gx - 170, gy - 90, GREEN, eo(prog(t, t_e - 0.3, 0.3)))
    t_n = wt(sc, "nicht")
    card(o, t, t_n - 0.3, "VERDAUT", "0 %", CORAL, "L")
    card(o, t, t_e, "KAUMASSE", "BLEIBT", AMBER, "R")
    return st, o, 1.06, (560, 930)


def s_travel(t, sc, gt):
    st, o = Stage(), Over()
    t_w, t_t = wt(sc, "weiter"), wt(sc, "Tagen")
    f = F_STOMACH + (1 - F_STOMACH) * eio(prog(t, wt(sc, "Darm") - 0.2, (t_t + 0.8) - (wt(sc, "Darm") - 0.2)))
    xray(st, 1.0, gt, wave=f + 0.05)
    x, y = along(f)
    gum(st, x, y, 21, 1 - prog(f, 0.98, 0.02))
    day = 1 + int(2.999 * prog(t, wt(sc, "Darm"), t_t - wt(sc, "Darm") + 0.6))
    card(o, t, 0.1, "UNTERWEGS", f"TAG {day}", AMBER, "L")
    # myth card gets crossed out
    k = eo(prog(t, 0.1, 0.3))
    o.card(520, 250, 940, 400, "MYTHOS", "7 JAHRE", CORAL, k)
    p = eo(prog(t, wt(sc, "liegen") - 0.1, 0.35))
    if p > 0:
        o.d.line((540 * K, 360 * K, (540 + 380 * p) * K, (300 - 10 * p) * K), fill=CORAL + (255,), width=10 * K)
        o.text("FALSCH!", 46, 730, 450, CORAL, path=MONO_XB, a=p, sc=0.9 + 0.1 * bo(p))
    if t > t_t + 0.4:
        chip(o, "WIEDER DRAUSSEN", 540, 1290, GREEN, eo(prog(t, t_t + 0.4, 0.3)))
    return st, o, 1.0, (540, 900)


def s_danger(t, sc, gt):
    st, o = Stage(), Over()
    t_v, t_k, t_d = wt(sc, "viele"), wt(sc, "Kindern"), wt(sc, "verstopft")
    alarm = 0.5 + 0.5 * math.sin(gt * 9) if t > t_k else 0.0
    xray(st, 1.0, gt, alarm=0.4 * alarm)
    n = int(12 * eo(prog(t, t_v - 0.6, 1.6)))
    cx, cy = along(0.74)
    for k in range(n):
        f0 = 0.25 + 0.05 * k
        f = min(0.74, f0 + 0.6 * prog(t, t_v - 0.6 + k * 0.1, 1.2))
        x, y = along(f)
        if f >= 0.74:            # clump
            a = k * 2.4
            x, y = cx + 16 * math.cos(a) * (k ** 0.5) / 2, cy + 14 * math.sin(a) * (k ** 0.5) / 2
        gum(st, x, y, 16)
    if t > t_k - 0.2:
        st.glow(cx, cy, 150, CORAL, 0.22 * (0.5 + 0.5 * alarm))
        chip(o, "KLUMPEN!", cx + 190, cy - 40, CORAL, eo(prog(t, t_d - 0.6, 0.3)))
    card(o, t, 0.1, "NUR WENN", "SEHR VIELE", AMBER, "L")
    card(o, t, t_k - 0.2, "VOR ALLEM", "KINDER", CORAL, "R")
    return st, o, 1.04, (560, 1000)


def s_outro(t, sc, gt):
    st, o = Stage(), Over()
    L.S.floor_line(st)
    chew = math.sin(gt * 9) * 4
    hx, hy = figure(st, 540, 975, 1.3, pose(head=chew, eyes=1, ba=(-150, 10), fa=(150, -10)))
    r = 22 + 20 * (0.5 + 0.5 * math.sin(gt * 2))
    st.circ(hx + 50 + r * 0.6, hy + 16, r, fill=(255, 140, 200))
    brand(o, t)
    question(o, "HÄTTEST DU'S GEWUSST?", t, 0.1, y=320, size=58)
    outro_cta(o, t, gt, t_in=wt(sc, "Schreib's") - 0.2)
    return st, o, 1.0, (540, 900)


def sfx():
    sc = L.SCENES
    out = [(sc[0]["start"] + wt(sc[0], "verschluckst") - 0.45, "pop", 0.25),
           (sc[0]["start"] + wt(sc[0], "verschluckst"), "gulp", 0.3),
           (sc[1]["start"] + wt(sc[1], "7"), "hit", 0.25),
           (sc[3]["start"] + wt(sc[3], "liegen"), "hit", 0.2),
           (sc[3]["start"] + wt(sc[3], "draußen"), "ding", 0.18)]
    for k in range(6):
        out.append((sc[4]["start"] + wt(sc[4], "Kindern") + k * 0.35, "alarm", 0.05))
    return out


L.setup(HERE, "kaugummi_verschluckt.mp4", [s_hook, s_myth, s_enzyme, s_travel, s_danger, s_outro], tempo=1.05,
        sfx=sfx)

if __name__ == "__main__":
    L.main()

#!/usr/bin/env python3
"""Rate mal, was passiert, wenn du die Luft anhältst, so lange du kannst? – dark stick-figure style, German VO."""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import lib as L  # noqa: E402
from lib import (Stage, Over, figure, pose, prog, eo, eio, bo, mix, wt, brand, question, outro_cta, chip,  # noqa
                 K, TXT, DIM, AMBER, CORAL, BLUE, GREEN, TONE_COOL, MONO_XB)

S = L.S
XR_FILL = (18, 26, 48)
XR_LINE = (110, 150, 230)
LUNGS = ((470, 880), (610, 880))


def card(o, t, t_in, label, value, col, side="L", a=1.0, bar=None):
    k = eo(prog(t, t_in, 0.35)) * a
    x0, x1 = (80, 500) if side == "L" else (520, 940)
    o.card(x0, 250, x1, 400, label, value, col, k, bar=bar)


def mmss(sec):
    sec = int(sec)
    return f"{sec // 60:02d}:{sec % 60:02d}"


def bust(st, gt, co2=0.0, alarm=0.0, twitch=0.0, breathe=0.0, puff=1.0):
    """x-ray bust with lungs: blue O2 dots get replaced by red CO2 dots"""
    lay = Image.new("RGBA", st.im.size)
    d = ImageDraw.Draw(lay)

    def rr(box, r, fill, outline, w=5):
        d.rounded_rectangle([v * K for v in box], int(r * K), fill=fill, outline=outline, width=int(w * K))

    line = mix(XR_LINE, CORAL, alarm)
    rr((380, 690, 700, 1260), 130, XR_FILL + (210,), line + (255,))
    rr((300, 720, 390, 1180), 45, XR_FILL + (210,), line + (255,))
    rr((690, 720, 780, 1180), 45, XR_FILL + (210,), line + (255,))
    rr((505, 630, 575, 720), 20, XR_FILL + (220,), line + (255,))
    d.ellipse((440 * K, 440 * K, 640 * K, 640 * K), fill=XR_FILL + (230,), outline=line + (255,), width=5 * K)
    # cheeks (held breath)
    if puff > 0.02:
        for kx in (-1, 1):
            cx = 540 + kx * 70
            d.ellipse(((cx - 30 * puff) * K, (575 - 26 * puff) * K, (cx + 30 * puff) * K, (575 + 26 * puff) * K),
                      fill=(70, 90, 150, int(200 * puff)))
    d.line((515 * K, 590 * K, 565 * K, 590 * K), fill=line + (255,), width=5 * K)       # closed mouth
    for kx in (-1, 1):
        d.ellipse(((540 + kx * 34 - 8) * K, 515 * K, (540 + kx * 34 + 8) * K, 531 * K), fill=line + (255,))
    # lungs
    sc_ = 1 + 0.06 * breathe
    lcol = mix((70, 110, 190), CORAL, alarm * (0.5 + 0.5 * math.sin(gt * 12)))
    for (cx, cy) in LUNGS:
        d.ellipse(((cx - 70 * sc_) * K, (cy - 120 * sc_) * K, (cx + 70 * sc_) * K, (cy + 120 * sc_) * K),
                  fill=lcol + (120,), outline=lcol + (255,), width=4 * K)
    # diaphragm
    tw = twitch * 18 * math.sin(gt * 25)
    pts = [((380 + k * 32) * K, (1030 - 40 * math.sin(k / 10 * math.pi) + tw * math.sin(k / 10 * math.pi)) * K)
           for k in range(11)]
    d.line(pts, fill=mix((200, 200, 220), CORAL, twitch) + (255,), width=6 * K, joint="curve")
    # gas dots
    rr_ = random.Random(2)
    for k in range(40):
        cx, cy = LUNGS[k % 2]
        a = rr_.uniform(0, 6.28)
        q = rr_.uniform(0, 0.85)
        x = cx + 55 * q * math.cos(a + gt * 0.3)
        y = cy + 100 * q * math.sin(a + gt * 0.3)
        is_co2 = (k / 40) < co2
        col = CORAL if is_co2 else (120, 190, 255)
        d.ellipse(((x - 7) * K, (y - 7) * K, (x + 7) * K, (y + 7) * K), fill=col + (255,))
    st.im.paste(lay, (0, 0), lay)
    st.d = ImageDraw.Draw(st.im)


# ------------------------------------------------------------------ scenes
def s_hook(t, sc, gt):
    st, o = Stage(), Over()
    inhale = eio(prog(t, 0.0, 0.8))
    bust(st, gt, co2=0.0, breathe=inhale, puff=eo(prog(t, 0.6, 0.4)))
    k = eo(prog(t, 0.1, 0.4))
    o.card(80, 250, 500, 400, "LUFT ANGEHALTEN", mmss(max(0, t - 0.8) * 4), AMBER, k)
    o.card(520, 250, 940, 400, "CO2 IM KÖRPER", "STEIGT", CORAL, k, bar=0.1 + 0.1 * prog(t, 0.8, 3))
    brand(o, t, y=180)
    return st, o, 1.0 + 0.04 * eio(prog(t, 0, sc["dur"])), (540, 880)


def s_co2(t, sc, gt):
    st, o = Stage(), Over()
    tk, tsau = wt(sc, "Kohlendioxid"), wt(sc, "Sauerstoff")
    co2 = 0.15 + 0.55 * eio(prog(t, 0.2, sc["dur"] - 0.4))
    bust(st, gt, co2=co2)
    secs = 12 + 78 * prog(t, 0, sc["dur"])
    card(o, t, -1, "LUFT ANGEHALTEN", mmss(secs), AMBER, "L")
    card(o, t, -1, "CO2 IM KÖRPER", f"{int(co2 * 100)} %", CORAL, "R", bar=co2)
    chip(o, "NORMAL: 1–2 MIN", 540, 470, AMBER, eo(prog(t, wt(sc, "Minuten") - 0.4, 0.3)) *
         (1 - prog(t, tsau - 0.5, 0.3)), size=30)
    if t > tsau - 0.3:
        chip(o, "NICHT DER SAUERSTOFF …", 540, 470, (120, 190, 255), eo(prog(t, tsau - 0.3, 0.3)) *
             (1 - prog(t, tk - 0.3, 0.2)), size=30)
    if t > tk - 0.2:
        chip(o, "… SONDERN DAS CO2!", 540, 470, CORAL, eo(prog(t, tk - 0.2, 0.3)), size=30)
    return st, o, 1.0, (540, 880)


def s_alarm(t, sc, gt):
    st, o = Stage(), Over()
    tz, ta = wt(sc, "Zwerchfell"), wt(sc, "Alarm")
    alarm = eo(prog(t, ta - 0.3, 0.4))
    twitch = eo(prog(t, tz, 0.3))
    bust(st, gt, co2=0.75 + 0.15 * prog(t, 0, sc["dur"]), alarm=alarm, twitch=twitch)
    card(o, t, -1, "LUFT ANGEHALTEN", mmss(90 + 30 * prog(t, 0, sc["dur"])), AMBER, "L")
    card(o, t, -1, "CO2 IM KÖRPER", "ALARM!", CORAL, "R", bar=0.8 + 0.2 * prog(t, 0, sc["dur"]))
    if t > tz - 0.2:
        chip(o, "ZWERCHFELL ZUCKT", 730, 1110, CORAL, eo(prog(t, tz - 0.2, 0.3)), size=30)
    pulse = alarm * (0.5 + 0.5 * math.sin(gt * 10))

    def extra(arr, x0, y0, s_):
        if pulse > 0:
            yy, xx = L._yy, L._xx
            edge = ((xx - 540) / 620) ** 2 + ((yy - 900) / 1000) ** 2
            arr[..., 0] += 60 * pulse * edge.clip(0, 1)
        return arr

    return st, o, 1.03 + 0.02 * math.sin(gt * 20) * twitch, (540, 880), extra


def s_faint(t, sc, gt):
    st, o = Stage(), Over()
    S.floor_line(st)
    to, ta, tl, tu = wt(sc, "ohnmächtig"), wt(sc, "atmet"), wt(sc, "Land"), wt(sc, "Unter")
    fall = eio(prog(t, to - 0.3, 0.9))
    fa_ = 1 - eio(prog(t, tu - 0.5, 0.5))
    if fall < 1:
        p = pose(torso=-5 + 20 * fall, head=10 * fall, eyes=1 - fall, closed=fall > 0.5,
                 bl=(60 * fall, -100 * fall), fl=(50 * fall, -110 * fall), ba=(20, 10), fa=(-10, 10))
        figure(st, 520, 985 + 170 * fall, 1.15, p, alpha=fa_)
    else:
        figure(st, 520, 1110, 1.15, pose(rot=-80, closed=1, ba=(10, 10), fa=(-20, 10)), alpha=fa_)
    br = 0.0
    if t > ta - 0.2:
        br = 0.5 + 0.5 * math.sin((t - ta) * 4)
        for k in range(3):
            ph = ((t - ta) * 0.8 + k / 3) % 1
            if fa_ > 0.5:
                st.circ(380 - 120 * ph, 1080 - 60 * ph, 10 + 18 * ph, outline=(120, 190, 255), w=3)
        chip(o, "ATMET AUTOMATISCH", 540, 470, GREEN, eo(prog(t, ta - 0.2, 0.3)) * (1 - prog(t, tu - 0.4, 0.3)),
             size=30)
    if t > tl - 0.2 and t < tu - 0.3:
        chip(o, "AN LAND: KEIN ERSTICKEN", 540, 540, AMBER, eo(prog(t, tl - 0.2, 0.3)), size=30)
    water = eio(prog(t, tu - 0.3, 0.9))
    card(o, t, -1, "LUFT ANGEHALTEN", "STOPP", AMBER, "L", a=1 - water)
    card(o, t, ta - 0.3, "KÖRPER ATMET", "WIEDER", GREEN, "R", a=1 - water)
    if water > 0:
        p = prog(t, tu, 0.35)
        q = bo(prog(t, tu + 0.2, 0.45))
        if q > 0.02:
            r = 170 * q
            cy = 880
            A = int(255 * eo(p))
            o.d.polygon([(540 * K, (cy - r) * K), ((540 + r * 1.1) * K, (cy + r * 0.8) * K),
                         ((540 - r * 1.1) * K, (cy + r * 0.8) * K)], fill=(30, 10, 10, int(200 * eo(p))),
                        outline=CORAL + (A,), width=int(12 * K))
            o.text("!", 190 * q, 540, cy + 20 * q, CORAL, a=eo(p))
        o.text("UNTER WASSER:", 64, 540, 330, TXT, a=eo(p))
        o.text("LEBENSGEFAHR!", 84, 540, 420, CORAL, a=eo(prog(t, tu + 0.3, 0.35)), sc=0.9 + 0.1 * bo(
            prog(t, tu + 0.3, 0.35)))
    dim = 0.65 * eo(prog(t, to - 0.2, 0.6)) * (1 - eo(prog(t, ta - 0.3, 0.8)))

    def extra(arr, x0, y0, s_):
        if dim > 0:
            arr *= (1 - dim)
        if water > 0:
            lvl = 1920 - 1300 * water
            yy = L._yy
            mask = (yy > lvl + 10 * L.np.sin(L._xx / 60 + gt * 3)).astype(L.np.float32)[..., None]
            tint = L.np.array([20, 70, 150], L.np.float32)
            arr = arr * (1 - 0.55 * mask) + tint * 0.55 * mask
        return arr

    return st, o, 1.02, (540, 950), extra


def s_record(t, sc, gt):
    st, o = Stage(), Over()
    t29 = wt(sc, "29")
    v = 29 * 60 + 3
    secs = v * eio(prog(t, t29 - 0.9, 1.3))
    st.glow(540, 860, 420, AMBER, 0.25 * eo(prog(t, t29, 0.5)))
    o.text(mmss(secs), 190, 540, 860, AMBER, path=MONO_XB, a=eo(prog(t, 0.1, 0.3)))
    o.text("WELTREKORD", 46, 540, 700, DIM, path=MONO_XB, a=eo(prog(t, 0.1, 0.3)))
    chip(o, "JAHRELANGES TRAINING", 540, 1060, AMBER, eo(prog(t, wt(sc, "Training") - 0.3, 0.3)), size=30)
    chip(o, "REINER SAUERSTOFF VORHER", 540, 1150, (120, 190, 255), eo(prog(t, wt(sc, "Sauerstoff") - 0.3, 0.3)),
         size=30)
    chip(o, "2025 · OPATIJA", 540, 560, DIM, eo(prog(t, t29 + 0.4, 0.3)), size=26)
    return st, o, 1.0, (540, 900)


def s_outro(t, sc, gt):
    st, o = Stage(), Over()
    S.floor_line(st)
    br = 0.5 + 0.5 * math.sin(gt * 2.2)
    figure(st, 540, 985, 1.15, pose(torso=-2 * br, head=-4 * br, eyes=1, ba=(20 + 8 * br, 10), fa=(-14, 10)))
    brand(o, t)
    question(o, "HÄTTEST DU DAS GEDACHT?", t, 0.1, y=320, size=50)
    outro_cta(o, t, gt, t_in=wt(sc, "Schreib's") - 0.2)
    return st, o, 1.0, (540, 950)


def sfx():
    sc = L.SCENES
    out = [(0.0, "breath", 0.25)]
    for i in range(1, 3):
        rate = 0.8 if i == 1 else 0.45
        for k in range(int(sc[i]["dur"] / rate)):
            out.append((sc[i]["start"] + k * rate, "heart", 0.25 if i == 2 else 0.15))
    for k in range(5):
        out.append((sc[2]["start"] + wt(sc[2], "Alarm") + k * 0.4, "alarm", 0.04))
    out += [(sc[3]["start"] + wt(sc[3], "atmet") - 0.2, "breath", 0.3),
            (sc[3]["start"] + wt(sc[3], "Unter") - 0.3, "splash", 0.12),
            (sc[4]["start"] + wt(sc[4], "29") + 0.4, "ding", 0.16)]
    return out


L.setup(HERE, "luft_anhalten.mp4", [s_hook, s_co2, s_alarm, s_faint, s_record, s_outro], tempo=1.1, sfx=sfx)

if __name__ == "__main__":
    L.main()

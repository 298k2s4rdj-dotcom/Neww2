#!/usr/bin/env python3
"""Rate mal, was passiert, wenn du eine ganze Nacht nicht schläfst? – dark stick-figure style, German voice-over."""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import lib as L  # noqa: E402
from lib import (Stage, Over, figure, pose, walk, prog, eo, eio, bo, mix, wt, brand, question, outro_cta, chip,  # noqa
                 K, TXT, DIM, AMBER, CORAL, BLUE, GREEN, TONE_COOL, TONE_OLD, tone_mix, MONO_XB)

S = L.S


def card(o, t, t_in, label, value, col, side="L", a=1.0, bar=None):
    k = eo(prog(t, t_in, 0.35)) * a
    x0, x1 = (80, 500) if side == "L" else (520, 940)
    o.card(x0, 250, x1, 400, label, value, col, k, bar=bar)


def bedroom(st, gt):
    S.window(st)
    S.floor_line(st)
    S.bed(st)


def stumble_walk(st, t, gt, x0, x1, dur, wob, tone=TONE_COOL, eyes=1.0):
    p = min(1.0, t / dur)
    x = x0 + (x1 - x0) * p
    ph = gt * 7.5
    pz = walk(ph, lean=4 + wob * 10 * math.sin(gt * 2.1))
    pz["head"] += wob * 14 * math.sin(gt * 1.7)
    pz["eyes"] = eyes
    pz["closed"] = 1.0 if eyes <= 0 else 0.0
    sway = wob * 26 * math.sin(gt * 2.3)
    figure(st, x + sway, 985 - 6 * math.cos(2 * ph), 1.1, pz, tone=tone)


def balance_line(st):
    for x in range(120, 980, 60):
        st.line([(x, 1182), (x + 30, 1182)], 6, AMBER)


# ------------------------------------------------------------------ scenes
def s_hook(t, sc, gt):
    st, o = Stage(), Over()
    bedroom(st, gt)
    p = S.sitting(0.4)
    p.update(fa=(150, -40), eyes=1)
    hx, hy = figure(st, 360, 1000, 1.05, p)
    st.glow(hx + 70, hy + 30, 90, BLUE, 0.55)
    st.rr(hx + 50, hy + 10, hx + 80, hy + 60, 6, fill=(170, 200, 255), outline=None)
    k = eo(prog(t, 0.1, 0.4))
    o.card(80, 250, 500, 400, "UHRZEIT", f"0{2 + int(prog(t, 0.2, 2.5) * 2)}:{int(prog(t, 0.2, 2.5) * 59):02d}"
           if t < 2.7 else "04:00", AMBER, k)
    o.card(520, 250, 940, 400, "SCHLAF", "0 STD", CORAL, k)
    brand(o, t, y=180)
    return st, o, 1.0 + 0.05 * eio(prog(t, 0, sc["dur"])), (540, 950)


def s_17(t, sc, gt):
    st, o = Stage(), Over()
    S.floor_line(st)
    balance_line(st)
    t17, t05 = wt(sc, "17"), wt(sc, "0,5")
    wob = 0.3 + 0.4 * eo(prog(t, t05, 1.0))
    stumble_walk(st, t, gt, 200, 820, sc["dur"], wob)
    h = int(17 * eo(prog(t, t17 - 0.3, 0.8)))
    card(o, t, 0.0, "WACH SEIT", f"{h} STD", AMBER, "L")
    v = 0.5 * eo(prog(t, t05 - 0.2, 0.7))
    card(o, t, t05 - 0.2, "WIE MIT PROMILLE", f"{v:.1f}".replace(".", ","), CORAL, "R")
    if t > t05:
        chip(o, "REAKTION WIE BETRUNKEN", 540, 470, CORAL, eo(prog(t, t05 + 0.3, 0.3)), size=30)
    return st, o, 1.03, (540, 950)


def s_24(t, sc, gt):
    st, o = Stage(), Over()
    S.floor_line(st)
    balance_line(st)
    t24, t1, ts = wt(sc, "24"), wt(sc, "1"), wt(sc, "Sekundenschlaf")
    # micro-sleeps: two short blackouts
    blk = 0.0
    for c in (ts - 0.1, ts + 0.9):
        if c <= t < c + 0.45:
            blk = math.sin((t - c) / 0.45 * math.pi)
    stumble_walk(st, t, gt, 250, 760, sc["dur"], 0.8, eyes=0.0 if blk > 0.3 else 1.0)
    h = 17 + int(7 * eo(prog(t, t24 - 0.3, 0.8)))
    card(o, t, -1, "WACH SEIT", f"{h} STD", AMBER, "L")
    v = 0.5 + 0.5 * eo(prog(t, t1 - 0.3, 0.7))
    card(o, t, -1, "WIE MIT PROMILLE", f"{v:.1f}".replace(".", ","), CORAL, "R")
    if t > ts - 0.2:
        chip(o, "SEKUNDENSCHLAF", 540, 470, CORAL, eo(prog(t, ts - 0.2, 0.3)))

    def extra(arr, x0, y0, sc_):
        if blk > 0:
            arr *= (1 - 0.92 * blk)
        return arr

    return st, o, 1.03 + 0.03 * eio(prog(t, 0, sc["dur"])), (540, 950), extra


def fridge(st, gt, open_=1.0):
    x0, x1, y0 = 640, 880, 720
    if open_ > 0:
        st.glow(760, 960, 300, (255, 230, 170), 0.35 * open_)
    st.rr(x0, y0, x1, S.FLOOR, 16, fill=(36, 38, 48))
    st.rr(x0 + 14, y0 + 14, x1 - 14, S.FLOOR - 14, 10, fill=mix((30, 30, 40), (255, 240, 200), open_), outline=None)
    for y in (850, 980, 1090):
        st.line([(x0 + 20, y), (x1 - 20, y)], 5, mix((50, 50, 60), (220, 200, 160), open_))
    st.rr(x0 + 40, 800, x0 + 110, 845, 8, fill=(230, 120, 90), outline=None)
    st.rr(x0 + 130, 930, x0 + 200, 975, 8, fill=(120, 200, 120), outline=None)
    # door
    st.poly([(x1, y0), (x1 + 80 * open_, y0 + 30), (x1 + 80 * open_, S.FLOOR - 30), (x1, S.FLOOR)], (50, 52, 64))


def s_hunger(t, sc, gt):
    st, o = Stage(), Over()
    S.floor_line(st)
    fridge(st, gt, eo(prog(t, 0.1, 0.6)))
    bite = 0.5 + 0.5 * math.sin(gt * 5)
    p = pose(torso=6, head=-4, fa=(150 - 40 * bite, 40), ba=(20, 30), eyes=1)
    hx, hy = figure(st, 470, 985, 1.1, p)
    st.rr(hx + 22, hy + 10, hx + 62, hy + 40, 8, fill=(240, 190, 90), outline=None)
    t22 = wt(sc, "22")
    v = 22 * eo(prog(t, t22 - 0.3, 0.9))
    card(o, t, wt(sc, "Studie") - 0.3, "HUNGERHORMON", f"+{int(v)} %", CORAL, "L", bar=0.5 + 0.5 * v / 22 * 0.44)
    card(o, t, wt(sc, "Nacht") - 0.3, "NACH NUR", "1 NACHT", AMBER, "R")
    return st, o, 1.02, (560, 950)


def s_record(t, sc, gt):
    st, o = Stage(), Over()
    S.floor_line(st)
    t64, t11, tn, tg = wt(sc, "1964"), wt(sc, "11"), wt(sc, "nachmachen"), wt(sc, "Guinness")
    age = eo(prog(t, t11 - 0.3, 1.0))
    stumble_walk(st, t, gt * 0.6, 330, 600, sc["dur"], 0.6 + 0.4 * age,
                 tone=tone_mix(TONE_COOL, TONE_OLD, 0.7 * age))
    card(o, t, t64 - 0.3, "REKORD", "1964", AMBER, "L")
    d = int(11 * age)
    card(o, t, t11 - 0.4, "OHNE SCHLAF", f"{d} TAGE", CORAL, "R")
    if t > tn - 0.6:
        p = prog(t, tn - 0.6, 0.35)
        o.text("NICHT NACHMACHEN!", 66, 540, 520, CORAL, a=eo(p), sc=0.9 + 0.1 * bo(p))
    if t > tg - 0.2:
        chip(o, "GUINNESS: KEINE REKORDE MEHR", 540, 610, DIM, eo(prog(t, tg - 0.2, 0.3)), size=28)
    return st, o, 1.02, (540, 950)


def s_outro(t, sc, gt):
    st, o = Stage(), Over()
    bedroom(st, gt)
    figure(st, 470, 985, 1.0, pose(rot=-90, ba=(170, -10), fa=(10, 0), closed=1))
    S.blanket(st, 1.0)
    for k in range(3):
        ph = (gt * 0.5 + k / 3) % 1
        o.text("z", 40 + 26 * ph, 260 + 60 * ph + k * 6, 900 - 220 * ph, DIM, path=MONO_XB, a=math.sin(ph * math.pi))
    brand(o, t)
    question(o, "WIE LANGE WARST DU WACH?", t, 0.1, y=320, size=48)
    outro_cta(o, t, gt, t_in=wt(sc, "Schreib's") - 0.2)
    return st, o, 1.0, (540, 950)


def sfx():
    sc = L.SCENES
    out = []
    for i in range(1, 3):
        for k in range(int(sc[i]["dur"] / 0.5)):
            out.append((sc[i]["start"] + k * 0.5, "tick", 0.06))
    out += [(sc[1]["start"] + wt(sc[1], "0,5"), "hit", 0.2), (sc[2]["start"] + wt(sc[2], "1"), "hit", 0.22),
            (sc[3]["start"] + wt(sc[3], "22"), "ding", 0.14), (sc[4]["start"] + wt(sc[4], "nachmachen") - 0.5, "hit",
                                                               0.22)]
    return out


L.setup(HERE, "nacht_ohne_schlaf.mp4", [s_hook, s_17, s_24, s_hunger, s_record, s_outro], tempo=1.07, sfx=sfx)

if __name__ == "__main__":
    L.main()

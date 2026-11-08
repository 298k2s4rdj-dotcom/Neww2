"""Shared engine for the animated German "X vs. Y" TikTok comparison videos.

A video script (e.g. tiere/blauwal/render.py) calls `setup(...)` with its
names, colours, scene drawers and score events, then `main()`.

Everything is drawn procedurally with Pillow/NumPy; voice per scene from
ElevenLabs (audio_raw/s*.mp3) with Scribe word timings (audio_raw/w*.json);
sound effects are synthesised here.
"""
import json
import math
import os
import random
import subprocess
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
SR = 48000
GAP, HOLD, XF = 0.10, 0.9, 0.25
SAFE_T, SAFE_B, SAFE_R = 150, H - 400, W - 140
SPLIT, CXL, CXR = 540, 290, 740   # exakte 50:50-Teilung; rechts bleibt der TikTok-Rand (x > 940) frei
VIS_Y, NUM_Y, SUB_Y = 700, 1085, 1395
GROUND = 1000
WHITE = (255, 255, 255)
C_HI = (255, 226, 60)

FONT_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
_fonts = {}

CFG = {}
SCENES = []
SCORE = []          # list of (global_time, side) side in "L", "R"
TOTAL = 0.0
NFRAMES = 0
BG = None
STARS = []


def F(size, path=FONT_BLACK):
    key = (int(size), path)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, max(4, int(size)))
    return _fonts[key]


# ------------------------------------------------------------------ easing / format
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def back_out(x, s=1.9):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def prog(t, t0, d):
    return clamp((t - t0) / d) if d > 0 else float(t >= t0)


def fmt_int(n):
    return f"{int(round(n)):,}".replace(",", ".")


def fmt_dec(x, nd=1):
    return f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ timeline
PUNCT = ".,:;!?-"


def strip(w):
    return w.strip(PUNCT)


def wt(sc, word, n=1, edge="s"):
    c = 0
    for w in sc["words"]:
        if strip(w["text"]).lower() == word.lower():
            c += 1
            if c == n:
                return w[edge]
    raise KeyError(word)


def build_timeline():
    global TOTAL, NFRAMES
    raw_dir = CFG["raw"]
    n = len(CFG["scenes"])
    loaded = []
    for i in range(n):
        words = json.load(open(os.path.join(raw_dir, f"w{i}.json")))["words"]
        words = [w for w in words if w.get("type") == "word"]
        loaded.append(words)
    raw_total = sum(ws[-1]["end"] + 0.06 for ws in loaded)
    target = CFG.get("target", 43.5) - GAP * (n - 1) - HOLD
    tempo = CFG.get("tempo") or clamp(raw_total / target, 1.08, 1.25)
    CFG["tempo_used"] = tempo
    t = 0.0
    SCENES.clear()
    for i, key in enumerate(CFG["scenes"]):
        words = loaded[i]
        end = words[-1]["end"] + 0.06
        out = os.path.join(CFG["build"], f"s{i}_{tempo:.3f}.wav")
        if not os.path.exists(out):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(raw_dir, f"s{i}.mp3"), "-af",
                            f"atrim=0:{end:.3f},atempo={tempo:.4f},afade=t=out:st={end / tempo - 0.04:.3f}:d=0.04",
                            "-ar", str(SR), "-ac", "1", out], check=True)
        with wave.open(out) as wf:
            alen = wf.getnframes() / wf.getframerate()
        sc = dict(key=key, wav=out, alen=alen, start=t, dur=alen + (HOLD if i == n - 1 else GAP))
        sc["words"] = [dict(text=w["text"], s=w["start"] / tempo, e=w["end"] / tempo) for w in words]
        toks, k, ws = [], 0, sc["words"]
        while k < len(ws):
            hit = None
            for pat, disp in CFG["sub_map"]:
                m = len(pat)
                if tuple(strip(w["text"]) for w in ws[k:k + m]) == pat:
                    hit = (m, disp)
                    break
            if hit:
                m, disp = hit
                tail = ws[k + m - 1]["text"]
                p = tail[len(tail.rstrip(PUNCT)):]
                toks.append(dict(text=disp + p, s=ws[k]["s"], e=ws[k + m - 1]["e"]))
                k += m
            else:
                toks.append(dict(ws[k]))
                k += 1
        sc["toks"] = toks
        SCENES.append(sc)
        t += sc["dur"]
    TOTAL = t
    NFRAMES = int(math.ceil(TOTAL * FPS))
    SCORE.clear()
    for si, word, occ, side in CFG["score"]:
        SCORE.append((SCENES[si]["start"] + wt(SCENES[si], word, occ), side))


# ------------------------------------------------------------------ drawing helpers
def text(img, s, size, cx, cy, fill=WHITE, scale=1.0, alpha=1.0, stroke=0, sfill=(0, 0, 0),
         path=FONT_BLACK, rotate=0.0, anchor="mm"):
    if alpha <= 0.01 or scale <= 0.02:
        return (0, 0)
    font = F(size * scale, path)
    sw = int(round(stroke * scale))
    bb = font.getbbox(s, stroke_width=sw)
    w, h = bb[2] - bb[0] + 8, bb[3] - bb[1] + 8
    layer = Image.new("RGBA", (w, h))
    ImageDraw.Draw(layer).text((4 - bb[0], 4 - bb[1]), s, font=font, fill=tuple(fill) + (255,),
                               stroke_width=sw, stroke_fill=tuple(sfill) + (255,))
    if rotate:
        layer = layer.rotate(rotate, resample=Image.BICUBIC, expand=True)
        w, h = layer.size
    if alpha < 0.999:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    if anchor == "mm":
        x, y = cx - w / 2, cy - h / 2
    elif anchor == "lm":
        x, y = cx, cy - h / 2
    else:
        x, y = cx - w, cy - h / 2
    img.paste(layer, (int(x), int(y)), layer)
    return (w, h)


def text_w(s, size, path=FONT_BLACK):
    bb = F(size, path).getbbox(s)
    return bb[2] - bb[0]


def rrect(img, box, radius, fill, outline=None, width=0):
    x0, y0, x1, y1 = [int(v) for v in box]
    if x1 <= x0 or y1 <= y0:
        return
    layer = Image.new("RGBA", (x1 - x0, y1 - y0))
    ImageDraw.Draw(layer).rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), radius, fill=fill,
                                            outline=outline, width=width)
    img.paste(layer, (x0, y0), layer)


def paste_c(img, sprite, cx, cy, alpha=1.0, anchor="c"):
    if alpha <= 0.01 or sprite is None:
        return
    if alpha < 0.999:
        sprite = sprite.copy()
        sprite.putalpha(sprite.getchannel("A").point(lambda v: int(v * alpha)))
    w, h = sprite.size
    x = cx - w / 2
    y = cy - h / 2 if anchor == "c" else cy - h      # "b": bottom-centre at (cx, cy)
    img.paste(sprite, (int(x), int(y)), sprite)


class SS:
    """Supersampled RGBA drawing canvas: draw in local coords, get antialiased sprite."""

    def __init__(self, w, h, k=2):
        self.k = k
        self.w, self.h = int(math.ceil(w)), int(math.ceil(h))
        self.im = Image.new("RGBA", (self.w * k, self.h * k))
        self.d = ImageDraw.Draw(self.im)

    def P(self, pts):
        return [(x * self.k, y * self.k) for x, y in pts]

    def poly(self, pts, fill):
        self.d.polygon(self.P(pts), fill=fill)

    def ell(self, cx, cy, rx, ry, fill, outline=None, width=0):
        k = self.k
        rx, ry = max(0.0, rx), max(0.0, ry)
        self.d.ellipse(((cx - rx) * k, (cy - ry) * k, (cx + rx) * k, (cy + ry) * k), fill=fill, outline=outline,
                       width=int(width * k))

    def rect(self, x0, y0, x1, y1, r, fill):
        k = self.k
        if x1 <= x0 or y1 <= y0:
            return
        r = max(0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
        self.d.rounded_rectangle((x0 * k, y0 * k, x1 * k, y1 * k), int(r * k), fill=fill)

    def line(self, pts, fill, width):
        self.d.line(self.P(pts), fill=fill, width=int(width * self.k), joint="curve")

    def thick(self, pts, widths, fill):
        """variable-width stroke along a polyline"""
        left, right = [], []
        for i, (x, y) in enumerate(pts):
            x0, y0 = pts[max(0, i - 1)]
            x1, y1 = pts[min(len(pts) - 1, i + 1)]
            dx, dy = x1 - x0, y1 - y0
            n = math.hypot(dx, dy) or 1
            nx, ny = -dy / n, dx / n
            w = widths[i] / 2
            left.append((x + nx * w, y + ny * w))
            right.append((x - nx * w, y - ny * w))
        self.poly(left + right[::-1], fill)
        self.ell(pts[0][0], pts[0][1], widths[0] / 2, widths[0] / 2, fill)
        self.ell(pts[-1][0], pts[-1][1], widths[-1] / 2, widths[-1] / 2, fill)

    def img(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS)


def person_sprite(h, color, squash=1.0, arms_up=0.0):
    """self-drawn standing person, h px tall; returns sprite (bottom = feet)"""
    h = max(6, h)
    w = h * 0.5 / max(squash, 0.45) ** 0.6
    s = SS(w + 4, h + 4)
    cx = (w + 4) / 2
    hh = h * squash
    top = h + 2 - hh
    head = hh * 0.13
    s.ell(cx, top + head, head, head, color)
    bw = w * 0.27
    s.rect(cx - bw, top + head * 2.1, cx + bw, top + hh * 0.62, bw * 0.6, color)
    lw = w * 0.11
    s.rect(cx - bw + 1, top + hh * 0.55, cx - bw + 1 + 2 * lw, h + 2, lw, color)
    s.rect(cx + bw - 1 - 2 * lw, top + hh * 0.55, cx + bw - 1, h + 2, lw, color)
    aw = w * 0.09
    ay = -0.25 * arms_up
    s.thick([(cx - bw, top + hh * 0.30), (cx - bw - w * 0.12, top + hh * (0.55 + ay))], [2 * aw, 1.8 * aw], color)
    s.thick([(cx + bw, top + hh * 0.30), (cx + bw + w * 0.12, top + hh * (0.55 + ay))], [2 * aw, 1.8 * aw], color)
    return s.img()


_icon_cache = {}


def person_icon(h, color):
    key = (int(h), tuple(color))
    if key not in _icon_cache:
        _icon_cache[key] = person_sprite(h, color)
    return _icon_cache[key]


def heart_sprite(size, color=(235, 40, 70), beat=0.0):
    size = max(6, int(size * (1 + 0.12 * beat)))
    s = SS(size, size)
    pts = []
    for i in range(80):
        a = i / 80 * 2 * math.pi
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((size / 2 + x / 34 * size, size * 0.46 - y / 34 * size))
    s.poly(pts, color)
    s.ell(size * 0.34, size * 0.3, size * 0.09, size * 0.06, (255, 255, 255, 110))
    return s.img()


def baby_sprite(h, color=(255, 214, 180), wrap=(250, 250, 255)):
    """swaddled human baby, h px long (lying), returns sprite"""
    w = h
    hh = h * 0.42
    s = SS(w + 4, hh + 4)
    s.ell(w * 0.56, hh / 2 + 2, w * 0.42, hh * 0.42, wrap)
    s.ell(w * 0.18, hh / 2 + 2, hh * 0.33, hh * 0.33, color)
    s.ell(w * 0.14, hh / 2 - hh * 0.05, hh * 0.04, hh * 0.04, (60, 40, 40))
    s.line([(w * 0.35, hh * 0.25), (w * 0.4, hh * 0.85)], (200, 200, 220), max(1, h * 0.02))
    return s.img()


# ------------------------------------------------------------------ background
def make_bg():
    y = np.linspace(0, 1, H)[:, None, None]
    lt, lb = np.array(CFG["bg_l"][0]), np.array(CFG["bg_l"][1])
    rt, rb = np.array(CFG["bg_r"][0]), np.array(CFG["bg_r"][1])
    left = lt * (1 - y) + lb * y
    right = rt * (1 - y) + rb * y
    xs = np.arange(W)[None, :, None]
    m = np.clip((xs - SPLIT + 3) / 6, 0, 1)
    bg = left * (1 - m) + right * m
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.35 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
    bg = bg * v[..., None]
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGB")


def draw_bg(img, t):
    d = ImageDraw.Draw(img)
    for x, y, s, ph, sp in STARS:
        b = 0.25 + 0.5 * (0.5 + 0.5 * math.sin(t * sp * 2 + ph))
        v = int(255 * b)
        y2 = (y - t * 14 * s) % H
        d.ellipse((x - s, y2 - s, x + s, y2 + s), fill=(v, v, v))


# ------------------------------------------------------------------ common UI
def header(img, gt, title, t, title_a=1.0):
    sl = sum(1 for st, side in SCORE if gt >= st and side in ("L", "B"))
    sr = sum(1 for st, side in SCORE if gt >= st and side in ("R", "B"))
    popl = popr = 1.0
    for st, side in SCORE:
        if 0 <= gt - st < 0.45:
            k = 1 + 0.6 * (1 - ease_out((gt - st) / 0.45))
            if side in ("L", "B"):
                popl = k
            if side in ("R", "B"):
                popr = k
    rrect(img, (SPLIT - 270, 168, SPLIT + 270, 238), 35, (0, 0, 0, 150), outline=(255, 255, 255, 60), width=2)
    for nm, col, x in ((CFG.get("short_l", CFG["name_l"]), CFG["col_l"], SPLIT - 170),
                       (CFG.get("short_r", CFG["name_r"]), CFG["col_r"], SPLIT + 170)):
        fs = min(32, 32 * 150 / max(1, text_w(nm, 32)))
        text(img, nm, fs, x, 203, fill=col)
    text(img, str(sl), 46, SPLIT - 50, 203, scale=popl, fill=C_HI if popl > 1.01 else WHITE)
    text(img, ":", 46, SPLIT, 200)
    text(img, str(sr), 46, SPLIT + 50, 203, scale=popr, fill=C_HI if popr > 1.01 else WHITE)
    if title:
        k = ease_out(prog(t, 0.0, 0.35))
        sc = 1.5 - 0.5 * back_out(prog(t, 0.0, 0.4))
        fs = min(60, 60 * 760 / max(1, text_w(title, 60)))
        text(img, title, fs, SPLIT, 298, scale=sc, alpha=k * title_a, stroke=5, sfill=(20, 10, 40))


def panel_labels(img, t, a=1.0, right=None):
    k = ease_out(prog(t, 0.05, 0.4)) * a
    nl, nr = CFG["name_l"], right or CFG["name_r"]
    fs = min(54, 54 * 380 / max(text_w(nl, 54), text_w(nr, 54), 1))
    text(img, nl, fs, CXL - (1 - k) * 120, 390, fill=CFG["col_l"], alpha=k, stroke=4, sfill=(0, 0, 0))
    text(img, nr, fs, CXR + (1 - k) * 120, 390, fill=CFG["col_r"], alpha=k, stroke=4, sfill=(0, 0, 0))


def vs_badge(img, t, a=1.0, y=VIS_Y, x=SPLIT):
    if a <= 0.02:
        return
    p = 1 + 0.06 * math.sin(t * 6)
    r = int(50 * p)
    layer = Image.new("RGBA", (2 * r + 30, 2 * r + 30))
    d = ImageDraw.Draw(layer)
    d.ellipse((15, 15, 15 + 2 * r, 15 + 2 * r), fill=(255, 255, 255, int(235 * a)),
              outline=(255, 226, 60, int(255 * a)), width=6)
    img.paste(layer, (int(x - r - 15), int(y - r - 15)), layer)
    text(img, "VS", 44 * p, x, y + 1, fill=(30, 20, 60), alpha=a)


def counter(img, cx, val, unit, color, a=1.0, size=68, y=NUM_Y):
    if a <= 0.01:
        return
    text(img, val, size, cx, y, alpha=a, stroke=6, sfill=(0, 0, 0))
    if unit:
        text(img, unit, 38, cx, y + 68, fill=color, alpha=a, stroke=4, sfill=(0, 0, 0), path=FONT_XB)


def stamp(img, s, t, t0, cx=SPLIT, cy=VIS_Y, size=140, rot=-8, hold=99.0, fill=C_HI, sfill=(170, 20, 0)):
    if t < t0:
        return
    p = prog(t, t0, 0.35)
    q = ease_io(prog(t, t0 + hold, 0.35))
    sc = (2.4 - 1.4 * back_out(p, 2.4)) * (1 - 0.6 * q)
    text(img, s, size, cx, cy, fill=fill, scale=sc, alpha=ease_out(p * 2) * (1 - q), stroke=12, sfill=sfill,
         rotate=rot)


def burst(img, cx, cy, t, t0, color=C_HI, n=16, rad=260):
    p = prog(t, t0, 0.6)
    if p <= 0 or p >= 1:
        return
    d = ImageDraw.Draw(img)
    e = ease_out(p)
    for i in range(n):
        a = i / n * 2 * math.pi + 0.3
        r0, r1 = rad * (0.35 + 0.6 * e), rad * (0.5 + 0.75 * e)
        d.line((cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
               fill=color, width=max(1, int(10 * (1 - p))))


def confetti(img, t, t0, n=90, y0=260):
    if t < t0:
        return
    d = ImageDraw.Draw(img)
    r = random.Random(8)
    for i in range(n):
        x0 = r.uniform(30, 920)
        vy = r.uniform(250, 520)
        u = t - t0
        y = y0 + u * vy - 60 * r.random()
        if y > SAFE_B - 20:
            continue
        x = x0 + 30 * math.sin(u * 4 + i)
        s = r.uniform(6, 12)
        col = r.choice([(255, 226, 60), (64, 196, 255), (255, 90, 90), (120, 255, 160), (255, 255, 255)])
        ang = u * 6 + i
        dx, dy = s * math.cos(ang), s * 0.5 * math.sin(ang)
        d.polygon([(x - dx, y - dy), (x + dy, y - dx * 0.5), (x + dx, y + dy), (x - dy, y + dx * 0.5)], fill=col)


def crown(img, cx, cy, p, size=1.0):
    if p <= 0:
        return
    s = SS(300 * size, 200 * size)
    k = size
    oy = 150 * k
    pts = [(30 * k, oy), (20 * k, oy - 110 * k), (90 * k, oy - 55 * k), (150 * k, oy - 135 * k),
           (210 * k, oy - 55 * k), (280 * k, oy - 110 * k), (270 * k, oy)]
    s.poly(pts, (255, 215, 0, 255))
    s.rect(30 * k, oy - 10 * k, 270 * k, oy + 25 * k, 6 * k, (240, 190, 0, 255))
    for (x, y) in pts[1:6:2]:
        s.ell(x, y, 13 * k, 13 * k, (255, 60, 60, 255))
    spr = s.img()
    yy = cy - (1 - back_out(p)) * 200
    paste_c(img, spr, cx, yy, alpha=ease_out(p * 2))


def winner(img, t, t_k, name, cy=VIS_Y + 150):
    if t < t_k:
        return
    p = prog(t, t_k, 0.5)
    fs = min(80, 80 * 820 / max(1, text_w(f"SIEGER: {name}", 80)))
    text(img, f"SIEGER: {name}", fs, SPLIT, cy, fill=C_HI, scale=2 - back_out(p), alpha=ease_out(p * 2),
         stroke=10, sfill=(160, 20, 0), rotate=-4)
    confetti(img, t, t_k)


def ruler(img, x, y_bottom, px_per_m, meters, color=(255, 255, 255), a=1.0, side="left", step=1.0):
    if a <= 0.02:
        return
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    al = int(200 * a)
    top = y_bottom - meters * px_per_m
    d.line((x, y_bottom, x, top), fill=color + (al,), width=4)
    m = 0.0
    while m <= meters + 1e-6:
        y = y_bottom - m * px_per_m
        L = 18 if abs(m - round(m)) < 1e-6 else 10
        d.line((x - L if side == "left" else x, y, x if side == "left" else x + L, y), fill=color + (al,), width=3)
        m += step
    img.paste(layer, (0, 0), layer)
    m = 0
    while m <= meters + 1e-6:
        y = y_bottom - m * px_per_m
        if m > 0:
            text(img, f"{int(m)} m", 24, x - 24 if side == "left" else x + 24, y, fill=(230, 230, 240), alpha=a,
                 path=FONT_XB, anchor="rm" if side == "left" else "lm")
        m += 1


def subtitles(img, sc, t):
    toks = sc["toks"]
    chunks, cur = [], []
    for tk in toks:
        trial = cur + [tk]
        wdt = text_w(" ".join(x["text"] for x in trial), 74)
        if cur and (len(trial) > 3 or wdt > 800):
            chunks.append(cur)
            cur = [tk]
        else:
            cur = trial
        if tk["text"][-1] in ".!?:":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    active = None
    for i, ch in enumerate(chunks):
        st = ch[0]["s"] - 0.05
        en = chunks[i + 1][0]["s"] - 0.05 if i + 1 < len(chunks) else ch[-1]["e"] + 0.6
        if st <= t < en:
            active = ch
            break
    if not active:
        return
    p = ease_out(prog(t, active[0]["s"] - 0.05, 0.12))
    size = 74
    words = [x["text"] for x in active]
    curs = [tk["s"] - 0.03 <= t < tk["e"] + 0.05 for tk in active]
    scales = [(1.1 if c else 1.0) for c in curs]
    widths = [text_w(w, size * k) + 16 for w, k in zip(words, scales)]
    space = 20
    total = sum(widths) + space * (len(words) - 1)
    x = SPLIT - total / 2
    for tk, wtxt, wd, cur, k in zip(active, words, widths, curs, scales):
        on = tk["s"] - 0.03 <= t
        col = C_HI if cur else (WHITE if on else (215, 215, 225))
        text(img, wtxt, size, x + wd / 2, SUB_Y, fill=col, scale=k * (0.85 + 0.15 * p), alpha=p, stroke=8,
             sfill=(0, 0, 0))
        x += wd + space


def outro(img, sc, t, gt, mascot_l, mascot_r, line1="Dein Tipp?", line2="Ab in die Kommentare!"):
    header(img, gt, "", t)
    t_s = wt(sc, "Schreib's")
    p = back_out(prog(t, 0.0, 0.5))
    cx, cy = SPLIT, 640
    bw, bh = 380 * p, 170 * p
    if p > 0.05:
        layer = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(layer)
        d.rounded_rectangle((cx - bw, cy - bh, cx + bw, cy + bh), 50, fill=(255, 255, 255, 245))
        d.polygon([(cx - 60 * p, cy + bh - 2), (cx - 130 * p, cy + bh + 80 * p), (cx + 10 * p, cy + bh - 2)],
                  fill=(255, 255, 255, 245))
        img.paste(layer, (0, 0), layer)
        text(img, line1, 56, cx, cy - 60, fill=(40, 40, 70), scale=p)
        blink = "|" if int(gt * 3) % 2 == 0 else " "
        text(img, "_ _ _ _ _ _ " + blink, 60, cx, cy + 50, fill=(255, 120, 0), scale=p)
    bob = 12 * math.sin(gt * 4)
    mascot_l(img, CXL - 50, 1010 + bob, ease_out(prog(t, 0.2, 0.4)), gt)
    mascot_r(img, CXR + 30, 1010 - bob, ease_out(prog(t, 0.3, 0.4)), gt)
    if t > t_s:
        q = prog(t, t_s, 0.4)
        s = SS(240, 200)
        ss = 90
        ix, iy = 120, 90
        s.rect(ix - ss, iy - ss * 0.7, ix + ss, iy + ss * 0.7, ss * 0.45, (255, 226, 60, 255))
        s.poly([(ix - ss * 0.3, iy + ss * 0.65), (ix - ss * 0.6, iy + ss * 1.05), (ix + ss * 0.1, iy + ss * 0.65)],
               (255, 226, 60, 255))
        for k in (-1, 0, 1):
            s.ell(ix + k * ss * 0.45, iy, ss * 0.12, ss * 0.12, (40, 30, 60, 255))
        spr = s.img()
        sz = back_out(q)
        if sz > 0.05:
            spr = spr.resize((max(1, int(240 * sz)), max(1, int(200 * sz))), Image.BILINEAR)
            paste_c(img, spr, SPLIT, 990)
        a = ease_out(q)
        ax = 830 + 20 * math.sin(gt * 8)
        dd = ImageDraw.Draw(img)
        if a > 0.1:
            dd.line((ax - 110, 1190, ax, 1190), fill=C_HI, width=14)
            dd.polygon([(ax + 40, 1190), (ax - 5, 1155), (ax - 5, 1225)], fill=C_HI)
        text(img, line2, 40, ax - 140, 1190, alpha=a, stroke=5, path=FONT_XB, anchor="rm")


def brand(img, t, gt, y=300, a=1.0):
    """Kanal-Logo „RATE MAL?“ als gelbe Pille (für Hook und Outro)."""
    p = back_out(prog(t, 0.0, 0.45)) * a
    if p <= 0.03:
        return
    w, h = 210 * p, 52 * p
    rrect(img, (SPLIT - w, y - h, SPLIT + w, y + h), int(h), (255, 226, 60, int(255 * min(1, a))),
          outline=(30, 20, 60, 255), width=5)
    text(img, "RATE MAL", 58 * p, SPLIT - 28 * p, y + 2, fill=(30, 20, 60))
    q = 1 + 0.15 * math.sin(gt * 7)
    text(img, "?", 70 * p * q, SPLIT + 165 * p, y + 2, fill=(255, 70, 70), stroke=4, sfill=(30, 20, 60),
         rotate=10 * math.sin(gt * 5))


# ------------------------------------------------------------------ render
def scene_at(gt):
    for i, sc in enumerate(SCENES):
        if gt < sc["start"] + sc["dur"] or i == len(SCENES) - 1:
            return i


def render_scene(i, gt):
    sc = SCENES[i]
    t = gt - sc["start"]
    img = BG.copy()
    draw_bg(img, gt)
    CFG["draw"][sc["key"]](img, sc, t, gt)
    subtitles(img, sc, t)
    return img


def render_frame(fi):
    gt = fi / FPS
    i = scene_at(gt)
    img = render_scene(i, gt)
    t = gt - SCENES[i]["start"]
    if i > 0 and t < XF:
        prev = SCENES[i - 1]
        pimg = render_scene(i - 1, prev["start"] + prev["dur"] - 1 / FPS)
        img = Image.blend(pimg, img, ease_io(t / XF))
    return img


def render_bytes(fi):
    return render_frame(fi).tobytes()


# ------------------------------------------------------------------ audio
def synth_sfx():
    n = int((TOTAL + 0.5) * SR)
    out = np.zeros(n)
    r = np.random.default_rng(1)

    def add(sig, t0, gain):
        a = int(max(0, t0) * SR)
        b = min(n, a + len(sig))
        if a < n:
            out[a:b] += sig[:b - a] * gain

    def whoosh(d=0.45):
        m = int(d * SR)
        y = np.convolve(r.standard_normal(m), np.ones(24) / 24, mode="same") * np.sin(np.linspace(0, np.pi, m)) ** 2
        return y / (np.abs(y).max() + 1e-9)

    def thump(d=0.35):
        m = int(d * SR)
        tt = np.arange(m) / SR
        f = 120 * np.exp(-tt * 9) + 45
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 10)
        y[:200] += r.standard_normal(200) * np.linspace(0.6, 0, 200)
        return y

    def chime(d=1.2):
        m = int(d * SR)
        tt = np.arange(m) / SR
        return sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * k) for f, k in ((1046.5, 3), (1318.5, 3.5), (1568, 4))) / 3

    def tick():
        m = int(0.03 * SR)
        tt = np.arange(m) / SR
        return np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 200)

    for i, sc in enumerate(SCENES):
        if i > 0:
            add(whoosh(), sc["start"] - 0.15, 0.10)
    for st, _ in SCORE:
        add(thump(), st, 0.15)
    add(chime(), SCORE[-1][0] + 0.05, 0.10)
    for si, word, occ, d in CFG.get("ticks", []):
        t0 = SCENES[si]["start"] + wt(SCENES[si], word, occ)
        k = 0.0
        while k < d:
            add(tick(), t0 + k, 0.05)
            k += 0.06 + 0.10 * (k / d) ** 2
    for gtf, kind in CFG.get("extra_sfx", lambda: [])():
        if kind == "beat":
            m = int(0.25 * SR)
            tt = np.arange(m) / SR
            y = np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 18)
            add(y, gtf, 0.35)
    tt = np.arange(n) / SR
    pad = np.zeros(n)
    for f in (110, 164.81, 220, 277.18):
        pad += np.sin(2 * np.pi * f * tt + f) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * tt + f))
    pad *= 0.012 * np.clip(tt / 1.0, 0, 1) * np.clip((TOTAL - tt) / 1.0, 0, 1)
    return out + pad


def build_audio():
    n = int((TOTAL + 0.5) * SR)
    voice = np.zeros(n)
    for sc in SCENES:
        with wave.open(sc["wav"]) as wf:
            data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16) / 32768.0
        a = int(sc["start"] * SR)
        voice[a:a + len(data)] += data[:n - a]
    voice = voice / np.abs(voice).max() * 0.89
    mix = np.clip(voice + synth_sfx(), -0.98, 0.98)
    path = os.path.join(CFG["build"], "mix.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((mix[:int(TOTAL * SR)] * 32767).astype(np.int16).tobytes())
    return path


# ------------------------------------------------------------------ setup / main
def setup(**kw):
    global BG, STARS
    CFG.clear()
    CFG.update(kw)
    here = CFG["here"]
    CFG.setdefault("raw", os.path.join(here, "audio_raw"))
    CFG.setdefault("build", os.path.join(here, "build"))
    os.makedirs(CFG["build"], exist_ok=True)
    build_timeline()
    BG = make_bg()
    r = random.Random(11)
    STARS[:] = [(r.uniform(0, W), r.uniform(0, H), r.uniform(0.8, 2.4), r.uniform(0, 6.3), r.uniform(0.5, 2.0))
                for _ in range(120)]


def main():
    here = CFG["here"]
    if "--stills" in sys.argv:
        qc = os.path.join(here, "qc")
        os.makedirs(qc, exist_ok=True)
        for f in os.listdir(qc):
            os.remove(os.path.join(qc, f))
        args = sys.argv[sys.argv.index("--stills") + 1:]
        times = [float(x) for x in args] if args else []
        if not times:
            for sc in SCENES:
                for f in (0.3, 0.55, 0.8, 0.97):
                    times.append(sc["start"] + sc["dur"] * f)
        for gt in times:
            render_frame(int(gt * FPS)).save(os.path.join(qc, f"f_{gt:06.2f}.png"))
        print("stills", len(times), "total", round(TOTAL, 2), "tempo", round(CFG["tempo_used"], 3))
        return
    print(f"total {TOTAL:.2f}s, {NFRAMES} frames, tempo {CFG['tempo_used']:.3f}")
    for i, sc in enumerate(SCENES):
        print(f"  scene {i} {sc['key']:12s} start {sc['start']:6.2f} dur {sc['dur']:5.2f}")
    audio = build_audio()
    out = os.path.join(here, CFG["out"])
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                           "-profile:v", "high", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ac", "2",
                           "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                           "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for b in pool.imap(render_bytes, range(NFRAMES), chunksize=4):
            ff.stdin.write(b)
    ff.stdin.close()
    ff.wait()
    print("wrote", out)

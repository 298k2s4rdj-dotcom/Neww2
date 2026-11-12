"""Premium drawing helpers: supersampled masks, gradients, soft shading, shadows, glow, glass panels.

All sprites are RGBA PIL images. Coordinates passed to shape callbacks are in sprite-local pixels.
"""
import math
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

SSM = 3          # mask supersampling


def mask(w, h, fn, ss=SSM):
    """fn(draw, k) draws white shapes with coordinates multiplied by k."""
    w, h = max(1, int(w)), max(1, int(h))
    m = Image.new("L", (w * ss, h * ss), 0)
    fn(ImageDraw.Draw(m), ss)
    return m.resize((w, h), Image.LANCZOS)


def P(pts, k):
    return [(x * k, y * k) for x, y in pts]


def E(box, k):
    return [v * k for v in box]


def lin(w, h, stops, angle=90.0):
    """linear gradient; angle 90 = top->bottom. stops: [(pos, (r,g,b[,a]))]"""
    w, h = max(1, int(w)), max(1, int(h))
    a = math.radians(angle)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = math.cos(a), math.sin(a)
    proj = (xx - w / 2) * dx + (yy - h / 2) * dy
    span = abs(w / 2 * dx) + abs(h / 2 * dy) + 1e-6
    t = np.clip((proj + span) / (2 * span), 0, 1)
    return _apply_stops(t, stops)


def rad(w, h, cx, cy, r, stops):
    w, h = max(1, int(w)), max(1, int(h))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.clip(np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(1e-6, r), 0, 1)
    return _apply_stops(t, stops)


def _apply_stops(t, stops):
    stops = [(p, tuple(c) + ((255,) if len(c) == 3 else ())) for p, c in stops]
    out = np.zeros(t.shape + (4,), np.float32)
    ps = np.array([p for p, _ in stops], np.float32)
    cs = np.array([c for _, c in stops], np.float32)
    for ch in range(4):
        out[..., ch] = np.interp(t, ps, cs[:, ch])
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def apply_mask(img, m):
    a = np.array(img.getchannel("A"), np.float32) * (np.array(m, np.float32) / 255.0)
    img = img.copy()
    img.putalpha(Image.fromarray(a.astype(np.uint8)))
    return img


def shaded(m, fill, light=(-0.6, -0.8), depth=0.12, dark=(0, 0, 0), dark_a=0.45, hi=(255, 255, 255), hi_a=0.35,
           outline=None, ow=0):
    """fill (RGBA, same size) masked by m with soft inner shadow + highlight for a 3D look."""
    w, h = m.size
    base = apply_mask(fill, m)
    r = max(2, int(min(w, h) * depth))
    blur = m.filter(ImageFilter.GaussianBlur(r))
    lx, ly = light
    sh = ImageChops.offset(blur, int(-lx * r), int(-ly * r))
    inner_dark = ImageChops.subtract(m, sh)          # far side from light
    hl = ImageChops.offset(blur, int(lx * r * 0.8), int(ly * r * 0.8))
    inner_hi = ImageChops.subtract(m, hl)
    out = base
    dk = Image.new("RGBA", (w, h), tuple(dark) + (0,))
    dk.putalpha(inner_dark.point(lambda v: int(v * dark_a)))
    out = Image.alpha_composite(out, dk)
    hk = Image.new("RGBA", (w, h), tuple(hi) + (0,))
    hk.putalpha(ImageChops.multiply(inner_hi, m).point(lambda v: int(v * hi_a)))
    out = Image.alpha_composite(out, hk)
    if outline and ow > 0:
        dil = m.filter(ImageFilter.MaxFilter(ow * 2 + 1))
        ring = ImageChops.subtract(dil, m)
        ol = Image.new("RGBA", (w, h), tuple(outline) + (0,))
        ol.putalpha(ring)
        out = Image.alpha_composite(ol, out)
    return out


def shape(w, h, draw_fn, stops, angle=90, **kw):
    m = mask(w, h, draw_fn)
    return shaded(m, lin(w, h, stops, angle), **kw)


def pad(img, p):
    out = Image.new("RGBA", (img.width + 2 * p, img.height + 2 * p))
    out.paste(img, (p, p))
    return out


def drop_shadow(img, dx=0, dy=18, blur=22, alpha=0.45, color=(10, 5, 25)):
    p = blur * 2 + max(abs(dx), abs(dy))
    out = pad(img, p)
    a = out.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha))
    sh = Image.new("RGBA", out.size, tuple(color) + (0,))
    sh.putalpha(a)
    sh = ImageChops.offset(sh, dx, dy)
    return Image.alpha_composite(sh, out)


def glow(img, color, radius=24, strength=1.0):
    p = radius * 2
    out = pad(img, p)
    a = out.getchannel("A").filter(ImageFilter.GaussianBlur(radius)).point(lambda v: min(255, int(v * strength)))
    g = Image.new("RGBA", out.size, tuple(color) + (0,))
    g.putalpha(a)
    return Image.alpha_composite(g, out)


def place(canvas, sprite, cx, cy, scale=1.0, rot=0.0, alpha=1.0, anchor="c"):
    """composite sprite centred (or bottom-anchored) at (cx, cy) in canvas pixels."""
    if sprite is None or alpha <= 0.01 or scale <= 0.01:
        return
    sp = sprite
    if abs(scale - 1) > 1e-3:
        sp = sp.resize((max(1, int(sp.width * scale)), max(1, int(sp.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.05:
        sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        sp = sp.copy()
        sp.putalpha(sp.getchannel("A").point(lambda v: int(v * alpha)))
    x = int(cx - sp.width / 2)
    y = int(cy - sp.height / 2) if anchor == "c" else int(cy - sp.height)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(canvas.width, x + sp.width), min(canvas.height, y + sp.height)
    if x1 <= x0 or y1 <= y0:
        return
    crop = sp.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    canvas.alpha_composite(crop, (x0, y0))


def glass(w, h, r, tint=(255, 255, 255), a0=46, a1=18, border=110):
    w, h = int(w), int(h)
    m = mask(w, h, lambda d, k: d.rounded_rectangle(E((0, 0, w - 1, h - 1), k), int(r * k), fill=255))
    fill = lin(w, h, [(0, tint + (a0,)), (1, tint + (a1,))], 90)
    out = apply_mask(fill, m)
    ring = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(5)))
    ol = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    ol.putalpha(ring.point(lambda v: int(v * border / 255)))
    out = Image.alpha_composite(out, ol)
    hl = mask(w, h, lambda d, k: d.rounded_rectangle(E((r * 0.8, 5, w - r * 0.8, 9 + h * 0.025), k), int(8 * k),
                                                     fill=255))
    hk = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    hk.putalpha(hl.point(lambda v: int(v * 0.08)))
    return Image.alpha_composite(out, hk)


def dark_panel(w, h, r, a=170):
    w, h = int(w), int(h)
    m = mask(w, h, lambda d, k: d.rounded_rectangle(E((0, 0, w - 1, h - 1), k), int(r * k), fill=255))
    fill = lin(w, h, [(0, (20, 14, 46, a)), (1, (8, 6, 24, a + 20))], 90)
    out = apply_mask(fill, m)
    ring = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(5)))
    ol = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    ol.putalpha(ring.point(lambda v: int(v * 0.28)))
    return Image.alpha_composite(out, ol)


def background(W, H, top, bottom, accent, seed=3):
    y = np.linspace(0, 1, H)[:, None, None]
    bg = np.array(top, np.float32) * (1 - y) + np.array(bottom, np.float32) * y
    bg = np.repeat(bg, W, axis=1)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - W * 0.5) / (W * 0.55)) ** 2 + ((yy - H * 0.42) / (H * 0.3)) ** 2))[..., None]
    bg = bg + g * np.array(accent, np.float32)
    vig = (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)[..., None]
    bg = bg * np.clip(1.08 - 0.45 * vig, 0.45, 1.08)
    rng = np.random.default_rng(seed)
    bg = bg + rng.normal(0, 2.2, bg.shape)
    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")
    # bokeh
    bok = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(bok)
    r = random.Random(seed)
    for _ in range(26):
        x, yv, s = r.uniform(0, W), r.uniform(0, H), r.uniform(W * 0.015, W * 0.06)
        c = r.choice([(255, 255, 255), (255, 220, 150), (150, 200, 255), (255, 160, 220)])
        d.ellipse((x - s, yv - s, x + s, yv + s), fill=c + (int(r.uniform(14, 38)),))
    bok = bok.filter(ImageFilter.GaussianBlur(W * 0.006))
    img.alpha_composite(bok)
    d = ImageDraw.Draw(img)
    for _ in range(320):
        x, yv, s = r.uniform(0, W), r.uniform(0, H), r.uniform(0.8, 2.6) * W / 1080
        v = int(r.uniform(150, 255))
        d.ellipse((x - s, yv - s, x + s, yv + s), fill=(v, v, 255, int(r.uniform(90, 200))))
    return img


def line_glow(canvas, pts, color, width, glow_w=None, alpha=1.0):
    lay = Image.new("RGBA", canvas.size)
    d = ImageDraw.Draw(lay)
    gw = glow_w or width * 4
    for k, (ww, aa) in enumerate(((gw, 50), (gw * 0.55, 90), (width, 255))):
        d.line(pts, fill=tuple(color) + (int(aa * alpha),), width=max(1, int(ww)), joint="curve")
    canvas.alpha_composite(lay)

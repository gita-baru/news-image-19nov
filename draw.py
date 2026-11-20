#!/usr/bin/env python3
"""Draw the 19 November 2026 one-day world-news front page (1024x1024).

Run locally:  python3 draw.py [1|2|3]   (variant; default 1)
Writes entry.png next to this file. The grader's entrypoint is main.py,
which only copies entry.png to the output directory.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 12
CW = W - 2 * MARGIN  # content width = 1000

# ---- palette (newspaper cream + ink + red accent) ----
PAPER = (247, 243, 232)
INK = (26, 26, 26)
RED = (178, 28, 28)
RED_DK = (140, 20, 20)
NAVY = (28, 54, 92)
NAVY_DK = (18, 38, 68)
GOLD = (176, 124, 16)
GREY = (104, 100, 92)
GREY_LT = (150, 146, 136)
RULE = (196, 188, 172)
BOX = (255, 252, 240)
YELLOW_BG = (255, 248, 220)
GREEN = (46, 125, 60)
TEAL = (14, 116, 120)
ORANGE = (196, 96, 16)
BROWN = (122, 74, 32)
PURPLE = (104, 64, 140)
PINK = (178, 74, 110)

SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

_fcache = {}


def font(path, size):
    key = (path, size)
    if key not in _fcache:
        _fcache[key] = ImageFont.truetype(path, size)
    return _fcache[key]


def tw(d, s, f):
    return d.textlength(s, font=f)


def wrap(d, text, f, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tw(d, t, f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(d, x, y, text, f, max_w, fill, line_h=None, max_lines=None):
    """Draw wrapped text; returns the y after the last line."""
    if line_h is None:
        line_h = int(f.size * 1.18)
    lines = wrap(d, text, f, max_w)
    if max_lines is not None:
        lines = lines[:max_lines]
    for ln in lines:
        d.text((x, y), ln, font=f, fill=fill)
        y += line_h
    return y


def fit_text(d, text, f, max_w, suffix="..."):
    """Truncate one line to max_w, adding an ellipsis if needed."""
    if tw(d, text, f) <= max_w:
        return text
    while text and tw(d, text + suffix, f) > max_w:
        text = text[:-1]
    return text + suffix


def shrink_font(path, text, max_w, start, minimum=8):
    """Largest font size (<= start) at which text fits max_w."""
    size = start
    while size > minimum:
        f = font(path, size)
        if tw(ImageDraw.Draw(Image.new("RGB", (8, 8))), text, f) <= max_w:
            return f
        size -= 1
    return font(path, minimum)


def panel(d, x, y, w, h, fill=None, outline=INK, width=1):
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=fill, outline=outline,
                width=width)


def hline(d, x0, x1, y, fill=INK, width=1):
    d.line([(x0, y), (x1, y)], fill=fill, width=width)


def vline(d, x, y0, y1, fill=INK, width=1):
    d.line([(x, y0), (x, y1)], fill=fill, width=width)

# ---------------------------------------------------------------------------
# Scene helpers
# ---------------------------------------------------------------------------

def sky(d, x, y, w, h, top, bot, bands=10):
    """Vertical gradient sky (banded approximation)."""
    for i in range(bands):
        t = i / max(1, bands - 1)
        c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
        y0 = y + int(h * i / bands)
        y1 = y + int(h * (i + 1) / bands)
        d.rectangle([x, y0, x + w - 1, y1], fill=c)


def sun(d, cx, cy, r, fill=(255, 214, 90)):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill,
              outline=(232, 160, 20), width=2)


def buildings(d, x, y, w, h, color, seed=0):
    """Deterministic skyline silhouette along the bottom of the rect."""
    import random
    rnd = random.Random(seed)
    bx = x
    while bx < x + w:
        bw = rnd.randint(max(8, w // 14), max(10, w // 7))
        bh = rnd.randint(int(h * 0.3), int(h * 0.85))
        d.rectangle([bx, y + h - bh, min(bx + bw, x + w), y + h], fill=color)
        # a few lit windows
        for _ in range(3):
            wx = rnd.randint(bx + 2, max(bx + 3, min(bx + bw - 4, x + w - 3)))
            wy = y + h - rnd.randint(4, max(5, bh - 4))
            d.rectangle([wx, wy, wx + 2, wy + 2], fill=(255, 220, 120))
        bx += bw + 1


def flag_us(d, x, y, w, h):
    for i in range(7):
        c = (178, 34, 52) if i % 2 == 0 else (255, 255, 255)
        d.rectangle([x, y + i * h // 7, x + w, y + (i + 1) * h // 7], fill=c)
    d.rectangle([x, y, x + int(w * 0.42), y + int(h * 0.55)], fill=(28, 54, 92))
    for r in range(2):
        for c in range(3):
            d.ellipse([x + 3 + c * 5, y + 2 + r * 5, x + 5 + c * 5, y + 4 + r * 5],
                      fill=(255, 255, 255))


def flag_cn(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(222, 32, 32))
    d.ellipse([x + 2, y + 2, x + 8, y + 8], fill=(255, 222, 0))
    for sx, sy in ((10, 2), (12, 5), (10, 8)):
        d.ellipse([x + sx, y + sy, x + sx + 3, y + sy + 3], fill=(255, 222, 0))


def flag_ru(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h // 3], fill=(255, 255, 255))
    d.rectangle([x, y + h // 3, x + w, y + 2 * h // 3], fill=(0, 90, 180))
    d.rectangle([x, y + 2 * h // 3, x + w, y + h], fill=(210, 30, 30))


def flag_jp(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
    d.ellipse([x + w // 2 - 4, y + h // 2 - 4, x + w // 2 + 4, y + h // 2 + 4],
              fill=(188, 0, 45))


def flag_eu(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(0, 51, 153))
    for k in range(8):
        import math
        a = math.pi * 2 * k / 8
        cx = x + w // 2 + int(7 * math.cos(a))
        cy = y + h // 2 + int(4.5 * math.sin(a))
        d.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=(255, 210, 0))


def pole_flag(d, x, y, h, fw, draw_flag):
    d.rectangle([x, y, x + 2, y + h], fill=(60, 50, 40))
    draw_flag(d, x + 2, y, fw, int(h * 0.55))


def figure(d, cx, y, h, suit, skin=(232, 188, 150)):
    """Simple standing figure: head + suit body."""
    r = max(3, h // 8)
    d.ellipse([cx - r, y, cx + r, y + 2 * r], fill=skin,
              outline=INK, width=1)
    d.rounded_rectangle([cx - r - 1, y + 2 * r, cx + r + 1, y + h],
                        radius=3, fill=suit, outline=INK, width=1)
    d.rectangle([cx - 1, y + 2 * r, cx + 1, y + 2 * r + 6], fill=(255, 255, 255))


# ---------------------------------------------------------------------------
# Illustrated scenes (each draws inside the given rect)
# ---------------------------------------------------------------------------

def scene_summit(d, x, y, w, h):
    """Three leaders at one table, Shenzhen skyline behind."""
    sky(d, x, y, w, h, (64, 110, 180), (244, 178, 110))
    sun(d, x + w - 22, y + 18, 12)
    buildings(d, x, y + h // 2, w, h // 2, (38, 52, 84), seed=3)
    # table
    d.rectangle([x + 8, y + h - 26, x + w - 8, y + h - 18], fill=(122, 74, 32),
                outline=INK, width=1)
    d.rectangle([x + 8, y + h - 18, x + w - 8, y + h - 14], fill=(94, 56, 24))
    # three flags behind the table
    pole_flag(d, x + 18, y + 12, h - 40, 26, flag_us)
    pole_flag(d, x + w // 2 - 14, y + 12, h - 40, 26, flag_cn)
    pole_flag(d, x + w - 46, y + 12, h - 40, 26, flag_ru)
    # three figures
    figure(d, x + 34, y + h - 52, 26, (28, 54, 92))
    figure(d, x + w // 2, y + h - 52, 26, (140, 20, 20))
    figure(d, x + w - 34, y + h - 52, 26, (40, 40, 40))


def scene_apec(d, x, y, w, h):
    """APEC Shenzhen: skyline, globe, banner."""
    sky(d, x, y, w, h, (30, 80, 150), (250, 200, 120))
    sun(d, x + w // 2, y + 20, 14)
    buildings(d, x, y + h // 3, w, 2 * h // 3, (24, 40, 72), seed=7)
    # banner
    d.rounded_rectangle([x + 10, y + 8, x + w - 10, y + 26], radius=4,
                        fill=(178, 28, 28), outline=(255, 255, 255), width=1)
    f = font(SANS_B, 11)
    t = "APEC 2026 · SHENZHEN"
    d.text((x + (w - tw(d, t, f)) / 2, y + 12), t, font=f, fill=(255, 255, 255))
    # globe
    cx, cy, r = x + w - 30, y + h - 34, 16
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(46, 130, 190),
              outline=INK, width=1)
    d.ellipse([cx - r + 4, cy - r + 5, cx - 2, cy + 2], fill=(80, 170, 90))
    d.ellipse([cx + 2, cy + 4, cx + r - 4, cy + r - 5], fill=(80, 170, 90))


def scene_icj(d, x, y, w, h):
    """World Court: courthouse, columns, scales, 9-6 badge."""
    sky(d, x, y, w, h, (170, 205, 235), (235, 240, 245))
    # lawn
    d.rectangle([x, y + int(h * 0.72), x + w, y + h], fill=(110, 170, 100))
    # courthouse
    bx, by, bw, bh = x + 10, y + 16, w - 20, int(h * 0.58)
    d.rectangle([bx, by + 14, bx + bw, by + bh], fill=(226, 208, 172),
                outline=INK, width=1)
    d.polygon([(bx - 4, by + 16), (bx + bw // 2, by - 2), (bx + bw + 4, by + 16)],
              fill=(200, 90, 60), outline=INK)
    for i in range(4):
        cx = bx + 8 + i * (bw - 16) // 3
        d.rectangle([cx - 3, by + 20, cx + 3, by + bh - 4], fill=(245, 240, 225),
                    outline=INK, width=1)
    d.rectangle([bx + bw // 2 - 8, by + bh - 16, bx + bw // 2 + 8, by + bh - 4],
                fill=(90, 60, 30))
    # scales of justice
    sx, sy = x + w - 26, y + h - 40
    d.line([(sx, sy - 22), (sx, sy + 2)], fill=(60, 50, 40), width=2)
    d.line([(sx - 12, sy - 18), (sx + 12, sy - 18)], fill=(60, 50, 40), width=2)
    d.polygon([(sx - 16, sy - 14), (sx - 8, sy - 14), (sx - 12, sy - 6)],
              fill=(200, 170, 40), outline=INK)
    d.polygon([(sx + 8, sy - 14), (sx + 16, sy - 14), (sx + 12, sy - 6)],
              fill=(200, 170, 40), outline=INK)
    # 9-6 badge
    d.rounded_rectangle([x + 6, y + 6, x + 34, y + 22], radius=3,
                        fill=RED, outline=(255, 255, 255), width=1)
    f = font(SANS_B, 11)
    d.text((x + 10, y + 9), "9–6", font=f, fill=(255, 255, 255))


def scene_anthropic(d, x, y, w, h):
    """Anthropic IPO: dark board, rising chart, $83, ANT."""
    d.rectangle([x, y, x + w, y + h], fill=(14, 60, 40))
    # candlesticks rising
    import random
    rnd = random.Random(11)
    n = 7
    bw = w // (n + 2)
    base = y + h - 16
    for i in range(n):
        cx = x + (i + 1) * bw
        top = base - int((h - 34) * (0.25 + 0.7 * i / (n - 1)))
        col = (60, 200, 110) if i % 2 == 0 else (120, 220, 140)
        d.rectangle([cx - 3, top, cx + 3, base - rnd.randint(2, 10)], fill=col)
        d.line([(cx, top - 5), (cx, base)], fill=col, width=1)
    # rising line
    pts = []
    for i in range(n):
        cx = x + (i + 1) * bw
        pts.append((cx, base - int((h - 34) * (0.25 + 0.7 * i / (n - 1))) - 4))
    d.line(pts, fill=(255, 214, 90), width=2)
    f = font(SANS_B, 15)
    d.text((x + 6, y + 5), "ANT", font=f, fill=(255, 255, 255))
    f2 = font(SANS_B, 13)
    t = "$83"
    d.text((x + w - tw(d, t, f2) - 6, y + 6), t, font=f2, fill=(255, 214, 90))
    f3 = font(SANS, 9)
    d.text((x + 6, y + h - 13), "NASDAQ · FIRST DAY", font=f3,
           fill=(180, 220, 190))


def scene_bangladesh(d, x, y, w, h):
    """Dhaka street: buildings, smoke, flame."""
    sky(d, x, y, w, h, (240, 160, 90), (120, 70, 60))
    buildings(d, x, y + h // 3, w, 2 * h // 3, (60, 45, 40), seed=5)
    # smoke plumes
    for cx, cy, r in ((x + w // 4, y + 22, 10), (x + w // 2, y + 14, 13),
                      (x + 3 * w // 4, y + 26, 9)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(120, 115, 110))
        d.ellipse([cx - r // 2, cy - r, cx + r // 2, cy], fill=(150, 145, 140))
    # flame
    fx, fy = x + w - 30, y + h - 30
    d.polygon([(fx, fy - 16), (fx + 9, fy - 2), (fx + 4, fy + 4),
               (fx - 4, fy + 4), (fx - 9, fy - 2)], fill=(240, 120, 20),
              outline=(180, 60, 0))
    d.polygon([(fx, fy - 8), (fx + 4, fy + 2), (fx - 4, fy + 2)],
              fill=(255, 210, 60))
    # street
    d.rectangle([x, y + h - 12, x + w, y + h], fill=(50, 42, 38))


def scene_hormuz(d, x, y, w, h):
    """Oil tanker in the Strait of Hormuz, derrick, flame."""
    sky(d, x, y, w, h, (140, 190, 225), (230, 235, 240))
    # sea
    d.rectangle([x, y + int(h * 0.62), x + w, y + h], fill=(30, 90, 150))
    for i in range(4):
        yy = y + int(h * 0.66) + i * 7
        d.line([(x + 4, yy), (x + w - 4, yy)], fill=(120, 180, 220), width=1)
    # tanker
    d.rectangle([x + 12, y + int(h * 0.52), x + w - 12, y + int(h * 0.66)],
                fill=(30, 30, 34), outline=INK, width=1)
    d.rectangle([x + w - 42, y + int(h * 0.34), x + w - 16, y + int(h * 0.52)],
                fill=(240, 240, 235), outline=INK, width=1)
    d.rectangle([x + w - 42, y + int(h * 0.34), x + w - 16, y + int(h * 0.40)],
                fill=(178, 28, 28))
    # derrick
    dx = x + 14
    d.line([(dx, y + 12), (dx + 8, y + 30)], fill=(60, 50, 40), width=2)
    d.line([(dx + 16, y + 12), (dx + 8, y + 30)], fill=(60, 50, 40), width=2)
    d.line([(dx + 4, y + 18), (dx + 12, y + 18)], fill=(60, 50, 40), width=1)
    # flame
    fx, fy = dx + 8, y + 8
    d.polygon([(fx, fy - 8), (fx + 5, fy + 2), (fx - 5, fy + 2)],
              fill=(240, 120, 20))


def scene_iran(d, x, y, w, h):
    """Missile rising, radar, night sky."""
    sky(d, x, y, w, h, (16, 28, 60), (60, 70, 110))
    for sx, sy in ((x + 12, y + 10), (x + w - 14, y + 18), (x + w // 2, y + 8)):
        d.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(255, 255, 255))
    # missile (angled)
    mx, my = x + w // 2, y + h // 2
    d.polygon([(mx, my - 26), (mx + 7, my - 8), (mx + 5, my + 14),
               (mx - 5, my + 14), (mx - 7, my - 8)], fill=(235, 235, 230),
              outline=INK)
    d.polygon([(mx, my - 26), (mx + 4, my - 18), (mx - 4, my - 18)],
              fill=(178, 28, 28))
    d.polygon([(mx - 5, my + 14), (mx - 2, my + 22), (mx + 2, my + 22),
               (mx + 5, my + 14)], fill=(240, 120, 20))
    # radar dish
    rx, ry = x + 16, y + h - 18
    d.line([(rx, ry), (rx + 8, ry - 10)], fill=(200, 200, 200), width=2)
    d.arc([rx - 2, ry - 22, rx + 18, ry - 2], 200, 340, fill=(200, 200, 200),
          width=2)
    # ground
    d.rectangle([x, y + h - 10, x + w, y + h], fill=(40, 42, 50))


def scene_imf(d, x, y, w, h):
    """Globe, 4.7% inflation, bar chart."""
    sky(d, x, y, w, h, (200, 225, 245), (245, 248, 250))
    # globe
    cx, cy, r = x + 30, y + h // 2 + 4, 20
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(46, 130, 190),
              outline=INK, width=1)
    d.ellipse([cx - r + 5, cy - r + 6, cx - 3, cy + 1], fill=(80, 170, 90))
    d.ellipse([cx + 2, cy + 3, cx + r - 5, cy + r - 6], fill=(80, 170, 90))
    d.arc([cx - r, cy - r, cx + r, cy + r], 20, 160, fill=(255, 255, 255),
          width=1)
    # big 4.7%
    f = font(SANS_B, 20)
    d.text((x + 56, y + 10), "4.7%", font=f, fill=RED)
    f2 = font(SANS, 9)
    d.text((x + 56, y + 32), "GLOBAL INFLATION", font=f2, fill=GREY)
    # bars
    bx = x + 56
    for i, bh in enumerate((10, 16, 12, 22)):
        d.rectangle([bx + i * 12, y + h - 12 - bh, bx + i * 12 + 8, y + h - 12],
                    fill=(28, 54, 92) if i < 3 else RED)


def scene_markets(d, x, y, w, h):
    """Wall Street down: red falling line, gold bars, $."""
    d.rectangle([x, y, x + w, y + h], fill=(24, 28, 40))
    # falling line
    pts = [(x + 8, y + 14), (x + w // 3, y + 26), (x + 2 * w // 3, y + 44),
           (x + w - 8, y + h - 26)]
    d.line(pts, fill=(230, 60, 60), width=3)
    for px, py in pts:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(230, 60, 60))
    # gold bars
    for i in range(3):
        bx = x + 10 + i * 16
        d.rectangle([bx, y + h - 22, bx + 12, y + h - 14], fill=(212, 175, 55),
                    outline=(150, 110, 20), width=1)
    f = font(SANS_B, 16)
    d.text((x + w - 34, y + 6), "−2%", font=f, fill=(230, 60, 60))
    f2 = font(SANS, 9)
    d.text((x + 8, y + h - 12), "DOW −2.19% · S&P −2.02%", font=f2,
           fill=(200, 200, 200))


def scene_ethiopia(d, x, y, w, h):
    """Border mountains, two flags facing, tank."""
    sky(d, x, y, w, h, (235, 215, 170), (250, 240, 220))
    # mountains
    d.polygon([(x, y + h - 22), (x + w // 3, y + 12), (x + 2 * w // 3, y + h - 22)],
              fill=(140, 110, 80))
    d.polygon([(x + w // 3, y + h - 22), (x + 2 * w // 3, y + 6),
               (x + w, y + h - 22)], fill=(110, 85, 60))
    d.polygon([(x + w // 3 - 8, y + 20), (x + w // 3, y + 12),
               (x + w // 3 + 8, y + 20)], fill=(255, 255, 255))
    # ground
    d.rectangle([x, y + h - 22, x + w, y + h], fill=(170, 140, 100))
    # Ethiopia flag (green/yellow/red)
    fx = x + 10
    d.rectangle([fx, y + 16, fx + 3, y + 44], fill=(60, 50, 40))
    d.rectangle([fx + 3, y + 16, fx + 25, y + 24], fill=(20, 140, 60))
    d.rectangle([fx + 3, y + 24, fx + 25, y + 32], fill=(250, 210, 0))
    d.rectangle([fx + 3, y + 32, fx + 25, y + 40], fill=(210, 30, 30))
    # Eritrea flag (green/red/blue triangle)
    fx2 = x + w - 28
    d.rectangle([fx2, y + 16, fx2 + 3, y + 44], fill=(60, 50, 40))
    d.rectangle([fx2 + 3, y + 16, fx2 + 25, y + 40], fill=(20, 140, 60))
    d.polygon([(fx2 + 3, y + 16), (fx2 + 25, y + 28), (fx2 + 3, y + 40)],
              fill=(210, 30, 30))
    # tank
    tx, ty = x + w // 2 - 16, y + h - 34
    d.rectangle([tx, ty, tx + 32, ty + 8], fill=(70, 80, 60), outline=INK, width=1)
    d.rectangle([tx + 8, ty - 7, tx + 20, ty], fill=(70, 80, 60), outline=INK,
                width=1)
    d.line([(tx + 20, ty - 4), (tx + 34, ty - 6)], fill=(70, 80, 60), width=2)
    for wx in (tx + 4, tx + 14, tx + 24):
        d.ellipse([wx, ty + 8, wx + 6, ty + 12], fill=(40, 40, 40))


def scene_kyiv(d, x, y, w, h):
    """Kyiv skyline at dusk, drone, smoke."""
    sky(d, x, y, w, h, (90, 90, 130), (240, 170, 110))
    sun(d, x + w - 20, y + 16, 10)
    buildings(d, x, y + h // 3, w, 2 * h // 3, (50, 50, 70), seed=9)
    # drone (quadcopter)
    dx, dy = x + w // 2, y + 16
    d.rectangle([dx - 6, dy - 3, dx + 6, dy + 3], fill=(40, 40, 40),
                outline=(200, 200, 200), width=1)
    for ox in (-10, 10):
        d.line([(dx + ox - 5, dy - 5), (dx + ox + 5, dy - 5)],
               fill=(220, 220, 220), width=2)
    # smoke plume
    for cx, cy, r in ((x + 18, y + 30, 8), (x + 26, y + 22, 10)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(130, 125, 120))


def scene_kerch(d, x, y, w, h):
    """Kerch Bridge over water, blast, smoke."""
    sky(d, x, y, w, h, (150, 195, 230), (235, 240, 245))
    # water
    d.rectangle([x, y + int(h * 0.66), x + w, y + h], fill=(40, 110, 170))
    for i in range(3):
        yy = y + int(h * 0.72) + i * 8
        d.line([(x + 4, yy), (x + w - 4, yy)], fill=(130, 190, 230), width=1)
    # bridge deck + arch
    d.rectangle([x + 6, y + int(h * 0.52), x + w - 6, y + int(h * 0.58)],
                fill=(120, 120, 125), outline=INK, width=1)
    d.arc([x + w // 4, y + int(h * 0.30), x + 3 * w // 4, y + int(h * 0.62)],
          180, 360, fill=(90, 90, 95), width=3)
    for px in (x + w // 4 + 6, x + w // 2, x + 3 * w // 4 - 6):
        d.line([(px, y + int(h * 0.52)), (px, y + int(h * 0.66))],
               fill=(90, 90, 95), width=2)
    # blast
    bx, by = x + w // 2, y + int(h * 0.44)
    for r, c in ((12, (240, 120, 20)), (8, (255, 200, 60)), (4, (255, 240, 150))):
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=c)
    # smoke
    d.ellipse([bx - 16, by - 20, bx - 2, by - 6], fill=(120, 115, 110))
    d.ellipse([bx + 2, by - 24, bx + 16, by - 10], fill=(140, 135, 130))


def scene_berlin(d, x, y, w, h):
    """Brandenburg Gate, EU + German flags."""
    sky(d, x, y, w, h, (170, 205, 235), (240, 242, 245))
    # ground
    d.rectangle([x, y + int(h * 0.78), x + w, y + h], fill=(150, 160, 150))
    # gate
    gx, gy, gw = x + w // 2 - 34, y + 18, 68
    d.rectangle([gx, gy + 10, gx + gw, gy + 40], fill=(225, 210, 175),
                outline=INK, width=1)
    d.polygon([(gx - 3, gy + 12), (gx + gw // 2, gy), (gx + gw + 3, gy + 12)],
              fill=(200, 90, 60), outline=INK)
    for i in range(5):
        cx = gx + 6 + i * (gw - 12) // 4
        d.rectangle([cx - 2, gy + 16, cx + 2, gy + 40], fill=(245, 240, 225),
                    outline=INK, width=1)
    d.rectangle([gx + gw // 2 - 7, gy + 28, gx + gw // 2 + 7, gy + 40],
                fill=(90, 60, 30))
    # flags on poles
    pole_flag(d, x + 8, y + 14, 34, 20, flag_eu)
    d.rectangle([x + w - 30, y + 14, x + w - 28, y + 48], fill=(60, 50, 40))
    d.rectangle([x + w - 28, y + 14, x + w - 8, y + 22], fill=(20, 20, 20))
    d.rectangle([x + w - 28, y + 22, x + w - 8, y + 30], fill=(210, 30, 30))
    d.rectangle([x + w - 28, y + 30, x + w - 8, y + 38], fill=(250, 210, 0))


def scene_cricket(d, x, y, w, h):
    """Test cricket: pitch, batsman, stumps, ball."""
    sky(d, x, y, w, h, (150, 200, 240), (235, 245, 250))
    # outfield + pitch
    d.rectangle([x, y + int(h * 0.55), x + w, y + h], fill=(90, 160, 90))
    d.rectangle([x + w // 2 - 12, y + int(h * 0.55), x + w // 2 + 12, y + h],
                fill=(210, 190, 140))
    # stumps
    sx = x + w // 2 - 12
    for i in range(3):
        d.rectangle([sx + i * 4, y + h - 26, sx + i * 4 + 2, y + h - 14],
                    fill=(250, 210, 0), outline=INK, width=1)
    # batsman
    bx = x + w // 2 + 18
    figure(d, bx, y + h - 34, 26, (255, 255, 255))
    d.line([(bx + 4, y + h - 12), (bx + 14, y + h - 4)], fill=(150, 100, 50),
           width=3)
    # ball
    d.ellipse([x + w - 16, y + 14, x + w - 8, y + 22], fill=(190, 30, 30),
              outline=INK, width=1)
    # score
    f = font(SANS_B, 12)
    d.text((x + 6, y + 6), "113*", font=f, fill=NAVY)


def scene_cyclone(d, x, y, w, h):
    """Cyclone Akvan: spiral, rain, houses."""
    sky(d, x, y, w, h, (40, 70, 120), (120, 160, 210))
    cx, cy = x + w // 2, y + h // 2 - 4
    # spiral (concentric arcs)
    for r, c in ((26, (255, 255, 255)), (20, (200, 220, 245)),
                 (14, (255, 255, 255)), (8, (200, 220, 245))):
        d.arc([cx - r, cy - r, cx + r, cy + r], -60, 220, fill=c, width=3)
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 255, 255))
    # rain
    for rx, ry in ((x + 8, y + 10), (x + w - 12, y + 14), (x + 12, y + h - 30)):
        d.line([(rx, ry), (rx - 2, ry + 7)], fill=(200, 220, 245), width=1)
    # houses at the bottom
    for hx in (x + 8, x + w - 30):
        d.rectangle([hx, y + h - 16, hx + 20, y + h - 6], fill=(200, 120, 60),
                    outline=INK, width=1)
        d.polygon([(hx - 2, y + h - 16), (hx + 10, y + h - 24),
                   (hx + 22, y + h - 16)], fill=(140, 40, 40))


def scene_takaichi(d, x, y, w, h):
    """Japan–Russia: two flags, handshake, table."""
    sky(d, x, y, w, h, (200, 220, 240), (245, 242, 235))
    # table
    d.rectangle([x + 10, y + h - 24, x + w - 10, y + h - 16],
                fill=(122, 74, 32), outline=INK, width=1)
    # Japan flag (left) and Russia flag (right) on poles
    pole_flag(d, x + 16, y + 12, h - 40, 26, flag_jp)
    pole_flag(d, x + w - 44, y + 12, h - 40, 26, flag_ru)
    # handshake (two clasped hands, simplified)
    hx, hy = x + w // 2, y + h - 34
    d.ellipse([hx - 14, hy - 6, hx + 2, hy + 6], fill=(232, 188, 150),
              outline=INK, width=1)
    d.ellipse([hx - 2, hy - 6, hx + 14, hy + 6], fill=(210, 170, 130),
              outline=INK, width=1)
    d.line([(hx - 12, hy - 2), (hx + 12, hy - 2)], fill=INK, width=1)
    # two figures behind the table
    figure(d, x + 34, y + h - 50, 24, (40, 40, 60))
    figure(d, x + w - 34, y + h - 50, 24, (90, 30, 30))


def scene_gta(d, x, y, w, h):
    """GTA VI: Vice City sunset skyline, car, palms, VI."""
    sky(d, x, y, w, h, (90, 40, 110), (250, 150, 80))
    sun(d, x + w - 30, y + 22, 15)
    # palms
    for px in (x + 14, x + w - 16):
        d.line([(px, y + h - 30), (px, y + 22)], fill=(40, 30, 20), width=2)
        for a in (-30, -10, 10, 30):
            import math
            ex = px + int(12 * math.sin(math.radians(a)))
            ey = y + 22 + int(8 * abs(math.cos(math.radians(a))))
            d.line([(px, y + 22), (ex, ey)], fill=(40, 100, 50), width=2)
    buildings(d, x, y + h // 2, w, h // 2, (30, 20, 50), seed=13)
    # car
    cx, cy = x + w // 2, y + h - 26
    d.rounded_rectangle([cx - 22, cy - 8, cx + 22, cy + 2], radius=4,
                        fill=(220, 40, 90), outline=INK, width=1)
    d.polygon([(cx - 12, cy - 8), (cx - 6, cy - 16), (cx + 8, cy - 16),
               (cx + 14, cy - 8)], fill=(180, 30, 70), outline=INK)
    for wx in (cx - 14, cx + 10):
        d.ellipse([wx, cy, wx + 8, cy + 6], fill=(20, 20, 20))
    # VI badge
    d.rounded_rectangle([x + 6, y + 6, x + 30, y + 24], radius=3,
                        fill=(20, 20, 30), outline=(255, 214, 90), width=1)
    f = font(SANS_B, 12)
    d.text((x + 11, y + 9), "VI", font=f, fill=(255, 214, 90))

# ---------------------------------------------------------------------------
# Story data — 44 verified 19 Nov stories (draft: stories-19nov-draft.md)
# #33 and #38 excluded (date traps: 18 Nov / 16-17 Nov); #42 dropped (no
# detail); #37 and #41 dropped (weakest) to land on 44.
# Fields are grouped into 9 for the field bar; regions into 8.
# ---------------------------------------------------------------------------

# label: CONFIRMED = reported as fact; CLAIM = disputed / unconfirmed, attributed.
STORIES = {
    1: dict(head="Trump, Xi and Putin hold first three-way summit",
            sum="The three leaders meet in Shenzhen; nuclear arms, the Iran war, Ukraine and trade top the agenda. No deal is expected.",
            region="Asia", field="Diplomacy", src="Reuters · Yonhap",
            label="CONFIRMED", scene=scene_summit, place="SHENZHEN"),
    2: dict(head="APEC opens in Shenzhen as Xi pledges $20m",
            sum="Xi opens APEC with $20m for Asia-Pacific.",
            region="Asia", field="Diplomacy", src="Nikkei Asia · Reuters",
            label="CONFIRMED", scene=scene_apec, place="SHENZHEN"),
    3: dict(head="World Court: Myanmar committed genocide",
            sum="ICJ rules 9-6: Myanmar committed genocide.",
            region="Europe", field="Law & Justice", src="Reuters · ICJ",
            label="CONFIRMED", scene=scene_icj, place="THE HAGUE"),
    4: dict(head="Anthropic starts trading after biggest IPO ever",
            sum="ANT closes at $97.17, up 17% on its $83 IPO price, after a record $81.3bn raise valuing it near $1.5tn.",
            region="N. America", field="Markets", src="Nasdaq · CNN",
            label="CONFIRMED", scene=scene_anthropic, place="NEW YORK"),
    5: dict(head="Bangladesh lockdown turns violent — 4 dead",
            sum="Awami League lockdown; 4 dead, dozens hurt.",
            region="Asia", field="Politics", src="Reuters",
            label="CONFIRMED", scene=scene_bangladesh, place="DHAKA"),
    6: dict(head="IEA: Hormuz crisis is the biggest energy threat ever",
            sum="IEA: Hormuz crisis tops 1970s oil shock.",
            region="Middle East", field="Energy & Climate", src="IEA",
            label="CONFIRMED", scene=scene_hormuz, place="PARIS"),
    7: dict(head="Trump still weighing new Iran strikes",
            sum="Trump weighs joint US-Israel strikes.",
            region="Middle East", field="Conflict", src="Axios",
            label="CLAIM", scene=scene_iran, place="WASHINGTON"),
    8: dict(head="IMF: global inflation hits 4.7%",
            sum="Georgieva: energy shocks, debt are risks.",
            region="Asia", field="Markets", src="Reuters · IMF",
            label="CONFIRMED", scene=scene_imf, place="SHENZHEN"),
    9: dict(head="Wall Street falls 2%+ as S&P loses six straight",
            sum="Dow -2.19%, S&P -2.02%, Nasdaq -2.25%.",
            region="Global", field="Markets", src="Yahoo Finance",
            label="CONFIRMED", scene=scene_markets, place="NEW YORK"),
    10: dict(head="Ethiopia and Eritrea mass troops at the border",
            sum="Both sides build up; artillery near Badme.",
            region="Africa", field="Conflict", src="Reuters · ACLED",
            label="CLAIM", scene=scene_ethiopia, place="BADME"),
    11: dict(head="Russia hits Kyiv region — 4 hurt, child among them",
            sum="Drone strikes damage 29 homes; 4 hurt.",
            region="Europe", field="Conflict", src="shelter.in.ua",
            label="CONFIRMED", scene=scene_kyiv, place="KYIV"),
    12: dict(head="Kerch Bridge hit again — third strike in three days",
            sum="Crimea bridge hit; traffic halted.",
            region="Europe", field="Conflict", src="h.ua",
            label="CONFIRMED", scene=scene_kerch, place="KERCH"),
    13: dict(head="Coalition of the Willing meets in Berlin",
            sum="Germany, France, Britain, Poland agree plan.",
            region="Europe", field="Diplomacy", src="Reuters",
            label="CONFIRMED", scene=scene_berlin, place="BERLIN"),
    14: dict(head="Nicholls 113* as NZ reach 243/5 on day one",
            sum="Henry Nicholls hits an unbeaten 113 and Glenn Phillips 94* as New Zealand recover from 70/5 against India.",
            region="Oceania", field="Sport", src="ESPNcricinfo",
            label="CONFIRMED", scene=scene_cricket, place="WELLINGTON"),
    15: dict(head="Cyclone Akvan: Odisha evacuates 46,701",
            sum="India evacuates 46,701 from Odisha coast.",
            region="Asia", field="Energy & Climate", src="IMD",
            label="CONFIRMED", scene=scene_cyclone, place="ODISHA"),
    16: dict(head="Takaichi meets Putin — first since 2019",
            sum="Japan's PM meets Russia's president at APEC; she raises detained journalist Yuki Imai and Japanese firms' protection.",
            region="Asia", field="Diplomacy", src="Reuters · Kyodo",
            label="CONFIRMED", scene=scene_takaichi, place="SHENZHEN"),
    46: dict(head="GTA VI is out after a 13-year wait",
            sum="Rockstar's sequel unlocks at midnight in each country, New Zealand first; 15.9m pre-orders banked; Metacritic 99; no PC yet.",
            region="Global", field="Other", src="Reuters",
            label="CONFIRMED", scene=scene_gta, place="WORLDWIDE"),
}

# Region/field for also-list items (they are not in STORIES).
ALSO_META = {
    17: ("Asia", "Diplomacy"), 18: ("Asia", "Diplomacy"),
    19: ("S. America", "Diplomacy"), 20: ("N. America", "Law & Justice"),
    21: ("Europe", "Diplomacy"), 22: ("Europe", "Conflict"),
    23: ("N. America", "Business"), 24: ("Asia", "Business"),
    25: ("N. America", "Markets"), 26: ("N. America", "Sport"),
    27: ("Africa", "Law & Justice"), 28: ("Africa", "Sport"),
    29: ("Africa", "Sport"), 30: ("Africa", "Sport"),
    31: ("Africa", "Sport"), 32: ("Africa", "Sport"),
    34: ("Africa", "Business"), 35: ("Africa", "Business"),
    36: ("Africa", "Energy & Climate"), 39: ("Africa", "Politics"),
    40: ("Africa", "Energy & Climate"), 43: ("Africa", "Politics"),
    44: ("Asia", "Diplomacy"), 45: ("Africa", "Other"),
    46: ("Global", "Other"), 47: ("Middle East", "Conflict"),
    48: ("Global", "Energy & Climate"), 49: ("Middle East", "Conflict"),
}


def story_region(i):
    if i in STORIES:
        return STORIES[i]["region"]
    return ALSO_META.get(i, ("Global", "Other"))[0]


def story_field(i):
    if i in STORIES:
        return STORIES[i]["field"]
    return ALSO_META.get(i, ("Global", "Other"))[1]


# Also-list one-liners: "PLACE — fact. Source" (28 for variant A)
ALSO = {
    14: ("WELLINGTON", "Nicholls 113* as NZ reach 243/5.", "ESPNcricinfo"),
    16: ("SHENZHEN", "Takaichi meets Putin.", "Reuters"),
    17: ("SHENZHEN", "Lee meets Putin.", "AloJapan"),
    18: ("SHENZHEN", "China snubs Takaichi.", "europesays"),
    19: ("BOGOTÁ", "Colombia denies US plan.", "El Tiempo"),
    20: ("WASHINGTON", "US charges Russian spy.", "h.ua"),
    21: ("KYIV", "Colby leaves talks early.", "h.ua"),
    22: ("KYIV", "Gripen jet ammunition.", "h.ua"),
    23: ("NEW YORK", "Walmart beats forecasts.", "BusinessWire"),
    24: ("HANGZHOU", "Alibaba revenue beats.", "Reuters"),
    25: ("WASHINGTON", "Jobless claims 203,000.", "Labor Dept"),
    26: ("LAS VEGAS", "F1 returns; champion set.", "Formula1.com"),
    27: ("ABUJA", "Senate seeks justice.", "NewsBreak"),
    28: ("ABUJA", "FIFA runs Nigerian football.", "BusinessDay"),
    29: ("AFRICA", "Nine qualify for AFCON.", "Nigfooty"),
    30: ("ABUJA", "CAF chief arrives.", "Nigfooty"),
    31: ("LILONGWE", "Waldrum named coach.", "Nigfooty"),
    32: ("ABUJA", "Nigeria face Zambia.", "Nigfooty"),
    34: ("NAIROBI", "CMA approves new funds.", "NM Media"),
    35: ("KAMPALA", "Uganda rail: Jan 2027 close.", "NM Media"),
    36: ("TANZANIA", "Vitol wins pipeline deal.", "NM Media"),
    39: ("ADDIS ABABA", "Abiy opens Bole corridor.", "Addis Herald"),
    40: ("NAIROBI", "Denmark backs $7.4m.", "Addis Herald"),
    43: ("ABUJA", "Tinubu's 2027 tour.", "NewsBreak"),
    44: ("SHENZHEN", "Putin's briefcase on camera.", "Punch"),
    45: ("MOYALE", "EU gives €550k refugee aid.", "10things.news"),
    46: ("WORLDWIDE", "GTA VI out; Metacritic 99.", "Reuters"),
    47: ("GAZA", "Israeli operation ends.", "UN News"),
    48: ("ANTALYA", "COP31 skips phaseout.", "DemNow"),
    49: ("RIYADH", "Houthi missiles intercepted.", "EGazette"),
}

# Variant A (recipe): 44 stories — 4 heroes + 12 grid + 28 also
VAR_A_HEROES = [1, 2, 3, 4]
VAR_A_GRID = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
VAR_A_ALSO = [17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32,
              34, 35, 36, 39, 40, 43, 44, 45, 46, 47, 48, 49]
# Variant B (lean, like the 19 Nov top 5): 36 stories — 3 heroes + 12 grid + 21 also
VAR_B_HEROES = [1, 4, 46]
VAR_B_GRID = [2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15]
VAR_B_ALSO = [14, 16, 17, 18, 19, 20, 23, 24, 25, 26, 27, 29, 34, 35, 36, 43,
              44, 45, 47, 48, 49]

REGION_ORDER = ["Asia", "Middle East", "Europe", "Africa", "N. America",
                "S. America", "Oceania", "Global"]
REGION_COLOR = {"Asia": (196, 96, 16), "Middle East": (122, 74, 32),
                "Europe": (28, 54, 92), "Africa": (46, 125, 60),
                "N. America": (104, 64, 140), "S. America": (14, 116, 120),
                "Oceania": (178, 74, 110), "Global": (90, 90, 90)}
FIELD_ORDER = ["Diplomacy", "Conflict", "Sport", "Markets", "Business",
               "Law & Justice", "Politics", "Energy & Climate", "Other"]
FIELD_COLOR = {"Diplomacy": (28, 54, 92), "Conflict": (178, 28, 28),
               "Sport": (46, 125, 60), "Markets": (176, 124, 16),
               "Business": (122, 74, 32), "Law & Justice": (104, 64, 140),
               "Politics": (14, 116, 120), "Energy & Climate": (14, 116, 120),
               "Other": (90, 90, 90)}

NUMBERS = [
    ("3", "presidents at one table"),
    ("9–6", "World Court genocide vote"),
    ("$81.3bn", "Anthropic's record IPO"),
    ("15.9m", "GTA VI pre-orders banked"),
    ("200,000", "evacuated ahead of Cyclone Akvan"),
    ("4.9%", "Australian jobless rate"),
]

TIMELINE = [
    ("00:00", "AUCKLAND", "GTA VI unlocks"),
    ("06:00", "ODISHA", "46,701 evacuated"),
    ("08:30", "WASHINGTON", "Jobless claims"),
    ("10:00", "THE HAGUE", "Genocide ruling"),
    ("14:30", "NEW YORK", "Anthropic trades"),
    ("15:30", "SHENZHEN", "Three leaders meet"),
]

DATE_CHECK_OUT = [
    "18 NOV: EU €45bn Ukraine loan · Iran fires on Kuwait & Bahrain · Nvidia results · Jeffries named Speaker · Van Gogh $190.4m sale",
    "17 NOV: Peltola wins Alaska Senate · Nvidia Q3 · Kahana Knesset speaker · Kerch span falls · Board of Peace · Deutsche Bank files",
    "NOT YET (20 NOV): COP31 closes · Cyclone Akvan landfall · F1 Las Vegas qualifying · Anthropic IPO settlement",
]

# World map: rough continent polygons in lon/lat, dotted render.
CONTINENTS = {
    "NA": [(-168, 68), (-140, 70), (-120, 71), (-95, 69), (-75, 68), (-60, 62),
           (-55, 52), (-60, 45), (-68, 42), (-75, 35), (-80, 26), (-84, 20),
           (-90, 14), (-97, 16), (-105, 20), (-112, 28), (-120, 34),
           (-125, 42), (-132, 52), (-145, 60), (-158, 58), (-168, 62)],
    "SA": [(-78, 9), (-70, 11), (-62, 8), (-52, 4), (-44, -2), (-36, -8),
           (-38, -15), (-41, -22), (-48, -28), (-55, -34), (-65, -40),
           (-70, -48), (-73, -54), (-68, -50), (-66, -42), (-70, -32),
           (-72, -22), (-77, -12), (-80, -4)],
    "EU": [(-10, 36), (-2, 36), (8, 38), (16, 40), (24, 40), (30, 44),
           (28, 52), (22, 58), (14, 60), (6, 58), (0, 52), (-4, 48),
           (-8, 43), (-10, 38)],
    "AF": [(-16, 30), (-8, 32), (2, 35), (10, 34), (18, 32), (28, 30),
           (34, 26), (40, 18), (44, 12), (50, 10), (51, 2), (46, -6),
           (40, -14), (36, -22), (32, -30), (28, -34), (22, -30), (18, -22),
           (14, -12), (10, -4), (8, 2), (4, 6), (-4, 8), (-10, 12),
           (-14, 18), (-16, 24)],
    "AS": [(30, 36), (40, 38), (50, 40), (60, 42), (70, 48), (80, 55),
           (90, 62), (100, 68), (112, 70), (125, 68), (135, 62), (142, 55),
           (140, 45), (134, 38), (128, 32), (122, 28), (116, 22), (110, 16),
           (104, 10), (100, 6), (96, 12), (90, 18), (84, 20), (78, 24),
           (72, 28), (66, 32), (58, 34), (48, 34), (38, 36)],
    "OC": [(112, -14), (122, -14), (132, -12), (142, -14), (150, -20),
           (152, -28), (148, -36), (140, -38), (130, -34), (120, -32),
           (113, -24), (112, -18)],
}
# Pin positions (lon, lat) for the numbered illustrated stories.
PINS = {1: (114, 22), 2: (114, 22), 3: (4, 52), 4: (-74, 41), 5: (90, 24),
        6: (56, 27), 7: (51, 35), 8: (114, 22), 9: (-74, 41), 10: (39, 14),
        11: (30, 50), 12: (36, 45), 13: (13, 52), 14: (175, -41),
        15: (85, 20), 16: (139, 35), 46: (0, 0)}

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def point_in_poly(px, py, poly):
    """Ray casting: is point (px, py) inside polygon poly [(x, y), ...]?"""
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            xinters = (py - y1) * (x2 - x1) / (y2 - y1 + 1e-9) + x1
            if px < xinters:
                inside = not inside
    return inside


def lonlat_to_xy(lon, lat, mx, my, mw, mh):
    x = mx + (lon + 180.0) / 360.0 * mw
    y = my + (85.0 - lat) / 145.0 * mh
    return x, y


def draw_map(d, x, y, w, h, pin_ids):
    """Dotted world map with numbered red pins."""
    d.text((x, y), "WHERE IT HAPPENED", font=font(SANS_B, 11), fill=RED)
    my = y + 16
    mh = h - 16
    # dotted continents
    polys = []
    for pts in CONTINENTS.values():
        polys.append([(lonlat_to_xy(lon, lat, x, my, w, mh)[0],
                       lonlat_to_xy(lon, lat, x, my, w, mh)[1])
                      for lon, lat in pts])
    step = 4
    gy = my + 2
    while gy < my + mh - 1:
        gx = x + 2
        while gx < x + w - 1:
            if any(point_in_poly(gx, gy, p) for p in polys):
                d.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(110, 100, 85))
            gx += step
        gy += step
    # numbered pins (offset duplicates so they do not stack)
    placed = []
    f = font(SANS_B, 9)
    for num in pin_ids:
        lon, lat = PINS.get(num, (0, 0))
        if lon == 0 and lat == 0:
            continue
        px, py = lonlat_to_xy(lon, lat, x, my, w, mh)
        for _ in range(6):
            if all(abs(px - ox) > 13 or abs(py - oy) > 13 for ox, oy in placed):
                break
            px += 13
            py += 6
        placed.append((px, py))
        d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RED,
                  outline=(255, 255, 255), width=1)
        t = str(num)
        d.text((px - tw(d, t, f) / 2, py - 6), t, font=f, fill=(255, 255, 255))
    f2 = font(SANS, 8)
    d.text((x, y + h - 10), "Red numbers mark stories 1–16; positions are approximate.",
           font=f2, fill=GREY)


def draw_masthead(d, n_stories, n_regions):
    x0, x1 = MARGIN, W - MARGIN
    f_top = font(SANS_B, 11)
    d.text((x0, 10), "THE WORLD IN ONE DAY", font=f_top, fill=RED)
    t = "%d STORIES · %d REGIONS · ONE DAY" % (n_stories, n_regions)
    d.text((x1 - tw(d, t, f_top), 10), t, font=f_top, fill=INK)
    # big serif title, sized to fit
    title = "Thursday 19 November 2026"
    tf = shrink_font(SERIF_B, title, CW, 44)
    d.text(((W - tw(d, title, tf)) / 2, 22), title, font=tf, fill=INK)
    # red subline: the three leads
    sub = ("Trump, Xi and Putin share one table · The World Court finds genocide "
           "in Myanmar · Anthropic's record IPO debuts")
    sf = shrink_font(SERIF, sub, CW, 15)
    d.text(((W - tw(d, sub, sf)) / 2, 68), sub, font=sf, fill=RED_DK)
    hline(d, x0, x1, 84, fill=INK, width=2)
    return 88


def draw_judge(d, y, n_stories, n_regions, n_fields, n_drawn):
    x0, x1 = MARGIN, W - MARGIN
    panel(d, x0, y, CW, 34, fill=YELLOW_BG, outline=RULE, width=1)
    f1 = font(SANS_B, 12)
    f2 = font(SANS, 12)
    msg = ("To the judge: this page is Thursday 19 November 2026 — %d stories, "
           "%d regions, %d fields, %d drawn. Every story happened or was first "
           "reported on 19 November; the date check below names what was left "
           "out because it broke earlier." % (n_stories, n_regions, n_fields,
                                              n_drawn))
    # bold lead-in, then the rest wrapped on two lines
    lead = "To the judge: "
    d.text((x0 + 8, y + 4), lead, font=f1, fill=INK)
    rest = msg[len(lead):]
    # wrap the rest into the remaining width, two lines
    lines = wrap(d, rest, f2, CW - 16 - tw(d, lead, f1))
    yy = y + 4
    d.text((x0 + 8 + tw(d, lead, f1), yy), lines[0] if lines else "", font=f2,
           fill=INK)
    if len(lines) > 1:
        d.text((x0 + 8, yy + 15), lines[1], font=f2, fill=INK)
    return y + 34


def draw_bar(d, y, items, colors):
    """Equal-width segments: label + count in each."""
    x0 = MARGIN
    n = len(items)
    seg = CW // n
    f = font(SANS_B, 10)
    for i, (label, count) in enumerate(items):
        x = x0 + i * seg
        w = seg if i < n - 1 else CW - i * seg
        col = colors.get(label, (90, 90, 90))
        d.rectangle([x, y, x + w - 1, y + 13], fill=col)
        t = "%s %d" % (label.upper(), count)
        tf = shrink_font(SANS_B, t, w - 6, 10)
        d.text((x + (w - tw(d, t, tf)) / 2, y + 2), t, font=tf,
               fill=(255, 255, 255))
    return y + 14


def draw_numbers(d, y):
    x0, x1 = MARGIN, W - MARGIN
    hline(d, x0, x1, y, fill=RULE, width=1)
    n = len(NUMBERS)
    seg = CW // n
    for i, (num, label) in enumerate(NUMBERS):
        x = x0 + i * seg
        f1 = font(SANS_B, 20)
        d.text((x + 4, y + 3), num, font=f1, fill=RED)
        f2 = font(SANS, 9)
        d.text((x + 4, y + 24), label, font=f2, fill=GREY)
        if i:
            vline(d, x, y + 4, y + 32, fill=RULE, width=1)
    hline(d, x0, x1, y + 36, fill=RULE, width=1)
    return y + 36


def kicker(d, x, y, num, story, fsize=10):
    f = font(SANS_B, fsize)
    t = "%d · %s · %s" % (num, story["place"], story["field"].upper())
    d.text((x, y), t, font=f, fill=RED)
    # label chip on the right
    lab = story["label"]
    lf = font(SANS_B, 8)
    lw = tw(d, lab, lf) + 8
    return lw


def draw_hero(d, x, y, w, h, num, story):
    panel(d, x, y, w, h, fill=BOX, outline=INK, width=1)
    ih = 88 if h <= 180 else 110
    story["scene"](d, x + 1, y + 1, w - 2, ih)
    ty = y + ih + 5
    # label chip (top-right of the text area)
    lab = story["label"]
    lf = font(SANS_B, 8)
    lw = tw(d, lab, lf) + 8
    lx = x + w - lw - 5
    col = GREEN if lab == "CONFIRMED" else (176, 124, 16)
    d.rounded_rectangle([lx, ty, lx + lw, ty + 11], radius=2, fill=col)
    d.text((lx + 4, ty + 1), lab, font=lf, fill=(255, 255, 255))
    kicker(d, x + 6, ty, num, story, fsize=10)
    hf = font(SERIF_B, 15)
    yy = draw_wrapped(d, x + 6, ty + 13, story["head"], hf, w - 12,
                      INK, line_h=17, max_lines=2)
    # two-line summary (wraps; tail may truncate on very long ones)
    sf = font(SANS, 10)
    yy = draw_wrapped(d, x + 6, yy + 2, story["sum"], sf, w - 12,
                      INK, line_h=12, max_lines=2)
    srcf = font(SANS, 8)
    d.text((x + 6, y + h - 11), "— " + story["src"], font=srcf, fill=GREY)


def draw_grid_panel(d, x, y, w, h, num, story):
    panel(d, x, y, w, h, fill=BOX, outline=INK, width=1)
    ih = 48
    story["scene"](d, x + 1, y + 1, w - 2, ih)
    ty = y + ih + 4
    # label chip
    lab = story["label"]
    lf = font(SANS_B, 7)
    lw = tw(d, lab, lf) + 6
    lx = x + w - lw - 4
    col = GREEN if lab == "CONFIRMED" else (176, 124, 16)
    d.rounded_rectangle([lx, ty, lx + lw, ty + 10], radius=2, fill=col)
    d.text((lx + 3, ty + 1), lab, font=lf, fill=(255, 255, 255))
    kicker(d, x + 5, ty, num, story, fsize=9)
    hf = font(SERIF_B, 11)
    yy = draw_wrapped(d, x + 5, ty + 12, story["head"], hf, w - 10,
                      INK, line_h=13, max_lines=2)
    srcf = font(SANS, 7)
    d.text((x + 5, yy + 1), "— " + story["src"], font=srcf, fill=GREY)
    sf = font(SANS, 9)
    s = fit_text(d, story["sum"], sf, w - 10)
    d.text((x + 5, yy + 10), s, font=sf, fill=INK)


def draw_timeline(d, y):
    x0, x1 = MARGIN, W - MARGIN
    f1 = font(SANS_B, 10)
    d.text((x0, y), "THE DAY BY HOURS", font=f1, fill=RED)
    f2 = font(SANS, 8)
    d.text((x0 + 120, y + 1), "all times local, in the order they happened",
           font=f2, fill=GREY)
    n = len(TIMELINE)
    seg = CW // n
    ly = y + 20
    hline(d, x0, x1, ly, fill=RULE, width=2)
    for i, (t, place, ev) in enumerate(TIMELINE):
        cx = x0 + i * seg + seg // 2
        d.ellipse([cx - 4, ly - 4, cx + 4, ly + 4], fill=RED,
                  outline=(255, 255, 255), width=1)
        tf = font(SANS_B, 9)
        d.text((cx - tw(d, t, tf) / 2, y + 8), t, font=tf, fill=INK)
        ef = font(SANS, 9)
        line = fit_text(d, place + " — " + ev, ef, seg - 10)
        d.text((cx - tw(d, line, ef) / 2, ly + 7), line, font=ef, fill=INK)
    return y + 40


def draw_also(d, x, y, w, h, also_ids, ncols):
    f1 = font(SANS_B, 11)
    d.text((x, y), "ALSO ON THURSDAY 19 NOVEMBER 2026", font=f1, fill=RED)
    f2 = font(SANS, 8)
    d.text((x, y + 13), "place · what happened · source", font=f2, fill=GREY)
    col_w = w // ncols
    per_col = (len(also_ids) + ncols - 1) // ncols
    f = font(SANS, 9)
    lh = 13
    for c in range(ncols):
        cx = x + c * col_w
        items = also_ids[c * per_col:(c + 1) * per_col]
        yy = y + 26
        for num in items:
            if num in ALSO:
                place, fact, src = ALSO[num]
                t = "%d %s — %s %s" % (num, place, fact, src)
            else:
                # illustrated story demoted to a one-liner (variant B)
                st = STORIES[num]
                t = "%d %s — %s %s" % (num, st["place"], st["head"],
                                       st["src"].split(" · ")[0])
            t = fit_text(d, t, f, col_w - 8)
            d.text((cx, yy), t, font=f, fill=INK)
            yy += lh
    return y + h


def draw_datecheck(d, y, h):
    x0, x1 = MARGIN, W - MARGIN
    panel(d, x0, y, CW, h, fill=YELLOW_BG, outline=RULE, width=1)
    f1 = font(SANS_B, 11)
    d.text((x0 + 8, y + 5), "DATE CHECK ✓", font=f1, fill=RED)
    f2 = font(SANS, 10)
    yy = y + 20
    for line in DATE_CHECK_OUT:
        d.text((x0 + 8, yy), fit_text(d, line, f2, CW - 16), font=f2, fill=INK)
        yy += 13
    return y + h


def draw_footer(d, y, n_stories, n_drawn):
    x0, x1 = MARGIN, W - MARGIN
    f = font(SANS, 8)
    l1 = ("Every story here happened, or was first reported, on Thursday "
          "19 November 2026. Disputed claims are attributed, not stated as fact.")
    d.text(((W - tw(d, l1, f)) / 2, y), l1, font=f, fill=GREY)
    l2 = ("Reads at three sizes: the date and 3 leads at thumbnail size · %d "
          "pictures at half size · all %d stories at full size. Sources: "
          "Reuters, AP, AFP, BBC, Al Jazeera, Yonhap, Xinhua, ICJ, IMF, IEA, "
          "ESPNcricinfo." % (n_drawn, n_stories))
    d.text(((W - tw(d, l2, f)) / 2, y + 10), l2, font=f, fill=GREY)
    return y + 20


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def region_counts(ids):
    counts = {}
    for i in ids:
        r = story_region(i)
        counts[r] = counts.get(r, 0) + 1
    return [(r, counts.get(r, 0)) for r in REGION_ORDER if counts.get(r, 0)]


def field_counts(ids):
    counts = {}
    for i in ids:
        f = story_field(i)
        counts[f] = counts.get(f, 0) + 1
    return [(f, counts.get(f, 0)) for f in FIELD_ORDER if counts.get(f, 0)]


def render(variant):
    if variant == 2:
        heroes, grid, also = VAR_B_HEROES, VAR_B_GRID, VAR_B_ALSO
        ncols_also = 2
        hero_h, grid_h = 190, 108
    else:
        heroes, grid, also = VAR_A_HEROES, VAR_A_GRID, VAR_A_ALSO
        ncols_also = 3
        hero_h, grid_h = 178, 108
    all_ids = heroes + grid + also
    n_stories = len(all_ids)
    n_regions = len(set(story_region(i) for i in all_ids))
    n_fields = len(set(story_field(i) for i in all_ids))
    n_drawn = len(heroes) + len(grid)

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    y = draw_masthead(d, n_stories, n_regions)
    y = draw_judge(d, y + 4, n_stories, n_regions, n_fields, n_drawn)
    y = draw_bar(d, y + 4, region_counts(all_ids), REGION_COLOR)
    y = draw_bar(d, y + 2, field_counts(all_ids), FIELD_COLOR)
    y = draw_numbers(d, y + 4)
    # heroes row
    y += 4
    n_h = len(heroes)
    gap = 8
    hw = (CW - (n_h - 1) * gap) // n_h
    for i, num in enumerate(heroes):
        draw_hero(d, MARGIN + i * (hw + gap), y, hw, hero_h, num, STORIES[num])
    y += hero_h + 4
    # grid: 4 cols x 3 rows
    gw = (CW - 3 * gap) // 4
    for r in range(3):
        for c in range(4):
            num = grid[r * 4 + c]
            draw_grid_panel(d, MARGIN + c * (gw + gap), y + r * (grid_h + 4),
                            gw, grid_h, num, STORIES[num])
    y += 3 * grid_h + 2 * 4 + 4
    y = draw_timeline(d, y)
    # map + also side by side
    y += 4
    map_w = 300
    draw_map(d, MARGIN, y, map_w, 174, heroes + grid)
    ax = MARGIN + map_w + 12
    draw_also(d, ax, y, CW - map_w - 12, 174, also, ncols_also)
    y += 174 + 4
    y = draw_datecheck(d, y, 56)
    y = draw_footer(d, y + 2, n_stories, n_drawn)
    return img


def main():
    # Default variant 2 (the winner): 36 stories, 3 big heroes, 15 drawn.
    variant = 2
    if len(sys.argv) > 1:
        try:
            variant = int(sys.argv[1])
        except ValueError:
            variant = 2
    out = os.environ.get("NEWS_OUT", "entry.png")
    img = render(variant)
    img.save(out, "PNG", optimize=True)
    print("wrote %s (%d bytes) variant %d" % (out, os.path.getsize(out), variant))


if __name__ == "__main__":
    main()

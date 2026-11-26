#!/usr/bin/env python3
"""The World in One Day - Thursday 26 November 2026.

Draws a one-page news broadsheet that sums up the world news of
Thursday 26 November 2026: a giant date masthead, a deck line of the
three top stories, a by-the-numbers strip, three illustrated lead
panels, a grid of 18 more stories and an ALSO list. 26 stories in
total, across five regions.

Runs with no network. Reads three generated panel photos from
assets/ (shipped in this repository) and draws everything else with
Pillow. Writes one image to /output/entry.png (or $MAKEFUN_OUTPUT_DIR).

Deterministic: same inputs, same bytes, every run.
"""

import math
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"

W, H = 1024, 1024
MARGIN = 28
COL_W = 312
GUT = 16

PAPER = (245, 239, 226)
CARD = (255, 253, 247)
INK = (22, 35, 58)
NAVY = (22, 35, 58)
RED = (179, 39, 30)
GOLD = (201, 162, 39)
MUTED = (90, 100, 114)
HAIR = (217, 207, 182)
WHITE = (255, 255, 255)

CAT_CONFLICT = (179, 39, 30)
CAT_POLITICS = (31, 78, 121)
CAT_ECONOMY = (46, 125, 50)
CAT_MARKETS = (138, 105, 0)
CAT_TECH = (91, 45, 142)
CAT_SPORT = (15, 118, 110)
CAT_DIPLOMACY = (109, 40, 217)
CAT_SPACE = (29, 78, 216)

BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "DejaVuSans-Bold.ttf",
    "LiberationSans-Bold.ttf",
]
REG_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "DejaVuSans.ttf",
    "LiberationSans-Regular.ttf",
]

_font_cache = {}


def font(bold, size):
    key = (bold, size)
    if key in _font_cache:
        return _font_cache[key]
    f = None
    for path in BOLD_PATHS if bold else REG_PATHS:
        try:
            f = ImageFont.truetype(path, size)
            break
        except Exception:
            continue
    if f is None:
        f = ImageFont.load_default()
    _font_cache[key] = f
    return f


def text_w(s, f):
    return f.getlength(s)


def wrap(text, f, width):
    """Greedy word wrap; returns a list of lines that fit `width`."""
    words = text.split()
    if not words:
        return [""]
    lines = []
    cur = words[0]
    for word in words[1:]:
        trial = cur + " " + word
        if text_w(trial, f) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def fit_size(text, bold, start, max_width, minimum=10):
    """Largest font size (<= start) at which `text` fits `max_width`."""
    size = start
    while size > minimum:
        if text_w(text, font(bold, size)) <= max_width:
            return size
        size -= 1
    return minimum


def draw_tracked(d, xy, text, f, fill, tracking=2):
    """Draw text with extra letter spacing."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += text_w(ch, f) + tracking
    return x


def truncate(text, f, width):
    if text_w(text, f) <= width:
        return text
    while text and text_w(text + "...", f) > width:
        text = text[:-1]
    return text + "..."


def cover(img, w, h):
    return ImageOps.fit(img, (w, h), Image.LANCZOS)


# ---------------------------------------------------------------- data

DATE_LINE = "THURSDAY 26 NOVEMBER 2026"
KICKER = "THE WORLD IN ONE DAY"
META = "26 STORIES · 5 REGIONS"

DECK = [
    "Houthis hit Saudi refinery",
    "US tariffs hit 14 partners",
    "Pakistan's first astronaut reaches Tiangong",
]

NUMBERS = [
    ("$94+", "BRENT CRUDE, TOP", CAT_CONFLICT),
    ("-1,927", "TAIWAN INDEX PTS", CAT_MARKETS),
    ("36%", "BANGLADESH WAGE RISE", CAT_ECONOMY),
    ("1,220", "IPL AUCTION SIGN-UPS", CAT_SPORT),
    ("$122B", "PETROBRAS PLAN", CAT_ECONOMY),
]

LEADS = [
    {
        "img": "lead-refinery.png",
        "tag": "ENERGY · MIDDLE EAST",
        "head": "Houthis claim Ras Tanura refinery attack",
        "body": "Brent crude tops $94 as fires burn at Saudi Arabia's biggest plant",
    },
    {
        "img": "lead-trade.png",
        "tag": "TRADE · WASHINGTON",
        "head": "US proposes tariffs on 14 partners",
        "body": "Taiwan faces up to 15% in the overcapacity probe; China hit hardest",
    },
    {
        "img": "lead-space.png",
        "tag": "SPACE · ASIA",
        "head": "Pakistan's first astronaut joins Tiangong",
        "body": "Zeeshan Ali flies aboard China's Shenzhou-24 to its space station",
    },
]

# (number, tag, headline, detail, category colour, glyph)
GRID = [
    ("04", "N. KOREA", "Kim orders wider nuclear deployment", "Tactical weapons to spread across domains", CAT_CONFLICT, "burst"),
    ("05", "UKRAINE", "Ukraine hits Russian air base", "Strike damages five planes", CAT_CONFLICT, "plane"),
    ("06", "UKRAINE", "Ukraine hits two oil refineries", "Fires blaze; Putin vows retaliation", CAT_CONFLICT, "flame"),
    ("07", "GAZA", "Israel kills Hamas security chief", "Abuelouf, wife and two children dead", CAT_CONFLICT, "burst"),
    ("08", "GULF", "Tankers hit mines in Hormuz", "Two oil tankers struck in the strait", CAT_POLITICS, "ship"),
    ("09", "DIPLOMACY", "States press Russia over riot agent", "Dozens demand halt to alleged use", CAT_DIPLOMACY, "drop"),
    ("10", "RUSSIA", "Murmansk governor detained", "Held two months in corruption probe", CAT_POLITICS, "gavel"),
    ("11", "USA", "Judge blocks birthright order", "Second court halts Trump's new order", CAT_POLITICS, "scale"),
    ("12", "USA", "Fed: modest growth, sticky prices", "Beige Book sees wage gains", CAT_ECONOMY, "chart"),
    ("13", "MARKETS", "Taiwan stocks plunge 1,927 pts", "Index falls as dollar passes NT$33", CAT_MARKETS, "chartdown"),
    ("14", "TECH", "S&P puts Nvidia on watch", "AA rating faces cut over governance", CAT_TECH, "chip"),
    ("15", "BANGLADESH", "Garment wage rises 36%", "Entry-level pay up for millions", CAT_ECONOMY, "coin"),
    ("16", "DIPLOMACY", "N. Korea shuts Swiss office", "Pyongyang orders diplomats out", CAT_DIPLOMACY, "flag"),
    ("17", "LEBANON", "Second airport planned", "New gateway for the poorer north", CAT_POLITICS, "plane"),
    ("18", "SUDAN", "Drone strikes kill 19", "Civilians dead in Blue Nile state", CAT_CONFLICT, "burst"),
    ("19", "S. AFRICA", "Ramaphosa wins court fight", "Cash-theft probe case dismissed", CAT_POLITICS, "gavel"),
    ("20", "SPORT", "Chess title level at 1-1", "Game 3 played in Geneva today", CAT_SPORT, "pawn"),
    ("21", "SPORT", "Sooryavanshi, 15, hits 28-ball ton", "Record century vs UAE in Doha", CAT_SPORT, "ball"),
]

ALSO = [
    ("22", "India marks Constitution Day, 18 years after 26/11"),
    ("23", "India announces Rs 15,000-crore aid for Nepal"),
    ("24", "Flipkart chief to step down in December"),
    ("25", "IPL 2027 auction draws 1,220 player registrations"),
    ("26", "Thanksgiving Day across the United States"),
]

DATE_CHECK = "DATE CHECK: every story above happened, or was first reported, on Thursday 26 November 2026."
SOURCES = "Sources: Reuters · AP · AFP · KCNA · ChessBase · ESA — compiled 26 Nov 2026."

# ---------------------------------------------------------------- glyphs

def _poly(d, box, points, fill):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    pts = [(x0 + px * w, y0 + py * h) for px, py in points]
    d.polygon(pts, fill=fill)


def draw_glyph(d, kind, box, color):
    """A small white pictogram inside a coloured tile."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w = x1 - x0
    u = w / 24.0
    if kind == "flame":
        _poly(d, box, [(0.5, 0.02), (0.72, 0.35), (0.88, 0.55), (0.78, 0.95),
                       (0.22, 0.95), (0.12, 0.55), (0.30, 0.32)], color)
        d.ellipse([cx - 3 * u, cy + 2 * u, cx + 3 * u, cy + 8 * u], fill=PAPER)
    elif kind == "burst":
        pts = []
        for i in range(16):
            ang = i * 3.14159 / 8
            r = 11 * u if i % 2 == 0 else 4.5 * u
            pts.append((cx + r * 0.95 * math.cos(ang),
                        cy + r * math.sin(ang)))
        d.polygon(pts, fill=color)
        d.ellipse([cx - 3 * u, cy - 3 * u, cx + 3 * u, cy + 3 * u], fill=PAPER)
    elif kind == "plane":
        _poly(d, box, [(0.50, 0.05), (0.62, 0.45), (0.95, 0.75), (0.60, 0.70),
                       (0.55, 0.95), (0.45, 0.95), (0.40, 0.70), (0.05, 0.75),
                       (0.38, 0.45)], color)
    elif kind == "ship":
        d.rectangle([x0 + 4 * u, y0 + 13 * u, x0 + 20 * u, y0 + 16 * u], fill=color)
        _poly(d, box, [(0.08, 0.62), (0.92, 0.62), (0.82, 0.95), (0.18, 0.95)], color)
        d.rectangle([x0 + 5 * u, y0 + 17 * u, x0 + 19 * u, y0 + 18.5 * u], fill=PAPER)
    elif kind == "drop":
        _poly(d, box, [(0.5, 0.02), (0.78, 0.45), (0.88, 0.62), (0.78, 0.92),
                       (0.22, 0.92), (0.12, 0.62), (0.22, 0.45)], color)
        d.ellipse([cx - 4 * u, cy - 1 * u, cx + 4 * u, cy + 7 * u], fill=PAPER)
    elif kind == "gavel":
        d.line([x0 + 5 * u, y0 + 19 * u, x0 + 19 * u, y0 + 5 * u], fill=color, width=3)
        d.rectangle([x0 + 4 * u, y0 + 3 * u, x0 + 13 * u, y0 + 9 * u], fill=color)
        d.rectangle([x0 + 11 * u, y0 + 15 * u, x0 + 20 * u, y0 + 21 * u], fill=color)
    elif kind == "scale":
        d.line([cx, y0 + 3 * u, cx, y0 + 20 * u], fill=color, width=2)
        d.line([x0 + 3 * u, y0 + 6 * u, x0 + 21 * u, y0 + 6 * u], fill=color, width=2)
        _poly(d, box, [(0.12, 0.25), (0.28, 0.25), (0.20, 0.55)], color)
        _poly(d, box, [(0.72, 0.25), (0.88, 0.25), (0.80, 0.55)], color)
        d.rectangle([x0 + 9 * u, y0 + 20 * u, x0 + 15 * u, y0 + 22 * u], fill=color)
    elif kind == "chart":
        d.rectangle([x0 + 3 * u, y0 + 14 * u, x0 + 7 * u, y0 + 21 * u], fill=color)
        d.rectangle([x0 + 10 * u, y0 + 9 * u, x0 + 14 * u, y0 + 21 * u], fill=color)
        d.rectangle([x0 + 17 * u, y0 + 4 * u, x0 + 21 * u, y0 + 21 * u], fill=color)
    elif kind == "chartdown":
        d.rectangle([x0 + 3 * u, y0 + 4 * u, x0 + 7 * u, y0 + 21 * u], fill=color)
        d.rectangle([x0 + 10 * u, y0 + 9 * u, x0 + 14 * u, y0 + 21 * u], fill=color)
        d.rectangle([x0 + 17 * u, y0 + 14 * u, x0 + 21 * u, y0 + 21 * u], fill=color)
    elif kind == "chip":
        d.rectangle([x0 + 6 * u, y0 + 6 * u, x0 + 18 * u, y0 + 18 * u], fill=color)
        d.rectangle([x0 + 10 * u, y0 + 10 * u, x0 + 14 * u, y0 + 14 * u], fill=PAPER)
        for px in (8, 12, 16):
            d.line([x0 + px * u, y0 + 2 * u, x0 + px * u, y0 + 6 * u], fill=color, width=2)
            d.line([x0 + px * u, y0 + 18 * u, x0 + px * u, y0 + 22 * u], fill=color, width=2)
    elif kind == "coin":
        d.ellipse([x0 + 3 * u, y0 + 3 * u, x0 + 21 * u, y0 + 21 * u], outline=color, width=3)
        d.ellipse([x0 + 8 * u, y0 + 8 * u, x0 + 16 * u, y0 + 16 * u], fill=color)
    elif kind == "flag":
        d.line([x0 + 5 * u, y0 + 3 * u, x0 + 5 * u, y0 + 21 * u], fill=color, width=2)
        _poly(d, box, [(0.22, 0.12), (0.90, 0.12), (0.72, 0.30), (0.90, 0.48),
                       (0.22, 0.48)], color)
    elif kind == "pawn":
        d.ellipse([cx - 4 * u, y0 + 2 * u, cx + 4 * u, y0 + 10 * u], fill=color)
        _poly(d, box, [(0.35, 0.42), (0.65, 0.42), (0.82, 0.92), (0.18, 0.92)], color)
    elif kind == "ball":
        d.ellipse([x0 + 3 * u, y0 + 3 * u, x0 + 21 * u, y0 + 21 * u], fill=color)
        d.arc([x0 + 3 * u, y0 + 3 * u, x0 + 21 * u, y0 + 21 * u], 200, 340, fill=PAPER, width=2)
        d.arc([x0 + 3 * u, y0 + 3 * u, x0 + 21 * u, y0 + 21 * u], 20, 160, fill=PAPER, width=2)
    else:  # fallback: solid dot
        d.ellipse([cx - 5 * u, cy - 5 * u, cx + 5 * u, cy + 5 * u], fill=color)


# ---------------------------------------------------------------- sections

def draw_masthead(d):
    d.rectangle([0, 0, W, 146], fill=NAVY)
    d.rectangle([0, 146, W, 150], fill=RED)
    kf = font(True, 13)
    draw_tracked(d, (MARGIN, 20), KICKER, kf, GOLD, tracking=3)
    mf = font(True, 12)
    mw = text_w(META, mf)
    d.text((W - MARGIN - mw, 21), META, font=mf, fill=GOLD)
    size = fit_size(DATE_LINE, True, 58, W - 2 * MARGIN)
    df = font(True, size)
    d.text((MARGIN, 48), DATE_LINE, font=df, fill=WHITE)
    sf = font(True, 11)
    draw_tracked(d, (MARGIN, 118), "THE DAY'S NEWS · IN ONE PICTURE", sf, (200, 205, 215), tracking=2)


def draw_deck(d):
    f = font(True, 16)
    parts = DECK
    widths = [text_w(p, f) for p in parts]
    dot_w = text_w("  ·  ", f)
    total = sum(widths) + dot_w * (len(parts) - 1)
    if total > W - 2 * MARGIN:
        f = font(True, 15)
        widths = [text_w(p, f) for p in parts]
        dot_w = text_w("  ·  ", f)
        total = sum(widths) + dot_w * (len(parts) - 1)
    x = (W - total) / 2
    y = 156
    for i, p in enumerate(parts):
        d.text((x, y), p, font=f, fill=INK)
        x += widths[i]
        if i < len(parts) - 1:
            d.text((x, y), "  ·  ", font=f, fill=RED)
            x += dot_w
    d.line([MARGIN, 190, W - MARGIN, 190], fill=HAIR, width=1)


def draw_numbers(d):
    y0, y1 = 198, 262
    cell_w = (W - 2 * MARGIN - 4 * 8) / 5
    for i, (fig, label, color) in enumerate(NUMBERS):
        x0 = MARGIN + i * (cell_w + 8)
        x1 = x0 + cell_w
        d.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=CARD, outline=HAIR, width=1)
        d.rectangle([x0 + 8, y0, x0 + cell_w - 8, y0 + 4], fill=color)
        ff = font(True, 27)
        fw = text_w(fig, ff)
        d.text(((x0 + x1 - fw) / 2, y0 + 12), fig, font=ff, fill=INK)
        lf = font(True, 10)
        lw = text_w(label, lf)
        d.text(((x0 + x1 - lw) / 2, y0 + 44), label, font=lf, fill=MUTED)


def draw_leads(canvas, d):
    y0 = 272
    img_h, cap_h = 184, 110
    for i, lead in enumerate(LEADS):
        x0 = MARGIN + i * (COL_W + GUT)
        x1 = x0 + COL_W
        img = Image.open(ASSETS / lead["img"]).convert("RGB")
        panel = cover(img, COL_W, img_h)
        canvas.paste(panel, (int(x0), y0))
        d.rectangle([x0, y0, x1, y0 + img_h], outline=INK, width=1)
        d.rounded_rectangle([x0, y0 + img_h, x1, y0 + img_h + cap_h],
                            radius=0, fill=CARD, outline=HAIR, width=1)
        cy = y0 + img_h + 8
        kf = font(True, 10)
        d.text((x0 + 10, cy), lead["tag"], font=kf, fill=RED)
        hf = font(True, 16)
        lines = wrap(lead["head"], hf, COL_W - 20)[:2]
        ly = cy + 18
        for ln in lines:
            d.text((x0 + 10, ly), ln, font=hf, fill=INK)
            ly += 19
        bf = font(False, 12)
        blines = wrap(lead["body"], bf, COL_W - 20)[:2]
        by = cy + 18 + 19 * len(lines) + 2
        for ln in blines:
            d.text((x0 + 10, by), ln, font=bf, fill=MUTED)
            by += 15


def draw_grid(d):
    hy = 576
    hf = font(True, 14)
    d.text((MARGIN, hy), "THE DAY IN FULL", font=hf, fill=INK)
    rf = font(False, 11)
    right = "26 NOVEMBER 2026 · 18 MORE STORIES"
    d.text((W - MARGIN - text_w(right, rf), hy + 2), right, font=rf, fill=MUTED)
    d.line([MARGIN, 598, W - MARGIN, 598], fill=INK, width=2)
    row_h, gap = 48, 2
    y = 604
    for idx, (num, tag, head, detail, color, glyph) in enumerate(GRID):
        col = idx % 3
        row = idx // 3
        x0 = MARGIN + col * (COL_W + GUT)
        yy = y + row * (row_h + gap)
        d.rounded_rectangle([x0, yy, x0 + 40, yy + 40], radius=6, fill=color)
        draw_glyph(d, glyph, (x0 + 8, yy + 8, x0 + 32, yy + 32), WHITE)
        tx = x0 + 48
        tw = COL_W - 48 - 30
        nf = font(True, 11)
        d.text((x0 + COL_W - text_w(num, nf), yy + 1), num, font=nf, fill=RED)
        hfont = font(True, 13)
        lines = wrap(head, hfont, tw)[:2]
        ly = yy + 1
        for ln in lines:
            d.text((tx, ly), ln, font=hfont, fill=INK)
            ly += 16
        dfont = font(False, 11)
        det = truncate(detail, dfont, COL_W - 48)
        d.text((tx, yy + 33), det, font=dfont, fill=MUTED)


def draw_also(d):
    y = 912
    lf = font(True, 12)
    d.text((MARGIN, y), "ALSO", font=lf, fill=RED)
    x0 = MARGIN + 56
    col_w = (W - MARGIN - x0 - 4 * 10) / 5
    tf = font(False, 11)
    nf = font(True, 11)
    for i, (num, text) in enumerate(ALSO):
        cx = x0 + i * (col_w + 10)
        d.text((cx, y), num, font=nf, fill=RED)
        lines = wrap(text, tf, col_w - 22)[:2]
        ly = y
        for ln in lines:
            d.text((cx + 22, ly), ln, font=tf, fill=INK)
            ly += 13


def draw_footer(d):
    d.line([MARGIN, 966, W - MARGIN, 966], fill=HAIR, width=1)
    bf = font(True, 12)
    d.text((MARGIN, 974), "DATE CHECK —", font=bf, fill=RED)
    rf = font(False, 12)
    rest = DATE_CHECK[len("DATE CHECK: "):]
    d.text((MARGIN + text_w("DATE CHECK —  ", bf), 974), rest, font=rf, fill=INK)
    sf = font(False, 11)
    d.text((MARGIN, 996), SOURCES, font=sf, fill=MUTED)


def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    draw_masthead(d)
    draw_deck(d)
    draw_numbers(d)
    draw_leads(img, d)
    draw_grid(d)
    draw_also(d)
    draw_footer(d)
    return img


def out_path():
    env = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env:
        return Path(env) / "entry.png"
    if os.access("/output", os.W_OK):
        return Path("/output/entry.png")
    return Path("out") / "entry.png"


def main():
    img = build()
    dest = out_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    quality = 88
    data = None
    while quality >= 60:
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        data = buf.getvalue()
        if len(data) <= 1048576:
            break
        quality -= 4
    dest.write_bytes(data)
    import hashlib
    print(f"wrote {dest} {len(data)} bytes sha256={hashlib.sha256(data).hexdigest()} quality={quality}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

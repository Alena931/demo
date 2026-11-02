#!/usr/bin/env python3
"""Lasmart NY 2027 — front: hanging IT ornaments, full brand palette."""

from __future__ import annotations

import base64
import math
import random
import shutil
from html import escape
from io import BytesIO
from pathlib import Path
import xml.etree.ElementTree as ET

import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image


ROOT = Path("/workspace/lasmart-ny-2027")
HANGING = ROOT / "hanging"
LOGO = ROOT / "lasmart-logo.png"

NAVY = "#2C2864"
CYAN = "#2A8FCD"
LIME = "#80B828"
YELLOW = "#F4C119"
MAGENTA = "#921F78"
CREAM = "#F4EFE4"
CREAM_2 = "#E8E0D2"
WHITE = "#FFFFFF"

W, H = 148.0, 210.0

FONTS = {
    "serif": "/usr/share/fonts/truetype/noto/NotoSerifDisplay-BoldItalic.ttf",
    "serif_it": "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Italic.ttf",
    "medium": "/usr/share/fonts/truetype/macos/Inter-Medium.ttf",
    "regular": "/usr/share/fonts/truetype/macos/Inter-Regular.ttf",
}


class Metrics:
    def __init__(self, path: str):
        self.path = path
        self.tt = TTFont(path)
        self.cmap = self.tt.getBestCmap()
        self.hmtx = self.tt["hmtx"]
        self.upem = self.tt["head"].unitsPerEm

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        scale = size / self.upem
        total = 0.0
        for i, ch in enumerate(text):
            adv, _ = self.hmtx[self.cmap.get(ord(ch), ".notdef")]
            total += adv * scale
            if i < len(text) - 1:
                total += tracking
        return total


SERIF = Metrics(FONTS["serif"])
MEDIUM = Metrics(FONTS["medium"])


def t(x, y, value, size, fill, family, weight="400", anchor="start", tracking=0.0, italic=False):
    ital = ' font-style="italic"' if italic else ""
    return (
        f'<text x="{x:.3f}" y="{y:.3f}" fill="{fill}" font-family="{family}" '
        f'font-size="{size:.3f}" font-weight="{weight}" text-anchor="{anchor}" '
        f'letter-spacing="{tracking:.3f}"{ital}>{escape(value)}</text>'
    )


def svg_wrap(body: str, title: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n'
        f"<title>{escape(title)}</title>\n{body}\n</svg>\n"
    )


def logo_image(x, y, height):
    im = Image.open(LOGO).convert("RGBA")
    px = im.load()
    w, h = im.size
    for yy in range(h):
        for xx in range(w):
            r, g, b, a = px[xx, yy]
            if r > 245 and g > 245 and b > 245:
                px[xx, yy] = (255, 255, 255, 0)
            elif r > 230 and g > 230 and b > 230:
                px[xx, yy] = (r, g, b, min(a, int(max(0, (255 - r) * 8))))
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    buf = BytesIO()
    im.save(buf, format="PNG")
    width = height * (im.size[0] / im.size[1])
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return (
        f'<image x="{x:.3f}" y="{y:.3f}" width="{width:.3f}" height="{height:.3f}" '
        f'href="data:image/png;base64,{b64}"/>'
    )


def hang(x, y1, color, width=0.4):
    return (
        f'<line x1="{x:.2f}" y1="0" x2="{x:.2f}" y2="{y1:.2f}" '
        f'stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>'
    )


def star(cx, cy, r, color):
    pts = []
    for i in range(8):
        ang = math.radians(-90 + i * 45)
        rad = r if i % 2 == 0 else r * 0.38
        pts.append(f"{cx + rad * math.cos(ang):.2f},{cy + rad * math.sin(ang):.2f}")
    return f'<polygon points="{" ".join(pts)}" fill="{color}"/>'


def snowflake(cx, cy, r, color, stroke=0.7):
    parts = [f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r * 0.12:.2f}" fill="{color}"/>']
    for i in range(6):
        a = math.radians(i * 60)
        x2, y2 = cx + r * math.cos(a), cy + r * math.sin(a)
        parts.append(
            f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round"/>'
        )
        b1, b2 = a + math.radians(22), a - math.radians(22)
        mx, my = cx + r * 0.62 * math.cos(a), cy + r * 0.62 * math.sin(a)
        tlen = r * 0.28
        parts.append(
            f'<line x1="{mx + tlen * math.cos(b1):.2f}" y1="{my + tlen * math.sin(b1):.2f}" '
            f'x2="{mx:.2f}" y2="{my:.2f}" stroke="{color}" stroke-width="{stroke * 0.85}" stroke-linecap="round"/>'
        )
        parts.append(
            f'<line x1="{mx + tlen * math.cos(b2):.2f}" y1="{my + tlen * math.sin(b2):.2f}" '
            f'x2="{mx:.2f}" y2="{my:.2f}" stroke="{color}" stroke-width="{stroke * 0.85}" stroke-linecap="round"/>'
        )
        parts.append(f'<circle cx="{x2:.2f}" cy="{y2:.2f}" r="{r * 0.08:.2f}" fill="{color}"/>')
    return "".join(parts)


def bauble(cx, cy, r, ring, inner, kind="graph"):
    cap_h, cap_w = r * 0.28, r * 0.42
    cap_y = cy - r - cap_h + 0.4
    ring_el = (
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="none" stroke="{ring}" stroke-width="1.4"/>'
        f'<rect x="{cx - cap_w/2:.2f}" y="{cap_y:.2f}" width="{cap_w:.2f}" height="{cap_h:.2f}" rx="0.4" fill="{ring}"/>'
        f'<circle cx="{cx:.2f}" cy="{cap_y:.2f}" r="{cap_w * 0.22:.2f}" fill="none" stroke="{ring}" stroke-width="0.7"/>'
    )
    if kind == "graph":
        guts = snowflake(cx, cy, r * 0.58, inner, stroke=0.6)
    elif kind == "chip":
        s = r * 0.78
        guts = (
            f'<rect x="{cx - s/2:.2f}" y="{cy - s/2:.2f}" width="{s:.2f}" height="{s:.2f}" '
            f'rx="0.8" fill="none" stroke="{inner}" stroke-width="0.75"/>'
        )
        for i in range(3):
            yy = cy - s * 0.22 + i * s * 0.22
            guts += (
                f'<line x1="{cx - s*0.28:.2f}" y1="{yy:.2f}" x2="{cx + s*0.28:.2f}" y2="{yy:.2f}" '
                f'stroke="{inner}" stroke-width="0.6" stroke-linecap="round"/>'
            )
            guts += f'<rect x="{cx - s/2 - 0.95:.2f}" y="{yy - 0.45:.2f}" width="0.95" height="0.9" fill="{inner}"/>'
            guts += f'<rect x="{cx + s/2:.2f}" y="{yy - 0.45:.2f}" width="0.95" height="0.9" fill="{inner}"/>'
    else:
        guts = (
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r * 0.42:.2f}" fill="none" stroke="{inner}" stroke-width="1.15"/>'
            f'<path d="M {cx:.2f} {cy - r*0.42:.2f} A {r*0.42:.2f} {r*0.42:.2f} 0 0 1 {cx + r*0.36:.2f} {cy + r*0.22:.2f}" '
            f'fill="none" stroke="{inner}" stroke-width="2.2" stroke-linecap="round"/>'
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r * 0.09:.2f}" fill="{inner}"/>'
        )
    return ring_el + guts


def tree(cx, top, s, color):
    h1, h2, h3 = s * 0.42, s * 0.38, s * 0.34
    w1, w2, w3 = s * 0.92, s * 0.72, s * 0.52

    def tri(cx, y, w, h):
        return (
            f'<polygon points="{cx:.2f},{y:.2f} {cx + w/2:.2f},{y + h:.2f} {cx - w/2:.2f},{y + h:.2f}" fill="{color}"/>'
        )

    y = top
    parts = [tri(cx, y, w1, h1)]
    parts.append(tri(cx, y + h1 * 0.55, w2, h2))
    parts.append(tri(cx, y + h1 * 0.55 + h2 * 0.55, w3, h3))
    trunk_w, trunk_h = s * 0.12, s * 0.16
    ty = y + h1 * 0.55 + h2 * 0.55 + h3
    parts.append(
        f'<rect x="{cx - trunk_w/2:.2f}" y="{ty - 0.3:.2f}" width="{trunk_w:.2f}" height="{trunk_h:.2f}" fill="{color}"/>'
    )
    return "".join(parts)


def gift(cx, cy, s, box, ribbon):
    x, y, w, h = cx - s / 2, cy - s / 2, s, s * 0.92
    rw = s * 0.16
    return (
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="1.2" fill="{box}"/>'
        f'<rect x="{cx - rw/2:.2f}" y="{y:.2f}" width="{rw:.2f}" height="{h:.2f}" fill="{ribbon}"/>'
        f'<rect x="{x:.2f}" y="{cy - rw/2:.2f}" width="{w:.2f}" height="{rw:.2f}" fill="{ribbon}"/>'
        f'<circle cx="{cx - rw*0.9:.2f}" cy="{y:.2f}" r="{rw*0.55:.2f}" fill="{ribbon}"/>'
        f'<circle cx="{cx + rw*0.9:.2f}" cy="{y:.2f}" r="{rw*0.55:.2f}" fill="{ribbon}"/>'
    )


def node_cluster(cx, cy, s, colors):
    pts = [
        (cx, cy - s * 0.42),
        (cx - s * 0.4, cy + s * 0.28),
        (cx + s * 0.4, cy + s * 0.28),
    ]
    parts = []
    for i, (x1, y1) in enumerate(pts):
        for x2, y2 in pts[i + 1 :]:
            parts.append(
                f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                f'stroke="{NAVY}" stroke-width="0.75"/>'
            )
    for (x, y), c in zip(pts, colors):
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{s*0.16:.2f}" fill="{c}"/>')
    return "".join(parts)


def background():
    parts = [
        f'<defs>'
        f'<linearGradient id="wash" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{NAVY}" stop-opacity="0.11"/>'
        f'<stop offset="0.55" stop-color="{CYAN}" stop-opacity="0.05"/>'
        f'<stop offset="1" stop-color="{CREAM}" stop-opacity="0"/>'
        f'</linearGradient>'
        f'<radialGradient id="glow" cx="72%" cy="28%" r="55%">'
        f'<stop offset="0" stop-color="{LIME}" stop-opacity="0.10"/>'
        f'<stop offset="0.45" stop-color="{CYAN}" stop-opacity="0.06"/>'
        f'<stop offset="1" stop-color="{CREAM}" stop-opacity="0"/>'
        f'</radialGradient>'
        f'</defs>'
        f'<rect width="{W}" height="{H}" fill="{CREAM}"/>'
        f'<rect width="{W}" height="{H}" fill="url(#wash)"/>'
        f'<rect width="{W}" height="{H}" fill="url(#glow)"/>'
    ]

    # dashboard grid — readable, not a notebook
    parts.append(f'<g stroke="{NAVY}" fill="none">')
    step = 8.0
    for i, x in enumerate([i * step for i in range(0, 20)]):
        op = 0.16 if i % 4 == 0 else 0.09
        sw = 0.38 if i % 4 == 0 else 0.22
        parts.append(f'<line x1="{x:.2f}" y1="0" x2="{x:.2f}" y2="{H}" stroke-width="{sw}" opacity="{op}"/>')
    for i, y in enumerate([i * step for i in range(0, 28)]):
        op = 0.16 if i % 4 == 0 else 0.09
        sw = 0.38 if i % 4 == 0 else 0.22
        parts.append(f'<line x1="0" y1="{y:.2f}" x2="{W}" y2="{y:.2f}" stroke-width="{sw}" opacity="{op}"/>')
    parts.append("</g>")

    # radar / range rings from the hanging corner
    parts.append(f'<g fill="none" stroke="{CYAN}" stroke-width="0.45">')
    for r, op in ((36, 0.16), (58, 0.13), (84, 0.11), (112, 0.09)):
        parts.append(f'<circle cx="148" cy="-2" r="{r}" opacity="{op}"/>')
    parts.append("</g>")

    # data streams
    parts.append(
        f'<path d="M -6 36 C 28 58, 52 18, 84 42 S 124 64, 154 28" fill="none" '
        f'stroke="{CYAN}" stroke-width="0.7" opacity="0.22"/>'
    )
    parts.append(
        f'<path d="M -6 92 C 34 70, 60 118, 96 96 S 128 78, 154 108" fill="none" '
        f'stroke="{NAVY}" stroke-width="0.55" opacity="0.16"/>'
    )
    parts.append(
        f'<path d="M 8 202 C 46 194, 88 206, 154 198" fill="none" '
        f'stroke="{LIME}" stroke-width="0.5" opacity="0.18"/>'
    )

    # constellation — a real graph in the field, not random dust
    nodes = [
        (18, 28, LIME),
        (32, 48, CYAN),
        (22, 72, NAVY),
        (44, 22, YELLOW),
        (40, 96, MAGENTA),
        (28, 118, CYAN),
        (58, 14, CYAN),
        (70, 54, NAVY),
        (88, 18, LIME),
        (102, 62, CYAN),
        (118, 14, YELLOW),
        (132, 48, MAGENTA),
        (142, 86, CYAN),
        (54, 132, LIME),
        (16, 132, NAVY),
        (128, 132, LIME),
        (8, 52, MAGENTA),
        (96, 132, CYAN),
        (140, 198, YELLOW),
        (80, 200, CYAN),
    ]
    edges = [
        (0, 1), (1, 2), (0, 3), (1, 4), (2, 4), (4, 5), (3, 6), (6, 8),
        (7, 8), (7, 9), (8, 10), (9, 11), (11, 12), (5, 13), (5, 14),
        (12, 15), (2, 16), (13, 17), (9, 7), (1, 7), (18, 19),
    ]
    parts.append("<g>")
    for a, b in edges:
        x1, y1, _ = nodes[a]
        x2, y2, _ = nodes[b]
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{NAVY}" stroke-width="0.5" opacity="0.28"/>'
        )
    for x, y, c in nodes:
        parts.append(f'<circle cx="{x}" cy="{y}" r="1.25" fill="{c}" opacity="0.80"/>')
        parts.append(f'<circle cx="{x}" cy="{y}" r="2.6" fill="none" stroke="{c}" stroke-width="0.35" opacity="0.40"/>')
    parts.append("</g>")

    # brand tesserae — quiet pixels of the logo
    rng = random.Random(2027)
    palette = [CYAN, LIME, MAGENTA, YELLOW, NAVY]
    parts.append("<g>")
    for _ in range(26):
        x, y = rng.uniform(6, W - 6), rng.uniform(6, 138)
        if 12 < x < 132 and 148 < y < 178:
            continue
        s = rng.choice((1.1, 1.4, 1.8))
        c = palette[rng.randrange(len(palette))]
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{s}" height="{s}" fill="{c}" opacity="0.40"/>')
    parts.append("</g>")
    return "".join(parts)


def front_svg() -> str:
    g = [background()]

    def cap(cy, r):
        return cy - r - r * 0.28 + 0.4

    # hanging cluster — navy as the body, lime/magenta/yellow as the holiday accent
    pieces = [
        (52, cap(42, 9.4), NAVY, lambda: bauble(52, 42, 9.4, NAVY, LIME, "graph")),
        (74, 18.0, LIME, lambda: tree(74, 18, 17.5, LIME)),
        (96, 42 - 14.2 / 2, NAVY, lambda: gift(96, 42, 14.2, NAVY, YELLOW)),
        (118, 26 - 8.6, MAGENTA, lambda: snowflake(118, 26, 8.6, MAGENTA, 0.85)),
        (136, 20.0, CYAN, lambda: tree(136, 20, 14.5, CYAN)),
        (62, cap(96, 8.6), CYAN, lambda: bauble(62, 96, 8.6, CYAN, MAGENTA, "gauge")),
        (84, 68.0, NAVY, lambda: tree(84, 68, 15.5, NAVY)),
        (108, 100 - 12.8 / 2, MAGENTA, lambda: gift(108, 100, 12.8, MAGENTA, YELLOW)),
        (130, cap(78, 7.8), NAVY, lambda: bauble(130, 78, 7.8, NAVY, LIME, "chip")),
    ]
    for x, hang_y, c, draw in pieces:
        g.append(hang(x, hang_y, c, 0.42))
        g.append(draw())

    # lower pieces sit in the field — no strings through the greeting
    g.append(node_cluster(44, 108, 11, (LIME, CYAN, MAGENTA)))
    g.append(snowflake(90, 118, 6.6, CYAN, 0.7))
    g.append(snowflake(72, 128, 5.4, LIME, 0.6))

    sparks = [
        (40, 32, 2.2, YELLOW),
        (66, 22, 1.7, LIME),
        (88, 48, 1.6, MAGENTA),
        (110, 18, 2.0, YELLOW),
        (142, 44, 1.8, LIME),
        (56, 68, 1.5, CYAN),
        (78, 58, 1.4, YELLOW),
        (122, 56, 1.7, CYAN),
        (140, 100, 1.6, MAGENTA),
        (38, 88, 1.5, LIME),
        (50, 128, 1.8, YELLOW),
        (102, 128, 1.4, LIME),
        (128, 122, 1.5, YELLOW),
        (28, 44, 1.2, MAGENTA),
        (20, 100, 1.3, CYAN),
        (148 - 10, 132, 1.4, LIME),
        (98, 78, 1.3, YELLOW),
        (70, 110, 1.2, MAGENTA),
    ]
    for x, y, r, c in sparks:
        g.append(star(x, y, r, c))

    # greeting sits in the composition, like the reference — not on a blank bottom
    g.append(t(16, 164, "С", 30, MAGENTA, "Noto Serif Display", "700", "start", -0.8, italic=True))
    g.append(t(38, 162, "Новым годом!", 12.2, NAVY, "Noto Serif Display", "700", "start", -0.12, italic=True))
    g.append(t(38, 172.4, "ясных данных и спокойных релизов", 4.5, CYAN, "Inter", "500", "start", 0.38))

    g.append(logo_image(12, 192, 9.4))
    return svg_wrap("\n".join(g), "Lasmart — открытка 2027, лицевая")


FONT_FOR = {
    ("Noto Serif Display", "700"): FONTS["serif"],
    ("Noto Serif Display", "400"): FONTS["serif_it"],
    ("Inter", "500"): FONTS["medium"],
    ("Inter", "400"): FONTS["regular"],
    ("Inter", "700"): "/usr/share/fonts/truetype/macos/Inter-Bold.ttf",
}


def outline_text(source: Path, target: Path) -> None:
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree = ET.parse(source)
    root = tree.getroot()
    ns = "{http://www.w3.org/2000/svg}"
    cache = {}

    def font(family, weight):
        key = (family, weight)
        path = FONT_FOR.get(key) or FONT_FOR.get((family, "400")) or FONTS["regular"]
        if path not in cache:
            cache[path] = TTFont(path)
        return cache[path]

    for parent in root.iter():
        for index, node in list(enumerate(list(parent))):
            if node.tag != ns + "text":
                continue
            value = "".join(node.itertext())
            size = float(node.attrib.get("font-size", "16"))
            family = node.attrib.get("font-family", "Inter")
            weight = node.attrib.get("font-weight", "400")
            ft = font(family, weight)
            glyph_set = ft.getGlyphSet()
            cmap = ft.getBestCmap()
            hmtx = ft["hmtx"]
            upem = ft["head"].unitsPerEm
            scale = size / upem
            spacing = float(node.attrib.get("letter-spacing", "0"))
            glyphs, total = [], 0.0
            for position, char in enumerate(value):
                glyph_name = cmap.get(ord(char), ".notdef")
                advance, _ = hmtx[glyph_name]
                glyphs.append((glyph_name, total))
                total += advance * scale
                if position < len(value) - 1:
                    total += spacing
            x = float(node.attrib.get("x", "0"))
            y = float(node.attrib.get("y", "0"))
            anchor = node.attrib.get("text-anchor", "start")
            if anchor == "middle":
                x -= total / 2
            elif anchor == "end":
                x -= total
            group = ET.Element(
                ns + "g",
                {
                    "fill": node.attrib.get("fill", "#000"),
                    "transform": f"translate({x:.4f} {y:.4f}) scale({scale:.8f} {-scale:.8f})",
                    "aria-label": value,
                },
            )
            for glyph_name, offset in glyphs:
                pen = SVGPathPen(glyph_set)
                glyph_set[glyph_name].draw(pen)
                commands = pen.getCommands()
                if commands:
                    ET.SubElement(
                        group,
                        ns + "path",
                        {"d": commands, "transform": f"translate({offset / scale:.4f} 0)"},
                    )
            parent.remove(node)
            parent.insert(index, group)
    tree.write(target, encoding="utf-8", xml_declaration=True)


def export():
    front = ROOT / "lasmart-2027-front.svg"
    front_print = ROOT / "lasmart-2027-front-print.svg"
    front.write_text(front_svg(), encoding="utf-8")
    outline_text(front, front_print)

    front_png = ROOT / "lasmart-2027-front.png"
    cairosvg.svg2png(url=str(front_print), write_to=str(front_png), output_width=1748, output_height=2480)
    front_pdf = ROOT / "lasmart-2027-front.pdf"
    cairosvg.svg2pdf(url=str(front_print), write_to=str(front_pdf))

    # keep hanging copies in sync
    HANGING.mkdir(exist_ok=True)
    for src in (front, front_print, front_png, front_pdf):
        shutil.copy2(src, HANGING / src.name)

    artifacts = Path("/opt/cursor/artifacts")
    artifacts.mkdir(parents=True, exist_ok=True)
    preview = ROOT / "lasmart-2027-front-preview.png"
    Image.open(front_png).resize((874, 1240), Image.Resampling.LANCZOS).save(preview, "PNG")
    for src in (front_png, front_pdf, front_print, preview):
        shutil.copy2(src, artifacts / src.name)
    print("front", front_png, Image.open(front_png).size)


if __name__ == "__main__":
    export()

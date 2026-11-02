#!/usr/bin/env python3
"""Lasmart NY 2027 card: hanging IT ornaments, navy + cyan, subtle ground."""

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
LOGO = ROOT / "lasmart-logo.png"

NAVY = "#2C2864"
CYAN = "#2A8FCD"
CREAM = "#F6F3EB"
WHITE = "#FFFFFF"

# Portrait card — hanging composition like the reference panel
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
SERIF_IT = Metrics(FONTS["serif_it"])
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
    raw = buf.getvalue()
    width = height * (im.size[0] / im.size[1])
    b64 = base64.b64encode(raw).decode("ascii")
    return (
        f'<image x="{x:.3f}" y="{y:.3f}" width="{width:.3f}" height="{height:.3f}" '
        f'href="data:image/png;base64,{b64}"/>'
    )


def hang(x, y1, color, width=0.35):
    return f'<line x1="{x:.2f}" y1="0" x2="{x:.2f}" y2="{y1:.2f}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>'


def star(cx, cy, r, color):
    # 4-point spark, like a UI marker
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
        # side ticks — reads as both snowflake and a 6-node graph
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
        parts.append(
            f'<circle cx="{x2:.2f}" cy="{y2:.2f}" r="{r * 0.08:.2f}" fill="{color}"/>'
        )
    return "".join(parts)


def bauble(cx, cy, r, color, kind="graph"):
    cap_h, cap_w = r * 0.28, r * 0.42
    cap_y = cy - r - cap_h + 0.4
    ring = (
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="none" stroke="{color}" stroke-width="1.35"/>'
        f'<rect x="{cx - cap_w/2:.2f}" y="{cap_y:.2f}" width="{cap_w:.2f}" height="{cap_h:.2f}" rx="0.4" fill="{color}"/>'
        f'<circle cx="{cx:.2f}" cy="{cap_y:.2f}" r="{cap_w * 0.22:.2f}" fill="none" stroke="{color}" stroke-width="0.7"/>'
    )
    if kind == "graph":
        inner = snowflake(cx, cy, r * 0.58, color, stroke=0.55)
    elif kind == "chip":
        s = r * 0.78
        inner = (
            f'<rect x="{cx - s/2:.2f}" y="{cy - s/2:.2f}" width="{s:.2f}" height="{s:.2f}" '
            f'rx="0.8" fill="none" stroke="{color}" stroke-width="0.7"/>'
        )
        for i in range(3):
            yy = cy - s * 0.22 + i * s * 0.22
            inner += (
                f'<line x1="{cx - s*0.28:.2f}" y1="{yy:.2f}" x2="{cx + s*0.28:.2f}" y2="{yy:.2f}" '
                f'stroke="{color}" stroke-width="0.55" stroke-linecap="round"/>'
            )
            # side pads
            inner += f'<rect x="{cx - s/2 - 0.9:.2f}" y="{yy - 0.45:.2f}" width="0.9" height="0.9" fill="{color}"/>'
            inner += f'<rect x="{cx + s/2:.2f}" y="{yy - 0.45:.2f}" width="0.9" height="0.9" fill="{color}"/>'
    else:  # gauge / ring chart
        inner = (
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r * 0.42:.2f}" fill="none" stroke="{color}" stroke-width="1.1"/>'
            f'<path d="M {cx:.2f} {cy - r*0.42:.2f} A {r*0.42:.2f} {r*0.42:.2f} 0 0 1 {cx + r*0.36:.2f} {cy + r*0.22:.2f}" '
            f'fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round"/>'
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r * 0.08:.2f}" fill="{color}"/>'
        )
    return ring + inner


def tree(cx, top, s, color):
    """Hierarchy chevrons — reads as a tree, built like a folder tree / organigram."""
    h1, h2, h3 = s * 0.42, s * 0.38, s * 0.34
    w1, w2, w3 = s * 0.92, s * 0.72, s * 0.52
    y = top

    def tri(cx, y, w, h):
        return (
            f'<polygon points="{cx:.2f},{y:.2f} {cx + w/2:.2f},{y + h:.2f} {cx - w/2:.2f},{y + h:.2f}" fill="{color}"/>'
        )

    parts = [tri(cx, y, w1, h1)]
    parts.append(tri(cx, y + h1 * 0.55, w2, h2))
    parts.append(tri(cx, y + h1 * 0.55 + h2 * 0.55, w3, h3))
    trunk_w, trunk_h = s * 0.12, s * 0.16
    ty = y + h1 * 0.55 + h2 * 0.55 + h3
    parts.append(
        f'<rect x="{cx - trunk_w/2:.2f}" y="{ty - 0.3:.2f}" width="{trunk_w:.2f}" height="{trunk_h:.2f}" fill="{color}"/>'
    )
    return "".join(parts)


def gift(cx, cy, s, color, filled=True):
    """Release package — rounded module with a plus-ribbon."""
    x, y, w, h = cx - s / 2, cy - s / 2, s, s * 0.92
    if filled:
        box = f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="1.2" fill="{color}"/>'
        rib = WHITE
    else:
        box = f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="1.2" fill="none" stroke="{color}" stroke-width="1.2"/>'
        rib = color
    rw = s * 0.16
    ribbon = (
        f'<rect x="{cx - rw/2:.2f}" y="{y:.2f}" width="{rw:.2f}" height="{h:.2f}" fill="{rib}"/>'
        f'<rect x="{x:.2f}" y="{cy - rw/2:.2f}" width="{w:.2f}" height="{rw:.2f}" fill="{rib}"/>'
    )
    # small bow
    bow = (
        f'<circle cx="{cx - rw*0.9:.2f}" cy="{y:.2f}" r="{rw*0.55:.2f}" fill="{rib}"/>'
        f'<circle cx="{cx + rw*0.9:.2f}" cy="{y:.2f}" r="{rw*0.55:.2f}" fill="{rib}"/>'
    )
    return box + ribbon + bow


def node_cluster(cx, cy, s, color):
    """Tiny graph of three nodes — data cluster ornament."""
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
                f'stroke="{color}" stroke-width="0.7"/>'
            )
    for x, y in pts:
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{s*0.16:.2f}" fill="{color}"/>')
    return "".join(parts)


def subtle_background():
    """Barely-there dashboard grid, traces and nodes — not a flat fill."""
    parts = [f'<rect width="{W}" height="{H}" fill="{CREAM}"/>']
    # faint grid
    parts.append('<g opacity="0.07" stroke="{}" stroke-width="0.22">'.format(NAVY))
    step = 7.4
    for x in [i * step for i in range(0, 22)]:
        parts.append(f'<line x1="{x:.2f}" y1="0" x2="{x:.2f}" y2="{H}"/>')
    for y in [i * step for i in range(0, 30)]:
        parts.append(f'<line x1="0" y1="{y:.2f}" x2="{W}" y2="{y:.2f}"/>')
    parts.append("</g>")
    # faint radar arcs, top-right
    parts.append('<g fill="none" stroke="{}" stroke-width="0.35" opacity="0.07">'.format(NAVY))
    for r in (40, 62, 86, 112):
        parts.append(f'<circle cx="148" cy="0" r="{r}"/>')
    parts.append("</g>")
    # faint data-stream polylines
    parts.append(
        f'<path d="M -4 168 C 30 150, 50 190, 80 172 S 130 155, 160 178" fill="none" '
        f'stroke="{CYAN}" stroke-width="0.6" opacity="0.08"/>'
    )
    parts.append(
        f'<path d="M -4 40 C 25 55, 48 22, 78 38 S 120 58, 160 30" fill="none" '
        f'stroke="{NAVY}" stroke-width="0.5" opacity="0.06"/>'
    )
    # seeded micro-nodes
    rng = random.Random(2027)
    parts.append("<g>")
    for _ in range(70):
        x, y = rng.uniform(4, W - 4), rng.uniform(4, H - 4)
        r = rng.choice((0.35, 0.45, 0.6))
        col = CYAN if rng.random() > 0.55 else NAVY
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{col}" opacity="0.10"/>')
    parts.append("</g>")
    return "".join(parts)


def front_svg() -> str:
    g = [subtle_background()]

    # --- hanging ornaments (right-weighted, like the reference) ---
    # (x, hang_end, color)
    def bauble_hang(cy, r):
        return cy - r - r * 0.28 + 0.4

    ornaments = [
        # x, hang_y, color, drawer
        (76, bauble_hang(40, 9.2), NAVY, lambda: bauble(76, 40, 9.2, NAVY, "graph")),
        (98, 20.0, CYAN, lambda: tree(98, 20, 16, CYAN)),
        (116, 40 - 13.5 / 2, NAVY, lambda: gift(116, 40, 13.5, NAVY, True)),
        (134, 28 - 8.2, CYAN, lambda: snowflake(134, 28, 8.2, CYAN, 0.8)),
        (84, bauble_hang(94, 8.4), CYAN, lambda: bauble(84, 94, 8.4, CYAN, "gauge")),
        (104, 72.0, NAVY, lambda: tree(104, 72, 15, NAVY)),
        (124, 102 - 12.2 / 2, CYAN, lambda: gift(124, 102, 12.2, CYAN, True)),
        (138, bauble_hang(78, 7.6), NAVY, lambda: bauble(138, 78, 7.6, NAVY, "chip")),
        (68, 108 - 10 * 0.42, NAVY, lambda: node_cluster(68, 108, 10, NAVY)),
        (99, 118 - 6.4, NAVY, lambda: snowflake(99, 118, 6.4, NAVY, 0.65)),
    ]
    for x, hang_y, c, draw in ornaments:
        g.append(hang(x, hang_y, c))
        g.append(draw())

    # stars / sparks
    stars = [
        (64, 34, 2.1, CYAN),
        (84, 58, 1.6, NAVY),
        (118, 26, 1.8, NAVY),
        (140, 48, 2.3, CYAN),
        (70, 72, 1.4, CYAN),
        (96, 48, 1.5, CYAN),
        (130, 92, 1.7, NAVY),
        (108, 102, 1.3, CYAN),
        (60, 118, 1.8, NAVY),
        (140, 118, 1.5, CYAN),
        (76, 132, 1.2, NAVY),
        (52, 88, 1.4, CYAN),
        (44, 40, 1.1, NAVY),
        (56, 54, 0.9, CYAN),
    ]
    for x, y, r, c in stars:
        g.append(star(x, y, r, c))
    # tiny dots like the reference
    rng = random.Random(7)
    for _ in range(18):
        x, y = rng.uniform(50, 144), rng.uniform(12, 140)
        c = CYAN if rng.random() > 0.5 else NAVY
        g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="0.55" fill="{c}" opacity="0.7"/>')

    # greeting — large italic С, then the line
    g.append(t(22, 168, "С", 28, CYAN, "Noto Serif Display", "700", "start", -0.8, italic=True))
    g.append(t(42, 166, "Новым годом!", 11.5, NAVY, "Noto Serif Display", "700", "start", -0.15, italic=True))
    g.append(t(42, 176, "ясных данных и спокойных релизов", 4.4, CYAN, "Inter", "500", "start", 0.35))

    g.append(logo_image(12, 192, 9.2))
    return svg_wrap("\n".join(g), "Lasmart — открытка 2027, лицевая")


def back_svg() -> str:
    g = [subtle_background()]
    # a few quiet hanging pieces
    g.append(hang(112, 22, CYAN, 0.3))
    g.append(hang(124, 18, NAVY, 0.3))
    g.append(hang(136, 26, CYAN, 0.3))
    g.append(snowflake(112, 30, 6, CYAN, 0.7))
    g.append(star(124, 22, 2.0, NAVY))
    g.append(bauble(136, 36, 6.5, NAVY, "graph"))
    g.append(star(100, 28, 1.4, CYAN))
    g.append(star(142, 52, 1.6, NAVY))

    g.append(t(W / 2, 88, "С новым годом", 10, NAVY, "Noto Serif Display", "700", "middle", 0.1, italic=True))
    lines = [
        "Спасибо, что доверяете нам",
        "данные, процессы и решения.",
        "",
        "Пусть в 2027 всё важное",
        "будет на виду.",
    ]
    y = 108
    for line in lines:
        if line:
            g.append(t(W / 2, y, line, 5.2, NAVY, "Inter", "400", "middle", 0.12))
        y += 8.2
    g.append(t(W / 2, 196, "lasmart.ru", 4.0, CYAN, "Inter", "500", "middle", 0.8))
    return svg_wrap("\n".join(g), "Lasmart — открытка 2027, оборот")


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
    back = ROOT / "lasmart-2027-back.svg"
    front_print = ROOT / "lasmart-2027-front-print.svg"
    back_print = ROOT / "lasmart-2027-back-print.svg"
    front.write_text(front_svg(), encoding="utf-8")
    back.write_text(back_svg(), encoding="utf-8")
    outline_text(front, front_print)
    outline_text(back, back_print)

    # ~300 dpi: 148mm → 1748 px, 210mm → 2480 px
    front_png = ROOT / "lasmart-2027-front.png"
    back_png = ROOT / "lasmart-2027-back.png"
    cairosvg.svg2png(url=str(front_print), write_to=str(front_png), output_width=1748, output_height=2480)
    cairosvg.svg2png(url=str(back_print), write_to=str(back_png), output_width=1748, output_height=2480)

    front_pdf = ROOT / "lasmart-2027-front.pdf"
    back_pdf = ROOT / "lasmart-2027-back.pdf"
    cairosvg.svg2pdf(url=str(front_print), write_to=str(front_pdf))
    cairosvg.svg2pdf(url=str(back_print), write_to=str(back_pdf))

    from pypdf import PdfWriter, PdfReader

    writer = PdfWriter()
    writer.append(PdfReader(str(front_pdf)))
    writer.append(PdfReader(str(back_pdf)))
    combined = ROOT / "lasmart-2027-otkrytka.pdf"
    with combined.open("wb") as f:
        writer.write(f)

    artifacts = Path("/opt/cursor/artifacts")
    artifacts.mkdir(parents=True, exist_ok=True)
    for src in (front_png, back_png, combined, front_print, back_print):
        shutil.copy2(src, artifacts / src.name)
    print("wrote", combined)


if __name__ == "__main__":
    export()

#!/usr/bin/env python3
"""Lasmart New Year 2027 client card — A5 landscape, front + back."""

from __future__ import annotations

import base64
import shutil
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


ROOT = Path("/workspace/lasmart-ny-2027")
LOGO = ROOT / "lasmart-logo.png"

# Brand, sampled from the logo
NAVY = "#2C2864"
NAVY_DEEP = "#211E4A"
LIME = "#80B828"
CYAN = "#2A8FCD"
YELLOW = "#F4C119"
MAGENTA = "#921F78"
CREAM = "#F3EFE4"
CREAM_SOFT = "#E8E2D4"
WHITE = "#FFFFFF"

W, H = 210.0, 148.0  # mm, A5 landscape

FONTS = {
    "regular": "/usr/share/fonts/truetype/macos/Inter-Regular.ttf",
    "medium": "/usr/share/fonts/truetype/macos/Inter-Medium.ttf",
    "semibold": "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf",
    "bold": "/usr/share/fonts/truetype/macos/Inter-Bold.ttf",
}
FAMILY = "Inter"


class Metrics:
    def __init__(self, path: str):
        self.tt = TTFont(path)
        self.glyph_set = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.hmtx = self.tt["hmtx"]
        self.upem = self.tt["head"].unitsPerEm
        self.ascent = self.tt["hhea"].ascent
        self.descent = self.tt["hhea"].descent

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        scale = size / self.upem
        total = 0.0
        for i, ch in enumerate(text):
            name = self.cmap.get(ord(ch), ".notdef")
            adv, _ = self.hmtx[name]
            total += adv * scale
            if i < len(text) - 1:
                total += tracking
        return total


BOLD = Metrics(FONTS["bold"])
MEDIUM = Metrics(FONTS["medium"])
SEMIBOLD = Metrics(FONTS["semibold"])
REGULAR = Metrics(FONTS["regular"])


def text_el(x, y, value, size, fill, weight="600", anchor="start", tracking=0.0):
    return (
        f'<text x="{x:.3f}" y="{y:.3f}" fill="{fill}" font-family="{FAMILY}" '
        f'font-size="{size:.3f}" font-weight="{weight}" text-anchor="{anchor}" '
        f'letter-spacing="{tracking:.3f}">{escape(value)}</text>'
    )


def svg_wrap(body: str, title: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n'
        f"<title>{escape(title)}</title>\n"
        f"{body}\n</svg>\n"
    )


def logo_png_transparent() -> bytes:
    from io import BytesIO
    from PIL import Image

    im = Image.open(LOGO).convert("RGBA")
    pixels = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r > 245 and g > 245 and b > 245:
                pixels[x, y] = (255, 255, 255, 0)
            elif r > 230 and g > 230 and b > 230:
                fade = int(max(0, (255 - r) * 8))
                pixels[x, y] = (r, g, b, min(a, fade))
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def logo_image(x, y, height):
    from PIL import Image
    from io import BytesIO

    raw = logo_png_transparent()
    im = Image.open(BytesIO(raw))
    width = height * (im.size[0] / im.size[1])
    b64 = base64.b64encode(raw).decode("ascii")
    return (
        f'<image x="{x:.3f}" y="{y:.3f}" width="{width:.3f}" height="{height:.3f}" '
        f'href="data:image/png;base64,{b64}"/>'
    )


def front_svg() -> str:
    # The card restates the logo: lime module + navy field + three tiles on top,
    # with the company name replaced by the year.
    year = "2027"
    year_size = 42.0
    year_track = -1.4
    year_w = BOLD.width(year, year_size, year_track)

    panel_h = 58.0
    panel_pad_x = 14.0
    panel_w = year_w + panel_pad_x * 2
    lime_w = 22.0
    overlap = 8.0
    radius = 10.0
    lime_rx = 7.0

    sq = 14.0
    sq_gap = 2.0
    mag_w = 32.0  # wide magenta tile, as in the logo
    tiles_w = sq + sq_gap + sq + sq_gap + mag_w

    lockup_w = lime_w - overlap + panel_w
    origin_x = (W - lockup_w) / 2
    panel_y = 48.0
    lime_x = origin_x
    panel_x = lime_x + lime_w - overlap

    year_x = panel_x + (panel_w - year_w) / 2
    year_baseline = panel_y + panel_h * 0.69

    tiles_x = panel_x + panel_w - tiles_w
    tiles_y = panel_y - sq

    caption = "всё важное — на виду"
    cap_size = 5.0
    cap_track = 1.45
    cap_w = MEDIUM.width(caption, cap_size, cap_track)
    cap_x = (W - cap_w) / 2
    cap_y = panel_y + panel_h + 16.0

    logo_h = 10.5
    logo_x = 18.0
    logo_y = H - 15.0 - logo_h

    # Lime module: rounded on the left only, straight edge under the navy bar
    lime_path = (
        f"M {lime_x + lime_rx:.3f} {panel_y:.3f} "
        f"H {panel_x + radius:.3f} "
        f"V {panel_y + panel_h:.3f} "
        f"H {lime_x + lime_rx:.3f} "
        f"A {lime_rx:.3f} {lime_rx:.3f} 0 0 1 {lime_x:.3f} {panel_y + panel_h - lime_rx:.3f} "
        f"V {panel_y + lime_rx:.3f} "
        f"A {lime_rx:.3f} {lime_rx:.3f} 0 0 1 {lime_x + lime_rx:.3f} {panel_y:.3f} Z"
    )

    body = [
        f'<rect width="{W}" height="{H}" fill="{CREAM}"/>',
        f'<path d="{lime_path}" fill="{LIME}"/>',
        # Navy field: rounded on the right only, so it meets the lime module cleanly
        f'<path d="'
        f'M {panel_x:.3f} {panel_y:.3f} '
        f'H {panel_x + panel_w - radius:.3f} '
        f'A {radius:.3f} {radius:.3f} 0 0 1 {panel_x + panel_w:.3f} {panel_y + radius:.3f} '
        f'V {panel_y + panel_h - radius:.3f} '
        f'A {radius:.3f} {radius:.3f} 0 0 1 {panel_x + panel_w - radius:.3f} {panel_y + panel_h:.3f} '
        f'H {panel_x:.3f} Z" fill="{NAVY}"/>',
        f'<rect x="{tiles_x:.3f}" y="{tiles_y:.3f}" width="{sq:.3f}" height="{sq:.3f}" fill="{CYAN}"/>',
        f'<rect x="{tiles_x + sq + sq_gap:.3f}" y="{tiles_y:.3f}" width="{sq:.3f}" height="{sq:.3f}" fill="{YELLOW}"/>',
        f'<rect x="{tiles_x + sq + sq_gap + sq + sq_gap:.3f}" y="{tiles_y:.3f}" width="{mag_w:.3f}" height="{sq:.3f}" fill="{MAGENTA}"/>',
        text_el(year_x, year_baseline, year, year_size, WHITE, "700", "start", year_track),
        text_el(cap_x, cap_y, caption, cap_size, NAVY, "500", "start", cap_track),
        logo_image(logo_x, logo_y, logo_h),
    ]
    return svg_wrap("\n".join(body), "Lasmart — открытка 2027, лицевая")


def back_svg() -> str:
    lines = [
        "Спасибо, что доверяете нам",
        "данные, процессы и решения.",
        "",
        "Пусть в новом году всё важное",
        "будет на виду.",
    ]
    size = 6.2
    leading = 9.2
    block_h = leading * len(lines)
    start_y = (H - block_h) / 2 + 6

    sq = 7.0
    gap = 1.6
    tiles_w = sq * 3 + gap * 2
    tiles_x = (W - tiles_w) / 2
    tiles_y = 24.0

    grain = (
        "<defs>"
        '<filter id="night" x="-5%" y="-5%" width="110%" height="110%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" result="n"/>'
        '<feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.10 0" in="n"/>'
        "</filter>"
        "</defs>"
    )

    parts = [
        grain,
        f'<rect width="{W}" height="{H}" fill="{NAVY_DEEP}"/>',
        f'<rect width="{W}" height="{H}" filter="url(#night)" opacity="0.4"/>',
    ]
    for i, color in enumerate([CYAN, YELLOW, MAGENTA]):
        x = tiles_x + i * (sq + gap)
        parts.append(
            f'<rect x="{x:.3f}" y="{tiles_y:.3f}" width="{sq:.3f}" height="{sq:.3f}" fill="{color}"/>'
        )

    parts.append(
        text_el(W / 2, tiles_y + sq + 14, "С новым годом", 8.0, WHITE, "600", "middle", 0.4)
    )

    y = start_y + 10
    for line in lines:
        if line:
            parts.append(text_el(W / 2, y, line, size, CREAM, "400", "middle", 0.15))
        y += leading

    parts.append(text_el(W / 2, H - 20, "lasmart.ru", 4.0, LIME, "500", "middle", 0.9))
    return svg_wrap("\n".join(parts), "Lasmart — открытка 2027, оборот")


WEIGHT_FONT = {
    "400": FONTS["regular"],
    "500": FONTS["medium"],
    "600": FONTS["semibold"],
    "700": FONTS["bold"],
}


def outline_text(source: Path, target: Path) -> None:
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree = ET.parse(source)
    root = tree.getroot()
    ns = "{http://www.w3.org/2000/svg}"
    fonts = {w: TTFont(path) for w, path in WEIGHT_FONT.items()}

    for parent in root.iter():
        for index, node in list(enumerate(list(parent))):
            if node.tag != ns + "text":
                continue
            value = "".join(node.itertext())
            size = float(node.attrib.get("font-size", "16"))
            weight = node.attrib.get("font-weight", "400")
            font = fonts.get(weight, fonts["400"])
            glyph_set = font.getGlyphSet()
            cmap = font.getBestCmap()
            hmtx = font["hmtx"]
            upem = font["head"].unitsPerEm
            scale = size / upem
            spacing = float(node.attrib.get("letter-spacing", "0"))
            glyphs = []
            total = 0.0
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
                    "fill": node.attrib.get("fill", "#000000"),
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

    front_png = ROOT / "lasmart-2027-front.png"
    back_png = ROOT / "lasmart-2027-back.png"
    # ~300 dpi
    cairosvg.svg2png(url=str(front_print), write_to=str(front_png), output_width=2480, output_height=1748)
    cairosvg.svg2png(url=str(back_print), write_to=str(back_png), output_width=2480, output_height=1748)

    front_pdf = ROOT / "lasmart-2027-front.pdf"
    back_pdf = ROOT / "lasmart-2027-back.pdf"
    cairosvg.svg2pdf(url=str(front_print), write_to=str(front_pdf))
    cairosvg.svg2pdf(url=str(back_print), write_to=str(back_pdf))

    # Combined 2-page PDF
    try:
        from pypdf import PdfWriter, PdfReader
        writer = PdfWriter()
        for p in (front_pdf, back_pdf):
            writer.append(PdfReader(str(p)))
        combined = ROOT / "lasmart-2027-otkrytka.pdf"
        with combined.open("wb") as f:
            writer.write(f)
    except Exception:
        import subprocess
        combined = ROOT / "lasmart-2027-otkrytka.pdf"
        subprocess.check_call(["pdfunite", str(front_pdf), str(back_pdf), str(combined)])

    artifacts = Path("/opt/cursor/artifacts")
    artifacts.mkdir(parents=True, exist_ok=True)
    for src in (front_png, back_png, combined, front_print, back_print, front, back):
        shutil.copy2(src, artifacts / src.name)
    print("wrote", combined)


if __name__ == "__main__":
    export()

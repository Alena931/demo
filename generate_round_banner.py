#!/usr/bin/env python3
"""Chosen round banner: olive/gold, max phone in the green field, print SVG+PDF."""

from __future__ import annotations

from html import escape
from pathlib import Path
import math
import shutil
import xml.etree.ElementTree as ET

import cairosvg
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image


SIZE = 700
CX = CY = SIZE / 2
GOLD_SW = 11
GOLD_R = 339
GOLD_INNER = GOLD_R - GOLD_SW / 2
GOLD_OUTER = GOLD_R + GOLD_SW / 2
SAFE_R = GOLD_INNER - 8
SPLIT = 486.0

CREAM = "#F3F0E7"
INK = "#26372F"
GOLD = "#B18B4B"
GOLD_SOFT = "#C7A365"

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_FAMILY = "DejaVu Sans"

TEXT = {
    "label": "РЕМОНТ • ОТДЕЛКА • КОНТРОЛЬ",
    "title": "РЕМОНТ КВАРТИР",
    "turnkey": "ПОД КЛЮЧ",
    "line1": "ПО ДОГОВОРУ • ГАРАНТИЯ",
    "line2": "ПОЭТАПНАЯ ОПЛАТА • ТЕХНАДЗОР",
    "name": "РОМАН",
    "phone": "+7 988 525 29 15",
}

ROOT = Path("/workspace")
VARIANT_DIR = ROOT / "banner-variants"


class FontMetrics:
    def __init__(self, path: str):
        self.tt = TTFont(path)
        self.glyph_set = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.hmtx = self.tt["hmtx"]
        self.upem = self.tt["head"].unitsPerEm
        hhea = self.tt["hhea"]
        self.ascent = hhea.ascent
        self.descent = hhea.descent

    def width(self, value: str, size: float, tracking: float = 0.0) -> float:
        scale = size / self.upem
        total = 0.0
        for i, char in enumerate(value):
            name = self.cmap.get(ord(char), ".notdef")
            advance, _ = self.hmtx[name]
            total += advance * scale
            if i < len(value) - 1:
                total += tracking
        return total

    def height(self, size: float) -> tuple[float, float, float]:
        scale = size / self.upem
        asc = self.ascent * scale
        desc = -self.descent * scale
        return asc, desc, asc + desc

    def ink_bbox(
        self,
        value: str,
        size: float,
        tracking: float,
        x: float,
        baseline: float,
        anchor: str = "start",
    ) -> tuple[float, float, float, float]:
        scale = size / self.upem
        w = self.width(value, size, tracking)
        if anchor == "middle":
            origin = x - w / 2
        elif anchor == "end":
            origin = x - w
        else:
            origin = x
        min_x = min_y = 1e9
        max_x = max_y = -1e9
        cursor = 0.0
        found = False
        for i, char in enumerate(value):
            name = self.cmap.get(ord(char), ".notdef")
            pen = BoundsPen(self.glyph_set)
            self.glyph_set[name].draw(pen)
            if pen.bounds is not None:
                gx0, gy0, gx1, gy1 = pen.bounds
                min_x = min(min_x, origin + cursor + gx0 * scale)
                max_x = max(max_x, origin + cursor + gx1 * scale)
                min_y = min(min_y, baseline - gy1 * scale)
                max_y = max(max_y, baseline - gy0 * scale)
                found = True
            advance, _ = self.hmtx[name]
            cursor += advance * scale
            if i < len(value) - 1:
                cursor += tracking
        if not found:
            asc, desc, _ = self.height(size)
            return origin, baseline - asc, origin + w, baseline + desc
        return min_x, min_y, max_x, max_y


FONT = FontMetrics(FONT_PATH)


def chord_half(y: float, radius: float = SAFE_R) -> float:
    dy = abs(y - CY)
    inner = radius * radius - dy * dy
    if inner <= 0:
        return 0.0
    return math.sqrt(inner)


def rect_inside_circle(x0, y0, x1, y1, radius=SAFE_R, cx=CX, cy=CY) -> bool:
    for x in (x0, x1):
        for y in (y0, y1):
            if (x - cx) ** 2 + (y - cy) ** 2 > radius * radius + 0.05:
                return False
    return True


def boxes_overlap(a, b, gap: float = 0.0) -> bool:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return not (
        ax1 + gap <= bx0
        or bx1 + gap <= ax0
        or ay1 + gap <= by0
        or by1 + gap <= ay0
    )


def fit_size(value: str, max_width: float, size: float, tracking: float) -> tuple[float, float]:
    while size > 8 and FONT.width(value, size, tracking) > max_width:
        size -= 0.25
        tracking *= 0.995
    return size, tracking


def text_el(x, y, value, size, fill, anchor="start", spacing=0):
    return (
        f'<text x="{x:.3f}" y="{y:.3f}" fill="{fill}" '
        f'font-family="{FONT_FAMILY}" font-size="{size:.3f}" font-weight="700" '
        f'text-anchor="{anchor}" letter-spacing="{spacing:.3f}">{escape(value)}</text>'
    )


def layout():
    top_limit = CY - SAFE_R + 22
    cream_bottom = SPLIT - 22

    label_size, label_track = 13.0, 1.7
    title_size, title_track = 42.0, -1.0
    hero_size, hero_track = 76.0, -2.4
    line1_size, line1_track = 17.0, 0.4
    line2_size, line2_track = 15.0, 0.35
    rule_h = 3.5

    label_h = FONT.height(label_size)[2]
    title_h = FONT.height(title_size)[2]
    hero_h = FONT.height(hero_size)[2]
    line1_h = FONT.height(line1_size)[2]
    line2_h = FONT.height(line2_size)[2]
    gaps = (18, 16, 22, 22, 16)
    block_h = label_h + title_h + hero_h + rule_h + line1_h + line2_h + sum(gaps)
    start = top_limit + max(0, (cream_bottom - top_limit - block_h) / 2)

    def place_line(y_top, size, track, value):
        asc, desc, h = FONT.height(size)
        baseline = y_top + asc
        half = min(chord_half(y_top), chord_half(y_top + h)) - 8
        size, track = fit_size(value, max(40, 2 * half), size, track)
        asc, desc, h = FONT.height(size)
        baseline = y_top + asc
        box = FONT.ink_bbox(value, size, track, CX, baseline, "middle")
        if not rect_inside_circle(*box):
            while size > 8 and not rect_inside_circle(
                *FONT.ink_bbox(
                    value, size, track, CX, y_top + FONT.height(size)[0], "middle"
                )
            ):
                size -= 0.25
            asc, desc, h = FONT.height(size)
            baseline = y_top + asc
            box = FONT.ink_bbox(value, size, track, CX, baseline, "middle")
        return {
            "value": value,
            "size": size,
            "track": track,
            "baseline": baseline,
            "box": box,
            "y_bottom": box[3],
        }

    y = start
    label = place_line(y, label_size, label_track, TEXT["label"])
    y = label["y_bottom"] + gaps[0]
    title = place_line(y, title_size, title_track, TEXT["title"])
    y = title["y_bottom"] + gaps[1]
    hero = place_line(y, hero_size, hero_track, TEXT["turnkey"])
    y = hero["y_bottom"] + gaps[2]

    rule_w = min(hero["box"][2] - hero["box"][0], 2 * chord_half(y + rule_h / 2) - 36, 390)
    rule = {
        "x": CX - rule_w / 2,
        "y": y,
        "w": rule_w,
        "h": rule_h,
        "box": (CX - rule_w / 2, y, CX + rule_w / 2, y + rule_h),
    }
    y = rule["box"][3] + gaps[3]
    line1 = place_line(y, line1_size, line1_track, TEXT["line1"])
    y = line1["y_bottom"] + gaps[4]
    line2 = place_line(y, line2_size, line2_track, TEXT["line2"])

    if line2["box"][3] > cream_bottom:
        raise RuntimeError(f"Cream stack overflows split: {line2['box'][3]:.1f} > {cream_bottom:.1f}")

    name_size, name_track = 16.0, 3.2
    div_w, div_gap = 2.5, 14.0
    phone_track = -1.5
    name_w = FONT.width(TEXT["name"], name_size, name_track)
    green_top = SPLIT + 16
    green_bottom = CY + SAFE_R - 14

    def contact_at(phone_size: float):
        phone_w = FONT.width(TEXT["phone"], phone_size, phone_track)
        total_w = name_w + div_gap + div_w + div_gap + phone_w
        probe = FONT.ink_bbox(TEXT["phone"], phone_size, phone_track, 0, 0)
        phone_ink_h = probe[3] - probe[1]
        name_probe = FONT.ink_bbox(TEXT["name"], name_size, name_track, 0, 0)
        name_ink_h = name_probe[3] - name_probe[1]
        group_h = max(phone_ink_h, name_ink_h)
        top = green_top
        bottom = top + group_h
        if bottom > green_bottom:
            return None
        x0 = CX - total_w / 2
        group_box = (x0, top, x0 + total_w, bottom)
        phone_baseline = top + (-probe[1])
        name_center = top + group_h / 2
        name_baseline = name_center - (name_probe[1] + name_probe[3]) / 2
        name_x = x0
        div_x = name_x + name_w + div_gap
        phone_x = div_x + div_w + div_gap
        div_h = phone_ink_h * 0.72
        div_top = top + (group_h - div_h) / 2
        name_box = FONT.ink_bbox(TEXT["name"], name_size, name_track, name_x, name_baseline)
        phone_box = FONT.ink_bbox(
            TEXT["phone"], phone_size, phone_track, phone_x, phone_baseline
        )
        div_box = (div_x, div_top, div_x + div_w, div_top + div_h)
        if boxes_overlap(name_box, div_box, gap=6) or boxes_overlap(div_box, phone_box, gap=6):
            return None
        if boxes_overlap(name_box, phone_box, gap=8):
            return None
        for box in (name_box, phone_box, div_box):
            if not rect_inside_circle(*box):
                return None
        return {
            "phone_size": phone_size,
            "phone_track": phone_track,
            "phone_x": phone_x,
            "phone_baseline": phone_baseline,
            "phone_box": phone_box,
            "name_size": name_size,
            "name_track": name_track,
            "name_x": name_x,
            "name_baseline": name_baseline,
            "name_box": name_box,
            "div": div_box,
            "group": group_box,
        }

    lo, hi = 28.0, 84.0
    best = None
    for _ in range(28):
        mid = (lo + hi) / 2
        cand = contact_at(mid)
        if cand:
            best = cand
            lo = mid
        else:
            hi = mid
    if best is None:
        raise RuntimeError("Could not fit contact row inside the green field")

    cream = [label, title, hero, line1, line2]
    for i, a in enumerate(cream):
        for b in cream[i + 1 :]:
            if boxes_overlap(a["box"], b["box"], gap=8):
                raise RuntimeError("Cream texts overlap")
        if boxes_overlap(a["box"], rule["box"], gap=8):
            raise RuntimeError("Cream text overlaps rule")
        if a["box"][3] > SPLIT - 8:
            raise RuntimeError("Cream text collides with green split")

    if best["group"][1] < SPLIT + 8:
        raise RuntimeError("Contact row collides with split")

    return {
        "label": label,
        "title": title,
        "hero": hero,
        "rule": rule,
        "line1": line1,
        "line2": line2,
        "contact": best,
        "split": SPLIT,
    }


def green_cap_path(split: float, radius: float = SIZE / 2) -> str:
    half = math.sqrt(max(0.0, radius * radius - (split - CY) ** 2))
    x0, x1 = CX - half, CX + half
    return (
        f"M {x0:.3f} {split:.3f} "
        f"A {radius:.3f} {radius:.3f} 0 0 0 {x1:.3f} {split:.3f} Z"
    )


def build_svg(lay) -> str:
    c = lay["contact"]
    dx0, dy0, dx1, dy1 = c["div"]
    body = [
        '<defs><clipPath id="circle-cut">'
        f'<circle cx="{CX}" cy="{CY}" r="{SIZE/2}"/>'
        "</clipPath></defs>",
        '<g clip-path="url(#circle-cut)">',
        f'<circle cx="{CX}" cy="{CY}" r="{SIZE/2}" fill="{CREAM}"/>',
        f'<path d="{green_cap_path(lay["split"])}" fill="{INK}"/>',
        f'<circle cx="{CX}" cy="{CY}" r="{GOLD_R}" fill="none" '
        f'stroke="{GOLD}" stroke-width="{GOLD_SW}"/>',
        text_el(
            CX, lay["label"]["baseline"], lay["label"]["value"],
            lay["label"]["size"], INK, "middle", lay["label"]["track"],
        ),
        text_el(
            CX, lay["title"]["baseline"], lay["title"]["value"],
            lay["title"]["size"], INK, "middle", lay["title"]["track"],
        ),
        text_el(
            CX, lay["hero"]["baseline"], lay["hero"]["value"],
            lay["hero"]["size"], INK, "middle", lay["hero"]["track"],
        ),
        f'<rect x="{lay["rule"]["x"]:.3f}" y="{lay["rule"]["y"]:.3f}" '
        f'width="{lay["rule"]["w"]:.3f}" height="{lay["rule"]["h"]:.3f}" fill="{GOLD}"/>',
        text_el(
            CX, lay["line1"]["baseline"], lay["line1"]["value"],
            lay["line1"]["size"], INK, "middle", lay["line1"]["track"],
        ),
        text_el(
            CX, lay["line2"]["baseline"], lay["line2"]["value"],
            lay["line2"]["size"], INK, "middle", lay["line2"]["track"],
        ),
        text_el(
            c["name_x"], c["name_baseline"], TEXT["name"],
            c["name_size"], GOLD_SOFT, "start", c["name_track"],
        ),
        f'<rect x="{dx0:.3f}" y="{dy0:.3f}" width="{dx1-dx0:.3f}" '
        f'height="{dy1-dy0:.3f}" fill="{GOLD_SOFT}"/>',
        text_el(
            c["phone_x"], c["phone_baseline"], TEXT["phone"],
            c["phone_size"], CREAM, "start", c["phone_track"],
        ),
        "</g>",
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}mm" height="{SIZE}mm" '
        f'viewBox="0 0 {SIZE} {SIZE}">\n'
        "<title>Ремонт квартир под ключ — Роман</title>\n"
        "<desc>Круглый печатный баннер 700 × 700 мм. Телефон максимально крупный "
        "в нижнем зелёном поле. Все элементы внутри окружности.</desc>\n"
        + "\n".join(body)
        + "\n</svg>\n"
    )


def outline_text(source: Path, target: Path, font_path: str) -> None:
    font = TTFont(font_path)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upem = font["head"].unitsPerEm
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    tree = ET.parse(source)
    root = tree.getroot()
    ns = "{http://www.w3.org/2000/svg}"

    for parent in root.iter():
        for index, node in list(enumerate(list(parent))):
            if node.tag != ns + "text":
                continue
            value = "".join(node.itertext())
            size = float(node.attrib.get("font-size", "16"))
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
            if node.attrib.get("text-anchor") == "middle":
                x -= total / 2
            elif node.attrib.get("text-anchor") == "end":
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
                        {
                            "d": commands,
                            "transform": f"translate({offset / scale:.4f} 0)",
                        },
                    )
            parent.remove(node)
            parent.insert(index, group)
    tree.write(target, encoding="utf-8", xml_declaration=True)


def verify_preview(path: Path, lay) -> None:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    scale = w / SIZE
    px = img.load()
    outside = 0
    samples = 0
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r_out = w / 2 + 3
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy > r_out * r_out:
                samples += 1
                rch, gch, bch, _a = px[x, y]
                if rch < 250 or gch < 250 or bch < 250:
                    outside += 1
    if outside > 20:
        raise RuntimeError(f"Pixels leak outside the circle: {outside} of {samples}")

    phone_h = (lay["contact"]["phone_box"][3] - lay["contact"]["phone_box"][1]) * scale
    if lay["contact"]["phone_size"] < 40:
        raise RuntimeError(f"Phone too small: {lay['contact']['phone_size']:.1f}")
    gold_y = int((CY + GOLD_R) * scale)
    gold_hits = 0
    for x in range(w // 2 - 8, w // 2 + 8):
        rch, gch, bch, _a = px[x, gold_y]
        if rch > 140 and gch > 90 and bch < 120:
            gold_hits += 1
    if gold_hits < 4:
        raise RuntimeError("Gold ring missing at the bottom of the circle")
    print(
        f"verify ok: phone {lay['contact']['phone_size']:.2f} px, "
        f"raster height {phone_h:.0f}px, outside {outside}, gold-bottom {gold_hits}"
    )


def export(svg_text: str, lay) -> None:
    editable = ROOT / "banner-roman-700x700-editable.svg"
    printable = ROOT / "banner-roman-700x700-print.svg"
    pdf = ROOT / "banner-roman-700x700-print.pdf"
    preview = ROOT / "banner-roman-700x700-preview.png"
    editable.write_text(svg_text, encoding="utf-8")
    outline_text(editable, printable, FONT_PATH)
    cairosvg.svg2pdf(url=str(printable), write_to=str(pdf))
    cairosvg.svg2png(
        url=str(printable),
        write_to=str(preview),
        output_width=1400,
        output_height=1400,
        background_color="white",
    )
    verify_preview(preview, lay)

    VARIANT_DIR.mkdir(exist_ok=True)
    mapping = {
        editable: VARIANT_DIR / "variant-1-round-700x700-editable.svg",
        printable: VARIANT_DIR / "variant-1-round-700x700-print.svg",
        pdf: VARIANT_DIR / "variant-1-round-700x700-print.pdf",
        preview: VARIANT_DIR / "variant-1-round-700x700-preview.png",
    }
    for src, dst in mapping.items():
        shutil.copy2(src, dst)

    artifacts = Path("/opt/cursor/artifacts")
    artifacts.mkdir(parents=True, exist_ok=True)
    for src in (preview, pdf, printable, editable):
        shutil.copy2(src, artifacts / src.name)


def main():
    lay = layout()
    c = lay["contact"]
    print("split", lay["split"])
    print("phone_size", round(c["phone_size"], 2), "box", tuple(round(v, 1) for v in c["phone_box"]))
    print("name_box", tuple(round(v, 1) for v in c["name_box"]))
    print("div", tuple(round(v, 1) for v in c["div"]))
    print("hero", round(lay["hero"]["size"], 2), "title", round(lay["title"]["size"], 2))
    export(build_svg(lay), lay)


if __name__ == "__main__":
    main()

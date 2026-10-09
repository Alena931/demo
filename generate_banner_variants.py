from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw


OUT = Path("banner-variants")
OUT.mkdir(exist_ok=True)

TEXT = {
    "label": "\u0420\u0415\u041c\u041e\u041d\u0422 \u2022 \u041e\u0422\u0414\u0415\u041b\u041a\u0410 \u2022 \u041a\u041e\u041d\u0422\u0420\u041e\u041b\u042c",
    "remont": "\u0420\u0415\u041c\u041e\u041d\u0422",
    "kvartir": "\u041a\u0412\u0410\u0420\u0422\u0418\u0420",
    "remont_kvartir": "\u0420\u0415\u041c\u041e\u041d\u0422 \u041a\u0412\u0410\u0420\u0422\u0418\u0420",
    "turnkey": "\u041f\u041e\u0414 \u041a\u041b\u042e\u0427",
    "contract": "\u041f\u041e \u0414\u041e\u0413\u041e\u0412\u041e\u0420\u0423",
    "warranty": "\u0413\u0410\u0420\u0410\u041d\u0422\u0418\u042f",
    "stages": "\u041f\u041e\u042d\u0422\u0410\u041f\u041d\u0410\u042f \u041e\u041f\u041b\u0410\u0422\u0410",
    "supervision": "\u0422\u0415\u0425\u041d\u0410\u0414\u0417\u041e\u0420",
    "roman": "\u0420\u041e\u041c\u0410\u041d",
    "phone": "+7 988 525 29 15",
}

FONTS = {
    "v1": {
        "family": "DejaVu Sans",
        "file": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    },
    "v2": {
        "family": "JetBrains Mono ExtraBold",
        "file": "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf",
    },
    "v3": {
        "family": "DejaVu Serif",
        "file": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    },
}


def text(x, y, value, size, fill, family, anchor="start", spacing=0):
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" '
        f'font-family="{family}" font-size="{size}" font-weight="700" '
        f'text-anchor="{anchor}" letter-spacing="{spacing}">{escape(value)}</text>'
    )


def svg_document(body, title, round_format=False):
    clip_open = ""
    clip_close = ""
    if round_format:
        clip_open = (
            '<defs><clipPath id="round-cut"><circle cx="350" cy="350" r="350"/>'
            '</clipPath></defs><g clip-path="url(#round-cut)">'
        )
        clip_close = "</g>"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="700mm" height="700mm" '
        'viewBox="0 0 700 700">\n'
        f"<title>{escape(title)}</title>\n"
        f"{clip_open}{body}{clip_close}\n</svg>\n"
    )


def variant_1(round_format):
    family = FONTS["v1"]["family"]
    bg, ink, accent = "#F3F0E7", "#26372F", "#B18B4B"
    if not round_format:
        body = [
            f'<rect width="700" height="700" fill="{bg}"/>',
            f'<rect width="18" height="700" fill="{accent}"/>',
            f'<rect x="70" y="57" width="340" height="35" rx="17.5" fill="{ink}"/>',
            text(240, 80.5, TEXT["label"], 12.5, bg, family, "middle", 1.4),
            text(67, 176, TEXT["remont_kvartir"], 50, ink, family, spacing=-1.2),
            text(64, 278, TEXT["turnkey"], 86, ink, family, spacing=-3),
            f'<rect x="70" y="324" width="560" height="4" fill="{accent}"/>',
        ]
        for x, y, value, size in [
            (96, 383, TEXT["contract"], 21),
            (384, 383, TEXT["warranty"], 21),
            (96, 434, TEXT["stages"], 18.5),
            (384, 434, TEXT["supervision"], 21),
        ]:
            body.append(f'<circle cx="{x - 17}" cy="{y - 7}" r="5" fill="{accent}"/>')
            body.append(text(x, y, value, size, ink, family))
        body += [
            f'<rect x="18" y="491" width="682" height="209" fill="{ink}"/>',
            text(80, 608, TEXT["roman"], 18, "#C7A365", family, spacing=3),
            '<rect x="183" y="571" width="3" height="53" fill="#C7A365"/>',
            text(210, 615, TEXT["phone"], 39, bg, family, spacing=-1),
            '<rect x="70" y="660" width="72" height="4" fill="#C7A365"/>',
        ]
    else:
        body = [
            f'<rect width="700" height="700" fill="{bg}"/>',
            f'<circle cx="350" cy="350" r="337" fill="none" stroke="{accent}" stroke-width="12"/>',
            text(350, 104, TEXT["label"], 12, ink, family, "middle", 1.1),
            text(350, 207, TEXT["remont_kvartir"], 40, ink, family, "middle", -1),
            text(350, 299, TEXT["turnkey"], 78, ink, family, "middle", -2.5),
            f'<rect x="145" y="340" width="410" height="4" fill="{accent}"/>',
            text(350, 391, TEXT["contract"] + "  \u2022  " + TEXT["warranty"], 18, ink, family, "middle"),
            text(350, 431, TEXT["stages"] + "  \u2022  " + TEXT["supervision"], 15, ink, family, "middle"),
            f'<rect x="0" y="476" width="700" height="224" fill="{ink}"/>',
            text(130, 586, TEXT["roman"], 17, "#C7A365", family, spacing=3),
            '<rect x="234" y="548" width="3" height="53" fill="#C7A365"/>',
            text(258, 592, TEXT["phone"], 32, bg, family, spacing=-1),
        ]
    return svg_document("".join(body), "Variant 1 - olive", round_format)


def variant_2(round_format):
    family = FONTS["v2"]["family"]
    light, ink, blue, slate, white = "#EAF2FF", "#27415F", "#5F8FD8", "#4D6683", "#FFFFFF"
    if not round_format:
        body = [
            f'<rect width="700" height="700" fill="{light}"/>',
            f'<rect x="58" y="55" width="8" height="326" fill="{blue}"/>',
            text(88, 170, TEXT["remont"], 61, ink, family, spacing=-3),
            text(88, 240, TEXT["kvartir"], 61, ink, family, spacing=-3),
            text(88, 332, TEXT["turnkey"], 70, blue, family, spacing=-3),
            f'<rect x="58" y="412" width="584" height="1.5" fill="{blue}"/>',
            text(61, 458, "01  " + TEXT["contract"], 17, slate, family),
            text(367, 458, "02  " + TEXT["warranty"], 17, slate, family),
            text(61, 503, "03  " + TEXT["stages"], 15, slate, family),
            text(367, 503, "04  " + TEXT["supervision"], 17, slate, family),
            f'<rect x="58" y="558" width="584" height="94" rx="9" fill="{blue}"/>',
            text(85, 617, TEXT["roman"], 16, white, family, spacing=3),
            '<rect x="194" y="580" width="2" height="48" fill="#FFFFFF"/>',
            text(220, 620, TEXT["phone"], 31, white, family, spacing=-1.5),
        ]
    else:
        body = [
            f'<rect width="700" height="700" fill="{light}"/>',
            f'<circle cx="350" cy="350" r="328" fill="none" stroke="{blue}" stroke-width="9"/>',
            text(350, 191, TEXT["remont"], 52, ink, family, "middle", -2),
            text(350, 249, TEXT["kvartir"], 52, ink, family, "middle", -2),
            text(350, 333, TEXT["turnkey"], 64, blue, family, "middle", -3),
            f'<rect x="150" y="369" width="400" height="2" fill="{blue}"/>',
            text(350, 417, TEXT["contract"] + " / " + TEXT["warranty"], 15, slate, family, "middle"),
            text(350, 453, TEXT["stages"] + " / " + TEXT["supervision"], 12.5, slate, family, "middle"),
            f'<rect x="105" y="513" width="490" height="98" rx="49" fill="{blue}"/>',
            text(140, 574, TEXT["roman"], 14, white, family, spacing=2),
            '<rect x="235" y="540" width="2" height="46" fill="#FFFFFF"/>',
            text(260, 576, TEXT["phone"], 27, white, family, spacing=-1.5),
        ]
    return svg_document("".join(body), "Variant 2 - light blue", round_format)


def variant_3(round_format):
    family = FONTS["v3"]["family"]
    sand, wine, terra, cream = "#E9DDC9", "#512A2E", "#C66A4A", "#FFF9EF"
    if not round_format:
        body = [
            f'<rect width="700" height="700" fill="{sand}"/>',
            f'<rect x="38" y="38" width="624" height="624" fill="none" stroke="{wine}" stroke-width="3"/>',
            text(350, 204, TEXT["remont_kvartir"], 45, wine, family, "middle", -1),
            text(350, 303, TEXT["turnkey"], 82, wine, family, "middle", -2),
            f'<circle cx="350" cy="354" r="7" fill="{terra}"/>',
            text(350, 408, TEXT["contract"] + "  \u2022  " + TEXT["warranty"], 18, wine, family, "middle"),
            text(350, 449, TEXT["stages"] + "  \u2022  " + TEXT["supervision"], 15.5, wine, family, "middle"),
            f'<rect x="87" y="512" width="526" height="111" fill="{wine}"/>',
            text(115, 582, TEXT["roman"], 15, cream, family, spacing=2),
            f'<rect x="219" y="544" width="2" height="51" fill="{terra}"/>',
            text(245, 587, TEXT["phone"], 31, cream, family, spacing=-1),
        ]
    else:
        body = [
            f'<rect width="700" height="700" fill="{sand}"/>',
            f'<circle cx="350" cy="350" r="330" fill="none" stroke="{wine}" stroke-width="3"/>',
            f'<circle cx="350" cy="350" r="312" fill="none" stroke="{terra}" stroke-width="2"/>',
            text(350, 205, TEXT["remont_kvartir"], 39, wine, family, "middle", -1),
            text(350, 296, TEXT["turnkey"], 73, wine, family, "middle", -2),
            f'<circle cx="350" cy="345" r="7" fill="{terra}"/>',
            text(350, 396, TEXT["contract"] + "  \u2022  " + TEXT["warranty"], 16, wine, family, "middle"),
            text(350, 435, TEXT["stages"] + "  \u2022  " + TEXT["supervision"], 13.5, wine, family, "middle"),
            f'<rect x="105" y="501" width="490" height="108" rx="54" fill="{wine}"/>',
            text(137, 568, TEXT["roman"], 14, cream, family, spacing=2),
            f'<rect x="232" y="529" width="2" height="51" fill="{terra}"/>',
            text(257, 573, TEXT["phone"], 28, cream, family, spacing=-1),
        ]
    return svg_document("".join(body), "Variant 3 - sand terracotta", round_format)


def outline_text(source, target, font_path):
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


def make_contact_sheet(previews):
    thumb = 460
    label_height = 46
    sheet = Image.new("RGB", (thumb * 3, (thumb + label_height) * 2), "#EFEFEF")
    draw = ImageDraw.Draw(sheet)
    for index, (label, path) in enumerate(previews):
        image = Image.open(path).convert("RGBA")
        background = Image.new("RGBA", image.size, "#FFFFFF")
        background.alpha_composite(image)
        image = background.convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS)
        x = (index % 3) * thumb
        y = (index // 3) * (thumb + label_height)
        sheet.paste(image, (x, y))
        draw.text((x + 14, y + thumb + 12), label, fill="#111111")
    sheet.save(OUT / "all-variants-preview.png", quality=95)


def main():
    previews = []
    generators = [variant_1, variant_2, variant_3]
    for number, generator in enumerate(generators, 1):
        for shape in ("square", "round"):
            round_format = shape == "round"
            stem = f"variant-{number}-{shape}-700x700"
            editable = OUT / f"{stem}-editable.svg"
            printable = OUT / f"{stem}-print.svg"
            pdf = OUT / f"{stem}-print.pdf"
            preview = OUT / f"{stem}-preview.png"
            editable.write_text(generator(round_format), encoding="utf-8")
            outline_text(editable, printable, FONTS[f"v{number}"]["file"])
            cairosvg.svg2pdf(url=str(printable), write_to=str(pdf))
            cairosvg.svg2png(
                url=str(printable),
                write_to=str(preview),
                output_width=1400,
                output_height=1400,
            )
            previews.append((f"Variant {number} - {shape}", preview))
    make_contact_sheet(previews)


if __name__ == "__main__":
    main()

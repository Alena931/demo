#!/usr/bin/env python3
"""A5 back: navy wish text on white, faint circuit silhouettes from the front."""

from __future__ import annotations

import io
import math
import random
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdfcanvas

ROOT = Path("/workspace/lasmart-ny-2027")
OUT = ROOT / "pixel" / "back"
PRINT = ROOT / "pixel" / "print"
LOGO = ROOT / "lasmart-logo.png"
FRONT_PDF = PRINT / "lasmart-2027-a5-148x210.pdf"
ART = Path("/opt/cursor/artifacts")

W_MM, H_MM = 148.0, 210.0
DPI = 300
W = int(round(W_MM / 25.4 * DPI))
H = int(round(H_MM / 25.4 * DPI))
PX = DPI / 25.4  # px per mm

NAVY = (44, 40, 100)
CYAN = (42, 143, 205)
WHITE = (255, 255, 255)

FONT_BODY = "/usr/share/fonts/truetype/macos/Inter-Regular.ttf"
FONT_MED = "/usr/share/fonts/truetype/macos/Inter-Medium.ttf"
FONT_SIGN = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Italic.ttf"

# Same length and structure as 2026: greeting, year-wish, trust/partnership, IT close.
SALUTATION = "Дорогие партнёры!"
P1 = [
    "Команда Lasmart поздравляет вас",
    "с Новым годом! Пусть 2027 принесёт",
    "новые возможности, уверенность",
    "и поводы для профессиональной",
    "гордости.",
]
P2 = [
    "Ваше доверие и готовность идти",
    "вместе — то, что помогает нам",
    "находить верные взаимосвязи.",
    "Каждый новый проект — возможность",
    "расти рядом с вами, преодолевать",
    "вызовы и задавать новые стандарты",
    "в IT-индустрии.",
]
P3 = [
    "Мы ценим наше партнёрство, вместе",
    "мы создаём IT-реальность будущего!",
]
SIGN = ["С наилучшими пожеланиями,", "команда Lasmart"]


def font(path: str, mm_size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, int(round(mm_size * PX)))


def mmxy(x: float, y: float) -> tuple[int, int]:
    return int(round(x * PX)), int(round(y * PX))


def draw_trace(d: ImageDraw.ImageDraw, pts: list[tuple[float, float]], width_mm: float, color, scale: int) -> None:
    if len(pts) < 2:
        return
    xy = [(x * PX * scale, y * PX * scale) for x, y in pts]
    w = max(1, int(round(width_mm * PX * scale)))
    d.line(xy, fill=color, width=w, joint="curve")
    r = w / 2
    for x, y in xy:
        d.ellipse((x - r, y - r, x + r, y + r), fill=color)


def draw_pad(d: ImageDraw.ImageDraw, x: float, y: float, r_mm: float, color, scale: int, fill: bool = True) -> None:
    cx, cy = x * PX * scale, y * PX * scale
    r = r_mm * PX * scale
    box = (cx - r, cy - r, cx + r, cy + r)
    if fill:
        d.ellipse(box, fill=color)
    else:
        d.ellipse(box, outline=color, width=max(1, int(round(0.22 * PX * scale))))


def circuit_layer(scale: int = 2) -> Image.Image:
    """Orthogonal PCB silhouettes in the spirit of the front ice traces."""
    im = Image.new("RGBA", (W * scale, H * scale), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(2027)
    cyan = (*CYAN, 255)
    navy = (*NAVY, 255)

    nets: list[tuple[list[tuple[float, float]], float, tuple[int, int, int, int], list[tuple[float, float, float]]]] = []

    def net(pts, w=0.82, color=cyan, pads=None):
        nets.append((pts, w, color, pads or []))

    # Bottom-left — large fragment like the ice board on the front
    net([(4, 198), (28, 198), (28, 178), (48, 178), (48, 164), (18, 164), (18, 186)], 0.92, cyan,
        [(4, 198, 1.45), (28, 198, 1.05), (28, 178, 0.9), (48, 178, 1.2), (48, 164, 0.9), (18, 164, 1.05), (18, 186, 0.9)])
    net([(8, 206), (40, 206), (40, 190), (62, 190)], 0.7, navy,
        [(8, 206, 1.15), (40, 206, 0.85), (40, 190, 0.85), (62, 190, 1.05)])
    net([(2, 172), (22, 172), (22, 154), (36, 154), (36, 142)], 0.78, cyan,
        [(2, 172, 1.05), (22, 172, 0.8), (22, 154, 0.9), (36, 154, 0.8), (36, 142, 1.15)])
    net([(10, 148), (10, 132), (26, 132), (26, 118)], 0.62, navy,
        [(10, 148, 0.9), (10, 132, 0.7), (26, 132, 0.7), (26, 118, 0.95)])
    net([(6, 190), (6, 178), (14, 178)], 0.55, cyan, [(6, 190, 0.7), (6, 178, 0.65), (14, 178, 0.8)])

    # Bottom-right
    net([(144, 200), (118, 200), (118, 182), (100, 182), (100, 168), (128, 168)], 0.9, cyan,
        [(144, 200, 1.4), (118, 200, 0.95), (118, 182, 0.9), (100, 182, 1.15), (100, 168, 0.9), (128, 168, 1.05)])
    net([(146, 188), (132, 188), (132, 174), (146, 174)], 0.68, navy,
        [(146, 188, 0.9), (132, 188, 0.7), (132, 174, 0.7), (146, 174, 0.95)])
    net([(138, 158), (138, 140), (116, 140), (116, 126), (132, 126)], 0.75, cyan,
        [(138, 158, 1.05), (138, 140, 0.8), (116, 140, 0.9), (116, 126, 0.7), (132, 126, 1.0)])
    net([(108, 206), (108, 194), (92, 194), (92, 178)], 0.6, navy,
        [(108, 206, 0.9), (108, 194, 0.65), (92, 194, 0.7), (92, 178, 0.95)])
    net([(140, 206), (140, 194)], 0.55, cyan, [(140, 206, 0.75), (140, 194, 0.7)])

    # Top-left
    net([(4, 8), (26, 8), (26, 24), (12, 24), (12, 38), (32, 38)], 0.85, cyan,
        [(4, 8, 1.25), (26, 8, 0.9), (26, 24, 0.8), (12, 24, 0.7), (12, 38, 0.9), (32, 38, 1.1)])
    net([(6, 18), (18, 18), (18, 6)], 0.58, navy, [(6, 18, 0.8), (18, 18, 0.65), (18, 6, 0.9)])
    net([(2, 50), (16, 50), (16, 64), (8, 64), (8, 78)], 0.62, cyan,
        [(2, 50, 0.9), (16, 50, 0.7), (16, 64, 0.65), (8, 64, 0.65), (8, 78, 0.95)])

    # Top-right
    net([(144, 10), (122, 10), (122, 26), (136, 26), (136, 42), (114, 42)], 0.85, cyan,
        [(144, 10, 1.25), (122, 10, 0.9), (122, 26, 0.8), (136, 26, 0.7), (136, 42, 0.9), (114, 42, 1.1)])
    net([(146, 32), (146, 18), (132, 18)], 0.58, navy, [(146, 32, 0.9), (146, 18, 0.65), (132, 18, 0.9)])
    net([(140, 56), (140, 72), (124, 72), (124, 88)], 0.68, cyan,
        [(140, 56, 0.95), (140, 72, 0.7), (124, 72, 0.7), (124, 88, 1.0)])

    # Mid-left edge
    net([(0, 96), (18, 96), (18, 110), (8, 110), (8, 128), (22, 128)], 0.48, navy,
        [(0, 96, 0.6), (18, 96, 0.55), (18, 110, 0.5), (8, 110, 0.5), (8, 128, 0.55), (22, 128, 0.75)])
    net([(3, 108), (12, 108)], 0.35, cyan, [(3, 108, 0.55), (12, 108, 0.45)])

    # Mid-right edge
    net([(148, 100), (130, 100), (130, 116), (142, 116), (142, 134), (126, 134)], 0.48, cyan,
        [(148, 100, 0.65), (130, 100, 0.55), (130, 116, 0.5), (142, 116, 0.5), (142, 134, 0.55), (126, 134, 0.8)])
    net([(146, 122), (136, 122)], 0.35, navy, [(146, 122, 0.5), (136, 122, 0.45)])

    # A few extra short hops so the field is not empty
    extras = [
        ([(44, 8), (44, 20), (56, 20)], 0.38, navy, [(44, 8, 0.6), (44, 20, 0.45), (56, 20, 0.7)]),
        ([(92, 6), (104, 6), (104, 18)], 0.38, cyan, [(92, 6, 0.65), (104, 6, 0.45), (104, 18, 0.7)]),
        ([(54, 202), (54, 188), (70, 188)], 0.4, cyan, [(54, 202, 0.7), (54, 188, 0.5), (70, 188, 0.75)]),
        ([(78, 206), (86, 206), (86, 192)], 0.36, navy, [(78, 206, 0.55), (86, 206, 0.45), (86, 192, 0.7)]),
        ([(4, 88), (14, 88), (14, 78)], 0.36, cyan, [(4, 88, 0.55), (14, 88, 0.4), (14, 78, 0.6)]),
        ([(144, 90), (134, 90), (134, 80)], 0.36, navy, [(144, 90, 0.55), (134, 90, 0.4), (134, 80, 0.6)]),
    ]
    for e in extras:
        net(*e)

    for pts, w, color, pads in nets:
        draw_trace(d, pts, w, color, scale)
        for x, y, r in pads:
            if r >= 1.0:
                draw_pad(d, x, y, r, color, scale, fill=False)
                draw_pad(d, x, y, r * 0.42, color, scale, fill=True)
            else:
                draw_pad(d, x, y, r, color, scale, fill=True)

    # Tiny via dots along the side rails, like the reference crop
    for _ in range(14):
        x = rnd.choice([rnd.uniform(4, 16), rnd.uniform(132, 144)])
        y = rnd.uniform(12, 198)
        col = cyan if rnd.random() > 0.4 else navy
        draw_pad(d, x, y, rnd.choice([0.42, 0.52, 0.62]), col, scale)

    layer = im.resize((W, H), Image.Resampling.LANCZOS)
    arr = np.array(layer).astype(np.float32)
    yy, xx = np.ogrid[:H, :W]
    nx = (xx - W / 2) / (W * 0.36)
    ny = (yy - H / 2) / (H * 0.34)
    r = np.sqrt(nx * nx + ny * ny)
    fade = np.clip((r - 0.42) / 0.85, 0.0, 1.0)
    # keep corners stronger, text column quieter
    fade = fade ** 0.85
    arr[..., 3] *= fade * 0.34
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def paste_logo(card: Image.Image) -> None:
    logo = Image.open(LOGO).convert("RGBA")
    width_mm = 34.0
    w = int(round(width_mm * PX))
    h = int(round(w * logo.size[1] / logo.size[0]))
    logo = logo.resize((w, h), Image.Resampling.LANCZOS)
    x = (W - w) // 2
    y = int(round(20 * PX))
    card.alpha_composite(logo, (x, y))


def center_text(draw: ImageDraw.ImageDraw, text: str, y_mm: float, fnt, fill) -> float:
    x = W / 2
    y = y_mm * PX
    draw.text((x, y), text, font=fnt, fill=fill, anchor="ma")
    bbox = fnt.getbbox(text)
    return (bbox[3] - bbox[1]) / PX


def block(draw, lines, y_mm, fnt, fill, leading_mm) -> float:
    for line in lines:
        center_text(draw, line, y_mm, fnt, fill)
        y_mm += leading_mm
    return y_mm


def compose() -> Image.Image:
    card = Image.new("RGBA", (W, H), (*WHITE, 255))
    card.alpha_composite(circuit_layer(scale=2))
    paste_logo(card)
    draw = ImageDraw.Draw(card)

    body = font(FONT_BODY, 4.15)
    med = font(FONT_MED, 4.35)
    sign = font(FONT_SIGN, 5.4)
    navy = (*NAVY, 255)

    y = 48.0
    center_text(draw, SALUTATION, y, med, navy)
    y = 62.0
    y = block(draw, P1, y, body, navy, 6.15)
    y += 7.2
    y = block(draw, P2, y, body, navy, 6.15)
    y += 7.2
    y = block(draw, P3, y, body, navy, 6.15)

    y = 176.0
    y = block(draw, SIGN, y, sign, navy, 8.2)
    return card.convert("RGB")


def save_pdf(im: Image.Image, dest: Path, width_mm: float, height_mm: float) -> None:
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=95, subsampling=0, optimize=True, dpi=(DPI, DPI))
    buf.seek(0)
    c = pdfcanvas.Canvas(str(dest), pagesize=(width_mm * mm, height_mm * mm))
    c.setTitle("Lasmart 2027 — оборот")
    c.setAuthor("Lasmart")
    c.drawImage(ImageReader(buf), 0, 0, width=width_mm * mm, height=height_mm * mm, mask="auto")
    c.showPage()
    c.save()


def extend_bleed(trim: Image.Image, bleed_mm: float = 3.0) -> Image.Image:
    pad = int(round(bleed_mm / 25.4 * DPI))
    arr = np.asarray(trim)
    return Image.fromarray(np.pad(arr, ((pad, pad), (pad, pad), (0, 0)), mode="edge"))


def duplex(front: Path, back: Path, dest: Path) -> None:
    writer = PdfWriter()
    for p in (front, back):
        reader = PdfReader(str(p))
        writer.add_page(reader.pages[0])
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        writer.write(f)


def write_svg(dest: Path) -> None:
    """Editable SVG with the same copy; circuits as simple paths."""
    def t(x, y, s, size, weight="400", family="Inter", italic=False):
        ital = ' font-style="italic"' if italic else ""
        return (
            f'<text x="{x:.2f}" y="{y:.2f}" fill="#2C2864" font-family="{family}" '
            f'font-size="{size:.2f}" font-weight="{weight}" text-anchor="middle"{ital}>{s}</text>'
        )

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_MM}mm" height="{H_MM}mm" viewBox="0 0 {W_MM} {H_MM}">',
        "<title>Lasmart 2027 — оборот</title>",
        '<rect width="148" height="210" fill="#FFFFFF"/>',
        t(74, 48.8, SALUTATION, 4.35, "500"),
    ]
    y = 64.2
    for line in P1:
        parts.append(t(74, y, line, 4.15))
        y += 6.15
    y += 7.2
    for line in P2:
        parts.append(t(74, y, line, 4.15))
        y += 6.15
    y += 7.2
    for line in P3:
        parts.append(t(74, y, line, 4.15))
        y += 6.15
    y = 178.2
    for line in SIGN:
        parts.append(t(74, y, line, 5.4, "400", "Noto Serif Display", True))
        y += 8.2
    parts.append("</svg>")
    dest.write_text("\n".join(parts) + "\n", encoding="utf-8")


def word_count() -> None:
    import re

    def words(s: str) -> list[str]:
        return re.findall(r"[A-Za-zА-Яа-яЁё0-9-]+", s)

    last = (
        "Команда Lasmart поздравляет вас с Новым годом! Пусть 2026 принесет "
        "новые возможности, уверенность и поводы для профессиональной гордости. "
        "Ваше доверие и готовность к инновациям то что помогает нам двигаться вперед. "
        "Каждый новый проект возможность вместе менять будущее, преодолевать вызовы "
        "и задавать новые стандарты в IT-индустрии. "
        "Мы ценим наше партнерство, вместе мы создаём IT-реальность будущего!"
    )
    now = " ".join(P1 + P2 + P3)
    print("words 2026 body", len(words(last)))
    print("words 2027 body", len(words(now)))
    print("salut", SALUTATION, len(words(SALUTATION)))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PRINT.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    word_count()

    card = compose()
    png = OUT / "lasmart-2027-back.png"
    jpg = OUT / "lasmart-2027-back.jpg"
    pdf = OUT / "lasmart-2027-back.pdf"
    pdf_bleed = OUT / "lasmart-2027-back-bleed-3mm.pdf"
    svg = OUT / "lasmart-2027-back.svg"
    preview = OUT / "lasmart-2027-back-preview.jpg"

    card.save(png, "PNG", dpi=(DPI, DPI), optimize=True)
    card.save(jpg, "JPEG", quality=95, subsampling=0, dpi=(DPI, DPI))
    save_pdf(card, pdf, W_MM, H_MM)
    save_pdf(extend_bleed(card), pdf_bleed, W_MM + 6, H_MM + 6)
    write_svg(svg)

    prev = card.copy()
    prev.thumbnail((900, 1280), Image.Resampling.LANCZOS)
    prev.save(preview, "JPEG", quality=90)
    prev.save(ART / "back_card_preview.jpg", "JPEG", quality=90)

    shutil.copy2(png, ROOT / "lasmart-2027-back.png")
    shutil.copy2(pdf, ROOT / "lasmart-2027-back.pdf")
    shutil.copy2(png, PRINT / "lasmart-2027-back-300dpi.png")
    shutil.copy2(pdf, PRINT / "lasmart-2027-back-148x210.pdf")
    shutil.copy2(pdf_bleed, PRINT / "lasmart-2027-back-bleed-3mm.pdf")
    shutil.copy2(png, ART / "lasmart-2027-back.png")
    shutil.copy2(pdf, ART / "lasmart-2027-back.pdf")

    if FRONT_PDF.exists():
        duplex_path = PRINT / "lasmart-2027-otkrytka-a5.pdf"
        duplex(FRONT_PDF, pdf, duplex_path)
        shutil.copy2(duplex_path, ROOT / "lasmart-2027-otkrytka.pdf")
        shutil.copy2(duplex_path, ART / "lasmart-2027-otkrytka-a5.pdf")
        print("duplex", duplex_path)

    print("wrote", png, card.size)


if __name__ == "__main__":
    main()

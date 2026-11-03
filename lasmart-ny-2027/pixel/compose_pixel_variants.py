#!/usr/bin/env python3
"""Pack pixel-tree card fronts: PNG, A5 PDF, labeled comparison sheet."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/workspace/lasmart-ny-2027")
PIXEL = ROOT / "pixel"
ART = Path("/opt/cursor/artifacts/assets")
WALK = Path("/opt/cursor/artifacts")

# A5 portrait at 300 dpi
A5 = (1748, 2480)

FONT = "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf"
FONT_SM = "/usr/share/fonts/truetype/macos/Inter-Medium.ttf"

VARIANTS = [
    {
        "src": "pixel-a-navy-mid.jpg",
        "slug": "a-navy-mid",
        "title": "Navy средний",
        "hex": "#2A3F86",
        "group": "navy",
        "note": "тот же navy, чуть светлее оригинала; пиксельный город и лес",
    },
    {
        "src": "pixel-f-navy-light.jpg",
        "slug": "f-navy-light",
        "title": "Navy светлый",
        "hex": "#3E5BB5",
        "group": "navy",
        "note": "зимний вечер; серверные стойки на горизонте",
    },
    {
        "src": "pixel-g-navy-mist.jpg",
        "slug": "g-navy-mist",
        "title": "Navy дымка",
        "hex": "#5C74C8",
        "group": "navy",
        "note": "ещё светлее, серверы и пиксельный снег",
    },
    {
        "src": "pixel-b-navy-ice.jpg",
        "slug": "b-navy-ice",
        "title": "Navy лёд",
        "hex": "#6A88D4",
        "group": "navy",
        "note": "самый светлый navy; стойки и трассы на снегу",
    },
    {
        "src": "pixel-e-twilight.jpg",
        "slug": "e-twilight",
        "title": "Сумерки / циан",
        "hex": "#2A6A80",
        "group": "other",
        "note": "ледяной циан из логотипа; плата во льду",
    },
    {
        "src": "pixel-c-forest.jpg",
        "slug": "c-forest",
        "title": "Хвоя",
        "hex": "#2A6B4C",
        "group": "other",
        "note": "новогодний лес; пиксельные ели и горы-стойки",
    },
    {
        "src": "pixel-d-burgundy.jpg",
        "slug": "d-burgundy",
        "title": "Бордо",
        "hex": "#6A1F3A",
        "group": "other",
        "note": "праздничное вино; плата под сугробами, стойки",
    },
]


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def upscale_a5(im: Image.Image) -> Image.Image:
    return im.convert("RGB").resize(A5, Image.Resampling.LANCZOS)


def save_pdf(im: Image.Image, dest: Path) -> None:
    page = im.convert("RGB")
    page.save(dest, "PDF", resolution=300.0)


def labeled_thumb(im: Image.Image, title: str, hex_code: str, note: str, w: int = 520) -> Image.Image:
    ratio = im.height / im.width
    h = int(w * ratio)
    card = im.convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
    pad_top, pad_side, pad_bot = 18, 18, 92
    canvas = Image.new("RGB", (w + pad_side * 2, h + pad_top + pad_bot), (248, 248, 250))
    canvas.paste(card, (pad_side, pad_top))
    draw = ImageDraw.Draw(canvas)
    draw.text((pad_side, pad_top + h + 12), title, fill=(28, 28, 40), font=font(FONT, 22))
    draw.text((pad_side, pad_top + h + 40), hex_code, fill=(90, 96, 120), font=font(FONT_SM, 16))
    draw.text((pad_side, pad_top + h + 62), note, fill=(110, 114, 132), font=font(FONT_SM, 13))
    return canvas


def comparison_sheet(thumbs: list[Image.Image]) -> Image.Image:
    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    tw, th = thumbs[0].size
    gap = 24
    header = 110
    W = cols * tw + (cols + 1) * gap
    H = header + rows * th + (rows + 1) * gap
    sheet = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text((gap, 28), "Lasmart · пиксельная ёлка · вариации фона", fill=(28, 28, 40), font=font(FONT, 32))
    draw.text(
        (gap, 70),
        "Без 0/1. Задний план — пиксельный лес, серверные стойки, плата в снегу.",
        fill=(110, 114, 132),
        font=font(FONT_SM, 18),
    )
    for i, thumb in enumerate(thumbs):
        r, c = divmod(i, cols)
        x = gap + c * (tw + gap)
        y = header + gap + r * (th + gap)
        sheet.paste(thumb, (x, y))
    return sheet


def main() -> None:
    PIXEL.mkdir(parents=True, exist_ok=True)
    orig = Path("/home/ubuntu/.cursor/projects/workspace/assets/b6fab7be-e8cf-428b-86dc-a863e671f1e3.jpg")
    if orig.exists():
        shutil.copy2(orig, PIXEL / "00-original-concept.jpg")

    thumbs: list[Image.Image] = []
    for v in VARIANTS:
        src = ART / v["src"]
        im = Image.open(src)
        a5 = upscale_a5(im)
        png = PIXEL / f"lasmart-2027-pixel-{v['slug']}.png"
        pdf = PIXEL / f"lasmart-2027-pixel-{v['slug']}.pdf"
        a5.save(png, "PNG", optimize=True)
        save_pdf(a5, pdf)
        shutil.copy2(png, WALK / f"pixel_card_{v['slug']}.png")
        thumbs.append(labeled_thumb(im, v["title"], v["hex"], v["note"]))
        print("wrote", png.name, a5.size)

    sheet = comparison_sheet(thumbs)
    sheet_path = PIXEL / "lasmart-2027-pixel-compare.png"
    sheet.save(sheet_path, "PNG", optimize=True)
    shutil.copy2(sheet_path, WALK / "pixel_card_compare.png")
    print("compare", sheet.size)


if __name__ == "__main__":
    main()

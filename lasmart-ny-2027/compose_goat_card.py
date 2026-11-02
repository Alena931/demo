#!/usr/bin/env python3
"""Compose the geometric-goat NY card: art + type + logo, square print PDF."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pypdf import PdfReader, PdfWriter

ROOT = Path("/workspace/lasmart-ny-2027")
ART = ROOT / "lasmart-2027-goat-art.jpg"

SIZE = 2400  # px ≈ 180 mm at 338 dpi
GOLD = (214, 168, 86)
CREAM = (242, 232, 218)
GREEN = (4, 62, 47)
CYAN = (42, 143, 205)
MAGENTA = (146, 31, 120)
LIME = (128, 184, 40)

FONT_YEAR = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf"
FONT_LINE = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Regular.ttf"
FONT_UI_M = "/usr/share/fonts/truetype/macos/Inter-Medium.ttf"


def nudge_corporate(im: Image.Image) -> Image.Image:
    """Shift the few IT shards toward Lasmart cyan / magenta / lime."""
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            # generated cyan/teal triangle → brand cyan
            if r < 70 and g > 140 and b > 160 and b > r + 80:
                px[x, y] = (
                    int(r * 0.25 + CYAN[0] * 0.75),
                    int(g * 0.35 + CYAN[1] * 0.65),
                    int(b * 0.30 + CYAN[2] * 0.70),
                )
            # magenta diamonds → logo magenta, keep a little punch
            elif r > 150 and g < 90 and b > 70 and r > g + 80:
                px[x, y] = (
                    int(r * 0.35 + MAGENTA[0] * 0.65),
                    int(g * 0.45 + MAGENTA[1] * 0.55),
                    int(b * 0.40 + MAGENTA[2] * 0.60),
                )
            # lime circuit / bauble stripe → logo lime, keep it readable as "board"
            elif g > 170 and r > 90 and r < 200 and b < 90 and g > r + 20:
                px[x, y] = (
                    int(r * 0.45 + LIME[0] * 0.55),
                    int(g * 0.45 + LIME[1] * 0.55),
                    int(b * 0.50 + LIME[2] * 0.50),
                )
    return im


def draw_tracked(draw: ImageDraw.ImageDraw, xy, text, font, fill, tracking=0.0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking


def foil_text(overlay: Image.Image, xy, text, font, tracking=0.0):
    """Gold type with a quiet shadow so it sits on the green field."""
    shadow = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    gold = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    dg = ImageDraw.Draw(gold)
    x, y = xy
    draw_tracked(ds, (x + 2, y + 3), text, font, (0, 18, 12, 90), tracking)
    draw_tracked(dg, (x, y), text, font, GOLD + (255,), tracking)
    shadow = shadow.filter(ImageFilter.GaussianBlur(2.2))
    overlay.alpha_composite(shadow)
    overlay.alpha_composite(gold)


def brand_lockup(overlay: Image.Image, xy, tile=22, gap=6, word="Lasmart", size=36):
    """Four logo tiles + gold wordmark — readable on the dark green."""
    d = ImageDraw.Draw(overlay)
    x, y = xy
    colors = [CYAN, GOLD, MAGENTA, LIME]
    for i, color in enumerate(colors):
        tx = x + i * (tile + gap)
        d.rectangle((tx, y, tx + tile, y + tile), fill=color + (255,))
    font = ImageFont.truetype("/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf", size)
    word_x = x + 4 * (tile + gap) + 10
    word_y = y + tile / 2
    d.text((word_x, word_y), word, font=font, fill=GOLD + (255,), anchor="lm")


def front() -> Image.Image:
    art = Image.open(ART).convert("RGB")
    art = nudge_corporate(art)
    art = art.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    # paper grain, light — the field should not read as a dead fill
    noise = Image.effect_noise((SIZE, SIZE), 14).convert("L")
    noise = Image.merge("RGB", (noise, noise, noise))
    art = Image.blend(art, noise, 0.018)

    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    year = ImageFont.truetype(FONT_YEAR, 228)
    line = ImageFont.truetype(FONT_LINE, 62)
    foil_text(overlay, (108, 78), "2027", year, tracking=4)

    d = ImageDraw.Draw(overlay)
    draw_tracked(d, (118, 328), "С Новым годом,", line, CREAM + (255,), tracking=1.2)
    draw_tracked(d, (118, 412), "партнёры!", line, CREAM + (255,), tracking=1.2)

    brand_lockup(overlay, (118, SIZE - 118), tile=36, gap=8, size=48)

    return Image.alpha_composite(art.convert("RGBA"), overlay).convert("RGB")


def back() -> Image.Image:
    im = Image.new("RGB", (SIZE, SIZE), GREEN)
    noise = Image.effect_noise((SIZE, SIZE), 16).convert("L")
    noise = Image.merge("RGB", (noise, noise, noise))
    im = Image.blend(im, noise, 0.035)

    # faint mosaic — same geometry language as the goat, quieter
    d0 = ImageDraw.Draw(im, "RGBA")
    step = 80
    for y in range(0, SIZE, step):
        for x in range(0, SIZE, step):
            if (x // step + y // step) % 7 == 0:
                d0.polygon(
                    [(x, y + step), (x + step // 2, y), (x + step, y + step)],
                    fill=(214, 168, 86, 18),
                )
            elif (x // step + y // step) % 11 == 0:
                d0.rectangle((x + 18, y + 18, x + 38, y + 38), fill=(42, 143, 205, 22))

    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    tiles = [(CYAN, 0), (GOLD, 1), (MAGENTA, 2), (LIME, 3)]
    tw, gap = 52, 10
    total = 4 * tw + 3 * gap
    x0 = (SIZE - total) // 2
    y0 = 420
    for color, i in tiles:
        x = x0 + i * (tw + gap)
        d.rectangle((x, y0, x + tw, y0 + tw), fill=color + (255,))

    title = ImageFont.truetype(FONT_YEAR, 68)
    body = ImageFont.truetype(FONT_LINE, 46)
    ui = ImageFont.truetype(FONT_UI_M, 34)
    d.text((SIZE / 2, 560), "С новым годом", font=title, fill=GOLD + (255,), anchor="mt")

    lines = [
        "Спасибо, что доверяете нам",
        "данные, процессы и решения.",
        "",
        "Пусть 2027 будет годом,",
        "когда всё важное видно сразу.",
    ]
    y = 690
    for text in lines:
        if text:
            d.text((SIZE / 2, y), text, font=body, fill=CREAM + (255,), anchor="mt")
        y += 74

    word = ImageFont.truetype("/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf", 52)
    d.text((SIZE / 2, SIZE - 220), "Lasmart", font=word, fill=GOLD + (255,), anchor="mt")
    d.text((SIZE / 2, SIZE - 150), "lasmart.ru", font=ui, fill=GOLD + (255,), anchor="mt")
    return Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")


def save_pdf(images: list[Image.Image], dest: Path, mm: float = 180.0) -> None:
    paths = []
    for i, im in enumerate(images):
        p = ROOT / f"_page{i}.pdf"
        im.save(p, "PDF", resolution=im.size[0] / (mm / 25.4), title="Lasmart 2027")
        paths.append(p)
    writer = PdfWriter()
    for p in paths:
        writer.append(PdfReader(str(p)))
        p.unlink()
    with dest.open("wb") as f:
        writer.write(f)


def main():
    fr = front()
    bk = back()
    front_png = ROOT / "lasmart-2027-front.png"
    back_png = ROOT / "lasmart-2027-back.png"
    fr.save(front_png, "PNG")
    bk.save(back_png, "PNG")
    # preview-sized copies for the PR
    fr.resize((1200, 1200), Image.Resampling.LANCZOS).save(ROOT / "lasmart-2027-front-preview.png", "PNG")
    bk.resize((1200, 1200), Image.Resampling.LANCZOS).save(ROOT / "lasmart-2027-back-preview.png", "PNG")
    pdf = ROOT / "lasmart-2027-otkrytka.pdf"
    save_pdf([fr, bk], pdf)

    artifacts = Path("/opt/cursor/artifacts")
    artifacts.mkdir(parents=True, exist_ok=True)
    for src in (front_png, back_png, pdf, ROOT / "lasmart-2027-front-preview.png", ROOT / "lasmart-2027-back-preview.png"):
        shutil.copy2(src, artifacts / src.name)
    print("front", fr.size, "pdf", pdf, "bytes", pdf.stat().st_size)


if __name__ == "__main__":
    main()

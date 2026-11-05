#!/usr/bin/env python3
"""Print pack for the selected twilight pixel card: A5, 300 dpi, 3 mm bleed."""

from __future__ import annotations

import io
import shutil
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path("/workspace/lasmart-ny-2027")
SRC = ROOT / "pixel" / "lasmart-2027-pixel-e-twilight.png"
OUT = ROOT / "pixel" / "print"
ART = Path("/opt/cursor/artifacts")

DPI = 300
TRIM_MM = (148.0, 210.0)
BLEED_MM = 3.0
SLUG_MM = 8.0  # space for crop marks


def mm_px(value: float) -> int:
    return int(round(value / 25.4 * DPI))


def load_trim() -> Image.Image:
    im = Image.open(SRC).convert("RGB")
    target = (mm_px(TRIM_MM[0]), mm_px(TRIM_MM[1]))
    if im.size != target:
        im = im.resize(target, Image.Resampling.LANCZOS)
    return im


def extend_bleed(trim: Image.Image, bleed_mm: float) -> Image.Image:
    pad = mm_px(bleed_mm)
    arr = np.asarray(trim)
    padded = np.pad(arr, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    return Image.fromarray(padded)


def jpeg_bytes(im: Image.Image, quality: int = 95) -> bytes:
    buf = io.BytesIO()
    im.save(
        buf,
        "JPEG",
        quality=quality,
        subsampling=0,
        optimize=True,
        dpi=(DPI, DPI),
    )
    return buf.getvalue()


def pdf_from_image(im: Image.Image, dest: Path, width_mm: float, height_mm: float) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(dest), pagesize=(width_mm * mm, height_mm * mm))
    c.setTitle("Lasmart 2027 — С Новым Годом")
    c.setAuthor("Lasmart")
    reader = ImageReader(io.BytesIO(jpeg_bytes(im)))
    c.drawImage(reader, 0, 0, width=width_mm * mm, height=height_mm * mm, mask="auto")
    c.showPage()
    c.save()


def set_boxes(pdf_path: Path, media_mm: tuple[float, float], trim_inset_mm: float) -> None:
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    page = reader.pages[0]
    w = media_mm[0] * mm
    h = media_mm[1] * mm
    inset = trim_inset_mm * mm
    page.mediabox.lower_left = (0, 0)
    page.mediabox.upper_right = (w, h)
    page.cropbox.lower_left = (0, 0)
    page.cropbox.upper_right = (w, h)
    page.bleedbox.lower_left = (0, 0)
    page.bleedbox.upper_right = (w, h)
    page.trimbox.lower_left = (inset, inset)
    page.trimbox.upper_right = (w - inset, h - inset)
    writer.add_page(page)
    with pdf_path.open("wb") as f:
        writer.write(f)


def pdf_with_marks(bleed: Image.Image, dest: Path) -> None:
    """Bleed artwork + crop marks in the slug. Media = trim + bleed + slug."""
    page_w = TRIM_MM[0] + 2 * BLEED_MM + 2 * SLUG_MM
    page_h = TRIM_MM[1] + 2 * BLEED_MM + 2 * SLUG_MM
    c = canvas.Canvas(str(dest), pagesize=(page_w * mm, page_h * mm))
    c.setTitle("Lasmart 2027 — С Новым Годом (метки реза)")
    c.setAuthor("Lasmart")

    ox = (SLUG_MM) * mm
    oy = (SLUG_MM) * mm
    bw = (TRIM_MM[0] + 2 * BLEED_MM) * mm
    bh = (TRIM_MM[1] + 2 * BLEED_MM) * mm
    reader = ImageReader(io.BytesIO(jpeg_bytes(bleed)))
    c.drawImage(reader, ox, oy, width=bw, height=bh, mask="auto")

    trim_x0 = (SLUG_MM + BLEED_MM) * mm
    trim_y0 = (SLUG_MM + BLEED_MM) * mm
    trim_x1 = trim_x0 + TRIM_MM[0] * mm
    trim_y1 = trim_y0 + TRIM_MM[1] * mm
    mark = 5 * mm
    gap = 2 * mm
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.25)

    def hmark(x, y, direction):
        c.line(x + direction * gap, y, x + direction * (gap + mark), y)

    def vmark(x, y, direction):
        c.line(x, y + direction * gap, x, y + direction * (gap + mark))

    # Crop marks at trim corners
    hmark(trim_x0, trim_y0, -1)
    vmark(trim_x0, trim_y0, -1)
    hmark(trim_x1, trim_y0, 1)
    vmark(trim_x1, trim_y0, -1)
    hmark(trim_x0, trim_y1, -1)
    vmark(trim_x0, trim_y1, 1)
    hmark(trim_x1, trim_y1, 1)
    vmark(trim_x1, trim_y1, 1)

    c.setFont("Times-Roman", 7)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawString(ox, 3 * mm, "Lasmart 2027  |  A5 148x210 mm  |  bleed 3 mm  |  300 dpi  |  RGB")
    c.showPage()
    c.save()

    reader = PdfReader(str(dest))
    writer = PdfWriter()
    page = reader.pages[0]
    page.trimbox.lower_left = (trim_x0, trim_y0)
    page.trimbox.upper_right = (trim_x1, trim_y1)
    page.bleedbox.lower_left = (ox, oy)
    page.bleedbox.upper_right = (ox + bw, oy + bh)
    writer.add_page(page)
    with dest.open("wb") as f:
        writer.write(f)


def write_readme(dest: Path) -> None:
    dest.write_text(
        """# Lasmart 2027 — печатные файлы лицевой

Формат готового изделия: A5, 148 × 210 мм, одна сторона.
Разрешение: 300 dpi. Цветовое пространство: RGB.

## Что отдавать в типографию

- `lasmart-2027-a5-148x210.pdf` — чистый A5 без вылетов. Для цифровой печати «в размер».
- `lasmart-2027-a5-bleed-3mm.pdf` — 154 × 216 мм, вылет 3 мм, TrimBox = 148 × 210 мм.
- `lasmart-2027-a5-cropmarks.pdf` — то же с метками реза.
- `lasmart-2027-a5-300dpi.tif` — TIFF RGB, LZW, 300 dpi. Запасной растр.
- `lasmart-2027-a5-300dpi.jpg` — JPEG максимального качества, 300 dpi.
- `lasmart-2027-a5-300dpi.png` — PNG, 300 dpi.

Рекомендация: картон 300–350 г/м², без мелования. Вылет 3 мм со всех сторон.
""",
        encoding="utf-8",
    )


def zip_pack(files: list[Path], zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            zf.write(p, arcname=p.name)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    trim = load_trim()
    bleed = extend_bleed(trim, BLEED_MM)

    png = OUT / "lasmart-2027-a5-300dpi.png"
    jpg = OUT / "lasmart-2027-a5-300dpi.jpg"
    tif = OUT / "lasmart-2027-a5-300dpi.tif"
    pdf_trim = OUT / "lasmart-2027-a5-148x210.pdf"
    pdf_bleed = OUT / "lasmart-2027-a5-bleed-3mm.pdf"
    pdf_marks = OUT / "lasmart-2027-a5-cropmarks.pdf"
    readme = OUT / "README.md"

    trim.save(png, "PNG", dpi=(DPI, DPI), optimize=True)
    trim.save(
        jpg,
        "JPEG",
        quality=95,
        subsampling=0,
        optimize=True,
        dpi=(DPI, DPI),
    )
    trim.save(tif, "TIFF", compression="tiff_lzw", dpi=(DPI, DPI))

    pdf_from_image(trim, pdf_trim, TRIM_MM[0], TRIM_MM[1])
    pdf_from_image(bleed, pdf_bleed, TRIM_MM[0] + 2 * BLEED_MM, TRIM_MM[1] + 2 * BLEED_MM)
    set_boxes(pdf_bleed, (TRIM_MM[0] + 2 * BLEED_MM, TRIM_MM[1] + 2 * BLEED_MM), BLEED_MM)
    pdf_with_marks(bleed, pdf_marks)
    write_readme(readme)

    pack_files = [pdf_trim, pdf_bleed, pdf_marks, tif, jpg, png, readme]
    zpath = OUT / "lasmart-2027-print.zip"
    zip_pack(pack_files, zpath)

    ART.mkdir(parents=True, exist_ok=True)
    for p in pack_files + [zpath]:
        shutil.copy2(p, ART / p.name)

    # preview for chat
    preview = trim.copy()
    preview.thumbnail((900, 1280), Image.Resampling.LANCZOS)
    preview.save(ART / "print_card_preview.jpg", "JPEG", quality=90)

    print("trim", trim.size)
    print("bleed", bleed.size)
    for p in pack_files + [zpath]:
        print(p.name, p.stat().st_size)


if __name__ == "__main__":
    main()

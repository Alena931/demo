#!/usr/bin/env python3
"""Front-only: more IT mosaic, three lighter field greens, type overlay."""

from __future__ import annotations

import shutil
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path("/workspace/lasmart-ny-2027")
ART = Path("/opt/cursor/artifacts/assets/lasmart-2027-goat-it-v5.jpg")
SIZE = 2400

GOLD = (214, 168, 86)
CREAM = (242, 232, 218)
CYAN = (42, 143, 205)
MAGENTA = (146, 31, 120)
LIME = (128, 184, 40)
YELLOW = (244, 193, 25)
NAVY = (44, 40, 100)

FONT_YEAR = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf"
FONT_LINE = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Regular.ttf"
FONT_UI = "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf"
FONT_CAP = "/usr/share/fonts/truetype/macos/Inter-Medium.ttf"

# Three lighter fields. Original card field was ~#043E2F.
VARIANTS = [
    {
        "id": "a",
        "slug": "hvoya",
        "title": "Хвоя",
        "hex": "#1B6A4A",
        "rgb": (27, 106, 74),
        "note": "на ступень светлее исходного, всё ещё глубокий лес",
    },
    {
        "id": "b",
        "slug": "malachite",
        "title": "Малахит",
        "hex": "#228A58",
        "rgb": (34, 138, 88),
        "note": "средний, золото читается как фольга",
    },
    {
        "id": "c",
        "slug": "sage",
        "title": "Шалфей",
        "hex": "#3AA06C",
        "rgb": (58, 160, 108),
        "note": "самый открытый, дневной зелёный",
    },
]


def flood_background(arr: np.ndarray, tol: float = 36.0) -> np.ndarray:
    """Field green: flood from borders, plus any enclosed pocket of the same green."""
    h, w = arr.shape[:2]
    ref = arr[4, 4].astype(np.int16)
    visited = np.zeros((h, w), dtype=np.uint8)
    mask = np.zeros((h, w), dtype=np.uint8)
    q: deque[tuple[int, int]] = deque()
    seeds = [
        (4, 4),
        (w - 5, 4),
        (4, h - 5),
        (w - 5, h - 5),
        (w // 2, 4),
        (4, h // 3),
        (w - 5, h // 3),
        (w // 4, 4),
        (3 * w // 4, 4),
        (w // 2, h - 8),
        (420, 800),
        (500, 820),
    ]
    for x, y in seeds:
        if 0 <= x < w and 0 <= y < h:
            visited[y, x] = 1
            q.append((x, y))
    while q:
        x, y = q.popleft()
        pix = arr[y, x].astype(np.int16)
        if np.abs(pix - ref).sum() > tol:
            continue
        mask[y, x] = 255
        if x > 0 and not visited[y, x - 1]:
            visited[y, x - 1] = 1
            q.append((x - 1, y))
        if x + 1 < w and not visited[y, x + 1]:
            visited[y, x + 1] = 1
            q.append((x + 1, y))
        if y > 0 and not visited[y - 1, x]:
            visited[y - 1, x] = 1
            q.append((x, y - 1))
        if y + 1 < h and not visited[y + 1, x]:
            visited[y + 1, x] = 1
            q.append((x, y + 1))
    dist = np.abs(arr.astype(np.int16) - ref).sum(axis=2)
    mask = np.maximum(mask, np.where(dist < 30, 255, 0).astype(np.uint8))
    return mask


def nudge_corporate(im: Image.Image) -> Image.Image:
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r < 80 and g > 130 and b > 150 and b > r + 60:
                px[x, y] = (
                    int(r * 0.20 + CYAN[0] * 0.80),
                    int(g * 0.30 + CYAN[1] * 0.70),
                    int(b * 0.25 + CYAN[2] * 0.75),
                )
            elif r > 150 and g < 100 and b > 70 and r > g + 60:
                px[x, y] = (
                    int(r * 0.30 + MAGENTA[0] * 0.70),
                    int(g * 0.40 + MAGENTA[1] * 0.60),
                    int(b * 0.35 + MAGENTA[2] * 0.65),
                )
            elif g > 150 and 70 < r < 200 and b < 100 and g > r + 15:
                px[x, y] = (
                    int(r * 0.40 + LIME[0] * 0.60),
                    int(g * 0.40 + LIME[1] * 0.60),
                    int(b * 0.45 + LIME[2] * 0.55),
                )
    return im


def recolor_field(art: Image.Image, mask_u8: np.ndarray, target: tuple[int, int, int]) -> Image.Image:
    arr = np.array(art).astype(np.float32)
    m = mask_u8.astype(np.float32) / 255.0
    m = np.dstack([m, m, m])
    # keep a whisper of original grain so the field is not a dead fill
    ref = arr[4, 4]
    grain = arr - ref
    painted = np.array(target, dtype=np.float32) + grain * 0.35
    painted = np.clip(painted, 0, 255)
    out = arr * (1.0 - m) + painted * m
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def extra_bits(im: Image.Image, mask_u8: np.ndarray, rng: np.random.Generator) -> Image.Image:
    """Sparse brand-color tesserae on the field — data-confetti, not stickers."""
    d = ImageDraw.Draw(im)
    h, w = mask_u8.shape
    colors = [CYAN, MAGENTA, LIME, YELLOW, GOLD]
    placed = 0
    attempts = 0
    while placed < 16 and attempts < 400:
        attempts += 1
        x = int(rng.integers(40, w - 40))
        y = int(rng.integers(40, h - 70))
        if x < 300 and y < 220:
            continue
        if y > h - 90 and x < 280:
            continue
        if mask_u8[y, x] < 220:
            continue
        s = int(rng.choice([4, 5, 6, 7]))
        d.rectangle((x, y, x + s, y + s), fill=colors[int(rng.integers(0, len(colors)))])
        placed += 1
    return im


def draw_tracked(draw: ImageDraw.ImageDraw, xy, text, font, fill, tracking=0.0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking


def foil_text(overlay: Image.Image, xy, text, font, tracking=0.0):
    shadow = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    gold = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    dg = ImageDraw.Draw(gold)
    x, y = xy
    draw_tracked(ds, (x + 2, y + 3), text, font, (0, 18, 12, 80), tracking)
    draw_tracked(dg, (x, y), text, font, GOLD + (255,), tracking)
    overlay.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(2.0)))
    overlay.alpha_composite(gold)


def brand_lockup(overlay: Image.Image, xy, tile=36, gap=8, size=48):
    d = ImageDraw.Draw(overlay)
    x, y = xy
    for i, color in enumerate([CYAN, YELLOW, MAGENTA, LIME]):
        tx = x + i * (tile + gap)
        d.rectangle((tx, y, tx + tile, y + tile), fill=color + (255,))
    font = ImageFont.truetype(FONT_UI, size)
    word_x = x + 4 * (tile + gap) + 10
    d.text((word_x, y + tile / 2), "Lasmart", font=font, fill=GOLD + (255,), anchor="lm")


def overlay_type(art: Image.Image) -> Image.Image:
    art = art.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    year = ImageFont.truetype(FONT_YEAR, 228)
    line = ImageFont.truetype(FONT_LINE, 62)
    foil_text(overlay, (108, 78), "2027", year, tracking=4)
    d = ImageDraw.Draw(overlay)
    draw_tracked(d, (118, 328), "С Новым годом,", line, CREAM + (255,), tracking=1.2)
    draw_tracked(d, (118, 412), "партнёры!", line, CREAM + (255,), tracking=1.2)
    brand_lockup(overlay, (118, SIZE - 118), tile=36, gap=8, size=48)
    return Image.alpha_composite(art.convert("RGBA"), overlay).convert("RGB")


def labeled_strip(images: list[Image.Image], labels: list[str]) -> Image.Image:
    thumb = 720
    gap = 28
    cap = 72
    n = len(images)
    w = n * thumb + (n + 1) * gap
    h = thumb + cap + gap * 2
    canvas = Image.new("RGB", (w, h), (247, 244, 238))
    d = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT_CAP, 22)
    for i, (im, label) in enumerate(zip(images, labels)):
        t = im.resize((thumb, thumb), Image.Resampling.LANCZOS)
        x = gap + i * (thumb + gap)
        y = gap
        canvas.paste(t, (x, y))
        d.text((x + thumb / 2, y + thumb + 28), label, font=font, fill=(40, 50, 46), anchor="mt")
    return canvas


def main():
    raw = Image.open(ART).convert("RGB")
    raw = nudge_corporate(raw)
    arr = np.array(raw)
    mask = flood_background(arr, tol=42)
    # feather
    mask_im = Image.fromarray(mask, mode="L").filter(ImageFilter.GaussianBlur(1.1))
    mask = np.array(mask_im)
    artifacts = Path("/opt/cursor/artifacts")
    artifacts.mkdir(parents=True, exist_ok=True)
    out_dir = ROOT / "variants"
    out_dir.mkdir(exist_ok=True)

    composed = []
    labels = []
    for v in VARIANTS:
        field = recolor_field(raw, mask, v["rgb"])
        field = extra_bits(field, mask, np.random.default_rng(2027))
        # light paper grain
        noise = Image.effect_noise(field.size, 12).convert("L")
        noise = Image.merge("RGB", (noise, noise, noise))
        field = Image.blend(field, noise, 0.016)
        front = overlay_type(field)
        name = f"lasmart-2027-front-{v['id']}-{v['slug']}.png"
        dest = out_dir / name
        front.save(dest, "PNG")
        preview = front.resize((1200, 1200), Image.Resampling.LANCZOS)
        prev_name = f"lasmart-2027-front-{v['id']}-{v['slug']}-preview.png"
        preview.save(out_dir / prev_name, "PNG")
        preview.save(artifacts / prev_name, "PNG")
        shutil.copy2(dest, artifacts / name)
        composed.append(front)
        labels.append(f"{v['title']}  {v['hex']}")
        print(v["id"], v["hex"], dest)

    strip = labeled_strip(composed, labels)
    strip.save(out_dir / "lasmart-2027-front-bg-compare.png", "PNG")
    strip.save(artifacts / "lasmart-2027-front-bg-compare.png", "PNG")
    shutil.copy2(ART, ROOT / "lasmart-2027-goat-art-it.jpg")
    print("strip", strip.size)


if __name__ == "__main__":
    main()

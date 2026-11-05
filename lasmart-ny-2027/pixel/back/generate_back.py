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

# Year on the card is 2027; source copy said 2026.
VARIANTS = [
    {
        "id": "v1",
        "slug": "friends",
        "title": "Друзья и коллеги",
        "salut": "Дорогие друзья и коллеги!",
        "paragraphs": [
            "От всей души поздравляем вас с Новым годом! Пусть наступающий 2027 год принесет в вашу жизнь и бизнес гармонию, вдохновение и новые возможности для профессионального роста.",
            "Ваше доверие — это главный драйвер нашего развития. Спасибо, что разделяете с нами стремление к инновациям и готовность к экспериментам. Вместе мы не просто внедряем технологии, а создаем ту самую IT-реальность, в которой хочется жить и работать. Каждый ваш проект для нас — это ценный опыт и возможность преодолеть новые вызовы.",
            "Желаем вам в новом году уверенности в завтрашнем\u00a0дне и неизменного успеха во всех начинаниях!",
        ],
        "sign": ["С наилучшими пожеланиями,", "Команда Lasmart"],
    },
    {
        "id": "v2",
        "slug": "updates",
        "title": "Продуктивные апдейты",
        "salut": None,
        "paragraphs": [
            "Команда Lasmart поздравляет вас с наступающим Новым годом! Пусть 2027 год станет для вас годом продуктивных апдейтов, стабильной работы и новых профессиональных высот.",
            "Мы очень ценим ваше доверие и готовность идти в ногу с инновациями. Ваши идеи и задачи вдохновляют нас на создание качественных решений и помогают задавать новые стандарты в IT-индустрии. Вместе мы создаем прочную основу для будущего, где технологии работают на благо бизнеса и людей.",
            "Желаем вам в новом году безотказных решений, широких возможностей и только положительных откликов во всех начинаниях!",
        ],
        "sign": ["С наилучшими пожеланиями,", "Команда Lasmart"],
    },
    {
        "id": "v3",
        "slug": "renewal",
        "title": "Точка обновления",
        "salut": "Дорогие друзья и коллеги!",
        "paragraphs": [
            "Новый год — это точка обновления, с которой начинается следующий этап. Команда Lasmart рада пройти его вместе с вами.",
            "Спасибо за задачи, которые заставляли нас расти, и за диалог, в котором рождались сильные решения. В уходящем году мы вместе запускали, дорабатывали и доводили до результата — и именно это сотрудничество делает нашу работу осмысленной.",
            "Пусть в 2027 году ваши проекты идут по плану, идеи находят воплощение, а любые перемены приносят только пользу. Желаем вам крепкой команды рядом, ясных целей и времени на всё важное — и в работе, и за её пределами.",
        ],
        "sign": ["С Новым годом!", "Команда Lasmart"],
    },
    {
        "id": "v4",
        "slug": "stories",
        "title": "Друзья, итог года",
        "salut": "Дорогие друзья и коллеги!",
        "paragraphs": [
            "Подводим итог года и хотим сказать главное: нам ценно работать с людьми, которые не боятся нового. Спасибо, что выбирали нас и доверяли свои задачи.",
            "Каждый ваш проект — это отдельная история со своими вызовами и решениями. Мы вместе учились, искали нестандартные ходы и находили их. Этот опыт дорогого стоит.",
            "В наступающем году желаем вам уверенности в своих силах, интересных задач и достойных результатов. Пусть всё задуманное получается, а трудности оказываются просто этапами на пути к цели. Будем рады быть рядом в этом движении.",
        ],
        "sign": ["С Новым годом!", "Команда Lasmart"],
    },
    {
        "id": "v5",
        "slug": "partners",
        "title": "Уважаемые партнёры",
        "salut": "Уважаемые партнёры!",
        "paragraphs": [
            "За каждым проектом стоят люди — и это главное, что мы вынесли из уходящего года. Спасибо вам за сотрудничество, за доверие и за готовность вместе искать лучшие решения.",
            "Мы ценим наш диалог и надеемся, что и дальше будем двигаться в одном направлении — делать работу качественно, а технологии — полезными. Впереди новый год, а значит, новые задачи и новые поводы для гордости за результат.",
            "Желаем вам в 2027 году спокойствия в делах, вдохновения в идеях и людей рядом, на которых можно положиться.",
        ],
        "sign": ["С Новым годом!", "Команда Lasmart"],
    },
]

_CIRCUIT: Image.Image | None = None
TEXT_WIDTH_MM = 102.0
ORPHANS = {
    "в", "и", "на", "с", "к", "о", "у", "а", "я", "во", "со", "ко",
    "для", "от", "по", "из", "за", "не", "но", "об", "обо", "при",
}


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


def get_circuit() -> Image.Image:
    global _CIRCUIT
    if _CIRCUIT is None:
        _CIRCUIT = circuit_layer(scale=2)
    return _CIRCUIT


def paste_logo(card: Image.Image) -> None:
    logo = Image.open(LOGO).convert("RGBA")
    width_mm = 34.0
    w = int(round(width_mm * PX))
    h = int(round(w * logo.size[1] / logo.size[0]))
    logo = logo.resize((w, h), Image.Resampling.LANCZOS)
    x = (W - w) // 2
    y = int(round(18 * PX))
    card.alpha_composite(logo, (x, y))


def wrap_line(text: str, fnt: ImageFont.FreeTypeFont, max_mm: float) -> list[str]:
    max_px = max_mm * PX
    words = [w for w in text.split(" ") if w]
    lines: list[str] = []
    cur: list[str] = []

    def width(ws: list[str]) -> float:
        return fnt.getlength(" ".join(ws))

    i = 0
    while i < len(words):
        word = words[i]
        trial = cur + [word]
        if not cur or width(trial) <= max_px:
            cur = trial
            i += 1
            continue
        if len(cur) > 1 and cur[-1].lower().strip("—,.") in ORPHANS:
            orphan = cur.pop()
            lines.append(" ".join(cur))
            cur = [orphan, word]
            i += 1
        else:
            lines.append(" ".join(cur))
            cur = [word]
            i += 1
    if cur:
        lines.append(" ".join(cur))
    return lines


def center_text(draw: ImageDraw.ImageDraw, text: str, y_mm: float, fnt, fill) -> None:
    draw.text((W / 2, y_mm * PX), text, font=fnt, fill=fill, anchor="ma")


def layout_copy(variant: dict, body_mm: float, leading_mm: float) -> dict:
    body_f = font(FONT_BODY, body_mm)
    med_f = font(FONT_MED, 4.2)
    sign_f = font(FONT_SIGN, 5.2)
    blocks: list[tuple[str, list[str], ImageFont.FreeTypeFont]] = []
    if variant["salut"]:
        blocks.append(("salut", [variant["salut"]], med_f))
    for para in variant["paragraphs"]:
        blocks.append(("para", wrap_line(para, body_f, TEXT_WIDTH_MM), body_f))
    blocks.append(("sign", variant["sign"], sign_f))
    return {"blocks": blocks, "leading": leading_mm, "gap": 5.6, "sign_lead": 7.8}


def measure(layout: dict) -> float:
    h = 0.0
    n = len(layout["blocks"])
    for i, (kind, lines, _fnt) in enumerate(layout["blocks"]):
        lead = layout["sign_lead"] if kind == "sign" else layout["leading"]
        h += lead * len(lines)
        if i < n - 1:
            h += layout["gap"]
    return h


def compose(variant: dict) -> Image.Image:
    card = Image.new("RGBA", (W, H), (*WHITE, 255))
    card.alpha_composite(get_circuit())
    paste_logo(card)
    draw = ImageDraw.Draw(card)
    navy = (*NAVY, 255)

    y0, y1 = 44.0, 198.0
    layout = None
    for body_mm, leading in ((3.85, 5.55), (3.7, 5.35), (3.55, 5.15)):
        layout = layout_copy(variant, body_mm, leading)
        if measure(layout) <= (y1 - y0):
            break
    assert layout is not None
    y = y0 + max(0.0, (y1 - y0 - measure(layout)) / 2)

    for i, (kind, lines, fnt) in enumerate(layout["blocks"]):
        lead = layout["sign_lead"] if kind == "sign" else layout["leading"]
        for line in lines:
            center_text(draw, line, y, fnt, navy)
            y += lead
        if i < len(layout["blocks"]) - 1:
            y += layout["gap"]
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


def write_text(variant: dict, dest: Path) -> None:
    lines = []
    if variant["salut"]:
        lines.append(variant["salut"])
        lines.append("")
    for para in variant["paragraphs"]:
        lines.append(para)
        lines.append("")
    lines.extend(variant["sign"])
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def comparison(thumbs: list[tuple[str, Image.Image]], dest: Path, title: str) -> None:
    cols = min(3, max(1, len(thumbs)))
    rows = (len(thumbs) + cols - 1) // cols
    w, h = 480, int(480 * H / W)
    gap, header, pad, cap = 24, 72, 24, 40
    sheet = Image.new(
        "RGB",
        (pad * 2 + cols * w + (cols - 1) * gap, header + rows * (h + cap) + (rows - 1) * gap + pad),
        (255, 255, 255),
    )
    draw = ImageDraw.Draw(sheet)
    title_f = ImageFont.truetype(FONT_MED, 26)
    cap_f = ImageFont.truetype(FONT_BODY, 16)
    draw.text((pad, 22), title, fill=NAVY, font=title_f)
    for i, (label, im) in enumerate(thumbs):
        r, c = divmod(i, cols)
        thumb = im.resize((w, h), Image.Resampling.LANCZOS)
        x = pad + c * (w + gap)
        y = header + r * (h + cap + gap)
        sheet.paste(thumb, (x, y))
        draw.text((x, y + h + 6), label, fill=NAVY, font=cap_f)
    sheet.save(dest, "PNG", optimize=True)


def export_variant(variant: dict, card: Image.Image) -> Path:
    slug = variant["slug"]
    stem = f"lasmart-2027-back-{variant['id']}-{slug}"
    png = OUT / f"{stem}.png"
    jpg = OUT / f"{stem}.jpg"
    pdf = OUT / f"{stem}.pdf"
    bleed = OUT / f"{stem}-bleed-3mm.pdf"
    preview = OUT / f"{stem}-preview.jpg"
    card.save(png, "PNG", dpi=(DPI, DPI), optimize=True)
    card.save(jpg, "JPEG", quality=95, subsampling=0, dpi=(DPI, DPI))
    save_pdf(card, pdf, W_MM, H_MM)
    save_pdf(extend_bleed(card), bleed, W_MM + 6, H_MM + 6)
    prev = card.copy()
    prev.thumbnail((900, 1280), Image.Resampling.LANCZOS)
    prev.save(preview, "JPEG", quality=90)
    write_text(variant, OUT / f"{stem}.txt")
    shutil.copy2(png, PRINT / f"{stem}-300dpi.png")
    shutil.copy2(pdf, PRINT / f"{stem}-148x210.pdf")
    shutil.copy2(bleed, PRINT / f"{stem}-bleed-3mm.pdf")
    shutil.copy2(png, ART / f"back_{variant['id']}_{slug}.png")
    shutil.copy2(preview, ART / f"back_{variant['id']}_{slug}_preview.jpg")
    shutil.copy2(pdf, ART / f"back_{variant['id']}_{slug}.pdf")
    if FRONT_PDF.exists():
        duplex_path = PRINT / f"lasmart-2027-otkrytka-{variant['id']}.pdf"
        duplex(FRONT_PDF, pdf, duplex_path)
        shutil.copy2(duplex_path, ART / f"otkrytka_{variant['id']}.pdf")
    print("wrote", png.name, card.size)
    return png


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PRINT.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)

    thumbs: list[tuple[str, Image.Image]] = []
    first_pdf = None
    for variant in VARIANTS:
        card = compose(variant)
        png = export_variant(variant, card)
        thumbs.append((f"{variant['id'].upper()} · {variant['title']}", card))
        if first_pdf is None:
            shutil.copy2(png, ROOT / "lasmart-2027-back.png")
            pdf = OUT / f"lasmart-2027-back-{variant['id']}-{variant['slug']}.pdf"
            shutil.copy2(pdf, ROOT / "lasmart-2027-back.pdf")
            first_pdf = pdf

    compare_all = OUT / "lasmart-2027-back-compare.png"
    comparison(thumbs, compare_all, "Lasmart 2027 — тексты оборота")
    new_thumbs = [t for t in thumbs if t[0].startswith("V3") or t[0].startswith("V4") or t[0].startswith("V5")]
    compare_new = OUT / "lasmart-2027-back-compare-set2.png"
    comparison(new_thumbs, compare_new, "Lasmart 2027 — три новых текста оборота")
    shutil.copy2(compare_new, ART / "back_set2_compare.png")
    print("compare", compare_new)


if __name__ == "__main__":
    main()

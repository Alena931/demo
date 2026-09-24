#!/usr/bin/env python3
"""Деловая презентация: карта конкурентов Товароведа (5 слайдов)."""

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import nsmap, qn
from pptx.util import Emu, Inches, Pt
from lxml import etree

# --- palette (muted, readable) ---
BG = RGBColor(0xF3, 0xF1, 0xEC)
INK = RGBColor(0x2B, 0x36, 0x42)
MUTED = RGBColor(0x5C, 0x67, 0x72)
LINE = RGBColor(0xD6, 0xD0, 0xC6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NAVY = RGBColor(0x3A, 0x54, 0x66)
SAGE = RGBColor(0x5E, 0x6F, 0x64)
TAUPE = RGBColor(0x8A, 0x73, 0x58)
CLAY = RGBColor(0x8B, 0x5A, 0x4A)
ACCENT = RGBColor(0x4A, 0x6B, 0x7C)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def set_run(run, text, size=14, bold=False, color=INK, font="Calibri"):
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    run.font.italic = False


def add_textbox(slide, l, t, w, h, text, size=14, bold=False, color=INK, align=PP_ALIGN.LEFT, font="Calibri"):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    set_run(p.add_run() if p.runs else p.add_run(), text, size, bold, color, font)
    # pptx: first paragraph already has empty run sometimes — fix
    return box


def set_para(p, text, size=14, bold=False, color=INK, align=PP_ALIGN.LEFT, space_after=6):
    p.alignment = align
    p.space_after = Pt(space_after)
    p.clear()
    run = p.add_run()
    set_run(run, text, size, bold, color)
    return p


def fill_shape(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def stroke_shape(shape, color, pt=1):
    shape.line.color.rgb = color
    shape.line.width = Pt(pt)


def rect(slide, l, t, w, h, fill, stroke=None, radius=None):
    if radius:
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
        sh.adjustments[0] = radius
    else:
        sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    fill_shape(sh, fill)
    if stroke:
        stroke_shape(sh, stroke, 1)
    else:
        sh.line.fill.background()
    return sh


def oval(slide, l, t, w, h, fill):
    sh = slide.shapes.add_shape(MSO_SHAPE.OVAL, l, t, w, h)
    fill_shape(sh, fill)
    return sh


def text_in(shape, lines, valign=MSO_ANCHOR.TOP):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    try:
        shape.text_frame._txBody.bodyPr.set("anchor", "t" if valign == MSO_ANCHOR.TOP else "ctr")
    except Exception:
        pass
    first = True
    for item in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        text, size, bold, color, align, after = item
        p.alignment = align
        p.space_after = Pt(after)
        # clear existing
        if p.runs:
            p.clear()
        run = p.add_run()
        set_run(run, text, size, bold, color)
    return tf


def hyperlink_run(paragraph, url, size=10, color=ACCENT):
    run = paragraph.add_run()
    set_run(run, url, size, False, color)
    r = run._r
    rPr = r.get_or_add_rPr()
    # underline
    rPr.set("u", "sng")
    hlink = etree.SubElement(rPr, qn("a:hlinkClick"))
    # relationship will be added via pptx hyperlink API if possible
    return run


def add_link_box(slide, l, t, w, h, url, size=10):
    """Clickable text box with URL."""
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    set_run(run, url, size, False, ACCENT)
    run.font.underline = True
    try:
        run.hyperlink.address = url
    except Exception:
        pass
    return box


def footer(slide, n, total=5):
    bar = rect(slide, 0, Inches(7.28), SLIDE_W, Inches(0.22), NAVY)
    box = slide.shapes.add_textbox(Inches(0.5), Inches(7.28), Inches(10), Inches(0.22))
    tf = box.text_frame
    p = tf.paragraphs[0]
    run = p.add_run()
    set_run(run, "Ласмарт  ·  Товаровед  ·  карта конкурентов", 10, False, WHITE)
    num = slide.shapes.add_textbox(Inches(11.6), Inches(7.28), Inches(1.3), Inches(0.22))
    p = num.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    run = p.add_run()
    set_run(run, f"{n} / {total}", 10, False, WHITE)


def header(slide, kicker, title):
    rect(slide, 0, 0, SLIDE_W, Inches(0.08), NAVY)
    box = slide.shapes.add_textbox(Inches(0.55), Inches(0.22), Inches(12.2), Inches(0.28))
    p = box.text_frame.paragraphs[0]
    run = p.add_run()
    set_run(run, kicker.upper(), 11, True, SAGE)
    box = slide.shapes.add_textbox(Inches(0.55), Inches(0.46), Inches(12.2), Inches(0.5))
    p = box.text_frame.paragraphs[0]
    run = p.add_run()
    set_run(run, title, 26, True, INK)


def bg(slide):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = BG


def icon_box(slide, l, t, color, glyph="■"):
    """Small square with schematic mark."""
    s = rect(slide, l, t, Inches(0.42), Inches(0.42), color, radius=0.15)
    tf = s.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    set_run(run, glyph, 14, True, WHITE)
    try:
        s.text_frame._txBody.bodyPr.set("anchor", "ctr")
    except Exception:
        pass
    return s


def build():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    # ========== SLIDE 1 ==========
    s = prs.slides.add_slide(blank)
    bg(s)
    header(s, "Конкурентная карта", "Три группы рядом с Товароведом")
    sub = s.shapes.add_textbox(Inches(0.55), Inches(1.05), Inches(12.2), Inches(0.4))
    p = sub.text_frame.paragraphs[0]
    run = p.add_run()
    set_run(run, "Не «кто ещё пишет карточки», а кто пересекается по методу, словам или результату на полке.", 14, False, MUTED)

    # center node
    cx, cy = Inches(6.15), Inches(3.15)
    hub = oval(s, cx, cy, Inches(1.05), Inches(1.05), NAVY)
    tf = hub.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    set_run(run, "ТВ", 16, True, WHITE)
    try:
        hub.text_frame._txBody.bodyPr.set("anchor", "ctr")
    except Exception:
        pass
    cap = s.shapes.add_textbox(Inches(5.55), Inches(4.22), Inches(2.25), Inches(0.35))
    p = cap.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    set_run(run, "Товаровед → SP", 11, True, NAVY)

    groups = [
        (Inches(0.5), SAGE, "01", "Похожий метод",
         "Патчи 1С: нормализация НСИ\nи веб-заполнение полей.",
         "Клиенты SP это не пробовали"),
        (Inches(4.55), TAUPE, "02", "Похожие слова",
         "PIM / маркетплейсы.\n«Полка» — digital shelf, не планограмма.",
         "Не оппонент в сделках SP"),
        (Inches(8.6), CLAY, "03", "Тот же результат",
         "Габариты и фото для выкладки.\nДругой путь: лаборатория или свой планограммер.",
         "Не «прямой ИИ-агент»"),
    ]
    cards_y = Inches(4.95)
    for x, col, num, title, body, note in groups:
        rect(s, x, cards_y, Inches(3.85), Inches(2.12), WHITE, LINE, 0.08)
        rect(s, x, cards_y, Inches(0.1), Inches(2.12), col)
        nbox = s.shapes.add_textbox(x + Inches(0.28), cards_y + Inches(0.14), Inches(3.4), Inches(0.28))
        p = nbox.text_frame.paragraphs[0]
        run = p.add_run()
        set_run(run, f"Группа {num}", 11, True, col)
        tbox = s.shapes.add_textbox(x + Inches(0.28), cards_y + Inches(0.42), Inches(3.4), Inches(0.32))
        p = tbox.text_frame.paragraphs[0]
        run = p.add_run()
        set_run(run, title, 16, True, INK)
        bbox = s.shapes.add_textbox(x + Inches(0.28), cards_y + Inches(0.78), Inches(3.4), Inches(0.75))
        tf = bbox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        run = p.add_run()
        set_run(run, body, 12, False, MUTED)
        nbox2 = s.shapes.add_textbox(x + Inches(0.28), cards_y + Inches(1.55), Inches(3.4), Inches(0.4))
        p = nbox2.text_frame.paragraphs[0]
        run = p.add_run()
        set_run(run, note, 11, True, INK)

    # three nodes around the hub
    nodes = [
        (Inches(1.35), Inches(2.15), SAGE, "01  метод"),
        (Inches(9.55), Inches(2.15), TAUPE, "02  слова"),
        (Inches(5.45), Inches(2.15), CLAY, "03  результат"),
    ]
    for nx, ny, col, label in nodes:
        nd = oval(s, nx, ny, Inches(2.4), Inches(0.7), WHITE)
        stroke_shape(nd, col, 1.5)
        tf = nd.text_frame
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        set_run(run, label, 13, True, col)
        try:
            nd.text_frame._txBody.bodyPr.set("anchor", "ctr")
        except Exception:
            pass

    footer(s, 1)

    # ========== SLIDE 2 ==========
    s = prs.slides.add_slide(blank)
    bg(s)
    header(s, "Группа 01  ·  похожий метод", "Патчи 1С: заполняют карточку, не полку")
    sub = s.shapes.add_textbox(Inches(0.55), Inches(1.02), Inches(12.2), Inches(0.35))
    p = sub.text_frame.paragraphs[0]
    run = p.add_run()
    set_run(run, "Жест похож: взять данные снаружи и дописать карточку. Результат остаётся в 1С, не в Space Planner.", 14, False, MUTED)

    # two product cards
    left = Inches(0.5)
    right = Inches(6.85)
    y = Inches(1.5)
    w = Inches(5.95)
    h = Inches(4.55)

    def product_card(slide, x, color, tag, name, role, bullets, url, price=None):
        rect(slide, x, y, w, h, WHITE, LINE, 0.06)
        rect(slide, x, y, w, Inches(0.08), color)
        tagb = slide.shapes.add_textbox(x + Inches(0.35), y + Inches(0.22), Inches(5.2), Inches(0.28))
        p = tagb.text_frame.paragraphs[0]
        run = p.add_run()
        set_run(run, tag.upper(), 11, True, color)
        nb = slide.shapes.add_textbox(x + Inches(0.35), y + Inches(0.5), Inches(5.2), Inches(0.4))
        p = nb.text_frame.paragraphs[0]
        run = p.add_run()
        set_run(run, name, 20, True, INK)
        rb = slide.shapes.add_textbox(x + Inches(0.35), y + Inches(0.92), Inches(5.2), Inches(0.55))
        tf = rb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        run = p.add_run()
        set_run(run, role, 13, False, MUTED)
        # куда попадает результат — две ячейки, без «агента»
        fy = y + Inches(1.52)
        a = rect(slide, x + Inches(0.35), fy, Inches(2.45), Inches(0.78), RGBColor(0xE8, 0xE4, 0xDC), radius=0.1)
        tf = a.text_frame
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        set_run(run, "пишут в 1С", 13, True, NAVY)
        try:
            a.text_frame._txBody.bodyPr.set("anchor", "ctr")
        except Exception:
            pass
        b = rect(slide, x + Inches(3.0), fy, Inches(2.55), Inches(0.78), RGBColor(0xEB, 0xE4, 0xDF), radius=0.1)
        tf = b.text_frame
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        set_run(run, "в Space Planner — нет", 13, True, CLAY)
        try:
            b.text_frame._txBody.bodyPr.set("anchor", "ctr")
        except Exception:
            pass
        by = fy + Inches(0.95)
        bb = slide.shapes.add_textbox(x + Inches(0.35), by, Inches(5.2), Inches(1.5))
        tf = bb.text_frame
        tf.word_wrap = True
        first = True
        for b in bullets:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.space_after = Pt(4)
            run = p.add_run()
            set_run(run, "▸  " + b, 13, False, INK)
        add_link_box(slide, x + Inches(0.35), y + h - Inches(0.55), Inches(5.2), Inches(0.4), url, 10)
        if price:
            pb = slide.shapes.add_textbox(x + Inches(0.35), y + h - Inches(0.85), Inches(5.2), Inches(0.28))
            p = pb.text_frame.paragraphs[0]
            run = p.add_run()
            set_run(run, price, 12, True, NAVY)

    product_card(
        s, left, SAGE, "НСИ, не габариты с полки",
        "MBS Нормализатор НСИ",
        "Дубли, названия, классификация. Веб-габариты единицы выкладки не собирает.",
        ["метод: нормализация справочника в 1С", "не facing WxHxD, не фото для планограммы"],
        "https://mbsgroup.ru/ai/com/ii-agent-normalizator-nsi/",
    )
    product_card(
        s, right, NAVY, "ближайший жест заполнения",
        "Infostart «Оперативное заполнение»",
        "Веб → описание, фото, вес/объём/длина/площадь в 1С. Не единица выкладки.",
        ["результат в 1С, не в SP", "логистические меры ≠ WxHxD facing"],
        "https://infostart.ru/marketplace/2667216/",
        "48 800 ₽ / мес + пакеты запросов",
    )
    footer(s, 2)

    # ========== SLIDE 3 ==========
    s = prs.slides.add_slide(blank)
    bg(s)
    header(s, "Группа 02  ·  похожие слова", "PIM и маркетплейсы — не полка магазина")
    sub = s.shapes.add_textbox(Inches(0.55), Inches(1.02), Inches(12.2), Inches(0.38))
    p = sub.text_frame.paragraphs[0]
    run = p.add_run()
    set_run(run, "Совпадают слова «карточка», «атрибуты», «полка». Не совпадает работа: единица выкладки в мм для планограммы.", 14, False, MUTED)

    items = [
        (SAGE, "SelSup", "OMS WB / Ozon",
         "Формализатор разбирает уже существующий текст. Габариты = транспортная упаковка, не facing.",
         "https://selsup.ru/",
         "не в сделках SP"),
        (TAUPE, "BrandQuad", "PIM / digital shelf",
         "Контент для сайта и ритейл-медиа. Слово «полка» — digital shelf. Риск путаницы в разговоре.",
         "https://brandquad.ru/products/pim-systema/",
         "~360,9 млн ₽  ·  2025"),
        (NAVY, "Compo PIM", "PIM-платформа",
         "Управление контентом товара. Не паспорт полки и не загрузка в Space Planner.",
         "https://www.compo.ru/products/pim/",
         "~110 млн ₽  ·  вся компания, 2025"),
    ]
    x = Inches(0.5)
    for col, name, role, body, url, foot in items:
        rect(s, x, Inches(1.55), Inches(3.95), Inches(5.15), WHITE, LINE, 0.06)
        rect(s, x, Inches(1.55), Inches(3.95), Inches(0.08), col)
        # schematic: two boxes "site" vs "shelf" with X
        icon_box(s, x + Inches(0.3), Inches(1.8), col, "PIM")
        # actually glyph too long - use simple oval
        tb = s.shapes.add_textbox(x + Inches(0.3), Inches(1.82), Inches(3.35), Inches(0.28))
        p = tb.text_frame.paragraphs[0]
        run = p.add_run()
        set_run(run, role.upper(), 11, True, col)
        nb = s.shapes.add_textbox(x + Inches(0.3), Inches(2.15), Inches(3.35), Inches(0.45))
        p = nb.text_frame.paragraphs[0]
        run = p.add_run()
        set_run(run, name, 20, True, INK)

        # mini diagram site vs shelf
        a = rect(s, x + Inches(0.3), Inches(2.75), Inches(1.5), Inches(0.85), RGBColor(0xE8, 0xE4, 0xDC), radius=0.1)
        tf = a.text_frame
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        set_run(run, "сайт / MP\nконтент", 11, True, MUTED)
        try:
            a.text_frame._txBody.bodyPr.set("anchor", "ctr")
        except Exception:
            pass
        b = rect(s, x + Inches(2.1), Inches(2.75), Inches(1.5), Inches(0.85), RGBColor(0xEB, 0xE4, 0xDF), radius=0.1)
        tf = b.text_frame
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        set_run(run, "полка мм\nнет", 11, True, CLAY)
        try:
            b.text_frame._txBody.bodyPr.set("anchor", "ctr")
        except Exception:
            pass

        bb = s.shapes.add_textbox(x + Inches(0.3), Inches(3.8), Inches(3.35), Inches(1.55))
        tf = bb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        run = p.add_run()
        set_run(run, body, 13, False, INK)

        fb = s.shapes.add_textbox(x + Inches(0.3), Inches(5.45), Inches(3.35), Inches(0.4))
        p = fb.text_frame.paragraphs[0]
        run = p.add_run()
        set_run(run, foot, 12, True, NAVY)

        add_link_box(s, x + Inches(0.3), Inches(5.95), Inches(3.35), Inches(0.55), url, 10)
        x += Inches(4.15)

    footer(s, 3)

    # ========== SLIDE 4 ==========
    s = prs.slides.add_slide(blank)
    bg(s)
    header(s, "Группа 03  ·  тот же результат", "Габариты для выкладки — другим путём")
    sub = s.shapes.add_textbox(Inches(0.55), Inches(1.02), Inches(12.2), Inches(0.38))
    p = sub.text_frame.paragraphs[0]
    run = p.add_run()
    set_run(run, "Нужны WxHxD и фото facing. Добывают лабораторией, своей базой или внутри своего планограммера — не ИИ-агентом в SP.", 14, False, MUTED)

    g3 = [
        (Inches(0.5), Inches(1.52), CLAY, "Listex", "физическая лаборатория",
         "Cubiscan + съёмка, дни на партию. API в ABM / PlanoHero.",
         "https://listex.info/"),
        (Inches(6.85), Inches(1.52), NAVY, "Astor", "планограммы + своя БД",
         "Конкурент SP. База габаритов клиентов; качество слабое (по продажам SP).",
         "https://astorsoft.ru/products/rs-shelfspace/"),
        (Inches(0.5), Inches(4.22), SAGE, "ABM Shelf", "процесс выкладки",
         "Габариты из rollout или Listex. Не отдельный ИИ-заполнитель карточки.",
         "https://abmcloud.com/abm-soft/abm-shelf/"),
        (Inches(6.85), Inches(4.22), TAUPE, "PlanoHero", "класс Space Planner",
         "Часто берёт фото и WHD у Listex. Lite $199 / мес.",
         "https://planohero.com/ru/create-planograms/"),
    ]
    for x, y, col, name, role, body, url in g3:
        rect(s, x, y, Inches(5.95), Inches(2.52), WHITE, LINE, 0.06)
        rect(s, x, y, Inches(0.1), Inches(2.52), col)
        # schematic circle
        o = oval(s, x + Inches(0.35), y + Inches(0.28), Inches(0.48), Inches(0.48), col)
        tb = s.shapes.add_textbox(x + Inches(0.98), y + Inches(0.22), Inches(4.6), Inches(0.32))
        p = tb.text_frame.paragraphs[0]
        run = p.add_run()
        set_run(run, name, 18, True, INK)
        rb = s.shapes.add_textbox(x + Inches(0.98), y + Inches(0.52), Inches(4.6), Inches(0.28))
        p = rb.text_frame.paragraphs[0]
        run = p.add_run()
        set_run(run, role, 12, False, col)
        bb = s.shapes.add_textbox(x + Inches(0.35), y + Inches(0.95), Inches(5.25), Inches(0.9))
        tf = bb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        run = p.add_run()
        set_run(run, body, 13, False, INK)
        add_link_box(s, x + Inches(0.35), y + Inches(1.9), Inches(5.25), Inches(0.45), url, 10)

    footer(s, 4)

    # ========== SLIDE 5 ==========
    s = prs.slides.add_slide(blank)
    bg(s)
    header(s, "Вывод", "Поля пересекаются. Карточки для выкладки — нет")
    sub = s.shapes.add_textbox(Inches(0.55), Inches(1.02), Inches(12.2), Inches(0.4))
    p = sub.text_frame.paragraphs[0]
    run = p.add_run()
    set_run(run, "Никто из групп 1–2 не готовит паспорт полки. Группа 3 получает WxHxD иначе — лабораторией или своим стеком планограмм.", 14, False, MUTED)

    # three "not this" + one "this"
    rows = [
        (SAGE, "01", "Патчи 1С", "карточка в учёте", "не facing, не SP"),
        (TAUPE, "02", "PIM / MP", "контент и отгрузки", "не единица выкладки"),
        (CLAY, "03", "Лаб / свой SP", "габариты есть", "другой метод и канал"),
    ]
    x = Inches(0.5)
    for col, num, title, mid, end in rows:
        rect(s, x, Inches(1.6), Inches(3.95), Inches(2.85), WHITE, LINE, 0.06)
        oval(s, x + Inches(1.7), Inches(1.82), Inches(0.55), Inches(0.55), col)
        nb = s.shapes.add_textbox(x + Inches(1.7), Inches(1.9), Inches(0.55), Inches(0.42))
        p = nb.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        set_run(run, num, 12, True, WHITE)
        tb = s.shapes.add_textbox(x + Inches(0.2), Inches(2.5), Inches(3.55), Inches(0.4))
        p = tb.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        set_run(run, title, 16, True, INK)
        mb = s.shapes.add_textbox(x + Inches(0.25), Inches(2.95), Inches(3.45), Inches(0.7))
        tf = mb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        set_run(run, mid + "\n" + end, 13, False, MUTED)
        x += Inches(4.15)

    # bottom conclusion bar
    rect(s, Inches(0.5), Inches(4.7), Inches(12.3), Inches(2.15), WHITE, LINE, 0.05)
    rect(s, Inches(0.5), Inches(4.7), Inches(0.12), Inches(2.15), NAVY)
    t = s.shapes.add_textbox(Inches(0.9), Inches(4.9), Inches(11.6), Inches(0.4))
    p = t.text_frame.paragraphs[0]
    run = p.add_run()
    set_run(run, "Товаровед", 18, True, NAVY)
    t = s.shapes.add_textbox(Inches(0.9), Inches(5.35), Inches(11.6), Inches(1.2))
    tf = t.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    set_run(run, "Карточка, с которой можно собрать качественную планограмму: WxHxD единицы выкладки, фото facing, штрихкод, атрибуты — и загрузка в Space Planner.", 15, False, INK)
    p = tf.add_paragraph()
    p.space_before = Pt(8)
    run = p.add_run()
    set_run(run, "SP — канал. Задача — паспорт полки, не «почистить весь 1С».", 14, True, MUTED)

    footer(s, 5)

    out = "/workspace/Tovaroved_karta_konkurentov.pptx"
    prs.save(out)
    print(out)


if __name__ == "__main__":
    build()

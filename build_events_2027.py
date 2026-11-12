#!/usr/bin/env python3
"""Restyle the 2027 events calendar: one font, three status colours, add missing prices."""
from copy import copy
from pathlib import Path
import re
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, Protection

SRC = "/workspace/plan_meropriyatiy_2027_src.xlsx"
OUT = "/workspace/Plan_meropriyatiy_2027.xlsx"
ART = "/opt/cursor/artifacts/Plan_meropriyatiy_2027.xlsx"

TEAL = "A2C4C9"
OK = "D9EAD3"
REVIEW = "FFF2CC"
NO = "F4CCCC"
LINK = "0563C1"

FILL_TEAL = PatternFill("solid", fgColor=TEAL)
FILL_OK = PatternFill("solid", fgColor=OK)
FILL_REVIEW = PatternFill("solid", fgColor=REVIEW)
FILL_NO = PatternFill("solid", fgColor=NO)
FILL_WHITE = PatternFill("solid", fgColor="FFFFFF")

FONT = Font(name="Times New Roman", size=11, color="000000")
FONT_BOLD = Font(name="Times New Roman", size=11, bold=True, color="000000")
WRAP = Alignment(wrap_text=True, vertical="top", horizontal="left")
CENTER = Alignment(wrap_text=True, vertical="center", horizontal="center")
THIN = Border(
    left=Side(style="thin", color="D0D0D0"),
    right=Side(style="thin", color="D0D0D0"),
    top=Side(style="thin", color="D0D0D0"),
    bottom=Side(style="thin", color="D0D0D0"),
)
UNLOCK = Protection(locked=False)

AGREED = {"FFB6D7A8", "FFD9EAD3"}
REVIEW_SET = {"FFFFF2CC", "FFFFD966", "FFFFE599"}
NO_SET = {"FFEA9999", "FFD5A6BD", "FFC27BA0", "FFFF0000", "FFE06666"}
TEAL_SET = {"FF00FFFF", "FF00FF00", "FFA2C4C9"}
BLUE_SET = {"FF6FA8DC"}
EMPTY_SET = {
    "00000000",
    "FFFFFFFF",
    "FF000000",
    "FFF3F3F3",
    "FFF7F7F7",
    "00F3F3F3",
    "00F7F7F7",
    "00FFFFFF",
}

MONEY_RE = re.compile(
    r"(\d[\d\s]*\s*(руб|₽|\$|€|юан|долл)|бесплатн|\d+\s*к\b)",
    re.I,
)


def rgb_of(cell):
    if not cell.fill or not cell.fill.patternType:
        return None
    col = cell.fill.fgColor
    if col is None:
        return None
    rgb = getattr(col, "rgb", None)
    if rgb is None:
        return None
    return str(rgb).upper()


def mapped_fill(rgb, row):
    """Keep only header teal and three status colours. Empty week cells stay white."""
    if not rgb or rgb in EMPTY_SET:
        if row <= 2:
            return FILL_TEAL
        return FILL_WHITE
    if rgb in AGREED:
        return FILL_OK
    if rgb in REVIEW_SET or rgb in BLUE_SET:
        return FILL_REVIEW
    if rgb in NO_SET:
        return FILL_NO
    if rgb in TEAL_SET:
        return FILL_TEAL
    if row <= 2:
        return FILL_TEAL
    return FILL_WHITE


def apply_font(cell, bold=None):
    is_link = bool(cell.hyperlink)
    want_bold = cell.font.bold if bold is None else bold
    if is_link:
        cell.font = Font(
            name="Times New Roman",
            size=11,
            bold=bool(want_bold),
            color=LINK,
            underline="single",
        )
    elif want_bold:
        cell.font = FONT_BOLD
    else:
        cell.font = FONT
    cell.protection = UNLOCK


# Last published figure. Year is in the sentence; 2027 is not invented.
COST_RULES = [
    (
        "Digital Transformation Day",
        "Стоимость: на 2027 не публиковали. По данным TAdviser в 2025 заказчик бесплатно "
        "(после подтверждения), вендор 12 500 ₽ за человека.",
    ),
    (
        "IT Retail",
        "Стоимость: на 2027 не публиковали. По 2026 на all-events указано 25 000 ₽.",
    ),
    (
        "Данные+ИИ",
        "Стоимость: на 2027 не публиковали. По форуму «Данные + ИИ» 2026 "
        "(«Открытые системы»): ИТ-компании 35 900–39 900 ₽, корпоративный сектор "
        "20 900–25 900 ₽, онлайн 12 900 ₽.",
    ),
    (
        "Data Fusion",
        "Стоимость: на 2027 не публиковали. Конференция 2026 была бесплатной "
        "(data-fusion.ru: «Участие бесплатно»).",
    ),
    (
        "Russian Retail Show",
        "Стоимость: на 2027 не публиковали. По 2026 для ритейла, e-com и FMCG "
        "вход бесплатный. Для ИТ-поставщика отдельного посетительского прайса нет — "
        "обычно стенд или партнёрство.",
    ),
    (
        "BI TECH",
        "Стоимость: на 2027 не публиковали. По конференции «Технологии бизнес-аналитики» "
        "2026 («Открытые системы», та же дата, что у BI TECH): ИТ-компании 20 000–26 000 ₽, "
        "корпоративный сектор 8 500–12 500 ₽, онлайн 7 900 ₽.",
    ),
    (
        "DIY&Household Retail 2027",
        "Стоимость уже на 2027 (diyretailrussia.ru): партнёры рынка 114 000 ₽ без НДС "
        "(ранняя цена до 30 декабря — 81 000 ₽ без НДС, с НДС 98 820 ₽); сети DIY "
        "46 000 ₽ без НДС (ранняя 41 000, с НДС 50 020 ₽).",
    ),
    (
        "саммит DIY&Household Retail 2026",
        "Стоимость: по 2026 агрегатор all-events писал «от 42 000 ₽». На 2027 у того же "
        "саммита открыта регистрация: партнёры 114 000 ₽ без НДС, сети 46 000 ₽ без НДС.",
    ),
    (
        "Конвент Мир торговли",
        "Стоимость: точную цену именно на 2027 не нашли. В одной из программ конвента "
        "участие компании — 90 000 ₽ (стеллаж, 2 бейджа, переговоры).",
    ),
    (
        "Мир торговли 2026",
        "Стоимость: точную цену именно на этот заезд не нашли. В одной из программ "
        "конвента «Мир торговли» участие компании — 90 000 ₽ (стеллаж, 2 бейджа).",
    ),
    (
        "BEE-Fashion",
        "Стоимость: на 2027 не публиковали. Форум ноября 2026: оба дня 8 000 ₽, "
        "один день 5 000 ₽. Выставка BEE-TOGETHER для посетителей по регистрации бесплатно.",
    ),
    (
        "Неделя Российского Ритейла",
        "Стоимость: на 2027 не публиковали. По 2026: «Стандарт» 80 000 ₽ все дни, "
        "«Премиум» 190 000 ₽; для сотрудников торговых сетей — бесплатный спецпакет. "
        "Стенд: взнос экспонента 50 000 ₽ + площадь 35 000–65 000 ₽/м², без НДС 5%.",
    ),
    (
        "Зеленого Креста",
        "Стоимость: по прайсу «Зелёного Креста» остальные компании 50 000 ₽ за делегата; "
        "аптечные сети — первый и второй бесплатно. Отдельного нового прайса на 2027 нет.",
    ),
    (
        "Зеленый Крест",
        "Стоимость: остальные компании 50 000 ₽ за делегата; аптечные сети — первый и второй "
        "бесплатно.",
    ),
    (
        "CDO/CDTO",
        "Стоимость: по 2026 от 49 000 ₽; CIO / CDO / CDTO / CISO / CTO — бесплатно после "
        "подтверждения. На 2027 не публиковали.",
    ),
    (
        "FOOD-MARKETING FORUM",
        "Стоимость: по 2026 агрегаторы пишут 45 000–100 000 ₽. На 2027 не публиковали.",
    ),
    (
        "Презентация Российского Ритейл",
        "Стоимость: отдельного прайса нет, обычно по приглашению.",
    ),
    (
        "Бизнес-завтрак",
        "Стоимость: своё мероприятие, входного билета нет.",
    ),
    (
        "Корпоратив",
        "Стоимость: внутреннее, публичной цены нет.",
    ),
    (
        "Вебинар",
        "Стоимость: своё или партнёрский вебинар, отдельного входного билета обычно нет.",
    ),
    (
        "Спортивное мероприятие",
        "Стоимость: внутреннее, публичной цены нет.",
    ),
    (
        "Развлекательн",
        "Стоимость: внутреннее, публичной цены нет.",
    ),
    (
        "Мерч",
        "Стоимость: внутреннее (закупка), публичного «билета» нет.",
    ),
    (
        "Управление персональными данными",
        "Стоимость: своё или партнёрский вебинар, отдельного входного билета обычно нет.",
    ),
    (
        "Скрытые проблемы в СУБД",
        "Стоимость: своё или партнёрский вебинар, отдельного входного билета обычно нет.",
    ),
    (
        "Central Asia Trade Forum",
        "Стоимость: открытого прайса нет. В 2026 билеты уже купили, форум отменили.",
    ),
    (
        "Алена З. просила",
        "Стоимость: на странице retailacademy.info/diy26 (даты 20–21 ноября, как в таблице) "
        "для розничных компаний 145 000 ₽ + НДС 5%. Проживание в кампусе отдельно. "
        "Для поставщиков на более ранней странице той же сессии было 168 300 ₽.",
    ),
]


def cost_for(name):
    if not name:
        return None
    n = str(name)
    for key, text in COST_RULES:
        if key.lower() in n.lower():
            return text
    return None


def already_has_price(notes):
    t = str(notes or "")
    if MONEY_RE.search(t):
        return True
    low = t.lower()
    if "стоим" in low and "не публик" not in low and "нет" not in low:
        return True
    return False


def inject_cost(cell_name, cell_notes, force=False, for_2026=False):
    extra = cost_for(cell_name.value)
    if not extra:
        return
    if for_2026:
        extra = extra.replace("Стоимость: на 2027 не публиковали. ", "Стоимость: ")
    notes = cell_notes.value or ""
    if not force and already_has_price(notes):
        return
    if str(notes).strip():
        cell_notes.value = extra + "\n\n" + str(notes).lstrip()
    else:
        cell_notes.value = extra


def restyle_sheet(ws, has_notes_col=True, for_2026=False):
    max_row, max_col = ws.max_row, ws.max_column

    for r in range(1, max_row + 1):
        for c in range(1, max_col + 1):
            cell = ws.cell(r, c)
            apply_font(cell)
            cell.fill = mapped_fill(rgb_of(cell), r)
            cell.border = THIN
            cell.protection = UNLOCK
            if c <= 2:
                cell.alignment = WRAP
            elif r <= 2:
                cell.alignment = CENTER
            else:
                cell.alignment = Alignment(
                    wrap_text=True, vertical="center", horizontal="center"
                )

    for c in range(1, max_col + 1):
        ws.cell(1, c).fill = FILL_TEAL
        ws.cell(1, c).font = FONT_BOLD
        ws.cell(2, c).fill = FILL_TEAL
        ws.cell(2, c).font = FONT_BOLD

    if has_notes_col:
        for r in range(3, max_row + 1):
            name = str(ws.cell(r, 1).value or "")
            force = "Алена З. просила" in name
            inject_cost(ws.cell(r, 1), ws.cell(r, 2), force=force, for_2026=for_2026)
            ws.cell(r, 2).alignment = WRAP

    for r in range(3, max_row + 1):
        a = ws.cell(r, 1)
        text = (a.value or "") if isinstance(a.value, str) else ""
        if text.startswith("Мероприятия ") or text.startswith("Условные"):
            for c in range(1, min(3, max_col) + 1):
                ws.cell(r, c).fill = FILL_TEAL
                ws.cell(r, c).font = FONT_BOLD

    for mr in ws.merged_cells.ranges:
        master = ws.cell(mr.min_row, mr.min_col)
        for r in range(mr.min_row, mr.max_row + 1):
            for c in range(mr.min_col, mr.max_col + 1):
                cell = ws.cell(r, c)
                cell.font = copy(master.font)
                cell.fill = copy(master.fill)
                cell.alignment = copy(master.alignment)
                cell.protection = UNLOCK

    ws.sheet_properties.tabColor = TEAL
    ws.sheet_view.showGridLines = False
    ws.row_dimensions[1].height = 22
    ws.row_dimensions[2].height = 18


def unmerge_overlapping(ws, min_row, max_row, min_col, max_col):
    to_drop = []
    for mr in list(ws.merged_cells.ranges):
        if mr.max_row < min_row or mr.min_row > max_row:
            continue
        if mr.max_col < min_col or mr.min_col > max_col:
            continue
        to_drop.append(str(mr))
    for ref in to_drop:
        ws.unmerge_cells(ref)


def rewrite_legend(ws, start_row):
    unmerge_overlapping(ws, start_row, start_row + 5, 1, 12)
    labels = [
        (start_row, "Условные обозначения", FONT_BOLD, FILL_TEAL),
        (start_row + 1, "Согласовано", FONT, FILL_OK),
        (start_row + 2, "На рассмотрении", FONT, FILL_REVIEW),
        (start_row + 3, "Не едем / не согласовано", FONT, FILL_NO),
    ]
    for r, text, font, fill in labels:
        for c in range(1, 8):
            cell = ws.cell(r, c)
            cell.fill = fill
            cell.font = font if c == 1 else FONT
            cell.border = THIN
            cell.alignment = WRAP
            cell.value = text if c == 1 else None
    note_r = start_row + 4
    ws.cell(note_r, 1).value = (
        "Шрифт один — Times New Roman 11. Цвета только эти три. "
        "Если в «О главном» не было цены, дописали последний открытый прайс "
        "и год, откуда он. На 2027 цифру не выдумывали."
    )
    ws.cell(note_r, 1).font = FONT
    ws.cell(note_r, 1).alignment = WRAP
    ws.merge_cells(start_row=note_r, start_column=1, end_row=note_r, end_column=8)
    ws.row_dimensions[note_r].height = 36


def clear_old_format_legend(ws, rows, cols):
    unmerge_overlapping(ws, min(rows), max(rows), min(cols), max(cols))
    for r in rows:
        for c in cols:
            cell = ws.cell(r, c)
            val = str(cell.value or "")
            if val.startswith("Формат") or val in (
                "Внутрнее мероприятие",
                "Внутреннее мероприятие",
                "Внешнее мероприятие",
                "Вебинар",
            ):
                cell.value = None
                cell.fill = FILL_WHITE


def main():
    wb = load_workbook(SRC)

    ws26 = wb["Сквозной график мероприятий 202"]
    ws26.title = "График 2026"
    restyle_sheet(ws26, has_notes_col=True, for_2026=True)
    clear_old_format_legend(ws26, [42, 43, 44, 45], range(4, 12))
    rewrite_legend(ws26, 42)
    ws26.column_dimensions["A"].width = 42
    ws26.column_dimensions["B"].width = 72

    ws27 = wb["Лист6"]
    ws27.title = "План 2027"
    restyle_sheet(ws27, has_notes_col=True)
    rewrite_legend(ws27, 48)
    for r in range(3, 44):
        if ws27.cell(r, 2).value:
            ws27.row_dimensions[r].height = min(
                96, 36 + len(str(ws27.cell(r, 2).value)) // 18
            )
    ws27.column_dimensions["A"].width = 42
    ws27.column_dimensions["B"].width = 72

    ws_hr = wb["Для Ани HR"]
    ws_hr.title = "HR 2026"
    restyle_sheet(ws_hr, has_notes_col=False)
    clear_old_format_legend(ws_hr, [33, 34, 35, 36], range(3, 12))
    rewrite_legend(ws_hr, 33)

    order = ["План 2027", "График 2026", "HR 2026"]
    for i, name in enumerate(order):
        wb.move_sheet(name, offset=i - wb.sheetnames.index(name))

    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(ART).parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    Path(ART).write_bytes(Path(OUT).read_bytes())
    print("saved", OUT)
    print("sheets", wb.sheetnames)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""FMCG РФ, срез сентябрь 2026. Только столбцы со скриншота.
В таблицах — только строки с хотя бы одной раскрытой цифрой 2025.
Ничего не выдумано; пустые региональные заглушки не добавляются."""
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule
from copy import copy
from pathlib import Path

OUT = "/workspace/FMCG_RF_sentyabr_2026.xlsx"
ART = "/opt/cursor/artifacts/FMCG_RF_sentyabr_2026.xlsx"
ND = None

# name, typ, rev, yoy, profit, debt, stores_or_plants, share, inside_group
# inside_group=True → бренд/юрлицо внутри уже учтённой группы, не суммировать

CHAINS = [
    # --- независимые операторы, по выручке 2025 ---
    ("X5 Group (Пятёрочка, Перекрёсток, Чижик)", "у дома / супер / хард-дискаунтер / e-grocery",
     4642.0, 18.8, 94.8, 228.5, 29790, 16.6, False),
    ("Магнит (вкл. Дикси, Самбери, Азбука вкуса)", "у дома / супер / гипер / косметик / e-com",
     3509.2, 15.3, -16.6, 496.0, 33440, 12.3, False),
    ("Mercury Retail (Красное & Белое, Бристоль)", "алкоголь / у дома",
     1660.0, 20.0, 54.5, ND, 28000, ND, False),
    ("Группа Лента (Гипер/Супер Лента, Монетка, Улыбка радуги, Реми)", "гипер / супер / у дома / дрогери",
     1103.7, 24.2, 38.2, 48.8, 6760, ND, False),
    ("Светофор / Маяк (ГК Торгсервис)", "хард-дискаунтер",
     394.43, -3.0, 5.8, ND, 2405, ND, False),
    ("ВкусВилл", "у дома / dark store / e-grocery",
     358.6, 9.7, 6.6, ND, 1973, ND, False),
    ("Fix Price", "value-ритейл, смешанный FMCG",
     313.3, 4.3, 11.18, ND, 7818, ND, False),
    ("Самокат", "e-grocery / dark store",
     279.3, 12.3, ND, ND, 2400, ND, False),
    ("METRO Россия", "cash&carry / гипер",
     260.3, 5.0, 4.4, ND, 91, ND, False),
    ("АШАН Ритейл Россия", "гипер / супер",
     250.0, -10.0, ND, ND, 231, ND, False),
    ("Ozon + Ozon Fresh", "e-grocery / маркетплейс",
     207.2, 61.1, ND, ND, ND, ND, False),
    ("Яндекс Лавка", "e-grocery / dark store",
     203.1, 42.4, ND, ND, 716, ND, False),
    ("ГК О'КЕЙ / Да!", "гипер продан / дискаунтер Да!",
     196.0, -11.0, 14.3, ND, ND, ND, False),
    ("ТС Победа / Гулливер / Народный амбар (ТК Лето)", "у дома / супер, Поволжье",
     176.0, 26.0, 0.2, ND, ND, ND, False),
    ("Ярче! (Камелот-А, Томск)", "у дома / супер, Сибирь",
     168.3, 28.0, -4.0, ND, ND, ND, False),
    ("Гиперглобус (Globus)", "гипер",
     165.6, 5.4, 7.4, ND, 20, ND, False),
    ("Верный (Союз Святого Иоанна Воина)", "у дома, ЦФО",
     154.4, 12.7, 0.0214, ND, 1000, ND, False),
    ("SPAR Миддл Волга (SPAR, EUROSPAR)", "супер / у дома",
     136.3, 6.1, 0.229, ND, 142, ND, False),
    ("Мария-Ра (Розница К-1)", "у дома / супер, Сибирь",
     127.6, 6.0, 2.7, ND, 1303, ND, False),
    ("Ермолино (оценка INFOLine, производство + своя розница)", "у дома / производство+розница",
     111.1, ND, ND, ND, 3005, ND, False),
    ("ГК Командор (Командор, Аллея, Хороший)", "супер / гипер / дискаунтер, Красноярск",
     100.0, 12.0, 1.7, ND, 477, ND, False),
    ("Винлаб (ПАО ВинЛаб / Novabev)", "алкоголь",
     95.1, 9.0, 3.5, -6.5, 2175, ND, False),
    ("Находка (ООО Табыш)", "хард-дискаунтер, Поволжье",
     81.7, 22.8, ND, ND, 370, ND, False),
    ("Семишагофф (ООО ТК Прогресс)", "хард-дискаунтер, СЗФО",
     70.67, 29.0, 0.954, ND, 188, ND, False),
    ("Авокадо (франшиза ГК Сладкая жизнь)", "франчайзи у дома",
     65.69, 4.7, ND, ND, ND, ND, False),
    ("Линия (ООО Гипермаркет Линия / Гринн)", "гипер, Черноземье",
     44.0, 6.7, 2.41, ND, 18, ND, False),
    ("Лама (SPAR / Первоцен / F City; сумма 4 юрлиц)", "супер / у дома, Томск–Новосибирск",
     32.31, 8.5, 0.335, ND, ND, ND, False),
    ("Аникс (ТС Аникс + Прайд-А)", "у дома, Алтай",
     31.3, 9.4, 0.414, ND, ND, ND, False),
    ("Европа (ООО Европа, Курск)", "гипер / супер, Черноземье",
     31.0, 3.0, 1.1, ND, ND, ND, False),
    ("Бегемаг (ООО Универсамы Бегемаг)", "у дома / SPAR, Кузбасс",
     12.87, 1.3, 0.0653, ND, ND, ND, False),
    ("Низкоцен (ООО Холлифуд)", "хард-дискаунтер, Сибирь/Урал",
     9.5, -2.0, 0.0613, ND, ND, ND, False),
    ("Победа Омск (ООО Формат; не ТК Лето)", "у дома / дискаунтер, Омск",
     8.0, ND, 0.202, ND, ND, ND, False),
    ("Доброцен (одно юрлицо, не вся сеть)", "хард-дискаунтер",
     6.3, -26.0, -0.013, ND, ND, ND, False),
    ("Быстроном (ООО Мегаторг)", "у дома, Новосибирск",
     4.9, 4.0, 0.0063, ND, ND, ND, False),
    ("Бахетле (ООО Бахетле-1, Татарстан)", "супер, Татарстан",
     4.64, 0.1, 0.0097, ND, ND, ND, False),
    ("Бахетле Новосибирск (ООО Гастромаркет)", "супер, Новосибирск",
     3.4, -5.0, 0.000045, ND, ND, ND, False),
    ("Макси (юрлицо, Вологда)", "гипер / супер, СЗФО",
     2.42, 19.1, -0.0084, ND, ND, ND, False),
    ("Добрянка (ООО Русская поварня)", "супер, регионы",
     2.4, ND, 0.0011, ND, ND, ND, False),
    ("Форне (ООО Форне Кондитер)", "кондитерская розница, Бийск",
     0.93, 14.0, 0.0819, ND, ND, ND, False),
    # --- бренды / юрлица внутри групп: цифры раскрыты, не суммировать с холдингом ---
    ("Пятёрочка (бренд X5)", "у дома; внутри X5, не суммировать",
     3600.0, ND, ND, ND, ND, ND, True),
    ("Красное & Белое (ООО Альфа-М; внутри Mercury)", "алкоголь / у дома; не суммировать с Mercury",
     846.6, 33.0, 26.1, ND, 21482, ND, True),
    ("Перекрёсток (бренд X5)", "супер; внутри X5, не суммировать",
     531.0, ND, ND, ND, ND, ND, True),
    ("Чижик (бренд X5)", "хард-дискаунтер; внутри X5, не суммировать",
     417.5, 67.3, ND, ND, ND, ND, True),
    ("Дикси (формат Магнита)", "у дома; внутри Магнита, не суммировать",
     376.2, 15.4, ND, ND, 2668, ND, True),
    ("Бристоль (ООО Альбион-2002; внутри Mercury)", "алкоголь; не суммировать с Mercury",
     365.7, 10.0, 8.6, ND, ND, ND, True),
    ("X5 онлайн (канал группы)", "e-grocery; внутри X5, не суммировать",
     285.7, 42.8, ND, ND, ND, ND, True),
    ("ВкусВилл онлайн (канал сети)", "e-grocery; внутри ВкусВилл, не суммировать",
     221.1, 16.7, ND, ND, ND, ND, True),
    ("Азбука вкуса (бренд Магнита с 2025)", "премиум супер; внутри Магнита, не суммировать",
     106.3, ND, ND, ND, ND, ND, True),
    ("Около (франшиза X5)", "франчайзи у дома; внутри периметра X5, не суммировать",
     66.0, 680.0, ND, ND, ND, ND, True),
    ("Монетка (бренд Ленты)", "у дома, Урал; внутри Ленты, не суммировать",
     ND, 29.1, ND, ND, ND, ND, True),
    ("Фасоль (франшиза METRO)", "у дома; франшиза, не консолидируется полностью",
     ND, 3.8, ND, ND, ND, ND, True),
]

MFG = [
    ("PepsiCo Россия (вкл. Вимм-Билль-Данн)", "напитки / снеки / молочка",
     398.8, 11.1, ND, ND, ND, ND, False),
    ("Русагро", "масложир / сахар / мясо / агро",
     396.5, 16.6, 19.9, 148.0, ND, ND, False),
    ("ЭФКО", "масложир / B2C / экспорт",
     344.0, 0.0, ND, ND, ND, ND, False),
    ("АПХ Мираторг", "мясо / от поля до прилавка",
     342.2, 13.6, ND, ND, ND, ND, False),
    ("KDV Group", "кондитерка / снеки",
     308.1, 1.0, ND, ND, ND, ND, False),
    ("Черкизово", "мясо / птица / мясопереработка",
     288.7, 11.4, 30.0, 139.9, ND, ND, False),
    ("ГАП Ресурс", "птица / мясо",
     287.5, 7.3, ND, ND, ND, ND, False),
    ("Nestlé Россия", "кофе / корма / кулинария",
     257.6, 2.2, ND, ND, ND, ND, False),
    ("Mars Россия", "корма / кондитерка / еда",
     235.1, 11.0, ND, ND, ND, ND, False),
    ("Продимекс (сумма предприятий группы)", "сахар / агро; внутригрупповые обороты возможны",
     220.0, ND, 33.0, ND, ND, ND, False),
    ("Агропромкомплектация", "мясо / молоко / агро",
     204.4, 15.0, ND, ND, ND, ND, False),
    ("Логика молока (ex-Danone / Health&Nutrition)", "молочка / детское питание",
     167.1, 17.9, ND, ND, 12, ND, False),
    ("Напитки вместе (ex-AB InBev Efes)", "пиво / безалкогольные",
     164.7, 16.6, ND, ND, ND, ND, False),
    ("Балтика (ООО ПК Балтика)", "пиво / вода",
     145.9, 8.2, 13.3, ND, ND, ND, False),
    ("Сибагро (совокупность компаний группы)", "свинина / мясо, Сибирь",
     132.0, 13.8, ND, ND, ND, ND, False),
    ("Объединённые кондитеры (ООО, дистрибуция группы)", "кондитерка",
     113.2, 4.7, 0.513, ND, ND, ND, False),
    ("АБИ (ABI Product)", "мясопереработка / полуфабрикаты",
     87.9, ND, ND, ND, ND, ND, False),
    ("Дамате", "индейка / молоко / баранина",
     82.8, 15.0, ND, ND, ND, ND, False),
    ("Комос Групп (молочный контур рейтинга)", "молоко / мясо / птица",
     63.1, 17.5, ND, ND, ND, ND, False),
    ("Орими Трейд (Tess, Greenfield, Jardin)", "чай / кофе",
     62.32, 9.9, 8.475, ND, ND, ND, False),
    ("Hochland Russland", "сыр / молочка",
     60.8, 12.6, ND, ND, ND, ND, False),
    ("ГК Ренна", "мороженое / сгущёнка",
     58.1, 13.3, ND, ND, ND, ND, False),
    ("Агроэко", "свинина / мясо",
     56.4, 19.0, 8.5, ND, ND, ND, False),
    ("Прогресс (ФрутоНяня / Малышам)", "детское питание / соки",
     52.1, 8.0, 10.2, ND, ND, ND, False),
    ("ГК Молвест", "молочка",
     51.7, 4.2, ND, ND, ND, ND, False),
    ("Эссен Продакшн (Махеевъ)", "соусы / консервация / кондитерка",
     50.2, 15.7, 4.9, ND, ND, ND, False),
    ("Юговской комбинат молочных продуктов", "молочка / сыр",
     46.4, 4.7, ND, ND, ND, ND, False),
    ("Сады Придонья", "соки / пюре / растениеводство",
     42.88, 13.6, 4.155, ND, ND, ND, False),
    ("Ehrmann Россия", "молочка / десерты",
     40.6, 19.8, ND, ND, ND, ND, False),
    ("ГК Фудлэнд", "сыр / молочка",
     40.0, 3.1, ND, ND, ND, ND, False),
    ("Инвест Альянс (производство Ермолино)", "полуфабрикаты; связано с розницей Ермолино",
     36.7, 21.0, 6.8, ND, 3, ND, False),
    ("Lactalis Россия", "сыр / молочка",
     33.0, 8.2, ND, ND, ND, ND, False),
    ("ГК ЭкоНива (молочный контур рейтинга)", "молочка / агро",
     29.8, 4.9, ND, ND, ND, ND, False),
    ("ГК Айсберри", "мороженое",
     29.5, 10.9, ND, ND, ND, ND, False),
    ("МПБК Очаково", "пиво / квас / напитки",
     28.3, 17.0, 2.33, ND, ND, ND, False),
    ("ГК Российское Молоко", "молочка",
     27.7, 24.8, ND, ND, ND, ND, False),
    ("ГК Экомилк", "молочка",
     27.6, 19.0, ND, ND, ND, ND, False),
    ("АМП Дамол", "молочка",
     26.8, 3.1, ND, ND, ND, ND, False),
    ("ГК Русское молоко", "молочка",
     24.8, 17.5, ND, ND, ND, ND, False),
    ("ГК РостАгроКомплекс", "молочка / творожные",
     24.4, 9.4, ND, ND, ND, ND, False),
    ("ГК Сыробогатов", "сыр",
     23.1, 54.0, ND, ND, ND, ND, False),
    ("Арнест ЮниРусь", "молочка / мороженое",
     22.5, 15.4, ND, ND, ND, ND, False),
    ("Нэфис Косметикс", "бытовая химия",
     21.5, -1.5, -1.2, ND, ND, ND, False),
    ("Агрокомплекс им. Н.И. Ткачёва (молочный контур)", "молочка / агро, Юг",
     20.7, 23.2, ND, ND, ND, ND, False),
    ("ГК Доминант (молочный контур)", "молочка / сахар смежно",
     18.4, 18.7, ND, ND, ND, ND, False),
    ("MLK Group (Ува-молоко)", "молочка",
     18.2, 8.3, ND, ND, ND, ND, False),
    ("Ровеньки-Маслосырзавод", "сыр / молочка",
     18.1, 2.8, ND, ND, ND, ND, False),
    ("Брянский молочный комбинат", "молочка",
     18.0, 12.5, ND, ND, ND, ND, False),
    ("ГК Мультипро", "молочка / ингредиенты",
     17.3, 14.6, ND, ND, ND, ND, False),
    ("Зеленодольский МК", "молочка",
     17.2, 11.0, ND, ND, ND, ND, False),
    ("Лебедяньмолоко", "молочка",
     17.2, 25.5, ND, ND, ND, ND, False),
    ("Froneri Россия", "мороженое",
     15.9, 16.0, ND, ND, ND, ND, False),
    ("ГК Руслакто", "молочка",
     14.6, 10.6, ND, ND, ND, ND, False),
    ("ГК ВАМИН", "молочка, Татарстан",
     14.5, 11.5, ND, ND, ND, ND, False),
    ("СК Ичалковский / СЗ Сармич", "сыр / молочка",
     14.4, 9.9, ND, ND, ND, ND, False),
    ("Ирбитский молочный завод", "молочка",
     14.1, 21.6, ND, ND, ND, ND, False),
    ("ТнВ Сыр Стародубский", "сыр",
     14.0, 19.7, ND, ND, ND, ND, False),
    ("МилкЭкспресс", "молочка",
     13.9, 18.8, ND, ND, ND, ND, False),
    ("Пискарёвский молочный завод", "молочка, СЗФО",
     13.7, 12.3, ND, ND, ND, ND, False),
    ("Барнаульский молочный комбинат", "молочка",
     13.1, 11.0, ND, ND, ND, ND, False),
    ("DMK Group", "молочка",
     13.0, 3.2, ND, ND, ND, ND, False),
    ("ГК Галактика", "молочка",
     12.7, 9.5, ND, ND, ND, ND, False),
    ("Виола", "сыр / молочка",
     12.3, 8.8, ND, ND, ND, ND, False),
    # внутри PepsiCo — цифра раскрыта, не суммировать с стр. PepsiCo
    ("Вимм-Билль-Данн (молочка PepsiCo)", "молочка; внутри PepsiCo, не суммировать",
     162.3, 6.7, ND, ND, ND, ND, True),
]

HEADERS = [
    "Компания", "Тип / формат",
    "Выручка 2025, млрд ₽", "YoY, %",
    "Чистая прибыль 2025, млрд ₽", "Чистый долг, млрд ₽",
    "Магазины / заводы, шт", "Доля рынка Food, %",
]

NUM_COLS = {3, 4, 5, 6, 8}  # 1-indexed
INT_COLS = {7}


def disclosed(row):
    name, typ, rev, yoy, prof, debt, stores, share, inside = row
    return any(v is not None for v in (rev, yoy, prof, debt, stores, share))


def style_header(ws, ncol):
    fill = PatternFill("solid", fgColor="1F4E79")
    font = Font(name="Calibri", bold=True, color="FFFFFF", size=10)
    align = Alignment(wrap_text=True, vertical="center", horizontal="center")
    thin = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )
    for col in range(1, ncol + 1):
        c = ws.cell(1, col)
        c.fill = fill
        c.font = font
        c.alignment = align
        c.border = thin
    ws.row_dimensions[1].height = 36
    ws.freeze_panes = "B2"


def write_table(ws, rows, widths):
    rows = [r for r in rows if disclosed(r)]
    for i, h in enumerate(HEADERS, 1):
        ws.cell(1, i, h)
    style_header(ws, len(HEADERS))
    thin = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )
    wrap = Alignment(wrap_text=True, vertical="center")
    even = PatternFill("solid", fgColor="F2F2F2")
    brand = PatternFill("solid", fgColor="FFF2CC")
    num_font = Font(name="Calibri", size=10)
    for r_i, row in enumerate(rows, 2):
        name, typ, rev, yoy, prof, debt, stores, share, inside = row
        values = [name, typ, rev, yoy, prof, debt, stores, share]
        for c_i, val in enumerate(values, 1):
            cell = ws.cell(r_i, c_i)
            cell.border = thin
            cell.alignment = wrap
            cell.font = num_font
            if inside:
                cell.fill = brand
            elif r_i % 2 == 0:
                cell.fill = even
            if val is None:
                cell.value = "н/д"
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            else:
                cell.value = val
            if c_i in (3, 5, 6) and isinstance(val, (int, float)):
                cell.number_format = "#,##0.00" if abs(val) < 1 else "#,##0.0"
            if c_i in (4, 8) and isinstance(val, (int, float)):
                cell.number_format = "0.0"
            if c_i == 7 and isinstance(val, (int, float)):
                cell.number_format = "#,##0"
        ws.row_dimensions[r_i].height = 36
    red = Font(name="Calibri", size=10, color="C00000", bold=True)
    ws.conditional_formatting.add(
        f"E2:E{len(rows)+1}",
        CellIsRule(operator="lessThan", formula=["0"], font=red),
    )
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    last = get_column_letter(len(HEADERS))
    ws.auto_filter.ref = f"A1:{last}{len(rows)+1}"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    return len(rows)


def main():
    n_ch = sum(1 for r in CHAINS if disclosed(r))
    n_ch_ind = sum(1 for r in CHAINS if disclosed(r) and not r[8])
    n_mfg = sum(1 for r in MFG if disclosed(r))
    n_mfg_ind = sum(1 for r in MFG if disclosed(r) and not r[8])
    assert n_ch >= 50, n_ch
    assert n_mfg >= 50, n_mfg
    assert all(disclosed(r) for r in CHAINS)
    assert all(disclosed(r) for r in MFG)

    wb = Workbook()
    title_f = Font(name="Calibri", size=16, bold=True, color="1F4E79")
    h_f = Font(name="Calibri", size=12, bold=True, color="1F4E79")
    b_f = Font(name="Calibri", size=11)

    ws0 = wb.active
    ws0.title = "0. Как читать"
    ws0.sheet_properties.tabColor = "1F4E79"
    ws0["A1"] = "FMCG Россия — финансовый срез на сентябрь 2026"
    ws0["A1"].font = title_f
    ws0.merge_cells("A1:B1")
    bullets = [
        ("A3", "Таблицы", h_f),
        ("A4",
         "Листы «Сети» и «Производители»: только 8 столбцов со скриншота. "
         "Строк больше 50, если нашлись; пустых «н/д»-заглушек нет. "
         f"Сети: {n_ch} с хотя бы одной раскрытой цифрой 2025 (из них {n_ch_ind} независимых операторов, остальные — бренды/юрлица внутри групп, жёлтым). "
         f"Производители: {n_mfg} с раскрытием (из них {n_mfg_ind} независимых контуров).",
         b_f),
        ("A6", "Что считать раскрытым", h_f),
        ("A7",
         "В строке есть хотя бы одно из: выручка, YoY, прибыль, чистый долг, магазины/заводы, доля Food. "
         "«н/д» в соседних ячейках — открытой сопоставимой цифры нет, ничего не досчитано.",
         b_f),
        ("A9", "Период и контур", h_f),
        ("A10",
         "Основной столбец — полный 2025 (последний закрытый год). Доля Food у X5 — INFOLine YE2025 (16,6%); у Магнита — последний опубликованный срез INFOLine Q1 2026 (12,3%). "
         "Два независимых рейтинга, не пары «сеть ↔ производитель». РФ only.",
         b_f),
        ("A12", "Жёлтые строки", h_f),
        ("A13",
         "Бренд или юрлицо внутри уже стоящей выше группы (Пятёрочка внутри X5, Альфа-М внутри Mercury, ВБД внутри PepsiCo и т.п.). "
         "Цифры нужны для полки, суммировать с холдингом нельзя.",
         b_f),
        ("A15", "Источники (иерархия)", h_f),
        ("A16",
         "1) МСФО эмитента. 2) INFOLine Food retail / Food&Drink 2026. 3) РСБУ юрлица. 4) Ведомости / Т-Ж / Союзмолоко / Milknews. "
         "При расхождении в ячейке приоритетный источник: МСФО/INFOLine важнее РСБУ одного юрлица.",
         b_f),
        ("A18", "Дата сборки", h_f),
        ("A19", "13 октября 2026. Срез «на сентябрь 2026» = отчётность 2025 + опубликованные операционные факты 2026, без смешения лет в одной ячейке выручки.", b_f),
    ]
    for cell, text, font in bullets:
        ws0[cell] = text
        ws0[cell].font = font
        ws0[cell].alignment = Alignment(wrap_text=True, vertical="top")
    ws0.column_dimensions["A"].width = 118
    ws0.row_dimensions[4].height = 64
    ws0.row_dimensions[7].height = 40
    ws0.row_dimensions[10].height = 48
    ws0.row_dimensions[13].height = 48
    ws0.row_dimensions[16].height = 48

    ws1 = wb.create_sheet("1. Выводы")
    ws1.sheet_properties.tabColor = "C45911"
    ws1["A1"] = "Тезисы — для слайда или письма"
    ws1["A1"].font = title_f
    ws1.merge_cells("A1:F1")
    theses = [
        "1. Рынок Food РФ концентрируется: топ-10 сетей ≈ 12,7 трлн ₽ выручки 2025 (INFOLine), доля топ-10 в РТО Food 45,9% в 1 кв. 2026. X5 16,6% (YE2025) / 17,4% (Q1 2026), Магнит 12,3% (Q1 2026).",
        "2. Выручка лидеров растёт, прибыль — нет. X5: 4,64 трлн (+18,8%), прибыль 94,8 млрд. Магнит: 3,51 трлн (+15,3%), убыток ≈ 16,6 млрд, чистый долг 496 млрд.",
        "3. Из топ-4 одновременно ускорили выручку и прибыль Лента (1,10 трлн, +24,2%; прибыль 38,2) и Mercury (1,66 трлн, +20%; прибыль 54,5). Лента: долг 48,8 млрд.",
        "4. Хард-дискаунтер расколот: Чижик (внутри X5) 417,5 млрд (+67%), Светофор 394 млрд (−3%) и сжатие сети. Семишагофф 70,7 млрд (+29%), Находка ~82 млрд.",
        "5. Производители: топ-10 Food&Drink = 3 трлн ₽ (+9,1%). PepsiCo РФ 399 и Русагро 397 почти вничью. В десятке уже 5 агрохолдингов.",
        "6. На полке молочки 2025 лидер «Логика молока» 167,1 млрд, не ВБД (162,3, внутри PepsiCo). Пиво: «Напитки вместе» 164,7; Балтика 145,9 выручки и 13,3 прибыли.",
        "7. Регионалы с твёрдой выручкой >100 млрд: Верный 154, SPAR МВ 136, Мария-Ра 128, Ермолино ~111, Командор 100. Ниже — зона РСБУ отдельных юрлиц, не всегда вся вывеска.",
        "8. Для переговоров/полки: кэш у X5, Ленты, Mercury, Черкизово, Русагро. Осторожнее Магнит (долг/убыток) и Светофор (сжатие). Жёлтые строки не прибавлять к холдингу.",
    ]
    for i, t in enumerate(theses, 3):
        ws1.merge_cells(start_row=i, start_column=1, end_row=i, end_column=6)
        ws1.cell(i, 1, t).font = Font(name="Calibri", size=11)
        ws1.cell(i, 1).alignment = Alignment(wrap_text=True, vertical="top")
        ws1.row_dimensions[i].height = 44
    ws1.column_dimensions["A"].width = 28
    ws1.column_dimensions["B"].width = 22
    ws1.column_dimensions["C"].width = 14
    ws1.column_dimensions["D"].width = 14
    ws1.column_dimensions["E"].width = 22
    ws1.column_dimensions["F"].width = 14

    ws1["A12"] = "Данные для графиков"
    ws1["A12"].font = h_f
    ws1["A13"] = "Сеть"
    ws1["B13"] = "Выручка 2025, млрд ₽"
    ws1["C13"] = "Прибыль 2025, млрд ₽"
    ws1["E13"] = "Производитель"
    ws1["F13"] = "Выручка 2025, млрд ₽"
    for col in range(1, 7):
        if ws1.cell(13, col).value:
            ws1.cell(13, col).font = Font(name="Calibri", bold=True, color="FFFFFF", size=10)
            ws1.cell(13, col).fill = PatternFill("solid", fgColor="1F4E79")

    chart_chains = [
        ("X5", 4642, 94.8),
        ("Магнит", 3509, -16.6),
        ("Mercury", 1660, 54.5),
        ("Лента", 1104, 38.2),
        ("Светофор", 394, 5.8),
        ("ВкусВилл", 359, 6.6),
        ("Fix Price", 313, 11.2),
        ("METRO", 260, 4.4),
        ("Ашан", 250, None),
        ("О'КЕЙ", 196, 14.3),
    ]
    for i, (n, v, p) in enumerate(chart_chains, 14):
        ws1.cell(i, 1, n)
        ws1.cell(i, 2, v).number_format = "#,##0"
        if p is None:
            ws1.cell(i, 3, "н/д")
        else:
            ws1.cell(i, 3, p).number_format = "0.0"

    chart_mfg = [
        ("PepsiCo РФ", 399),
        ("Русагро", 397),
        ("ЭФКО", 344),
        ("Мираторг", 342),
        ("KDV", 308),
        ("Черкизово", 289),
        ("Ресурс", 288),
        ("Nestlé РФ", 258),
        ("Mars", 235),
        ("Агропромкомплектация", 204),
    ]
    for i, (n, v) in enumerate(chart_mfg, 14):
        ws1.cell(i, 5, n)
        ws1.cell(i, 6, v).number_format = "#,##0"

    c1 = BarChart()
    c1.type = "bar"
    c1.title = "Топ сетей по выручке 2025, млрд ₽"
    data = Reference(ws1, min_col=2, min_row=13, max_row=23)
    cats = Reference(ws1, min_col=1, min_row=14, max_row=23)
    c1.add_data(data, titles_from_data=True)
    c1.set_categories(cats)
    c1.legend = None
    c1.style = 10
    c1.y_axis.scaling.orientation = "maxMin"
    c1.width = 18
    c1.height = 8
    ws1.add_chart(c1, "A26")

    c2 = BarChart()
    c2.type = "bar"
    c2.title = "Прибыль тех же сетей 2025, млрд ₽"
    data2 = Reference(ws1, min_col=3, min_row=13, max_row=22)
    cats2 = Reference(ws1, min_col=1, min_row=14, max_row=22)
    c2.add_data(data2, titles_from_data=True)
    c2.set_categories(cats2)
    c2.legend = None
    c2.style = 11
    c2.y_axis.scaling.orientation = "maxMin"
    c2.width = 18
    c2.height = 8
    ws1.add_chart(c2, "D26")

    c3 = BarChart()
    c3.type = "bar"
    c3.title = "Топ-10 производителей Food&Drink 2025, млрд ₽"
    data3 = Reference(ws1, min_col=6, min_row=13, max_row=23)
    cats3 = Reference(ws1, min_col=5, min_row=14, max_row=23)
    c3.add_data(data3, titles_from_data=True)
    c3.set_categories(cats3)
    c3.legend = None
    c3.style = 10
    c3.y_axis.scaling.orientation = "maxMin"
    c3.width = 18
    c3.height = 8
    ws1.add_chart(c3, "A43")

    widths = [46, 42, 16, 10, 18, 16, 16, 14]
    ws2 = wb.create_sheet("2. Сети")
    ws2.sheet_properties.tabColor = "2E7D32"
    write_table(ws2, CHAINS, widths)
    ws2.sheet_view.showGridLines = False

    ws3 = wb.create_sheet("3. Производители")
    ws3.sheet_properties.tabColor = "7B1FA2"
    write_table(ws3, MFG, widths)
    ws3.sheet_view.showGridLines = False

    ws4 = wb.create_sheet("4. Источники")
    ws4.sheet_properties.tabColor = "607D8B"
    ws4["A1"] = "Короткий список источников"
    ws4["A1"].font = title_f
    sources = [
        "INFOLine: розница Food РФ; рейтинг сетей FMCG; FOOD&DRINK RATING RUSSIA-2026; e-grocery 2025 (Самокат 279,3; X5 Digital/онлайн; Лавка 203,1; Ozon 207,2). Топ-10 сетей ≈ 12,7 трлн, +16,1%.",
        "X5 МСФО 2025: 4 642 млрд, +18,8%, прибыль 94,8, долг 228,5, магазины 29 790; онлайн 285,7 (+42,8%); доля Food YE2025 16,6%.",
        "Магнит МСФО 2025: 3 509,2 (+15,3%), магазины 33 440; убыток INFOLine/Т-Ж ≈ −16,6; долг 496. Дикси: 10,8% розницы группы ≈ 376 млрд, +15,4%, 2 668 магазинов.",
        "Лента МСФО 2025: 1 103,7, прибыль 38,2, долг 48,8, 6 760 магазинов. Монетка +29,1% (INFOLine, без абсолюта).",
        "Fix Price МСФО 12М 2025 (упр.): 313,3 (+4,3%), прибыль 11,18, 7 818 магазинов.",
        "Винлаб МСФО 2025: 95,1 (+9%), прибыль 3,5, чистая денежная позиция 6,5, 2 175 магазинов.",
        "Верный (Союз св. Иоанна Воина) РСБУ 2025: 154,4 (+12,7%), прибыль 21,4 млн.",
        "SPAR МВ РСБУ: 136,3 (+6,1%), прибыль 229 млн, 142 магазина (AK&M).",
        "Семишагофф / ТК Прогресс РСБУ: 70,67 (+29%), прибыль 0,95. Авокадо INFOLine 65,69 (+4,7%). Около (X5) 66 млрд (×7,8 к 2024).",
        "Линия / Гринн: 44 (+6,7%), прибыль 2,41, 18 гипер. Европа Курск РСБУ: 31 (+3%), прибыль 1,1.",
        "Сибирь РСБУ (ksonline / Асефера / Толк): Ярче 168,3; Мария-Ра 127,6; Командор 100 / прибыль 1,7; Аникс 31,3; Лама 4 юрлица ≈ 32,3; Бегемаг 12,87; Низкоцен 9,5; Победа Омск 8; Доброцен 6,3; Быстроном 4,9.",
        "Ермолино: INFOLine 111,1 выручки сети 2025; 3 005 магазинов на июнь 2026. Производство (Инвест Альянс) 36,7 / прибыль 6,8 — на листе производителей.",
        "Союзмолоко / Milknews / Streda — переработчики молока 2025. INFOLine Food&Drink топ-10. МСФО Русагро, Черкизово, Дамате. РСБУ Балтика, Прогресс, Эссен, Сады Придонья, Очаково, Орими, Нэфис, Объединённые кондитеры.",
        "Т-Ж 15.06.2026 — прибыль сетей INFOLine. Ведомости/EcomHub — Mercury 1,66; Ашан 250; О'КЕЙ 196; Победа/ТК Лето 176.",
    ]
    for i, s in enumerate(sources, 3):
        ws4.cell(i, 1, s).font = b_f
        ws4.cell(i, 1).alignment = Alignment(wrap_text=True, vertical="top")
        ws4.row_dimensions[i].height = 36
    ws4.column_dimensions["A"].width = 124

    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(ART).parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    wb.save(ART)
    print(f"saved {OUT}")
    print(f"chains {n_ch} (independent {n_ch_ind}), mfg {n_mfg} (independent {n_mfg_ind})")


if __name__ == "__main__":
    main()

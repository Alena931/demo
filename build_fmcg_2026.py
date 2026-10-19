#!/usr/bin/env python3
"""FMCG 2026 revenue snapshot in the user's Google Sheets format.
Times New Roman 11, teal A2C4C9 header/name column, wrap, freeze B2.
No invented FY numbers: fact = published; FY estimate only if a method is stated."""
from copy import copy
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, Protection
from openpyxl.utils import get_column_letter
from pathlib import Path
import shutil

SRC = "/tmp/template_sheet.xlsx"
OUT = "/workspace/FMCG_RF_vyruchka_2026.xlsx"
ART = "/opt/cursor/artifacts/FMCG_RF_vyruchka_2026.xlsx"
ND = "н/д"

TEAL = "A2C4C9"
HEADER = [
    "Компания",
    "Тип / формат",
    "Выручка 2026 факт, млрд ₽",
    "Период факта",
    "YoY факта, %",
    "Оценка / прогноз года 2026, млрд ₽",
    "Магазины / заводы, шт",
    "Откуда цифра / как считали оценку",
]

# name matches template row order. tuple:
# fact, period, yoy, fy_est, stores, note
CHAINS_2026 = {
    "X5 Group (Пятёрочка, Перекрёсток, Чижик)": (
        3791.5, "9 мес.", 11.4, "5200–5385", 30981,
        "ПАО, trading update 16.10.2026 (предварительные, без аудита). "
        "9М выручка 3 791,5 млрд (+11,4%); 3 кв. 1 311 млрд (+13,0%). "
        "Пятёрочка 9М 2 918 (+9,4%), Перекрёсток 413 (+7,1%), Чижик 391 (+31,4%), "
        "X5 Digital 257 (+28,4%). Магазинов 30 981 на 30.09. "
        "Прогноз самой компании на год: рост 12–16% от 4 642 → 5 200–5 385. "
        "https://www.x5.ru/wp-content/uploads/2026/10/q3_2026_trading_update_rus.pdf"
    ),
    "Магнит (вкл. Дикси, Самбери, Азбука вкуса)": (
        1887.2, "1 пол.", 12.8, 3958, 33652,
        "МСФО 1П, 28.08.2026: 1 887,2 млрд (+12,8%). Чистая розница 1 871. "
        "Магазинов 33 652. Чистый долг ~514,5; убыток по IFRS 16 ≈ −9,5. "
        "Оценка года: 3 509 × 1,128, если темп 1П удержится (это не отчёт за год). "
        "https://www.magnit.com/ru/media/press-releases/magnit-obyavlyaet-operatstionnye-i-finansovye-rezultaty-deyatelnosti-za-pervoe-polugodie-2026-goda/"
    ),
    "Mercury Retail (Красное & Белое, Бристоль)": (
        878.0, "1 пол.", 11.2, 1846, ND,
        "INFOLine / «Коммерсантъ» 02.09.2026, топ-10 FMCG 1П: 878 млрд (+11,2%). "
        "Сводного МСФО холдинга нет. Оценка года: 1 660 × 1,112, если темп 1П удержится. "
        "https://www.kommersant.ru/doc/8923592"
    ),
    "Группа Лента (Гипер/Супер Лента, Монетка, Улыбка радуги, Реми)": (
        648.49, "1 пол.", 26.2, 1393, 7456,
        "МСФО 1П: 648,5 млрд (+26,2%); 2 кв. 341,6 (+28,8%). Магазинов 7 456 на 30.06. "
        "Супер Лента +30,2%, Монетка +26,1%, гипер +12,9% (INFOLine). "
        "В августе закрыла покупку гипермаркетов «О’КЕЙ» — во 2П периметр шире. "
        "Оценка года без сделки: 1 104 × 1,262. Стратегия к 2028 — 2,2 трлн. "
        "https://www.lentagroup.ru/ru/media/news-and-press-releases/gruppa-lenta-obyavlyaet-o-roste-vyruchki-na-28-8-roste-lfl-prodazh-na-6-5-vo-2-kvartale-2026-goda/"
    ),
    "Светофор / Маяк (ГК Торгсервис)": (
        189.0, "1 пол.", -4.5, 377, ND,
        "INFOLine / «Коммерсантъ»: 189 млрд (−4,5%). Оценка года: 394 × 0,955. "
        "https://www.kommersant.ru/doc/8923592"
    ),
    "ВкусВилл": (
        191.06, "1 пол.", 7.8, 387, ND,
        "INFOLine / «Коммерсантъ»: 191,06 млрд (+7,8%), обогнал Светофор в топ-5. "
        "Оценка года: 359 × 1,078. "
        "https://www.infoline.spb.ru/news/?news=308855"
    ),
    "Fix Price": (
        155.3, "1 пол.", 4.8, 328, 8077,
        "МСФО 1П, 27.08.2026: 155,3 млрд (+4,8%); 2 кв. 82,2 (+6,9%). "
        "Розница 1П 138,2, опт 17,1. Магазинов 8 077. Оценка года: 313 × 1,048. "
        "https://investors.fix-price.ru/upload/iblock/927/qomfciov5lu66hurwrrsb5bn5wkxeut0/PJSC_Fix_Price_announces_key_operating_and_financial_results_for_Q2_2026_RUS.pdf"
    ),
    "Самокат": (
        135.0, "1 пол.", 15.5, 323, ND,
        "Оценка INFOLine / «Коммерсантъ»: 135 млрд (+15,5%). "
        "Оценка года: 279 × 1,155. "
        "https://www.kommersant.ru/doc/8923592"
    ),
    "METRO Россия": (
        118.9, "1 пол.", 0.5, 262, ND,
        "INFOLine / «Коммерсантъ»: 118,9 млрд (+0,5%). Оценка года: 260 × 1,005. "
        "https://www.kommersant.ru/doc/8923610"
    ),
    "АШАН Ритейл Россия": (
        127.01, "1 пол.", -2.5, 244, ND,
        "INFOLine / «Коммерсантъ»: 127 млрд (−2,5%). Оценка года: 250 × 0,975. "
        "https://www.kommersant.ru/doc/8923592"
    ),
    "Ozon + Ozon Fresh": (
        ND, ND, ND, ND, ND,
        "Отдельной продуктовой выручки Ozon Fresh за 2026 нет. "
        "Data Insight: пятёрка e-grocery (Самокат, ВкусВилл, Лавка, Пятёрочка, Ozon Fresh) "
        "во 2 кв. вместе 260 млрд ₽ и 214 млн заказов; у Ozon Fresh заказы +65%. "
        "Это оборот рынка доставки, не строка МСФО Ozon. "
        "https://abn.agency/2026/08/14/oborot-rossijskogo-egrocery-dostig-8942-mlrd-rublej-za-polugodie/"
    ),
    "Яндекс Лавка": (
        ND, ND, ND, ND, ND,
        "Выручку Лавки отдельно не публикуют. Блок e-com Яндекса (Лавка+Маркет+Еда+Деливери) "
        "1П 247 млрд (+19%) — это не только продукты. Заказы Лавки во 2 кв. +5% (Data Insight). "
        "https://www.comnews.ru/content/246667/2026-07-31/2026-w31/1008/ozon-ustremilsya-lidery-sredi-marketpleysov"
    ),
    "ГК О'КЕЙ / Да!": (
        43.3, "1 пол. «ДА!»", 10.4, 88, 236,
        "После продажи гипер в конце 2025 у листинга O’KEY Group остался только «ДА!»: "
        "МСФО 1П 43,3 млрд (+10,4%), 236 магазинов. Оценка года контура «ДА!»: 80 × 1,104. "
        "Гипер ООО «О’КЕЙ» по РСБУ 1П 68,2 (−5,6%) — уже периметр Ленты, не складывать с «ДА!». "
        "https://okeygroup.lu/upload/IFRS%201H2026_RUS_final_.pdf"
    ),
    "SPAR Миддл Волга (SPAR, EUROSPAR)": (
        103.57, "1 пол.", 7.8, 147, ND,
        "INFOLine / «Коммерсантъ»: «Спар Миддл Волга, Smart» 103,57 млрд (+7,8%) — "
        "периметр шире, чем строка 2025 (только SPAR МВ 136 за год). Оценка года грубая: 136 × 1,078. "
        "https://www.kommersant.ru/doc/8923592"
    ),
    "Винлаб (ПАО ВинЛаб / Novabev)": (
        51.2, "1 пол.", 7.2, 102, 2222,
        "МСФО 1П, 24.08.2026: 51,2 млрд (+7,2%), EBITDA 4,5, прибыль 0,8, точек 2 225 на 30.06 "
        "(2 222 на 30.09). Оценка года с темпа 1П: 95,1 × 1,072. "
        "9М «продажи с НДС +24%» — это не IFRS-выручка, в ячейку не ставили. "
        "https://corp.winelab.ru/ru/press-center/news-and-press-releases/vyruchka-vinlab-vyrosla-na-7-2-i-prevysila-51-mlrd-rubley-v-pervom-polugodii-2026-goda/"
    ),
}

MFG_2026 = {
    "Русагро": (
        183.0, "1 пол.", 9.1, 433, ND,
        "МСФО 1П: 183,0 млрд (+9,1%). У агро 2П обычно больше 1П, поэтому не умножали на 2. "
        "Оценка года: 396,5 × 1,091, если темп удержится. "
        "https://www.rusagrogroup.ru/fileadmin/files/reports/ru/pdf/Rusagro_Group_PJSC_IFRS_6m_2026_RUS.pdf"
    ),
    "АПХ Мираторг": (
        ND, ND, ND, 350, ND,
        "Полной выручки 1П 2026 в открытом виде нет. Президент Линник (ПМЭФ, июнь): "
        "ожидает рост выручки «на несколько процентов»; экспорт удержать ~58 млрд как в 2025 "
        "(план +20% по экспорту снят из‑за крепкого рубля). Оценка года ≈ 342 × 1,03. "
        "Прибыль МСФО 6 мес. 19,61 млрд (+26%) — это не выручка. "
        "https://echomsk.spb.ru/nws/5317198-miratorg-ogidaet-neznachitelnyj-rost-vyruchki-po-itogam-2026-goda.html"
    ),
    "Черкизово": (
        141.6, "1 пол.", 3.5, 299, ND,
        "МСФО 1П: 141,6 млрд (+3,5%); скорр. EBITDA 27,2 (+38%). "
        "Оценка года: 288,7 × 1,035. "
        "https://www.interfax.ru/business/1111410"
    ),
    "Дамате": (
        46.3, "1 пол.", 19.0, 99, ND,
        "Пресс-служба 07.09.2026: 46,3 млрд (+19%), EBITDA 10. Оценка года: 82,8 × 1,19. "
        "https://www.acdamate.com/press-center/press/vyruchka-damate-v-i-polugodii-2026-goda-vyrosla-na-19-i-prevysila-46-mlrd-rubley/"
    ),
    "Агроэко": (
        24.63, "1 пол.", -6.4, 53, ND,
        "МСФО 6 мес.: 24,63 млрд (−6,4% к 26,31). Прибыль 1,99 (−40%). "
        "Оценка года: 56,4 × 0,936. Объём свинины +10% при падении цены. "
        "https://www.tbank.ru/invest/social/profile/Marten_Resting/cbc77ff8-2a7f-49ae-8534-59a60c86da65/"
    ),
    "ГК ЭкоНива (молочный контур рейтинга)": (
        45.2, "1 пол. весь холдинг", -2.8, ND, ND,
        "МСФО холдинга 1П 45,2 млрд (−2,8%), прибыль 1,1. Это ВЕСЬ холдинг, "
        "не молочный контур рейтинга INFOLine 2025 (29,8) — сравнивать с 29,8 нельзя. "
        "Оценку года для контура не ставили. "
        "https://abireg.ru/newsitem/116916/"
    ),
    "Сады Придонья": (
        ND, "1 кв., только тонны", ND, ND, ND,
        "Выручку 2026 не публиковали. 1 кв.: продажи в натуральном выражении +7,5%, "
        "бренды «Сады Придонья» +11%, Nemoloko +19% (РБК Компании). "
        "https://companies.rbc.ru/news/kwQXFC9CLJ/kak-sadyi-pridonya-adaptiruyutsya-v-usloviyah-ryinochnoj-neopredelennosti/"
    ),
}

MEDIA = [
    ("Как читать цифру 2026",
     "Года ещё нет (сейчас октябрь 2026), полного МСФО за 2026 ни у кого нет. "
     "В столбце «факт» — уже опубликованный кусок: 9 месяцев, полугодие или квартал. "
     "«Оценка года» — не отчёт, а арифметика: либо прогноз самой компании, либо "
     "выручка-2025 × темп уже вышедшего куска 2026. Где куска нет — «н/д», ничего не додумано.",
     "https://www.x5.ru/ru/investors/financial-and-operational-results/"),
    ("X5 — 9 месяцев",
     "Касса за январь–сентябрь 3,79 трлн ₽, на 11,4% больше, чем за те же 9 месяцев 2025-го. "
     "Третий квартал быстрее полугодия: +13% до 1,31 трлн. Чижик по-прежнему самый быстрый внутри группы "
     "(+31% за 9 мес., +35% за квартал). Компания свой прогноз на весь год не снимала: +12–16%.",
     "https://www.x5.ru/wp-content/uploads/2026/10/q3_2026_trading_update_rus.pdf"),
    ("X5 — ориентир на год",
     "В марте и снова в июне президент Екатерина Лобачева: прогноз роста выручки 12–16% на 2026 держим. "
     "От базы 4,642 трлн это примерно 5,20–5,39 трлн за полный год. 9 месяцев идут ближе к нижней границе.",
     "https://www.x5.ru/ru/news/x5-predstavila-prognozy-i-orientiry-na-2026-god/"),
    ("Магнит — полугодие",
     "1 887 млрд ₽ за полгода, +12,8%. Магазины работают, касса растёт, по прибыли группа всё ещё в минусе "
     "по IFRS 16. Это тот же сюжет, что в 2025: полка живая, проценты тяжёлые.",
     "https://www.magnit.com/ru/media/press-releases/magnit-obyavlyaet-operatstionnye-i-finansovye-rezultaty-deyatelnosti-za-pervoe-polugodie-2026-goda/"),
    ("Топ-10 сетей, 1 пол. 2026",
     "INFOLine сложил десятку: 6,76 трлн ₽, +11,6% (годом раньше десятка росла на 17%). "
     "Лента +26% — самый быстрый из крупных. Светофор и Ашан в минусе. "
     "На весь 2026 INFOLine ждёт рост крупнейших сетей примерно 9–11%.",
     "https://www.kommersant.ru/doc/8923592"),
    ("Лента — полугодие",
     "648 млрд ₽ за полгода, +26%. Драйверы — Супер Лента и Монетка. В августе забрала гипер «О’КЕЙ» — "
     "второе полугодие будет уже с чужими магазинами в периметре.",
     "https://www.lentagroup.ru/ru/media/news-and-press-releases/gruppa-lenta-obyavlyaet-o-roste-vyruchki-na-28-8-roste-lfl-prodazh-na-6-5-vo-2-kvartale-2026-goda/"),
    ("Fix Price — полугодие",
     "155 млрд ₽, +4,8%. Медленнее продуктовых федералов: фиксированная цена и смешанный ассортимент.",
     "https://investors.fix-price.ru/upload/iblock/927/qomfciov5lu66hurwrrsb5bn5wkxeut0/PJSC_Fix_Price_announces_key_operating_and_financial_results_for_Q2_2026_RUS.pdf"),
    ("Винлаб — полугодие",
     "51 млрд ₽ по МСФО, +7%. Отдельно компания хвалится продажами с НДС за 9 месяцев (+24%) — "
     "это восстановление после кибератаки 2025-го, не путать с выручкой в таблице.",
     "https://corp.winelab.ru/ru/press-center/news-and-press-releases/vyruchka-vinlab-vyrosla-na-7-2-i-prevysila-51-mlrd-rubley-v-pervom-polugodii-2026-goda/"),
    ("Русагро — полугодие",
     "183 млрд ₽, +9%. Догнать PepsiCo по году ещё рано: полного 2026 нет ни у кого из заводов.",
     "https://www.rusagrogroup.ru/fileadmin/files/reports/ru/pdf/Rusagro_Group_PJSC_IFRS_6m_2026_RUS.pdf"),
    ("Черкизово — полугодие",
     "142 млрд ₽, всего +3,5%. Слабее инфляции: дешевле свинина и меньше экспорта в Китай.",
     "https://www.interfax.ru/business/1111410"),
    ("Дамате — полугодие",
     "46 млрд ₽, +19% — один из немногих заводов с двузначным ростом кассы.",
     "https://www.acdamate.com/press-center/press/vyruchka-damate-v-i-polugodii-2026-goda-vyrosla-na-19-i-prevysila-46-mlrd-rubley/"),
    ("Мираторг — прогноз, не факт",
     "Выручку за 2026 пока не раскрыли. Глава холдинга в июне: ждать роста «на несколько процентов», "
     "экспорт удержать около 58 млрд ₽.",
     "https://news.mail.ru/economics/71212403/"),
]


def font_like(src, **kw):
    return Font(
        name=kw.get("name", src.name or "Times New Roman"),
        size=kw.get("size", src.size or 11),
        bold=kw.get("bold", src.bold),
        italic=src.italic,
        color=src.color,
        underline=src.underline,
    )


def restyle_header_row(ws):
    for col in range(1, 9):
        c = ws.cell(1, col)
        c.value = HEADER[col - 1]


def fill_row(ws, r, data):
    fact, period, yoy, fy, stores, note = data
    ws.cell(r, 3).value = fact
    ws.cell(r, 4).value = period
    ws.cell(r, 5).value = yoy
    ws.cell(r, 6).value = fy
    ws.cell(r, 7).value = stores
    ws.cell(r, 8).value = note
    # keep wrap on comment
    ws.cell(r, 8).alignment = Alignment(wrap_text=True, vertical="top", horizontal="left")
    ws.row_dimensions[r].height = 48


def nd_row(ws, r, why):
    for col in range(3, 8):
        ws.cell(r, col).value = ND
    ws.cell(r, 8).value = why
    ws.cell(r, 8).alignment = Alignment(wrap_text=True, vertical="top", horizontal="left")
    ws.row_dimensions[r].height = 32


def apply_table(ws, mapping, empty_note):
    restyle_header_row(ws)
    ws.row_dimensions[1].height = 32
    for r in range(2, ws.max_row + 1):
        name = ws.cell(r, 1).value
        if name in mapping:
            fill_row(ws, r, mapping[name])
        else:
            nd_row(ws, r, empty_note)
    # comment column wider so format stays readable
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 16
    ws.column_dimensions["E"].width = 12
    ws.column_dimensions["F"].width = 18
    ws.column_dimensions["G"].width = 14
    ws.column_dimensions["H"].width = 78


def style_new_sheet(ws):
    header_fill = PatternFill("solid", fgColor=TEAL)
    header_font = Font(name="Times New Roman", size=11, bold=True)
    body_font = Font(name="Times New Roman", size=11)
    wrap = Alignment(wrap_text=True, vertical="top", horizontal="left")
    name_fill = PatternFill("solid", fgColor=TEAL)
    for col in range(1, 4):
        cell = ws.cell(1, col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = wrap
    ws.freeze_panes = "B2"
    ws.sheet_view.showGridLines = True
    return body_font, name_fill, wrap


def main():
    shutil.copyfile(SRC, OUT)
    wb = load_workbook(OUT)

    apply_table(
        wb["Сети"],
        CHAINS_2026,
        "Открытой выручки / прогноза за 2026 не нашли. Региональные сети обычно публикуют РСБУ только весной следующего года.",
    )
    apply_table(
        wb["Производители"],
        MFG_2026,
        "Открытой выручки / прогноза за 2026 не нашли. Большинство заводов рейтинга INFOLine отчитываются раз в год.",
    )

    # Медиа — overwrite with 2026 sources, keep format
    wsM = wb["Медиа"]
    for rng in list(wsM.merged_cells.ranges):
        wsM.unmerge_cells(str(rng))
    for r in range(2, wsM.max_row + 1):
        for col in range(1, 8):
            wsM.cell(r, col).value = None
    wsM.cell(1, 1).value = "Кто"
    wsM.cell(1, 2).value = "Что случилось простыми словами"
    wsM.cell(1, 3).value = "Ссылка"
    link_font = Font(name="Times New Roman", size=11, color="0000FF", underline="single")
    body = Font(name="Times New Roman", size=11)
    wrap = Alignment(wrap_text=True, vertical="top", horizontal="left")
    teal = PatternFill("solid", fgColor=TEAL)
    for i, (who, what, url) in enumerate(MEDIA, 2):
        a, b, c = wsM.cell(i, 1), wsM.cell(i, 2), wsM.cell(i, 3)
        a.value, b.value, c.value = who, what, url
        a.font = body
        a.fill = teal
        a.alignment = wrap
        b.font = body
        b.alignment = wrap
        c.font = link_font
        c.alignment = wrap
        c.hyperlink = url
        wsM.row_dimensions[i].height = 72
    wsM.column_dimensions["A"].width = 22
    wsM.column_dimensions["B"].width = 65
    wsM.column_dimensions["C"].width = 40

    # How-to sheet in the same visual language
    ws0 = wb.create_sheet("Как читать 2026", 0)
    title_f = Font(name="Times New Roman", size=14, bold=True)
    h_f = Font(name="Times New Roman", size=11, bold=True)
    b_f = Font(name="Times New Roman", size=11)
    wrap = Alignment(wrap_text=True, vertical="top")
    teal = PatternFill("solid", fgColor=TEAL)
    ws0["A1"] = "Выручка 2026: что уже есть, чего ещё нет"
    ws0["A1"].font = title_f
    ws0["A1"].fill = teal
    ws0["B1"].fill = teal
    ws0.row_dimensions[1].height = 24
    blocks = [
        ("Почему нет колонки «выручка за весь 2026»",
         "Сегодня 19 октября 2026. Финансовый год закроется 31 декабря. "
         "Годовые МСФО/РСБУ компании обычно публикуют весной 2027. "
         "Поэтому в таблице два разных числа: уже вышедший кусок года и, где можно, оценка полного года."),
        ("Что в столбце «факт»",
         "Только опубликованная выручка за 9 месяцев, полугодие или (редко) квартал. "
         "X5 — единственная из крупных, у кого на октябрь уже есть 9 месяцев. "
         "Магнит, Лента, Fix Price, Русагро, Черкизово — полугодие. "
         "Светофор, Mercury, Самокат, Ашан, Metro — оценки INFOLine за полугодие, не их собственный МСФО."),
        ("Что в столбце «оценка / прогноз года»",
         "Либо слова самой компании (X5: рост 12–16%; Мираторг: «несколько процентов»), "
         "либо простая арифметика: выручка-2025 × темп уже вышедшего куска 2026. "
         "Это не отчёт и не гарантия. У агро (Русагро) второе полугодие обычно сильнее первого — поэтому не умножали полугодие на два."),
        ("Чего в ячейках нет",
         "Пустых «примерно» без источника. Если открытой цифры нет — «н/д». "
         "Региональные сети и большинство молочных заводов так и стоят: они отчитаются в 2027-м."),
        ("Формат файла",
         "Шрифт Times New Roman 11, шапка и столбец «Компания» — заливка #A2C4C9, как в вашей Google-таблице. "
         "Списки те же: сети и производители в том же порядке. Добавлен только этот лист и обновлён «Медиа»."),
    ]
    r = 3
    for title, text in blocks:
        ws0.cell(r, 1, title).font = h_f
        ws0.cell(r, 1).fill = teal
        ws0.cell(r, 1).alignment = wrap
        ws0.cell(r, 2, text).font = b_f
        ws0.cell(r, 2).alignment = wrap
        ws0.row_dimensions[r].height = 64
        r += 2
    ws0.column_dimensions["A"].width = 28
    ws0.column_dimensions["B"].width = 92
    ws0.freeze_panes = "A3"
    ws0.sheet_properties.tabColor = TEAL

    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(ART).parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    Path(ART).write_bytes(Path(OUT).read_bytes())
    print("saved", OUT)
    print("chains with fact", sum(1 for v in CHAINS_2026.values() if v[0] != ND))
    print("mfg with fact", sum(1 for v in MFG_2026.values() if v[0] != ND))


if __name__ == "__main__":
    main()

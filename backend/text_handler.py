import re
import os

def find_contract_number(text: str) -> str:
    """
    Ищет номер основного договора, поддерживая варианты:
    - «договором ng123C/456789-Х»
    - «договором 123C/456789-Х»
    - «к договору ng123C/456789-Х»
    - «к договору 123C/456789-Х»
    - «по договору ng123C/456789»
    - «по договору 123C/456789»
    - и в обоих случаях fallback на просто цифры/слэш/цифры
    """
    lower = text.lower()
    pre = r"(?:договором|к\s+договору|по\s+договору)[\s\S]{0,100}?"

    # 1) префикс ng или n2 + основной номер + «-...» до пробела
    m = re.search(
        pre + r"(?:ng|n2)\s*([0-9]+[cс]/[0-9]+(?:-[^\s]+)?)",
        lower
    )
    if m:
        return m.group(1).upper()

    # 2) без ng/n2, но с C/c и возможным «-...»
    m = re.search(
        pre + r"([0-9]+[cс]/[0-9]+(?:-[^\s]+)?)",
        lower
    )
    if m:
        return m.group(1).upper()

    # 3) просто цифры/слэш/цифры (до пробела)
    m = re.search(
        pre + r"([0-9]+/[0-9]+(?:-[^\s]+)?)",
        lower
    )
    if m:
        return m.group(1).upper()

    return "[не найдено]"


def find_contract_date(text: str) -> str:

    match = re.search(
        r"договор(?:ом|а)?[\s\S]{0,100}?от\s*(\d{2})\.(\d{2})\.(\d{4})",
        text,
        flags=re.IGNORECASE
    )
    if not match:
        match = re.search(
            r"от\s*(\d{2})\.(\d{2})\.(\d{4})",
            text,
            flags=re.IGNORECASE
        )
    if not match:
        return "[не найдено]"
    day, month, year_full = match.group(1), match.group(2), match.group(3)
    yy = year_full[-2:]
    return f"{day}/{month}/{yy}"


def find_principal_tin(text: str) -> str:
    """
    Ищет ИНН принципала:
    1) Находит все вхождения 'ИНН' или 'ИНН/КПП' с 10 цифрами.
    2) Выбирает то, которое стоит непосредственно перед словом 'принципал' (его конец < позиции 'принципал').
    3) Если таких нет, возвращает второе вхождение в тексте.
    """
    lower = text.lower()
    idx_princ = lower.find("принципал")

    # Регекс ловит «ИНН» или «ИНН/КПП» и сразу захватывает 10 цифр
    pattern = re.compile(r"\bинн(?:/кпп)?[\s/:]*([0-9]{10})", flags=re.IGNORECASE)
    matches = list(pattern.finditer(text))

    # 1) Если нашли «принципал», попробуем взять последнее INN до него
    if idx_princ != -1:
        before = [m for m in matches if m.end() < idx_princ]
        if before:
            return before[-1].group(1)

    # 2) Иначе возвращаем второе вхождение (если есть)
    if len(matches) >= 2:
        return matches[1].group(1)

    # 3) Не найдено
    return ""


def find_guarantor_bik(text: str) -> str:
    """
    Ищет первое упоминание БИК в тексте и возвращает его (9 цифр).
    Поддерживает формы "БИК 044525593" и "БИК:044525593", без учёта регистра.
    """
    pattern = re.compile(r"\bбик[:\s]*([0-9]{9})", flags=re.IGNORECASE)
    for m in pattern.finditer(text):
        return m.group(1)
    return "[не найдено]"


GUARANTEE_TYPES = [
    "Возврат авансового платежа",
    "Надлежащее исполнение договора",
    "Исполнение гарантийных обязательств",
    "Независимая гарантия",
]

def find_guarantee_type(text: str) -> str:
    """Ищет один из четырёх типов банковской гарантии по заголовку."""
    lower = text.lower()

    # Спецслучай «исполнения контракта»
    if re.search(r"банковская\s+гарантия[\s\S]{0,100}исполнени[ея]\s+контракт", lower):
        return "Исполнение гарантийных обязательств"

    # Берём всё после «банковская гарантия» (несколько строк)
    m = re.search(r"банковская\s+гарантия[\s:\-,]*([\s\S]+)", text, flags=re.IGNORECASE)
    if not m:
        return "[не найдено]"
    candidate = m.group(1).lower()

    # Сплитим на слова
    words = re.findall(r"[\wа-яё]+", candidate)

    best_type = ""
    best_score = 0

    for gtype in GUARANTEE_TYPES:
        gwords = re.findall(r"[\wа-яё]+", gtype.lower())
        score = 0
        for w in words:
            for gw in gwords:
                if w == gw or w.startswith(gw) or gw.startswith(w):
                    score += 1
                    break
        if score > best_score:
            best_score = score
            best_type = gtype

    return best_type if best_score > 0 else "[не найдено]"

ENTITY_TYPES = {
    "АО": [
        "акционерное общество",
        "акционерного общества",
    ],
    "ОАО": [
        "открытое акционерное общество",
        "открытого акционерного общества",
    ],
    "ЗАО": [
        "закрытое акционерное общество",
        "закрытого акционерного общества",
    ],
    "ООО": [
        "общество с ограниченной ответственностью",
        "общества с ограниченной ответственностью",
        "обяества $ сграниченной отзетственностью",
    ],
    "ПАО": [
        "публичное акционерное общество",
        "публичного акционерного общества",
    ],
}

def find_principal_name(text: str) -> str:
    lower = text.lower()
    idx = lower.find("принципал")
    if idx == -1:
        return "[не найдено]"

    left = text[:idx]
    left_lower = lower[:idx]

    best_end = -1
    best_abbrev = None

    # 1) ищем самый правый вариант типа юрлица
    for abbrev, variants in ENTITY_TYPES.items():
        for variant in variants:
            parts = variant.split()
            pattern = r"\b" + r"\s+".join(map(re.escape, parts)) + r"\b"
            for m in re.finditer(pattern, left_lower, flags=re.IGNORECASE):
                if m.end() > best_end:
                    best_end = m.end()
                    best_abbrev = abbrev

    if not best_abbrev:
        return "[не найдено]"

    # 2) вырезаем фрагмент между вариантом и 'принципал'
    fragment = text[best_end:idx].lstrip()

    # === Специальный случай для «научно‑производственное предприятие» ===
    special = re.search(
        r"(научно)[-–]?\s*(производственное)\s*(предприятие)\s+([кК]?[^\s(]+)",
        fragment, flags=re.IGNORECASE
    )
    if special:
        phrase_part = f"{special.group(1)}-{special.group(2)} {special.group(3)}".upper()
        next_word = special.group(4)
        if next_word.lower().startswith("к"):
            next_word = next_word[1:]
        next_word = re.sub(r"[^\w]+$", "", next_word).upper()
        return f'{best_abbrev} "{phrase_part} "{next_word}"'

    # === Общая ветка: сначала заменяем переводы строк на пробелы ===
    clean = fragment.replace("\n", " ").strip()

    # Захватываем всё до первого разделителя ; , ( .
    name_match = re.match(r"([^;,\(\.]+)", clean)
    if not name_match:
        return "[не найдено]"

    org_name = name_match.group(1).strip()
    # Обрезаем первый/последний символ (к…х)
    core = org_name[1:-1] if len(org_name) > 2 else org_name

    return f'{best_abbrev} "{core}"'.upper()


def find_guarantee_number(text: str) -> str:
    """
    Ищет номер гарантии в нижнем регистре.
    Захватывает до 200 символов после 'банковская гарантия',
    находит префикс 'ng' или 'n2', затем сам номер.
    Исправляет OCR-ошибки: 'э'->'9', 'i'/'l'->'1', 'o'/'о'->'0'.
    """
    # 1) Берём фрагмент до 200 символов после 'банковская гарантия'
    header_match = re.search(r"банковская гарантия[\s\S]{0,200}", text)
    if not header_match:
        return "[не найдено]"
    header = header_match.group(0)

    # 2) Ищем 'n' + ('g' или '2')
    m = re.search(r"\bn([g2])", header)
    if not m:
        m = re.search(r"\bл:", header)
        if not m:
            return "[не найдено]"
    # 3) Начинаем чтение сразу после найденного префикса
    pos = m.end()

    # 4) Пропускаем любые пробельные символы
    while pos < len(header) and header[pos].isspace():
        pos += 1

    # 5) Захватываем подряд идущие буквы (лат и кирилл), цифры, slash и dash
    num_match = re.match(r"([a-zа-я0-9/\-]+)", header[pos:], flags=re.IGNORECASE)
    if not num_match:
        return "[не найдено]"
    num = num_match.group(1)

    # 6) OCR‑исправления
    num = num.replace("э", "9")
    num = re.sub(r"[il]", "1", num, flags=re.IGNORECASE)
    # Заменяем все латинские 'o' и кириллические 'о' на '0'
    num = re.sub(r"[oо]", "0", num, flags=re.IGNORECASE)

    return num.upper()


def find_has_changes(text: str) -> str:
    """Проверяет наличие слов об изменениях"""
    return "[найдено]" if re.search(r"изменени|пролонгац", text, re.IGNORECASE) else ""


MONTH_MAP = {
    "01": ["январь", "января"],
    "02": ["февраль", "февраля"],
    "03": ["март", "марта"],
    "04": ["апрель", "апреля"],
    "05": ["май", "мая"],
    "06": ["июнь", "июня"],
    "07": ["июль", "июля"],
    "08": ["август", "августа"],
    "09": ["сентябрь", "сентября"],
    "10": ["октябрь", "октября"],
    "11": ["ноябрь", "ноября"],
    "12": ["декабрь", "декабря"],
}


# Функция для извлечения дня из заданного куска текста
def extract_day(chunk: str):
    # оставить только цифры или OCR-символы
    raw = ''.join(ch for ch in chunk if ch.isalnum() or ch in ('О', 'о', 'б'))
    raw = raw[-2:]
    day = ''
    for ch in raw:
        if ch in ('О', 'о'):
            day += '0'
        elif ch == 'б':
            day += '6'
        elif ch.isdigit():
            day += ch
    if len(day) == 1:
        day = '0' + day
    return day

def find_signature_date(text: str) -> str:
    """
    Ищет дату подписания гарантии в первых 20 строках с учётом переноса дня на отдельную строку.
    """
    lines = text.splitlines()[:20]
    for i, line in enumerate(lines):
        lower = line.lower()
        for month_num, variants in MONTH_MAP.items():
            for variant in variants:
                idx = lower.find(variant)
                if idx == -1:
                    continue

                # 1) пробуем из текущей строки
                left = lower[:idx].strip()
                day = extract_day(left)

                # 2) если не получилось (слишком коротко), пробуем соединить с предыдущей
                if len(day) < 2 and i > 0:
                    prev = lines[i-1].lower().strip()
                    combined = prev + ' ' + lower
                    idx2 = combined.find(variant)
                    if idx2 != -1:
                        day = extract_day(combined[:idx2].strip())

                if not day:
                    # можно добавить ещё уровней предыдущих строк при необходимости
                    continue

                # год — как было
                right = lower[idx + len(variant):]
                year_match = re.search(r"(\d{4})", right)
                if not year_match:
                    continue
                yy = year_match.group(1)[-2:]
                return f"{day}/{month_num}/{yy}"
    return "[не найдено]"


def find_start_date(text: str) -> str:
    """
    Ищет дату начала действия гарантии:
    1) пытается найти точный шаблон 'вступает в силу [со дня] DD.MM.YYYY'
    2) если не найден явный DD.MM.YYYY, но есть фраза 'вступает в силу со дня',
       то:
         - если есть дата подписания (find_signature_date != ""), вернуть её,
         - иначе вернуть '[со дня подписания]'.
    3) если нет ни того, ни другого, вернуть дату подписания гарантии.
    """
    # 1) смотрим на явный DD.MM.YYYY после 'вступает в силу'
    full_match = re.search(
        r"вступает в силу\s*(?:со\s*дня\s*)?(\d{2}\.\d{2}\.\d{4})",
        text,
        flags=re.IGNORECASE
    )
    if full_match:
        # если нашли дату в тексте, возвращаем её
        return full_match.group(1)

    # 2) проверяем, есть ли фраза 'вступает в силу со дня'
    so_day = re.search(r"вступает в силу\s*со\s*дня", text, flags=re.IGNORECASE)
    if so_day:
        # если дата подписания гарантии есть — возвращаем её
        signed = find_signature_date(text)
        if signed:
            return signed
        # иначе — возвращаем пометку
        return "[со дня выдачи]"

    # 3) fallback — возвращаем дату подписания гарантии
    return find_signature_date(text)


def find_end_date(text: str) -> str:
    """
    Ищет дату окончания действия гарантии и возвращает в формате DD/MM/YY.
    Дополнительно обрабатывает случай вида:
      «действует по (2w декабря 2028 г. включительно»
    где 'w' нужно трактовать как '2'.
    """
    # 1) Исходный поиск «действует по DD.MM.YYYY»
    match = re.search(r"действует по(?:о)?\s*(\d{2})\.(\d{2})\.(\d{4})", text, flags=re.IGNORECASE)
    if match:
        day, month, year_full = match.group(1), match.group(2), match.group(3)
        return f"{day}/{month}/{year_full[-2:]}"

    # 2) Общий поиск «по DD.MM.YYYY»
    match = re.search(r"\bпо\s*(\d{2})\.(\d{2})\.(\d{4})", text, flags=re.IGNORECASE)
    if match:
        day, month, year_full = match.group(1), match.group(2), match.group(3)
        return f"{day}/{month}/{year_full[-2:]}"

    # 3) Специальный вариант: «действует по» + текст + название месяца
    m = re.search(r"действует по(?:о)?([\s\S]{0,100})", text, flags=re.IGNORECASE)
    if m:
        segment = m.group(1)
        lower = segment.lower()
        for month_num, variants in MONTH_MAP.items():
            for variant in variants:
                idx = lower.find(variant)
                if idx == -1:
                    continue
                # 3.1) День — всё, что до названия месяца
                day_raw = segment[:idx]
                # Оставляем цифры и возможные OCR-символы O, o, б, w
                day_raw = re.sub(r"[^0-9OobwW]", "", day_raw)
                # Исправляем OCR:
                day_raw = day_raw.replace("w", "2").replace("W", "2")
                day_raw = day_raw.replace("O", "0").replace("o", "0").replace("б", "6")
                # Берём последние две цифры
                digits = re.findall(r"\d", day_raw)
                if len(digits) >= 2:
                    day = digits[-2] + digits[-1]
                elif len(digits) == 1:
                    day = "0" + digits[0]
                else:
                    continue
                # 3.2) Год — первое 4-значное число после месяца
                after = lower[idx + len(variant):]
                year_m = re.search(r"(\d{4})", after)
                if not year_m:
                    continue
                yy = year_m.group(1)[-2:]
                return f"{day}/{month_num}/{yy}"

    # Ничего не найдено
    return "[не найдено]"

def find_amount(text: str) -> str:
    """
    Ищет сумму гарантии:
    - ловит после 'сумма' или 'суммой' цифры, пробелы, точки, запятые и буквы 'з'/'З';
    - заменяет 'з'/'З' на '3';
    - удаляет все пробелы.
    """
    match = re.search(r"(?:сумма|суммой)[\s:\-]*([\d\s\.,зЗ]+)", text, flags=re.IGNORECASE)
    if not match:
        return "[не найдено]"
    val = match.group(1)
    # Исправляем OCR: кириллическую 'з' и 'З' → цифра '3'
    val = val.replace('з', '3').replace('З', '3')
    # Убираем все пробельные символы
    val = re.sub(r"\s+", "", val)
    return val

CURRENCY_MAP = {
    "RUB": [
        "российских рублей",
        "российские рубли",
        "рубль",      # теперь ловим и единственное число
        "рубл"       # или корень для общей подстановки
    ],
    "USD": [
        "долларов",
        "долларов сша",
        "доллары"
    ],
    "EUR": [
        "евро"
    ],
}

def find_currency(text: str) -> str:
    """
    Ищет валюту в пределах 100 символов после найденной суммы.
    Использует ту же логику поиска суммы, что и find_amount.
    """
    lower = text.lower()

    # 1) Ищем сумму по тому же шаблону, что и в find_amount
    sum_match = re.search(r"(?:сумма|суммой)[\s:\-]*([\d\s\.,]+)", lower, flags=re.IGNORECASE)
    if not sum_match:
        return "[не найдено]"

    # 2) Определяем границы окна в 100 символов после конца найденной суммы
    start = sum_match.end(1)
    window = lower[start:start + 100]

    # 3) Ищем валюту в этом окне
    for code, variants in CURRENCY_MAP.items():
        for variant in variants:
            if variant in window:
                return code

    return "[не найдено]"

def parse_bank_guarantee(file_path: str):

    with open(file_path, encoding='utf-8') as f:
        text = f.read()

    funcs = [
        ('№ Основного договора', find_contract_number),
        ('Дата подписания основного договора', find_contract_date),
        ('ИНН', find_principal_tin),
        ('БИК', find_guarantor_bik),
        ('Вид гарантии', find_guarantee_type),
        ('Принципал', find_principal_name),
        ('№ Гарантии', find_guarantee_number),
        ('ДОП / ИЗМ', find_has_changes),
        ('Дата подписания', find_signature_date),
        ('Дата начала', find_start_date),
        ('Дата окончания', find_end_date),
        ('Сумма', find_amount),
        ('Валюта', find_currency),
    ]
    result = {}
    for name, func in funcs:
        try:
            val = func(text)
        except Exception:
            val = ''
        result[name] = val

    return result

# os.chdir('../')
# result = parse_bank_guarantee("texts/20241106 Альфабанк 0T9H4X.txt")
# print(result)
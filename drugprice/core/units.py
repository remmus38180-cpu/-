# -*- coding: utf-8 -*-
"""含量、包裝數量與名稱的解析與正規化。

各國原始檔把「含量」與「包裝數量」寫成各式各樣的自由文字，例如::

    "2,5 mg"            法國、比利時常用逗號當小數點
    "30 comprimés"      包裝數量與單位混在一起
    "5 mg/5 ml"         比例式含量
    "PLAQ THERMO 30"    包裝說明夾雜其他文字

本模組把這些拆成數值與單位。**拆不出來就回傳 None，不猜**——
猜錯的包裝數量會讓單位藥價整個失真，寧可留空讓人處理。

僅使用 Python 標準函式庫。
"""

import re
import unicodedata

__all__ = ["parse_quantity", "parse_strength", "parse_pack_size",
           "normalize_name", "strip_salt", "clean_number"]

# 常見的包裝單位字樣（多語）。用來從自由文字中認出包裝數量。
PACK_UNITS = [
    ("錠", ["tablet", "tablets", "tabl", "comprimé", "comprimes", "comprimés",
            "tabletten", "tablett", "compresse", "錠", "tab"]),
    ("膠囊", ["capsule", "capsules", "gélule", "gelules", "gélules",
              "kapsel", "kapseln", "kapslar", "カプセル", "膠囊"]),
    ("支", ["ampoule", "ampoules", "ampulle", "ampuller", "vial", "vials",
            "flacon", "flacons", "injektion", "支", "瓶"]),
    ("毫升", ["ml", "millilitre", "milliliter", "毫升"]),
    ("公克", ["g", "gram", "gramme", "gramm", "公克", "克"]),
    ("片", ["patch", "patches", "pflaster", "plåster", "片"]),
    ("劑", ["dose", "doses", "dosis", "doser", "劑"]),
]

_UNIT_LOOKUP = {}
for _zh, _words in PACK_UNITS:
    for _word in _words:
        _UNIT_LOOKUP[_word.lower()] = _zh

# 含量單位，順序重要：先長後短，避免 "mg" 先被 "g" 吃掉
STRENGTH_UNITS = [
    "microgram", "micrograms", "mikrogram", "mcg", "µg", "ug",
    "milligram", "milligrams", "mg", "gram", "grams", "g",
    "iu", "ie", "units", "unit", "u",
    "ml", "l", "%",
]

_NUMBER = r"\d+(?:[.,]\d+)?"


def _to_float(text):
    """把數字字串轉成 float，同時處理歐洲式的逗號小數點。"""
    if text is None:
        return None
    text = str(text).strip()
    if not text:
        return None
    # 千分位逗號（1,234.56）vs 小數逗號（2,5）
    if "," in text and "." in text:
        text = text.replace(",", "")
    elif "," in text:
        left, _, right = text.partition(",")
        text = f"{left}.{right}" if len(right) <= 3 and right.isdigit() else text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def _unit_pattern():
    """組出包裝單位的比對樣式。

    各國語言的複數變化很多（tablett／tabletter、kapsel／kapslar、
    comprimé／comprimés），逐一列舉會漏。因此四個字元以上的單位允許
    後面接字尾變化，三個字元以內的短單位（g、ml、tab）則要求完整結尾，
    以免 "g" 誤中 "granulat"。
    """
    parts = []
    for word in sorted(_UNIT_LOOKUP, key=len, reverse=True):
        escaped = re.escape(word)
        parts.append(escaped + r"[a-zà-ÿ]*" if len(word) >= 4 else escaped + r"\b")
    return "|".join(parts)


def _lookup_unit(matched):
    """把實際比對到的字（可能含字尾變化）對回中文單位。"""
    text = matched.lower()
    if text in _UNIT_LOOKUP:
        return _UNIT_LOOKUP[text]
    for word in sorted(_UNIT_LOOKUP, key=len, reverse=True):
        if text.startswith(word):
            return _UNIT_LOOKUP[word]
    return ""


def clean_number(text, max_decimals=6):
    """去掉數字字串裡的浮點雜訊，但不改變真正的有效位數。

    澳洲 PBS API 把 JSON 浮點數轉成 CSV 時會出現 ``456.65000000000003``
    這種尾數。小數位數超過 max_decimals 時才做處理，且只有在四捨五入後
    的值與原值相等（誤差在浮點精度內）才採用，避免動到真正的精度。

    無法解析為數字時原樣回傳，不吞掉資料。
    """
    if text is None:
        return ""
    raw = str(text).strip()
    if not raw:
        return ""
    _, _, fraction = raw.partition(".")
    if len(fraction) <= max_decimals:
        return raw
    try:
        value = float(raw)
    except ValueError:
        return raw
    rounded = round(value, max_decimals)
    if rounded != value and abs(rounded - value) > abs(value) * 1e-12:
        return raw
    return f"{rounded:.{max_decimals}f}".rstrip("0").rstrip(".") or "0"


def parse_quantity(text, units=None):
    """從自由文字取出 (數值, 單位原文)。取不出來回傳 (None, "")。"""
    if not text:
        return None, ""
    text = unicodedata.normalize("NFKC", str(text)).strip()

    if units:
        pattern = "|".join(re.escape(u) for u in sorted(units, key=len, reverse=True))
        match = re.search(rf"({_NUMBER})\s*({pattern})\b", text, re.IGNORECASE)
        if match:
            return _to_float(match.group(1)), match.group(2)

    match = re.search(rf"({_NUMBER})\s*([^\d\s,;/]+)?", text)
    if match:
        return _to_float(match.group(1)), (match.group(2) or "").strip()
    return None, ""


def parse_strength(text):
    """解析含量，回傳 (數值, 單位)。

    ``"2,5 mg"`` → ``(2.5, "mg")``；``"5 mg/5 ml"`` 取分子 ``(5.0, "mg")``。
    """
    if not text:
        return None, ""
    text = unicodedata.normalize("NFKC", str(text)).strip()
    pattern = "|".join(re.escape(u) for u in
                       sorted(STRENGTH_UNITS, key=len, reverse=True))
    match = re.search(rf"({_NUMBER})\s*({pattern})(?![a-z])", text, re.IGNORECASE)
    if match:
        return _to_float(match.group(1)), match.group(2).lower()
    return None, ""


def parse_pack_size(text):
    """解析包裝數量，回傳 (數值, 中文單位, 原文單位)。

    認得出單位就回傳中文單位；認不出來但有數字，單位留空由人補。
    """
    if text is None:
        return None, "", ""
    text = unicodedata.normalize("NFKC", str(text)).strip()
    if not text:
        return None, "", ""

    # 純數字（例如澳洲 PBS 的 pack_size 欄位就是純數字）
    if re.fullmatch(rf"{_NUMBER}", text):
        return _to_float(text), "", ""

    # "數字 + 單位" 或 "單位 + 數字" 兩種寫法都要認
    pattern = _unit_pattern()

    match = re.search(rf"({_NUMBER})\s*({pattern})", text, re.IGNORECASE)
    if match:
        return (_to_float(match.group(1)),
                _lookup_unit(match.group(2)), match.group(2))

    match = re.search(rf"\b({pattern})\s*({_NUMBER})", text, re.IGNORECASE)
    if match:
        return (_to_float(match.group(2)),
                _lookup_unit(match.group(1)), match.group(1))

    # 文字裡只有一個數字時，把它當作包裝數量（如 "PLAQ THERMO 30"）
    numbers = re.findall(_NUMBER, text)
    if len(numbers) == 1:
        return _to_float(numbers[0]), "", ""

    return None, "", ""


# 鹽類與酯類字尾。比對成分名時要先拿掉，
# 否則 "apixaban" 會對不上 "apixaban maleate"。
SALT_WORDS = [
    "hydrochloride", "hydrochlorid", "chlorhydrate", "hcl",
    "hydrobromide", "sulfate", "sulphate", "sulfat",
    "maleate", "maleat", "mesylate", "mesilate", "besylate", "besilate",
    "tartrate", "citrate", "acetate", "phosphate", "fumarate",
    "succinate", "sodium", "natrium", "potassium", "kalium",
    "calcium", "magnesium", "dihydrate", "monohydrate", "trihydrate",
    "anhydrous", "hemihydrate",
]


def strip_salt(name):
    """去掉成分名尾端的鹽類／水合物字樣。"""
    text = normalize_name(name)
    changed = True
    while changed:
        changed = False
        for word in SALT_WORDS:
            if text.endswith(" " + word):
                text = text[: -len(word) - 1].strip()
                changed = True
    return text


def normalize_name(name):
    """名稱正規化：全形轉半形、去掉重音、轉小寫、壓縮空白。"""
    if not name:
        return ""
    text = unicodedata.normalize("NFKD", str(name))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^\w\s%/-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

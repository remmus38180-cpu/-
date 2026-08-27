# -*- coding: utf-8 -*-
"""讀取要查詢的藥品清單。

支援兩種輸入：

* **純文字**：每行一個商品名（相容既有的 drug_list.csv）
* **CSV**：有表頭，欄位可用中文或英文，順序不拘

可用的欄位名（大小寫與全半形不拘）::

    商品名     brand, brand_name, product, 產品名, 藥品名
    成分名     generic, ingredient, inn, 成分, 學名
    ATC        atc, atc_code, atc代碼
    含量       strength, 規格
    劑型       form, dosage_form
    藥商       marketer, company, manufacturer, 廠商, 藥廠

只有商品名是必填。**成分名強烈建議一併提供**——跨國商品名差異大，
只靠商品名比對的漏抓率會明顯偏高。

僅使用 Python 標準函式庫。
"""

import csv
import io
import unicodedata

from .scoring import Query

__all__ = ["read_drug_list", "COLUMN_ALIASES"]

COLUMN_ALIASES = {
    "brand_name": ["商品名", "商品名稱", "藥品名", "藥品名稱", "產品名", "品名",
                   "brand", "brand_name", "product", "product_name", "trade_name"],
    "generic_name": ["成分名", "成分", "學名", "主成分",
                     "generic", "generic_name", "ingredient", "inn",
                     "active_ingredient", "substance"],
    "atc_code": ["atc", "atc代碼", "atc_code", "atc碼", "atc code"],
    "strength": ["含量", "規格", "劑量", "strength", "dose"],
    "form": ["劑型", "form", "dosage_form", "dosage form"],
    "marketer": ["藥商", "藥廠", "廠商", "藥證持有商", "公司",
                 "marketer", "company", "manufacturer", "holder"],
}

_LOOKUP = {}
for _field, _names in COLUMN_ALIASES.items():
    for _name in _names:
        _LOOKUP[_name] = _field


def _normalize_header(name):
    text = unicodedata.normalize("NFKC", str(name or "")).strip().lower()
    return text.lstrip("﻿")


def read_drug_list(data, filename=""):
    """解析藥品清單，回傳 (Query 清單, 說明訊息清單)。

    ``data`` 可以是位元組或字串。
    """
    if isinstance(data, bytes):
        for encoding in ("utf-8-sig", "utf-8", "cp950", "big5", "cp1252"):
            try:
                text = data.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            text = data.decode("utf-8", "replace")
    else:
        text = data

    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return [], ["清單是空的，沒有讀到任何藥品。"]

    messages = []
    rows = list(csv.reader(io.StringIO(text)))
    header = [_normalize_header(cell) for cell in rows[0]] if rows else []
    mapping = {index: _LOOKUP[name] for index, name in enumerate(header)
               if name in _LOOKUP}

    # 認得出至少一個欄位名，才當成有表頭的 CSV
    if mapping:
        queries = []
        for row in rows[1:]:
            values = {}
            for index, field in mapping.items():
                if index < len(row):
                    values[field] = row[index].strip()
            if not any(values.values()):
                continue
            queries.append(Query(**values))
        found = "、".join(sorted({field for field in mapping.values()}))
        messages.append(f"以有表頭的 CSV 讀入，辨識到欄位：{found}")
    else:
        queries = [Query(brand_name=line.split(",")[0].strip())
                   for line in lines if line.split(",")[0].strip()]
        messages.append("以純文字清單讀入，每行視為一個商品名。")

    if not queries:
        messages.append("沒有讀到任何藥品，請確認檔案內容。")
        return [], messages

    without_generic = sum(1 for q in queries if not q.generic_name)
    if without_generic:
        messages.append(
            f"有 {without_generic} 筆只有商品名、沒有成分名。"
            f"跨國商品名差異大，建議補上成分名以降低漏抓；"
            f"沒有成分名時仍會比對，但比對層級會偏低。")

    messages.append(f"共讀入 {len(queries)} 筆藥品。")
    return queries, messages

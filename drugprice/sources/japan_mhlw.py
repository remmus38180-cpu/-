# -*- coding: utf-8 -*-
"""日本 — 厚生労働省（MHLW）薬価基準収載品目リスト。

來源與操作手冊指定機關相同。公告頁固定，但**每次藥價改定後檔案網址會變**，
因此本模組先抓公告頁、解析出當期的三個檔案連結，不寫死網址。
（報告中記載的 ``tp20260715`` 系列在撰寫本模組時已被 ``tp20260813`` 取代，
正好說明寫死網址行不通。）

三個檔案分別為內用薬、注射薬、外用薬。

兩個日本特有的重點
------------------
1. **薬価本身就是單位價**。「規格」欄的寫法是「１ｍｇ１錠」，意思是
   每 1 錠含 1mg，薬価即為每錠的價格。因此包裝數量固定為規格所載的
   計價單位數（通常是 1），不需要再除以包裝量。

2. **原廠／學名藥有官方註記**。「先発医薬品」欄標示「先発品」者為原廠藥，
   「後発医薬品」欄標示者為學名藥。此為官方欄位，非推估。

僅使用 Python 標準函式庫。
"""

import os
import re
import unicodedata
from datetime import date

from ..core import xlsx
from ..core.schema import Confidence, PriceCategory
from ..core.units import parse_strength
from ..core.textfile import decode
from .base import Downloaded, Source

HOST = "https://www.mhlw.go.jp"

# 公告頁網址含年度，藥價改定後會換。依序嘗試本年度與前一年度。
INDEX_TEMPLATES = [
    "{host}/topics/{year}/04/tp{year}0401-01.html",
]

# 檔案序號 -> 分類
CATEGORY_FILES = {"01": "內用藥", "02": "針劑", "03": "外用藥"}

# 欄位索引（依檔案表頭核對）
COL_CATEGORY, COL_YJ_CODE, COL_GENERIC, COL_SPEC = 0, 1, 2, 3
COL_BRAND, COL_MAKER = 7, 8
COL_GENERIC_MARK, COL_ORIGINATOR_MARK = 9, 10
COL_HAS_GENERIC, COL_PRICE, COL_EXPIRY = 11, 12, 13

# 規格欄常見的計價單位
PRICING_UNITS = [
    "錠", "カプセル", "包", "瓶", "管", "本", "個", "枚", "袋", "筒",
    "キット", "バイアル", "アンプル", "シリンジ", "パック", "組", "台",
    "mL", "ml", "L", "g", "mg", "µg",
]

_SPEC_TAIL = re.compile(
    r"(\d+(?:\.\d+)?)\s*(" + "|".join(re.escape(u) for u in
                                      sorted(PRICING_UNITS, key=len, reverse=True)) + r")$")

_LINK = re.compile(r'href="([^"]*?/xls/tp(\d{8})-01_(\d{2})\.xlsx)"', re.IGNORECASE)


def parse_spec(spec):
    """解析「規格」欄，回傳 (含量原文, 計價單位數, 計價單位)。

    ``"１ｍｇ１錠"`` → ``("1mg", 1.0, "錠")``
    ``"１％１ｇ"``　 → ``("1%", 1.0, "g")``
    ``"１ｇ"``　　　 → ``("", 1.0, "g")``

    對不上就回傳 ``(原文, None, "")``，由人工處理，不猜。
    """
    if not spec:
        return "", None, ""
    text = unicodedata.normalize("NFKC", str(spec)).strip()
    match = _SPEC_TAIL.search(text)
    if not match:
        return text, None, ""
    strength = text[: match.start()].strip()
    try:
        count = float(match.group(1))
    except ValueError:
        return text, None, ""
    return strength, count, match.group(2)


class JapanMHLW(Source):
    country = "JP"
    country_name = "日本"
    agency = "厚生労働省（MHLW）"
    currency = "JPY"
    field_confidence = Confidence.OFFICIAL_DOC
    field_doc_url = ""
    probe_url = "https://www.mhlw.go.jp/topics/2026/04/tp20260401-01.html"

    def _find_index(self, ctx):
        """找出當期公告頁，回傳 (網址, 頁面內容)。"""
        year = date.today().year
        # 日本年度自 4 月起算，1 至 3 月時當期頁面仍掛在前一年度
        candidates = [year, year - 1] if date.today().month >= 4 else [year - 1, year]
        for candidate in candidates:
            for template in INDEX_TEMPLATES:
                url = template.format(host=HOST, year=candidate)
                ctx.log(f"　查詢公告頁 {url}")
                try:
                    resp = ctx.fetcher.fetch(url)
                except Exception as exc:            # noqa: BLE001 - 換下一個候選
                    ctx.log(f"　　取不到（{exc}）")
                    continue
                text, _ = decode(resp.content, ["shift_jis", "utf-8", "cp932"])
                if _LINK.search(text):
                    return url, text
        raise RuntimeError(
            "找不到厚生労働省的薬価基準公告頁。網址結構可能已變更，"
            "請至 mhlw.go.jp 搜尋「薬価基準収載品目リスト」確認新網址後回報。")

    def download(self, ctx):
        index_url, html = self._find_index(ctx)

        # 同一頁會列出多個發布日的檔案，取日期最大的那一批
        found = {}
        for href, stamp, serial in _LINK.findall(html):
            if serial not in CATEGORY_FILES:
                continue
            found.setdefault(stamp, {})[serial] = href
        if not found:
            raise RuntimeError(f"公告頁 {index_url} 內找不到藥價檔連結")

        latest = max(found)
        ctx.log(f"　當期版本：{latest[:4]}-{latest[4:6]}-{latest[6:]}")
        version = f"{latest[:4]}-{latest[4:6]}-{latest[6:]}"

        out = []
        for serial in sorted(found[latest]):
            href = found[latest][serial]
            url = href if href.startswith("http") else HOST + href
            label = CATEGORY_FILES[serial]
            ctx.log(f"　下載 {label}")
            resp = ctx.fetcher.fetch(url)
            rel, digest = ctx.store.save(
                self.country, f"tp{latest}-01_{serial}.xlsx", resp.content,
                source_url=url, status=resp.status, ssl_mode=resp.ssl_mode,
                data_version=version, source_track=self.track, notes=label)
            out.append(Downloaded(
                path=os.path.join(ctx.store.root, rel), rel_path=rel,
                sha256=digest, source_url=url, data_version=version,
                label=label, ssl_mode=resp.ssl_mode))
            ctx.log(f"　　{len(resp.content):,} 位元組")
        return out

    def parse(self, ctx, downloaded):
        records = []
        unparsed_specs = 0

        for item in downloaded:
            rows = xlsx.read_sheet(item.path, 0)
            if len(rows) < 2:
                ctx.log(f"　[注意] {item.label} 沒有資料列")
                continue

            header = [str(c).strip() for c in rows[0]]
            if len(header) <= COL_PRICE or "薬価" not in header[COL_PRICE]:
                ctx.log(f"　[注意] {item.label} 的表頭與預期不符，已略過")
                ctx.log(f"　　實際表頭：{header}")
                continue

            for row_number, row in enumerate(rows[1:], start=2):
                def cell(index):
                    return str(row[index]).strip() if index < len(row) else ""

                price = cell(COL_PRICE).replace(",", "")
                if not price:
                    continue

                strength, count, unit = parse_spec(cell(COL_SPEC))
                if count is None:
                    unparsed_specs += 1
                strength_value, strength_unit = parse_strength(strength)

                originator = ""
                if cell(COL_ORIGINATOR_MARK):
                    originator = "原廠藥（先発品）"
                elif cell(COL_GENERIC_MARK):
                    originator = "學名藥（後発品）"

                record = self._base_record(item)
                record.native_code_type = "薬価基準収載医薬品コード"
                record.native_code = cell(COL_YJ_CODE)
                record.brand_name = cell(COL_BRAND)
                record.generic_name = cell(COL_GENERIC)
                record.form = cell(COL_CATEGORY)
                record.strength_value = ("" if strength_value is None
                                         else f"{strength_value:g}")
                record.strength_unit = strength_unit
                record.pack_size_value = "" if count is None else f"{count:g}"
                record.pack_size_unit = unit
                record.price = price
                record.price_category = PriceCategory.REIMBURSEMENT
                record.price_category_label = PriceCategory.label(
                    PriceCategory.REIMBURSEMENT)
                record.marketer = cell(COL_MAKER)
                record.originator_flag = originator
                record.source_row = f"{item.label} 第 {row_number} 列"
                record.notes = "；".join(part for part in (
                    f"規格：{cell(COL_SPEC)}",
                    "有同劑形同規格學名藥" if cell(COL_HAS_GENERIC) else "",
                    f"經過措置期限：{cell(COL_EXPIRY)}" if cell(COL_EXPIRY) else "",
                ) if part)
                record.compute_unit_price()
                records.append(record)

        if unparsed_specs:
            ctx.log(f"　[注意] 有 {unparsed_specs:,} 筆的「規格」欄無法拆出計價單位，"
                    f"已保留原文於備註，單位藥價留空")
        return records


SOURCE = JapanMHLW()

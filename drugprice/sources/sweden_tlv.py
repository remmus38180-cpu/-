# -*- coding: utf-8 -*-
"""瑞典 — TLV（Tandvårds- och läkemedelsförmånsverket，藥物福利委員會）。

TLV 是瑞典官方的藥價與給付訂定機關。操作手冊原指定的 FASS 由藥廠公會
（LIF）經營，非政府機關，且未提供整批下載。

下載連結固定為 ``https://www.tlv.se/file/medprice``，免登入、免查詢，
官方說明為每日更新。已由同仁實際下載確認為完整資料庫檔案。

檔案結構（真實檔案核對）::

    Produktnamn | Varunummer | ATC-kod | NPL id | NPL pack-id |
    Form | Styrka | Förpackning | Antal | Företag | AIP | AUP

**一列會產生兩筆記錄**：AIP（藥局採購價）與 AUP（藥局零售價）是兩種
不同層級的價格，不可混用，因此各自獨立成一筆並標示價格類別。

僅使用 Python 標準函式庫。
"""

from ..core import xlsx
from ..core.schema import Confidence, PriceCategory
from ..core.units import parse_pack_size, parse_strength
from .base import Downloaded, Source

DOWNLOAD_URL = "https://www.tlv.se/file/medprice"

# 原始欄位名 -> 中文，供人工核對用
FIELD_LABELS = {
    "Produktnamn": "藥品名稱",
    "Varunummer": "商品編號",
    "ATC-kod": "ATC代碼",
    "NPL id": "北歐藥品編號",
    "NPL pack-id": "北歐包裝編號",
    "Form": "劑型",
    "Styrka": "含量",
    "Förpackning": "包裝說明",
    "Antal": "包裝數量",
    "Företag": "藥證持有商",
    "AIP": "藥局採購價",
    "AUP": "藥局零售價",
}

PRICE_COLUMNS = [
    ("AIP", PriceCategory.PHARMACY_PURCHASE),
    ("AUP", PriceCategory.RETAIL),
]


class SwedenTLV(Source):
    country = "SE"
    country_name = "瑞典"
    agency = "TLV 藥物福利委員會"
    currency = "SEK"
    field_confidence = Confidence.VERIFIED_FILE
    field_doc_url = ""
    probe_url = "https://www.tlv.se/file/medprice"

    def download(self, ctx):
        ctx.log(f"　下載 {DOWNLOAD_URL}")
        resp = ctx.fetcher.fetch(DOWNLOAD_URL)

        # 檔名不含日期，改用伺服器提供的最後修改時間當版本資訊
        version = (resp.headers.get("Last-Modified") or "")[:16]
        rel, digest = ctx.store.save(
            self.country, "tlv_medprice.xlsx", resp.content,
            source_url=DOWNLOAD_URL, status=resp.status,
            ssl_mode=resp.ssl_mode, data_version=version,
            source_track=self.track, notes="TLV 完整藥價資料庫")
        ctx.log(f"　已存檔 {len(resp.content):,} 位元組")

        import os
        return [Downloaded(
            path=os.path.join(ctx.store.root, rel), rel_path=rel,
            sha256=digest, source_url=DOWNLOAD_URL,
            data_version=version, label="藥價資料庫", ssl_mode=resp.ssl_mode)]

    def parse(self, ctx, downloaded):
        records = []
        for item in downloaded:
            rows = xlsx.read_sheet(item.path, 0)
            if not rows:
                ctx.log("　[注意] 檔案沒有任何資料列")
                continue

            header = [str(cell).strip() for cell in rows[0]]
            index = {name: pos for pos, name in enumerate(header)}

            missing = [name for name in ("Produktnamn", "Antal", "AIP", "AUP")
                       if name not in index]
            if missing:
                ctx.log(f"　[注意] 檔案缺少預期欄位：{', '.join(missing)}")
                ctx.log(f"　　實際欄位：{', '.join(header)}")
                continue

            def cell(row, name):
                pos = index.get(name)
                if pos is None or pos >= len(row):
                    return ""
                return str(row[pos]).strip()

            for row_number, row in enumerate(rows[1:], start=2):
                if not any(str(c).strip() for c in row):
                    continue
                name = cell(row, "Produktnamn")
                if not name:
                    continue

                strength_text = cell(row, "Styrka")
                strength_value, strength_unit = parse_strength(strength_text)
                package_text = cell(row, "Förpackning")

                # Antal 是乾淨的數字但沒有單位；單位要從 Förpackning
                # （如「Blister, 30 tabletter」）取得
                pack_value, pack_unit, _ = parse_pack_size(cell(row, "Antal"))
                package_value, package_unit, _ = parse_pack_size(package_text)
                if pack_value is None:
                    pack_value, pack_unit = package_value, package_unit
                elif not pack_unit:
                    pack_unit = package_unit

                for column, category in PRICE_COLUMNS:
                    price = cell(row, column).replace(",", ".")
                    if not price or price in ("-", "0", "0.00"):
                        continue

                    record = self._base_record(item)
                    record.native_code_type = "Varunummer"
                    record.native_code = cell(row, "Varunummer")
                    record.brand_name = name
                    record.atc_code = cell(row, "ATC-kod").strip()
                    record.form = cell(row, "Form")
                    record.strength_value = ("" if strength_value is None
                                             else f"{strength_value:g}")
                    record.strength_unit = strength_unit
                    record.pack_size_value = ("" if pack_value is None
                                              else f"{pack_value:g}")
                    record.pack_size_unit = pack_unit
                    record.price = price
                    record.price_category = category
                    record.price_category_label = PriceCategory.label(category)
                    record.marketer = cell(row, "Företag")
                    record.source_row = f"第 {row_number} 列／{column} 欄"
                    # 複方藥的含量欄（如 600 mg/300 mg）只會解析出第一個成分，
                    # 原文一併留存供人工核對
                    record.notes = "；".join(
                        part for part in (package_text,
                                          f"含量原文：{strength_text}"
                                          if strength_text else "")
                        if part)
                    record.compute_unit_price()
                    records.append(record)
        return records


SOURCE = SwedenTLV()

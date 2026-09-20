# -*- coding: utf-8 -*-
"""加拿大薩克其萬省 — Saskatchewan Drug Plan Formulary。

**本模組推翻了先前的兩項結論**（2026-09-14 重新查證）

1. 先前記載「站台 robots.txt 擋自動化」。實際上該站**沒有 robots.txt**：
   ``/robots.txt`` 回傳的是單頁應用程式的首頁 HTML，與任意不存在的路徑
   （如 ``/nonexistent-xyz``）回應完全相同，代表根本沒有這個檔案。

2. 先前記載「查無官方整批下載，僅有 PDF」。實際上官網提供
   **Drug Plan Formulary in Fixed Width Format**——固定寬度純文字檔，
   **並附官方欄位版面說明文件**。查詢頁是 Vue 單頁應用程式，
   下載連結寫在 JavaScript 套件裡，從首頁 HTML 看不到，因此先前漏掉。

這正好符合專案避雷紀錄裡的那條：瑞典、比利時、德國的「找不到整批下載」
結論後來都被推翻，薩省也是同一回事。

檔案
----
資料檔　``/Publns/Formularyv{版本}_172fw.txt``（約 830 KB、10,345 列）
版面說明``/Publns/FormularyLayout.txt``（官方逐欄位定義）

檔案為**階層式**結構，每列第 1 個字元是記錄型態::

    1  大分類（ASHP Major Class）
    2  次分類（ASHP Minor Class）
    3  次分類的治療注意事項
    4  序號 1 = 成分名；序號 2 或 3 = 含量與劑型
    5  成分名的治療注意事項
    6  產品（含 DIN、商品名、廠商、單位成本）

產品列本身不含成分名與規格，必須沿用前面出現的第 4 型記錄，
因此解析時要一路帶著目前的分類、成分名與規格。

**Unit Cost 欄位格式為 999v9999**，即 7 位數字隱含 4 位小數
（``0104950`` 代表 10.4950）。這是官方版面文件明定的，非推估。
且它**本身就是單位價**，不需要再除以包裝量。

僅使用 Python 標準函式庫。
"""

import os
import re

from ..core.schema import Confidence, PriceCategory
from ..core.textfile import decode
from ..core.units import parse_strength
from .base import Downloaded, Source

HOST = "https://formulary.drugplan.ehealthsask.ca"
LAYOUT_URL = f"{HOST}/Publns/FormularyLayout.txt"
DATA_URL_TEMPLATE = HOST + "/Publns/Formularyv{version}_172fw.txt"

# 現行版本。抓不到時會自動往前一版重試。
CURRENT_VERSION = 62
VERSIONS_BACK = 4

# --- 官方版面（位置為 1 起算，程式內轉成 0 起算的切片）---
# 產品列（記錄型態 6）
P_DRUG_INDICATOR = slice(1, 2)      # 空白 = Formulary；1 = 例外給付（EDS）
P_MINOR_CLASS = slice(3, 9)
P_MAC_INDICATOR = slice(9, 10)
P_DIN = slice(28, 36)
P_PRODUCT_CODE = slice(37, 39)
P_PRODUCT_NAME = slice(40, 65)
P_MANUFACTURER = slice(66, 69)
P_UNIT_COST = slice(70, 77)
P_SOC_INDICATOR = slice(77, 78)
P_DRUG_TYPE = slice(78, 79)

# 分類與成分名列
C_CLASS_CODE = slice(3, 9)
C_CLASS_NAME = slice(10, 73)
G_MAC_INDICATOR = slice(9, 10)
G_NAME = slice(28, 73)
S_INTERCHANGEABLE = slice(27, 28)
S_TEXT = slice(28, 73)

UNIT_COST_DECIMALS = 4

DRUG_TYPE_LABELS = {"F": "一般給付（Formulary）", "E": "例外給付（EDS）"}
INTERCHANGEABLE_LABELS = {"*": "可替代", "?": "不可替代"}


class CanadaSaskatchewan(Source):
    country = "CA-SK"
    country_name = "加拿大薩克其萬省"
    agency = "Saskatchewan Drug Plan（DPEB／eHealth Saskatchewan）"
    currency = "CAD"
    field_confidence = Confidence.OFFICIAL_DOC
    field_doc_url = LAYOUT_URL
    probe_url = LAYOUT_URL

    def download(self, ctx):
        ctx.log("　下載官方欄位版面說明")
        layout = ctx.fetcher.fetch(LAYOUT_URL)
        layout_rel, layout_digest = ctx.store.save(
            self.country, "FormularyLayout.txt", layout.content,
            source_url=LAYOUT_URL, status=layout.status,
            ssl_mode=layout.ssl_mode, source_track=self.track,
            notes="官方逐欄位版面說明")

        for offset in range(VERSIONS_BACK):
            version = CURRENT_VERSION - offset
            url = DATA_URL_TEMPLATE.format(version=version)
            ctx.log(f"　嘗試第 {version} 版")
            try:
                resp = ctx.fetcher.fetch(url)
            except Exception as exc:                  # noqa: BLE001 - 往前一版
                ctx.log(f"　　取不到（{exc}）")
                continue

            rel, digest = ctx.store.save(
                self.country, f"Formularyv{version}_172fw.txt", resp.content,
                source_url=url, status=resp.status, ssl_mode=resp.ssl_mode,
                data_version=f"v{version}", source_track=self.track,
                notes="固定寬度格式藥品清單")
            ctx.log(f"　取得第 {version} 版，{len(resp.content):,} 位元組")
            return [
                Downloaded(path=os.path.join(ctx.store.root, rel), rel_path=rel,
                           sha256=digest, source_url=url,
                           data_version=f"v{version}", label="藥品清單",
                           ssl_mode=resp.ssl_mode),
                Downloaded(path=os.path.join(ctx.store.root, layout_rel),
                           rel_path=layout_rel, sha256=layout_digest,
                           source_url=LAYOUT_URL, label="欄位版面說明",
                           ssl_mode=layout.ssl_mode),
            ]

        raise RuntimeError(
            f"往前找了 {VERSIONS_BACK} 版都取不到薩省的固定寬度檔。"
            f"版本號可能已超前，請至 {HOST} 的「Formulary in Fixed Width Format」"
            f"頁面確認現行版本後回報。")

    def parse(self, ctx, downloaded):
        records = []
        for item in downloaded:
            if item.label != "藥品清單":
                continue
            with open(item.path, "rb") as fh:
                text, encoding = decode(fh.read(), ["cp1252", "utf-8"])
            ctx.log(f"　編碼 {encoding}")

            major_class = minor_class = ""
            generic_name = strength_text = ""
            interchangeable = ""
            skipped = 0

            for line_number, line in enumerate(text.splitlines(), start=1):
                if not line.strip():
                    continue
                kind = line[0]

                if kind == "1":
                    major_class = line[C_CLASS_NAME].strip()
                    minor_class = ""
                    continue
                if kind == "2":
                    minor_class = line[C_CLASS_NAME].strip()
                    continue
                if kind == "4":
                    if line[1:2] == "1":
                        # 成分名。換了成分就要把規格清掉，否則會沿用到別的成分
                        generic_name = line[G_NAME].strip()
                        strength_text = ""
                        interchangeable = ""
                    else:
                        strength_text = line[S_TEXT].strip()
                        interchangeable = INTERCHANGEABLE_LABELS.get(
                            line[S_INTERCHANGEABLE], "")
                    continue
                if kind != "6":
                    continue                       # 3、5 為說明文字，不入表

                cost = self._unit_cost(line[P_UNIT_COST])
                if cost is None:
                    skipped += 1
                    continue

                strength_value, strength_unit = parse_strength(strength_text)
                drug_type = line[P_DRUG_TYPE].strip()

                record = self._base_record(item)
                record.native_code_type = "DIN"
                record.native_code = line[P_DIN].strip()
                record.brand_name = line[P_PRODUCT_NAME].strip()
                record.generic_name = generic_name
                record.form = strength_text
                record.strength_value = ("" if strength_value is None
                                         else f"{strength_value:g}")
                record.strength_unit = strength_unit
                # Unit Cost 本身就是單位價，包裝量固定為 1
                record.pack_size_value = "1"
                record.pack_size_unit = "單位"
                record.price = f"{cost:.4f}".rstrip("0").rstrip(".")
                record.price_category = PriceCategory.REIMBURSEMENT
                record.price_category_label = PriceCategory.label(
                    PriceCategory.REIMBURSEMENT)
                record.marketer = line[P_MANUFACTURER].strip()
                # 本檔案沒有原廠／學名藥註記欄位，留空由人判斷
                record.originator_flag = ""
                record.source_row = f"第 {line_number} 列（記錄型態 6）"
                record.notes = "；".join(part for part in (
                    f"大分類：{major_class}" if major_class else "",
                    f"次分類：{minor_class}" if minor_class else "",
                    f"給付別：{DRUG_TYPE_LABELS.get(drug_type, drug_type)}"
                    if drug_type else "",
                    interchangeable,
                    "最高可給付金額群組（MAC）"
                    if line[P_MAC_INDICATOR].strip() == "M" else "",
                    f"廠商代碼：{line[P_MANUFACTURER].strip()}"
                    if line[P_MANUFACTURER].strip() else "",
                ) if part)
                record.compute_unit_price()
                records.append(record)

            if skipped:
                ctx.log(f"　[注意] 有 {skipped:,} 列的單位成本欄無法解析，已略過")
        return records

    @staticmethod
    def _unit_cost(raw):
        """解析 999v9999 格式：7 位數字，隱含 4 位小數。"""
        digits = (raw or "").strip()
        if not digits or not digits.isdigit():
            return None
        return int(digits) / (10 ** UNIT_COST_DECIMALS)


SOURCE = CanadaSaskatchewan()

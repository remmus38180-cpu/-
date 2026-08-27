# -*- coding: utf-8 -*-
"""法國（藥局零售 CIP）— base-donnees-publique.medicaments.gouv.fr。

操作手冊指定的來源為 BdM_IT（CNAM 法國健保局）。整批下載改採 ANSM／HAS
共同維運的法國公開藥品資料庫，兩者均為法國政府機關，法定零售價為同一組
數字，僅發布機關不同。

三個檔案以「Code CIS」合併::

    CIS_bdpm.txt        藥品主檔（名稱、劑型、給藥途徑、藥證持有商）
    CIS_CIP_bdpm.txt    包裝及藥價檔（CIP7／CIP13、包裝說明、價格）
    CIS_GENER_bdpm.txt  學名藥群組對照檔（**含原廠／學名藥註記**）

兩個注意事項
------------
1. **三個檔案的編碼不一致**：CIS_bdpm 與 CIS_GENER 為 cp1252，
   CIS_CIP_bdpm 為 UTF-8。寫死單一編碼會讓價格檔的法文重音字變成亂碼。
   本模組使用自動偵測（見 ``core.textfile``）。

2. **價格有兩種**：未含調劑費與含調劑費，兩者相差一筆
   honoraire de dispensation。這是兩個不同的數字，各自獨立成一筆記錄
   並標示價格類別，不可混用。

僅使用 Python 標準函式庫。
"""

import os

from ..core.schema import Confidence, PriceCategory
from ..core.textfile import read_delimited
from ..core.units import parse_pack_size, parse_strength
from .base import Downloaded, Source

BASE_URL = "https://base-donnees-publique.medicaments.gouv.fr/download/file/"

FILES = [
    ("CIS_bdpm.txt", "藥品主檔"),
    ("CIS_CIP_bdpm.txt", "包裝及藥價檔"),
    ("CIS_GENER_bdpm.txt", "學名藥群組對照檔"),
]

# --- CIS_bdpm.txt 欄位（依官方欄位說明）---
CIS_CODE, CIS_NAME, CIS_FORM, CIS_ROUTE = 0, 1, 2, 3
CIS_AMM_STATUS, CIS_PROCEDURE, CIS_MARKETING_STATUS = 4, 5, 6
CIS_AMM_DATE, CIS_BDM_STATUS, CIS_EU_NUMBER = 7, 8, 9
CIS_HOLDER, CIS_ENHANCED_SURVEILLANCE = 10, 11

# --- CIS_CIP_bdpm.txt 欄位 ---
CIP_CIS, CIP_CIP7, CIP_LABEL, CIP_STATUS = 0, 1, 2, 3
CIP_MARKETING, CIP_DECL_DATE, CIP_CIP13 = 4, 5, 6
CIP_COLLECTIVITY, CIP_REIMBURSE_RATE = 7, 8
CIP_PRICE, CIP_PRICE_WITH_FEE, CIP_FEE, CIP_INDICATIONS = 9, 10, 11, 12

# --- CIS_GENER_bdpm.txt 欄位 ---
GEN_GROUP_ID, GEN_GROUP_LABEL, GEN_CIS, GEN_TYPE, GEN_SORT = 0, 1, 2, 3, 4

# 「Type de générique」代碼。0 代表 princeps，也就是原廠藥。
GENERIC_TYPE_LABELS = {
    "0": "原廠藥（princeps）",
    "1": "學名藥（générique）",
    "2": "學名藥（劑量互補）",
    "4": "學名藥（可替代）",
}

PRICE_COLUMNS = [
    (CIP_PRICE, PriceCategory.RETAIL),
    (CIP_PRICE_WITH_FEE, PriceCategory.RETAIL_WITH_FEE),
]


class FranceCIP(Source):
    country = "FR"
    country_name = "法國（藥局零售）"
    agency = "ANSM／HAS 公開藥品資料庫"
    currency = "EUR"
    field_confidence = Confidence.OFFICIAL_DOC
    field_doc_url = "https://base-donnees-publique.medicaments.gouv.fr/telechargement.php"
    probe_url = ("https://base-donnees-publique.medicaments.gouv.fr/download/file/CIS_bdpm.txt")

    def download(self, ctx):
        out = []
        for filename, label in FILES:
            url = BASE_URL + filename
            ctx.log(f"　下載 {label}：{filename}")
            resp = ctx.fetcher.fetch(url)
            rel, digest = ctx.store.save(
                self.country, filename, resp.content, source_url=url,
                status=resp.status, ssl_mode=resp.ssl_mode,
                source_track=self.track, notes=label)
            out.append(Downloaded(
                path=os.path.join(ctx.store.root, rel), rel_path=rel,
                sha256=digest, source_url=url, label=label,
                ssl_mode=resp.ssl_mode))
            ctx.log(f"　　{len(resp.content):,} 位元組")
        return out

    def parse(self, ctx, downloaded):
        by_name = {os.path.basename(d.rel_path): d for d in downloaded}
        for filename, _ in FILES:
            if filename not in by_name:
                ctx.log(f"　[注意] 缺少 {filename}，無法合併")
                return []

        master, master_encoding = self._load(by_name["CIS_bdpm.txt"])
        packs, pack_encoding = self._load(by_name["CIS_CIP_bdpm.txt"])
        groups, _ = self._load(by_name["CIS_GENER_bdpm.txt"])
        ctx.log(f"　編碼：藥品主檔 {master_encoding}／藥價檔 {pack_encoding}")

        # Code CIS -> 藥品主檔那一列
        drugs = {row[CIS_CODE]: row for row in master
                 if len(row) > CIS_HOLDER and row[CIS_CODE]}

        # Code CIS -> (原廠註記, 群組名稱)
        originator = {}
        for row in groups:
            if len(row) <= GEN_TYPE or not row[GEN_CIS]:
                continue
            originator[row[GEN_CIS]] = (
                GENERIC_TYPE_LABELS.get(row[GEN_TYPE], row[GEN_TYPE]),
                row[GEN_GROUP_LABEL] if len(row) > GEN_GROUP_LABEL else "")

        item = by_name["CIS_CIP_bdpm.txt"]
        records = []
        unmatched = 0

        for row_number, row in enumerate(packs, start=1):
            if len(row) <= CIP_PRICE_WITH_FEE:
                continue
            cis = row[CIP_CIS]
            drug = drugs.get(cis)
            if drug is None:
                unmatched += 1

            label = row[CIP_LABEL]
            name = drug[CIS_NAME] if drug else ""
            strength_value, strength_unit = parse_strength(name)
            pack_value, pack_unit, _ = parse_pack_size(label)
            flag, group_label = originator.get(cis, ("", ""))

            for column, category in PRICE_COLUMNS:
                price = row[column].replace(",", ".").strip()
                if not price or price in ("0", "0.00"):
                    continue

                record = self._base_record(item)
                record.native_code_type = "CIP13"
                record.native_code = row[CIP_CIP13] if len(row) > CIP_CIP13 else ""
                record.brand_name = name
                record.form = drug[CIS_FORM] if drug else ""
                record.strength_value = ("" if strength_value is None
                                         else f"{strength_value:g}")
                record.strength_unit = strength_unit
                record.pack_size_value = ("" if pack_value is None
                                          else f"{pack_value:g}")
                record.pack_size_unit = pack_unit
                record.price = price
                record.price_category = category
                record.price_category_label = PriceCategory.label(category)
                record.marketer = drug[CIS_HOLDER].strip() if drug else ""
                record.originator_flag = flag
                record.first_listed_date = drug[CIS_AMM_DATE] if drug else ""
                record.source_row = f"CIS_CIP_bdpm.txt 第 {row_number} 列／第 {column + 1} 欄"
                record.notes = "；".join(part for part in (
                    label,
                    f"給付比例：{row[CIP_REIMBURSE_RATE]}"
                    if len(row) > CIP_REIMBURSE_RATE and row[CIP_REIMBURSE_RATE] else "",
                    f"調劑費：{row[CIP_FEE]}"
                    if len(row) > CIP_FEE and row[CIP_FEE] else "",
                    f"學名藥群組：{group_label}" if group_label else "",
                ) if part)
                record.compute_unit_price()
                records.append(record)

        if unmatched:
            ctx.log(f"　[注意] 有 {unmatched:,} 列的 Code CIS 在藥品主檔中找不到，"
                    f"已保留價格但缺少名稱與藥商")
        return records

    @staticmethod
    def _load(downloaded):
        with open(downloaded.path, "rb") as fh:
            return read_delimited(fh.read())


SOURCE = FranceCIP()

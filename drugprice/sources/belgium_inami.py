# -*- coding: utf-8 -*-
"""比利時 — INAMI／RIZIV（比利時聯邦健康保險署）。

操作手冊指定的 CBIP 為非營利機構、非政府機關，其網頁價格資料本身標註
來源即為 INAMI。本模組採用 INAMI 每月發布的可給付藥品清單。

檔案為每月 1 日發布的 Excel，網址格式固定::

    https://www.riziv.fgov.be/SiteCollectionDocuments/liste_specialites_YYYYMM01.xlsx

當月尚未發布時自動往前一個月重試。

活頁簿為關聯式結構，用到三張工作表（欄位語意依官方欄位說明文件確認）::

    SPECIALITY  S_COD、品名、含量、藥商、ATC、原廠／學名藥註記
    PACKING     包裝說明（法文／荷蘭文）
    PRICES      依交付模式分列的價格

**交付模式（SPB_DEL_ID）會改變價格的意義**：1 公眾、2 門診、3 住院、
4 出廠、5 安養機構。同一個藥品在不同交付模式下是不同的數字，
因此價格類別代碼一併帶上交付模式，只有完全相同的代碼才可互相比較。

**同一組（藥品碼、交付模式）可能有多列不同生效日的價格**，
必須取生效日不晚於本期版本的最新一列，否則會誤取到歷史價格。

官方欄位說明文件：
https://www.riziv.fgov.be/SiteCollectionDocuments/liste-specialites-pharmaceutiques-remboursables-description-fichier-reference.pdf

僅使用 Python 標準函式庫。
"""

import os
from datetime import date

from ..core import xlsx
from ..core.schema import Confidence, PriceCategory
from ..core.units import parse_pack_size, parse_strength
from .base import Downloaded, Source

URL_TEMPLATE = ("https://www.riziv.fgov.be/SiteCollectionDocuments/"
                "liste_specialites_{stamp}.xlsx")

# SPB_DEL_ID -> (代碼後綴, 中文說明)
DELIVERY_MODES = {
    "1": ("PUBLIQUE", "公眾"),
    "2": ("AMBULATOIRE", "門診"),
    "3": ("HOSPITALISEE", "住院"),
    "4": ("EX_USINE", "出廠"),
    "5": ("MAISON_REPOS", "安養機構"),
}

# SPECIALITY 欄位
SP_COD, SP_NAM, SP_SPECIF, SP_ORGA, SP_ATC = 0, 1, 2, 3, 4
SP_OGC_NL, SP_OGC_FR, SP_ADMIS_DAT = 11, 12, 13

# PACKING 欄位
PK_COD, PK_DEL_ID, PK_LBL_FR, PK_LBL_NL = 0, 1, 2, 3

# PRICES 欄位
PR_COD, PR_DEL_ID, PR_PUBLIC, PR_BASE, PR_R_BASE, PR_DIFF, PR_DAT_BEG = range(7)

# OGC_LBL_FR 的值 -> 中文。實際檔案裡的寫法比官方文件列的四種多
# （含生物藥、平行輸入、孤兒藥等），因此改用字首比對，並一律把法文原文
# 附在括號內，讓人工判讀時能看到原始依據。
ORIGINATOR_PREFIXES = [
    ("spécialité de bioréférence", "生物原廠藥"),
    ("spécialité de référence", "原廠藥"),
    ("spécialité originale", "原廠藥"),
    ("générique avec plus-value", "加值型學名藥"),
    ("générique", "學名藥"),
    ("biosimilaire", "生物相似藥"),
    ("biologique", "生物藥"),
    ("copie", "仿製藥"),
    ("distribution parallèle", "平行配銷"),
    ("spécialité importée de façon parallèle", "平行輸入"),
    ("médicament orphelin", "孤兒藥"),
    ("spécialité radiopharmaceutique", "放射性藥品"),
    ("préparation magistrale", "調製處方"),
    ("dispositif médical", "醫療器材"),
]


def originator_label(raw):
    """把 OGC_LBL_FR 轉成中文說明，法文原文一併保留。"""
    text = (raw or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    for prefix, chinese in ORIGINATOR_PREFIXES:
        if lowered.startswith(prefix):
            return f"{chinese}（{text}）"
    return text


class BelgiumINAMI(Source):
    country = "BE"
    country_name = "比利時"
    agency = "INAMI／RIZIV 聯邦健康保險署"
    currency = "EUR"
    field_confidence = Confidence.OFFICIAL_DOC
    field_doc_url = ("https://www.riziv.fgov.be/SiteCollectionDocuments/"
                     "liste-specialites-pharmaceutiques-remboursables-"
                     "description-fichier-reference.pdf")
    probe_url = ("https://www.riziv.fgov.be/SiteCollectionDocuments/"
                 "liste-specialites-pharmaceutiques-remboursables-"
                 "description-fichier-reference.pdf")

    def download(self, ctx, months_back=6):
        today = date.today()
        year, month = today.year, today.month

        for attempt in range(months_back):
            stamp = f"{year:04d}{month:02d}01"
            url = URL_TEMPLATE.format(stamp=stamp)
            ctx.log(f"　嘗試 {year}-{month:02d} 版本")
            try:
                resp = ctx.fetcher.fetch(url)
            except Exception as exc:                 # noqa: BLE001 - 往前一個月
                ctx.log(f"　　未發布或取不到（{exc}）")
                month -= 1
                if month == 0:
                    year, month = year - 1, 12
                continue

            version = f"{year:04d}-{month:02d}-01"
            rel, digest = ctx.store.save(
                self.country, f"liste_specialites_{stamp}.xlsx", resp.content,
                source_url=url, status=resp.status, ssl_mode=resp.ssl_mode,
                data_version=version, source_track=self.track,
                notes="可給付藥品清單")
            ctx.log(f"　取得 {version} 版本，{len(resp.content):,} 位元組")
            return [Downloaded(
                path=os.path.join(ctx.store.root, rel), rel_path=rel,
                sha256=digest, source_url=url, data_version=version,
                label="可給付藥品清單", ssl_mode=resp.ssl_mode)]

        raise RuntimeError(
            f"往前找了 {months_back} 個月都取不到 INAMI 的藥品清單。"
            f"網址格式可能已變更，請至 riziv.fgov.be 確認後回報。")

    def parse(self, ctx, downloaded):
        records = []
        for item in downloaded:
            cutoff = (item.data_version or "9999-12-31").replace("-", "")

            specialities = self._index_specialities(item.path)
            packings = self._index_packings(item.path)
            prices = self._latest_prices(item.path, cutoff)
            ctx.log(f"　藥品 {len(specialities):,} 項／包裝 {len(packings):,} 項／"
                    f"價格 {len(prices):,} 組")

            for (code, mode), row in sorted(prices.items()):
                speciality = specialities.get(code)
                if speciality is None:
                    continue
                mode_code, mode_name = DELIVERY_MODES.get(mode, (mode, mode))
                package = packings.get((code, mode)) or packings.get((code, "1")) or ""

                strength_value, strength_unit = parse_strength(speciality["strength"])
                pack_value, pack_unit, _ = parse_pack_size(package)

                for column, base_code, base_name in (
                        (PR_PUBLIC, PriceCategory.RETAIL_TAXED, "公眾價格"),
                        (PR_BASE, PriceCategory.REIMBURSEMENT, "給付基準"),
                        (PR_R_BASE, PriceCategory.REFERENCE, "給付基準（R 代碼）"),
                        (PR_DIFF, PriceCategory.PATIENT_SUPPLEMENT, "自付差額")):
                    price = self._number(row, column)
                    if price is None or price == 0:
                        continue

                    record = self._base_record(item)
                    record.native_code_type = "INAMI 代碼"
                    record.native_code = code
                    record.brand_name = speciality["name"]
                    record.generic_name = speciality["ingredient"]
                    record.atc_code = speciality["atc"]
                    record.strength_value = ("" if strength_value is None
                                             else f"{strength_value:g}")
                    record.strength_unit = strength_unit
                    record.pack_size_value = ("" if pack_value is None
                                              else f"{pack_value:g}")
                    record.pack_size_unit = pack_unit
                    record.price = f"{price:g}"
                    record.price_category = f"{base_code}@{mode_code}"
                    record.price_category_label = f"{base_name}（{mode_name}交付）"
                    record.marketer = speciality["firm"]
                    record.originator_flag = speciality["originator"]
                    record.first_listed_date = speciality["admis_date"]
                    record.source_row = (f"PRICES 工作表 {code}／交付模式 {mode}"
                                         f"／生效日 {row[PR_DAT_BEG]}")
                    record.notes = "；".join(part for part in (
                        package,
                        f"含量原文：{speciality['strength']}"
                        if speciality["strength"] else "",
                    ) if part)
                    record.compute_unit_price()
                    records.append(record)
        return records

    # ------------------------------------------------------------ 工作表索引

    @staticmethod
    def _number(row, index):
        if index >= len(row):
            return None
        try:
            return float(str(row[index]).replace(",", ".").strip())
        except ValueError:
            return None

    def _index_specialities(self, path):
        rows = xlsx.read_sheet(path, "SPECIALITY")
        ingredients = self._index_ingredients(path)
        out = {}
        for row in rows[1:]:
            if not row or not row[SP_COD]:
                continue
            def cell(index):
                return str(row[index]).strip() if index < len(row) else ""

            out[cell(SP_COD)] = {
                "name": cell(SP_NAM),
                "strength": cell(SP_SPECIF),
                "firm": cell(SP_ORGA),
                "atc": cell(SP_ATC),
                "originator": originator_label(cell(SP_OGC_FR)),
                "admis_date": cell(SP_ADMIS_DAT),
                "ingredient": ingredients.get(cell(SP_COD), ""),
            }
        return out

    @staticmethod
    def _index_ingredients(path):
        """成分名在第一張工作表，以 S_COD 對應。"""
        try:
            rows = xlsx.read_sheet(path, 0)
        except KeyError:
            return {}
        if not rows:
            return {}
        header = [str(c).strip() for c in rows[0]]
        try:
            code_col = header.index("S_COD")
            ingredient_col = header.index("ACTIVE_INGREDIENT")
        except ValueError:
            return {}
        out = {}
        for row in rows[1:]:
            if len(row) > max(code_col, ingredient_col) and row[code_col]:
                out.setdefault(str(row[code_col]).strip(),
                               str(row[ingredient_col]).strip())
        return out

    @staticmethod
    def _index_packings(path):
        rows = xlsx.read_sheet(path, "PACKING")
        out = {}
        for row in rows[1:]:
            if len(row) <= PK_LBL_FR or not row[PK_COD]:
                continue
            key = (str(row[PK_COD]).strip(), str(row[PK_DEL_ID]).strip())
            out.setdefault(key, str(row[PK_LBL_FR]).strip())
        return out

    @staticmethod
    def _latest_prices(path, cutoff):
        """每組（藥品碼, 交付模式）只保留生效日不晚於本期版本的最新一列。"""
        rows = xlsx.read_sheet(path, "PRICES")
        best = {}
        for row in rows[1:]:
            if len(row) <= PR_DAT_BEG or not row[PR_COD]:
                continue
            key = (str(row[PR_COD]).strip(), str(row[PR_DEL_ID]).strip())
            begin = str(row[PR_DAT_BEG]).strip().replace("-", "")
            if begin and begin > cutoff:
                continue                      # 尚未生效的未來價格
            current = best.get(key)
            if current is None or begin > str(current[PR_DAT_BEG]).replace("-", ""):
                best[key] = row
        return best


SOURCE = BelgiumINAMI()

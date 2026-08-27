# -*- coding: utf-8 -*-
"""統一藥價欄位定義。

十國的原始檔格式各不相同，全部轉成本模組定義的同一組欄位後，
比對、排序、匯出才有共同基礎。

三個設計決定
------------
1. **價格類別是必填欄位**。各國公布的不是同一種價格（出廠價／零售價／
   給付價／參考價），混在同一欄比較會產生系統性偏差。每一筆價格都必須
   自己說明它是哪一種。

2. **包裝數量與價格分開存，單位藥價保留分子分母**。單位藥價是算出來的，
   覆核時要能看到它是怎麼算的。

3. **欄位對照可信度要標示**。有官方逐欄位定義文件的國家（法國、比利時、
   澳洲）與只能推估的國家（瑞士）不應等同看待。

僅使用 Python 標準函式庫。
"""

import csv
import dataclasses
import io
import os
from datetime import datetime, timedelta, timezone

__all__ = ["PriceRecord", "PriceCategory", "Confidence", "SourceTrack",
           "write_csv", "read_csv", "TAIPEI", "now_stamp"]

TAIPEI = timezone(timedelta(hours=8))


def now_stamp():
    """台北時間的 ISO 8601 字串，佐證用。"""
    return datetime.now(TAIPEI).isoformat(timespec="seconds")


class PriceCategory:
    """價格類別代碼與中文說明。

    排序與比較只能在**同一個類別內**進行。
    """

    EX_FACTORY = "EX_FACTORY"
    PHARMACY_PURCHASE = "PHARMACY_PURCHASE"
    RETAIL = "RETAIL"
    RETAIL_TAXED = "RETAIL_TAXED"
    RETAIL_WITH_FEE = "RETAIL_WITH_FEE"
    DISPENSING_FEE = "DISPENSING_FEE"
    REIMBURSEMENT = "REIMBURSEMENT"
    REFERENCE = "REFERENCE"
    CLAIMED = "CLAIMED"
    DETERMINED = "DETERMINED"
    PROPORTIONAL = "PROPORTIONAL"
    WEIGHTED_AVG_DISCLOSED = "WEIGHTED_AVG_DISCLOSED"
    PATIENT_SUPPLEMENT = "PATIENT_SUPPLEMENT"

    LABELS = {
        EX_FACTORY: "廠商出廠價",
        PHARMACY_PURCHASE: "藥局採購價",
        RETAIL: "藥局零售價",
        RETAIL_TAXED: "含稅藥局零售價",
        RETAIL_WITH_FEE: "含調劑費零售價",
        DISPENSING_FEE: "調劑費",
        REIMBURSEMENT: "健保給付價",
        REFERENCE: "參考價／固定給付額",
        CLAIMED: "廠商申報價",
        DETERMINED: "官方核定價",
        PROPORTIONAL: "比例計價",
        WEIGHTED_AVG_DISCLOSED: "加權平均揭露價",
        PATIENT_SUPPLEMENT: "病患自付差額",
    }

    @classmethod
    def label(cls, code):
        """取得中文說明。

        代碼可加上 ``@`` 後綴表示更細的區分（如比利時依交付模式分成
        公眾、門診、住院、出廠、安養機構五種價格）。同一個完整代碼字串
        才代表同一種價格，排序與比較以完整字串為準。
        """
        if code in cls.LABELS:
            return cls.LABELS[code]
        base = (code or "").split("@", 1)[0]
        return cls.LABELS.get(base, code or "")


class Confidence:
    """欄位對照的可信度等級。"""

    OFFICIAL_DOC = "官方文件佐證"        # 有官方逐欄位定義文件可查
    VERIFIED_FILE = "實際檔案驗證"        # 無官方文件，但已用真實檔案核對過
    FILE_HEADER = "檔案內建欄位名"        # 直接取用原始檔欄位名，未翻譯
    ESTIMATED = "推估未驗證"              # 依網頁介面推估，尚未經檔案驗證


class SourceTrack:
    """來源軌別。兩軌並列，不是二選一。"""

    BATCH = "A"      # 批次檔來源（可機讀）
    MANUAL_SITE = "B"  # 操作手冊指定網站（逐筆查詢頁）

    LABELS = {BATCH: "A 批次檔來源", MANUAL_SITE: "B 手冊指定網站"}


@dataclasses.dataclass
class PriceRecord:
    """一筆藥價。欄位順序即為匯出 CSV 的欄位順序。"""

    # --- 來源 ---
    country: str = ""                 # 國家代碼
    country_name: str = ""            # 國家中文名
    source_agency: str = ""           # 來源機關
    source_track: str = SourceTrack.BATCH

    # --- 藥品識別 ---
    native_code_type: str = ""        # 原生碼種類，如 PBS code、CIP13
    native_code: str = ""
    brand_name: str = ""              # 商品名
    generic_name: str = ""            # 成分名（原文）
    atc_code: str = ""

    # --- 規格 ---
    form: str = ""                    # 劑型
    strength_value: str = ""          # 含量數值
    strength_unit: str = ""           # 含量單位
    pack_size_value: str = ""         # 包裝數量
    pack_size_unit: str = ""          # 包裝單位

    # --- 價格 ---
    price: str = ""                   # 當地價格
    currency: str = ""                # 幣別
    price_category: str = ""          # 價格類別代碼
    price_category_label: str = ""    # 價格類別中文
    unit_price: str = ""              # 單位藥價
    unit_price_basis: str = ""        # 單位藥價的算式，供覆核

    # --- 原廠判定線索（供人工判斷，程式不自行認定） ---
    marketer: str = ""                # 藥商／藥證持有商
    originator_flag: str = ""         # 原始檔的原廠／學名藥註記
    first_listed_date: str = ""       # 首次收載日期

    # --- 佐證 ---
    data_version: str = ""            # 資料版本日期
    downloaded_at: str = ""           # 下載時間（台北時間）
    source_url: str = ""              # 來源網址
    source_file: str = ""             # 原始檔存放路徑
    source_sha256: str = ""           # 原始檔雜湊
    source_row: str = ""              # 原始檔中的位置

    # --- 品質 ---
    field_confidence: str = Confidence.OFFICIAL_DOC
    notes: str = ""

    def compute_unit_price(self):
        """依價格與包裝數量計算單位藥價，並記下算式。

        算不出來就留空，不猜。
        """
        try:
            price = float(str(self.price).replace(",", "").strip())
            pack = float(str(self.pack_size_value).replace(",", "").strip())
        except (TypeError, ValueError):
            return
        if pack <= 0:
            return
        self.unit_price = f"{price / pack:.6f}".rstrip("0").rstrip(".")
        unit = self.pack_size_unit or "單位"
        self.unit_price_basis = f"{price:g} ÷ {pack:g} {unit}"


# 匯出 CSV 時使用的中文欄位名
FIELD_LABELS = {
    "country": "國家代碼",
    "country_name": "國家",
    "source_agency": "來源機關",
    "source_track": "來源軌別",
    "native_code_type": "原生碼種類",
    "native_code": "原生碼",
    "brand_name": "商品名",
    "generic_name": "成分名（原文）",
    "atc_code": "ATC代碼",
    "form": "劑型",
    "strength_value": "含量數值",
    "strength_unit": "含量單位",
    "pack_size_value": "包裝數量",
    "pack_size_unit": "包裝單位",
    "price": "當地價格",
    "currency": "幣別",
    "price_category": "價格類別代碼",
    "price_category_label": "價格類別",
    "unit_price": "單位藥價",
    "unit_price_basis": "單位藥價算式",
    "marketer": "藥商",
    "originator_flag": "原廠註記",
    "first_listed_date": "首次收載日期",
    "data_version": "資料版本日期",
    "downloaded_at": "下載時間",
    "source_url": "來源網址",
    "source_file": "原始檔",
    "source_sha256": "原始檔雜湊",
    "source_row": "原始檔位置",
    "field_confidence": "欄位對照可信度",
    "notes": "備註",
}

FIELD_ORDER = [f.name for f in dataclasses.fields(PriceRecord)]


def write_csv(records, path):
    """寫出中文表頭的 CSV。

    使用 utf-8-sig（含 BOM），Excel 直接雙擊開啟才不會變成亂碼。
    """
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([FIELD_LABELS[name] for name in FIELD_ORDER])
        for record in records:
            writer.writerow([getattr(record, name, "") for name in FIELD_ORDER])
    return path


def read_csv(path):
    """讀回 write_csv 產生的檔案。"""
    label_to_field = {label: name for name, label in FIELD_LABELS.items()}
    out = []
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if not header:
            return out
        fields = [label_to_field.get(col, col) for col in header]
        for row in reader:
            values = dict(zip(fields, row))
            out.append(PriceRecord(**{k: v for k, v in values.items()
                                      if k in FIELD_ORDER}))
    return out

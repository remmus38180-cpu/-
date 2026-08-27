# -*- coding: utf-8 -*-
"""把藥價資料比對到查詢清單，並排出候選順序。

輸出的每一筆候選都帶「排序依據」，寫明分數是怎麼來的。
說明文字由 ``scoring`` 的規則表產生，與計分用的是同一份資料，
不會出現算一套、講另一套的情況。

**排序不是決定。** 所有達到門檻的候選都會列出，由人勾選最終採用哪一筆。

僅使用 Python 標準函式庫。
"""

import dataclasses

from ..core.schema import PriceRecord
from .scoring import (MAX_SCORE, Query, rules_table, score_drug_match,
                      score_originator)

__all__ = ["Candidate", "MatchResult", "match_country", "TIERS"]

# 藥品相符度的分級門檻
TIERS = [
    (70, "A", "高度相符"),
    (40, "B", "需確認"),
    (1, "C", "僅供參考"),
]


def tier_of(score):
    for threshold, code, label in TIERS:
        if score >= threshold:
            return code, label
    return "-", "未達門檻"


@dataclasses.dataclass
class PriceLine:
    """同一個品項下的一種價格。"""

    category: str
    category_label: str
    price: str
    currency: str
    unit_price: str
    unit_price_basis: str
    source_row: str
    duplicate_count: int = 1     # 原始檔中有幾列是同樣的價格


@dataclasses.dataclass
class Candidate:
    """一個候選品項（同一品項的多種價格收在 prices 裡）。"""

    country: str
    country_name: str
    source_agency: str
    native_code_type: str
    native_code: str
    brand_name: str
    generic_name: str
    atc_code: str
    form: str
    strength_value: str
    strength_unit: str
    pack_size_value: str
    pack_size_unit: str
    marketer: str
    originator_flag: str
    first_listed_date: str
    data_version: str
    source_url: str
    source_file: str
    field_confidence: str
    notes: str

    prices: list = dataclasses.field(default_factory=list)

    drug_score: int = 0
    originator_score: int = 0
    tier: str = ""
    tier_label: str = ""
    rank: int = 0
    ranking_basis: str = ""      # 給人看的排序依據
    caution: str = ""            # 判讀提醒

    def cheapest(self, category=None):
        """回傳單位藥價最低的那一筆價格。指定類別時只在該類別內比較。"""
        lines = [p for p in self.prices if p.unit_price]
        if category:
            lines = [p for p in lines if p.category_label == category]
        if not lines:
            return None
        return min(lines, key=lambda p: float(p.unit_price))


@dataclasses.dataclass
class MatchResult:
    """一列查詢在一個國家的比對結果。"""

    query: Query
    country: str
    country_name: str
    candidates: list = dataclasses.field(default_factory=list)
    message: str = ""


def _product_key(record):
    """同一品項的判定依據。原生碼優先，沒有才退回名稱加規格。"""
    if record.native_code:
        return (record.country, record.native_code)
    return (record.country, record.brand_name, record.form,
            record.strength_value, record.pack_size_value)


def _describe(drug_score, drug_hits, originator_score, originator_hits,
              rank_note):
    """把命中的規則寫成人看得懂的一段話。"""
    def part(name, score, hits):
        if not hits:
            return f"{name} {score}（未命中任何條件）"
        detail = "、".join(
            f"{rule.description}{'（' + note + '）' if note else ''} {rule.points:+d}"
            for rule, note in hits)
        return f"{name} {score} ＝ {detail}"

    text = "；".join([
        part("藥品相符度", drug_score, drug_hits),
        part("原廠可能性", originator_score, originator_hits),
    ])
    return f"{text}。{rank_note}" if rank_note else text + "。"


def match_country(queries, records, source=None, rank_by_category=None,
                  min_score=1, limit_per_query=50):
    """為每一列查詢，在單一國家的資料中找出候選並排序。

    參數
    ----
    queries            Query 清單
    records            該國的 PriceRecord 清單
    source             該國的 Source 物件，用來判斷是否有官方原廠註記
    rank_by_category   指定用哪一種價格類別比單位藥價；不指定則用最低者
    min_score          藥品相符度低於此值不列入
    limit_per_query    每列查詢最多列出幾個候選
    """
    if not records:
        return []

    country = records[0].country
    country_name = records[0].country_name

    # 該國的官方檔案有沒有原廠註記欄位
    has_official_flag = any(r.originator_flag for r in records)

    # 先把同一品項的多筆價格收攏。
    # 有些國家的原始檔會為同一個藥品碼列出多列（澳洲 PBS 依處方集、
    # 給付類別等分列），價格完全相同。這種重複只留一筆並記下列數，
    # 否則同一個候選底下會出現幾十行一模一樣的價格，反而看不清楚。
    grouped = {}
    for record in records:
        key = _product_key(record)
        entry = grouped.get(key)
        if entry is None:
            entry = {"record": record, "prices": {}}
            grouped[key] = entry
        price_key = (record.price_category, record.price, record.unit_price)
        existing = entry["prices"].get(price_key)
        if existing is not None:
            existing.duplicate_count += 1
            continue
        entry["prices"][price_key] = PriceLine(
            category=record.price_category,
            category_label=record.price_category_label,
            price=record.price,
            currency=record.currency,
            unit_price=record.unit_price,
            unit_price_basis=record.unit_price_basis,
            source_row=record.source_row,
        )

    for entry in grouped.values():
        entry["prices"] = list(entry["prices"].values())

    results = []
    for query in queries:
        scored = []
        for entry in grouped.values():
            record = entry["record"]
            drug_score, drug_hits = score_drug_match(query, record)
            if drug_score < min_score:
                continue
            originator_score, originator_hits, caution = score_originator(
                query, record, has_official_flag)
            scored.append((drug_score, drug_hits, originator_score,
                           originator_hits, caution, entry))

        def sort_key(item):
            drug_score, _, originator_score, _, _, entry = item
            candidate_prices = [p for p in entry["prices"] if p.unit_price]
            if rank_by_category:
                candidate_prices = [p for p in candidate_prices
                                    if p.category_label == rank_by_category]
            cheapest = (min(float(p.unit_price) for p in candidate_prices)
                        if candidate_prices else float("inf"))
            return (-drug_score, -originator_score, cheapest)

        scored.sort(key=sort_key)

        # 分數完全相同的候選，先後其實只由單位藥價決定。
        # 這件事要講出來，否則人會以為第 1 筆比第 2 筆更有依據。
        tied = set()
        for index in range(len(scored) - 1):
            this_scores = (scored[index][0], scored[index][2])
            next_scores = (scored[index + 1][0], scored[index + 1][2])
            if this_scores == next_scores:
                tied.add(index)
                tied.add(index + 1)

        candidates = []
        for position, item in enumerate(scored[:limit_per_query], start=1):
            (drug_score, drug_hits, originator_score,
             originator_hits, caution, entry) = item
            record = entry["record"]

            cheapest_note = ""
            priced = [p for p in entry["prices"] if p.unit_price]
            if priced:
                target = (min((p for p in priced
                               if not rank_by_category
                               or p.category_label == rank_by_category),
                              key=lambda p: float(p.unit_price), default=None))
                if target:
                    cheapest_note = (f"排序用的單位藥價為 {target.unit_price} "
                                     f"{record.currency}／"
                                     f"{target.category_label}。")

            if position - 1 in tied:
                cheapest_note += ("此筆與相鄰候選的兩項分數完全相同，"
                                  "先後僅由單位藥價決定，不代表更可能正確。")

            tier, tier_label = tier_of(drug_score)
            candidates.append(Candidate(
                country=record.country,
                country_name=record.country_name,
                source_agency=record.source_agency,
                native_code_type=record.native_code_type,
                native_code=record.native_code,
                brand_name=record.brand_name,
                generic_name=record.generic_name,
                atc_code=record.atc_code,
                form=record.form,
                strength_value=record.strength_value,
                strength_unit=record.strength_unit,
                pack_size_value=record.pack_size_value,
                pack_size_unit=record.pack_size_unit,
                marketer=record.marketer,
                originator_flag=record.originator_flag,
                first_listed_date=record.first_listed_date,
                data_version=record.data_version,
                source_url=record.source_url,
                source_file=record.source_file,
                field_confidence=record.field_confidence,
                notes=record.notes,
                prices=sorted(entry["prices"], key=lambda p: p.category_label),
                drug_score=drug_score,
                originator_score=originator_score,
                tier=tier,
                tier_label=tier_label,
                rank=position,
                ranking_basis=_describe(drug_score, drug_hits, originator_score,
                                        originator_hits, cheapest_note),
                caution=caution,
            ))

        message = ""
        if not candidates:
            message = (f"在{country_name}的資料中找不到相符的品項。"
                       f"可能是該國沒有這個藥，或是名稱寫法不同——"
                       f"建議補上成分名或 ATC 代碼再試一次。")
        results.append(MatchResult(query=query, country=country,
                                   country_name=country_name,
                                   candidates=candidates, message=message))
    return results

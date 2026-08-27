# -*- coding: utf-8 -*-
"""比對與排序測試。

執行方式：python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from drugprice.core.schema import PriceCategory, PriceRecord      # noqa: E402
from drugprice.matching.druglist import read_drug_list            # noqa: E402
from drugprice.matching.kana import (consonant_key, looks_japanese,  # noqa: E402
                                     similarity, to_romaji)
from drugprice.matching.matcher import match_country              # noqa: E402
from drugprice.matching.scoring import (DRUG_RULES, ORIGINATOR_RULES,  # noqa: E402
                                        Query, rules_table,
                                        score_drug_match, score_originator)


def record(**kwargs):
    base = dict(country="XX", country_name="測試國", currency="EUR",
                price_category=PriceCategory.RETAIL,
                price_category_label="藥局零售價")
    base.update(kwargs)
    row = PriceRecord(**base)
    row.compute_unit_price()
    return row


class TestKana(unittest.TestCase):
    """日本的藥價檔用片假名，英文清單要靠轉寫才比得到。"""

    def test_romaji(self):
        self.assertEqual(to_romaji("アピキサバン"), "apikisaban")

    def test_long_vowel(self):
        self.assertEqual(to_romaji("エリキュース"), "erikyuusu")

    def test_hiragana_also_works(self):
        self.assertEqual(to_romaji("あぴきさばん"), "apikisaban")

    def test_looks_japanese(self):
        self.assertTrue(looks_japanese("アピキサバン"))
        self.assertFalse(looks_japanese("apixaban"))

    def test_correct_pairs_clear_threshold(self):
        pairs = [("アピキサバン", "apixaban"), ("エリキュース", "Eliquis"),
                 ("ロスバスタチン", "rosuvastatin"), ("メトホルミン", "metformin"),
                 ("セレコキシブ", "celecoxib"), ("リツキシマブ", "rituximab"),
                 ("パクリタキセル", "paclitaxel"), ("アムロジピン", "amlodipine")]
        for japanese, english in pairs:
            with self.subTest(japanese=japanese):
                self.assertGreaterEqual(similarity(japanese, english), 0.75)

    def test_wrong_pairs_stay_below_threshold(self):
        pairs = [("アピキサバン", "atorvastatin"), ("メトホルミン", "celecoxib"),
                 ("アムロジピン", "estazolam"), ("シタグリプチン", "metformin")]
        for japanese, english in pairs:
            with self.subTest(japanese=japanese):
                self.assertLess(similarity(japanese, english), 0.75)

    def test_consonant_skeleton(self):
        """日文插入的母音要被略過，只比子音骨架。"""
        self.assertEqual(consonant_key("ロスバスタチン"), consonant_key("rosuvastatin"))


class TestScoring(unittest.TestCase):

    def test_rules_table_matches_the_rules_used(self):
        """介面顯示的說明必須來自實際計分用的同一張表。"""
        table = rules_table()
        self.assertEqual(len(table["藥品相符度"]), len(DRUG_RULES))
        self.assertEqual(len(table["原廠可能性"]), len(ORIGINATOR_RULES))
        self.assertEqual(table["藥品相符度"][0]["description"],
                         DRUG_RULES[0].description)

    def test_exact_ingredient_scores_highest(self):
        query = Query(brand_name="Eliquis", generic_name="apixaban")
        score, hits = score_drug_match(query, record(generic_name="apixaban"))
        self.assertEqual(score, 50)
        self.assertEqual(hits[0][0].key, "ingredient_exact")

    def test_salt_form_still_matches(self):
        query = Query(generic_name="apixaban")
        score, hits = score_drug_match(query, record(generic_name="Apixaban Maleate"))
        self.assertEqual(hits[0][0].key, "ingredient_salt")
        self.assertGreater(score, 0)

    def test_brand_inside_longer_name_matches(self):
        """各國常把含量劑型寫進商品名，仍應視為相符。"""
        query = Query(brand_name="Eliquis")
        _, hits = score_drug_match(
            query, record(brand_name="ELIQUIS 2,5 mg, comprimé pelliculé"))
        self.assertIn("brand_token", [rule.key for rule, _ in hits])

    def test_short_prefix_does_not_false_match(self):
        query = Query(brand_name="Eli")
        _, hits = score_drug_match(query, record(brand_name="ELIQUIS 2,5 mg"))
        self.assertNotIn("brand_token", [rule.key for rule, _ in hits])

    def test_katakana_ingredient_matches_with_detail(self):
        query = Query(brand_name="Eliquis", generic_name="apixaban")
        _, hits = score_drug_match(query, record(generic_name="アピキサバン"))
        keys = {rule.key: note for rule, note in hits}
        self.assertIn("ingredient_romaji_high", keys)
        self.assertIn("近似度", keys["ingredient_romaji_high"])

    def test_official_originator_flag_scores(self):
        query = Query(brand_name="Eliquis")
        score, hits, _ = score_originator(
            query, record(originator_flag="原廠藥（princeps）"))
        self.assertGreaterEqual(score, 60)
        self.assertEqual(hits[0][0].key, "official_originator")

    def test_generic_flag_is_penalised_not_excluded(self):
        query = Query(brand_name="X")
        score, hits, _ = score_originator(
            query, record(originator_flag="學名藥（générique）"))
        self.assertEqual(score, 0)              # 下限為 0，不會變負數
        self.assertEqual(hits[0][0].key, "official_generic")

    def test_caution_when_country_has_no_official_flag(self):
        query = Query(brand_name="Eliquis")
        _, _, caution = score_originator(query, record(), country_has_official_flag=False)
        self.assertIn("沒有原廠", caution)
        self.assertIn("藥商名", caution)         # 應告訴使用者可以怎麼補救


class TestMatcher(unittest.TestCase):

    def _records(self):
        return [
            record(native_code="1", brand_name="Eliquis", generic_name="apixaban",
                   atc_code="B01AF02", strength_value="2.5", strength_unit="mg",
                   pack_size_value="60", pack_size_unit="錠", price="100",
                   marketer="Bristol-Myers Squibb",
                   originator_flag="原廠藥（princeps）", source_row="第 1 列"),
            record(native_code="2", brand_name="Apixaban Teva", generic_name="apixaban",
                   atc_code="B01AF02", strength_value="2.5", strength_unit="mg",
                   pack_size_value="60", pack_size_unit="錠", price="40",
                   marketer="Teva", originator_flag="學名藥（générique）",
                   source_row="第 2 列"),
            record(native_code="3", brand_name="Something Else",
                   generic_name="paracetamol", atc_code="N02BE01",
                   pack_size_value="20", price="5", source_row="第 3 列"),
        ]

    def test_originator_ranks_above_cheaper_generic(self):
        """學名藥雖然便宜，但原廠可能性低，不該排在原廠前面。"""
        query = Query(brand_name="Eliquis", generic_name="apixaban",
                      atc_code="B01AF02", strength="2.5 mg")
        result = match_country([query], self._records())[0]
        self.assertEqual(result.candidates[0].brand_name, "Eliquis")
        self.assertGreater(result.candidates[0].originator_score,
                           result.candidates[1].originator_score)

    def test_unrelated_drug_excluded(self):
        query = Query(brand_name="Eliquis", generic_name="apixaban",
                      atc_code="B01AF02")
        result = match_country([query], self._records())[0]
        names = [c.brand_name for c in result.candidates]
        self.assertNotIn("Something Else", names)

    def test_ranking_basis_is_readable_and_complete(self):
        query = Query(brand_name="Eliquis", generic_name="apixaban",
                      atc_code="B01AF02")
        candidate = match_country([query], self._records())[0].candidates[0]
        self.assertIn("藥品相符度", candidate.ranking_basis)
        self.assertIn("原廠可能性", candidate.ranking_basis)
        self.assertIn("成分名完全相符", candidate.ranking_basis)
        self.assertIn("+50", candidate.ranking_basis)

    def test_identical_prices_are_collapsed(self):
        """同一藥品碼在原始檔重複多列時，價格只留一行並記下列數。"""
        rows = [record(native_code="9", brand_name="A", generic_name="x",
                       pack_size_value="10", price="20", source_row=f"第 {i} 列")
                for i in range(1, 6)]
        result = match_country([Query(brand_name="A", generic_name="x")], rows)[0]
        prices = result.candidates[0].prices
        self.assertEqual(len(prices), 1)
        self.assertEqual(prices[0].duplicate_count, 5)

    def test_tie_is_disclosed(self):
        """分數相同時要講明先後只由單位藥價決定。"""
        rows = [
            record(native_code="a", brand_name="A", generic_name="x",
                   pack_size_value="10", price="20"),
            record(native_code="b", brand_name="A", generic_name="x",
                   pack_size_value="10", price="30"),
        ]
        result = match_country([Query(brand_name="A", generic_name="x")], rows)[0]
        self.assertIn("僅由單位藥價決定", result.candidates[0].ranking_basis)

    def test_no_match_gives_actionable_message(self):
        result = match_country([Query(brand_name="不存在的藥")], self._records())[0]
        self.assertEqual(result.candidates, [])
        self.assertIn("成分名", result.message)

    def test_tiers_assigned(self):
        query = Query(brand_name="Eliquis", generic_name="apixaban",
                      atc_code="B01AF02", strength="2.5 mg")
        result = match_country([query], self._records())[0]
        self.assertEqual(result.candidates[0].tier, "A")


class TestDrugList(unittest.TestCase):

    def test_plain_text_list(self):
        queries, messages = read_drug_list("Eliquis\nExforge\n")
        self.assertEqual([q.brand_name for q in queries], ["Eliquis", "Exforge"])
        self.assertTrue(any("純文字" in m for m in messages))

    def test_csv_with_chinese_headers(self):
        text = "商品名,成分名,ATC\nEliquis,apixaban,B01AF02\n"
        queries, _ = read_drug_list(text)
        self.assertEqual(queries[0].generic_name, "apixaban")
        self.assertEqual(queries[0].atc_code, "B01AF02")

    def test_csv_with_english_headers(self):
        text = "brand,generic,atc\nEliquis,apixaban,B01AF02\n"
        queries, _ = read_drug_list(text)
        self.assertEqual(queries[0].generic_name, "apixaban")

    def test_column_order_does_not_matter(self):
        text = "成分名,ATC,商品名\napixaban,B01AF02,Eliquis\n"
        queries, _ = read_drug_list(text)
        self.assertEqual(queries[0].brand_name, "Eliquis")

    def test_warns_when_generic_missing(self):
        _, messages = read_drug_list("Eliquis\n")
        self.assertTrue(any("成分名" in m for m in messages))

    def test_utf8_bom_handled(self):
        data = "﻿商品名,成分名\nEliquis,apixaban\n".encode("utf-8")
        queries, _ = read_drug_list(data)
        self.assertEqual(queries[0].brand_name, "Eliquis")

    def test_empty_input(self):
        queries, messages = read_drug_list("")
        self.assertEqual(queries, [])
        self.assertTrue(messages)


if __name__ == "__main__":
    unittest.main(verbosity=2)

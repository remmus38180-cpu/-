# -*- coding: utf-8 -*-
"""十國工作流總表與加拿大固定寬度解析的測試。"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from drugprice.countries import (AUTO, BLOCKED, COUNTRIES, MANUAL,  # noqa: E402
                                 build_worklist, get_country)
from drugprice.matching.scoring import Query                        # noqa: E402
from drugprice.registry import NOT_YET, SOURCES                     # noqa: E402
from drugprice.sources.canada_sk import CanadaSaskatchewan          # noqa: E402


class TestCountryTable(unittest.TestCase):

    def test_ten_countries_covered(self):
        self.assertEqual(len(COUNTRIES), 10)

    def test_every_country_has_a_defined_path(self):
        """每個國家都要有明確的執行方式，不能留空。"""
        for country in COUNTRIES:
            with self.subTest(code=country.code):
                self.assertIn(country.method, (AUTO, MANUAL, BLOCKED))

    def test_non_auto_countries_explain_why(self):
        """自動不了的國家一定要寫原因，否則同仁會以為是程式漏抓。"""
        for country in COUNTRIES:
            if country.method != AUTO:
                with self.subTest(code=country.code):
                    self.assertTrue(country.reason.strip(),
                                    f"{country.code} 沒有寫出無法自動化的原因")
                    self.assertTrue(country.steps,
                                    f"{country.code} 沒有提供人工操作步驟")

    def test_auto_countries_have_an_adapter(self):
        for country in COUNTRIES:
            if country.method == AUTO:
                with self.subTest(code=country.code):
                    self.assertIn(country.code, SOURCES)

    def test_registry_not_yet_matches_country_table(self):
        """登記表的『尚未接上』要與國家總表一致，不能各說各話。"""
        expected = {c.code for c in COUNTRIES if c.method != AUTO}
        self.assertEqual(set(NOT_YET), expected)

    def test_search_url_is_escaped(self):
        country = get_country("CH")
        url = country.search_url("Co-Amoxi 500 mg")
        self.assertNotIn(" ", url)
        self.assertIn("Co-Amoxi", url.replace("%20", " "))

    def test_search_url_falls_back_to_query_page(self):
        country = get_country("DE")      # 沒有查詢樣板
        self.assertEqual(country.search_url("X"), country.manual_url)

    def test_worklist_excludes_automated_countries(self):
        work = build_worklist([Query(brand_name="Eliquis")])
        codes = {item["代碼"] for item in work}
        self.assertNotIn("JP", codes)
        self.assertIn("US", codes)

    def test_worklist_carries_reason_and_steps(self):
        work = build_worklist([Query(brand_name="Eliquis")], ["CH"])
        self.assertEqual(len(work), 1)
        self.assertTrue(work[0]["原因"])
        self.assertTrue(work[0]["操作步驟"])
        self.assertEqual(len(work[0]["待查藥品"]), 1)

    def test_unknown_code_message_lists_valid_codes(self):
        with self.assertRaises(KeyError) as caught:
            get_country("ZZ")
        self.assertIn("可用的代碼", str(caught.exception))


class TestCanadaUnitCost(unittest.TestCase):
    """Unit Cost 為 999v9999 格式：7 位數字，隱含 4 位小數。"""

    def test_implied_decimals(self):
        self.assertEqual(CanadaSaskatchewan._unit_cost("0104950"), 10.495)

    def test_small_value(self):
        self.assertEqual(CanadaSaskatchewan._unit_cost("0000062"), 0.0062)

    def test_blank_returns_none(self):
        self.assertIsNone(CanadaSaskatchewan._unit_cost("       "))

    def test_non_numeric_returns_none(self):
        """拆不出來就回 None，不能猜成 0。"""
        self.assertIsNone(CanadaSaskatchewan._unit_cost("ABC1234"))

    def test_none_input(self):
        self.assertIsNone(CanadaSaskatchewan._unit_cost(None))


class TestCanadaHierarchy(unittest.TestCase):
    """檔案是階層式的，產品列本身沒有成分名，要沿用前面的第 4 型記錄。

    合成資料依官方版面說明的欄位位置組出來（位置為 1 起算），
    所以這個測試同時也是版面文件的複述。
    """

    @staticmethod
    def _row(fields):
        """fields 為 {起始位置: 內容}，位置以 1 起算。"""
        line = [" "] * 80
        for position, text in fields.items():
            for offset, char in enumerate(str(text)):
                line[position - 1 + offset] = char
        return "".join(line)

    def _sample(self):
        return "\n".join([
            # 大分類：型態 1、序號、分類碼 4-9、名稱 11-73
            self._row({1: "1", 2: "0", 4: "AAAAAA", 11: "ANTI-INFECTIVES"}),
            # 次分類：型態 2
            self._row({1: "2", 2: "0", 4: "BBBBBB", 11: "ANTHELMINTICS"}),
            # 成分名：型態 4、序號 1、名稱 29-73
            self._row({1: "4", 2: "1", 4: "BBBBBB", 29: "MEBENDAZOLE"}),
            # 含量與劑型：型態 4、序號 2、可替代註記 28、內容 29-73
            self._row({1: "4", 2: "2", 4: "BBBBBB", 28: "*", 29: "100MG TABLET"}),
            # 產品：DIN 29-36、產品碼 38-39、品名 41-65、
            #       廠商 67-69、單位成本 71-77、給付別 79
            self._row({1: "6", 4: "BBBBBB", 29: "00556734", 38: "01",
                       41: "VERMOX", 67: "JAN", 71: "0104950", 79: "F"}),
            self._row({1: "4", 2: "1", 4: "BBBBBB", 29: "PRAZIQUANTEL"}),
            self._row({1: "4", 2: "2", 4: "BBBBBB", 29: "600MG TABLET"}),
            self._row({1: "6", 2: "1", 4: "BBBBBB", 29: "02230897", 38: "01",
                       41: "BILTRICIDE", 67: "BAY", 71: "0062900", 79: "E"}),
        ])

    def _parse(self):
        import tempfile

        from drugprice.sources.base import Context, Downloaded

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "fw.txt")
            with open(path, "w", encoding="cp1252") as fh:
                fh.write(self._sample())
            item = Downloaded(path=path, rel_path="fw.txt", sha256="",
                              source_url="x", data_version="v62",
                              label="藥品清單")
            source = CanadaSaskatchewan()
            return source.parse(Context(None, None, log=lambda m: None), [item])

    def test_two_products_parsed(self):
        self.assertEqual(len(self._parse()), 2)

    def test_generic_name_carried_forward(self):
        records = self._parse()
        self.assertEqual(records[0].generic_name, "MEBENDAZOLE")
        self.assertEqual(records[0].brand_name, "VERMOX")

    def test_generic_name_resets_between_groups(self):
        """換了成分就不能沿用上一個成分的規格。"""
        records = self._parse()
        self.assertEqual(records[1].generic_name, "PRAZIQUANTEL")
        self.assertEqual(records[1].form, "600MG TABLET")

    def test_unit_cost_applied(self):
        records = self._parse()
        self.assertEqual(records[0].price, "10.495")
        self.assertEqual(records[1].price, "6.29")

    def test_unit_price_equals_price(self):
        """Unit Cost 本身就是單位價，包裝量固定為 1。"""
        record = self._parse()[0]
        self.assertEqual(record.pack_size_value, "1")
        self.assertEqual(record.unit_price, record.price)

    def test_din_and_manufacturer(self):
        record = self._parse()[0]
        self.assertEqual(record.native_code, "00556734")
        self.assertEqual(record.marketer, "JAN")

    def test_strength_parsed_from_dosage_form(self):
        record = self._parse()[0]
        self.assertEqual(record.strength_value, "100")
        self.assertEqual(record.strength_unit, "mg")

    def test_class_and_benefit_type_in_notes(self):
        records = self._parse()
        self.assertIn("ANTI-INFECTIVES", records[0].notes)
        self.assertIn("一般給付", records[0].notes)
        self.assertIn("例外給付", records[1].notes)

    def test_interchangeable_flag_recorded(self):
        self.assertIn("可替代", self._parse()[0].notes)


if __name__ == "__main__":
    unittest.main(verbosity=2)

# -*- coding: utf-8 -*-
"""核心模組測試。

執行方式：python -m unittest discover -s tests -v

只用標準函式庫的 unittest，不需要 pytest。
"""

import io
import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from drugprice.core import xlsx                                  # noqa: E402
from drugprice.core.robots import parse_robots                   # noqa: E402
from drugprice.core.schema import (Confidence, PriceCategory,     # noqa: E402
                                   PriceRecord, read_csv, write_csv)
from drugprice.core.textfile import decode, read_delimited       # noqa: E402
from drugprice.core.units import (normalize_name, parse_pack_size,  # noqa: E402
                                  parse_strength, strip_salt)


class TestRobots(unittest.TestCase):
    """robots.txt 比對。萬用字元是重點——Python 內建的解析器不支援。"""

    # 澳洲 PBS 的真實內容
    PBS = """User-agent: *
Disallow: /downloads/
Disallow: /archive/
Disallow: /api/
Disallow: /bzindex/
Disallow: /*.zip$
Allow: /
"""

    def test_wildcard_zip_is_blocked(self):
        rules = parse_robots(self.PBS)
        allowed, rule = rules.is_allowed(
            "https://www.pbs.gov.au/downloads/2026/08/2026-08-01-PBS-API-CSV-files.zip")
        self.assertFalse(allowed, "PBS 的 zip 下載路徑必須判定為禁止")
        self.assertIn("Disallow", rule)

    def test_zip_anywhere_is_blocked(self):
        rules = parse_robots(self.PBS)
        self.assertFalse(rules.is_allowed("https://www.pbs.gov.au/x/y.zip")[0])

    def test_dollar_anchor_only_matches_at_end(self):
        rules = parse_robots(self.PBS)
        # 結尾不是 .zip，不該被 /*.zip$ 擋住
        self.assertTrue(rules.is_allowed("https://www.pbs.gov.au/x/y.zip.txt")[0])

    def test_normal_page_allowed(self):
        rules = parse_robots(self.PBS)
        self.assertTrue(rules.is_allowed("https://www.pbs.gov.au/browse/medicine-listing")[0])

    def test_longest_rule_wins(self):
        rules = parse_robots("User-agent: *\nDisallow: /a/\nAllow: /a/b/\n")
        self.assertFalse(rules.is_allowed("https://x/a/z")[0])
        self.assertTrue(rules.is_allowed("https://x/a/b/c")[0])

    def test_crawl_delay(self):
        rules = parse_robots("User-agent:*\nAllow: /\nCrawl-delay: 5\n")
        self.assertEqual(rules.crawl_delay, 5.0)

    def test_specific_agent_group_wins_over_star(self):
        text = ("User-agent: Baiduspider\nDisallow: /\n\n"
                "User-agent: *\nAllow: /\n")
        self.assertTrue(parse_robots(text, "*").is_allowed("https://x/a")[0])
        self.assertFalse(parse_robots(text, "Baiduspider").is_allowed("https://x/a")[0])

    def test_empty_disallow_means_allow_all(self):
        rules = parse_robots("User-agent: *\nDisallow:\n")
        self.assertTrue(rules.is_allowed("https://x/anything")[0])


class TestUnits(unittest.TestCase):

    def test_strength_with_european_comma(self):
        self.assertEqual(parse_strength("2,5 mg"), (2.5, "mg"))

    def test_strength_full_width(self):
        self.assertEqual(parse_strength("１ｍｇ"), (1.0, "mg"))

    def test_strength_combination_takes_first(self):
        self.assertEqual(parse_strength("600 mg/300 mg"), (600.0, "mg"))

    def test_strength_absent(self):
        self.assertEqual(parse_strength("comprimé pelliculé"), (None, ""))

    def test_pack_swedish_plural(self):
        self.assertEqual(parse_pack_size("Blister, 30 tabletter")[:2], (30.0, "錠"))

    def test_pack_french(self):
        value, unit, _ = parse_pack_size(
            "plaquette(s) thermoformée(s) PVC de 60 comprimé(s)")
        self.assertEqual((value, unit), (60.0, "錠"))

    def test_pack_plain_number(self):
        self.assertEqual(parse_pack_size("30")[0], 30.0)

    def test_pack_unparseable_returns_none(self):
        """拆不出來要回 None，不可以亂猜。"""
        self.assertEqual(parse_pack_size("boîte de comprimés")[0], None)

    def test_pack_short_unit_not_over_matched(self):
        """短單位 g 不應誤中 granulat。"""
        value, unit, _ = parse_pack_size("100 granulat")
        self.assertNotEqual(unit, "公克")

    def test_strip_salt(self):
        self.assertEqual(strip_salt("Apixaban Maleate"), "apixaban")
        self.assertEqual(strip_salt("Metoprolol Succinate"), "metoprolol")

    def test_normalize_removes_accents_and_case(self):
        self.assertEqual(normalize_name("Éliquis®"), "eliquis")


class TestSchema(unittest.TestCase):

    def test_unit_price(self):
        record = PriceRecord(price="123.45", pack_size_value="30",
                             pack_size_unit="錠")
        record.compute_unit_price()
        self.assertEqual(record.unit_price, "4.115")
        self.assertIn("÷", record.unit_price_basis)

    def test_unit_price_left_blank_when_pack_unknown(self):
        record = PriceRecord(price="123.45", pack_size_value="")
        record.compute_unit_price()
        self.assertEqual(record.unit_price, "")

    def test_unit_price_left_blank_when_pack_is_zero(self):
        record = PriceRecord(price="10", pack_size_value="0")
        record.compute_unit_price()
        self.assertEqual(record.unit_price, "")

    def test_price_category_label_with_suffix(self):
        """比利時用 @ 後綴區分交付模式，取標籤時要能對回基底類別。"""
        self.assertEqual(PriceCategory.label("RETAIL_TAXED@PUBLIQUE"),
                         "含稅藥局零售價")

    def test_csv_roundtrip_keeps_chinese(self):
        record = PriceRecord(country="SE", country_name="瑞典",
                             brand_name="測試藥品", price="1,5",
                             price_category=PriceCategory.RETAIL,
                             price_category_label="藥局零售價",
                             field_confidence=Confidence.VERIFIED_FILE)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.csv")
            write_csv([record], path)
            with open(path, "rb") as fh:
                head = fh.read(3)
            self.assertEqual(head, b"\xef\xbb\xbf", "需有 BOM，Excel 才不會亂碼")
            back = read_csv(path)
        self.assertEqual(len(back), 1)
        self.assertEqual(back[0].brand_name, "測試藥品")
        self.assertEqual(back[0].price_category_label, "藥局零售價")


class TestTextFile(unittest.TestCase):
    """法國三個檔案的編碼不一致，偵測必須正確。"""

    def test_utf8_detected(self):
        text, encoding = decode("comprimé".encode("utf-8"))
        self.assertEqual(text, "comprimé")
        self.assertEqual(encoding, "utf-8")

    def test_cp1252_detected(self):
        text, encoding = decode("comprimé".encode("cp1252"))
        self.assertEqual(text, "comprimé")
        self.assertEqual(encoding, "cp1252")

    def test_delimited_rows(self):
        data = "a\tb\tc\n1\t2\t3\n\n4\t5\t6\n".encode("cp1252")
        rows, _ = read_delimited(data)
        self.assertEqual(rows, [["a", "b", "c"], ["1", "2", "3"], ["4", "5", "6"]])


def build_xlsx(rows, sheet_name="Sheet1"):
    """做一個最小但合規的 xlsx，用來測解析邏輯。"""
    shared = []
    index = {}
    for row in rows:
        for cell in row:
            if cell not in index:
                index[cell] = len(shared)
                shared.append(cell)

    sheet_xml = ['<?xml version="1.0"?>',
                 '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
                 '<sheetData>']
    for row_number, row in enumerate(rows, start=1):
        sheet_xml.append(f'<row r="{row_number}">')
        for col_number, cell in enumerate(row):
            ref = chr(ord("A") + col_number) + str(row_number)
            sheet_xml.append(f'<c r="{ref}" t="s"><v>{index[cell]}</v></c>')
        sheet_xml.append("</row>")
    sheet_xml.append("</sheetData></worksheet>")

    strings_xml = ('<?xml version="1.0"?>'
                   '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                   + "".join(f"<si><t>{s}</t></si>" for s in shared) + "</sst>")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("xl/workbook.xml",
                    '<?xml version="1.0"?>'
                    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
                    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                    f'<sheets><sheet name="{sheet_name}" sheetId="1" r:id="rId1"/></sheets>'
                    "</workbook>")
        zf.writestr("xl/_rels/workbook.xml.rels",
                    '<?xml version="1.0"?>'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    '<Relationship Id="rId1" Target="worksheets/sheet1.xml"'
                    ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/>'
                    "</Relationships>")
        zf.writestr("xl/sharedStrings.xml", strings_xml)
        zf.writestr("xl/worksheets/sheet1.xml", "".join(sheet_xml))
    buffer.seek(0)
    return buffer


class TestXlsx(unittest.TestCase):

    def test_read_shared_strings(self):
        rows = [["藥品", "價格"], ["Eliquis", "123,45"]]
        result = xlsx.read_sheet(build_xlsx(rows), 0)
        self.assertEqual(result, rows)

    def test_sheet_names(self):
        self.assertEqual(xlsx.sheet_names(build_xlsx([["a"]], "資料")), ["資料"])

    def test_read_by_sheet_name(self):
        rows = [["x"], ["y"]]
        self.assertEqual(xlsx.read_sheet(build_xlsx(rows, "資料"), "資料"), rows)

    def test_missing_sheet_raises_clear_error(self):
        with self.assertRaises(KeyError):
            xlsx.read_sheet(build_xlsx([["a"]]), "不存在的工作表")

    def test_column_index(self):
        self.assertEqual(xlsx.column_index("A1"), 0)
        self.assertEqual(xlsx.column_index("Z9"), 25)
        self.assertEqual(xlsx.column_index("AA1"), 26)
        self.assertEqual(xlsx.column_index("BC12"), 54)

    def test_sparse_row_is_padded(self):
        """中間跳過的儲存格要補空字串，欄位才不會錯位。"""
        sheet = ('<?xml version="1.0"?>'
                 '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                 '<sheetData><row r="1">'
                 '<c r="A1" t="inlineStr"><is><t>甲</t></is></c>'
                 '<c r="D1" t="inlineStr"><is><t>丁</t></is></c>'
                 "</row></sheetData></worksheet>")
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("xl/workbook.xml",
                        '<?xml version="1.0"?>'
                        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
                        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                        '<sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets></workbook>')
            zf.writestr("xl/_rels/workbook.xml.rels",
                        '<?xml version="1.0"?>'
                        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                        '<Relationship Id="rId1" Target="worksheets/sheet1.xml"'
                        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/>'
                        "</Relationships>")
            zf.writestr("xl/worksheets/sheet1.xml", sheet)
        buffer.seek(0)
        self.assertEqual(xlsx.read_sheet(buffer, 0), [["甲", "", "", "丁"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestCleanNumber(unittest.TestCase):
    """澳洲 PBS 的 CSV 會帶浮點雜訊，需要清掉但不能動到真正的精度。"""

    def test_removes_float_noise(self):
        from drugprice.core.units import clean_number
        self.assertEqual(clean_number("456.65000000000003"), "456.65")

    def test_keeps_normal_price(self):
        from drugprice.core.units import clean_number
        self.assertEqual(clean_number("123.45"), "123.45")

    def test_keeps_short_decimals_untouched(self):
        from drugprice.core.units import clean_number
        self.assertEqual(clean_number("0.3861"), "0.3861")

    def test_non_numeric_passes_through(self):
        from drugprice.core.units import clean_number
        self.assertEqual(clean_number("abc"), "abc")

    def test_empty(self):
        from drugprice.core.units import clean_number
        self.assertEqual(clean_number(""), "")
        self.assertEqual(clean_number(None), "")

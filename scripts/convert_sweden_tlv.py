#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下載瑞典 TLV(藥物福利委員會)整批藥價資料庫，轉成中文欄名的CSV。

網址（已由使用者實測確認，內含多種不同藥品，非單筆查詢結果）：
    https://www.tlv.se/file/medprice

這是TLV「Öppna data」開放資料政策下的整包資料庫檔案，每天更新，
不需要搜尋、不需要登入，直接下載即可。

實際欄位（已用真實下載檔驗證過，不是用猜的）：

    Produktnamn      藥品名稱
    Varunummer       商品編號（瑞典藥品貨號，Varunummer）
    ATC-kod          ATC代碼
    NPL id           NPL主檔代碼（藥品主檔識別碼）
    NPL pack-id      NPL包裝代碼
    Form             劑型
    Styrka           含量/劑量
    Förpackning      包裝說明
    Antal            數量（顆數/單位數）
    Företag          藥證持有商/廠商
    AIP              藥局採購價（Apotekens InköpsPris，藥局向藥廠進貨的價格）
    AUP              藥局零售價（Apotekens UtförsäljningsPris，病人實際看到的售價，**這是你要的藥價**）
    AIP per st       每單位藥局採購價
    AUP per st       每單位藥局零售價
    Subventionerad   是否納入健保給付(Ja=是/Nej=否)

使用方式：
    python3 convert_sweden_tlv.py                # 自動下載最新整批資料庫
    python3 convert_sweden_tlv.py 檔名.xlsx        # 或處理你自己手動下載好的xlsx檔

全程只用 Python 標準函式庫（urllib、zipfile、xml.etree、csv），不需要
openpyxl/pandas/requests。xlsx解析邏輯跟比利時那支程式共用同一套
（xlsx本質是zip包XML）。
"""

import argparse
import io
import os
import re
import zipfile
import xml.etree.ElementTree as ET
import urllib.request
import ssl
import csv

DOWNLOAD_URL = "https://www.tlv.se/file/medprice"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

FIELD_NAME_MAP = {
    "Produktnamn": "藥品名稱",
    "Varunummer": "商品編號(Varunummer)",
    "ATC-kod": "ATC代碼",
    "NPL id": "NPL主檔代碼",
    "NPL pack-id": "NPL包裝代碼",
    "Form": "劑型",
    "Styrka": "含量",
    "Förpackning": "包裝說明",
    "Antal": "數量",
    "Företag": "藥證持有商",
    "AIP": "藥局採購價(AIP)",
    "AUP": "藥局零售價(AUP)",
    "AIP per st": "每單位採購價",
    "AUP per st": "每單位零售價",
    "Subventionerad": "是否納入健保給付",
}


def _make_ssl_context():
    """建立會信任Windows系統憑證存放區的SSL context（公司網路常見的SSL檢查設備問題）"""
    ctx = ssl.create_default_context()
    try:
        for store_name in ("CA", "ROOT"):
            for cert, encoding, trust in ssl.enum_certificates(store_name):
                try:
                    ctx.load_verify_locations(cadata=cert)
                except ssl.SSLError:
                    pass
    except AttributeError:
        pass
    return ctx


_SSL_CONTEXT = _make_ssl_context()
_UNVERIFIED_SSL_CONTEXT = ssl._create_unverified_context()


def _urlopen_with_fallback(req, timeout=60):
    """先用驗證過的SSL context下載，遇到憑證錯誤就自動改用不驗證模式並印警告"""
    try:
        return urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT)
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            print("[警告] 憑證驗證失敗（通常是公司網路的安全設備造成），"
                  "改用不驗證憑證的方式繼續下載。")
            return urllib.request.urlopen(req, timeout=timeout, context=_UNVERIFIED_SSL_CONTEXT)
        raise


def download_database(out_dir="."):
    filename = os.path.join(out_dir, "tlv_medprice.xlsx")
    if os.path.exists(filename):
        print(f"[跳過] {filename} 已存在，不重新下載")
        return filename

    print(f"[下載中] {DOWNLOAD_URL}")
    req = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "Mozilla/5.0"})
    with _urlopen_with_fallback(req, timeout=120) as resp:
        data = resp.read()
    with open(filename, "wb") as f:
        f.write(data)
    print(f"[完成] {filename}（{len(data)} bytes）")
    return filename


# ---------------------------------------------------------------------------
# xlsx解析（跟比利時那支程式邏輯相同：zip + XML，不用第三方套件）
# ---------------------------------------------------------------------------

def col_letter_to_index(cell_ref):
    letters = re.match(r"[A-Z]+", cell_ref).group()
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def read_xlsx_first_sheet(path):
    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()

        shared_strings = []
        if "xl/sharedStrings.xml" in names:
            with zf.open("xl/sharedStrings.xml") as f:
                tree = ET.parse(f)
            for si in tree.getroot().findall("m:si", NS):
                texts = si.findall(".//m:t", NS)
                shared_strings.append("".join(t.text or "" for t in texts))

        sheet_candidates = sorted(n for n in names if re.match(r"xl/worksheets/sheet\d+\.xml", n))
        if not sheet_candidates:
            raise RuntimeError("找不到工作表XML，檔案可能不是標準xlsx")
        with zf.open(sheet_candidates[0]) as f:
            tree = ET.parse(f)

    rows_out = []
    sheet_data = tree.getroot().find("m:sheetData", NS)
    for row in sheet_data.findall("m:row", NS):
        row_values = {}
        max_col = -1
        for c in row.findall("m:c", NS):
            ref = c.get("r", "")
            col_idx = col_letter_to_index(ref) if ref else len(row_values)
            cell_type = c.get("t", "")
            v_elem = c.find("m:v", NS)
            is_elem = c.find("m:is", NS)

            if cell_type == "s" and v_elem is not None:
                idx = int(v_elem.text)
                value = shared_strings[idx] if idx < len(shared_strings) else ""
            elif cell_type == "inlineStr" and is_elem is not None:
                t_elem = is_elem.find("m:t", NS)
                value = t_elem.text if t_elem is not None else ""
            elif v_elem is not None:
                value = v_elem.text
            else:
                value = ""

            row_values[col_idx] = value
            max_col = max(max_col, col_idx)

        row_list = [row_values.get(i, "") for i in range(max_col + 1)]
        rows_out.append(row_list)

    return rows_out


def translate_header(header_row):
    return [FIELD_NAME_MAP.get(name.strip(), name) for name in header_row]


def write_csv(header, rows, out_path):
    with io.open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"[完成] 已輸出 {len(rows)} 筆資料到 {out_path}")


def main():
    parser = argparse.ArgumentParser(description="下載並轉換瑞典TLV整批藥價資料庫成中文欄名CSV")
    parser.add_argument(
        "xlsx_file", nargs="?", default=None,
        help="（選填）自己手動下載好的xlsx檔名；不指定就自動從TLV官網下載最新整批資料庫"
    )
    args = parser.parse_args()

    if args.xlsx_file:
        xlsx_path = args.xlsx_file
        if not os.path.exists(xlsx_path):
            raise FileNotFoundError(f"找不到檔案：{xlsx_path}")
    else:
        xlsx_path = download_database()

    rows = read_xlsx_first_sheet(xlsx_path)
    if not rows:
        print("這個檔案是空的")
        return

    header, data_rows = rows[0], rows[1:]
    print(f"原始表頭：{header}")
    print(f"資料筆數：{len(data_rows)}")

    zh_header = translate_header(header)
    out_csv = os.path.splitext(xlsx_path)[0] + "_中文欄名.csv"
    write_csv(zh_header, data_rows, out_csv)


if __name__ == "__main__":
    main()

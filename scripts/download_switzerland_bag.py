#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下載並解析瑞士BAG(聯邦衛生署)每月「Spezialitätenliste(SL)」藥品主檔Excel檔。

網址規律（已由使用者提供實例確認）：
    https://epl.bag.admin.ch/static/sl/current/excel/publication/2026-07-01/Publications.xlsx
規律：.../publication/YYYY-MM-01/Publications.xlsx，每月1號那份，每月更新一次，不用登入。

全程只用 Python 標準函式庫解析（zipfile+xml.etree），不需要openpyxl/pandas，
跟比利時/瑞典/日本那幾支程式共用同一套xlsx解析邏輯。

使用方式：
    python3 download_switzerland_bag.py                # 自動抓「這個月」，抓不到往前試最多6個月
    python3 download_switzerland_bag.py --date 2026-07  # 指定年月
"""

import argparse
import datetime
import io
import os
import re
import zipfile
import xml.etree.ElementTree as ET
import urllib.request
import ssl
import csv

BASE_URL = "https://epl.bag.admin.ch/static/sl/current/excel/publication/"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


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

# 依BAG官方查詢頁面(spezialitätenliste.ch)實際顯示的欄位名稱整理，
# 未經官方文件逐欄核對，對不上字典的欄位一律保留原文，不亂猜。
FIELD_NAME_MAP = {
    "FAP": "廠商出廠價(Fabrikabgabepreis)",
    "PP": "藥局零售價(Publikumspreis)",
    "Selbstbehalt": "病患自付比例",
    "GTIN": "條碼(GTIN)",
    "ATC Code": "ATC代碼",
    "ATC-Code": "ATC代碼",
    "Zulassungsinhaberin": "藥證持有商",
    "Wirkstoff": "成分",
    "Limitierung": "給付限制",
    "Befristungen": "給付期限註記",
    "IT-Code": "IT代碼(治療分類)",
    "Packungsgrösse": "包裝規格",
    "Menge": "數量",
    "Bezeichnung": "藥品名稱",
    "Charakteristikum": "劑型特性",
    "Liste": "所屬清單(SL/GGSL)",
}


# ---------------------------------------------------------------------------
# 第一步：組出網址並下載（自動抓最新月份，抓不到就往前試，最多6次）
# ---------------------------------------------------------------------------

def build_url(year, month):
    return f"{BASE_URL}{year:04d}-{month:02d}-01/Publications.xlsx"


def try_download(year, month, out_dir="."):
    url = build_url(year, month)
    filename = os.path.join(out_dir, f"Publications_{year:04d}{month:02d}.xlsx")
    if os.path.exists(filename):
        print(f"[跳過] {filename} 已存在")
        return filename

    print(f"[嘗試下載] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with _urlopen_with_fallback(req, timeout=60) as resp:
            data = resp.read()
    except Exception as e:
        print(f"  找不到（{e}），改試上一個月")
        return None

    with open(filename, "wb") as f:
        f.write(data)
    print(f"[完成] {filename}（{len(data)} bytes）")
    return filename


def download_latest(max_tries=6, out_dir="."):
    today = datetime.date.today()
    year, month = today.year, today.month
    for _ in range(max_tries):
        path = try_download(year, month, out_dir)
        if path:
            return path
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    raise RuntimeError("試了好幾個月都下載不到檔案，網址規律可能變了")


# ---------------------------------------------------------------------------
# 第二步：純標準函式庫解析xlsx（跟比利時/瑞典/日本那幾支程式共用同一套邏輯）
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


def find_header_row(rows, max_scan=10):
    """
    有些官方Excel第一列是標題文字，不是表頭。掃前面幾列，
    找「非空儲存格數>=3」且包含關鍵字的那一列當表頭。
    """
    keywords = ["FAP", "PP", "ATC", "GTIN", "Wirkstoff", "Bezeichnung"]
    for i, row in enumerate(rows[:max_scan]):
        non_empty = [cell for cell in row if cell not in (None, "")]
        if len(non_empty) < 3:
            continue
        row_text = "".join(row)
        if any(k in row_text for k in keywords):
            return i, row
    return 0, rows[0] if rows else []


def translate_header(header_row):
    translated = []
    for name in header_row:
        key = (name or "").strip()
        if key in FIELD_NAME_MAP:
            translated.append(f"{FIELD_NAME_MAP[key]}（原欄位：{key}）")
        else:
            translated.append(name)
    return translated


def write_csv(header, rows, out_path):
    with io.open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"[完成] 已輸出 {len(rows)} 筆資料到 {out_path}")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="下載並解析瑞士BAG每月SL藥品Excel參考檔")
    parser.add_argument("--date", type=str, default=None, help="指定年月 YYYY-MM，不指定就自動抓最新")
    args = parser.parse_args()

    if args.date:
        year, month = map(int, args.date.split("-"))
        xlsx_path = try_download(year, month)
        if not xlsx_path:
            raise RuntimeError(f"{args.date} 這期下載失敗，請確認網址或日期是否正確")
    else:
        xlsx_path = download_latest()

    print(f"\n[解析中] {xlsx_path}")
    rows = read_xlsx_first_sheet(xlsx_path)
    if not rows:
        print("這個檔案是空的")
        return

    header_idx, header = find_header_row(rows)
    data_rows = rows[header_idx + 1:]
    print(f"表頭在第{header_idx + 1}列：{header}")
    print(f"資料筆數：{len(data_rows)}")

    zh_header = translate_header(header)
    out_csv = os.path.splitext(xlsx_path)[0] + "_中文欄名.csv"
    write_csv(zh_header, data_rows, out_csv)


if __name__ == "__main__":
    main()

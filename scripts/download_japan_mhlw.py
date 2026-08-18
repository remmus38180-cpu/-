#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下載並解析日本厚生労働省(MHLW)「薬価基準収載品目リスト」Excel檔案。

來源頁面（每次薬価改定會在這頁更新新網址）：
    https://www.mhlw.go.jp/topics/2026/04/tp20260401-01.html

目前(2026/7/15適用版)下載網址：
    內用薬(口服藥，Eliquis屬這類)：
        https://www.mhlw.go.jp/topics/2026/04/xls/tp20260715-01_01.xlsx
    注射薬(針劑)：
        https://www.mhlw.go.jp/topics/2026/04/xls/tp20260715-01_02.xlsx
    外用薬(外用藥)：
        https://www.mhlw.go.jp/topics/2026/04/xls/tp20260715-01_03.xlsx

注意：這個網址每次薬価改定就會換掉(日期會變)，不是永久固定網址，
跟法國/比利時那種固定路徑不一樣。目前寫死在下面 DEFAULT_URLS，
以後過期了要回去上面那個頁面手動確認新網址，更新這支程式。

格式：Excel，有表頭。全程用Python標準函式庫解析(zipfile+xml.etree)，
不需要openpyxl/pandas。

使用方式：
    python3 download_japan_mhlw.py              # 下載三個檔案(內用/注射/外用)全部處理
    python3 download_japan_mhlw.py --only naiyo  # 只處理內用薬(查Eliquis只需要這個)
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

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

DEFAULT_URLS = {
    "naiyo": "https://www.mhlw.go.jp/topics/2026/04/xls/tp20260715-01_01.xlsx",   # 內用薬(口服)
    "chusha": "https://www.mhlw.go.jp/topics/2026/04/xls/tp20260715-01_02.xlsx",  # 注射薬
    "gaiyo": "https://www.mhlw.go.jp/topics/2026/04/xls/tp20260715-01_03.xlsx",   # 外用薬
}

# 依官網「薬価基準収載品目リスト」頁面上的欄位文字說明整理，
# 實際下載後若表頭字樣略有不同，程式會保留原文不亂猜。
FIELD_NAME_MAP = {
    "薬価基準収載医薬品コード": "藥價基準收載代碼",
    "医薬品名": "藥品名稱",
    "品名": "藥品名稱",
    "規格": "含量/劑型規格",
    "単位": "計價單位",
    "薬価": "藥價(日圓)",
    "メーカー名": "藥證持有商/廠商",
    "区分": "先發/學名藥區分",
}


# ---------------------------------------------------------------------------
# 第一步：下載
# ---------------------------------------------------------------------------

def download_file(url, out_dir="."):
    filename = os.path.join(out_dir, os.path.basename(url))
    if os.path.exists(filename):
        print(f"[跳過] {filename} 已存在")
        return filename

    print(f"[下載中] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with _urlopen_with_fallback(req, timeout=60) as resp:
            data = resp.read()
    except Exception as e:
        raise RuntimeError(
            f"下載失敗：{e}\n"
            f"這個網址是寫死的(每次薬価改定會換)，"
            f"請去 https://www.mhlw.go.jp/topics/2026/04/tp20260401-01.html "
            f"確認最新網址並更新程式裡的 DEFAULT_URLS"
        )

    with open(filename, "wb") as f:
        f.write(data)
    print(f"[完成] {filename}（{len(data)} bytes）")
    return filename


# ---------------------------------------------------------------------------
# 第二步：純標準函式庫解析xlsx（跟比利時/瑞典那兩支程式共用同一套邏輯）
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
    厚労省這類公文Excel常見在最上面放一列「令和8年...適用 薬価基準収載品目リスト」
    這種標題列（通常只有1個儲存格有內容），不是真正的表頭。
    真正表頭的特徵是：同一列有好幾個欄位（不只1格）、且包含關鍵字。
    掃前面幾列，找「非空儲存格數 >= 3」且包含關鍵字的那一列。
    回傳 (header_row_index, header_row)
    """
    keywords = ["薬価", "品名", "医薬品", "規格", "コード", "メーカー"]
    for i, row in enumerate(rows[:max_scan]):
        non_empty = [cell for cell in row if cell not in (None, "")]
        if len(non_empty) < 3:
            continue
        row_text = "".join(row)
        if any(k in row_text for k in keywords):
            return i, row
    # 找不到就假設第一列是表頭
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


def process_file(xlsx_path):
    rows = read_xlsx_first_sheet(xlsx_path)
    if not rows:
        print(f"{xlsx_path} 是空檔案")
        return
    header_idx, header = find_header_row(rows)
    data_rows = rows[header_idx + 1:]
    print(f"表頭在第{header_idx + 1}列：{header}")
    print(f"資料筆數：{len(data_rows)}")

    zh_header = translate_header(header)
    out_csv = os.path.splitext(xlsx_path)[0] + "_中文欄名.csv"
    write_csv(zh_header, data_rows, out_csv)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="下載並解析日本MHLW薬価基準收載品目リスト")
    parser.add_argument(
        "--only", choices=["naiyo", "chusha", "gaiyo"], default=None,
        help="只處理其中一個檔案：naiyo=內用薬(口服) chusha=注射薬 gaiyo=外用薬。不指定就三個都跑"
    )
    args = parser.parse_args()

    targets = {args.only: DEFAULT_URLS[args.only]} if args.only else DEFAULT_URLS

    for label, url in targets.items():
        print(f"\n=== 處理 {label} ===")
        xlsx_path = download_file(url)
        process_file(xlsx_path)


if __name__ == "__main__":
    main()

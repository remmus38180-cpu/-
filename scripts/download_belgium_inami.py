#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下載並解析比利時 INAMI/RIZIV「fichier de référence médicaments」每月藥價參考檔（Excel格式）。

網址規律（已由使用者提供兩期實例確認）：
    https://www.riziv.fgov.be/SiteCollectionDocuments/liste_specialites_20260701.xlsx
    https://www.riziv.fgov.be/SiteCollectionDocuments/liste_specialites_20260601.xlsx
規律：liste_specialites_YYYYMM01.xlsx，永遠是每月「01」號那天，每月更新一次。

本程式全程只用 Python 標準函式庫：
    - urllib.request 下載檔案
    - zipfile + xml.etree.ElementTree 解析 .xlsx
      （.xlsx 檔案本質上是一個zip壓縮包，裡面裝的是XML檔，
       不需要 openpyxl / pandas 這類第三方套件）

使用方式：
    python3 download_belgium_inami.py                # 自動抓「這個月」，抓不到就往前抓上個月...最多往前試6個月
    python3 download_belgium_inami.py --date 2026-07  # 指定年月
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

BASE_URL = "https://www.riziv.fgov.be/SiteCollectionDocuments/"
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

# 依官方「DESCRIPTION FICHIER INAMI」文件整理的欄位代碼中文對照表。
# 只有出現在檔案表頭、且能對上這份字典的欄位才會被翻成中文，
# 對不上的欄位會保留原始英文/法文代碼（避免亂翻）。
FIELD_NAME_MAP = {
    "S_COD": "INAMI代碼",
    "S_NAM": "藥品名稱",
    "S_NAM_SPECIF": "藥品名稱附註",
    "F_ORGA": "藥證持有商",
    "ATC_COD": "ATC代碼",
    "S_BIG": "大包裝註記",
    "S_COD_F": "醫院包裹式給付註記",
    "APB_CNK_PUB": "CNK代碼(藥局零售)",
    "APB_CNK_AMB": "CNK代碼(門診)",
    "APB_CNK_HOS": "CNK代碼(住院)",
    "APB_CNK_RH": "CNK代碼(安養機構)",
    "S_BEG_ADMIS_DAT": "給付生效日",
    "S_SPEC_TYP_ID": "藥品類型(1=一般藥品,4=放射性藥品)",
    "SPB_DEL_ID": "調劑通路(1=藥局,2=門診,3=住院,4=出廠,5=安養機構)",
    "SPB_PUBLIC": "零售價",
    "SPB_BASE": "給付基準價",
    "SPB_R_BASE": "給付基準價(R類品項)",
    "SPB_DIFF_AMB": "門診自付差額",
    "SPBH_DAT_BEG": "價格生效日",
    "CAT_LBL": "給付類別(A/B/C/Cs/Cx)",
    "RFGP_COD": "給付群組代碼",
    "LVL1_LBL": "給付章節",
    "LVL2_NUM": "給付段落編號",
    "SRC_CODE_M": "M碼註記",
    "SRC_CODE_R": "R碼註記",
    "SRC_CODE_T": "T碼註記",
    "SRC_CODE_E": "E碼註記(特殊情況臨時給付)",
    "OGC_TYPE": "藥品種類(O原廠/R原廠參考品/G學名藥/C copie/I輸入藥/BI生物製劑)",
    "CHEAPEST": "是否為最便宜學名藥",
    "CHEAP": "是否為平價藥",
    "UNAVAILABLE": "是否缺貨(1=缺貨)",
    "RPT_PCK_LBL_FR": "包裝說明(法文)",
    "RPT_PCK_LBL_NL": "包裝說明(荷文)",
}


# ---------------------------------------------------------------------------
# 第一步：組出目標網址並下載（找不到就自動往前一個月再試，最多試6次）
# ---------------------------------------------------------------------------

def build_url(year, month):
    return f"{BASE_URL}liste_specialites_{year:04d}{month:02d}01.xlsx"


def try_download(year, month, out_dir="."):
    url = build_url(year, month)
    filename = os.path.join(out_dir, os.path.basename(url))
    if os.path.exists(filename):
        print(f"[跳過] {filename} 已存在")
        return filename

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        print(f"[嘗試下載] {url}")
        with _urlopen_with_fallback(req, timeout=60) as resp:
            data = resp.read()
    except Exception as e:
        print(f"  找不到（{e}），改試上一個月")
        return None

    with open(filename, "wb") as f:
        f.write(data)
    print(f"[完成] {filename}（{len(data)} bytes）")
    return filename


def download_latest(start_year=None, start_month=None, max_tries=6, out_dir="."):
    if start_year is None:
        today = datetime.date.today()
        start_year, start_month = today.year, today.month

    year, month = start_year, start_month
    for _ in range(max_tries):
        path = try_download(year, month, out_dir)
        if path:
            return path
        # 往前推一個月
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    raise RuntimeError("試了好幾個月都下載不到檔案，可能網址規律變了，建議手動確認")


# ---------------------------------------------------------------------------
# 第二步：純標準函式庫解析 .xlsx（zip + XML），不用openpyxl/pandas
# ---------------------------------------------------------------------------

def col_letter_to_index(cell_ref):
    """把儲存格參照(如 'C7')裡的欄字母('C')轉成從0開始的欄位索引"""
    letters = re.match(r"[A-Z]+", cell_ref).group()
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def read_xlsx_first_sheet(path):
    """
    讀取xlsx裡第一個工作表，回傳 list of list（每列是一個字串陣列）。
    處理共用字串表(sharedStrings.xml)與內嵌字串兩種儲存方式。
    """
    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()

        # 讀取共用字串表（如果有的話）
        shared_strings = []
        if "xl/sharedStrings.xml" in names:
            with zf.open("xl/sharedStrings.xml") as f:
                tree = ET.parse(f)
            for si in tree.getroot().findall("m:si", NS):
                # 一個 <si> 可能包含多個 <t>（富文字），全部串起來
                texts = si.findall(".//m:t", NS)
                shared_strings.append("".join(t.text or "" for t in texts))

        # 找出第一個工作表的路徑（通常是 xl/worksheets/sheet1.xml）
        sheet_candidates = [n for n in names if re.match(r"xl/worksheets/sheet\d+\.xml", n)]
        sheet_candidates.sort()
        if not sheet_candidates:
            raise RuntimeError("在xlsx裡找不到工作表(worksheet) XML，檔案格式可能不是標準xlsx")
        sheet_path = sheet_candidates[0]

        with zf.open(sheet_path) as f:
            tree = ET.parse(f)

    rows_out = []
    sheet_data = tree.getroot().find("m:sheetData", NS)
    for row in sheet_data.findall("m:row", NS):
        row_values = {}
        max_col = -1
        for c in row.findall("m:c", NS):
            ref = c.get("r", "")
            col_idx = col_letter_to_index(ref) if ref else len(row_values)
            cell_type = c.get("t", "")  # "s"=共用字串, "str"=公式字串, "inlineStr"=內嵌字串, 無=數字
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


# ---------------------------------------------------------------------------
# 第三步：套用中文欄名對照表，輸出成CSV
# ---------------------------------------------------------------------------

def translate_header(header_row):
    """
    header_row: 原始表頭字串list
    回傳翻譯後的表頭：對得上 FIELD_NAME_MAP 的翻中文，對不上的保留原樣，
    並在後面加註「（原欄位：XXX）」避免混淆。
    """
    translated = []
    for name in header_row:
        key = name.strip().upper()
        if key in FIELD_NAME_MAP:
            translated.append(f"{FIELD_NAME_MAP[key]}（原欄位：{name}）")
        else:
            translated.append(name)  # 對不上就保留原文，不亂猜
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
    parser = argparse.ArgumentParser(description="下載並解析比利時INAMI每月藥價Excel參考檔")
    parser.add_argument(
        "--date", type=str, default=None,
        help="指定年月，格式 YYYY-MM（例如 2026-07）。不指定就自動抓最新一期"
    )
    args = parser.parse_args()

    if args.date:
        year, month = map(int, args.date.split("-"))
        xlsx_path = try_download(year, month)
        if not xlsx_path:
            raise RuntimeError(f"{args.date} 這期檔案下載失敗，請確認網址或日期是否正確")
    else:
        xlsx_path = download_latest()

    print(f"\n[解析中] {xlsx_path}")
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

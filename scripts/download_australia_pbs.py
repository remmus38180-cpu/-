#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下載並解析澳洲PBS(Pharmaceutical Benefits Scheme)「PBS API CSV files」整批壓縮檔。

背景：PBS舊制的Text files(drug_yyyymmdd.txt等)已在2026年5月正式停用，
現在唯一的官方資料來源是「PBS API」，以及給不想接API的人用的
「PBS API CSV files」整批壓縮包——這才是原始手冊裡指定要抓cp2p欄位的
正確位置(cp2p在PBS API裡是drug相關端點/表格裡的一個欄位)。

網址規律（已確認，跟比利時同一套邏輯）：
    https://www.pbs.gov.au/downloads/YYYY/MM/YYYY-MM-01-PBS-API-CSV-files.zip
每月1號發布一次，不用登入。

裡面是一個zip，內含PBS API所有端點(table)的CSV檔（不只一個檔案），
本程式會：
    1. 下載zip（自動抓最新月份，抓不到就往前試，最多6個月）
    2. 解壓縮全部CSV
    3. 掃描所有CSV，找出表頭含有「cp2p」欄位的那個檔案（就是手冊指定要的價格檔）
    4. 把該檔輸出成中文欄名版本

全程只用 Python 標準函式庫（urllib、zipfile、csv），不需要第三方套件。

使用方式：
    python3 download_australia_pbs.py
"""

import argparse
import csv
import datetime
import io
import os
import zipfile
import urllib.request
import ssl

BASE_URL = "https://www.pbs.gov.au/downloads/"


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

# 依 PBS Text Extracts 官方欄位說明（data.pbs.gov.au/text-extracts.html）整理，
# 這份文件列出的欄位順序，PBS API CSV裡的欄位名稱大概率沿用同一套代碼。
# 對不上的欄位一律保留原文，不亂猜。
FIELD_NAME_MAP = {
    "program-code": "給付計畫代碼",
    "atc": "ATC代碼",
    "atc-type": "ATC代碼類型",
    "atc-print-option": "ATC顯示選項",
    "item-code": "PBS品項代碼",
    "restriction-flag": "限制用藥註記",
    "has-caution": "是否有警語",
    "has-note": "是否有附註",
    "mq": "最大處方量(Maximum Quantity)",
    "repeats": "可重複調劑次數",
    "manufacturer-code": "廠商代碼",
    "pack-size": "包裝顆數",
    "markup-band": "加成等級",
    "fee-code": "調劑費代碼",
    "dangerous-drug-code": "管制藥品代碼",
    "brand-premium": "品牌溢價",
    "therapeutic-premium": "治療同等溢價",
    "cp2p": "健保申報藥局進價(Claimed Price to Pharmacist)",
    "cdpmq": "健保申報最大量調劑總價",
    "lp2p": "表定藥局進價(List Price to Pharmacist)",
    "ldpmq": "表定最大量調劑總價",
    "mp2p": "廠商藥局進價(Manufacturer Price to Pharmacist)",
    "mdpmq": "廠商最大量調劑總價",
    "mrvsn": "最高零售價漲幅版本",
    "bioequivalence": "生體相等性代碼",
    "brand-name": "品牌名稱",
    "mp-pt": "藥品名稱(Medicinal Product)",
    "tpuu-or-mpp-pt": "藥品規格名稱",
}


# ---------------------------------------------------------------------------
# 第一步：組出網址並下載（自動抓最新月份，抓不到就往前試）
# ---------------------------------------------------------------------------

def build_url(year, month):
    return f"{BASE_URL}{year:04d}/{month:02d}/{year:04d}-{month:02d}-01-PBS-API-CSV-files.zip"


def try_download(year, month, out_dir="."):
    url = build_url(year, month)
    filename = os.path.join(out_dir, os.path.basename(url))
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
    raise RuntimeError("試了好幾個月都下載不到檔案，PBS網址規律可能變了")


# ---------------------------------------------------------------------------
# 第二步：解壓縮，掃描所有CSV找出含cp2p欄位的檔案
# ---------------------------------------------------------------------------

def extract_all_csv(zip_path, out_dir="."):
    csv_paths = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if name.lower().endswith(".csv"):
                zf.extract(name, out_dir)
                csv_paths.append(os.path.join(out_dir, name))
    print(f"[解壓縮] 共{len(csv_paths)}個CSV檔")
    return csv_paths


def find_price_file(csv_paths, target_field="cp2p"):
    """掃描所有CSV，回傳第一個表頭含target_field的檔案路徑及其表頭"""
    for path in csv_paths:
        try:
            with io.open(path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, None)
        except Exception:
            continue
        if header and any(h.strip().lower() == target_field for h in header):
            return path, header
    return None, None


# ---------------------------------------------------------------------------
# 第三步：翻中文欄名，輸出
# ---------------------------------------------------------------------------

def translate_header(header):
    translated = []
    for name in header:
        key = name.strip().lower()
        if key in FIELD_NAME_MAP:
            translated.append(f"{FIELD_NAME_MAP[key]}（原欄位：{name}）")
        else:
            translated.append(name)
    return translated


def convert_to_chinese_csv(csv_path, header):
    zh_header = translate_header(header)
    out_path = os.path.splitext(csv_path)[0] + "_中文欄名.csv"
    with io.open(csv_path, "r", encoding="utf-8-sig", newline="") as fin:
        reader = csv.reader(fin)
        next(reader)  # 跳過原表頭
        rows = list(reader)
    with io.open(out_path, "w", encoding="utf-8-sig", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow(zh_header)
        writer.writerows(rows)
    print(f"[完成] 已輸出 {len(rows)} 筆資料到 {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="下載並解析澳洲PBS API CSV整批檔")
    parser.add_argument("--date", type=str, default=None, help="指定年月 YYYY-MM，不指定就抓最新")
    args = parser.parse_args()

    if args.date:
        year, month = map(int, args.date.split("-"))
        zip_path = try_download(year, month)
        if not zip_path:
            raise RuntimeError(f"{args.date} 這期下載失敗")
    else:
        zip_path = download_latest()

    csv_paths = extract_all_csv(zip_path)
    price_file, header = find_price_file(csv_paths)

    if not price_file:
        print("在所有CSV裡都沒找到含cp2p欄位的檔案，"
              "PBS API的表格結構可能改了，建議打開解壓出來的CSV人工看一下表頭")
        print(f"目前解壓出的檔案清單：{csv_paths}")
        return

    print(f"\n找到含cp2p欄位的檔案：{price_file}")
    print(f"原始表頭：{header}")
    convert_to_chinese_csv(price_file, header)


if __name__ == "__main__":
    main()

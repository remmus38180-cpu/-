#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下載並合併法國公開藥品資料庫(base-donnees-publique.medicaments.gouv.fr)三個檔案：

  1. CIS_bdpm.txt        藥品主檔(藥品基本資料)
  2. CIS_CIP_bdpm.txt    藥品包裝檔(含藥價、給付比例)
  3. CIS_GENER_bdpm.txt  學名藥群組檔

三個檔案都是「無表頭、Tab分隔、Latin-1(cp1252)編碼」的純文字檔，
用 Code CIS(藥品主檔代碼)當作合併鍵(key)串接。

全程只用 Python 標準函式庫(urllib、io、csv)，不需要 pandas / requests 等套件。

使用方式：
    python3 merge_cip_files.py

輸出：
    merged_output.csv   (utf-8-sig編碼，Excel可直接開啟，欄位為中文)
"""

import urllib.request
import ssl
import csv
import io
import os


def _make_ssl_context():
    """
    建立一個會信任Windows系統憑證存放區的SSL context。

    背景：有些公司/機關電腦有網路安全設備會攔截HTTPS流量並用自己的憑證
    重新加密（俗稱SSL/TLS檢查），Windows作業系統本身信任這張憑證，
    但Python預設用的是自帶的一份固定憑證清單，不包含公司內部這張，
    所以會出現 CERTIFICATE_VERIFY_FAILED 錯誤。這裡改成同時把
    Windows「受信任的根憑證授權單位」存放區也載入，讓Python跟
    瀏覽器一樣信任同一份憑證清單。
    """
    ctx = ssl.create_default_context()
    try:
        for store_name in ("CA", "ROOT"):
            for cert, encoding, trust in ssl.enum_certificates(store_name):
                try:
                    ctx.load_verify_locations(cadata=cert)
                except ssl.SSLError:
                    pass
    except AttributeError:
        pass  # 非Windows系統沒有 ssl.enum_certificates，跳過即可
    return ctx


_SSL_CONTEXT = _make_ssl_context()
_UNVERIFIED_SSL_CONTEXT = ssl._create_unverified_context()

BASE_URL = "https://base-donnees-publique.medicaments.gouv.fr/download/file/"
FILES = {
    "CIS": "CIS_bdpm.txt",
    "CIP": "CIS_CIP_bdpm.txt",
    "GENER": "CIS_GENER_bdpm.txt",
}
ENCODING = "cp1252"  # 官方文件用 latin1/cp1252，法文重音字元才不會亂碼

# ---------------------------------------------------------------------------
# 第一步：下載三個檔案（若本機已存在同名檔案就跳過，避免重複下載）
# ---------------------------------------------------------------------------

def download_file(filename):
    """下載單一檔案到本機，回傳本機檔名"""
    if os.path.exists(filename):
        print(f"[跳過] {filename} 已存在，不重新下載")
        return filename

    url = BASE_URL + filename
    print(f"[下載中] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=60, context=_SSL_CONTEXT) as response:
            data = response.read()
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            print("[警告] 憑證驗證失敗（通常是公司網路的安全設備造成），"
                  "改用不驗證憑證的方式繼續下載。"
                  "這份是政府公開資料檔，非帳密或金融資料，風險可接受。")
            with urllib.request.urlopen(req, timeout=60, context=_UNVERIFIED_SSL_CONTEXT) as response:
                data = response.read()
        else:
            raise
    with open(filename, "wb") as f:
        f.write(data)
    print(f"[完成] {filename}（{len(data)} bytes）")
    return filename


# ---------------------------------------------------------------------------
# 第二步：讀取並解析 Tab 分隔檔案
# ---------------------------------------------------------------------------

def read_tab_file(filename, encoding=ENCODING):
    """
    讀取無表頭、Tab分隔的檔案，回傳 list of list（每一列是一個字串陣列）。
    用標準函式庫 csv 模組處理，delimiter 指定為 '\t'。
    """
    rows = []
    with io.open(filename, "r", encoding=encoding, errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if row:  # 跳過空行
                rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# 第三步：把每個檔案轉成以 Code CIS 為鍵的查找結構
# ---------------------------------------------------------------------------

def build_cis_lookup(cis_rows):
    """
    CIS_bdpm.txt 欄位（共12欄，索引從0開始）：
      0 藥品主檔代碼(CIS)
      1 藥品名稱
      2 藥品劑型
      3 給藥途徑
      4 上市許可狀態
      5 上市許可程序類型
      6 上市狀態
      7 許可日期
      8 資料庫狀態註記
      9 歐盟許可證號
      10 藥證持有商
      11 加強監視註記
    每個 CIS 理論上只會出現一次，做成 dict：{ CIS代碼: {欄位...} }
    """
    lookup = {}
    for row in cis_rows:
        if len(row) < 12:
            row = row + [""] * (12 - len(row))  # 欄位不足時補空字串，避免索引錯誤
        cis_code = row[0]
        lookup[cis_code] = {
            "藥品名稱": row[1],
            "藥品劑型": row[2],
            "給藥途徑": row[3],
            "上市許可狀態": row[4],
            "上市許可程序類型": row[5],
            "上市狀態": row[6],
            "許可日期": row[7],
            "資料庫狀態註記": row[8],
            "歐盟許可證號": row[9],
            "藥證持有商": row[10],
            "加強監視註記": row[11],
        }
    return lookup


def build_gener_lookup(gener_rows):
    """
    CIS_GENER_bdpm.txt 欄位（共5欄）：
      0 學名藥群組代碼
      1 學名藥群組名稱
      2 藥品主檔代碼(CIS)
      3 學名藥類型代碼(0=原廠, 1=學名藥, 2=劑量互補學名藥, 4=可替代學名藥)
      5 群組內排序編號
    一個 CIS 理論上只屬於一個群組，但保守起見用 list 存，避免漏資料。
    """
    type_map = {
        "0": "原廠藥(princeps)",
        "1": "學名藥(générique)",
        "2": "劑量互補學名藥",
        "4": "可替代學名藥",
    }
    lookup = {}
    for row in gener_rows:
        if len(row) < 5:
            row = row + [""] * (5 - len(row))
        cis_code = row[2]
        entry = {
            "學名藥群組代碼": row[0],
            "學名藥群組名稱": row[1],
            "學名藥類型": type_map.get(row[3], row[3]),
        }
        lookup.setdefault(cis_code, []).append(entry)
    return lookup


# ---------------------------------------------------------------------------
# 第四步：以 CIP 檔為主表，逐列合併 CIS 主檔與學名藥群組資料
# ---------------------------------------------------------------------------

def merge_all(cip_rows, cis_lookup, gener_lookup):
    """
    CIS_CIP_bdpm.txt 欄位（共11欄）：
      0  藥品主檔代碼(CIS)
      1  CIP7碼
      2  包裝名稱
      3  包裝行政狀態
      4  包裝上市狀態
      5  上市申報日期
      6  CIP13碼
      7  機構採購核准(Agrément collectivités)
      8  給付比例
      9  藥價(歐元)
      10 給付適應症說明
    """
    merged = []
    for row in cip_rows:
        if len(row) < 11:
            row = row + [""] * (11 - len(row))

        cis_code = row[0]
        cis_info = cis_lookup.get(cis_code, {})
        gener_list = gener_lookup.get(cis_code, [])
        # 一個CIS若屬於多個群組紀錄，這裡只取第一筆；多數藥品只會有一筆
        gener_info = gener_list[0] if gener_list else {
            "學名藥群組代碼": "",
            "學名藥群組名稱": "",
            "學名藥類型": "",
        }

        record = {
            "藥品主檔代碼CIS": cis_code,
            "藥品名稱": cis_info.get("藥品名稱", ""),
            "藥品劑型": cis_info.get("藥品劑型", ""),
            "給藥途徑": cis_info.get("給藥途徑", ""),
            "上市許可狀態": cis_info.get("上市許可狀態", ""),
            "上市狀態": cis_info.get("上市狀態", ""),
            "藥證持有商": cis_info.get("藥證持有商", ""),
            "CIP7碼": row[1],
            "包裝名稱": row[2],
            "包裝行政狀態": row[3],
            "包裝上市狀態": row[4],
            "上市申報日期": row[5],
            "CIP13碼": row[6],
            "機構採購核准": row[7],
            "給付比例": row[8],
            "藥價歐元": row[9],
            "給付適應症說明": row[10],
            "學名藥群組代碼": gener_info["學名藥群組代碼"],
            "學名藥群組名稱": gener_info["學名藥群組名稱"],
            "學名藥類型": gener_info["學名藥類型"],
        }
        merged.append(record)
    return merged


# ---------------------------------------------------------------------------
# 第五步：輸出成 Excel 可直接開啟的 CSV（中文欄名、utf-8-sig編碼）
# ---------------------------------------------------------------------------

def write_csv(records, out_path="merged_output.csv"):
    if not records:
        print("沒有資料可寫出")
        return
    fieldnames = list(records[0].keys())
    # utf-8-sig：開頭加BOM，Excel雙擊開啟中文欄名才不會亂碼
    with io.open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"[完成] 已輸出 {len(records)} 筆資料到 {out_path}")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    # 1. 下載三個檔案
    cis_file = download_file(FILES["CIS"])
    cip_file = download_file(FILES["CIP"])
    gener_file = download_file(FILES["GENER"])

    # 2. 讀取解析
    cis_rows = read_tab_file(cis_file)
    cip_rows = read_tab_file(cip_file)
    gener_rows = read_tab_file(gener_file)
    print(f"CIS筆數={len(cis_rows)}  CIP筆數={len(cip_rows)}  GENER筆數={len(gener_rows)}")

    # 3. 建立查找表
    cis_lookup = build_cis_lookup(cis_rows)
    gener_lookup = build_gener_lookup(gener_rows)

    # 4. 合併（以 CIP 檔為主表，逐列補上 CIS 與 GENER 資訊）
    merged = merge_all(cip_rows, cis_lookup, gener_lookup)

    # 5. 輸出
    write_csv(merged, "merged_output.csv")


if __name__ == "__main__":
    main()

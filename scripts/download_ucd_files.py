#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下載並解析法國醫院用藥 UCD 資料檔（BdM_IT，codage.ext.cnamts.fr）。

跟藥局用的 CIP 三檔（base-donnees-publique.medicaments.gouv.fr）不同，
UCD 檔案有兩個地方比較麻煩，先講清楚：

1. 下載網址不固定：UCD壓縮檔的版本號是一個逐次+1的流水號，
   每次CNAM更新就會+1，網址長這樣：
       http://www.codage.ext.cnamts.fr/f_mediam/fo/bdm_it/UCD_TOT_<版本號5碼>.zip
   例如版本1524就是 UCD_TOT_01524.zip。版本號目前看得到的地方，
   是你截圖裡「BdM_IT」選單下方寫的「Version : 1524」這一行——
   查詢頁面上顯示的版本號，跟下載檔案的版本號是同一組流水號，
   所以你要先去網站上看一眼目前版本號，填進這支程式的 START_VERSION。

2. 檔案格式是 .dbf（dBASE資料庫檔），不是純文字檔，不能直接用記事本開。
   dbf是舊式資料庫格式，但格式本身有公開規格（表頭+欄位描述+資料列），
   可以用Python標準函式庫的 struct 模組自己解析二進位內容，不需要
   dbfread、pandas 等套件。

3. 老實說在哪：CIP那三個檔案（CIS_bdpm等）CNAM/ANSM有發正式PDF文件寫明
   每一欄的中文對照意思；但UCD這幾個dbf檔，我沒有找到官方公開、逐欄位
   說明用途的文件。dbf檔本身的表頭會存「欄位名稱」（通常是縮寫過的法文，
   例如 CODE_UCD、LIB_UCD、PRIX 這類），程式會把這些原始欄位名稱讀出來
   當作CSV表頭，但不會幫你「腦補翻譯」成中文欄名，因為那樣可能會翻錯。
   建議：下載後打開CSV，把出現的欄位縮寫貼給我，我再一個一個查證是什麼意思，
   比較不會誤導你。

使用方式：
    python3 download_ucd_files.py --version 1524

會做的事：
    1. 下載 UCD_TOT_01524.zip
    2. 解壓縮，找出裡面的 .dbf 檔
    3. 用純Python解析dbf，輸出成 utf-8-sig 編碼的 CSV（Excel可直接開）
"""

import argparse
import io
import os
import struct
import urllib.request
import ssl
import zipfile
import csv

BASE_URL = "http://www.codage.ext.cnamts.fr/codif/bdm_it/download_file.php"
ENCODING = "cp1252"


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


# ---------------------------------------------------------------------------
# 第一步：下載指定版本號的zip檔
# ---------------------------------------------------------------------------

def download_zip(version, out_dir="."):
    """
    version: 整數，例如 796
    真實下載網址格式（已由使用者實際複製連結確認）：
        http://www.codage.ext.cnamts.fr/codif/bdm_it/download_file.php?filename=bdm_it/UCD_TOT_00796.zip
    檔名部分固定是5碼補零，例如 796 -> UCD_TOT_00796.zip
    """
    filename = f"UCD_TOT_{version:05d}.zip"
    url = f"{BASE_URL}?filename=bdm_it/{filename}"
    dest = os.path.join(out_dir, filename)

    if os.path.exists(dest):
        print(f"[跳過] {dest} 已存在")
        return dest

    print(f"[下載中] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with _urlopen_with_fallback(req, timeout=60) as response:
            data = response.read()
    except Exception as e:
        raise RuntimeError(
            f"下載失敗（版本 {version} 可能不存在，或CNAM已改版）：{e}"
        )

    with open(dest, "wb") as f:
        f.write(data)
    print(f"[完成] {dest}（{len(data)} bytes）")
    return dest


# ---------------------------------------------------------------------------
# 第二步：解壓縮，找出裡面所有 .dbf 檔案
# ---------------------------------------------------------------------------

def extract_dbf_files(zip_path, out_dir="."):
    dbf_paths = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        all_names = zf.namelist()
        for name in all_names:
            if name.lower().endswith(".dbf"):
                zf.extract(name, out_dir)
                dbf_paths.append(os.path.join(out_dir, name))
                print(f"[解壓縮] {name}")

        if not dbf_paths and len(all_names) == 1:
            # CNAM有時候發布的檔案裡面那份資料檔完全沒有副檔名
            # （檔名就是 UCD_TOT_00796，不是 UCD_TOT_00796.dbf）。
            # zip裡只有這一個檔案時，直接當作dbf資料檔處理。
            name = all_names[0]
            zf.extract(name, out_dir)
            extracted_path = os.path.join(out_dir, name)
            renamed_path = extracted_path + ".dbf"
            os.replace(extracted_path, renamed_path)
            dbf_paths.append(renamed_path)
            print(f"[解壓縮] {name}（原始檔案沒有副檔名，已另存為 {os.path.basename(renamed_path)}）")

    if not dbf_paths:
        print("[警告] 這個zip裡面沒有找到.dbf檔，請確認zip內容")
        print(f"這個zip裡實際包含的檔案清單：{all_names}")
    return dbf_paths


# ---------------------------------------------------------------------------
# 第三步：純Python解析 DBF 檔案（dBase III/IV格式，最常見版本）
#
# DBF 檔案結構（標準dBase格式）：
#   - 前32 bytes：檔頭（記錄數、資料起始位置等）
#   - 之後每32 bytes一組：欄位描述（欄名、型別、長度），直到遇到 0x0D 結束
#   - 資料起始位置之後：一筆一筆的紀錄，每筆記錄第一個byte是刪除標記
#     (0x20=正常，0x2A=已刪除)，之後照欄位長度依序排列資料
# ---------------------------------------------------------------------------

def read_dbf(path, encoding=ENCODING):
    """
    回傳 (fieldnames, rows)
    fieldnames: list of str，欄位名稱（來自dbf檔頭本身，非外部文件）
    rows: list of dict
    """
    with open(path, "rb") as f:
        header = f.read(32)
        if len(header) < 32:
            raise ValueError("檔案太短，不是有效的dbf檔")

        version_byte = header[0]
        num_records = struct.unpack("<I", header[4:8])[0]
        header_len = struct.unpack("<H", header[8:10])[0]
        record_len = struct.unpack("<H", header[10:12])[0]

        print(f"[dbf檔頭資訊] 版本byte=0x{version_byte:02x}  "
              f"筆數={num_records}  header_len={header_len}  record_len={record_len}")

        # 讀取欄位描述區：從第32 byte開始，每個描述32 bytes，
        # 直到遇到結束符 0x0D，或讀到header_len指定的位置為止（以先到者為準，
        # 避免因為某些dbf變體沒有標準終止符而一直讀到檔案結尾當機）
        fields = []
        f.seek(32)
        while f.tell() < header_len - 1:
            desc = f.read(32)
            if not desc or len(desc) < 32 or desc[0:1] == b"\x0d":
                break
            name_raw = desc[0:11].split(b"\x00")[0]
            name = name_raw.decode(encoding, errors="replace").strip()
            field_type = desc[11:12].decode("ascii", errors="replace")
            length = desc[16]
            fields.append({"name": name, "type": field_type, "length": length})

        print(f"[dbf欄位解析] 共解析出{len(fields)}個欄位："
              f"{[fld['name'] for fld in fields]}")

        if not fields:
            raise ValueError(
                "沒有解析出任何欄位，這個dbf檔的結構可能跟標準dBase III格式不一樣。"
                "請把上面印出的[dbf檔頭資訊]那行數字告訴我，我再調整解析邏輯。"
            )

        # 資料區從 header_len 開始
        f.seek(header_len)
        rows = []
        for _ in range(num_records):
            record = f.read(record_len)
            if not record or len(record) < record_len:
                break
            if record[0:1] == b"\x2a":  # 已刪除的紀錄，跳過
                continue
            row = {}
            pos = 1  # 第0個byte是刪除標記，資料從第1個byte開始
            for field in fields:
                raw = record[pos:pos + field["length"]]
                value = raw.decode(encoding, errors="replace").strip()
                row[field["name"]] = value
                pos += field["length"]
            rows.append(row)

    fieldnames = [fld["name"] for fld in fields]
    return fieldnames, rows


# ---------------------------------------------------------------------------
# 第四步：輸出成 Excel 可直接開啟的 CSV
# ---------------------------------------------------------------------------

def write_csv(fieldnames, rows, out_path):
    with io.open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[完成] 已輸出 {len(rows)} 筆資料到 {out_path}（欄位為dbf原始名稱，非中文）")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="下載並解析法國UCD醫院藥價dbf檔")
    parser.add_argument(
        "--version", type=int, required=True,
        help="目前的UCD版本號（去 codage.ext.cnamts.fr 網站左側 BdM_IT 選單看 Version 那一行）"
    )
    args = parser.parse_args()

    zip_path = download_zip(args.version)
    dbf_paths = extract_dbf_files(zip_path)

    for dbf_path in dbf_paths:
        print(f"\n[解析中] {dbf_path}")
        fieldnames, rows = read_dbf(dbf_path)
        print(f"欄位名稱（原始，來自dbf檔頭）：{fieldnames}")
        print(f"筆數：{len(rows)}")
        out_csv = os.path.splitext(dbf_path)[0] + ".csv"
        write_csv(fieldnames, rows, out_csv)


if __name__ == "__main__":
    main()

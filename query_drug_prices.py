#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
國際藥價查詢引擎 - 多國藥價統一查詢工具

用途：
  1. 執行各國下載腳本，取得最新藥價資料
  2. 統一搜尋指定藥品在各國的價格
  3. 生成整合報告

查詢藥品：
  - Eliquis Film-Coated Tablet 2.5mg
  - Eliquis Film-Coated Tablet 5mg
  - Zelboraf film-coated tablets 240mg

全程使用 Python 標準函式庫，無第三方依賴。
"""

import os
import sys
import glob
import csv
import io
import subprocess
from pathlib import Path
from datetime import datetime

# 藥品名稱（支援模糊查詢）
TARGET_DRUGS = [
    "Eliquis Film-Coated Tablet 2.5mg",
    "Eliquis Film-Coated Tablet 5mg",
    "Zelboraf film-coated tablets 240mg",
]

# 預期各國下載後的CSV檔案
EXPECTED_OUTPUT_FILES = {
    "日本 (Japan MHLW)": ["tp20260715-01_01_中文欄名.csv"],
    "瑞典 (Sweden TLV)": ["tlv_medprice_中文欄名.csv"],
    "澳洲 (Australia PBS)": ["*_中文欄名.csv"],  # PBS的檔案名稍微不同
    "比利時 (Belgium INAMI)": ["liste_specialites_*_中文欄名.csv"],
    "瑞士 (Switzerland BAG)": ["Publications_*_中文欄名.csv"],
    "英國 (UK dm+d)": ["vmpp_中文欄名.csv"],
    "法國CIP (France CIP)": ["merged_output.csv"],
    "法國UCD (France UCD)": ["UCD_TOT_*.csv"],
}

SCRIPTS_DIR = "scripts"
DATA_DIR = "drug_price_data"


def ensure_data_dir():
    """確保資料目錄存在"""
    Path(DATA_DIR).mkdir(exist_ok=True)


def run_downloader(script_name, args=None):
    """執行指定國家的下載腳本"""
    script_path = os.path.join(SCRIPTS_DIR, script_name)

    if not os.path.exists(script_path):
        print(f"  [跳過] 找不到 {script_path}")
        return False

    print(f"  [執行] {script_name}...")
    try:
        cmd = ["python3", script_path]
        if args:
            cmd.extend(args)
        result = subprocess.run(cmd, cwd=DATA_DIR, capture_output=True, timeout=300, text=True)

        if result.returncode == 0:
            print(f"  [成功] {script_name}")
            return True
        else:
            print(f"  [失敗] {script_name}")
            if result.stderr:
                print(f"    錯誤：{result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  [逾時] {script_name} 執行超過5分鐘")
        return False
    except Exception as e:
        print(f"  [異常] {script_name}: {e}")
        return False


def download_all_prices():
    """下載所有國家的藥價資料"""
    print("\n=== 開始下載各國藥價資料 ===\n")
    ensure_data_dir()

    # 日本
    print("[日本] MHLW 藥價基準...")
    run_downloader("download_japan_mhlw.py", ["--only", "naiyo"])

    # 瑞典
    print("\n[瑞典] TLV 藥價...")
    run_downloader("convert_sweden_tlv.py")

    # 澳洲
    print("\n[澳洲] PBS 藥價...")
    run_downloader("download_australia_pbs.py")

    # 比利時
    print("\n[比利時] INAMI 藥價...")
    run_downloader("download_belgium_inami.py")

    # 瑞士
    print("\n[瑞士] BAG 藥價...")
    run_downloader("download_switzerland_bag.py")

    # 英國（需要API金鑰，先跳過）
    print("\n[英國] dm+d 藥價...")
    print("  [提示] 需要TRUD API金鑰，若有金鑰請執行：")
    print("    python scripts/download_uk_dmd.py --api-key YOUR_KEY")

    # 法國CIP
    print("\n[法國] CIP 藥價（藥局）...")
    run_downloader("merge_cip_files.py")

    # 法國UCD（需要版本號，先跳過）
    print("\n[法國] UCD 藥價（醫院）...")
    print("  [提示] 需要版本號，若已知版本號請執行：")
    print("    python scripts/download_ucd_files.py --version XXX")

    print("\n=== 下載完成 ===\n")


def search_drug_in_csv(csv_path, drug_names):
    """在CSV檔案中搜尋藥品"""
    results = []
    try:
        with io.open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return results

            for row in reader:
                # 將整列轉成字串進行模糊搜尋
                row_text = " ".join(str(v).lower() for v in row.values())

                for drug_name in drug_names:
                    # 使用模糊匹配，例如搜尋 "eliquis" 會配對 "Eliquis Film-Coated"
                    if drug_name.lower() in row_text or _fuzzy_match(drug_name.lower(), row_text):
                        results.append(row)
                        break
    except Exception as e:
        pass

    return results


def _fuzzy_match(search_term, text):
    """簡單的模糊匹配：檢查搜尋詞的關鍵部分是否都在文本中"""
    # 把 "Eliquis Film-Coated Tablet 2.5mg" 拆成關鍵詞
    keywords = search_term.split()
    # 需要至少有主要關鍵詞（例如 "eliquis"）
    if not keywords:
        return False
    main_keyword = keywords[0]
    if main_keyword not in text:
        return False
    # 檢查其他關鍵詞中至少有一個也在文本中
    return any(kw in text for kw in keywords[1:])


def find_output_files():
    """掃描資料目錄，找出所有生成的CSV檔案"""
    found_files = {}
    for country, patterns in EXPECTED_OUTPUT_FILES.items():
        for pattern in patterns:
            full_pattern = os.path.join(DATA_DIR, pattern)
            matches = glob.glob(full_pattern)
            if matches:
                found_files[country] = matches
                break
    return found_files


def query_all_prices():
    """查詢所有國家的藥品價格"""
    print("\n=== 開始查詢藥品價格 ===\n")

    found_files = find_output_files()

    if not found_files:
        print("[提示] 未找到任何CSV檔案，請先執行下載步驟")
        print("       run_downloader() 或直接執行各國腳本")
        return {}

    all_results = {}

    for country, csv_paths in found_files.items():
        print(f"\n[{country}]")
        country_results = {drug: [] for drug in TARGET_DRUGS}

        for csv_path in csv_paths:
            print(f"  搜尋 {os.path.basename(csv_path)}...")
            matches = search_drug_in_csv(csv_path, TARGET_DRUGS)

            if matches:
                print(f"    找到 {len(matches)} 筆")
                for match in matches:
                    # 判定這筆符合哪個藥品
                    for drug in TARGET_DRUGS:
                        if drug.lower() in " ".join(str(v).lower() for v in match.values()):
                            country_results[drug].append({
                                "file": os.path.basename(csv_path),
                                "data": match
                            })
                            break
            else:
                print(f"    未找到相符藥品")

        all_results[country] = country_results

    return all_results


def print_summary(all_results):
    """印出查詢結果摘要"""
    print("\n" + "="*80)
    print("查詢結果摘要")
    print("="*80 + "\n")

    for country, results in all_results.items():
        print(f"【{country}】")
        found_any = False
        for drug, matches in results.items():
            if matches:
                found_any = True
                print(f"\n  ✓ {drug}")
                for match_info in matches:
                    print(f"    檔案：{match_info['file']}")
                    # 打印前5個欄位
                    for key, value in list(match_info['data'].items())[:5]:
                        print(f"      {key}: {value}")
                    if len(match_info['data']) > 5:
                        print(f"      ... 共 {len(match_info['data'])} 個欄位")

        if not found_any:
            print("  ✗ 未找到查詢的藥品")
        print()


def generate_report(all_results):
    """生成完整的查詢報告"""
    report_path = "drug_query_report.txt"
    with io.open(report_path, "w", encoding="utf-8-sig") as f:
        f.write("國際藥價查詢報告\n")
        f.write(f"生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n查詢藥品：\n")
        for drug in TARGET_DRUGS:
            f.write(f"  - {drug}\n")
        f.write("\n" + "="*80 + "\n\n")

        for country, results in all_results.items():
            f.write(f"\n【{country}】\n")
            for drug, matches in results.items():
                if matches:
                    f.write(f"\n  ✓ {drug}\n")
                    for i, match_info in enumerate(matches, 1):
                        f.write(f"\n    [記錄 {i}] 來源：{match_info['file']}\n")
                        for key, value in match_info['data'].items():
                            f.write(f"      {key}: {value}\n")
                else:
                    f.write(f"\n  ✗ {drug}：未找到\n")
            f.write("\n")

    print(f"[報告] 完整結果已儲存至 {report_path}")
    return report_path


def main():
    """主流程"""
    if len(sys.argv) > 1 and sys.argv[1] == "--download":
        # 執行下載
        download_all_prices()
        print("\n[提示] 資料已下載到 drug_price_data/ 目錄")
    else:
        # 只進行查詢
        print("[提示] 使用 --download 參數以執行下載，例如：")
        print("       python query_drug_prices.py --download")
        print("\n現在進行查詢（基於已有的資料）...\n")

    # 查詢
    all_results = query_all_prices()

    # 印出摘要
    if all_results:
        print_summary(all_results)
        # 生成報告
        generate_report(all_results)
    else:
        print("\n[提示] 目前沒有查詢結果。請先執行下載：")
        print("       python query_drug_prices.py --download")


if __name__ == "__main__":
    main()

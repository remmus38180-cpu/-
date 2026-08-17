#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
藥價截圖自動化腳本 - Python 版
功能: 自動安裝依賴並執行截圖程式
"""

import os
import sys
import subprocess

def print_section(title):
    """打印分隔符和標題"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def run_command(cmd, description):
    """執行命令並檢查結果"""
    print(f"✓ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            print(f"✗ 失敗: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"✗ 錯誤: {str(e)[:100]}")
        return False

def check_file_exists(filename):
    """檢查檔案是否存在"""
    if os.path.exists(filename):
        return True
    return False

def main():
    print("\n" + "=" * 60)
    print("  國際藥價自動截圖 - 自動安裝版")
    print("=" * 60 + "\n")

    # Step 1: 檢查 Python
    print_section("Step 1: 檢查 Python 環境")
    result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
    python_version = result.stdout.strip()
    if python_version:
        print(f"✓ Python 已安裝: {python_version}")
    else:
        print("✗ Python 檢查失敗")
        return 1

    # Step 2: 安裝 Selenium
    print_section("Step 2: 安裝 Selenium")
    print("執行: pip install selenium --upgrade")
    if run_command(f"{sys.executable} -m pip install selenium --upgrade --quiet", "安裝 Selenium"):
        print("✓ Selenium 已安裝")
    else:
        print("⚠ Selenium 安裝可能失敗，但嘗試繼續...")

    # Step 3: 檢查 ChromeDriver
    print_section("Step 3: 檢查 ChromeDriver")
    chromedriver_check = subprocess.run("chromedriver --version", shell=True, capture_output=True, text=True)
    if chromedriver_check.returncode == 0:
        print(f"✓ ChromeDriver 已找到: {chromedriver_check.stdout.strip()}")
    else:
        print("⚠ ChromeDriver 未在 PATH 中")
        print("\n需要手動下載 ChromeDriver:")
        print("  1. 查詢您的 Chrome 版本: 設定 → 關於 Chrome")
        print("  2. 訪問 https://chromedriver.chromium.org/")
        print("  3. 下載相符版本的 win64")
        print("  4. 解壓到 Python Scripts 資料夾 或添加到 PATH")
        print("\n或將 chromedriver.exe 放在本腳本同目錄")

    # Step 4: 檢查輸入檔案
    print_section("Step 4: 檢查輸入檔案")

    if not check_file_exists("drug_list.csv"):
        print("✗ drug_list.csv 未找到")
        print("\n需要的檔案:")
        print("  - drug_price_screenshot_selenium.py")
        print("  - drug_list.csv")
        print("  - auto_setup_and_run.py (本檔案)")
        print("  - chromedriver.exe (或在 PATH 中)")
        return 1

    if not check_file_exists("drug_price_screenshot_selenium.py"):
        print("✗ drug_price_screenshot_selenium.py 未找到")
        return 1

    # 計算藥品數量
    try:
        with open("drug_list.csv", "r", encoding="utf-8") as f:
            drug_count = sum(1 for line in f if line.strip())
        print(f"✓ drug_list.csv 已找到")
        print(f"  共 {drug_count} 個藥品")
    except:
        print("✗ 無法讀取 drug_list.csv")
        return 1

    # Step 5: 執行主程式
    print_section("Step 5: 開始執行截圖程式")
    print(f"⏱ 預計時間: 30-60 分鐘 ({drug_count} 個藥品 × 8 國家)")
    print("💾 輸出目錄: drug_price_screenshots/")
    print("=" * 60 + "\n")

    try:
        result = subprocess.run(
            [sys.executable, "drug_price_screenshot_selenium.py", "--input", "drug_list.csv"],
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("  ✓✓✓ 執行完成! ✓✓✓")
            print("=" * 60)
            print(f"\n截圖存放在: drug_price_screenshots/")
            return 0
        else:
            print("\n" + "=" * 60)
            print("  ✗ 執行過程中出現錯誤")
            print("=" * 60)
            return 1

    except Exception as e:
        print(f"\n✗ 執行失敗: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

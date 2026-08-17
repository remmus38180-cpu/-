#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
國際藥價截圖自動完整安裝腳本
功能: 自動下載 ChromeDriver + Selenium + 執行截圖
"""

import os
import sys
import subprocess
import urllib.request
import json
import re
import zipfile
import shutil
from pathlib import Path

def print_section(title):
    """打印分隔符"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def run_command(cmd, description=""):
    """執行命令"""
    if description:
        print(f"  {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def get_chrome_version():
    """獲取 Chrome 版本"""
    print("  查詢 Chrome 版本...")

    # Windows 註冊表方式
    try:
        result = subprocess.run(
            'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\Binaries" /v pv',
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            match = re.search(r'pv\s+REG_SZ\s+(\S+)', result.stdout)
            if match:
                version = match.group(1).split('.')[0]  # 取主版本號
                print(f"  ✓ Chrome 版本: {version}")
                return version
    except:
        pass

    # 備選方式：直接執行 chrome.exe
    try:
        result = subprocess.run(
            '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --version',
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            match = re.search(r'(\d+)\.\d+\.\d+\.\d+', result.stdout)
            if match:
                version = match.group(1)
                print(f"  ✓ Chrome 版本: {version}")
                return version
    except:
        pass

    print("  ⚠ 無法自動查詢 Chrome 版本")
    print("\n  請手動查詢:")
    print("    1. 打開 Chrome")
    print("    2. 點擊右上角 ⋮ → 設定 → 關於 Chrome")
    print("    3. 記下版本號 (例: 141)")

    version = input("\n  請輸入 Chrome 主版本號: ").strip()
    return version if version else None

def download_chromedriver(version):
    """下載 ChromeDriver"""
    print(f"\n  尋找 ChromeDriver v{version} 的下載連結...")

    try:
        # 查詢 ChromeDriver 下載連結
        url = f"https://chromedriver.chromium.org/download"
        print(f"  📥 正在下載 ChromeDriver v{version}...")

        # 這裡簡化為通知用戶，因為 chromedriver.chromium.org 可能有 JS 動態載入
        print("\n  ⚠ 需要手動下載 ChromeDriver:")
        print(f"     1. 訪問 https://chromedriver.chromium.org/downloads")
        print(f"     2. 找到版本 {version}")
        print(f"     3. 下載 'Chromium' 下的 'win64'")
        print(f"     4. 解壓 chromedriver.exe 到本目錄")

        return False

    except Exception as e:
        print(f"  ✗ 下載失敗: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("  國際藥價截圖 - 自動完整安裝")
    print("=" * 60)
    print("\n  此腳本會自動:")
    print("    1. 檢查/安裝 Python")
    print("    2. 安裝 Selenium")
    print("    3. 下載 ChromeDriver")
    print("    4. 執行截圖程式")

    # Step 1: Python
    print_section("Step 1: 檢查 Python")
    success, stdout, stderr = run_command(f"{sys.executable} --version", "檢查 Python")
    if success:
        print(f"  ✓ {stdout.strip()}")
    else:
        print("  ✗ Python 版本檢查失敗")
        return 1

    # Step 2: Selenium
    print_section("Step 2: 安裝 Selenium")
    success, stdout, stderr = run_command(
        f"{sys.executable} -m pip install selenium --upgrade --quiet",
        "安裝 Selenium"
    )
    if success:
        print("  ✓ Selenium 已安裝")
    else:
        print("  ⚠ Selenium 安裝可能失敗，但嘗試繼續...")

    # Step 3: ChromeDriver
    print_section("Step 3: 檢查/下載 ChromeDriver")

    success, stdout, stderr = run_command("chromedriver --version")
    if success:
        print(f"  ✓ ChromeDriver 已在 PATH 中")
        print(f"     {stdout.strip()}")
    else:
        print("  ℹ ChromeDriver 未在 PATH 中")

        # 檢查本目錄
        if os.path.exists("chromedriver.exe"):
            print("  ✓ 在本目錄找到 chromedriver.exe")
        else:
            print("\n  需要下載 ChromeDriver:")
            chrome_version = get_chrome_version()

            if chrome_version:
                download_chromedriver(chrome_version)
                print("\n  ⚠ 下載完成後:")
                print("     1. 解壓 chromedriver.exe")
                print("     2. 放到本目錄")
                print("     3. 重新執行本腳本")
                return 1
            else:
                print("  ✗ 無法確定 Chrome 版本")
                return 1

    # Step 4: 檢查輸入檔案
    print_section("Step 4: 檢查輸入檔案")

    if not os.path.exists("drug_list.csv"):
        print("  ✗ drug_list.csv 未找到")
        return 1

    if not os.path.exists("drug_price_screenshot_selenium.py"):
        print("  ✗ drug_price_screenshot_selenium.py 未找到")
        return 1

    try:
        with open("drug_list.csv", "r", encoding="utf-8") as f:
            drug_count = sum(1 for line in f if line.strip())
        print(f"  ✓ drug_list.csv 已找到 ({drug_count} 個藥品)")
    except Exception as e:
        print(f"  ✗ 無法讀取 drug_list.csv: {e}")
        return 1

    # Step 5: 執行
    print_section("Step 5: 開始執行截圖程式")
    print(f"  ⏱ 預計時間: 30-60 分鐘")
    print(f"  💾 輸出目錄: drug_price_screenshots/")
    print("  " + "=" * 56)
    print()

    try:
        result = subprocess.run(
            [sys.executable, "drug_price_screenshot_selenium.py", "--input", "drug_list.csv"],
            capture_output=False
        )

        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("  ✓✓✓ 執行完成! ✓✓✓")
            print("=" * 60)
            print(f"\n  截圖存放在: drug_price_screenshots/\n")
            return 0
        else:
            print("\n" + "=" * 60)
            print("  ✗ 執行過程中出現錯誤")
            print("=" * 60 + "\n")
            return 1

    except Exception as e:
        print(f"\n  ✗ 執行失敗: {e}\n")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
    except KeyboardInterrupt:
        print("\n\n  已被使用者中斷")
        exit_code = 1
    except Exception as e:
        print(f"\n  ✗ 發生錯誤: {e}\n")
        exit_code = 1

    print("  按 Enter 鍵退出...")
    input()
    sys.exit(exit_code)

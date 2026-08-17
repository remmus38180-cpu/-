#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動解壓 Python 並執行自動下載腳本
"""

import os
import sys
import zipfile
import subprocess

def print_section(title):
    """打印分隔符"""
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print()

def main():
    print_section("自動解壓 + 執行")

    # 設定檔案和目錄
    python_zip = "python-3.12.0-embed-amd64.zip"
    python_dir = "python_portable"
    auto_script = "auto_download_and_install.py"
    python_exe = os.path.join(python_dir, "python.exe")

    # Step 1: 檢查 ZIP 檔案
    print("[步驟 1/4] 檢查 ZIP 檔案")
    print()

    if not os.path.exists(python_zip):
        print(f"[ERROR] ZIP 檔案未找到！")
        print()
        print(f"需要的檔案: {python_zip}")
        print()
        print("解決方案:")
        print("1. 下載: python-3.12.0-embed-amd64.zip")
        print("2. 放在此目錄")
        print("3. 重新運行此腳本")
        print()
        return False

    print(f"[OK] ZIP 檔案已找到: {python_zip}")
    file_size = os.path.getsize(python_zip) / 1024 / 1024
    print(f"     檔案大小: {file_size:.2f} MB")
    print()

    # Step 2: 檢查是否已解壓
    print("[步驟 2/4] 檢查解壓")
    print()

    if os.path.exists(python_exe):
        print("[OK] Python 已解壓")
        print()
    else:
        print("[INFO] 開始解壓 Python...")
        print()

        try:
            print("  正在解壓檔案...")
            with zipfile.ZipFile(python_zip, 'r') as zip_ref:
                zip_ref.extractall(".")

            # 檢查是否解壓成功
            if not os.path.exists(python_exe):
                print()
                print("[ERROR] Python 解壓失敗")
                print()
                print("需要手動解壓:")
                print("1. 右鍵點擊 ZIP 檔案")
                print("2. 選擇「解壓縮到」")
                print("3. 選擇此目錄")
                print("4. 重新運行此腳本")
                print()
                return False

            print()
            print("[OK] Python 解壓完成")
            print()

        except Exception as e:
            print()
            print(f"[ERROR] 解壓失敗: {e}")
            print()
            print("需要手動解壓:")
            print("1. 右鍵點擊 ZIP 檔案")
            print("2. 選擇「解壓縮到」")
            print("3. 選擇此目錄")
            print("4. 重新運行此腳本")
            print()
            return False

    # Step 3: 檢查自動下載腳本
    print("[步驟 3/4] 檢查腳本")
    print()

    if not os.path.exists(auto_script):
        print(f"[ERROR] 腳本未找到: {auto_script}")
        print()
        print("需要的檔案:")
        print("1. auto_download_and_install.py")
        print("2. drug_price_screenshot_selenium.py")
        print("3. drug_list.csv")
        print()
        return False

    print(f"[OK] 腳本已找到: {auto_script}")
    print()

    # Step 4: 執行自動下載腳本
    print("[步驟 4/4] 執行腳本")
    print()
    print("=" * 60)
    print()

    try:
        result = subprocess.run(
            [python_exe, auto_script],
            check=False
        )

        print()
        print("=" * 60)

        if result.returncode == 0:
            print("[SUCCESS] 完成!")
            print("=" * 60)
            print()
            return True
        else:
            print("[ERROR] 執行失敗")
            print("=" * 60)
            print()
            return False

    except Exception as e:
        print()
        print("=" * 60)
        print(f"[ERROR] 執行失敗: {e}")
        print("=" * 60)
        print()
        return False

if __name__ == "__main__":
    try:
        success = main()
        print("按 Enter 鍵退出...")
        input()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n已被使用者中斷")
        sys.exit(1)

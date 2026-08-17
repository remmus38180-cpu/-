#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 3.12.0 自動下載腳本
用於已安裝 Python 的系統
"""

import urllib.request
import os
import sys

def download_python():
    """自動下載 Python 3.12.0"""

    python_url = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip"
    output_file = "python-3.12.0-embed-amd64.zip"

    print("=" * 60)
    print("  Python 3.12.0 自動下載腳本")
    print("=" * 60)
    print()
    print(f"  下載網址: {python_url}")
    print(f"  保存檔案: {output_file}")
    print()

    # 檢查檔案是否已存在
    if os.path.exists(output_file):
        print(f"  [警告] 檔案已存在: {output_file}")
        response = input("  是否重新下載? (y/n): ").strip().lower()
        if response != 'y':
            print("  已取消下載")
            return False

    print("  [開始] 正在下載...")
    print()

    try:
        def progress_hook(block_num, block_size, total_size):
            """下載進度顯示"""
            downloaded = block_num * block_size
            percent = min(downloaded * 100 // total_size, 100) if total_size > 0 else 0
            bar_length = 40
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)

            print(f"\r  [{bar}] {percent}% ({downloaded / 1024 / 1024:.1f} MB)", end='', flush=True)

        # 下載檔案
        urllib.request.urlretrieve(python_url, output_file, progress_hook)

        print()  # 換行
        print()
        print("=" * 60)
        print("  [成功] 下載完成！")
        print("=" * 60)
        print()

        # 顯示檔案信息
        file_size = os.path.getsize(output_file) / 1024 / 1024
        print(f"  檔案名稱: {output_file}")
        print(f"  檔案大小: {file_size:.2f} MB")
        print(f"  位置: {os.path.abspath(output_file)}")
        print()
        print("  接下來:")
        print("  1. 將此檔案複製到隔離平台")
        print("  2. 在隔離平台解壓")
        print("  3. 執行 auto_download_and_install.py")
        print()

        return True

    except Exception as e:
        print()
        print()
        print("=" * 60)
        print("  [錯誤] 下載失敗！")
        print("=" * 60)
        print()
        print(f"  錯誤訊息: {e}")
        print()
        print("  可能原因:")
        print("  1. 網絡連接失敗")
        print("  2. Python.org 網站無響應")
        print("  3. 防火牆阻止下載")
        print()
        print("  解決方案:")
        print("  1. 檢查網絡連接")
        print("  2. 在瀏覽器中手動下載:")
        print(f"     {python_url}")
        print("  3. 聯絡 IT 部門檢查防火牆設定")
        print()

        return False

if __name__ == "__main__":
    try:
        success = download_python()
        print("  按 Enter 鍵退出...")
        input()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n  已被使用者中斷")
        sys.exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
國際藥價截圖 - 完全自動下載安裝腳本
功能: 自動下載 Python、Chrome 和 ChromeDriver，然後執行截圖
"""

import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
from pathlib import Path
import json
import re

def print_section(title):
    """打印分隔符"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def print_step(step_num, description):
    """打印步驟"""
    print(f"\n[步驟 {step_num}] {description}")
    print("-" * 70)

def run_command(cmd, description="", shell=True):
    """執行命令"""
    if description:
        print(f"  ✓ {description}...")
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "命令超時"
    except Exception as e:
        return False, "", str(e)

def download_file(url, filename, description=""):
    """下載檔案"""
    if description:
        print(f"  📥 {description}...")
    try:
        def progress_hook(block, block_size, total_size):
            downloaded = block * block_size
            percent = min(downloaded * 100 // total_size, 100) if total_size > 0 else 0
            bar_length = 40
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r  [{bar}] {percent}%", end='', flush=True)

        urllib.request.urlretrieve(url, filename, progress_hook)
        print()  # 換行
        return True
    except Exception as e:
        print(f"\n  ✗ 下載失敗: {e}")
        return False

def check_python_installed():
    """檢查 Python 是否已安裝"""
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout.strip()
    except:
        pass
    return False, None

def download_python():
    """下載 Python 便攜版本"""
    print_step(2, "下載 Python")

    # 使用 Python 官方便攜版本
    python_version = "3.12.0"
    python_url = f"https://www.python.org/ftp/python/{python_version}/python-{python_version}-embed-amd64.zip"
    python_zip = "python_portable.zip"
    python_dir = "python_portable"

    print(f"  版本: Python {python_version}")
    print(f"  URL: {python_url}")

    if os.path.exists(python_dir):
        print(f"  ✓ Python 已存在於 {python_dir}/")
        return True, python_dir

    if not os.path.exists(python_zip):
        if not download_file(python_url, python_zip, f"正在下載 Python {python_version}"):
            print("  ⚠ 無法從官方下載，嘗試備用方案...")
            return False, None

    # 解壓
    print(f"  📦 解壓 {python_zip}...")
    try:
        with zipfile.ZipFile(python_zip, 'r') as zip_ref:
            zip_ref.extractall(python_dir)
        print(f"  ✓ 已解壓到 {python_dir}/")

        # 清理 ZIP 檔案
        os.remove(python_zip)
        return True, python_dir
    except Exception as e:
        print(f"  ✗ 解壓失敗: {e}")
        return False, None

def get_chrome_version_from_registry():
    """從 Windows 註冊表獲取 Chrome 版本"""
    try:
        result = subprocess.run(
            'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BinariesVersion" /v pv',
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            match = re.search(r'pv\s+REG_SZ\s+(\S+)', result.stdout)
            if match:
                return match.group(1).split('.')[0]
    except:
        pass

    # 嘗試直接執行 chrome.exe
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]

    for chrome_path in chrome_paths:
        try:
            result = subprocess.run(f'"{chrome_path}" --version', shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                match = re.search(r'(\d+)\.\d+\.\d+', result.stdout)
                if match:
                    return match.group(1)
        except:
            pass

    return None

def download_chrome():
    """下載 Chrome 便攜版本 (Chrome for Testing - 官方穩定版)"""
    print_step(3, "下載 Chrome")

    # 檢查是否已安裝
    chrome_version = get_chrome_version_from_registry()
    if chrome_version:
        print(f"  ✓ Chrome 已安裝 (版本: {chrome_version})")
        return True, chrome_version, None

    chrome_zip = "chrome_portable.zip"
    chrome_dir = "chrome_portable"
    chrome_exe = Path(chrome_dir) / "chrome-win64" / "chrome.exe"

    # 檢查便攜版本 Chrome 是否已解壓
    if chrome_exe.exists():
        print(f"  ✓ Chrome 便攜版本已存在")
        print(f"  ✓ Chrome 位置: {chrome_exe}")
        return True, "152", str(chrome_exe)

    print("  ℹ Chrome 未找到，嘗試下載便攜版本...")

    try:
        # 使用 Google 官方穩定版本 (152.0.7977.42)
        # 來源: https://googlechromelabs.github.io/chrome-for-testing/
        version = "152.0.7977.42"
        chrome_download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chrome-win64.zip"

        print(f"  版本: Chrome {version}")
        print(f"  📥 正在下載 Chrome for Testing...")

        # 下載 Chrome
        if not os.path.exists(chrome_zip):
            if not download_file(chrome_download_url, chrome_zip, ""):
                print("  ⚠ 無法下載 Chrome")
                return False, None, None

        # 解壓
        print(f"  📦 解壓 {chrome_zip}...")
        with zipfile.ZipFile(chrome_zip, 'r') as zip_ref:
            zip_ref.extractall(chrome_dir)
        print(f"  ✓ 已解壓到 {chrome_dir}/")

        # 清理 ZIP
        os.remove(chrome_zip)

        # 查找 chrome.exe
        chrome_exe = Path(chrome_dir) / "chrome-win64" / "chrome.exe"
        if chrome_exe.exists():
            print(f"  ✓ Chrome 位置: {chrome_exe}")
            major_version = version.split('.')[0]
            return True, major_version, str(chrome_exe)

        print(f"  ⚠ 找不到 chrome.exe 在 {chrome_dir}/")
        return False, None, None

    except Exception as e:
        print(f"  ⚠ 無法下載 Chrome: {e}")
        print("\n  🌐 手動下載 Chrome:")
        print("     官網: https://googlechromelabs.github.io/chrome-for-testing/")
        print("     找 Stable 版本的 win64 chrome-win64.zip")
        return False, None, None

def download_chromedriver(chrome_version):
    """下載 ChromeDriver"""
    print_step(4, "下載 ChromeDriver")

    if not chrome_version:
        print("  ⚠ Chrome 版本未知，無法下載 ChromeDriver")
        return False

    print(f"  版本: ChromeDriver {chrome_version}")

    chromedriver_exe = "chromedriver.exe"
    if os.path.exists(chromedriver_exe):
        print(f"  ✓ {chromedriver_exe} 已存在")
        return True

    try:
        # 使用 Google 官方下載
        chromedriver_url = f"https://googlechromelabs.github.io/chrome-for-testing/download-chrome-for-testing.json"

        print("  📥 正在查詢 ChromeDriver 下載連結...")
        response = urllib.request.urlopen(chromedriver_url, timeout=10)
        data = json.loads(response.read().decode())

        # 從 JSON 中查找對應版本的 ChromeDriver
        for release in data.get('releases', []):
            if release.get('version', '').startswith(chrome_version):
                for platform in release.get('downloads', {}).get('chromedriver', []):
                    if 'win64' in platform.get('platform', ''):
                        driver_url = platform.get('url')
                        if driver_url:
                            driver_zip = "chromedriver_temp.zip"
                            if not download_file(driver_url, driver_zip, f"正在下載 ChromeDriver {chrome_version}"):
                                continue

                            print(f"  📦 解壓 ChromeDriver...")
                            with zipfile.ZipFile(driver_zip, 'r') as zip_ref:
                                # 找到 chromedriver.exe 並提取
                                for file in zip_ref.namelist():
                                    if file.endswith('chromedriver.exe'):
                                        zip_ref.extract(file, '.')
                                        # 將檔案移到當前目錄
                                        extracted_path = file
                                        if os.path.exists(extracted_path):
                                            shutil.move(extracted_path, chromedriver_exe)

                            os.remove(driver_zip)
                            print(f"  ✓ ChromeDriver 已下載")
                            return True

        print("  ⚠ 無法從 Google 官方下載，嘗試備用來源...")

        # 備用: 從 chromedriver.chromium.org 下載
        backup_url = f"https://googlechromelabs.github.io/chrome-for-testing/known-good-versions.json"
        print(f"  嘗試備用連結...")

        return False

    except Exception as e:
        print(f"  ⚠ 下載 ChromeDriver 失敗: {e}")
        print("\n  🌐 請手動下載:")
        print(f"     1. 訪問 https://googlechromelabs.github.io/chrome-for-testing/")
        print(f"     2. 找到版本 {chrome_version}")
        print(f"     3. 下載 'win64'")
        print(f"     4. 解壓 chromedriver.exe 到本目錄")
        return False

def install_selenium(python_path=None):
    """安裝 Selenium"""
    print_step(5, "安裝 Selenium")

    if python_path:
        python_exe = os.path.join(python_path, "python.exe")
    else:
        python_exe = sys.executable

    # 第一步：安裝 pip（使用 get-pip.py）
    print("  📦 確保 pip 已安裝...")

    # 嘗試 ensurepip（對於標準 Python）
    cmd_ensure_pip = f'"{python_exe}" -m ensurepip --upgrade'
    success_pip, _, stderr_pip = run_command(cmd_ensure_pip, "")

    if not success_pip:
        # 如果 ensurepip 失敗，使用 get-pip.py
        print("  ℹ ensurepip 不可用，使用 get-pip.py...")

        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip_file = "get-pip.py"

        if not os.path.exists(get_pip_file):
            print("  📥 正在下載 get-pip.py...")
            if not download_file(get_pip_url, get_pip_file, ""):
                print("  ✗ 無法下載 get-pip.py")
                return False

        # 執行 get-pip.py
        print("  ⚙️ 正在安裝 pip...")
        cmd_get_pip = f'"{python_exe}" "{get_pip_file}"'
        success_pip, _, stderr_get_pip = run_command(cmd_get_pip, "")

        if not success_pip:
            print(f"  ✗ pip 安裝失敗: {stderr_get_pip[:100]}")
            return False

        # 清理 get-pip.py
        try:
            os.remove(get_pip_file)
        except:
            pass

        print("  ✓ pip 已安裝")
    else:
        print("  ✓ pip 已安裝")

    # 第二步：安裝 Selenium 和 webdriver-manager
    print("  📥 正在安裝 Selenium...")
    cmd = f'"{python_exe}" -m pip install selenium webdriver-manager --upgrade --quiet'
    success, stdout, stderr = run_command(cmd, "")

    if success:
        print("  ✓ Selenium 已安裝")
        print("  ✓ webdriver-manager 已安裝")
        return True
    else:
        print(f"  ✗ Selenium 安裝失敗: {stderr[:100]}")
        return False

def check_input_files():
    """檢查輸入檔案"""
    print_step(6, "檢查輸入檔案")

    required_files = {
        "drug_list.csv": "藥品清單",
        "drug_price_screenshot_selenium.py": "主程式"
    }

    for filename, description in required_files.items():
        if os.path.exists(filename):
            print(f"  ✓ {filename} ({description})")
        else:
            print(f"  ✗ {filename} ({description}) 未找到")
            return False

    # 計算藥品數量
    try:
        with open("drug_list.csv", "r", encoding="utf-8") as f:
            drug_count = sum(1 for line in f if line.strip())
        print(f"  ✓ 共 {drug_count} 個藥品")
        return True, drug_count
    except Exception as e:
        print(f"  ✗ 無法讀取 drug_list.csv: {e}")
        return False, 0

def run_main_program(python_path=None, chrome_path=None, drug_count=10):
    """執行主程式"""
    print_step(7, "執行截圖程式")

    if python_path:
        python_exe = os.path.join(python_path, "python.exe")
    else:
        python_exe = sys.executable

    print(f"  ⏱ 預計時間: 30-60 分鐘 ({drug_count} 個藥品 × 8 國家)")
    print(f"  💾 輸出目錄: drug_price_screenshots/")
    print("=" * 70 + "\n")

    cmd = f'"{python_exe}" drug_price_screenshot_selenium.py --input drug_list.csv'

    # 如果有 Chrome 路徑，添加到命令行
    if chrome_path and os.path.exists(chrome_path):
        cmd += f' --chrome-path "{chrome_path}"'
        print(f"  使用 Chrome: {chrome_path}\n")

    result = subprocess.run(cmd, shell=True)

    return result.returncode == 0

def main():
    print("\n" + "=" * 70)
    print("  國際藥價自動截圖 - 完全自動安裝版")
    print("=" * 70)
    print("\n  此腳本會自動:")
    print("    1. 下載 Python (如果未安裝)")
    print("    2. 下載 Chrome/Chromium (如果未安裝)")
    print("    3. 下載 ChromeDriver")
    print("    4. 安裝 Selenium")
    print("    5. 執行截圖程式")

    python_dir = None
    chrome_version = None
    chrome_exe_path = None

    # Step 1: 檢查或下載 Python
    print_step(1, "檢查 Python")
    installed, version = check_python_installed()
    if installed:
        print(f"  ✓ Python 已安裝: {version}")
    else:
        print("  ℹ Python 未找到，嘗試下載...")
        success, python_dir = download_python()
        if not success:
            print("\n  ✗ 無法自動下載 Python")
            print("\n  🌐 請手動下載:")
            print("     1. 訪問 https://www.python.org/downloads/")
            print("     2. 下載 'Windows Portable' 版本 (win64)")
            print("     3. 解壓到本目錄的 python_portable/")
            print("     4. 重新執行此腳本")
            return 1

    # Step 2-4: 下載 Chrome 和 ChromeDriver
    success, chrome_version, chrome_exe = download_chrome()
    if success:
        print(f"  ✓ Chrome 版本確定: {chrome_version}")
        if chrome_exe:
            chrome_exe_path = chrome_exe
    else:
        print("\n  ✗ 無法獲取 Chrome 版本")
        return 1

    # 下載 ChromeDriver
    if chrome_version:
        if not download_chromedriver(chrome_version):
            print("\n  ⚠ ChromeDriver 下載失敗，將嘗試用已有的版本")

    # Step 5: 安裝 Selenium
    if not install_selenium(python_dir):
        print("\n  ⚠ Selenium 安裝可能失敗，但嘗試繼續...")

    # Step 6: 檢查輸入檔案
    result = check_input_files()
    if isinstance(result, tuple):
        success, drug_count = result
    else:
        success = result
        drug_count = 10

    if not success:
        return 1

    # Step 7: 執行主程式
    if run_main_program(python_dir, chrome_exe_path, drug_count):
        print("\n" + "=" * 70)
        print("  ✓✓✓ 執行完成! ✓✓✓")
        print("=" * 70)
        print(f"\n  截圖存放在: drug_price_screenshots/")
        return 0
    else:
        print("\n" + "=" * 70)
        print("  ✗ 執行過程中出現錯誤")
        print("=" * 70 + "\n")
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

    print("\n  按 Enter 鍵退出...")
    input()
    sys.exit(exit_code)

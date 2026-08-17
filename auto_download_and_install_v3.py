#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
國際藥價截圖 - 完全自動化版本 (優先本地 wheel 檔案)
功能: 優先使用本地 wheel 檔案安裝 Selenium，下載 Chrome/ChromeDriver，執行截圖

優點：
- 優先檢測本地 wheel 檔案，不需要網路連接
- 自動檢測系統 Python 3.12.0
- 完全自動化流程
- 適合隔離網路環境
"""

import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
from pathlib import Path
import json
import glob

def print_section(title):
    """打印分隔符"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def print_step(step_num, description):
    """打印步驟"""
    print(f"\n[步驟 {step_num}] {description}")
    print("-" * 70)

def run_command(cmd, description="", shell=True, timeout=300):
    """執行命令"""
    if description:
        print(f"  ✓ {description}...")
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
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

def detect_system_python():
    """偵測系統 Python"""
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            python_exe = sys.executable
            return True, version, python_exe
    except:
        pass
    return False, None, None

def find_local_wheel_files():
    """查找本地 wheel 檔案"""
    selenium_whl = None
    webdriver_manager_whl = None

    # 查找 Selenium wheel
    selenium_files = glob.glob("selenium-*.whl")
    if selenium_files:
        selenium_whl = selenium_files[0]

    # 查找 webdriver-manager wheel
    webdriver_files = glob.glob("webdriver_manager-*.whl")
    if webdriver_files:
        webdriver_manager_whl = webdriver_files[0]

    return selenium_whl, webdriver_manager_whl

def install_selenium_local(python_exe, selenium_whl, webdriver_manager_whl):
    """使用本地 wheel 檔案安裝 Selenium"""
    print_step(3, "安裝 Selenium (使用本地 wheel 檔案)")

    print(f"  使用 Python: {python_exe}")

    # 先驗證 pip
    print("  📦 驗證 pip...")
    cmd_check_pip = f'"{python_exe}" -m pip --version'
    success_pip, stdout_pip, stderr_pip = run_command(cmd_check_pip, "", timeout=30)

    if not success_pip:
        print(f"  ✗ pip 不可用: {stderr_pip[:100]}")
        return False

    print(f"  ✓ {stdout_pip.strip()}")

    # 安裝 Selenium
    if selenium_whl and os.path.exists(selenium_whl):
        print(f"\n  📦 正在安裝 Selenium (本地 {selenium_whl})...")
        cmd = f'"{python_exe}" -m pip install "{selenium_whl}" --quiet'
        success, _, stderr = run_command(cmd, "", timeout=60)

        if success:
            print(f"  ✓ Selenium 已安裝")
        else:
            print(f"  ✗ Selenium 安裝失敗: {stderr[:100]}")
            return False
    else:
        print(f"  ⚠ 找不到 Selenium wheel 檔案")
        return False

    # 安裝 webdriver-manager
    if webdriver_manager_whl and os.path.exists(webdriver_manager_whl):
        print(f"\n  📦 正在安裝 webdriver-manager (本地 {webdriver_manager_whl})...")
        cmd = f'"{python_exe}" -m pip install "{webdriver_manager_whl}" --quiet'
        success, _, stderr = run_command(cmd, "", timeout=60)

        if success:
            print(f"  ✓ webdriver-manager 已安裝")
        else:
            print(f"  ✗ webdriver-manager 安裝失敗: {stderr[:100]}")
            return False
    else:
        print(f"  ⚠ 找不到 webdriver-manager wheel 檔案")
        print(f"     (但可能不是必需的)")

    return True

def install_selenium_online(python_exe):
    """從網路安裝 Selenium（備用方案）"""
    print_step(3, "安裝 Selenium (從網路下載)")

    print(f"  使用 Python: {python_exe}")

    # 先驗證 pip
    print("  📦 驗證 pip...")
    cmd_check_pip = f'"{python_exe}" -m pip --version'
    success_pip, stdout_pip, stderr_pip = run_command(cmd_check_pip, "", timeout=30)

    if not success_pip:
        print(f"  ✗ pip 不可用: {stderr_pip[:100]}")
        return False

    print(f"  ✓ {stdout_pip.strip()}")

    # 安裝 Selenium 和 webdriver-manager
    print("  📥 正在安裝 Selenium...")
    print("  ⏱ 這可能需要 5-10 分鐘，請耐心等待...")

    cmd = f'"{python_exe}" -m pip install selenium webdriver-manager --upgrade --quiet --default-timeout=120 --retries 5'
    success, stdout, stderr = run_command(cmd, "", timeout=600)

    if success:
        print("  ✓ Selenium 已安裝")
        print("  ✓ webdriver-manager 已安裝")
        return True
    else:
        print(f"  ⚠ Selenium 安裝失敗或超時")
        return False

def download_chrome():
    """下載 Chrome for Testing 便攜版本"""
    print_step(1, "下載 Chrome")

    chrome_zip = "chrome_portable.zip"
    chrome_dir = "chrome_portable"
    chrome_exe = Path(chrome_dir) / "chrome-win64" / "chrome.exe"

    # 檢查便攜版本 Chrome 是否已解壓
    if chrome_exe.exists():
        print(f"  ✓ Chrome 便攜版本已存在")
        print(f"  ✓ Chrome 路徑: {chrome_exe}")
        return True, "152", str(chrome_exe)

    print("  ℹ 準備下載 Chrome for Testing 便攜版本...")

    try:
        # 使用 Google 官方穩定版本
        version = "152.0.7977.42"
        chrome_download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chrome-win64.zip"

        print(f"  版本: Chrome {version}")

        # 下載 Chrome
        if not os.path.exists(chrome_zip):
            if not download_file(chrome_download_url, chrome_zip, f"正在下載 Chrome {version}"):
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
        return False, None, None

def download_chromedriver(chrome_version):
    """下載 ChromeDriver"""
    print_step(2, "下載 ChromeDriver")

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
                                for file in zip_ref.namelist():
                                    if file.endswith('chromedriver.exe'):
                                        zip_ref.extract(file, '.')
                                        extracted_path = file
                                        if os.path.exists(extracted_path):
                                            shutil.move(extracted_path, chromedriver_exe)

                            os.remove(driver_zip)
                            print(f"  ✓ ChromeDriver 已下載")
                            return True

        print("  ⚠ 無法從 Google 官方下載")
        return False

    except Exception as e:
        print(f"  ⚠ 下載 ChromeDriver 失敗: {e}")
        return False

def check_input_files():
    """檢查輸入檔案"""
    print_step(4, "檢查輸入檔案")

    required_files = {
        "drug_list.csv": "藥品清單",
        "drug_price_screenshot_selenium.py": "主程式"
    }

    for filename, description in required_files.items():
        if os.path.exists(filename):
            print(f"  ✓ {filename} ({description})")
        else:
            print(f"  ✗ {filename} ({description}) 未找到")
            return False, 0

    # 計算藥品數量
    try:
        with open("drug_list.csv", "r", encoding="utf-8") as f:
            drug_count = sum(1 for line in f if line.strip())
        print(f"  ✓ 共 {drug_count} 個藥品")
        return True, drug_count
    except Exception as e:
        print(f"  ✗ 無法讀取 drug_list.csv: {e}")
        return False, 0

def run_main_program(python_exe, chrome_path=None, drug_count=10):
    """執行主程式"""
    print_step(5, "執行截圖程式")

    print(f"  Python: {python_exe}")
    if chrome_path:
        print(f"  Chrome: {chrome_path}")

    print(f"  ⏱ 預計時間: 30-60 分鐘 ({drug_count} 個藥品 × 8 國家)")
    print(f"  💾 輸出目錄: drug_price_screenshots/")
    print("=" * 70 + "\n")

    cmd = f'"{python_exe}" drug_price_screenshot_selenium.py --input drug_list.csv'

    # 如果有 Chrome 路徑，添加到命令行
    if chrome_path and os.path.exists(chrome_path):
        cmd += f' --chrome-path "{chrome_path}"'

    result = subprocess.run(cmd, shell=True)

    return result.returncode == 0

def main():
    print("\n" + "=" * 70)
    print("  國際藥價自動截圖 - 完全自動版 (本地 wheel 優先)")
    print("=" * 70)
    print("\n  此腳本會自動:")
    print("    1. 檢測本地 wheel 檔案並安裝")
    print("    2. 下載 Chrome/Chromium (如果未下載)")
    print("    3. 下載 ChromeDriver (如果未下載)")
    print("    4. 執行截圖程式")

    # Step 0: 偵測系統 Python
    print_step(0, "偵測 Python")
    installed, version, python_exe = detect_system_python()
    if installed:
        print(f"  ✓ Python 已安裝: {version}")
        print(f"  ✓ 位置: {python_exe}")
    else:
        print("  ✗ Python 未找到")
        return 1

    # Step 0.5: 查找本地 wheel 檔案
    print("\n  📦 查找本地 wheel 檔案...")
    selenium_whl, webdriver_manager_whl = find_local_wheel_files()

    if selenium_whl:
        print(f"  ✓ 找到 Selenium: {selenium_whl}")
    else:
        print(f"  ⚠ 未找到 Selenium wheel")

    if webdriver_manager_whl:
        print(f"  ✓ 找到 webdriver-manager: {webdriver_manager_whl}")
    else:
        print(f"  ⚠ 未找到 webdriver-manager wheel")

    chrome_version = None
    chrome_exe_path = None

    # Step 1: 下載 Chrome
    success, chrome_version, chrome_exe = download_chrome()
    if success:
        print(f"  ✓ Chrome 版本確定: {chrome_version}")
        if chrome_exe:
            chrome_exe_path = chrome_exe
    else:
        print("\n  ✗ 無法獲取 Chrome 版本")
        return 1

    # Step 2: 下載 ChromeDriver
    if chrome_version:
        if not download_chromedriver(chrome_version):
            print("\n  ⚠ ChromeDriver 下載失敗，請手動下載")
            return 1

    # Step 3: 安裝 Selenium
    if selenium_whl and os.path.exists(selenium_whl):
        # 優先使用本地 wheel
        if not install_selenium_local(python_exe, selenium_whl, webdriver_manager_whl):
            print("\n  ✗ Selenium 安裝失敗")
            return 1
    else:
        # 備用：從網路下載
        print("\n  ℹ 未找到本地 wheel，將從網路下載...")
        if not install_selenium_online(python_exe):
            print("\n  ✗ Selenium 安裝失敗")
            return 1

    # Step 4: 檢查輸入檔案
    success, drug_count = check_input_files()
    if not success:
        return 1

    # Step 5: 執行主程式
    if run_main_program(python_exe, chrome_exe_path, drug_count):
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

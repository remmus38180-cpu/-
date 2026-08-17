@echo off
REM ============================================================
REM 藥價截圖自動化腳本 - Windows
REM 功能: 自動安裝 Python + Selenium + ChromeDriver，然後執行
REM 用法: 雙擊此檔案或在命令提示符中執行
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo 國際藥價自動截圖 - 自動安裝版
echo ============================================================
echo.

REM 檢查 Python 是否已安裝
echo [步驟 1/5] 檢查 Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python 已安裝
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
    echo   版本: !PYTHON_VER!
) else (
    echo ✗ Python 未安裝
    echo.
    echo 請手動安裝 Python 3.8+ :
    echo   1. 訪問 https://www.python.org/downloads/
    echo   2. 下載 Windows 64-bit installer
    echo   3. 安裝時勾選 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

REM 安裝 Selenium
echo.
echo [步驟 2/5] 安裝 Selenium...
python -m pip install selenium --quiet
if %errorlevel% equ 0 (
    echo ✓ Selenium 已安裝
) else (
    echo ✗ Selenium 安裝失敗
    pause
    exit /b 1
)

REM 檢查 ChromeDriver
echo.
echo [步驟 3/5] 檢查 ChromeDriver...
chromedriver --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ ChromeDriver 已在 PATH 中
) else (
    echo ⚠ ChromeDriver 未在 PATH 中
    echo.
    echo 需要手動下載:
    echo   1. 查詢您的 Chrome 版本: 設定 → 關於 Chrome
    echo   2. 訪問 https://chromedriver.chromium.org/
    echo   3. 下載相符版本的 win64
    echo   4. 解壓到 Python 目錄 Scripts 資料夾
    echo        或添加到 PATH
    echo.
    echo 或將 chromedriver.exe 放在本腳本同目錄
    echo.
    pause
    exit /b 1
)

REM 檢查藥品清單檔案
echo.
echo [步驟 4/5] 檢查輸入檔案...
if exist "drug_list.csv" (
    echo ✓ drug_list.csv 已找到
    for /f %%A in ('find /c /v "" ^< drug_list.csv') do set DRUG_COUNT=%%A
    echo   共 !DRUG_COUNT! 個藥品
) else (
    echo ✗ drug_list.csv 未找到
    echo.
    echo 請確認以下檔案在同一目錄:
    echo   - auto_setup_and_run.bat (本檔案)
    echo   - drug_price_screenshot_selenium.py
    echo   - drug_list.csv
    echo.
    pause
    exit /b 1
)

REM 執行主程式
echo.
echo [步驟 5/5] 開始執行截圖程式...
echo ============================================================
echo.
echo ⏱ 預計時間: 30-60 分鐘 (!DRUG_COUNT! 個藥品 × 8 國家)
echo 💾 輸出目錄: drug_price_screenshots\
echo.
echo ============================================================
echo.

python drug_price_screenshot_selenium.py --input drug_list.csv

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo ✓✓✓ 執行完成! ✓✓✓
    echo ============================================================
    echo.
    echo 截圖存放在: drug_price_screenshots\
    echo.
) else (
    echo.
    echo ============================================================
    echo ✗ 執行過程中出現錯誤
    echo ============================================================
    echo.
)

pause

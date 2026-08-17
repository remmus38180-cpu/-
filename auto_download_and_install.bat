@echo off
REM ============================================================
REM 國際藥價截圖 - 完全自動下載安裝版本
REM 功能: 自動下載 Python、Chrome 和 ChromeDriver，然後執行
REM ============================================================

setlocal enabledelayedexpansion

cls
echo.
echo ============================================================
echo 國際藥價自動截圖 - 完全自動下載安裝版本
echo ============================================================
echo.
echo 此腳本會自動:
echo   1. 下載 Python (如果未安裝)
echo   2. 下載 Chrome/Chromium (如果未安裝)
echo   3. 下載 ChromeDriver
echo   4. 安裝 Selenium
echo   5. 執行截圖程式
echo.
echo ============================================================
echo.

REM 檢查 Python 是否已安裝
echo [步驟 1/7] 檢查 Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python 已安裝
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
    echo   版本: !PYTHON_VER!
    set PYTHON_EXE=python
) else (
    echo ℹ Python 未找到，嘗試下載...
    echo.
    echo 執行 Python 自動下載腳本...
    python auto_download_and_install.py
    if %errorlevel% neq 0 (
        echo ✗ 自動下載失敗，請參考說明手動下載
        pause
        exit /b 1
    )
    set PYTHON_EXE=python_portable\python.exe
)

REM 安裝 Selenium
echo.
echo [步驟 2/7] 安裝 Selenium...
!PYTHON_EXE! -m pip install selenium --upgrade --quiet
if %errorlevel% equ 0 (
    echo ✓ Selenium 已安裝
) else (
    echo ⚠ Selenium 安裝可能失敗，但嘗試繼續...
)

REM 檢查 ChromeDriver
echo.
echo [步驟 3/7] 檢查 ChromeDriver...
if exist "chromedriver.exe" (
    echo ✓ chromedriver.exe 已找到
) else (
    echo ⚠ ChromeDriver 未找到
    echo   自動下載腳本應該已下載過，請檢查
)

REM 檢查輸入檔案
echo.
echo [步驟 4/7] 檢查輸入檔案...

if not exist "drug_list.csv" (
    echo ✗ drug_list.csv 未找到
    pause
    exit /b 1
)
echo ✓ drug_list.csv 已找到

if not exist "drug_price_screenshot_selenium.py" (
    echo ✗ drug_price_screenshot_selenium.py 未找到
    pause
    exit /b 1
)
echo ✓ drug_price_screenshot_selenium.py 已找到

REM 計算藥品數量
for /f %%A in ('find /c /v "" ^< drug_list.csv') do set DRUG_COUNT=%%A
echo ✓ 共 !DRUG_COUNT! 個藥品

REM 執行主程式
echo.
echo [步驟 5/7] 開始執行截圖程式...
echo ============================================================
echo.
echo ⏱ 預計時間: 30-60 分鐘 (!DRUG_COUNT! 個藥品 × 8 國家)
echo 💾 輸出目錄: drug_price_screenshots\
echo.
echo ============================================================
echo.

!PYTHON_EXE! drug_price_screenshot_selenium.py --input drug_list.csv

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

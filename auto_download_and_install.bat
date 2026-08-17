@echo off
REM ============================================================
REM Guo Ji Yao Jia Jie Tu - Wan Quan Zi Dong Xia Zai An Zhuang Ban Ben
REM 國際藥價截圖 - 完全自動下載安裝版本
REM ============================================================

setlocal enabledelayedexpansion

cls
echo.
echo ============================================================
echo Guo Ji Yao Jia Zi Dong Jie Tu - Wan Quan Zi Dong Xia Zai An Zhuang
echo 國際藥價自動截圖 - 完全自動下載安裝版本
echo ============================================================
echo.
echo CI Jiao Ben Hui Zi Dong:
echo 此腳本會自動:
echo   1. Xia Zai Python (Ru Guo Wei An Zhuang)
echo   2. Xia Zai Chrome/Chromium (Ru Guo Wei An Zhuang)
echo   3. Xia Zai ChromeDriver
echo   4. An Zhuang Selenium
echo   5. Zhi Xing Jie Tu Cheng Xu
echo.
echo ============================================================
echo.

REM Jian Cha Python Shi Fou Yi An Zhuang
echo [Bu Zhou 1/7] Jian Cha Python...
echo [步驟 1/7] 檢查 Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python Yi An Zhuang
    echo [OK] Python 已安裝
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
    echo   Ban Ben: !PYTHON_VER!
    echo   版本: !PYTHON_VER!
    set PYTHON_EXE=python
) else (
    echo [INFO] Python Wei Zhao Dao, Chang Shi Xia Zai...
    echo [INFO] Python 未找到，嘗試下載...
    echo.
    echo Zhi Xing Python Zi Dong Xia Zai Jiao Ben...
    echo 執行 Python 自動下載腳本...
    python auto_download_and_install.py
    if %errorlevel% neq 0 (
        echo [ERROR] Zi Dong Xia Zai Shi Bai, Qing Can Kao Shuo Ming Shou Dong Xia Zai
        echo [ERROR] 自動下載失敗，請參考說明手動下載
        pause
        exit /b 1
    )
    set PYTHON_EXE=python_portable\python.exe
)

REM An Zhuang Selenium
echo.
echo [Bu Zhou 2/7] An Zhuang Selenium...
echo [步驟 2/7] 安裝 Selenium...
!PYTHON_EXE! -m pip install selenium --upgrade --quiet
if %errorlevel% equ 0 (
    echo [OK] Selenium Yi An Zhuang
    echo [OK] Selenium 已安裝
) else (
    echo [WARNING] Selenium An Zhuang Ke Neng Shi Bai, Dan Chang Shi Ji Xu...
    echo [WARNING] Selenium 安裝可能失敗，但嘗試繼續...
)

REM Jian Cha ChromeDriver
echo.
echo [Bu Zhou 3/7] Jian Cha ChromeDriver...
echo [步驟 3/7] 檢查 ChromeDriver...
if exist "chromedriver.exe" (
    echo [OK] chromedriver.exe Yi Zhao Dao
    echo [OK] chromedriver.exe 已找到
) else (
    echo [WARNING] ChromeDriver Wei Zhao Dao
    echo [WARNING] ChromeDriver 未找到
    echo   Zi Dong Xia Zai Jiao Ben Ying Gai Yi Xia Zai Guo, Qing Jian Cha
    echo   自動下載腳本應該已下載過，請檢查
)

REM Jian Cha Shu Ru Wen Jian
echo.
echo [Bu Zhou 4/7] Jian Cha Shu Ru Wen Jian...
echo [步驟 4/7] 檢查輸入檔案...

if not exist "drug_list.csv" (
    echo [ERROR] drug_list.csv Wei Zhao Dao
    echo [ERROR] drug_list.csv 未找到
    pause
    exit /b 1
)
echo [OK] drug_list.csv Yi Zhao Dao
echo [OK] drug_list.csv 已找到

if not exist "drug_price_screenshot_selenium.py" (
    echo [ERROR] drug_price_screenshot_selenium.py Wei Zhao Dao
    echo [ERROR] drug_price_screenshot_selenium.py 未找到
    pause
    exit /b 1
)
echo [OK] drug_price_screenshot_selenium.py Yi Zhao Dao
echo [OK] drug_price_screenshot_selenium.py 已找到

REM Ji Suan Yao Pin Shu Liang
for /f %%A in ('find /c /v "" ^< drug_list.csv') do set DRUG_COUNT=%%A
echo [OK] Gong !DRUG_COUNT! Ge Yao Pin
echo [OK] 共 !DRUG_COUNT! 個藥品

REM Zhi Xing Zhu Cheng Xu
echo.
echo [Bu Zhou 5/7] Kai Shi Zhi Xing Jie Tu Cheng Xu...
echo [步驟 5/7] 開始執行截圖程式...
echo ============================================================
echo.
echo Yu Ji Shi Jian: 30-60 Fen Zhong (!DRUG_COUNT! Ge Yao Pin * 8 Guo Jia)
echo 預計時間: 30-60 分鐘 (!DRUG_COUNT! 個藥品 × 8 國家)
echo Shu Chu Mu Lu: drug_price_screenshots\
echo 輸出目錄: drug_price_screenshots\
echo.
echo ============================================================
echo.

!PYTHON_EXE! drug_price_screenshot_selenium.py --input drug_list.csv

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo [SUCCESS] Zhi Xing Wan Cheng!
    echo [SUCCESS] 執行完成!
    echo ============================================================
    echo.
    echo Jie Tu Cun Fang Zai: drug_price_screenshots\
    echo 截圖存放在: drug_price_screenshots\
    echo.
) else (
    echo.
    echo ============================================================
    echo [ERROR] Zhi Xing Guo Cheng Zhong Chu Xian Cuo Wu
    echo [ERROR] 執行過程中出現錯誤
    echo ============================================================
    echo.
)

pause

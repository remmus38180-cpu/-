@echo off
REM Zi Dong Jie Ya Python Bing Zhi Xing Auto_download Script
REM 自動解壓 Python 並執行自動下載腳本

setlocal enabledelayedexpansion

cls
echo.
echo ============================================================
echo Zi Dong Jie Ya + Zhi Xing
echo 自動解壓 + 執行
echo ============================================================
echo.

REM 設定檔案和目錄
set PYTHON_ZIP=python-3.12.0-embed-amd64.zip
set PYTHON_DIR=python_portable
set AUTO_SCRIPT=auto_download_and_install.py

REM Step 1: 檢查 ZIP 檔案
echo [Bu Zhou 1/4] Jian Cha ZIP Wen Jian
echo [步驟 1/4] 檢查 ZIP 檔案

if not exist "%PYTHON_ZIP%" (
    echo.
    echo [ERROR] ZIP Wen Jian Wei Zhao Dao!
    echo [ERROR] ZIP 檔案未找到！
    echo.
    echo Xu Yao De Wen Jian: %PYTHON_ZIP%
    echo 需要的檔案: %PYTHON_ZIP%
    echo.
    echo Jie Jue Ban Fa:
    echo 解決方案:
    echo 1. Xia Zai: python-3.12.0-embed-amd64.zip
    echo 2. Fang Zai Ci Mu Lu
    echo 3. Zhong Xin Yun Xing Ci Jiao Ben
    echo.
    pause
    exit /b 1
)

echo [OK] ZIP Wen Jian Yi Zhao Dao
echo [OK] ZIP 檔案已找到：%PYTHON_ZIP%
echo.

REM Step 2: 檢查是否已解壓
echo [Bu Zhou 2/4] Jian Cha Jie Ya
echo [步驟 2/4] 檢查解壓

if exist "%PYTHON_DIR%\python.exe" (
    echo [OK] Python Yi Jie Ya
    echo [OK] Python 已解壓
    echo.
) else (
    echo [INFO] Kai Shi Jie Ya Python...
    echo [INFO] 開始解壓 Python...
    echo.

    REM 解壓 ZIP 檔案（使用 Windows 內置 tar 命令）
    REM 如果沒有 tar，使用 PowerShell

    REM 方法 1: 嘗試使用 tar (Windows 10+)
    tar -xf "%PYTHON_ZIP%" -C . >nul 2>&1

    if !errorlevel! neq 0 (
        REM 方法 2: 使用 PowerShell
        echo Yong PowerShell Jie Ya...
        echo 用 PowerShell 解壓...

        powershell -NoProfile -Command "Expand-Archive -Path '%PYTHON_ZIP%' -DestinationPath '.' -Force" >nul 2>&1

        if !errorlevel! neq 0 (
            echo.
            echo [ERROR] Jie Ya Shi Bai
            echo [ERROR] 解壓失敗
            echo.
            echo Xu Yao Shou Dong Jie Ya:
            echo 需要手動解壓:
            echo 1. You Jian %PYTHON_ZIP%
            echo 2. Xuan Ze "Jie Ya Dao"
            echo 3. Xuan Ze Ci Mu Lu
            echo 4. Zhong Xin Yun Xing Ci Jiao Ben
            echo.
            pause
            exit /b 1
        )
    )

    REM 檢查解壓是否成功
    if not exist "%PYTHON_DIR%\python.exe" (
        echo.
        echo [ERROR] Python Jie Ya Shi Bai
        echo [ERROR] Python 解壓失敗
        echo.
        pause
        exit /b 1
    )

    echo [OK] Python Jie Ya Wan Cheng
    echo [OK] Python 解壓完成
    echo.
)

REM Step 3: 檢查自動下載腳本
echo [Bu Zhou 3/4] Jian Cha Jiao Ben
echo [步驟 3/4] 檢查腳本

if not exist "%AUTO_SCRIPT%" (
    echo [ERROR] Jiao Ben Wei Zhao Dao: %AUTO_SCRIPT%
    echo [ERROR] 腳本未找到: %AUTO_SCRIPT%
    pause
    exit /b 1
)

echo [OK] Jiao Ben Yi Zhao Dao
echo [OK] 腳本已找到
echo.

REM Step 4: 執行自動下載腳本
echo [Bu Zhou 4/4] Zhi Xing Jiao Ben
echo [步驟 4/4] 執行腳本
echo.
echo ============================================================
echo.

"%PYTHON_DIR%\python.exe" "%AUTO_SCRIPT%"

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo [SUCCESS] Wan Cheng!
    echo [SUCCESS] 完成!
    echo ============================================================
    echo.
) else (
    echo.
    echo ============================================================
    echo [ERROR] Zhi Xing Shi Bai
    echo [ERROR] 執行失敗
    echo ============================================================
    echo.
)

pause

@echo off
REM PowerShell 自動下載 Python
REM 無需任何外部工具，Windows 內置

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo Python 3.12.0 Zi Dong Xia Zai
echo Python 3.12.0 自動下載
echo ============================================================
echo.

REM 檢查 PowerShell 是否可用
powershell -Command "Write-Host '[OK] PowerShell Available'" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PowerShell Not Found
    echo [錯誤] PowerShell 未找到
    pause
    exit /b 1
)

REM 執行 PowerShell 腳本
echo.
echo [Executing PowerShell Script...]
echo [正在執行 PowerShell 腳本...]
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0download_python.ps1"

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Download Complete
    echo [成功] 下載完成
) else (
    echo.
    echo [ERROR] Download Failed
    echo [錯誤] 下載失敗
)

pause

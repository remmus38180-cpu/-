@echo off
REM ============================================================
REM One-Click Setup - Yi Jian Wan Cheng (一鍵完成)
REM Xia Zai + Jie Ya + Zhi Xing - All in One
REM ============================================================

setlocal enabledelayedexpansion

cls
echo.
echo ============================================================
echo Yi Jian Wan Quan Zi Dong Hua An Zhuang
echo 一鍵完全自動化安裝
echo ============================================================
echo.
echo Ci Jiao Ben Hui Zi Dong:
echo 此腳本會自動:
echo   1. Xia Zai Python 3.12.0
echo   2. Jie Ya Python
echo   3. Zhi Xing Zi Dong Xia Zai Jiao Ben
echo.

REM 檢查 PowerShell
echo Jian Cha PowerShell...
powershell -Command "Write-Host '[OK] PowerShell Available'" >nul 2>&1

if !errorlevel! neq 0 (
    echo [ERROR] PowerShell Bu Ke Yong
    echo [ERROR] PowerShell 不可用
    pause
    exit /b 1
)

REM 執行 PowerShell 腳本
echo.
echo Zhi Xing PowerShell Jiao Ben...
echo 執行 PowerShell 腳本...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0one_click_setup.ps1" -WorkDir "%CD%"

if !errorlevel! equ 0 (
    echo.
    echo [SUCCESS] Wan Cheng
    echo [SUCCESS] 完成
) else (
    echo.
    echo [ERROR] Shi Bai
    echo [ERROR] 失敗
)

pause

@echo off
REM ============================================================
REM One-Click Setup - Download Python, Extract, and Run Script
REM ============================================================

setlocal enabledelayedexpansion

cls
echo.
echo ============================================================
echo One-Click Setup
echo ============================================================
echo.
echo This script will automatically:
echo   1. Download Python 3.12.0
echo   2. Extract Python
echo   3. Run auto_download_and_install.py
echo.

REM Check if PowerShell is available
echo Checking PowerShell...
powershell -Command "Write-Host '[OK] PowerShell Available'" >nul 2>&1

if !errorlevel! neq 0 (
    echo [ERROR] PowerShell not available
    pause
    exit /b 1
)

REM Run PowerShell script
echo.
echo Running PowerShell script...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0one_click_setup.ps1" -WorkDir "%CD%"

if !errorlevel! equ 0 (
    echo.
    echo [SUCCESS] Complete!
) else (
    echo.
    echo [ERROR] Failed
)

pause

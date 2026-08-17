@echo off
REM Simple wrapper for auto-download script
REM No encoding issues - just run Python

setlocal enabledelayedexpansion

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found
    echo Please download Python 3.12+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Run the auto-download script
echo Starting auto-download and install script...
echo.
python auto_download_and_install.py

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS - Screenshot execution complete!
    echo Results saved to: drug_price_screenshots/
) else (
    echo.
    echo ERROR - Script failed
)

pause

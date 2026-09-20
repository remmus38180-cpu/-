@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   十國藥價自動化工具 - 環境檢測
echo ============================================================
echo.
echo   本程式只做檢查，不會下載藥價資料，也不會安裝任何軟體。
echo   預計耗時 1 至 3 分鐘。
echo.

set "PY="

REM 1. 先找同一台電腦上的 WinPython 免安裝版
for %%D in (
  "%~dp0..\python-3.13.13.amd64\python.exe"
  "C:\Users\%USERNAME%\Downloads\WPy64-313130\python-3.13.13.amd64\python.exe"
) do (
  if exist %%D set "PY=%%~D"
)

REM 2. 再找系統安裝的 Python
if not defined PY (
  where py >/dev/null 2>&1 && set "PY=py"
)
if not defined PY (
  where python >/dev/null 2>&1 && set "PY=python"
)

if not defined PY (
  echo [找不到 Python]
  echo.
  echo   請確認 WinPython 免安裝版的位置，或把本資料夾放到
  echo   WinPython 的 scripts 資料夾底下再執行一次。
  echo.
  pause
  exit /b 1
)

echo   使用的 Python：%PY%
echo.
"%PY%" "%~dp0tools\env_check.py"

echo.
echo   檢測結束。請把資料夾內的「環境檢測報告_日期時間.txt」回傳。
echo.
pause

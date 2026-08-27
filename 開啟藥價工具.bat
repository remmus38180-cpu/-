@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   十國藥價工具
echo ============================================================
echo.
echo   稍候會自動開啟瀏覽器。
echo   使用期間請不要關閉這個黑色視窗，用完再關。
echo.

set "PY="
for %%D in (
  "%~dp0..\python-3.13.13.amd64\python.exe"
  "C:\Users\%USERNAME%\Downloads\WPy64-313130\python-3.13.13.amd64\python.exe"
) do (
  if exist %%D set "PY=%%~D"
)
if not defined PY ( where py >/dev/null 2>&1 && set "PY=py" )
if not defined PY ( where python >/dev/null 2>&1 && set "PY=python" )

if not defined PY (
  echo [找不到 Python]
  echo.
  echo   請先執行「執行環境檢測.bat」，把產生的報告回傳給資訊窗口。
  echo.
  pause
  exit /b 1
)

"%PY%" -m drugprice.web

echo.
echo   工具已結束。
pause

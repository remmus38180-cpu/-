@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   十國藥價批次下載
echo ============================================================
echo.

set "PY="
for %%D in (
  "%~dp0..\python-3.13.13.amd64\python.exe"
  "C:\Users\%USERNAME%\Downloads\WPy64-313130\python-3.13.13.amd64\python.exe"
) do (
  if exist %%D set "PY=%%~D"
)
if not defined PY ( where py >nul 2>&1 && set "PY=py" )
if not defined PY ( where python >nul 2>&1 && set "PY=python" )

if not defined PY (
  echo [找不到 Python]
  echo   請先執行「執行環境檢測.bat」確認 Python 位置。
  echo.
  pause
  exit /b 1
)

echo   1. 下載全部國家
echo   2. 只做連線體檢（不下載）
echo   3. 列出可用國家
echo.
set /p CHOICE=請輸入 1 到 3 後按 Enter： 

if "%CHOICE%"=="1" goto DOWNLOAD
if "%CHOICE%"=="2" goto CHECK
if "%CHOICE%"=="3" goto LIST
echo 沒有這個選項。
pause
exit /b 1

:DOWNLOAD
echo.
echo 開始下載。澳洲的官方 API 規定每 20 秒 1 次請求，因此該國需要約 2 分鐘。
echo.
"%PY%" -m drugprice download --all
goto END

:CHECK
"%PY%" -m drugprice check
goto END

:LIST
"%PY%" -m drugprice list
goto END

:END
echo.
echo   結果在 output 資料夾，原始檔在 raw 資料夾。
echo.
pause

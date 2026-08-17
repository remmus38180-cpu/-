# PowerShell 自動下載 Python
# 無需 Python，Windows 內置 PowerShell 就能執行

# 設定下載參數
$pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip"
$outputFile = "python-3.12.0-embed-amd64.zip"
$downloadDir = Get-Location

Write-Host "============================================================"
Write-Host "Python 3.12.0 自動下載腳本"
Write-Host "============================================================"
Write-Host ""
Write-Host "下載位置: $downloadDir"
Write-Host "下載網址: $pythonUrl"
Write-Host ""

# 檢查檔案是否已存在
if (Test-Path $outputFile) {
    Write-Host "[警告] 檔案已存在: $outputFile"
    $response = Read-Host "是否重新下載? (y/n)"
    if ($response -ne 'y') {
        Write-Host "已取消下載"
        exit 0
    }
}

Write-Host "[開始] 正在下載 Python 3.12.0..."
Write-Host ""

try {
    # 下載檔案
    $ProgressPreference = 'SilentlyContinue'  # 隱藏進度條（可選）
    Invoke-WebRequest -Uri $pythonUrl -OutFile $outputFile -UseBasicParsing

    # 檢查下載是否成功
    if (Test-Path $outputFile) {
        $fileSize = (Get-Item $outputFile).Length / 1MB
        Write-Host ""
        Write-Host "============================================================"
        Write-Host "[成功] 下載完成！"
        Write-Host "============================================================"
        Write-Host ""
        Write-Host "檔案名稱: $outputFile"
        Write-Host "檔案大小: $([Math]::Round($fileSize, 2)) MB"
        Write-Host "位置: $(Get-Item $outputFile).FullName"
        Write-Host ""
        Write-Host "接下來:"
        Write-Host "1. 將此檔案複製到隔離平台"
        Write-Host "2. 在隔離平台解壓"
        Write-Host "3. 執行 auto_download_and_install.py"
        Write-Host ""

        # 詢問是否打開檔案夾
        $openFolder = Read-Host "是否打開檔案夾查看下載的檔案? (y/n)"
        if ($openFolder -eq 'y') {
            Start-Process explorer.exe -ArgumentList (Get-Item $outputFile).Directory.FullName
        }
    } else {
        Write-Host "[失敗] 下載失敗！檔案未找到"
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "[錯誤] 下載失敗！"
    Write-Host "錯誤訊息: $_"
    Write-Host ""
    Write-Host "可能原因:"
    Write-Host "1. 網絡連接失敗"
    Write-Host "2. Python.org 網站無響應"
    Write-Host "3. 防火牆阻止下載"
    Write-Host ""
    Write-Host "解決方案:"
    Write-Host "1. 檢查網絡連接"
    Write-Host "2. 在瀏覽器中手動下載:"
    Write-Host "   $pythonUrl"
    Write-Host "3. 聯絡 IT 部門檢查防火牆設定"
    exit 1
}

Write-Host "按 Enter 鍵退出..."
Read-Host

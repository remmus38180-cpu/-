# ============================================================
# 一鍵完全自動化腳本 (One-Click Setup)
# 功能: 下載 → 解壓 → 執行（全自動）
# ============================================================

param(
    [string]$WorkDir = (Get-Location).Path
)

# 設定顏色輸出
$colors = @{
    Success = 'Green'
    Error   = 'Red'
    Warning = 'Yellow'
    Info    = 'Cyan'
}

function Write-ColorOutput($message, $type = 'Info') {
    Write-Host $message -ForegroundColor $colors[$type]
}

function Print-Section($title) {
    Write-Host ""
    Write-Host "=" * 70
    Write-Host "  $title"
    Write-Host "=" * 70
    Write-Host ""
}

# ============================================================
# 主程式
# ============================================================

Print-Section "一鍵完全自動化安裝 - One-Click Setup"

Write-ColorOutput "此腳本會自動完成以下工作:" Info
Write-Host "  1. 下載 Python 3.12.0 便攜版本"
Write-Host "  2. 解壓縮 Python"
Write-Host "  3. 自動執行主腳本"
Write-Host "     └─ 自動下載 Chrome/Chromium"
Write-Host "     └─ 自動下載 ChromeDriver"
Write-Host "     └─ 自動下載並安裝 Selenium"
Write-Host "     └─ 自動執行截圖程式"
Write-Host ""

# ============================================================
# Step 1: 下載 Python
# ============================================================

Print-Section "Step 1: 下載 Python 3.12.0"

$pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip"
$pythonZip = Join-Path $WorkDir "python-3.12.0-embed-amd64.zip"
$pythonDir = Join-Path $WorkDir "python_portable"
$pythonExe = Join-Path $pythonDir "python.exe"

Write-ColorOutput "下載位置: $WorkDir" Info
Write-Host ""

# 檢查檔案是否已存在
if (Test-Path $pythonZip) {
    Write-ColorOutput "[OK] Python ZIP 檔案已存在" Success
    $fileSize = (Get-Item $pythonZip).Length / 1MB
    Write-Host "     檔案大小: $([Math]::Round($fileSize, 2)) MB"
    Write-Host ""
} else {
    Write-ColorOutput "[開始] 正在下載 Python 3.12.0..." Info
    Write-Host "        網址: $pythonUrl"
    Write-Host ""

    try {
        $ProgressPreference = 'Continue'
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonZip -UseBasicParsing

        if (Test-Path $pythonZip) {
            $fileSize = (Get-Item $pythonZip).Length / 1MB
            Write-ColorOutput "[成功] 下載完成!" Success
            Write-Host "        檔案: python-3.12.0-embed-amd64.zip"
            Write-Host "        大小: $([Math]::Round($fileSize, 2)) MB"
            Write-Host ""
        } else {
            Write-ColorOutput "[失敗] 下載失敗，檔案未找到" Error
            exit 1
        }
    } catch {
        Write-ColorOutput "[錯誤] 下載失敗！" Error
        Write-Host "原因: $_"
        Write-Host ""
        exit 1
    }
}

# ============================================================
# Step 2: 解壓縮 Python
# ============================================================

Print-Section "Step 2: 解壓縮 Python"

if (Test-Path $pythonExe) {
    Write-ColorOutput "[OK] Python 已解壓" Success
    Write-Host ""
} else {
    Write-ColorOutput "[開始] 正在解壓 Python..." Info
    Write-Host ""

    try {
        # 使用 System.IO.Compression.ZipFile
        Add-Type -AssemblyName System.IO.Compression.FileSystem

        Write-Host "  正在解壓檔案..."
        [System.IO.Compression.ZipFile]::ExtractToDirectory($pythonZip, $WorkDir, $true)

        # 驗證解壓結果
        if (Test-Path $pythonExe) {
            Write-ColorOutput "[成功] 解壓完成!" Success
            Write-Host "        目錄: $pythonDir"
            Write-Host ""
        } else {
            Write-ColorOutput "[失敗] 解壓失敗，Python 未找到" Error
            exit 1
        }
    } catch {
        Write-ColorOutput "[錯誤] 解壓失敗！" Error
        Write-Host "原因: $_"
        exit 1
    }
}

# ============================================================
# Step 3: 檢查必要檔案
# ============================================================

Print-Section "Step 3: 檢查必要檔案"

$requiredFiles = @(
    "auto_download_and_install.py",
    "drug_price_screenshot_selenium.py",
    "drug_list.csv"
)

$missingFiles = @()

foreach ($file in $requiredFiles) {
    $filePath = Join-Path $WorkDir $file
    if (Test-Path $filePath) {
        Write-ColorOutput "[OK] $file" Success
    } else {
        Write-ColorOutput "[缺失] $file" Error
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host ""
    Write-ColorOutput "[錯誤] 缺少必要檔案!" Error
    Write-Host "請確保以下檔案在此目錄:"
    foreach ($file in $missingFiles) {
        Write-Host "  - $file"
    }
    exit 1
}

Write-Host ""

# ============================================================
# Step 4: 執行主腳本
# ============================================================

Print-Section "Step 4: 執行自動下載腳本"

Write-ColorOutput "即將執行 auto_download_and_install.py" Info
Write-Host ""
Write-ColorOutput "此過程會自動:" Info
Write-Host "  ✓ 下載 Chrome/Chromium 瀏覽器"
Write-Host "  ✓ 下載 ChromeDriver"
Write-Host "  ✓ 下載並安裝 Selenium 庫"
Write-Host "  ✓ 執行截圖程式"
Write-Host ""
Write-ColorOutput "預計時間: 30-90 分鐘" Warning
Write-Host ""
Write-Host "=" * 70
Write-Host ""

$autoScript = Join-Path $WorkDir "auto_download_and_install.py"

try {
    & $pythonExe $autoScript
    $exitCode = $LASTEXITCODE

    Write-Host ""
    Write-Host "=" * 70

    if ($exitCode -eq 0) {
        Print-Section "完成！ SUCCESS"
        Write-ColorOutput "所有操作已自動完成！" Success
        Write-Host "截圖已保存在: drug_price_screenshots/"
        Write-Host ""
    } else {
        Print-Section "執行過程中出現錯誤"
        Write-ColorOutput "請檢查上方的錯誤訊息" Error
        Write-Host ""
        exit $exitCode
    }
} catch {
    Print-Section "執行失敗"
    Write-ColorOutput "錯誤: $_" Error
    exit 1
}

Write-Host "按 Enter 鍵退出..."
Read-Host

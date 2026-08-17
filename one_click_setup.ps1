# ============================================================
# One-Click Setup Script
# Downloads Python, Extracts, and Runs auto_download_and_install.py
# ============================================================

param(
    [string]$WorkDir = (Get-Location).Path
)

# Color output
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
# Main Program
# ============================================================

Print-Section "One-Click Setup"

Write-ColorOutput "This script will automatically:" Info
Write-Host "  1. Download Python 3.12.0 portable version"
Write-Host "  2. Extract Python"
Write-Host "  3. Run auto_download_and_install.py"
Write-Host "     - Download Chrome/Chromium"
Write-Host "     - Download ChromeDriver"
Write-Host "     - Download and install Selenium"
Write-Host "     - Run screenshot program"
Write-Host ""

# ============================================================
# Step 1: Download Python
# ============================================================

Print-Section "Step 1: Download Python 3.12.0"

$pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip"
$pythonZip = Join-Path $WorkDir "python-3.12.0-embed-amd64.zip"
$pythonDir = Join-Path $WorkDir "python_portable"
$pythonExe = Join-Path $pythonDir "python.exe"

Write-ColorOutput "Download location: $WorkDir" Info
Write-Host ""

# Check if file already exists
if (Test-Path $pythonZip) {
    Write-ColorOutput "[OK] Python ZIP file already exists" Success
    $fileSize = (Get-Item $pythonZip).Length / 1MB
    Write-Host "     File size: $([Math]::Round($fileSize, 2)) MB"
    Write-Host ""
} else {
    Write-ColorOutput "[START] Downloading Python 3.12.0..." Info
    Write-Host "        URL: $pythonUrl"
    Write-Host ""

    try {
        $ProgressPreference = 'Continue'
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonZip -UseBasicParsing

        if (Test-Path $pythonZip) {
            $fileSize = (Get-Item $pythonZip).Length / 1MB
            Write-ColorOutput "[SUCCESS] Download complete!" Success
            Write-Host "        File: python-3.12.0-embed-amd64.zip"
            Write-Host "        Size: $([Math]::Round($fileSize, 2)) MB"
            Write-Host ""
        } else {
            Write-ColorOutput "[FAILED] Download failed, file not found" Error
            exit 1
        }
    } catch {
        Write-ColorOutput "[ERROR] Download failed!" Error
        Write-Host "Reason: $_"
        Write-Host ""
        exit 1
    }
}

# ============================================================
# Step 2: Extract Python
# ============================================================

Print-Section "Step 2: Extract Python"

if (Test-Path $pythonExe) {
    Write-ColorOutput "[OK] Python already extracted" Success
    Write-Host ""
} else {
    Write-ColorOutput "[START] Extracting Python..." Info
    Write-Host ""

    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem

        Write-Host "  Extracting files..."
        [System.IO.Compression.ZipFile]::ExtractToDirectory($pythonZip, $WorkDir, $true)

        if (Test-Path $pythonExe) {
            Write-ColorOutput "[SUCCESS] Extraction complete!" Success
            Write-Host "        Directory: $pythonDir"
            Write-Host ""
        } else {
            Write-ColorOutput "[FAILED] Extraction failed, python.exe not found" Error
            exit 1
        }
    } catch {
        Write-ColorOutput "[ERROR] Extraction failed!" Error
        Write-Host "Reason: $_"
        exit 1
    }
}

# ============================================================
# Step 3: Check Required Files
# ============================================================

Print-Section "Step 3: Check Required Files"

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
        Write-ColorOutput "[MISSING] $file" Error
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host ""
    Write-ColorOutput "[ERROR] Missing required files!" Error
    Write-Host "Please ensure these files are in this directory:"
    foreach ($file in $missingFiles) {
        Write-Host "  - $file"
    }
    exit 1
}

Write-Host ""

# ============================================================
# Step 4: Run Main Script
# ============================================================

Print-Section "Step 4: Run auto_download_and_install.py"

Write-ColorOutput "Running auto_download_and_install.py" Info
Write-Host ""
Write-ColorOutput "This process will automatically:" Info
Write-Host "  - Download Chrome/Chromium browser"
Write-Host "  - Download ChromeDriver"
Write-Host "  - Download and install Selenium library"
Write-Host "  - Run screenshot program"
Write-Host ""
Write-ColorOutput "Estimated time: 30-90 minutes" Warning
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
        Print-Section "SUCCESS - Complete!"
        Write-ColorOutput "All operations completed successfully!" Success
        Write-Host "Screenshots saved to: drug_price_screenshots/"
        Write-Host ""
    } else {
        Print-Section "ERROR - Execution Failed"
        Write-ColorOutput "Please check the error messages above" Error
        Write-Host ""
        exit $exitCode
    }
} catch {
    Print-Section "ERROR - Execution Failed"
    Write-ColorOutput "Error: $_" Error
    exit 1
}

Write-Host "Press Enter to exit..."
Read-Host

# 🚀 自動解壓 + 執行指南

> 下載 Python ZIP 後的完整自動化流程

---

## ❓ 問題

下載 `python-3.12.0-embed-amd64.zip` 後，怎麼做？

**答案**：無需手動解壓！使用自動腳本！

---

## ✅ 三個選擇

### 🥇 **推薦：雙擊批文件（最簡單）**

```
setup_and_run.bat
```

**做什麼**：
1. ✅ 自動解壓 Python ZIP
2. ✅ 自動執行 `auto_download_and_install.py`
3. ✅ 自動下載 Chrome、ChromeDriver、Selenium
4. ✅ 自動執行截圖程式

**缺點**：
- ❌ 需要 Windows 10+ 或 PowerShell

---

### 🥈 **如果批文件不工作**

```
python setup_and_run.py
```

**前提**：系統中已有任何版本的 Python

**優點**：
- ✅ 純 Python，完全可靠
- ✅ 詳細的錯誤訊息

---

### 🥉 **手動解壓**

如果以上都不工作：

```
1. 右鍵點擊 python-3.12.0-embed-amd64.zip
2. 選擇「解壓縮到」
3. 選擇本目錄
4. 等待解壓完成
5. 執行: python_portable\python.exe auto_download_and_install.py
```

---

## 🎯 完整流程

### 在您有網絡的電腦上

```
Step 1: 執行 download_python.bat
        ↓
Step 2: 自動下載 python-3.12.0-embed-amd64.zip
        ↓
Step 3: 複製 ZIP 到隔離平台
```

### 在隔離平台上

```
Step 4: 複製以下檔案到同一目錄
        - python-3.12.0-embed-amd64.zip
        - setup_and_run.bat (或 setup_and_run.py)
        - auto_download_and_install.py
        - drug_price_screenshot_selenium.py
        - drug_list.csv
        ↓

Step 5: 雙擊 setup_and_run.bat
        ↓

Step 6: 自動完成！✅
        - 自動解壓 Python
        - 自動下載 Chrome、ChromeDriver、Selenium
        - 自動執行截圖
        - 完成！
```

---

## 📊 腳本詳細說明

### `setup_and_run.bat` 做什麼？

```
Step 1: 檢查 python-3.12.0-embed-amd64.zip 是否存在
        ↓
Step 2: 檢查是否已解壓（查找 python_portable\python.exe）
        ↓
Step 3: 如果未解壓，自動解壓 ZIP
        ↓
Step 4: 檢查 auto_download_and_install.py 是否存在
        ↓
Step 5: 執行 auto_download_and_install.py
        ↓
完成！✅
```

### `setup_and_run.py` 做什麼？

同上，但用 Python 實現，更可靠。

---

## 🔄 完整自動化流程示意

```
有網絡的電腦                           隔離平台

download_python.bat ──→ python-3.12.0-embed-amd64.zip ──→ setup_and_run.bat
                                                               ↓
                                                        自動解壓 Python
                                                               ↓
                                                        自動執行腳本
                                                               ↓
                                                        自動下載依賴
                                                               ↓
                                                        自動執行截圖
                                                               ↓
                                                           完成！✅
```

---

## ✅ 詳細步驟

### 您有網絡的電腦（只做一次）

```bash
1. 雙擊 download_python.bat
2. 等待下載完成
3. 檢查是否有 python-3.12.0-embed-amd64.zip
```

### 隔離平台（每次新環境）

```bash
1. 複製以下 6 個檔案到隔離平台:
   ✓ python-3.12.0-embed-amd64.zip
   ✓ setup_and_run.bat
   ✓ auto_download_and_install.py
   ✓ drug_price_screenshot_selenium.py
   ✓ drug_list.csv
   ✓ QUICK_START.md

2. 雙擊 setup_and_run.bat

3. 看著它自動完成
   (不需要手動做任何事！)

4. 檢查 drug_price_screenshots/ 目錄
   (應該有 80+ 個截圖！)
```

---

## 🆘 問題排除

### 問題 1：「無法解壓」

**原因**：ZIP 損壞或不完整

**解決**：
1. 重新下載 Python ZIP
2. 執行 `setup_and_run.bat`

### 問題 2：「Python 未找到」

**原因**：ZIP 未正確解壓

**解決**：
1. 手動解壓 ZIP
2. 確保有 `python_portable\python.exe`
3. 重新執行 `setup_and_run.bat`

### 問題 3：「找不到 auto_download_and_install.py」

**原因**：缺少必要檔案

**解決**：
1. 確認所有 6 個檔案都在同一目錄
2. 重新執行 `setup_and_run.bat`

---

## 📋 需要的檔案清單

### 在隔離平台上必須有

```
工作目錄/
├── python-3.12.0-embed-amd64.zip ✓ 必須
├── setup_and_run.bat ✓ 必須
├── setup_and_run.py ✓ 備用
├── auto_download_and_install.py ✓ 必須
├── drug_price_screenshot_selenium.py ✓ 必須
└── drug_list.csv ✓ 必須
```

---

## ✨ 完全自動化！

```
您要做的事:
1. 複製 6 個檔案到隔離平台
2. 雙擊 setup_and_run.bat
3. 完成！

您不需要做的事:
❌ 手動解壓 Python
❌ 手動運行任何命令
❌ 手動配置任何東西
❌ 手動下載 Chrome/ChromeDriver
❌ 手動安裝 Selenium
❌ 手動執行截圖程式

一切都自動完成！✨
```

---

## 📊 時間表

| 階段 | 時間 | 說明 |
|------|------|------|
| 有網絡電腦：下載 Python | 5-15 分鐘 | 一次性 |
| 隔離平台：解壓 + 執行 | 60-90 分鐘 | 首次（包括下載依賴） |
| 隔離平台：後續執行 | 30-60 分鐘 | 之後每次（依賴已有） |

---

**就這麼簡單！一切都自動完成！** 🎉

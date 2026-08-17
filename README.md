# 國際藥價自動截圖 - 完整包

> **完全自動化方案** - 自動下載所有依賴，一鍵執行

---

## 📦 包內容

```
drug_price_screenshot_package/
├── README.md (本檔案)
├── 
├── 【主程式】
├── drug_price_screenshot_selenium.py ⭐ 核心程式
├── drug_list.csv ⭐ 藥品清單（10 個測試）
├── 
├── 【完全自動化】⭐⭐⭐ 推薦使用
├── auto_download_and_install.py ⭐⭐⭐ Python 版本（推薦）
├── auto_download_and_install.bat ⭐⭐ Windows 一鍵執行
├── 
├── 【手動設置版本】(備用)
├── auto_setup_and_run.bat Windows 手動下載版
├── auto_setup_and_run.py Python 手動下載版
├── 
├── 【使用指南】
├── DAILY_EXECUTION_GUIDE.md ⭐ 每日快速指南
├── WINDOWS_EXECUTION_GUIDE.md 詳細設置
├── PYTHON_INSTALLATION_GUIDE.md Python 下載安裝
└── 
```

---

## 🚀 快速開始（1 步）✨ **最簡單方式**

### 完全自動方案 - 只需一個命令！

```bash
# 方法 A: 雙擊執行 (最簡單)
auto_download_and_install.bat

# 方法 B: 命令提示符
python auto_download_and_install.py
```

**會自動**：
- ✓ 下載 Python (如果未安裝)
- ✓ 下載 Chrome/Chromium (如果未安裝)
- ✓ 下載 ChromeDriver (匹配您的 Chrome 版本)
- ✓ 安裝 Selenium
- ✓ 執行截圖程式

**預計時間**：
- 首次：30-60 分鐘（包括下載和安裝）
- 之後：30-60 分鐘（只執行程式）

---

## 🔧 備用方案（如果自動下載失敗）

### 第 1 步：手動準備環境
1. **安裝 Python 3.8+**
   - 訪問 https://www.python.org/downloads/
   - 下載 Windows 64-bit installer
   - 安裝時勾選 "Add Python to PATH"

2. **下載 ChromeDriver**
   - 查詢 Chrome 版本：`設定` → `關於 Chrome`
   - 訪問 https://chromedriver.chromium.org/
   - 下載相符版本的 win64
   - **解壓 `chromedriver.exe` 到本目錄**

### 第 2 步：執行手動版自動化腳本
```bash
# 方法 A: 雙擊執行
auto_setup_and_run.bat

# 方法 B: 命令提示符
python auto_setup_and_run.py
```

### 第 3 步：等待完成
- 預計 30-60 分鐘
- 截圖會保存在 `drug_price_screenshots/` 目錄

---

## 📋 每天執行流程

由於您的隔離平台每天重新安裝，只需一個命令：

```bash
# 只需這一個命令（會自動下載所有依賴）
python auto_download_and_install.py

# 或
auto_download_and_install.bat
```

**會自動**：
- ✓ 下載 Python (如果需要)
- ✓ 下載 Chrome/Chromium (如果需要)
- ✓ 下載 ChromeDriver (匹配版本)
- ✓ 安裝 Selenium
- ✓ 執行截圖程式

---

## 📝 修改藥品清單

編輯 `drug_list.csv`，每行一個藥品名：

```csv
Exforge
Exforge HCT
Dafiro
Dafiro HCT
Dificid
Sunvepra
IXEMPRA
Ilaris
Zelboraf
Romiplate
（添加您的藥品名）
```

保存後，再次執行自動化腳本即可。

---

## ⚠️ 必須檔案清單

✅ 必備（本包已含）：
- `drug_price_screenshot_selenium.py` - 核心程式
- `drug_list.csv` - 藥品清單
- `auto_download_and_install.py` - 完全自動版（推薦）
- `auto_download_and_install.bat` - Windows 完全自動版
- `auto_setup_and_run.py` - 手動版本（備用）
- `auto_setup_and_run.bat` - 手動版本（備用）

❌ 不需要手動準備（會自動下載）：
- Python - 自動下載便攜版本
- ChromeDriver - 自動下載匹配版本
- Chrome/Chromium - 自動下載（如果需要）

---

## 🆘 常見問題

### Q1: "chromedriver 未找到"
**原因**: 自動下載失敗（可能網絡問題）
**解決**:
1. 檢查網絡連接是否正常
2. 如果自動下載失敗，使用備用方案：
   - 手動下載 ChromeDriver (https://chromedriver.chromium.org/)
   - 解壓到本目錄
   - 確保檔案名是 `chromedriver.exe`

### Q2: "Python 未安裝 / 自動下載失敗"
**解決**:
1. 檢查隔離平台的網絡連接
2. 如果自動下載失敗，手動下載：
   - 訪問 https://www.python.org/downloads/
   - 下載 Windows Portable 版本 (win64)
   - 解壓到 `python_portable/` 目錄
   - 重新執行腳本

### Q3: "Chrome 自動下載失敗"
**原因**: Chromium 下載服務可能不可用
**解決**:
1. 安裝 Google Chrome (https://www.google.com/chrome/)
2. 腳本會自動檢測已安裝的 Chrome
3. 自動下載匹配的 ChromeDriver

### Q4: "藥品找不到"
**原因**: 某些網站的 HTML 結構已改變
**解決**: 腳本會跳過該國家，繼續執行其他國家

### Q5: "連接超時"
**原因**: 網站無響應或網絡慢
**解決**: 重新執行即可（某些超時是暫時的）

---

## 📊 預期輸出

執行完成後，您會得到：

```
drug_price_screenshots/
├── UK_Exforge_search_results.png
├── UK_Exforge_HCT_search_results.png
├── UK_Dafiro_search_results.png
├── ... (80+ 個截圖)
└── 更多檔案...
```

**統計**:
- 10 個藥品 × 8 個國家 = 80 個截圖
- 磁碟空間: 約 50-100 MB
- 執行時間: 30-60 分鐘

---

## 🔧 進階配置

### 只查詢特定國家
```bash
python drug_price_screenshot_selenium.py --input drug_list.csv --countries UK,FR
```

支援的國家碼: `JP`, `AU`, `BE`, `FR`, `SE`, `CH`, `UK`, `CA`

### 指定輸出目錄
```bash
python drug_price_screenshot_selenium.py --input drug_list.csv --output-dir my_screenshots
```

---

## 📞 更多幫助

詳細指南：
- **DAILY_EXECUTION_GUIDE.md** - 每日快速參考
- **WINDOWS_EXECUTION_GUIDE.md** - 完整設置說明
- **PYTHON_INSTALLATION_GUIDE.md** - Python 安裝

---

## ✅ 執行檢查清單

執行前確認：

- [ ] `drug_list.csv` 存在
- [ ] `drug_price_screenshot_selenium.py` 存在
- [ ] 網絡連接正常（用於下載依賴）
- [ ] 足夠的磁碟空間 (至少 500 MB，用於下載和截圖)
- [ ] 隔離平台允許運行 Python 腳本

**其他所有內容都會自動處理！** ✨

---

## 📊 預期流程

### 首次運行（包含下載）
1. 下載 Python (~30-50 MB)
2. 下載 Chrome/Chromium (~100-200 MB)
3. 下載 ChromeDriver (~5-10 MB)
4. 安裝 Selenium
5. 執行截圖 (~30-60 分鐘)
6. **總計時間**: 60-90 分鐘

### 之後每天運行
1. 如果檔案已在，直接使用
2. 執行截圖 (~30-60 分鐘)
3. **總計時間**: 30-60 分鐘

---

**祝執行順利！有任何問題，檢查 DAILY_EXECUTION_GUIDE.md 或提問即可。**

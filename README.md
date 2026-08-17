# 國際藥價自動截圖 - 完整包

> **一鍵解決方案** - 包含所有必要檔案和說明

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
├── 【自動化執行】(推薦)
├── auto_setup_and_run.bat ⭐ Windows 一鍵執行
├── auto_setup_and_run.py ⭐ Python 版本
├── 
├── 【使用指南】
├── DAILY_EXECUTION_GUIDE.md ⭐ 每日快速指南
├── WINDOWS_EXECUTION_GUIDE.md 詳細設置
├── PYTHON_INSTALLATION_GUIDE.md Python 下載安裝
└── 
```

---

## 🚀 快速開始（3 步）

### 第 1 步：準備環境
1. 在隔離平台中**安裝 Python 3.8+**
   - 訪問 https://www.python.org/downloads/
   - 下載 Windows 64-bit installer
   - 安裝時勾選 "Add Python to PATH"

2. **下載 ChromeDriver**
   - 查詢 Chrome 版本：`設定` → `關於 Chrome`
   - 訪問 https://chromedriver.chromium.org/
   - 下載相符版本的 win64
   - **解壓 `chromedriver.exe` 到本目錄**

### 第 2 步：執行自動化腳本
```bash
# 方法 A: 雙擊執行 (最簡單)
auto_setup_and_run.bat

# 方法 B: 命令提示符
python auto_setup_and_run.py
```

### 第 3 步：等待完成
- 預計 30-60 分鐘
- 截圖會保存在 `drug_price_screenshots/` 目錄

---

## 📋 每天執行流程

由於您的隔離平台每天重新安裝，重複以下步驟：

```bash
# 只需這一個命令
python auto_setup_and_run.py
```

**會自動**：
- ✓ 檢查 Python
- ✓ 安裝 Selenium
- ✓ 驗證 ChromeDriver
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
- `drug_price_screenshot_selenium.py`
- `drug_list.csv`
- `auto_setup_and_run.bat` 或 `.py`

❌ 需要您手動準備：
- `chromedriver.exe` (下載後放在本目錄)
- Python 3.8+ (安裝在隔離平台)

---

## 🆘 常見問題

### Q1: "chromedriver 未找到"
**解決**:
1. 下載 ChromeDriver (https://chromedriver.chromium.org/)
2. 解壓到本目錄
3. 確保檔案名是 `chromedriver.exe`

### Q2: "Python 未安裝"
**解決**:
1. 在隔離平台安裝 Python 3.8+
2. 勾選 "Add Python to PATH"
3. 重啟命令提示符

### Q3: "藥品找不到"
**原因**: 某些網站的 HTML 結構已改變
**解決**: 腳本會跳過該國家，繼續執行其他國家

### Q4: "連接超時"
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

- [ ] Python 已安裝 (`python --version`)
- [ ] ChromeDriver 已下載並放在本目錄
- [ ] `drug_list.csv` 存在
- [ ] 網絡連接正常
- [ ] 足夠的磁碟空間 (100+ MB)

---

**祝執行順利！有任何問題，檢查 DAILY_EXECUTION_GUIDE.md 或提問即可。**

# 每日執行指南 - 隔離平台版本

> **適用於**: 每天都要重新安裝的隔離平台/VPN 環境

---

## 🎯 快速流程（第一次）

### 第 1 次執行時：

1. **下載這些檔案到您的隔離平台**：
   - `drug_price_screenshot_selenium.py` （主程式）
   - `drug_list.csv` （藥品清單）
   - `auto_setup_and_run.bat` 或 `.py` （自動化腳本）

2. **下載 ChromeDriver**：
   - 查詢您的 Chrome 版本：`設定` → `關於 Chrome`
   - 訪問 https://chromedriver.chromium.org/ 下載相符版本
   - 解壓 `chromedriver.exe` 到同一目錄

3. **執行自動化腳本**：
   - **方法 A** (簡單)：雙擊 `auto_setup_and_run.bat`
   - **方法 B** (更可靠)：打開命令提示符，執行
     ```bash
     python auto_setup_and_run.py
     ```

4. **等待完成**：
   - 大約 30-60 分鐘
   - 截圖會存放在 `drug_price_screenshots/` 目錄

---

## 🔄 之後每天的執行

由於您每天都要重新安裝，**重複以上步驟**：

```bash
# 簡單方式 - 只需 2 行命令
python auto_setup_and_run.py
# 或
auto_setup_and_run.bat
```

**自動會**：
- ✓ 檢查 Python
- ✓ 安裝 Selenium
- ✓ 檢查 ChromeDriver
- ✓ 驗證輸入檔案
- ✓ 自動執行截圖程式

---

## 📋 檔案準備清單

需要在同一目錄中：

```
您的工作目錄/
├── drug_price_screenshot_selenium.py ✓ 下載
├── drug_list.csv ✓ 下載
├── auto_setup_and_run.bat 或 .py ✓ 下載
├── chromedriver.exe ✓ 第 1 次時下載
└── drug_price_screenshots/ (自動建立)
    ├── UK_Exforge_search_results.png
    ├── UK_Exforge_HCT_search_results.png
    └── ... (80+ 個截圖)
```

---

## ⚙️ 如果出現錯誤

### 錯誤 1: "Python 未找到"
```
✗ Python 未安裝
```
**解決**: 在隔離平台中安裝 Python
- 下載 Python 3.10+ 安裝程式
- 執行安裝，**勾選 "Add Python to PATH"**
- 重新執行自動化腳本

### 錯誤 2: "ChromeDriver 未找到"
```
⚠ ChromeDriver 未在 PATH 中
```
**解決**:
- 確認 `chromedriver.exe` 與腳本在同一目錄
- 或將其放入 Python `Scripts` 資料夾
- 或添加到系統 PATH 環境變數

### 錯誤 3: "Selenium 安裝失敗"
```
✗ Selenium 安裝失敗
```
**解決**:
```bash
# 手動安裝
python -m pip install selenium --upgrade

# 確認安裝
python -c "import selenium; print(selenium.__version__)"
```

### 錯誤 4: "drug_list.csv 未找到"
```
✗ drug_list.csv 未找到
```
**解決**:
- 確保檔案在同一目錄
- 檔案名稱必須完全相同（小寫 csv）
- 檔案編碼為 UTF-8（建議用記事本編輯）

---

## 💡 進階用法

### 修改藥品清單
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
您的藥品名
```

### 只查詢特定國家
修改 `auto_setup_and_run.bat` 或 `.py`，改變命令行：

**BAT 版本**：找到最後一行，改為：
```bash
python drug_price_screenshot_selenium.py --input drug_list.csv --countries UK,FR
```

**Python 版本**：修改最後的 subprocess.run：
```python
[sys.executable, "drug_price_screenshot_selenium.py", 
 "--input", "drug_list.csv",
 "--countries", "UK,FR"]
```

支援的國家碼：`JP`, `AU`, `BE`, `FR`, `SE`, `CH`, `UK`, `CA`

---

## 🚀 完整示例

### Day 1 (第一次執行)
```bash
# 1. 準備檔案（已下載）
# drug_price_screenshot_selenium.py ✓
# drug_list.csv ✓
# auto_setup_and_run.bat ✓
# chromedriver.exe ✓

# 2. 執行
python auto_setup_and_run.py

# 3. 等待 30-60 分鐘

# 4. 檢查結果
dir drug_price_screenshots
# 應該有 80+ 個 PNG 檔案
```

### Day 2 (重新安裝後)
```bash
# 1. 複製相同檔案到新環境
# 2. 執行（會自動重新安裝依賴）
python auto_setup_and_run.py

# 3. 完成！
```

---

## 📝 注意事項

- ⏱ **首次執行慢**: 因為要安裝 Selenium，第一次需要額外 5-10 分鐘
- 🔌 **網絡穩定**: 確保隔離平台網絡穩定，否則查詢可能超時
- 💾 **清理舊檔**: 如果要重新執行，建議刪除舊的 `drug_price_screenshots/` 目錄
- 🛑 **中斷恢復**: 如果中途中斷，重新執行會從頭開始（目前無斷點續傳功能）

---

## ❓ 最常見的問題

**Q: 為什麼每天都要重新安裝？**
A: 您的隔離平台每天重置，所以需要重新安裝依賴。自動化腳本可以快速完成此流程。

**Q: 能否保存腳本以減少每天的下載？**
A: 可以。準備好 4 個檔案後，每次登入隔離平台只需上傳這 4 個檔案即可。

**Q: 如果隔離平台無法訪問 Python 官網？**
A: 改用在本機安裝 Python 便攜版，然後上傳到隔離平台。

**Q: 執行時間太長怎麼辦？**
A: 可以減少 `drug_list.csv` 中的藥品數量進行測試。

---

## ✅ 執行檢查清單

每次執行前檢查：

- [ ] Python 已安裝 (命令提示符執行 `python --version`)
- [ ] 4 個檔案在同一目錄
- [ ] `chromedriver.exe` 可用
- [ ] `drug_list.csv` 編碼為 UTF-8
- [ ] 網絡連接正常
- [ ] 足夠的磁碟空間 (80+ 個截圖 ≈ 50-100 MB)

---

**祝您執行順利！有問題隨時提問。**

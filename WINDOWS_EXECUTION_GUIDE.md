# Windows 本機執行指南 - 國際藥價自動截圖

> **此遠端環境無法執行，請在本機 Windows 環境執行**

---

## 📋 前置條件

### 1. Python 環境
```bash
# 檢查 Python 版本 (需要 3.8+)
python3 --version

# 或使用您的 WinPython 環境
C:\Users\a110701\Downloads\WPy64-313130\Scripts\python.exe --version
```

### 2. Chrome 瀏覽器
- 已安裝 Google Chrome
- 記下版本號：`設定` → `關於 Chrome` → 記下版本

### 3. ChromeDriver
下載對應您 Chrome 版本的 ChromeDriver：

| Chrome 版本 | ChromeDriver 下載 |
|-----------|------------------|
| 141 | https://chromedriver.chromium.org/downloads |
| 140 | https://chromedriver.chromium.org/downloads |
| 其他 | 相應版本 |

**下載方法**:
1. 訪問 https://chromedriver.chromium.org/
2. 點擊您的 Chrome 版本
3. 下載 `win64` 版本
4. 解壓到 `C:\Users\a110701\Downloads\WPy64-313130\scripts\` 目錄

---

## 🚀 執行步驟

### Step 1: 準備工作目錄
```bash
cd C:\Users\a110701\Downloads\WPy64-313130\scripts

# 確認以下文件存在：
# - drug_price_screenshot_selenium.py
# - drug_list.csv
# - chromedriver.exe (或 chromedriver)
```

### Step 2: 安裝 Selenium
```bash
# 使用您的 WinPython Python
C:\Users\a110701\Downloads\WPy64-313130\Scripts\python.exe -m pip install selenium --upgrade
```

### Step 3: 執行腳本

**全部 8 個國家**:
```bash
python3 drug_price_screenshot_selenium.py --input drug_list.csv
```

**或只測試英國**:
```bash
python3 drug_price_screenshot_selenium.py --input drug_list.csv --countries UK
```

**指定輸出目錄**:
```bash
python3 drug_price_screenshot_selenium.py --input drug_list.csv --output-dir my_screenshots
```

---

## 📊 執行預期

### 執行時間
- **10 個藥品 × 8 國** = 80 次查詢
- **平均每次** 2-3 秒
- **預計總時間** 30-60 分鐘

### 日誌輸出
```
[14:30:00] INFO - 讀取 10 個商品名
[14:30:01] INFO - 查詢國家: JP, AU, BE, FR, SE, CH, UK, CA
[14:30:01] INFO - === 開始查詢 日本 (JP) ===
[14:30:15] INFO - ✓ JP - Exforge
[14:30:28] INFO - ✓ JP - Exforge HCT
...
[15:00:00] INFO - 執行完成
[15:00:00] INFO - 成功國家 (8): JP, AU, BE, FR, SE, CH, UK, CA
[15:00:00] INFO - 共產生 80 個截圖
```

### 輸出檔案
```
drug_price_screenshots/
├─ UK_Exforge_search_results.png
├─ UK_Exforge_HCT_search_results.png
├─ DE_Exforge_search_results.png
├─ ... (共 80 個截圖)
└─ execution_log.txt
```

---

## ⚠️ 常見問題

### Q1: 「chromedriver 版本不符」
**解決**:
1. 查詢您的 Chrome 版本 (設定 → 關於)
2. 下載相符版本的 ChromeDriver
3. 確認 `chromedriver.exe` 在 `scripts` 目錄中

### Q2: 「搜尋欄未找到」
**原因**: 某些國家網站的 HTML 結構與預期不同
**解決**: 
- 腳本會跳過該國家，繼續執行其他國家
- 結果會記錄在日誌中

### Q3: 「連接超時」
**原因**: 網站無響應或網絡緩慢
**解決**: 
1. 檢查網絡連接
2. 增加超時時間（修改 `WAIT_TIMEOUT`）
3. 重新執行（某些查詢失敗是暫時的）

### Q4: 「截圖模糊或黑屏」
**原因**: 頁面未完全載入
**解決**:
1. 增加等待時間（修改 `time.sleep()` 值）
2. 調整視窗大小（修改 `set_window_size()` 參數）

---

## 🔧 進階配置

### 修改超時時間
編輯 `drug_price_screenshot_selenium.py`，找到：
```python
WAIT_TIMEOUT = 20  # 秒
```
改為您需要的值（建議 20-30 秒）

### 添加更多藥品
編輯 `drug_list.csv`，每行添加一個藥品名：
```csv
Exforge
Exforge HCT
Dafiro
...
（您的藥品名）
```

### 只查詢特定國家
```bash
# 只查詢英國和法國
python3 drug_price_screenshot_selenium.py --input drug_list.csv --countries UK,FR

# 支援的國家碼: JP, AU, BE, FR, SE, CH, UK, CA
```

---

## 📞 故障排除清單

- [ ] Python 版本 >= 3.8
- [ ] Chrome 瀏覽器已安裝並知道版本號
- [ ] ChromeDriver 版本與 Chrome 版本相符
- [ ] ChromeDriver 在 `scripts` 目錄或 PATH 中
- [ ] Selenium 已安裝 (`pip install selenium`)
- [ ] `drug_list.csv` 在 `scripts` 目錄中
- [ ] 網絡連接正常
- [ ] 無代理或代理已配置

---

## ✅ 後續步驟

1. **執行腳本並生成截圖**
2. **檢查 `drug_price_screenshots/` 目錄中的結果**
3. **如需增加藥品或國家，修改 `drug_list.csv` 或腳本參數**
4. **如有問題，檢查執行日誌找原因**

---

## 📝 注意事項

- ⚠️ **首次執行**可能較慢（Chrome 初始化）
- ⚠️ **某些國家網站**可能有速率限制，考慮添加延遲
- ⚠️ **HTTPS 連接**可能需要有效的 SSL 證書（通常無問題）
- ℹ️ **國家代碼**固定為：JP, AU, BE, FR, SE, CH, UK, CA（不包括 DE 和 US，需要登入）

祝執行順利！如有問題，檢查日誌輸出中的錯誤訊息。

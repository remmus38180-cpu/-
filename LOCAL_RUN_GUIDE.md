# 藥價網站自動截圖 - 本地運行指南

## 📋 前置準備

### 1. 安裝 Python 依賴
```bash
pip install selenium webdriver-manager
```

### 2. 確保已安裝 Chrome 瀏覽器
- **Windows**: `C:\Program Files\Google\Chrome\Application\chrome.exe`
- **macOS**: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- **Linux**: `google-chrome` 或 `chromium`

## 🚀 運行程式

### 最簡單的方式（查詢所有國家）
```bash
python3 drug_price_screenshot_selenium.py --input drug_list.csv
```

### 指定國家查詢
```bash
# 只查詢英國和法國
python3 drug_price_screenshot_selenium.py --countries UK,FR --input drug_list.csv

# 只查詢英國
python3 drug_price_screenshot_selenium.py --countries UK --input drug_list.csv
```

### 指定 Chrome 路徑（可選）
```bash
# 如果自動偵測失敗，可以明確指定 Chrome 路徑
python3 drug_price_screenshot_selenium.py \
    --input drug_list.csv \
    --chrome-path "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

### 自定義輸出目錄
```bash
python3 drug_price_screenshot_selenium.py \
    --input drug_list.csv \
    --output-dir "./my_screenshots"
```

## 📊 支援的國家代碼

| 代碼 | 國家 | 是否需登入 |
|------|------|----------|
| UK | 英國 | ❌ 否 |
| BE | 比利時 | ❌ 否 |
| FR | 法國 | ❌ 否 |
| SE | 瑞典 | ❌ 否 |
| CH | 瑞士 | ❌ 否 |
| AU | 澳洲 | ❌ 否 |
| JP | 日本 | ❌ 否 |
| CA | 加拿大 | ❌ 否 |

## 📝 藥品清單格式

編輯 `drug_list.csv`，每行一個藥品名（不需要標題）：

```csv
Zelboraf
Eliquis
Exforge
Aspirin
```

## ✅ 執行完成後

截圖會保存在 `drug_price_screenshots` 目錄中，檔名格式為：
```
<國家代碼>_<藥品名>_search_results.png
```

例如：
- `UK_Zelboraf_search_results.png`
- `FR_Eliquis_search_results.png`

## ⚙️ 日誌輸出示例

```
[2026-08-17 10:08:50] INFO - 讀取 2 個商品名
[2026-08-17 10:08:50] INFO - 查詢國家: UK, FR, BE
[2026-08-17 10:08:50] INFO - === 開始查詢 英國 (UK) ===
[2026-08-17 10:08:51] INFO - ✓ UK - Zelboraf
[2026-08-17 10:08:52] INFO - ✓ UK - Eliquis
[2026-08-17 10:08:50] INFO - === 開始查詢 法國 (FR) ===
...
[2026-08-17 10:09:00] INFO - 執行完成
[2026-08-17 10:09:00] INFO - 成功國家 (3): UK, FR, BE
[2026-08-17 10:09:00] INFO - 共產生 6 個截圖
```

## 🐛 常見問題

### ❌ 錯誤：`Cannot find Chrome`
**解決方案**：
1. 確認已安裝 Chrome
2. 使用 `--chrome-path` 參數明確指定路徑
3. 檢查路徑是否正確（Windows 使用雙反斜線或原生路徑）

### ❌ 錯誤：`ChromeDriver 版本不符`
**解決方案**：
- 程式會自動使用 `webdriver-manager` 下載正確版本
- 如果仍有問題，更新 Chrome 到最新版本

### ❌ 錯誤：`session not created`
**解決方案**：
1. 更新 Selenium：`pip install --upgrade selenium`
2. 更新 webdriver-manager：`pip install --upgrade webdriver-manager`
3. 重新安裝 Chrome 到預設位置

### ⚠️ 截圖失敗但程式繼續運行
- 程式會記錄失敗並繼續查詢其他國家
- 查看日誌中的 `✗` 標記了解失敗原因

## 💡 進階用法

### 查看所有可用選項
```bash
python3 drug_price_screenshot_selenium.py -h
```

### 批量修改藥品清單
```bash
# 添加新藥品
echo "新藥品名" >> drug_list.csv

# 清空並重新建立清單
cat > drug_list.csv << EOF
Zelboraf
Eliquis
Exforge
EOF
```

## 📧 如有任何問題或錯誤

直接告訴我錯誤訊息，我會立即修改程式碼 ✅

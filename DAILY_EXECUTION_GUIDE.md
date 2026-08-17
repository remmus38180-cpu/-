# 每日執行指南 - 自動下載版本

> **最簡單的方式** - 自動下載所有依賴，一鍵執行

---

## 🎯 超簡快流程（推薦）

### 僅需 1 步！

```bash
# 方法 A: 直接雙擊
auto_download_and_install.bat

# 方法 B: 命令提示符
python auto_download_and_install.py
```

**就這樣！** ✨ 其他一切都會自動完成。

---

## ⏱️ 預計時間

### 第一次
- **首次執行時間**: 60-90 分鐘
- 原因: 需要下載 Python (~30-50 MB) + Chrome (~100-200 MB) + ChromeDriver (~5-10 MB)

### 之後每天
- **執行時間**: 30-60 分鐘
- 原因: 只運行截圖程式，依賴已存在

---

## 📋 檔案準備清單

**只需準備這 3 個檔案**：

```
您的隔離平台/
├── drug_price_screenshot_selenium.py ✓
├── drug_list.csv ✓
└── auto_download_and_install.py ✓
    （或 auto_download_and_install.bat）
```

**所有其他依賴都會自動下載！**

---

## 🚀 完整示例

### Day 1 (第一次執行)
```bash
# 複製 3 個檔案到隔離平台

# 執行 (會自動下載依賴)
python auto_download_and_install.py

# 等待 60-90 分鐘
# 檢查結果
ls drug_price_screenshots/
# 應該有 80 個 PNG 檔案
```

### Day 2 (之後每天重新安裝)
```bash
# 1. 複製相同的 3 個檔案到新環境

# 2. 執行
python auto_download_and_install.py

# 3. 完成！（只需 30-60 分鐘）
```

---

## 🔍 自動下載流程

腳本會自動：

1. **檢查 Python**
   - 如果已安裝: 使用現有版本
   - 如果未安裝: 自動下載便攜版本 (3.12)

2. **檢查/下載 Chrome**
   - 如果已安裝: 讀取版本
   - 如果未安裝: 自動下載 Chromium 便攜版本

3. **下載 ChromeDriver**
   - 自動檢測 Chrome 版本
   - 下載匹配的 ChromeDriver

4. **安裝 Selenium**
   - 自動運行 pip install

5. **執行截圖**
   - 開始自動截圖流程

---

## 🆘 如果自動下載失敗

### 網絡問題導致下載失敗？

**選項 1: 使用備用方案**
```bash
# 使用手動版本（需要手動下載 Python 和 ChromeDriver）
python auto_setup_and_run.py
# 或
auto_setup_and_run.bat
```

**選項 2: 手動準備**
1. 在您的主機下載：
   - Python 便攜版本
   - ChromeDriver
2. 上傳到隔離平台
3. 放在同一目錄
4. 重新執行自動下載腳本

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
您的新藥品
```

保存後，執行自動化腳本即可。

---

## 💡 進階用法

### 只查詢特定國家

編輯 `auto_download_and_install.py`，找到最後的執行部分，改為：

```python
# 在 run_main_program() 調用時，修改為
cmd = f'"{python_exe}" drug_price_screenshot_selenium.py --input drug_list.csv --countries UK,FR'
```

支援的國家碼: `JP`, `AU`, `BE`, `FR`, `SE`, `CH`, `UK`, `CA`

### 指定輸出目錄

```bash
python drug_price_screenshot_selenium.py --input drug_list.csv --output-dir my_screenshots
```

---

## 📊 統計信息

- **藥品數**: 10 個（預設）
- **國家數**: 8 個（JP, AU, BE, FR, SE, CH, UK, CA）
- **總截圖數**: 80 個
- **磁碟空間**: ~100-150 MB （截圖結果）
- **執行時間**: 30-60 分鐘（不含下載）

---

## ✅ 故障排除

### 問題 1: "Python 下載失敗"
**原因**: 網絡連接問題
**解決**:
1. 檢查隔離平台網絡連接
2. 嘗試手動下載: https://www.python.org/downloads/ (Portable 版本)
3. 解壓到 `python_portable/` 目錄

### 問題 2: "ChromeDriver 下載失敗"
**原因**: 無法匹配 Chrome 版本
**解決**:
1. 檢查 Chrome 是否已安裝
2. 手動下載: https://googlechromelabs.github.io/chrome-for-testing/
3. 解壓 `chromedriver.exe` 到同一目錄

### 問題 3: "Selenium 安裝失敗"
**原因**: pip 下載問題
**解決**:
```bash
# 手動安裝
python -m pip install selenium --upgrade
```

### 問題 4: "藥品找不到"
**原因**: 某些網站結構改變
**解決**: 腳本會跳過該國家，繼續執行其他國家

### 問題 5: "連接超時"
**原因**: 網站無響應或網絡慢
**解決**: 重新執行即可

---

## 🎯 最佳實踐

1. **每次前準備相同的 3 個檔案**
   ```
   drug_price_screenshot_selenium.py
   drug_list.csv
   auto_download_and_install.py (或 .bat)
   ```

2. **保存成功的結果**
   ```
   drug_price_screenshots/
   ```

3. **隔離平台新環境時**
   - 上傳相同 3 個檔案
   - 執行一個命令
   - 等待完成

---

## 🌐 完全離線使用？

如果您的隔離平台完全無法聯網，請：

1. 在有網絡的電腦上：
   - 下載 Python 便攜版本
   - 下載 Chrome 或 Chromium 便攜版本
   - 下載 ChromeDriver
   - pip install selenium (到本地)

2. 將所有檔案轉移到隔離平台

3. 修改 `auto_download_and_install.py` 略過下載步驟

4. 執行

---

**祝您執行順利！** 

有任何問題，請參考 README.md 或檢查腳本的錯誤訊息。

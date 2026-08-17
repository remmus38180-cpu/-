# 📥 完整下載來源清單

> 所有腳本會下載的軟體來源和網址

---

## 🔍 腳本下載的所有網址

### 1️⃣ Python 3.12.0 便攜版

**網址**：
```
https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip
```

**來源**：python.org （官方 Python 基金會）

**檔案名稱**：`python-3.12.0-embed-amd64.zip`

**本地路徑**：`python_portable.zip` → 解壓到 `python_portable/`

**包含**：
- python.exe
- Python 標準庫
- 所有必要的 Python 工具

---

### 2️⃣ Chromium 瀏覽器（開源版 Chrome）

**第一步 - 查詢最新版本號**：
```
https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win_x64/LAST_CHANGE
```

**第二步 - 下載瀏覽器**：
```
https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win_x64/{BUILD_NUMBER}/chrome-win64.zip
```

**來源**：Google 官方 Chromium CI/CD 伺服器

**檔案名稱**：`chrome-win64.zip`

**本地路徑**：`chrome_portable.zip` → 解壓到 `chrome_portable/`

**包含**：
- chrome.exe（Chromium 瀏覽器）
- 所有必要的瀏覽器檔案

**注意**：Chromium 是 Chrome 的開源版本，由 Google 開發和維護

---

### 3️⃣ ChromeDriver 驅動程式

**第一步 - 查詢下載清單**：
```
https://googlechromelabs.github.io/chrome-for-testing/download-chrome-for-testing.json
```

**第二步 - 下載 ChromeDriver**：
```
https://googlechromelabs.github.io/chrome-for-testing/download-chrome-for-testing.json
(JSON 中包含對應版本的下載連結)
```

**來源**：Google Chrome for Testing 官方下載頁面

**檔案名稱**：`chromedriver.exe`

**本地路徑**：放在工作目錄根目錄

**功能**：用於自動控制瀏覽器進行截圖

---

## 🔐 安全驗證

### ✅ 所有來源都是官方的

| 軟體 | 官方機構 | 來源類型 |
|------|--------|--------|
| Python | Python Software Foundation | 官方網站 |
| Chromium | Google | 官方 CI 服務器 |
| ChromeDriver | Google | 官方下載頁面 |

### ✅ 沒有第三方來源

- ❌ 不使用 GitHub Releases
- ❌ 不使用非官方鏡像網站
- ❌ 不使用第三方軟體倉庫
- ✅ 只使用官方網址

### ✅ 都是開源或公開軟體

- Python：開源 (PSF License)
- Chromium：開源 (BSD License)
- ChromeDriver：開源 (BSD License)

---

## 📂 完整下載流程

```
Step 1: 檢查 Python
  └─ 如果未安裝 → 從 python.org 下載 python-3.12.0-embed-amd64.zip
     └─ 解壓到 python_portable/
     └─ 刪除 ZIP 檔案

Step 2: 檢查 Chrome
  └─ 查詢 Windows 註冊表中是否已安裝 Chrome
     └─ 如果已安裝 → 使用已安裝版本
     └─ 如果未安裝 → 從 Chromium 官方 CI 下載最新版本
        └─ 解壓到 chrome_portable/
        └─ 刪除 ZIP 檔案

Step 3: 下載 ChromeDriver
  └─ 查詢 Google Chrome for Testing 官方頁面
     └─ 找到與 Chrome 版本匹配的 ChromeDriver
     └─ 下載 chromedriver.exe
     └─ 解壓到工作目錄

Step 4: 安裝 Selenium
  └─ 使用 pip 從 PyPI（Python 官方包倉庫）下載 Selenium

Step 5: 執行截圖
  └─ 使用已安裝的軟體進行自動截圖
```

---

## 🛡️ 如何驗證下載

### 驗證 Python
```bash
# 訪問此網址查看官方下載
https://www.python.org/downloads/release/python-3120/
```

### 驗證 Chromium
```bash
# 訪問此網址查看官方構建
https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html?prefix=Win_x64/
```

### 驗證 ChromeDriver
```bash
# 訪問此網址查看官方下載
https://googlechromelabs.github.io/chrome-for-testing/
```

---

## ❓ 為什麼批文件中看不到這些網址？

**原因**：
- 批文件（.bat）只是一個 **調用程式**
- 真正的下載邏輯在 **Python 腳本**（.py）中
- 批文件主要負責：
  - 檢查 Python 是否存在
  - 調用 Python 腳本
  - 顯示執行結果

**所以**：
- 批文件看不到網址 ✓ 正常
- 但 Python 腳本中有所有網址 ✓ 完全透明

---

## 📖 查看完整代碼

如果您想驗證所有下載邏輯，請打開：

```
auto_download_and_install.py
```

搜索以下函數，會看到所有網址：
- `download_python()` - 第 71 行
- `download_chrome()` - 第 140 行
- `download_chromedriver()` - 第 200 行

---

## 💡 完全離線替代方案

如果您不信任任何自動下載，可以：

1. **在有網絡的電腦上手動下載**：
   - python-3.12.0-embed-amd64.zip
   - chrome-win64.zip
   - chromedriver.exe

2. **複製到隔離平台**

3. **腳本會自動檢測**到這些檔案，無需重新下載 ✅

---

## ✅ 總結

| 項目 | 詳情 |
|------|------|
| **下載總數** | 3 個軟體 + Selenium 庫 |
| **來源** | 全部官方 |
| **大小** | ~140-260 MB |
| **安全性** | ✅ 官方開源軟體 |
| **可追蹤性** | ✅ 網址完全公開 |
| **驗證方式** | ✅ 可手動驗證每個網址 |

**結論**：完全透明、可驗證、安全可靠！ 🎯

---

有任何問題或需要驗證具體網址，請隨時詢問！

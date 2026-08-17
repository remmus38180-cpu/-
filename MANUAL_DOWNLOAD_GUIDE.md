# 📥 手動下載指南（在有網絡的電腦上）

> 當隔離平台沒有 Python 時的解決方案

---

## 🎯 三步驟快速指南

### 第 1 步：在有網絡的電腦上下載

#### 檔案 A：Python 3.12.0 便攜版 ⭐ 最簡單

```
網址：https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip
檔案名：python-3.12.0-embed-amd64.zip
大小：約 30-50 MB
```

**瀏覽器下載方式**：
1. 在瀏覽器中打開上方網址
2. 右鍵點擊頁面 → 「另存連結為」或「Save Link As」
3. 選擇本機位置
4. 點擊儲存

✅ 最簡單！直接用瀏覽器下載即可

---

#### 檔案 B：Chromium 瀏覽器

```
網址：https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win_x64/LAST_CHANGE
步驟：
  1. 訪問上方網址
  2. 記下顯示的數字（例如：1234567）
  3. 使用這個數字訪問：
     https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win_x64/{數字}/chrome-win64.zip
  4. 下載 chrome-win64.zip
```

**或簡化方式** ✓ 使用最新版本連結：

```
https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html?prefix=Win_x64/
(上方頁面會列出最新的構建)
```

大小：約 100-200 MB

---

#### 檔案 C：ChromeDriver

```
網址：https://googlechromelabs.github.io/chrome-for-testing/
步驟：
  1. 訪問上方網址
  2. 找到最新版本的 "chromedriver" - "win64"
  3. 下載 chromedriver.zip
  4. 解壓得到 chromedriver.exe
```

大小：約 5-10 MB

---

### 第 2 步：轉移到隔離平台

將以下檔案複製到隔離平台的工作目錄：

```
您的隔離平台工作目錄/
├── python-3.12.0-embed-amd64.zip
├── chrome-win64.zip （或已解壓的檔案夾）
├── chromedriver.exe
├── drug_price_screenshot_selenium.py
├── drug_list.csv
└── auto_download_and_install.py
```

---

### 第 3 步：在隔離平台上執行

#### 方式 A：先解壓 Python，然後執行

```bash
# 1. 解壓 Python
解壓 python-3.12.0-embed-amd64.zip 到 python_portable/

# 2. 執行腳本
python_portable\python.exe auto_download_and_install.py
```

#### 方式 B：解壓所有檔案，然後執行批文件

```bash
# 1. 解壓所有 ZIP 檔案
python_portable/python.exe
chrome_portable/chrome.exe
chromedriver.exe

# 2. 執行
auto_download_and_install.bat
```

---

## 📊 完整清單

| 檔案 | 大小 | 必需嗎 | 下載方式 | 說明 |
|------|------|--------|---------|------|
| python-3.12.0-embed-amd64.zip | 30-50 MB | ✅ 是 | 瀏覽器直接下載 | **必須先下載** |
| chrome-win64.zip | 100-200 MB | ⭐ 可選 | 瀏覽器直接下載 | 如果已安裝 Chrome 可不下 |
| chromedriver.exe | 5-10 MB | ⭐ 可選 | 瀏覽器直接下載 | 腳本會自動配對 |
| Selenium | - | ✅ 自動* | pip 自動下載 | 不需手動下載 |

*注：Selenium 由 Python 的 pip 自動從 PyPI 下載安裝，無需手動下載（只要隔離平台有網絡）

---

## 🌐 瀏覽器下載方法（最簡單！）

### 為什麼用瀏覽器？
- ✅ 最簡單 - 無需命令行
- ✅ 直觀 - GUI 界面
- ✅ 可靠 - 瀏覽器內置下載功能
- ✅ 檢查 - 可看到下載進度和檔案大小

### 通用步驟（所有 ZIP 檔案都相同）

```
1. 複製下方的網址到瀏覽器網址列
2. 按 Enter 打開網址
3. 瀏覽器會開始下載
   OR
   右鍵點擊 → 「另存連結為」→ 選擇位置 → 儲存
4. 等待下載完成
5. 檢查本機是否有該 ZIP 檔案
```

### 各系統的操作

**Windows 瀏覽器**（Edge/Chrome/Firefox）：
```
1. 複製網址到網址列
2. 按 Enter
3. 如果出現下載提示，點「儲存」
4. 檔案會下載到「下載」資料夾
```

**macOS/Linux**（如果您在那邊操作）：
```
1. 複製網址
2. 瀏覽器會自動下載
3. 檢查「下載」資料夾
```

---

## 🔗 直接下載連結

### ✅ 推薦：Python（最重要）

```
https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip
```

**點擊上方連結直接下載** ✓

### ⚠️ Chrome/Chromium（需要查詢版本）

```
https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win_x64/LAST_CHANGE
```

上方網址會返回最新版本號，然後使用這個號碼下載：

```
https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win_x64/{BUILD_NUMBER}/chrome-win64.zip
```

### ⚠️ ChromeDriver（較複雜）

```
https://googlechromelabs.github.io/chrome-for-testing/
```

需要從頁面上找到對應版本的下載連結。

---

## 💡 簡化方案

**如果上方連結太複雜，只需下載 Python**：

```
https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip
```

然後在隔離平台上執行：

```bash
python_portable\python.exe auto_download_and_install.py
```

腳本會自動下載其他檔案！ ✅

（雖然會很慢，因為隔離平台要下載 Chrome 和 ChromeDriver）

---

## 🎯 最小化方案

**僅需 1 個檔案**：

```
python-3.12.0-embed-amd64.zip
```

下載方式：
1. 訪問 https://www.python.org/downloads/
2. 搜索 "3.12.0"
3. 下載 "Windows embeddable package (64-bit)"

---

## ✅ 執行檢查清單

下載完成後，檢查：

```
您的工作目錄/
□ python_portable/ （或 python-3.12.0-embed-amd64.zip）
□ drug_price_screenshot_selenium.py
□ drug_list.csv
□ auto_download_and_install.py
```

完成後執行：

```bash
python_portable\python.exe auto_download_and_install.py
```

---

## 🆘 如果下載困難

如果您無法從上方連結下載，可以：

1. **使用備用搜尋**：
   - 搜尋 "python 3.12 embedded windows 64"
   - 搜尋 "chromium latest release win64"

2. **使用任何 Python 版本**：
   - 如果您找到其他版本的 Python，也可以使用
   - 腳本會自動適應

3. **聯絡我**：
   - 告訴我您面臨的具體問題
   - 我可以提供替代方案

---

## 📋 網速參考

| 情況 | 時間 |
|------|------|
| 只下載 Python | 5-15 分鐘 |
| 下載 Python + Chrome | 30-60 分鐘 |
| 下載全部 3 個檔案 | 45-90 分鐘 |

---

**建議**：先下載 Python，其他檔案可以在隔離平台上讓腳本自動下載！ 🚀

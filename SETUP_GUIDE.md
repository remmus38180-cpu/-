# 國際藥價自動截圖 - 設置指南

## 快速開始

如果你已經有以下檔案，只需執行一個命令：

```cmd
cd C:\Users\a110701\Downloads\test
C:\Users\a110701\AppData\Local\Programs\Python\Python312\python.exe auto_download_and_install_v3.py
```

## 準備工作

### 必需檔案清單

```
C:\Users\a110701\Downloads\test\
├── auto_download_and_install_v3.py      ✓ 自動安裝腳本
├── drug_price_screenshot_selenium.py    ✓ 主截圖程式
├── drug_list.csv                         ✓ 藥品清單
├── selenium-4.47.0-py3-none-any.whl     ✓ Selenium wheel (可選)
├── webdriver_manager-4.1.2-py3-none-any.whl  ✓ webdriver-manager wheel (可選)
├── chromedriver.exe                     ✓ ChromeDriver (自動下載或手動放置)
└── chrome_portable/                     ✓ Chrome (自動下載)
```

### 系統要求

- **Python 3.12.0** (標準安裝版本)
  - 位置: `C:\Users\a110701\AppData\Local\Programs\Python\Python312\`
  - 驗證: `python --version`

## 第一次設置流程

### 1️⃣ 安裝 Python 3.12.0

如果還沒安裝，從官方下載：
https://www.python.org/downloads/

```cmd
# 驗證 Python
python --version
python -m pip --version
```

### 2️⃣ 準備 wheel 檔案 (可選但推薦)

在有網路的電腦上下載：
- Selenium: https://pypi.org/project/selenium/#files
- webdriver-manager: https://pypi.org/project/webdriver-manager/#files

下載版本：
- `selenium-4.47.0-py3-none-any.whl`
- `webdriver_manager-4.1.2-py3-none-any.whl`

複製到隔離平台

### 3️⃣ 準備 ChromeDriver (可選)

也可以預先下載 ChromeDriver：
- 訪問: https://googlechromelabs.github.io/chrome-for-testing/
- 下載 Chrome 152 的 win64 版本
- 解壓 `chromedriver.exe` 到專案目錄

### 4️⃣ 執行自動腳本

```cmd
cd C:\Users\a110701\Downloads\test
C:\Users\a110701\AppData\Local\Programs\Python\Python312\python.exe auto_download_and_install_v3.py
```

## 隔離平台工作流程 (推薦)

### 明天重新開始的步驟

1. **從 git 克隆/拉取專案**
   ```cmd
   # 如果是第一次
   git clone <repo-url> test
   cd test
   
   # 如果已有專案
   cd test
   git pull
   ```

2. **一鍵執行**
   ```cmd
   C:\Users\a110701\AppData\Local\Programs\Python\Python312\python.exe auto_download_and_install_v3.py
   ```

3. **等待完成**
   - 檢查 wheel 檔案（本地安裝，很快）
   - 下載 Chrome（如果需要）
   - 下載 ChromeDriver（如果需要）
   - 執行截圖程式

## 腳本版本說明

### auto_download_and_install_v3.py ⭐ 推薦

**優點：**
- ✓ 優先使用本地 wheel 檔案（不需要網路）
- ✓ 網路不穩定時也能工作
- ✓ 最快的安裝速度
- ✓ 適合隔離平台

**何時使用：**
- 隔離平台 (沒有網路或網路被防火牆擋)
- 需要快速執行
- wheel 檔案已準備好

### auto_download_and_install_v2.py

**優點：**
- ✓ 更長的超時時間
- ✓ 自動重試機制
- ✓ 網路下載 Selenium

**何時使用：**
- 有穩定網路連接
- wheel 檔案不可用

### auto_download_and_install.py

原始版本，不推薦使用。

## 常見問題

### Q: 我的隔離平台沒有網路，怎麼辦？

A: 使用 v3 腳本 + 本地 wheel 檔案
1. 在有網路的電腦上下載 wheel 檔案
2. 複製到隔離平台
3. 執行 v3 腳本（優先使用本地 wheel）

### Q: 明天平台重製後，我需要重新做所有設置嗎？

A: 不需要！
1. `git pull` 獲取所有檔案（包括 wheel 和腳本）
2. 執行 `auto_download_and_install_v3.py`
3. 完成！

### Q: wheel 檔案需要提交到 git 嗎？

A: 可以，但不必須
- 如果提交：`git add *.whl`（檔案會比較大）
- 如果不提交：腳本會自動從網路下載（需要網路）
- 建議在隔離平台環境中提交到 git

### Q: 我想手動安裝 Selenium，怎麼做？

A: 只需執行一個 pip 命令
```cmd
python -m pip install selenium-4.47.0-py3-none-any.whl webdriver_manager-4.1.2-py3-none-any.whl
```

## 完整執行流程圖

```
開始
  ↓
偵測 Python 3.12.0
  ↓
查找本地 wheel 檔案
  ├─ 找到 → 本地安裝 Selenium (快速 ✓)
  └─ 未找到 → 從網路下載並安裝
  ↓
下載 Chrome (如果未下載)
  ↓
下載 ChromeDriver (如果未下載)
  ↓
檢查輸入檔案 (drug_list.csv 等)
  ↓
執行截圖程式
  ↓
完成！輸出存在 drug_price_screenshots/
```

## 相關檔案

- `auto_download_and_install_v3.py` - 推薦的自動安裝腳本
- `drug_price_screenshot_selenium.py` - 主截圖程式
- `drug_list.csv` - 藥品清單
- `one_click_setup.ps1` - PowerShell 一鍵安裝 (Windows)
- `one_click_setup.bat` - Batch 一鍵安裝 (Windows)

## 支援的國家

腳本支援查詢以下國家的藥價：
1. 日本 (JP)
2. 澳洲 (AU)
3. 比利時 (BE)
4. 法國 (FR)
5. 瑞典 (SE)
6. 瑞士 (CH)
7. 英國 (UK)
8. 加拿大 (CA)

## 提示和最佳實踐

1. **提前準備 wheel 檔案**
   - 在有網路的電腦上下載 wheel 檔案
   - 提交到 git
   - 隔離平台不需要網路就能使用

2. **檢查 drug_list.csv 的編碼**
   - 必須是 UTF-8 編碼
   - 每行一個藥品名稱

3. **設置正確的 Python 路徑**
   - 使用完整路徑以確保運行正確的 Python
   - 或設置系統環境變數

4. **監控截圖進度**
   - 共 8 個國家 × 藥品數量
   - 每個國家需要 5-10 分鐘
   - 總共需要 30-60 分鐘或更久

## 支援

如有問題，請檢查：
1. Python 是否正確安裝
2. wheel 檔案是否存在
3. drug_list.csv 是否正確
4. 網路連接 (如果沒有本地 wheel)

---

**最後更新**: 2026-08-17
**推薦腳本**: auto_download_and_install_v3.py

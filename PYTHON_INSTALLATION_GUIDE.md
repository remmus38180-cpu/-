# Windows Python 安裝指南

## 📥 下載 Python

### 方案 A: 使用您現有的 WinPython（推薦）

您已經有 WinPython 環境了！位置：
```
C:\Users\a110701\Downloads\WPy64-313130\
```

**檢查您已有的 Python 版本：**
1. 打開命令提示符（Windows + R，輸入 `cmd`）
2. 執行：
   ```bash
   C:\Users\a110701\Downloads\WPy64-313130\python.exe --version
   ```
3. 如果看到 `Python 3.x.x`，表示已可用

**✅ 這是最簡單的方式，直接用已有的 WinPython**

---

### 方案 B: 重新下載最新 Python（如果需要）

#### 官方 Python.org
1. 訪問 https://www.python.org/downloads/
2. 點擊 **"Download Python 3.13"**（或最新版本）
3. 選擇 **"Windows installer (64-bit)"**
4. 下載完成後運行安裝程式

#### 安裝步驟
1. 雙擊 `.exe` 檔案
2. **✅ 重要**：勾選 **"Add Python to PATH"**
3. 選擇 **"Install Now"**（推薦）或自訂安裝
4. 等待完成

#### 驗證安裝
```bash
# 打開命令提示符，執行：
python --version
# 應顯示 Python 3.x.x
```

---

#### Microsoft Store 安裝（簡單）
1. 打開 **Microsoft Store**
2. 搜尋 **"Python 3.13"**
3. 點擊 **"Get"** 安裝
4. 完成後在命令提示符驗證

---

## 🎯 推薦方案（最快）

**直接使用您現有的 WinPython：**

```bash
# 打開命令提示符，導航到工作目錄
cd C:\Users\a110701\Downloads\WPy64-313130\scripts

# 使用您的 Python 安裝 Selenium
.\python.exe -m pip install selenium

# 運行藥價截圖腳本
.\python.exe drug_price_screenshot_selenium.py --input drug_list.csv
```

---

## 📍 檔案位置確認

確保以下檔案在同一目錄：

```
C:\Users\a110701\Downloads\WPy64-313130\scripts\
├── python.exe (您的 Python)
├── pip.exe (包管理器)
├── drug_price_screenshot_selenium.py ✓ (您下載的)
├── drug_list.csv ✓ (您下載的)
└── chromedriver.exe ✓ (需下載)
```

---

## 🔧 Python 版本要求

- **最低版本**: Python 3.8
- **推薦版本**: Python 3.10+
- **檢查版本**:
  ```bash
  python --version
  ```

---

## ❓ 常見問題

### Q: 我應該下載哪個版本？
**答**: 
- Windows 10/11 64位（大多數現代電腦）→ **64-bit installer**
- 如果電腦很舊 32 位 → **32-bit installer**
- 查詢您的系統位數：Windows 設定 → 系統 → 關於

### Q: Python 放在哪裡？
**答**: 
- 安裝時選擇預設位置（通常 `C:\Users\您的用戶名\AppData\Local\Programs\Python\Python313\`）
- **勾選 "Add Python to PATH"** 就能從任何地方使用

### Q: 多個 Python 版本衝突？
**答**: 使用完整路徑指定版本
```bash
# 方案 A: 您的 WinPython
C:\Users\a110701\Downloads\WPy64-313130\python.exe --version

# 方案 B: 新安裝的 Python
C:\Users\您的用戶名\AppData\Local\Programs\Python\Python313\python.exe --version
```

### Q: "python: command not found"？
**答**: 
1. 重新安裝，勾選 **"Add Python to PATH"**
2. 重啟命令提示符
3. 或使用完整路徑執行

---

## ✅ 安裝驗證清單

在命令提示符執行以下命令，確認都有結果：

```bash
# 1. 檢查 Python
python --version
# 應顯示: Python 3.x.x

# 2. 檢查 pip
pip --version
# 應顯示: pip x.x.x from ...

# 3. 測試 pip 可用
pip list
# 應顯示已安裝的套件列表

# 4. 安裝 selenium
pip install selenium
# 應顯示 "Successfully installed"
```

---

## 🚀 確認後的下一步

安裝 Selenium 後，執行：
```bash
cd C:\Users\a110701\Downloads\WPy64-313130\scripts
python drug_price_screenshot_selenium.py --input drug_list.csv
```

**完成！** 等待 30-60 分鐘，截圖會保存在 `drug_price_screenshots/` 目錄。

---

## 💡 提示

- **建議用您已有的 WinPython**，無需重新安裝
- 新 Python 安裝需要 5 分鐘
- Microsoft Store 安裝最簡單，自動添加 PATH

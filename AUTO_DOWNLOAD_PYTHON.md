# 🚀 Python 自動下載腳本

> 一鍵自動下載 Python，無需手動操作

---

## 📌 三個版本可選

### 🥇 **推薦：PowerShell 版本（最簡單）**

```bash
download_python.bat
```

**優點**：
- ✅ 無需任何依賴（Windows 內置 PowerShell）
- ✅ 雙擊即可執行
- ✅ 自動顯示進度
- ✅ 最簡單

**缺點**：
- 可能需要允許 PowerShell 執行腳本

---

### 🥈 **如果系統已有 Python**

```bash
python download_python.py
```

**優點**：
- ✅ 如果已有 Python 可直接用
- ✅ 功能完整

**缺點**：
- ❌ 需要先有 Python（但沒有 Python 才是問題）

---

### 🥉 **備選：PowerShell 腳本直接執行**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File download_python.ps1
```

**優點**：
- ✅ 更多控制
- ✅ 可看到詳細過程

**缺點**：
- ❌ 需要手動在 PowerShell 中執行

---

## 🎯 最簡單方式（推薦）

### 第 1 步：雙擊執行

```
download_python.bat
```

### 第 2 步：等待下載完成

腳本會自動：
- ✓ 連接到 python.org
- ✓ 下載 Python 3.12.0
- ✓ 顯示下載進度
- ✓ 儲存到本機

### 第 3 步：檔案會出現在同一目錄

```
python-3.12.0-embed-amd64.zip
```

---

## ⚠️ 可能的問題和解決方案

### 問題 1：「無法運行 PowerShell 腳本」

**原因**：Windows PowerShell 執行策略限制

**解決**：
1. 右鍵點擊 `download_python.bat`
2. 選擇「以管理員身份執行」
3. 允許腳本執行

### 問題 2：「防火牆阻止下載」

**症狀**：腳本卡住或超時

**解決**：
1. 檢查防火牆設定
2. 或在瀏覽器中手動下載
3. 聯絡 IT 部門

### 問題 3：「無法連接到 python.org」

**症狀**：網絡錯誤

**解決**：
1. 檢查網絡連接
2. 嘗試在瀏覽器中訪問 python.org
3. 等待網絡恢復後重試

---

## 📊 腳本比較

| 功能 | PowerShell .bat | Python .py | PowerShell .ps1 |
|------|-----------------|-----------|-----------------|
| 無需依賴 | ✅ | ❌ | ✅ |
| 雙擊執行 | ✅ | ✅ | ❌ |
| 顯示進度 | ✅ | ✅ | ✅ |
| 易用性 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

---

## 🔍 腳本做什麼？

```
Step 1: 檢查下載位置
Step 2: 連接到 https://www.python.org/ftp/python/3.12.0/
Step 3: 下載 python-3.12.0-embed-amd64.zip
Step 4: 顯示進度和檔案大小
Step 5: 完成！
```

---

## ✅ 執行後

下載完成後，您會看到：

```
============================================================
[成功] 下載完成！
============================================================

檔案名稱: python-3.12.0-embed-amd64.zip
檔案大小: 42.50 MB
位置: C:\Users\...\python-3.12.0-embed-amd64.zip

接下來:
1. 將此檔案複製到隔離平台
2. 在隔離平台解壓
3. 執行 auto_download_and_install.py
```

---

## 🎯 後續步驟

1. **複製下載的 ZIP 檔案到隔離平台**

2. **在隔離平台解壓**：
   ```
   python_portable/
   ├── python.exe
   ├── Lib/
   └── ...
   ```

3. **在隔離平台執行自動安裝**：
   ```bash
   python_portable\python.exe auto_download_and_install.py
   ```

4. **完成！** ✅

---

## 💡 完整流程示意

```
您的電腦（有網絡）
    ↓
執行 download_python.bat
    ↓
自動下載 Python ZIP
    ↓
複製到隔離平台
    ↓
隔離平台：執行 auto_download_and_install.py
    ↓
自動下載 Chrome、ChromeDriver、Selenium
    ↓
執行截圖程式
    ↓
完成！ ✅
```

---

## 🆘 如果腳本不工作

### 檢查清單

- [ ] 已連接到網絡
- [ ] 能否在瀏覽器中訪問 https://www.python.org/
- [ ] 防火牆是否阻止下載
- [ ] 磁碟空間是否充足（至少 100 MB）

### 備選方案

如果腳本不工作，直接在瀏覽器中：

```
1. 打開: https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip
2. 右鍵 → 另存連結
3. 完成！
```

---

## 📝 技術細節

### PowerShell 腳本 (`download_python.ps1`)

```powershell
- 使用 Invoke-WebRequest 下載檔案
- 顯示下載進度
- 驗證檔案大小
- 提供錯誤處理
```

### Python 腳本 (`download_python.py`)

```python
- 使用 urllib.request 下載
- 自訂進度顯示
- 詳細的錯誤訊息
- 檔案驗證
```

### 批文件 (`download_python.bat`)

```batch
- 啟動 PowerShell
- 執行 .ps1 腳本
- 提供 Unicode 相容性
- 錯誤處理
```

---

## ✨ 總結

**推薦流程**：
1. ✅ 雙擊 `download_python.bat`
2. ✅ 等待下載完成
3. ✅ 複製到隔離平台
4. ✅ 執行 `auto_download_and_install.py`
5. ✅ 完成！

**無需手動操作任何下載鏈接！** 🎉

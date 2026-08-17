# 📦 Selenium 庫 - 您需要知道的

> 關於 Selenium 自動安裝的說明

---

## ❓ Selenium 是什麼？

Selenium 是一個 Python 庫，用於自動控制瀏覽器。

**在我們的腳本中的作用**：
- 自動打開 Chrome/Chromium 瀏覽器
- 自動訪問藥價查詢網站
- 自動截圖保存

---

## ✅ 您需要下載 Selenium 嗎？

**通常不需要！** ✅

**原因**：
- 腳本會自動執行：`pip install selenium --upgrade`
- Python 會自動從 PyPI（Python 官方包倉庫）下載並安裝
- 這是自動的，無需您手動操作

---

## 🎯 正常情況下的流程

```
Step 1: 下載 Python 並在隔離平台上執行腳本
Step 2: 腳本自動執行 pip install selenium
Step 3: Python 連接到 PyPI 下載 Selenium
Step 4: 自動安裝完成
Step 5: 腳本繼續執行
```

---

## ⚠️ 如果隔離平台無法訪問 PyPI

**症狀**：
```
ERROR: Could not find a version that satisfies the requirement selenium
```

**原因**：隔離平台防火牆阻止了 PyPI 訪問

**解決方案**：手動下載 Selenium 的 .whl 檔案

---

## 📥 手動下載 Selenium（如果需要）

### 步驟 1：在有網絡的電腦上下載

打開此網址（或在瀏覽器中搜尋「selenium pypi」）：
```
https://pypi.org/project/selenium/
```

在頁面上找到：
```
Files → selenium-4.X.X-py3-none-any.whl
```

**右鍵 → 另存連結 → 下載**

### 步驟 2：複製到隔離平台

```
您的隔離平台/
├── python_portable/
├── selenium-4.X.X-py3-none-any.whl  ← 複製此檔案
└── ...
```

### 步驟 3：手動安裝

在隔離平台執行：
```bash
python_portable\python.exe -m pip install selenium-4.X.X-py3-none-any.whl
```

---

## 💡 最小化方案

**如果不想手動下載 Selenium**：

1. 下載 Python（必須）
2. 在隔離平台上執行腳本，讓 pip 自動下載
3. 確保隔離平台有網絡連接

---

## 📊 Selenium 簡要信息

| 項目 | 信息 |
|------|------|
| **檔案類型** | Python 庫 (.whl 檔案) |
| **大小** | 約 5-10 MB |
| **通常安裝位置** | python_portable/Lib/site-packages/ |
| **需要手動下載嗎** | ❌ 通常不需要（pip 自動） |
| **如果網絡受限** | ✅ 需要手動下載 .whl 檔案 |

---

## 🔗 官方下載連結

```
https://pypi.org/project/selenium/
```

或直接下載最新版本：
```
https://files.pythonhosted.org/packages/...
```

（具體連結取決於最新版本號）

---

## ✅ 總結

| 情況 | 做法 |
|------|------|
| 隔離平台有正常網絡 | ✅ 無需做任何事 - pip 自動下載 |
| 隔離平台無法訪問 PyPI | 📥 需要手動下載 .whl 檔案 |
| 不確定隔離平台網絡 | 🔄 先試試，不行再手動下載 |

---

**99% 的情況下，您不需要手動下載 Selenium！** ✨

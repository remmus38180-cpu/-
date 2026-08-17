# 🚀 快速開始指南

> **完全自動化方案已準備好！** 只需一個命令即可執行

---

## ✨ 最簡單的方式

### 第一步：下載必要的檔案

從 GitHub 倉庫下載以下 **3 個檔案**：

```
1. drug_price_screenshot_selenium.py
2. drug_list.csv
3. auto_download_and_install.py (或 .bat)
```

### 第二步：執行

```bash
# Windows 命令提示符
python auto_download_and_install.py

# 或雙擊 Windows 檔案瀏覽器中的
auto_download_and_install.bat
```

### 第三步：等待完成

- **首次**: 60-90 分鐘（包括依賴下載）
- **之後**: 30-60 分鐘（只執行截圖）

---

## 🎯 會自動完成的事情

✅ 下載 Python（如果未安裝）
✅ 下載 Chrome/Chromium（如果未安裝）
✅ 下載 ChromeDriver（匹配版本）
✅ 安裝 Selenium 庫
✅ 執行國際藥價截圖
✅ 保存 80+ 個截圖到 `drug_price_screenshots/`

---

## 📊 預期結果

執行成功後，您會得到：

```
drug_price_screenshots/
├── JP_Exforge_search_results.png
├── AU_Exforge_search_results.png
├── UK_Exforge_search_results.png
├── FR_Exforge_search_results.png
├── ... (共 80 個截圖)
└── ... (8 國家 × 10 藥品)
```

**統計**:
- 8 個國家：日本(JP)、澳洲(AU)、比利時(BE)、法國(FR)、瑞典(SE)、瑞士(CH)、英國(UK)、加拿大(CA)
- 10 個藥品：Exforge、Dafiro、Dificid、Sunvepra 等
- 共 80 個截圖
- 磁碟空間需求：~100-150 MB

---

## 💡 自訂藥品清單

編輯 `drug_list.csv`，每行一個藥品名稱：

```csv
Exforge
Exforge HCT
Dafiro
Dafiro HCT
您要查詢的藥品
```

保存後重新執行腳本即可。

---

## 🆘 如果遇到問題

### 自動下載失敗？

**備用方案：** 使用手動版本
```bash
python auto_setup_and_run.py
```

### 網絡問題？

1. 檢查隔離平台網絡連接
2. 嘗試重新執行腳本
3. 如果持續失敗，在有網絡的電腦上手動下載依賴，然後上傳

### 其他問題？

請參考完整文檔：
- **README.md** - 詳細說明
- **DAILY_EXECUTION_GUIDE.md** - 每日執行指南

---

## 📋 完整檔案清單

### 核心檔案（必須）
- `drug_price_screenshot_selenium.py` - 主程式
- `drug_list.csv` - 藥品清單

### 執行腳本（選一個）
- `auto_download_and_install.py` ⭐ **推薦**（Python 版，自動下載一切）
- `auto_download_and_install.bat` ⭐ **推薦**（Windows 版，自動下載一切）
- `auto_setup_and_run.py`（備用：需要手動下載依賴）
- `auto_setup_and_run.bat`（備用：需要手動下載依賴）

### 文檔
- `README.md` - 完整說明
- `DAILY_EXECUTION_GUIDE.md` - 每日執行指南
- `QUICK_START.md` - 本檔案

### 完整包
- `drug_price_screenshot_package.zip` - 所有檔案打包

---

## 🌍 隔離平台每日執行流程

由於您的隔離平台每天重新安裝，以下是每天的流程：

### Day 1
1. 下載 3 個檔案到隔離平台
2. 執行 `python auto_download_and_install.py`
3. 等待 60-90 分鐘
4. 檢查 `drug_price_screenshots/` 目錄

### Day 2+（每天）
1. 將相同 3 個檔案上傳到新環境
2. 執行 `python auto_download_and_install.py`
3. 等待 30-60 分鐘（依賴已存在）
4. 完成！

---

## 🔗 相關資源

- **GitHub 倉庫**: https://github.com/remmus38180-cpu/-
- **藥品資訊來源**: 多個國家的官方藥價查詢網站
- **支援的國家**: JP, AU, BE, FR, SE, CH, UK, CA

---

## ⏱️ 時間管理提示

| 階段 | 時間 | 說明 |
|------|------|------|
| 首次下載依賴 | 10-20 分鐘 | Python + Chrome + ChromeDriver |
| 安裝 Selenium | 2-5 分鐘 | 自動執行 |
| 截圖執行 | 30-60 分鐘 | 取決於網絡速度 |
| **首次總計** | **60-90 分鐘** | **包括所有下載** |
| **之後每次** | **30-60 分鐘** | **只執行截圖** |

---

**祝您執行順利！** 🎉

有任何問題，請檢查 README.md 或 DAILY_EXECUTION_GUIDE.md。

# 📚 國際藥品價格下載工具 - 使用指南

## 快速開始

### 1. 執行完整下載流程

```bash
# 進入目錄
cd /tmp/claude-0/-home-user--/5bf81379-3462-5982-b865-e204e2eb2c1d/scratchpad

# 執行v2版本下載（含備選URL支持）
python3 download_drug_prices_v2.py
```

### 2. 搜索特定藥品

```bash
# 搜索Eliquis和Zelboraf
python3 search_drug_prices.py
```

### 3. 生成價格比較報告

```bash
# 生成詳細的價格分析報告
python3 final_price_report.py
```

---

## 詳細文檔

### 📥 download_drug_prices.py (v1.0)

**功能**: 從多個國家官方網站自動下載藥品價格檔案

**支持的國家**:
- 🇯🇵 日本 (MHLW)
- 🇸🇪 瑞典 (TLV)
- 🇧🇪 比利時 (INAMI)
- 🇨🇭 瑞士 (BAG)
- 🇫🇷 法國 (ANSM)
- 🇦🇺 澳洲 (PBS)

**使用方式**:
```bash
python3 download_drug_prices.py
```

**輸出**:
- 下載檔案保存至 `drug_prices/` 目錄
- 生成下載統計報告
- 顯示成功/失敗詳情

---

### 📥 download_drug_prices_v2.py (v2.0)

**改進功能**:
- ✅ 支持備選URL
- ✅ 日期格式自動調整
- ✅ 重試機制
- ✅ 詳細的錯誤日誌

**支持備選來源**:
```python
# 範例：日本數據
urls: [
    "主URL",
    "2025年12月版本",
    "2025年4月版本"
]
```

**使用方式**:
```bash
python3 download_drug_prices_v2.py
```

---

### 🔍 search_drug_prices.py

**功能**: 在已下載的藥價檔案中搜索特定藥品

**支持的格式**:
- Excel (.xlsx)
- 純文字 (.txt)
- 其他文本格式

**搜索邏輯**:
1. 逐行掃描檔案
2. 模糊匹配藥品名稱
3. 返回所有匹配記錄

**使用方式**:
```bash
python3 search_drug_prices.py
```

**輸出範例**:
```
🇸🇪 瑞典藥品資料庫搜索
✅ Eliquis: 找到 15 筆記錄
✅ Zelboraf: 找到 2 筆記錄
```

**自訂搜索**:
編輯檔案的 `search_drugs` 變數:
```python
search_drugs = [
    'Eliquis',
    'Zelboraf',
    '您的藥品名稱'
]
```

---

### 📊 extract_drug_details.py

**功能**: 提取藥品詳細信息和價格

**輸出欄位**:
- 藥品名稱
- 含量/規格
- 包裝詳情
- 劑型
- 廠商
- 藥局採購價 (AIP)
- 藥局零售價 (AUP)
- 單位價格

**使用方式**:
```bash
python3 extract_drug_details.py
```

**輸出範例**:
```
藥品名稱: Eliquis
含量: 2.5 mg
包裝: Blister, 168片
廠商: Bristol-Myers Squibb AB
單位價格: 9.70 SEK/片
```

---

### 📈 final_price_report.py

**功能**: 生成最終的價格比較報告

**特點**:
- ✅ 按含量分組
- ✅ 按單位價格排序
- ✅ 計算價格差異
- ✅ 標註最便宜的包裝
- ✅ 多廠商價格對比

**使用方式**:
```bash
python3 final_price_report.py
```

**報告內容**:
```
排名 商品編號 包裝 數量 總價 單位價 廠商
⭐ 1  119614  Blister, 168片  168  1630.20  9.70  Bristol-Myers Squibb
```

---

## 🔧 進階使用

### 修改下載清單

編輯 `download_drug_prices_v2.py`:

```python
downloads = [
    {
        "name": "藥品名稱",
        "urls": [
            "主URL",
            "備選URL1",
            "備選URL2",
        ],
        "filename": "輸出檔名.xlsx"
    },
]
```

### 添加新國家

1. 查詢官方網站URL
2. 在下載清單中添加:
```python
{
    "name": "🇩🇪 德國 - 新來源",
    "urls": ["https://..."],
    "filename": "10_Germany_NewSource.xlsx"
}
```

### 自訂搜索邏輯

在搜索腳本中修改搜索條件:

```python
# 模糊匹配
if drug_name.lower() in line.lower():
    # 找到了

# 精確匹配
if drug_name == line:
    # 找到了

# 正則表達式
import re
if re.search(r'Eliquis.*2\.5', line):
    # 找到了
```

---

## 💾 數據格式說明

### 瑞典TLV格式 (Excel)

| 欄位 | 說明 | 範例 |
|------|------|------|
| Produktnamn | 藥品名稱 | Eliquis |
| Varunummer | 商品編號 | 071521 |
| Styrka | 含量 | 2,5 mg |
| Förpackning | 包裝說明 | Blister, 60 tabletter |
| AIP | 藥局採購價 | 551.12 |
| AUP | 藥局零售價 | 613.15 |
| AIP per st | 單位採購價 | 9.19 |
| AUP per st | 單位零售價 | 10.22 |

### 法國ANSM格式 (純文字)

**分隔符**: Tab (制表符)  
**編碼**: CP1252  
**結構**: CIS + CIP (包含價格)

檔案組成:
- `CIS_bdpm.txt` - 藥品主檔
- `CIS_CIP_bdpm.txt` - 包裝及藥價檔

---

## 🐛 常見問題與排除

### Q1: 下載失敗 (404 Not Found)

**原因**: 官方URL可能已更新

**解決方案**:
1. 訪問官方網站確認新URL
2. 使用v2版本的備選URL功能
3. 在下載清單中更新URL

### Q2: 藥品搜索不到

**原因**: 
- 藥品名稱拼寫不同
- 藥品在該國不上市
- 檔案編碼問題

**解決方案**:
1. 確認正確的藥品名稱（可試試搜索部分名稱）
2. 嘗試搜索通用名或ATC代碼
3. 檢查檔案編碼設定

### Q3: 數字格式錯誤

**原因**: 歐洲格式使用逗號作為小數點分隔符

**解決方案**:
```python
# 自動轉換
price_str = price_str.replace(',', '.')
price = float(price_str)
```

### Q4: 記憶體不足

**原因**: 大型檔案載入到記憶體

**解決方案**:
```python
# 使用串流處理
with open(file, 'r') as f:
    for line in f:
        # 逐行處理
```

---

## 📈 擴展功能想法

### 1. 數據庫儲存
```python
import sqlite3
# 將下載的數據存入本地數據庫
# 支持快速查詢和歷史追蹤
```

### 2. 定時更新
```python
import schedule
# 每週自動更新藥價數據
schedule.every().monday.at("10:00").do(download_prices)
```

### 3. 匯率換算
```python
# 不同國家價格換算為統一貨幣
USD = price_SEK / exchange_rate
```

### 4. 價格追蹤
```python
# 比較歷史價格變動
current_price = 100
previous_price = 95
change = ((current_price - previous_price) / previous_price) * 100
```

### 5. 報告導出
```python
# 導出為PDF、CSV等格式
report.to_pdf('price_report.pdf')
report.to_csv('price_data.csv')
```

---

## 📞 技術支持

### 依賴項
- Python 3.6+
- openpyxl (Excel支持)
- urllib (內置)

### 環境設置
```bash
# 安裝依賴
pip3 install openpyxl

# 驗證安裝
python3 -c "import openpyxl; print('✅ openpyxl installed')"
```

### 執行環境
- 支持: Windows, macOS, Linux
- Python: 3.6, 3.7, 3.8, 3.9, 3.10+

---

## 📝 版本歷史

| 版本 | 日期 | 改進 |
|------|------|------|
| v1.0 | 2026-08-18 | 初始版本，支持多國下載 |
| v2.0 | 2026-08-18 | 添加備選URL、重試機制 |

---

**最後更新**: 2026年8月18日  
**作者**: Claude Code  
**狀態**: ✨ 完全可用

# 國際藥價整批下載與查詢系統

本系統整合了8個國家的官方藥價資料下載腳本，並提供統一的藥品查詢引擎。

## 📦 專案結構

```
.
├── scripts/                           # 各國下載腳本
│   ├── download_japan_mhlw.py        # 日本厚生勞動省
│   ├── convert_sweden_tlv.py         # 瑞典TLV
│   ├── download_australia_pbs.py     # 澳洲PBS
│   ├── download_belgium_inami.py     # 比利時INAMI
│   ├── download_switzerland_bag.py   # 瑞士BAG
│   ├── download_uk_dmd.py            # 英國dm+d
│   ├── merge_cip_files.py            # 法國CIP（藥局用藥）
│   └── download_ucd_files.py         # 法國UCD（醫院用藥）
├── query_drug_prices.py              # 主查詢引擎 ⭐
├── drug_price_data/                  # 下載資料存放目錄
└── README.md                         # 本文檔
```

## 🚀 快速開始

### 步驟 1：下載各國藥價資料

```bash
python3 query_drug_prices.py --download
```

預期執行時間：3-10 分鐘（視網路速度）

執行內容：
- ✅ 日本：MHLW 藥價基準（內用藥）
- ✅ 瑞典：TLV 整批藥價資料庫
- ✅ 澳洲：PBS API CSV 整批檔
- ✅ 比利時：INAMI 每月參考檔
- ✅ 瑞士：BAG 特殊性清單
- ✅ 法國CIP：公開藥品資料庫（藥局用）

### 步驟 2：查詢藥品價格

```bash
python3 query_drug_prices.py
```

系統會搜尋：
- Eliquis Film-Coated Tablet 2.5mg
- Eliquis Film-Coated Tablet 5mg
- Zelboraf film-coated tablets 240mg

## 📋 環境要求

- Python 3.6+
- 網路連線
- WinPython 用戶（Windows）或任何 Python 3 環境

## 💾 檔案清單

| 檔案 | 用途 |
|------|------|
| query_drug_prices.py | 主查詢引擎 - 下載+查詢所有國家藥價 |
| scripts/ | 各國下載腳本存放目錄 |
| drug_price_data/ | 下載資料輸出目錄 |
| drug_query_report.txt | 查詢結果報告（自動生成） |

---

**最後更新：2026-08-18**
**分支：claude/drug-price-query-script-v67tqp**

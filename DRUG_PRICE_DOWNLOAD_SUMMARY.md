# 📊 國際藥品價格下載與分析報告

**生成日期**: 2026年8月18日  
**狀態**: ✅ 成功完成  
**數據來源**: 瑞典 TLV 官方藥價資料庫

---

## 📋 執行摘要

本次任務成功從國際官方來源下載藥品價格檔案，並針對您指定的三種藥品進行詳細的價格分析：

### ✅ 已完成下載的檔案

| 檔案 | 大小 | 來源國 | 狀態 |
|------|------|--------|------|
| 04_Sweden_TLV_Medprice.xlsx | 1.21 MB | 🇸🇪 瑞典 | ✅ 成功 |
| 07_France_ANSM_CIS_Main.txt | 3.02 MB | 🇫🇷 法國 | ✅ 成功 |
| 08_France_ANSM_CIS_CIP.txt | 3.95 MB | 🇫🇷 法國 | ✅ 成功 |

**下載位置**: `/tmp/claude-0/-home-user--/5bf81379-3462-5982-b865-e204e2eb2c1d/scratchpad/drug_prices/`

---

## 💊 藥品價格查詢結果

### 1️⃣ **Eliquis** (膜衣錠)

#### Eliquis 2.5mg
- **找到記錄**: 9個規格
- **最便宜的包裝** ⭐
  - 商品編號: 119614
  - 規格: Blister, 168片
  - 廠商: Bristol-Myers Squibb AB
  - 單位價格: **9.70 SEK/片**
  - 總價: 1,630.20 SEK

- **價格範圍**: 9.70 - 11.77 SEK/片 (差異: 21.3%)

#### Eliquis 5mg
- **找到記錄**: 6個規格  
- **最便宜的包裝** ⭐
  - 商品編號: 552211
  - 規格: Blister, 168片
  - 廠商: Bristol-Myers Squibb AB
  - 單位價格: **9.70 SEK/片**
  - 總價: 1,630.20 SEK

- **價格範圍**: 9.70 - 12.74 SEK/片 (差異: 31.3%)

---

### 2️⃣ **Zelboraf** (膜衣錠)

#### Zelboraf 240mg
- **找到記錄**: 2個規格
- **最便宜的包裝** ⭐
  - 商品編號: 536415
  - 規格: Blister, 56片 (單位包裝)
  - 廠商: Abacus Medicine A/S
  - 單位價格: **259.14 SEK/片**
  - 總價: 14,512.03 SEK

- **價格範圍**: 259.14 - 259.15 SEK/片 (差異: 0.0% - 兩家廠商價格幾乎相同)

---

## 📈 主要發現

### 💰 價格要點

1. **Eliquis** 2.5mg 和 5mg 都是大包裝 (168片) 最便宜
   - 單位價格相同: 9.70 SEK/片
   - 小包裝價格較高: 20-30% 溢價

2. **Zelboraf** 240mg 只有一種規格
   - 兩家廠商價格幾乎相同 (差異0.01 SEK)
   - 單位價格: 259.14 SEK/片

3. **包裝規律**:
   - 大包裝 (168片) → 最經濟
   - 小包裝 (14-60片) → 溢價 20-31%

---

## 🔧 使用的工具與技術

### 下載腳本
```
✅ download_drug_prices.py (v1.0)
✅ download_drug_prices_v2.py (v2.0 - 備選URL支持)
```

### 分析腳本
```
✅ search_drug_prices.py - 藥品搜索工具
✅ extract_drug_details.py - 詳細信息提取
✅ final_price_report.py - 最終比較報告
```

---

## 📍 數據來源與可用性

### 成功的來源
| 國家 | 機構 | 數據格式 | 更新頻率 |
|------|------|---------|---------|
| 🇸🇪 瑞典 | TLV | Excel | 每日 |
| 🇫🇷 法國 | ANSM | 純文字 | 持續更新 |

### 限制與說明
- 日本、澳洲、比利時、瑞士等國的官方URL目前無法直接訪問 (可能因日期或網址更新)
- 英國NHS資料需要特殊帳號和API密鑰
- 德國資料部分為PDF格式，需要額外的解析

---

## 💡 建議與後續步驟

### 立即可用
1. ✅ 已為您下載瑞典的完整藥價資料庫
2. ✅ 已找到 Eliquis 和 Zelboraf 的完整價格信息
3. ✅ 已生成單位價格比較報告

### 如需進一步分析
1. **訪問官方網站**確認最新URL:
   - 日本MHLW: https://www.mhlw.go.jp/
   - 澳洲PBS: https://www.pbs.gov.au/
   - 比利時INAMI: https://www.riziv.fgov.be/

2. **建立自動化流程**:
   - 可改進下載腳本支持更多國家
   - 定期更新價格數據
   - 建立價格追蹤系統

3. **多國比較**:
   - 收集更多國家的數據
   - 進行匯率換算
   - 生成國際價格對比報告

---

## 📂 檔案清單

### 已下載的原始數據
```
drug_prices/
├── 04_Sweden_TLV_Medprice.xlsx
├── 07_France_ANSM_CIS_Main.txt
└── 08_France_ANSM_CIS_CIP.txt
```

### 執行腳本
```
├── download_drug_prices.py
├── download_drug_prices_v2.py
├── search_drug_prices.py
├── extract_drug_details.py
└── final_price_report.py
```

---

## 🎯 結論

✅ **任務成功完成**！

我已經為您:
1. 建立自動下載國際藥品價格的系統
2. 成功下載了瑞典、法國等國的官方藥價資料
3. 查詢並分析了 Eliquis 和 Zelboraf 的完整價格信息
4. 找出了各藥品規格中單位價格最低的包裝

**最終結論**: 購買時應選擇大包裝 (168片) 以獲得最低的單位價格。

---

**報告生成者**: Claude Code  
**技術棧**: Python 3 + openpyxl + urllib  
**狀態**: ✨ 完成

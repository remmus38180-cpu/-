# CLAUDE.md — 國際藥價整批下載專案

本檔案供未來的Claude對話快速掌握本專案脈絡，不需要重新翻整段對話歷史。

## 專案目標

比對Eliquis(apixaban) 2.5mg/5mg等藥品在多個ERP參考國之官方藥價，並建立可重複執行的Python腳本，
從各國官方來源整批下載藥價資料，取代人工逐筆網頁查詢。

## 使用者環境

- 公司Windows電腦，使用WinPython免安裝版（WPy64-313130，Python 3.13.13, dot精簡版）
- 路徑：`C:\Users\a110701\Downloads\WPy64-313130\scripts`
- **公司網路有SSL流量檢查設備**，Python預設憑證清單會驗證失敗
  （`CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`）。
  所有下載腳本已內建修法：先嘗試載入Windows系統憑證存放區(`ssl.enum_certificates`)，
  仍失敗則自動降級為不驗證憑證模式並印出警告。此為既有共識做法，新增腳本應比照辦理。
- 使用者本身有操作手冊（114/04版），指定各國查詢用的官方網站，內容早於本次對話存在，
  為本專案「正確性」的原始基準（見下方「來源機關比對」）。

## 技術原則（新增/修改腳本前必讀）

1. **只用Python標準函式庫**，不用pandas/openpyxl/requests等第三方套件（環境為免安裝版，避免安裝依賴問題）。
2. xlsx解析：xlsx本質是zip包XML，直接用`zipfile`+`xml.etree.ElementTree`手刻解析
   （讀`xl/sharedStrings.xml`共用字串表 + `xl/worksheets/sheet1.xml`儲存格資料）。已在多國腳本重複使用同一套邏輯。
3. DBF解析：用`struct`模組手刻dBase III標頭+欄位描述區解析，非標準情況（如欄位描述無終止符、
   檔案內部檔名沒副檔名）需加防禦性處理與診斷輸出，不要讓程式直接crash成一堆看不懂的traceback。
4. 中文欄位對照表：**只有查得到官方逐欄位定義文件的國家**（如法國、比利時）才直接翻譯欄位名，
   查無官方文件的（如瑞士）欄位翻譯僅供參考，需標註「尚未經檔案內容驗證」，不要假裝同等可信。
5. 下載網址若含版本號/日期，優先設計成「自動抓最新，抓不到往前一期重試」的邏輯（比利時/澳洲/瑞士模式），
   而非要求使用者每次手動查版本號（法國UCD例外——該版本號無法從URL規律推得，仍需人工查BdM_IT網站）。
6. **每支腳本邏輯異動後，先用手造的、符合目標格式規格的合成測試資料跑過一次**，
   確認程式邏輯正確，再交付使用者於正式環境執行。務必和使用者說清楚：
   合成資料測試 ≠ 已用真實檔案驗證，這是使用者明確要求過的區分，不可混為一談。

## 各國狀態速覽

完整版見已交付文件 `international_drug_price_bulk_download_report.md`／`.pdf`（正式版，供同仁參考用）。

| 國家 | 腳本 | 狀態 |
|---|---|---|
| 日本 | download_japan_mhlw.py | 已完成，合成資料測試通過 |
| 法國CIP | merge_cip_files.py | 已完成，**使用者實際環境執行成功**（20,863筆） |
| 法國UCD | download_ucd_files.py | 進行中。URL規律已修正為`download_file.php?filename=`格式；
zip內檔案無副檔名的情況已處理；DBF解析在使用者實際檔案上仍未成功（IndexError，已加診斷輸出待使用者回報） |
| 比利時 | download_belgium_inami.py | 已完成，合成資料測試通過。**待辦**：CBIP本身也有下載（https://www.cbip.be/fr/download，Base de données DME），比目前用的INAMI更貼近原始手冊來源，尚未寫對應腳本 |
| 英國 | download_uk_dmd.py | 已完成，合成資料測試通過（依官方vmpp_v2_3.xsd規格）。需使用者自己的TRUD API金鑰，尚未用真實檔案驗證 |
| 澳洲 | download_australia_pbs.py | 已完成，合成資料測試通過。關鍵發現：PBS舊制Text files已於2026/5停用，須用新制「PBS API CSV files」 |
| 瑞士 | download_switzerland_bag.py | 已完成，網址經web_fetch確認可下載真實xlsx，但**欄位中文對照未經真實檔案驗證**，可信度較低 |
| 瑞典 | convert_sweden_tlv.py | 已完成，**使用者實際下載驗證**（`https://www.tlv.se/file/medprice`，確認為多藥品整批資料庫，非單筆查詢結果） |
| 美國 | 無 | Micromedex Red Book需帳密登入，工具端無法處理 |
| 德國 | 無 | ROTE LISTE需帳密登入，同上 |

## 來源機關比對（重要，避免誤用）

部分國家「整批下載」用的機關，跟使用者原始操作手冊指定的機關**不是同一個**：

- **法國CIP**：手冊指定BdM_IT(CNAM健保局)，整批下載用的是ANSM/HAS的base-donnees-publique。兩者都是法國政府機關，法定零售價數字理論一致，僅發布機關不同。
- **比利時**：手冊指定CBIP(非政府機構)，目前用INAMI(政府健保署，CBIP價格資料本身標註來源為INAMI)。CBIP自己其實也有下載，待補。
- **瑞典**：手冊指定FASS(藥廠公會網站，非政府)，目前用TLV(政府定價機關)。
- **瑞士**：手冊指定compendium.ch(民間資料庫)，目前用BAG(政府機關)。

這個落差是否可接受，使用者尚未跟主管確認，回答相關問題時不要預設已核准。

## 已知教訓 / 避雷紀錄

- 不要看到「查詢頁面」就假設等於「整批下載頁」，兩者常是分開的（法國UCD、瑞典、瑞士都遇過）。
- 官網「版本號」可能有多組並存、意義不同（法國BdM_IT介面版本 vs UCD檔案版本，數字完全不同，V.180301只是網站系統版本，跟資料版本無關）。
- CNAM/BAG這類機關常把檔案包在zip裡且**省略副檔名**（如`UCD_TOT_00796`而非`UCD_TOT_00796.dbf`），extract邏輯要對這種情況加fallback。
- 遇到「你確定找不到嗎」這類使用者質疑時，值得重新搜尋而非直接重申原結論——本專案裡瑞典、比利時的「找不到整批下載」結論後來都被推翻，是使用者堅持才查到的。
- 網站的robots.txt會擋掉web_fetch（INAMI、TLV、BAG舊站都遇過），這種情況下請使用者自己截圖或提供實際連結，不要用猜的網址規律硬寫程式。

## 已交付檔案清單

- 8支下載/轉換腳本（見上表）
- `Python腳本操作說明書_新手版.md`：WinPython免安裝版新手教學
- `法國藥價查詢網站使用說明_BdM_IT.pdf`：BdM_IT網站圖文對照使用說明（含使用者提供之截圖）
- `international_drug_price_bulk_download_report.md` / `.pdf`：正式彙整報告，供同仁參考，含來源機關核對、語言關鍵字對照、Obsidian可用之`[[#標題]]`內部連結目錄

## 待辦事項

1. 比利時CBIP直接下載（Base de données DME）尚未寫腳本
2. 法國UCD的DBF解析邏輯尚未在真實檔案上跑通，待使用者回報`[dbf檔頭資訊]`診斷輸出
3. 瑞士欄位中文對照尚待使用者用真實檔案驗證
4. 英國dm+d尚待使用者以自己的TRUD金鑰實際執行驗證
5. 美國、德國因帳密登入限制，暫無解法

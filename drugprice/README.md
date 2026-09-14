# 十國藥價批次下載工具（階段 1）

僅使用 Python 標準函式庫，不需要安裝任何套件。

## 快速使用

**一般同仁**：雙擊 `開啟藥價工具.bat`，會自動開啟網頁介面。

**命令列**（開發與疑難排解用）：

```
python -m drugprice list              列出可用國家
python -m drugprice check             連線與 robots.txt 體檢
python -m drugprice download SE FR    下載並轉換指定國家
python -m drugprice download --all    下載並轉換全部已接上的國家
python -m drugprice parse SE          只重新解析已下載的原始檔（不連網）
```

輸出：

```
raw/YYYY-MM-DD/<國別>/     原始檔（原封不動）＋ 每檔的中繼資料
raw/manifest.csv           所有原始檔的清單與 SHA-256
output/<國別>_藥價.csv     統一欄位的結果（UTF-8 BOM，Excel 可直接開）
```

## 十國狀態

| 代碼 | 國家 | 執行方式 | 來源 | 幣別 |
|---|---|---|---|---|
| JP | 日本 | 自動 | 厚生労働省 | JPY |
| FR | 法國（藥局零售） | 自動 | ANSM／HAS 公開藥品資料庫 | EUR |
| BE | 比利時 | 自動 | INAMI／RIZIV | EUR |
| SE | 瑞典 | 自動 | TLV | SEK |
| AU | 澳洲 | 自動 | PBS 公開 API | AUD |
| CA-SK | 加拿大薩克其萬省 | 自動 | Saskatchewan Drug Plan | CAD |
| DE | 德國 | 人工 | BfArM（僅 PDF） | EUR |
| CH | 瑞士 | 人工 | BAG（網址已失效） | CHF |
| UK | 英國 | 人工 | NHS TRUD（需 API 金鑰） | GBP |
| US | 美國 | 不涵蓋 | 無官方免費來源 | USD |

人工與不涵蓋的國家會在「人工待辦」分頁列出原因、操作步驟，
以及每個藥品可直接點開的查詢網址。詳見 `docs/十國工作流總表.md`。

## 模組結構

```
drugprice/
  core/
    net.py        連線：SSL 相容、robots.txt 遵循、速率限制、重試
    robots.py     robots.txt 解析（支援 * 與 $ 萬用字元）
    rawstore.py   原始檔留存與雜湊清單
    schema.py     統一欄位定義、價格類別、CSV 讀寫
    xlsx.py       以 zipfile + ElementTree 解析 xlsx
    textfile.py   分隔文字檔讀取（自動偵測編碼）
    units.py      含量、包裝數量、名稱的解析與正規化
  matching/
    scoring.py    候選排序的計分規則（介面說明也由這裡產生）
    kana.py       片假名轉羅馬字，供跨語言成分名比對
    matcher.py    候選收斂與排序，產生「排序依據」說明
    druglist.py   藥品清單讀取（純文字或 CSV，欄位名中英文皆可）
  web/
    server.py     本機網頁伺服器（http.server，只綁 127.0.0.1）
    workspace.py  工作狀態
    static/       單一頁面的操作介面
  sources/        各國轉換器，每國一個檔案
  countries.py    十國工作流總表（執行方式、人工步驟、查詢網址）
  registry.py     自動化來源登記表（新增一國只要改這裡）
  cli.py          命令列介面
```

## 三個設計原則

**價格類別不可混用。** 各國公布的不是同一種價格。瑞典有 AIP／AUP、
瑞士有 FAP／PP、法國有含與不含調劑費兩種、比利時依五種交付模式各有一組價格。
每一筆記錄都帶價格類別，單位藥價排序只在同一類別內進行。

**拆不出來就留空，不猜。** 包裝數量、含量解析不出來時留空並在備註保留原文，
由人處理。猜錯的包裝數量會讓單位藥價整個失真。

**原廠判定由人拍板，程式只給線索。** 五國中有四國的原始檔帶有官方的
原廠／學名藥註記，一併轉入「原廠註記」欄，但程式不據此自動選定。
排序會把最可能的擺前面，並在每一筆下方寫出「排序依據」——
分數是哪些條件加起來的、同分時先後怎麼決定的、哪些地方可信度較低。
規則說明與實際計分用的是同一張表，不會算一套講另一套。

## 測試

```
python -m unittest discover -s tests -v
```

測試使用合成資料驗證程式邏輯。**合成資料測試 ≠ 已用真實檔案驗證**，
兩者是不同的事。本階段五國的轉換器另已用各國真實檔案實際跑過，
結果記錄於 `docs/階段1_實作紀錄.md`。

# 十國藥價批次下載工具（階段 1）

僅使用 Python 標準函式庫，不需要安裝任何套件。

## 快速使用

雙擊 `執行藥價下載.bat`，或在命令列：

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

## 目前接上的國家

| 代碼 | 國家 | 來源機關 | 幣別 | 欄位對照依據 |
|---|---|---|---|---|
| JP | 日本 | 厚生労働省 | JPY | 官方文件 |
| FR | 法國（藥局零售） | ANSM／HAS 公開藥品資料庫 | EUR | 官方文件 |
| BE | 比利時 | INAMI／RIZIV | EUR | 官方文件 |
| SE | 瑞典 | TLV | SEK | 實際檔案驗證 |
| AU | 澳洲 | PBS 公開 API | AUD | 官方文件 |

尚未接上：法國 UCD、英國、瑞士、德國、加拿大薩省、美國（見 `python -m drugprice list`）。

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
  sources/        各國轉換器，每國一個檔案
  registry.py     國家登記表（新增一國只要改這裡）
  cli.py          命令列介面
```

## 三個設計原則

**價格類別不可混用。** 各國公布的不是同一種價格。瑞典有 AIP／AUP、
瑞士有 FAP／PP、法國有含與不含調劑費兩種、比利時依五種交付模式各有一組價格。
每一筆記錄都帶價格類別，單位藥價排序只在同一類別內進行。

**拆不出來就留空，不猜。** 包裝數量、含量解析不出來時留空並在備註保留原文，
由人處理。猜錯的包裝數量會讓單位藥價整個失真。

**原廠判定由人拍板，程式只給線索。** 五國的原始檔都有官方的原廠／學名藥註記，
一併轉入「原廠註記」欄，但程式不據此自動選定，由複核的人決定。

## 測試

```
python -m unittest discover -s tests -v
```

測試使用合成資料驗證程式邏輯。**合成資料測試 ≠ 已用真實檔案驗證**，
兩者是不同的事。本階段五國的轉換器另已用各國真實檔案實際跑過，
結果記錄於 `docs/階段1_實作紀錄.md`。

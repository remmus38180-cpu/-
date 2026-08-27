# -*- coding: utf-8 -*-
"""各國轉換器的共同介面。

每一國的轉換器都做兩件事：

* ``download(ctx)``　下載原始檔並存進留存區，回傳一份份 ``Downloaded``
* ``parse(ctx, downloaded)``　把原始檔轉成統一欄位的 ``PriceRecord``

分成兩步是刻意的：下載壞掉與解析壞掉是不同的問題，分開才好診斷；
而且原始檔存下來之後，解析邏輯改了可以重跑，不必再去打擾人家的網站。

僅使用 Python 標準函式庫。
"""

import dataclasses

from ..core.schema import SourceTrack

__all__ = ["Downloaded", "Context", "Source"]


@dataclasses.dataclass
class Downloaded:
    """一個已存入留存區的原始檔。"""

    path: str            # 留存區內的絕對路徑
    rel_path: str        # 相對於留存區根目錄
    sha256: str
    source_url: str
    data_version: str = ""
    label: str = ""      # 用途說明，例如「藥品主檔」
    ssl_mode: str = ""


class Context:
    """一次執行所需的共用物件。"""

    def __init__(self, fetcher, store, log=None):
        self.fetcher = fetcher
        self.store = store
        self.log = log or (lambda msg: print(msg))


class Source:
    """各國轉換器的基底類別。"""

    country = ""
    country_name = ""
    agency = ""
    track = SourceTrack.BATCH
    currency = ""
    # 這一國的欄位對照是否有官方逐欄位定義文件佐證
    field_confidence = ""
    # 官方欄位說明文件網址，留空表示查無
    field_doc_url = ""
    # 連線體檢用的網址：能代表這個來源是否還活著的一個位址
    probe_url = ""

    def probe_headers(self):
        """體檢請求需要的額外標頭（如 API 金鑰）。"""
        return None

    def download(self, ctx):
        raise NotImplementedError

    def parse(self, ctx, downloaded):
        raise NotImplementedError

    def run(self, ctx):
        """下載並解析，回傳 (記錄清單, 原始檔清單)。"""
        ctx.log(f"=== {self.country_name}（{self.agency}）===")
        files = self.download(ctx)
        records = self.parse(ctx, files)
        ctx.log(f"　完成：{len(records):,} 筆")
        return records, files

    def _base_record(self, downloaded):
        """建立帶有來源與佐證欄位的空白記錄，各國再填上藥品資料。"""
        from ..core.schema import PriceRecord, now_stamp
        return PriceRecord(
            country=self.country,
            country_name=self.country_name,
            source_agency=self.agency,
            source_track=self.track,
            currency=self.currency,
            data_version=downloaded.data_version,
            downloaded_at=now_stamp(),
            source_url=downloaded.source_url,
            source_file=downloaded.rel_path,
            source_sha256=downloaded.sha256,
            field_confidence=self.field_confidence,
        )

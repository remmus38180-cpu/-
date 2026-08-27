# -*- coding: utf-8 -*-
"""分隔文字檔讀取，含編碼自動偵測。

**不要假設同一個來源的檔案編碼一致。** 法國 base-donnees-publique 的三個
檔案由同一個下載端點提供，但 ``CIS_bdpm.txt`` 與 ``CIS_GENER_bdpm.txt``
是 cp1252、``CIS_CIP_bdpm.txt`` 卻是 UTF-8。寫死 cp1252 會讓價格檔裡
所有法文重音字變成亂碼（``comprimé`` → ``comprimÃ©``）。

偵測方式：先用嚴格 UTF-8 解碼，失敗才依序退到 cp1252、latin-1。
UTF-8 的位元組結構嚴謹，非 UTF-8 的檔案幾乎必定解碼失敗，
所以這個順序不會誤判。

僅使用 Python 標準函式庫。
"""

__all__ = ["decode", "read_delimited"]

ENCODING_ORDER = ["utf-8", "cp1252", "latin-1"]


def decode(data, order=None):
    """把位元組解碼成字串，回傳 (文字, 實際使用的編碼)。"""
    for encoding in (order or ENCODING_ORDER):
        try:
            return data.decode(encoding), encoding
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("latin-1", "replace"), "latin-1（含無法辨識字元）"


def read_delimited(data, delimiter="\t", order=None):
    """解析無表頭的分隔文字檔，回傳 (列清單, 編碼)。

    每一列是欄位字串的清單，前後空白會去掉。空白列自動略過。
    """
    text, encoding = decode(data, order)
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        rows.append([field.strip() for field in line.split(delimiter)])
    return rows, encoding

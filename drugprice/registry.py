# -*- coding: utf-8 -*-
"""可用國家來源的登記表。

新增一國時，在這裡加一行即可，其餘程式不用改。
"""

from .sources import (australia_pbs, belgium_inami, canada_sk, france_cip,
                      japan_mhlw, sweden_tlv)

__all__ = ["SOURCES", "get", "codes"]

SOURCES = {
    "JP": japan_mhlw.SOURCE,
    "FR": france_cip.SOURCE,
    "BE": belgium_inami.SOURCE,
    "SE": sweden_tlv.SOURCE,
    "AU": australia_pbs.SOURCE,
    "CA-SK": canada_sk.SOURCE,
}

# 無法自動下載的國家。說明取自 countries.py，兩邊不會各說各話。
def _not_yet():
    from .countries import COUNTRIES, AUTO
    return {c.code: f"{c.name} — {c.reason.splitlines()[0] if c.reason else ''}"
            for c in COUNTRIES if c.method != AUTO}


NOT_YET = _not_yet()


def codes():
    return sorted(SOURCES)


def get(code):
    key = (code or "").strip().upper()
    if key not in SOURCES:
        available = "、".join(codes())
        raise KeyError(f"沒有這個國家代碼：{code}\n　可用的代碼：{available}")
    return SOURCES[key]

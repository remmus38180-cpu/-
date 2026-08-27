# -*- coding: utf-8 -*-
"""可用國家來源的登記表。

新增一國時，在這裡加一行即可，其餘程式不用改。
"""

from .sources import (australia_pbs, belgium_inami, france_cip,
                      japan_mhlw, sweden_tlv)

__all__ = ["SOURCES", "get", "codes"]

SOURCES = {
    "JP": japan_mhlw.SOURCE,
    "FR": france_cip.SOURCE,
    "BE": belgium_inami.SOURCE,
    "SE": sweden_tlv.SOURCE,
    "AU": australia_pbs.SOURCE,
}

# 尚未接上的國家，列出來讓使用者知道不是漏抓
NOT_YET = {
    "FR-UCD": "法國（醫院用 UCD）— DBF 解析尚在調整",
    "UK": "英國（NHS dm+d）— 需申請 TRUD 帳號與 API 金鑰",
    "CH": "瑞士（BAG）— 欄位對照待真實檔案驗證",
    "DE": "德國（BfArM／G-BA）— 尚未撰寫",
    "CA-SK": "加拿大薩克其萬省 — 查無官方整批下載，須人工",
    "US": "美國（Micromedex Red Book）— 需帳號密碼，本工具不涵蓋",
}


def codes():
    return sorted(SOURCES)


def get(code):
    key = (code or "").strip().upper()
    if key not in SOURCES:
        available = "、".join(codes())
        raise KeyError(f"沒有這個國家代碼：{code}\n　可用的代碼：{available}")
    return SOURCES[key]

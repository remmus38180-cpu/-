# -*- coding: utf-8 -*-
"""原始檔留存區。

處理後的結果是二手資料，**原始檔才是佐證的根**。每次下載都把檔案原封不動
存下來並計算 SHA-256，同時寫入清單檔，日後可驗證檔案未被抽換。

目錄結構::

    raw/
      2026-08-27/
        AU/
          items_4708.json
          items_4708.json.meta.json
      manifest.csv

僅使用 Python 標準函式庫。
"""

import csv
import hashlib
import json
import os
import re
from datetime import datetime

from .schema import TAIPEI, now_stamp

__all__ = ["RawStore"]

MANIFEST_COLUMNS = [
    "存檔時間", "國家", "來源軌別", "檔案", "位元組", "SHA-256",
    "來源網址", "HTTP狀態", "SSL驗證模式", "資料版本日期", "備註",
]

_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_name(name):
    """把字串轉成可用於檔名的形式。"""
    cleaned = _UNSAFE.sub("_", str(name)).strip().strip(".")
    return cleaned[:120] or "unnamed"


class RawStore:
    """原始檔存放與清單管理。"""

    def __init__(self, root="raw", run_date=None):
        self.root = os.path.abspath(root)
        self.run_date = run_date or datetime.now(TAIPEI).strftime("%Y-%m-%d")
        self.manifest_path = os.path.join(self.root, "manifest.csv")

    def dir_for(self, country):
        path = os.path.join(self.root, self.run_date, safe_name(country))
        os.makedirs(path, exist_ok=True)
        return path

    def save(self, country, filename, content, *, source_url="", status="",
             ssl_mode="", data_version="", source_track="A", notes=""):
        """存下一個原始檔，回傳 (相對路徑, sha256)。"""
        directory = self.dir_for(country)
        path = os.path.join(directory, safe_name(filename))
        with open(path, "wb") as fh:
            fh.write(content)

        digest = hashlib.sha256(content).hexdigest()
        stamp = now_stamp()
        meta = {
            "存檔時間": stamp,
            "國家": country,
            "來源軌別": source_track,
            "檔案": os.path.basename(path),
            "位元組": len(content),
            "SHA-256": digest,
            "來源網址": source_url,
            "HTTP狀態": status,
            "SSL驗證模式": ssl_mode,
            "資料版本日期": data_version,
            "備註": notes,
        }
        with open(path + ".meta.json", "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=2)

        self._append_manifest(meta)
        return os.path.relpath(path, self.root), digest

    def _append_manifest(self, meta):
        os.makedirs(self.root, exist_ok=True)
        is_new = not os.path.exists(self.manifest_path)
        with open(self.manifest_path, "a", encoding="utf-8-sig", newline="") as fh:
            writer = csv.writer(fh)
            if is_new:
                writer.writerow(MANIFEST_COLUMNS)
            writer.writerow([meta.get(col, "") for col in MANIFEST_COLUMNS])

    def verify(self):
        """重新計算清單中每個檔案的雜湊，回傳不符或遺失的項目。"""
        problems = []
        if not os.path.exists(self.manifest_path):
            return problems
        with open(self.manifest_path, "r", encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                date = (row.get("存檔時間") or "")[:10]
                path = os.path.join(self.root, date,
                                    safe_name(row.get("國家", "")),
                                    row.get("檔案", ""))
                if not os.path.exists(path):
                    problems.append((row.get("檔案"), "檔案不存在"))
                    continue
                with open(path, "rb") as f:
                    digest = hashlib.sha256(f.read()).hexdigest()
                if digest != row.get("SHA-256"):
                    problems.append((row.get("檔案"), "雜湊不符，檔案可能已被更動"))
        return problems

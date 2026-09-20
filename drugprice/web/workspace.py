# -*- coding: utf-8 -*-
"""網頁介面的工作狀態。

把「目前的藥品清單」「各國已下載的資料」「正在執行的工作」收在一起，
讓網頁介面與命令列共用同一套邏輯。

僅使用 Python 標準函式庫。
"""

import os
import threading
import traceback
from datetime import datetime

from ..core.net import Fetcher, RobotsDisallowed
from ..core.rawstore import RawStore
from ..core.schema import TAIPEI, read_csv, write_csv
from ..matching.druglist import read_drug_list
from ..registry import NOT_YET, SOURCES, codes, get
from ..sources.base import Context, Downloaded

__all__ = ["Workspace", "Job"]


class Job:
    """一次背景執行的工作。"""

    def __init__(self, name):
        self.name = name
        self.lines = []
        self.status = "執行中"
        self.started = datetime.now(TAIPEI)
        self.finished = None
        self._lock = threading.Lock()

    def log(self, message):
        with self._lock:
            self.lines.append(str(message))

    def snapshot(self, since=0):
        with self._lock:
            return {
                "名稱": self.name,
                "狀態": self.status,
                "開始時間": self.started.strftime("%H:%M:%S"),
                "訊息": self.lines[since:],
                "訊息總數": len(self.lines),
            }

    def done(self, status):
        with self._lock:
            self.status = status
            self.finished = datetime.now(TAIPEI)


class Workspace:
    """一個工作目錄下的所有狀態。"""

    def __init__(self, root="."):
        self.root = os.path.abspath(root)
        self.raw_dir = os.path.join(self.root, "raw")
        self.out_dir = os.path.join(self.root, "output")
        self.list_path = os.path.join(self.root, "藥品清單.csv")
        os.makedirs(self.out_dir, exist_ok=True)

        self.queries = []
        self.list_messages = []
        self.job = None
        self._records = {}          # 國別 -> PriceRecord 清單（快取）
        self._lock = threading.Lock()
        self._load_saved_list()

    # ------------------------------------------------------------ 藥品清單

    def _load_saved_list(self):
        if os.path.exists(self.list_path):
            try:
                with open(self.list_path, "rb") as fh:
                    self.set_drug_list(fh.read(), save=False)
            except OSError:
                pass

    def set_drug_list(self, data, save=True):
        self.queries, self.list_messages = read_drug_list(data)
        if save and self.queries:
            with open(self.list_path, "wb") as fh:
                fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))
        return self.list_messages

    # ------------------------------------------------------------ 各國狀態

    def country_status(self):
        out = []
        for code in codes():
            source = SOURCES[code]
            path = os.path.join(self.out_dir, f"{code}_藥價.csv")
            entry = {
                "代碼": code,
                "國家": source.country_name,
                "來源機關": source.agency,
                "幣別": source.currency,
                "欄位對照依據": source.field_confidence,
                "官方欄位文件": source.field_doc_url,
                "已下載": os.path.exists(path),
                "筆數": None,
                "檔案時間": None,
            }
            if entry["已下載"]:
                stat = os.stat(path)
                entry["檔案時間"] = datetime.fromtimestamp(
                    stat.st_mtime, TAIPEI).strftime("%Y-%m-%d %H:%M")
                entry["筆數"] = self._count_rows(path)
            out.append(entry)
        return out

    @staticmethod
    def _count_rows(path):
        try:
            with open(path, "rb") as fh:
                return max(sum(1 for _ in fh) - 1, 0)
        except OSError:
            return None

    def not_yet(self):
        return [{"代碼": code, "說明": note} for code, note in NOT_YET.items()]

    # ------------------------------------------------------------ 下載

    def start_download(self, country_codes):
        with self._lock:
            if self.job and self.job.status == "執行中":
                return False, "已經有工作在執行中，請等它跑完。"
            job = Job("下載藥價：" + "、".join(country_codes))
            self.job = job

        thread = threading.Thread(target=self._run_download,
                                  args=(job, country_codes), daemon=True)
        thread.start()
        return True, ""

    def _run_download(self, job, country_codes):
        store = RawStore(self.raw_dir)
        fetcher = Fetcher(min_interval=1.0, log=job.log)
        ctx = Context(fetcher, store, log=job.log)
        failures = []

        for code in country_codes:
            try:
                source = get(code)
            except KeyError as exc:
                job.log(str(exc))
                failures.append(code)
                continue
            try:
                records, _ = source.run(ctx)
            except RobotsDisallowed as exc:
                job.log(f"[{code}] {exc}")
                failures.append(code)
                continue
            except Exception as exc:                    # noqa: BLE001
                job.log(f"[{code}] 執行失敗：{exc}")
                job.log(traceback.format_exc(limit=3))
                failures.append(code)
                continue

            path = os.path.join(self.out_dir, f"{code}_藥價.csv")
            write_csv(records, path)
            with self._lock:
                self._records[code] = records
            job.log(f"　已輸出 {os.path.basename(path)}（{len(records):,} 筆）")

        if failures:
            job.log(f"完成，但有 {len(failures)} 國失敗：{'、'.join(failures)}")
            job.done("部分失敗")
        else:
            job.log("全部完成。")
            job.done("完成")

    # ------------------------------------------------------------ 資料讀取

    def records_for(self, code):
        """取得某國的資料，優先用快取，其次讀已輸出的 CSV。"""
        with self._lock:
            if code in self._records:
                return self._records[code]
        path = os.path.join(self.out_dir, f"{code}_藥價.csv")
        if not os.path.exists(path):
            return []
        records = read_csv(path)
        with self._lock:
            self._records[code] = records
        return records

    def clear_cache(self):
        with self._lock:
            self._records.clear()

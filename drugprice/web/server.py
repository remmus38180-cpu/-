# -*- coding: utf-8 -*-
"""本機網頁操作介面。

用標準函式庫的 http.server 在本機開一個網頁，只綁 127.0.0.1，
不對外開放。同仁雙擊 .bat 就會自動開啟瀏覽器，不需要安裝任何東西，
也不需要看到命令列。

    python -m drugprice.web

僅使用 Python 標準函式庫。
"""

import argparse
import csv
import io
import json
import mimetypes
import os
import posixpath
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ..matching.matcher import TIERS, match_country
from ..matching.scoring import rules_table
from ..registry import SOURCES, codes, get
from .workspace import Workspace

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DEFAULT_PORTS = [8765, 8766, 8767]


def to_jsonable(value):
    """把 dataclass 與巢狀結構轉成可 JSON 化的形式。"""
    import dataclasses
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {k: to_jsonable(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value


class Handler(BaseHTTPRequestHandler):
    workspace = None
    server_version = "DrugPriceTool/1.0"

    # --------------------------------------------------------------- 基礎

    def log_message(self, fmt, *args):
        pass                                   # 不要把每個請求都印到畫面上

    def _send(self, status, body, content_type="application/json; charset=utf-8",
              extra_headers=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, status=200):
        self._send(status, json.dumps(to_jsonable(payload), ensure_ascii=False))

    def _error(self, message, status=400):
        self._json({"錯誤": message}, status)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    # --------------------------------------------------------------- 路由

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        route = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        try:
            if route in ("/", "/index.html"):
                return self._static("index.html")
            if route.startswith("/static/"):
                return self._static(route[len("/static/"):])
            if route == "/api/state":
                return self._state()
            if route == "/api/rules":
                return self._json(rules_table())
            if route == "/api/job":
                return self._job(params)
            if route == "/api/druglist":
                return self._json({
                    "訊息": self.workspace.list_messages,
                    "清單": [to_jsonable(q) for q in self.workspace.queries],
                })
            if route == "/api/export":
                return self._export(params)
        except Exception as exc:                          # noqa: BLE001
            return self._error(f"處理時發生錯誤：{exc}", 500)
        self._error("找不到這個頁面", 404)

    def do_POST(self):
        route = urllib.parse.urlsplit(self.path).path
        try:
            if route == "/api/druglist":
                return self._set_druglist()
            if route == "/api/download":
                return self._download()
            if route == "/api/match":
                return self._match()
        except Exception as exc:                          # noqa: BLE001
            return self._error(f"處理時發生錯誤：{exc}", 500)
        self._error("找不到這個頁面", 404)

    # --------------------------------------------------------------- 靜態

    def _static(self, name):
        safe = posixpath.normpath("/" + name).lstrip("/")
        path = os.path.join(STATIC_DIR, safe)
        if not os.path.abspath(path).startswith(STATIC_DIR) or not os.path.isfile(path):
            return self._error("找不到檔案", 404)
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type.endswith("javascript"):
            content_type += "; charset=utf-8"
        with open(path, "rb") as fh:
            self._send(200, fh.read(), content_type)

    # --------------------------------------------------------------- API

    def _state(self):
        workspace = self.workspace
        self._json({
            "國家": workspace.country_status(),
            "尚未接上": workspace.not_yet(),
            "清單筆數": len(workspace.queries),
            "清單訊息": workspace.list_messages,
            "工作": workspace.job.snapshot(since=10 ** 9) if workspace.job else None,
        })

    def _job(self, params):
        job = self.workspace.job
        if job is None:
            return self._json({"狀態": "沒有工作在執行"})
        since = int((params.get("since") or ["0"])[0])
        self._json(job.snapshot(since=since))

    def _set_druglist(self):
        data = self._body()
        if not data:
            return self._error("沒有收到內容")
        messages = self.workspace.set_drug_list(data)
        self._json({
            "訊息": messages,
            "筆數": len(self.workspace.queries),
            "清單": [to_jsonable(q) for q in self.workspace.queries],
        })

    def _download(self):
        payload = json.loads(self._body() or b"{}")
        selected = payload.get("國家") or []
        selected = [c.upper() for c in selected if c.upper() in SOURCES]
        if not selected:
            return self._error("請至少勾選一個國家")
        ok, message = self.workspace.start_download(selected)
        if not ok:
            return self._error(message, 409)
        self._json({"已開始": selected})

    def _match(self):
        payload = json.loads(self._body() or b"{}")
        selected = payload.get("國家") or codes()
        category = payload.get("價格類別") or None
        limit = int(payload.get("每列上限") or 20)

        queries = self.workspace.queries
        if not queries:
            return self._error("還沒有匯入藥品清單")

        results = []
        for code in selected:
            records = self.workspace.records_for(code)
            if not records:
                results.append({
                    "國家代碼": code,
                    "國家": SOURCES[code].country_name if code in SOURCES else code,
                    "尚未下載": True,
                    "查詢": [],
                })
                continue
            source = SOURCES.get(code)
            matched = match_country(queries, records, source=source,
                                    rank_by_category=category,
                                    limit_per_query=limit)
            results.append({
                "國家代碼": code,
                "國家": matched[0].country_name if matched else code,
                "尚未下載": False,
                "查詢": [{
                    "商品名": item.query.brand_name,
                    "成分名": item.query.generic_name,
                    "訊息": item.message,
                    "候選": [to_jsonable(c) for c in item.candidates],
                } for item in matched],
            })

        self._json({
            "結果": results,
            "分級": [{"門檻": t[0], "代碼": t[1], "說明": t[2]} for t in TIERS],
        })

    def _export(self, params):
        """把比對結果匯出成 CSV，含排序依據欄位。"""
        selected = params.get("國家") or codes()
        queries = self.workspace.queries
        if not queries:
            return self._error("還沒有匯入藥品清單")

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "查詢商品名", "查詢成分名", "國家", "來源機關", "排名", "分級",
            "藥品相符度", "原廠可能性", "商品名", "成分名", "ATC代碼",
            "劑型", "含量", "包裝數量", "藥商", "原廠註記",
            "價格類別", "當地價格", "幣別", "單位藥價", "單位藥價算式",
            "排序依據", "判讀提醒", "資料版本日期", "來源網址",
            "原始檔", "原始檔位置", "欄位對照可信度",
        ])

        rows = 0
        for code in selected:
            records = self.workspace.records_for(code)
            if not records:
                continue
            for item in match_country(queries, records, source=SOURCES.get(code)):
                for candidate in item.candidates:
                    for price in candidate.prices:
                        writer.writerow([
                            item.query.brand_name, item.query.generic_name,
                            candidate.country_name, candidate.source_agency,
                            candidate.rank, f"{candidate.tier} {candidate.tier_label}",
                            candidate.drug_score, candidate.originator_score,
                            candidate.brand_name, candidate.generic_name,
                            candidate.atc_code, candidate.form,
                            f"{candidate.strength_value}{candidate.strength_unit}",
                            f"{candidate.pack_size_value}{candidate.pack_size_unit}",
                            candidate.marketer, candidate.originator_flag,
                            price.category_label, price.price, price.currency,
                            price.unit_price, price.unit_price_basis,
                            candidate.ranking_basis, candidate.caution,
                            candidate.data_version, candidate.source_url,
                            candidate.source_file, price.source_row,
                            candidate.field_confidence,
                        ])
                        rows += 1

        body = "﻿" + buffer.getvalue()      # BOM，Excel 才不會亂碼
        self._send(200, body, "text/csv; charset=utf-8", {
            "Content-Disposition": 'attachment; filename="match_result.csv"',
        })


def find_port(preferred=None):
    import socket
    for port in ([preferred] if preferred else []) + DEFAULT_PORTS:
        if port is None:
            continue
        sock = socket.socket()
        try:
            sock.bind(("127.0.0.1", port))
            return port
        except OSError:
            continue
        finally:
            sock.close()
    return 0


def serve(root=".", port=None, open_browser=True):
    workspace = Workspace(root)
    Handler.workspace = workspace
    chosen = find_port(port)
    httpd = ThreadingHTTPServer(("127.0.0.1", chosen), Handler)
    actual = httpd.server_address[1]
    url = f"http://127.0.0.1:{actual}/"

    print("=" * 60)
    print("  十國藥價工具已啟動")
    print("=" * 60)
    print(f"  請在瀏覽器開啟：{url}")
    print(f"  工作目錄：{workspace.root}")
    print()
    print("  這個網頁只在您這台電腦上執行，不會對外開放。")
    print("  結束時請關閉這個黑色視窗。")
    print()

    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已結束。")
    finally:
        httpd.server_close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="十國藥價工具的網頁操作介面")
    parser.add_argument("--root", default=".", help="工作目錄")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    serve(args.root, args.port, not args.no_browser)


if __name__ == "__main__":
    main()

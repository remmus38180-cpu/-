# -*- coding: utf-8 -*-
"""命令列介面。

供開發與疑難排解使用；一般同仁請用網頁操作介面，不需要碰這裡。

    python -m drugprice list              列出可用國家
    python -m drugprice check             連線與 robots.txt 體檢
    python -m drugprice download SE FR    下載並轉換指定國家
    python -m drugprice download --all    下載並轉換全部已接上的國家
    python -m drugprice parse SE          只重新解析已下載的原始檔

僅使用 Python 標準函式庫。
"""

import argparse
import os
import sys
import traceback

from .core.net import Fetcher, RobotsDisallowed
from .core.rawstore import RawStore
from .core.schema import write_csv
from .registry import NOT_YET, SOURCES, codes, get
from .sources.base import Context, Downloaded


def _log(message):
    print(message, flush=True)


def cmd_list(args):
    print("已接上的國家：")
    for code in codes():
        source = SOURCES[code]
        print(f"  {code:6} {source.country_name}（{source.agency}）")
        print(f"         幣別 {source.currency}／欄位對照 {source.field_confidence}")
    print("\n尚未接上的國家：")
    for code, note in NOT_YET.items():
        print(f"  {code:6} {note}")
    return 0


def cmd_check(args):
    fetcher = Fetcher(log=_log)
    targets = [get(c) for c in (args.countries or codes())]
    problems = 0
    print("連線與 robots.txt 體檢\n" + "=" * 60)
    for source in targets:
        print(f"\n{source.country_name}（{source.agency}）")
        probe = source.probe_url
        if not probe:
            print("  （此來源未設定體檢網址）")
            continue
        allowed, rule = fetcher.check_allowed(probe)
        print(f"  robots.txt：{'允許' if allowed else '禁止'}　{rule}")
        if not allowed:
            problems += 1
            continue
        try:
            resp = fetcher.fetch(probe, headers=source.probe_headers(),
                                 expect_status=None)
            print(f"  連線：HTTP {resp.status}　憑證模式：{resp.ssl_mode}")
            if resp.status >= 400:
                problems += 1
        except Exception as exc:                     # noqa: BLE001
            print(f"  連線失敗：{exc}")
            problems += 1
    print(f"\n共 {problems} 項需要注意。")
    return 1 if problems else 0


def cmd_download(args):
    selected = codes() if args.all else [c.upper() for c in args.countries]
    if not selected:
        print("請指定國家代碼，或加上 --all。可用代碼：" + "、".join(codes()))
        return 2

    store = RawStore(args.raw_dir)
    fetcher = Fetcher(min_interval=args.min_interval, log=_log)
    ctx = Context(fetcher, store, log=_log)
    os.makedirs(args.out_dir, exist_ok=True)

    failures = []
    for code in selected:
        try:
            source = get(code)
        except KeyError as exc:
            print(exc)
            failures.append(code)
            continue
        try:
            records, _ = source.run(ctx)
        except RobotsDisallowed as exc:
            print(f"[{code}] {exc}")
            failures.append(code)
            continue
        except Exception as exc:                     # noqa: BLE001
            print(f"[{code}] 執行失敗：{exc}")
            if args.debug:
                traceback.print_exc()
            failures.append(code)
            continue

        path = os.path.join(args.out_dir, f"{code}_藥價.csv")
        write_csv(records, path)
        print(f"　已輸出 {path}（{len(records):,} 筆）\n")

    print("=" * 60)
    print(f"完成 {len(selected) - len(failures)} 國，失敗 {len(failures)} 國"
          + (f"：{'、'.join(failures)}" if failures else ""))
    return 1 if failures else 0


def cmd_parse(args):
    """只重新解析留存區裡的原始檔，不連網。"""
    store = RawStore(args.raw_dir, run_date=args.run_date)
    ctx = Context(None, store, log=_log)
    os.makedirs(args.out_dir, exist_ok=True)

    for code in [c.upper() for c in args.countries]:
        source = get(code)
        directory = store.dir_for(code)
        files = [f for f in sorted(os.listdir(directory))
                 if not f.endswith(".meta.json")]
        if not files:
            print(f"[{code}] 留存區 {directory} 內沒有原始檔")
            continue
        downloaded = [Downloaded(
            path=os.path.join(directory, name),
            rel_path=os.path.relpath(os.path.join(directory, name), store.root),
            sha256="", source_url="（重新解析既有原始檔）",
            data_version=store.run_date, label=name) for name in files]
        records = source.parse(ctx, downloaded)
        path = os.path.join(args.out_dir, f"{code}_藥價.csv")
        write_csv(records, path)
        print(f"[{code}] {len(records):,} 筆 → {path}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m drugprice",
        description="十國藥價批次下載與轉換（僅使用 Python 標準函式庫）")
    parser.add_argument("--raw-dir", default="raw", help="原始檔留存區")
    parser.add_argument("--out-dir", default="output", help="輸出目錄")
    parser.add_argument("--debug", action="store_true", help="出錯時顯示完整錯誤堆疊")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="列出可用國家").set_defaults(func=cmd_list)

    check = sub.add_parser("check", help="連線與 robots.txt 體檢")
    check.add_argument("countries", nargs="*")
    check.set_defaults(func=cmd_check)

    download = sub.add_parser("download", help="下載並轉換")
    download.add_argument("countries", nargs="*")
    download.add_argument("--all", action="store_true")
    download.add_argument("--min-interval", type=float, default=1.0,
                          help="同一網域兩次請求的最小間隔秒數")
    download.set_defaults(func=cmd_download)

    parse = sub.add_parser("parse", help="只重新解析已下載的原始檔")
    parse.add_argument("countries", nargs="+")
    parse.add_argument("--run-date", default=None, help="留存區日期資料夾，預設今天")
    parse.set_defaults(func=cmd_parse)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

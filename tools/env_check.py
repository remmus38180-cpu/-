#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
環境檢測工具（階段0）
====================

用途
----
在正式開發十國藥價自動化工具之前，先確認執行這台電腦的環境條件。
本程式「不會」下載任何藥價資料、不會安裝任何東西、不會修改系統設定，
只做檢查並產生一份報告檔，請放心執行。

檢查項目
--------
1. Python 版本與位元數
2. 檔案讀寫權限
3. 本機網頁介面所需的連接埠是否可用
4. 瀏覽器（Edge / Chrome）安裝位置與版本
5. 瀏覽器無頭截圖功能是否可用   ← 決定截圖技術路線的關鍵
6. 各國官方網站連線與 SSL 憑證驗證情形

執行方式
--------
    python env_check.py

或直接雙擊 執行環境檢測.bat

產出
----
    環境檢測報告_YYYYMMDD_HHMMSS.txt
請將此檔案回傳，以利判斷後續開發方向。

技術原則：僅使用 Python 標準內建函式庫，不需安裝任何套件。
"""

import os
import platform
import socket
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime

# ----------------------------------------------------------------------------
# 檢測目標
# ----------------------------------------------------------------------------

# 各國官方來源網域。僅發出 HEAD 請求確認連線與憑證，不下載資料。
TEST_HOSTS = [
    ("日本 MHLW（批次檔）", "https://www.mhlw.go.jp/"),
    ("法國 CIP（批次檔）", "https://base-donnees-publique.medicaments.gouv.fr/"),
    ("法國 UCD／BdM_IT（批次檔＋手冊指定）", "http://www.codage.ext.cnamts.fr/"),
    ("比利時 INAMI（批次檔）", "https://www.riziv.fgov.be/"),
    ("比利時 CBIP（手冊指定）", "https://www.cbip.be/"),
    ("英國 NHS TRUD（批次檔）", "https://isd.digital.nhs.uk/"),
    ("澳洲 PBS（批次檔＋手冊指定）", "https://www.pbs.gov.au/"),
    ("瑞士 BAG（批次檔）", "https://epl.bag.admin.ch/"),
    ("瑞士 compendium（手冊指定）", "https://compendium.ch/"),
    ("瑞典 TLV（批次檔）", "https://www.tlv.se/"),
    ("瑞典 FASS（手冊指定）", "https://www.fass.se/"),
    ("德國 BfArM（批次檔）", "https://www.bfarm.de/"),
    ("德國 G-BA AIS（批次檔）", "https://ais.g-ba.de/"),
    ("加拿大薩省 eHealth（僅人工查詢）", "https://formulary.drugplan.ehealthsask.ca/"),
]

# 瀏覽器可能的安裝位置（Windows）
WINDOWS_BROWSERS = [
    ("Microsoft Edge", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ("Microsoft Edge", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    ("Google Chrome", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    ("Google Chrome", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]

# 瀏覽器可能的安裝位置（Linux／macOS，供開發測試用）
OTHER_BROWSERS = [
    ("Chromium", "/opt/pw-browsers/chromium"),
    ("Chromium", "/usr/bin/chromium"),
    ("Chromium", "/usr/bin/chromium-browser"),
    ("Google Chrome", "/usr/bin/google-chrome"),
    ("Microsoft Edge", "/usr/bin/microsoft-edge"),
    ("Google Chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    ("Microsoft Edge", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
]

UI_PORTS = [8765, 8766, 8767]

CONNECT_TIMEOUT = 15


# ----------------------------------------------------------------------------
# 報告輸出
# ----------------------------------------------------------------------------

class Report:
    """同時輸出到畫面與報告檔的記錄器。"""

    def __init__(self):
        self.lines = []

    def line(self, text=""):
        print(text)
        self.lines.append(text)

    def section(self, title):
        self.line()
        self.line("=" * 68)
        self.line(title)
        self.line("=" * 68)

    def item(self, label, value, status=None):
        mark = {"ok": "[正常]", "warn": "[注意]", "fail": "[失敗]"}.get(status, "      ")
        self.line(f"{mark} {label}：{value}")

    def save(self, path):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(self.lines) + "\n")


# ----------------------------------------------------------------------------
# 1. Python 環境
# ----------------------------------------------------------------------------

def check_python(rep):
    rep.section("一、Python 執行環境")
    ver = sys.version_info
    rep.item("Python 版本", platform.python_version(),
             "ok" if ver >= (3, 8) else "fail")
    rep.item("位元數", platform.architecture()[0])
    rep.item("執行檔路徑", sys.executable)
    rep.item("作業系統", f"{platform.system()} {platform.release()}")
    rep.item("預設編碼", sys.getdefaultencoding())
    rep.item("主控台編碼", getattr(sys.stdout, "encoding", "未知"))

    if ver < (3, 8):
        rep.line("      → Python 版本過舊，請改用 3.8 以上版本。")

    # 確認會用到的標準函式庫都在（免安裝版有時是精簡過的）
    needed = ["zipfile", "xml.etree.ElementTree", "sqlite3", "csv",
              "http.server", "urllib.request", "ssl", "hashlib",
              "struct", "webbrowser", "json", "unicodedata"]
    missing = []
    for name in needed:
        try:
            __import__(name)
        except ImportError:
            missing.append(name)
    if missing:
        rep.item("標準函式庫", f"缺少 {', '.join(missing)}", "fail")
        rep.line("      → 這個 Python 是精簡版，缺少必要模組，請改用完整版 WinPython。")
    else:
        rep.item("標準函式庫", f"{len(needed)} 項全部具備", "ok")


# ----------------------------------------------------------------------------
# 2. 檔案讀寫權限
# ----------------------------------------------------------------------------

def check_filesystem(rep):
    rep.section("二、檔案讀寫權限")
    workdir = os.getcwd()
    rep.item("目前工作目錄", workdir)

    probe = os.path.join(workdir, "_環境檢測暫存檔.tmp")
    try:
        with open(probe, "w", encoding="utf-8") as fh:
            fh.write("測試")
        with open(probe, "r", encoding="utf-8") as fh:
            fh.read()
        os.remove(probe)
        rep.item("目錄可寫入", "是", "ok")
    except OSError as exc:
        rep.item("目錄可寫入", f"否（{exc}）", "fail")
        rep.line("      → 請把整個資料夾複製到您的「文件」或「下載」資料夾底下再執行。")

    # 中文檔名（截圖檔名會帶藥品名）
    cjk_probe = os.path.join(workdir, "_檢測中文檔名測試.tmp")
    try:
        with open(cjk_probe, "w", encoding="utf-8") as fh:
            fh.write("x")
        os.remove(cjk_probe)
        rep.item("中文檔名支援", "是", "ok")
    except OSError as exc:
        rep.item("中文檔名支援", f"否（{exc}）", "warn")

    try:
        usage = None
        if hasattr(__import__("shutil"), "disk_usage"):
            import shutil
            usage = shutil.disk_usage(workdir)
        if usage:
            rep.item("可用磁碟空間", f"{usage.free / (1024 ** 3):.1f} GB",
                     "ok" if usage.free > 2 * 1024 ** 3 else "warn")
    except OSError:
        pass


# ----------------------------------------------------------------------------
# 3. 本機網頁介面連接埠
# ----------------------------------------------------------------------------

def check_ports(rep):
    rep.section("三、本機網頁操作介面（連接埠）")
    rep.line("操作介面會在這台電腦本機開一個網頁伺服器，只有本機連得到，不對外開放。")
    rep.line()
    available = []
    for port in UI_PORTS:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
            available.append(port)
            rep.item(f"連接埠 {port}", "可使用", "ok")
        except OSError as exc:
            rep.item(f"連接埠 {port}", f"無法使用（{exc.strerror or exc}）", "warn")
        finally:
            sock.close()

    if not available:
        rep.line("      → 三個備用連接埠都被占用或被防火牆擋住，請回報此結果。")


# ----------------------------------------------------------------------------
# 4. 瀏覽器偵測
# ----------------------------------------------------------------------------

def find_browsers(rep):
    rep.section("四、瀏覽器偵測")
    import shutil

    candidates = WINDOWS_BROWSERS if os.name == "nt" else OTHER_BROWSERS
    found = []
    seen = set()

    def add(name, path):
        try:
            key = os.path.realpath(path)
        except OSError:
            key = path
        if key not in seen:
            seen.add(key)
            found.append((name, path))

    for name, path in candidates:
        if os.path.exists(path):
            add(name, path)

    for exe in ("msedge", "chrome", "chromium", "google-chrome", "chromium-browser"):
        which = shutil.which(exe)
        if which:
            add(exe, which)

    if not found:
        rep.item("瀏覽器", "找不到 Edge 或 Chrome", "fail")
        rep.line("      → 截圖功能需要瀏覽器。Windows 內建 Edge，若找不到請回報。")
        return []

    for name, path in found:
        rep.item(name, path, "ok")
        version = browser_version(path)
        if version:
            rep.line(f"       版本：{version}")
    return found


def browser_version(path):
    """取得瀏覽器版本字串，取不到就回傳 None。"""
    try:
        out = subprocess.run([path, "--version"], capture_output=True,
                             timeout=20, text=True, errors="replace")
        if out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    if os.name == "nt":
        # Windows 上 --version 常常沒有輸出，改讀檔案版本資訊
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"(Get-Item '{path}').VersionInfo.ProductVersion"],
                capture_output=True, timeout=30, text=True, errors="replace")
            if out.stdout.strip():
                return out.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return None


# ----------------------------------------------------------------------------
# 5. 無頭截圖能力
# ----------------------------------------------------------------------------

TEST_PAGE = """<!doctype html>
<meta charset="utf-8">
<title>screenshot test</title>
<body style="font-family:sans-serif;background:#fff;color:#111;padding:40px">
<h1>截圖測試頁</h1>
<p>若您看到這張圖，表示無頭截圖功能可用。</p>
<table border="1" cellpadding="6"><tr><th>藥品</th><th>價格</th></tr>
<tr><td>測試藥品</td><td>123.45</td></tr></table>
</body>
"""

# 不同版本的 Edge/Chrome 支援的無頭參數不同，依序嘗試。
HEADLESS_MODES = [
    ("新版無頭模式", ["--headless=new"]),
    ("舊版無頭模式", ["--headless"]),
    ("舊版無頭模式＋停用沙箱", ["--headless", "--no-sandbox"]),
]


def try_screenshot(browser_path, mode_args, page_url, workdir):
    """嘗試截一張圖。回傳 (是否成功, 說明文字)。"""
    shot = os.path.join(workdir, "shot.png")
    if os.path.exists(shot):
        os.remove(shot)
    cmd = [browser_path, *mode_args, "--disable-gpu", "--no-first-run",
           "--user-data-dir=" + os.path.join(workdir, "profile"),
           "--window-size=1280,900",
           "--virtual-time-budget=5000",
           "--screenshot=" + shot, page_url]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=90)
    except subprocess.TimeoutExpired:
        return False, "逾時未回應"
    except OSError as exc:
        return False, f"無法啟動（{exc}）"

    if os.path.exists(shot) and os.path.getsize(shot) > 1000:
        return True, f"成功，產出 PNG {os.path.getsize(shot):,} 位元組"

    # 失敗時把瀏覽器自己講的錯誤原因帶出來，才有辦法判斷怎麼修
    stderr = (proc.stderr or b"").decode("utf-8", "replace")
    reason = ""
    for raw in reversed(stderr.splitlines()):
        text = raw.strip()
        if text and "dbus" not in text.lower() and "GPU" not in text:
            reason = text[-160:]
            break
    return False, f"未產出 PNG 檔（結束代碼 {proc.returncode}）" + (
        f"；瀏覽器訊息：{reason}" if reason else "")


def check_screenshot(rep, browsers):
    rep.section("五、無頭截圖能力（決定截圖技術路線的關鍵項目）")
    rep.line("無頭截圖＝在背景開啟瀏覽器拍下網頁畫面，過程中不會有視窗彈出來干擾您。")
    rep.line()

    if not browsers:
        rep.item("截圖測試", "略過（未偵測到瀏覽器）", "fail")
        return

    tmpdir = tempfile.mkdtemp(prefix="drugprice_envcheck_")
    page = os.path.join(tmpdir, "test.html")
    with open(page, "w", encoding="utf-8") as fh:
        fh.write(TEST_PAGE)
    page_url = "file:///" + page.replace("\\", "/").lstrip("/")

    winner = None
    for name, path in browsers:
        for mode_label, mode_args in HEADLESS_MODES:
            ok, detail = try_screenshot(path, mode_args, page_url, tmpdir)
            rep.item(f"{name} / {mode_label}", detail, "ok" if ok else "warn")
            if ok:
                winner = (name, mode_label, " ".join(mode_args))
                break
        if winner:
            break

    rep.line()
    if winner:
        rep.line(f"      可用組合：{winner[0]}，參數 {winner[2]}")
        rep.line("      → 可採用「瀏覽器命令列截圖」路線，不需安裝 Selenium 或 ChromeDriver。")
    else:
        rep.line("      → 命令列截圖不可用。請回報上方的瀏覽器訊息，")
        rep.line("        以便判斷改走 Selenium 路線或全面改為人工截圖。")

    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


# ----------------------------------------------------------------------------
# 6. 網站連線與 SSL 憑證
# ----------------------------------------------------------------------------

def build_contexts():
    """依序回傳「憑證驗證模式」清單，由嚴格到寬鬆。"""
    modes = [("預設憑證驗證", ssl.create_default_context())]

    if hasattr(ssl, "enum_certificates"):  # 僅 Windows 有
        try:
            ctx = ssl.create_default_context()
            loaded = 0
            for cert, encoding, trust in ssl.enum_certificates("ROOT"):
                if encoding == "x509_asn":
                    try:
                        ctx.load_verify_locations(cadata=ssl.DER_cert_to_PEM_cert(cert))
                        loaded += 1
                    except ssl.SSLError:
                        pass
            if loaded:
                modes.append((f"Windows 系統憑證（載入 {loaded} 張）", ctx))
        except OSError:
            pass

    unverified = ssl.create_default_context()
    unverified.check_hostname = False
    unverified.verify_mode = ssl.CERT_NONE
    modes.append(("不驗證憑證", unverified))
    return modes


def probe_host(url, contexts):
    """回傳 (成功的模式名稱, 說明)；全部失敗則模式名稱為 None。"""
    req = urllib.request.Request(url, method="HEAD", headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    last_error = ""
    for label, ctx in contexts:
        try:
            with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT,
                                        context=ctx) as resp:
                return label, f"HTTP {resp.status}"
        except urllib.error.HTTPError as exc:
            # 有回應就代表連得到，HEAD 被拒是網站設定問題，不是連線問題
            return label, f"HTTP {exc.code}（連線正常，該站不接受 HEAD 查詢）"
        except urllib.error.URLError as exc:
            last_error = str(exc.reason)
        except (ssl.SSLError, socket.timeout, OSError) as exc:
            last_error = str(exc)
    return None, last_error


def check_network(rep):
    rep.section("六、各國官方網站連線測試")
    rep.line("本項只確認「連不連得到」與「憑證驗證是否通過」，不會下載任何藥價資料。")

    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    rep.line()
    rep.item("系統 Proxy 設定", proxy if proxy else "未設定")

    contexts = build_contexts()
    rep.item("可用的憑證驗證模式", "、".join(label for label, _ in contexts))
    rep.line()

    stats = {"default": 0, "winstore": 0, "noverify": 0, "fail": 0}
    for name, url in TEST_HOSTS:
        label, detail = probe_host(url, contexts)
        if label is None:
            rep.item(name, f"連線失敗（{detail}）", "fail")
            stats["fail"] += 1
        elif label.startswith("預設"):
            rep.item(name, f"正常（{detail}）", "ok")
            stats["default"] += 1
        elif label.startswith("Windows"):
            rep.item(name, f"需用系統憑證（{detail}）", "warn")
            stats["winstore"] += 1
        else:
            rep.item(name, f"憑證驗證失敗，改用不驗證模式（{detail}）", "warn")
            stats["noverify"] += 1

    rep.line()
    rep.line(f"      連線正常 {stats['default']} 站、"
             f"需系統憑證 {stats['winstore']} 站、"
             f"需關閉驗證 {stats['noverify']} 站、"
             f"完全連不到 {stats['fail']} 站。")
    if stats["noverify"] or stats["winstore"]:
        rep.line("      → 公司網路有 SSL 檢查設備，程式已內建對應處理，屬預期情形。")
    if stats["fail"]:
        rep.line("      → 連不到的網站可能被公司防火牆阻擋，需洽資訊單位開放。")


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

def main():
    rep = Report()
    started = datetime.now()

    rep.line("=" * 68)
    rep.line("  十國藥價自動化工具 — 環境檢測報告")
    rep.line("=" * 68)
    rep.line(f"  檢測時間：{started.strftime('%Y-%m-%d %H:%M:%S')}")
    rep.line(f"  電腦名稱：{platform.node()}")
    rep.line()
    rep.line("  本程式只做檢查，不會下載藥價資料、不會安裝軟體、不會修改設定。")
    rep.line("  預計耗時 1 至 3 分鐘，請等待畫面出現「檢測完成」。")

    check_python(rep)
    check_filesystem(rep)
    check_ports(rep)
    browsers = find_browsers(rep)
    check_screenshot(rep, browsers)
    check_network(rep)

    elapsed = (datetime.now() - started).total_seconds()
    rep.section("檢測完成")
    rep.line(f"耗時 {elapsed:.0f} 秒。")

    filename = f"環境檢測報告_{started.strftime('%Y%m%d_%H%M%S')}.txt"
    out_path = os.path.join(os.getcwd(), filename)
    try:
        rep.save(out_path)
        print()
        print(f"報告已存檔：{out_path}")
        print("請將這個檔案回傳，以利判斷後續開發方向。")
    except OSError as exc:
        print()
        print(f"報告存檔失敗（{exc}），請直接複製上方畫面內容回傳。")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已中斷。")
        sys.exit(1)

# -*- coding: utf-8 -*-
"""連線層：SSL 相容處理、robots.txt 遵循、速率限制、重試。

設計重點
--------
1. **SSL**：公司網路有流量檢查設備，Python 預設憑證清單會驗證失敗。
   依序嘗試「預設憑證」→「Windows 系統憑證存放區」→「不驗證」，
   並把實際採用的模式記錄在回應物件裡。佐證資料需要能說明當時的驗證狀態，
   所以這件事必須留痕，不能默默降級。

2. **robots.txt**：每個網域抓一次 robots.txt 並快取。被 Disallow 的網址
   一律拒絕下載並拋出 RobotsDisallowed，由呼叫端決定如何呈現給使用者。
   本專案已有先例（加拿大薩克其萬省），此處把規則制度化，
   避免每次都靠人記得。

3. **速率限制**：以網域為單位，遵守 robots.txt 的 Crawl-delay，
   亦可由呼叫端指定更保守的間隔（如澳洲 PBS 公開 API 為每 20 秒 1 次）。

僅使用 Python 標準函式庫。
"""

import hashlib
import gzip
import io
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

from .robots import parse_robots, RobotsRules

__all__ = ["Fetcher", "Response", "RobotsDisallowed", "FetchError"]

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "DrugPriceTool/1.0 (+health insurance price reference; contact via IT dept)"
)


class FetchError(Exception):
    """下載失敗（連線問題、HTTP 錯誤、重試耗盡）。"""


class RobotsDisallowed(Exception):
    """該網址被網站的 robots.txt 禁止自動化存取。"""

    def __init__(self, url, rule):
        self.url = url
        self.rule = rule
        super().__init__(
            f"網站的 robots.txt 禁止自動化存取此網址：{url}\n"
            f"　命中規則：{rule}\n"
            f"　本工具不會違反 robots.txt。此來源需改以人工方式取得，"
            f"或改用該機關提供的其他管道。"
        )


class Response:
    """一次成功下載的結果，含佐證所需的中繼資料。"""

    def __init__(self, url, final_url, status, headers, content, ssl_mode):
        self.url = url
        self.final_url = final_url
        self.status = status
        self.headers = headers
        self.content = content
        self.ssl_mode = ssl_mode
        self.fetched_at = time.time()

    @property
    def sha256(self):
        return hashlib.sha256(self.content).hexdigest()

    def text(self, encoding="utf-8", errors="strict"):
        return self.content.decode(encoding, errors)

    def __repr__(self):
        return (f"<Response {self.status} {len(self.content):,}B "
                f"ssl={self.ssl_mode} {self.final_url}>")


def _build_ssl_modes():
    """回傳 [(模式名稱, SSLContext), ...]，由嚴格到寬鬆。"""
    modes = [("預設憑證驗證", ssl.create_default_context())]

    if hasattr(ssl, "enum_certificates"):     # 僅 Windows 提供
        try:
            ctx = ssl.create_default_context()
            loaded = 0
            for cert, encoding, _trust in ssl.enum_certificates("ROOT"):
                if encoding == "x509_asn":
                    try:
                        ctx.load_verify_locations(
                            cadata=ssl.DER_cert_to_PEM_cert(cert))
                        loaded += 1
                    except ssl.SSLError:
                        pass
            if loaded:
                modes.append((f"Windows 系統憑證（{loaded} 張）", ctx))
        except OSError:
            pass

    lax = ssl.create_default_context()
    lax.check_hostname = False
    lax.verify_mode = ssl.CERT_NONE
    modes.append(("不驗證憑證", lax))
    return modes


def _decompress(content, headers):
    encoding = (headers.get("Content-Encoding") or "").lower()
    if "gzip" in encoding:
        try:
            return gzip.decompress(content)
        except (OSError, EOFError):
            return content
    if "deflate" in encoding:
        try:
            return zlib.decompress(content)
        except zlib.error:
            try:
                return zlib.decompress(content, -zlib.MAX_WBITS)
            except zlib.error:
                return content
    return content


class Fetcher:
    """帶 robots.txt 遵循與速率限制的下載器。

    參數
    ----
    user_agent      送出的 User-Agent，同時用於比對 robots.txt 區段
    respect_robots  是否遵循 robots.txt（預設是；關閉需明確指定並自負責任）
    min_interval    每個網域兩次請求間的最小秒數；robots.txt 的
                    Crawl-delay 若更長則以較長者為準
    max_retries     網路錯誤或 5xx／429 的重試次數
    log             接受單一字串參數的函式，用來輸出進度訊息
    """

    def __init__(self, user_agent=DEFAULT_USER_AGENT, respect_robots=True,
                 min_interval=1.0, max_retries=4, timeout=120, log=None):
        self.user_agent = user_agent
        self.respect_robots = respect_robots
        self.min_interval = min_interval
        self.max_retries = max_retries
        self.timeout = timeout
        self.log = log or (lambda msg: None)

        self._ssl_modes = _build_ssl_modes()
        self._preferred_ssl = {}      # host -> 上次成功的模式索引
        self._robots = {}             # host -> RobotsRules
        self._last_request = {}       # host -> 上次請求的時間戳

    # ---------------------------------------------------------------- robots

    def robots_for(self, url):
        """取得（並快取）該網域的 robots.txt 規則。"""
        parts = urllib.parse.urlsplit(url)
        host = f"{parts.scheme}://{parts.netloc}"
        if host in self._robots:
            return self._robots[host]

        rules = RobotsRules(fetched=False, reason="尚未取得")
        try:
            resp = self._raw_request(host + "/robots.txt", timeout=30)
            if resp.status == 200:
                rules = parse_robots(
                    resp.content.decode("utf-8", "replace"), self.user_agent)
                rules.fetched = True
            else:
                rules = RobotsRules(fetched=False,
                                    reason=f"robots.txt 回應 HTTP {resp.status}")
        except (FetchError, urllib.error.URLError, OSError) as exc:
            rules = RobotsRules(fetched=False, reason=f"robots.txt 取得失敗：{exc}")

        self._robots[host] = rules
        return rules

    def check_allowed(self, url):
        """回傳 (是否允許, 說明)。不會實際下載。"""
        if not self.respect_robots:
            return True, "已關閉 robots.txt 檢查"
        rules = self.robots_for(url)
        if not rules.fetched:
            return True, f"{rules.reason}，依慣例視為允許"
        allowed, rule = rules.is_allowed(url)
        return allowed, (rule or "robots.txt 未針對此路徑設限")

    # ------------------------------------------------------------ 速率限制

    def _wait_turn(self, host, rules):
        interval = self.min_interval
        if rules is not None and rules.crawl_delay:
            interval = max(interval, rules.crawl_delay)
        last = self._last_request.get(host)
        if last is not None:
            remaining = interval - (time.monotonic() - last)
            if remaining > 0:
                self.log(f"　（依網站規定等待 {remaining:.0f} 秒）")
                time.sleep(remaining)
        self._last_request[host] = time.monotonic()

    # -------------------------------------------------------------- 實際下載

    def _raw_request(self, url, headers=None, timeout=None):
        """單次請求，含 SSL 模式降級。不做 robots 檢查與重試。"""
        parts = urllib.parse.urlsplit(url)
        host = parts.netloc
        req_headers = {
            "User-Agent": self.user_agent,
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
        }
        if headers:
            req_headers.update(headers)
        request = urllib.request.Request(url, headers=req_headers)

        order = list(range(len(self._ssl_modes)))
        preferred = self._preferred_ssl.get(host)
        if preferred is not None:
            order.remove(preferred)
            order.insert(0, preferred)

        last_exc = None
        for index in order:
            mode_name, context = self._ssl_modes[index]
            try:
                with urllib.request.urlopen(
                        request, timeout=timeout or self.timeout,
                        context=context) as resp:
                    content = _decompress(resp.read(), resp.headers)
                    if index != self._preferred_ssl.get(host):
                        self._preferred_ssl[host] = index
                        if index > 0:
                            self.log(f"　（{host} 改用「{mode_name}」連線）")
                    return Response(url, resp.geturl(), resp.status,
                                    dict(resp.headers), content, mode_name)
            except urllib.error.HTTPError as exc:
                # HTTP 錯誤代表連得到，不需要換 SSL 模式
                content = _decompress(exc.read(), exc.headers)
                self._preferred_ssl[host] = index
                return Response(url, url, exc.code, dict(exc.headers),
                                content, mode_name)
            except (ssl.SSLError, urllib.error.URLError, OSError) as exc:
                last_exc = exc
                continue

        raise FetchError(f"連線失敗：{url}\n　最後的錯誤：{last_exc}")

    def fetch(self, url, headers=None, expect_status=(200,)):
        """下載一個網址，遵循 robots.txt 與速率限制，失敗自動重試。"""
        allowed, rule = self.check_allowed(url)
        if not allowed:
            raise RobotsDisallowed(url, rule)

        parts = urllib.parse.urlsplit(url)
        host = parts.netloc
        rules = self._robots.get(f"{parts.scheme}://{parts.netloc}")

        delay = 2.0
        last_error = ""
        for attempt in range(1, self.max_retries + 1):
            self._wait_turn(host, rules)
            try:
                resp = self._raw_request(url, headers=headers)
            except FetchError as exc:
                last_error = str(exc)
                if attempt == self.max_retries:
                    raise
                self.log(f"　第 {attempt} 次嘗試失敗，{delay:.0f} 秒後重試")
                time.sleep(delay)
                delay *= 2
                continue

            if expect_status and resp.status not in expect_status:
                if resp.status in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    wait = delay
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait = max(wait, float(retry_after))
                    self.log(f"　網站回應 HTTP {resp.status}，{wait:.0f} 秒後重試")
                    time.sleep(wait)
                    delay *= 2
                    last_error = f"HTTP {resp.status}"
                    continue
                raise FetchError(
                    f"下載失敗：{url}\n　網站回應 HTTP {resp.status}")
            return resp

        raise FetchError(f"下載失敗：{url}\n　{last_error}")

    def exists(self, url):
        """確認網址是否存在（用於版本號自動探測）。被 robots 擋住視為不存在。"""
        try:
            allowed, _ = self.check_allowed(url)
            if not allowed:
                return False
            parts = urllib.parse.urlsplit(url)
            rules = self._robots.get(f"{parts.scheme}://{parts.netloc}")
            self._wait_turn(parts.netloc, rules)
            resp = self._raw_request(url, headers={"Range": "bytes=0-0"})
            return resp.status in (200, 206)
        except (FetchError, OSError):
            return False

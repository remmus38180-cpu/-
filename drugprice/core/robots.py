# -*- coding: utf-8 -*-
"""robots.txt 規則解析與比對。

為什麼不用 Python 內建的 urllib.robotparser
------------------------------------------
內建的 RobotFileParser 只做字首比對，不支援 ``*`` 與 ``$`` 萬用字元。
本專案實際遇到的規則就有萬用字元，例如澳洲 PBS 的::

    Disallow: /*.zip$

用內建解析器會判定為「允許」，與網站的真實意思相反。本模組依 Robots
Exclusion Protocol 實作萬用字元比對與「最長規則優先」的判斷方式。

僅使用 Python 標準函式庫。
"""

import re
import urllib.parse

__all__ = ["RobotsRules", "parse_robots"]


def _pattern_to_regex(pattern):
    """把 robots.txt 的路徑樣式轉成正規表示式。

    ``*`` 代表任意字元，``$`` 若出現在結尾代表必須完全結束於此。
    """
    anchored_end = pattern.endswith("$")
    if anchored_end:
        pattern = pattern[:-1]

    out = []
    for char in pattern:
        if char == "*":
            out.append(".*")
        else:
            out.append(re.escape(char))
    regex = "^" + "".join(out)
    if anchored_end:
        regex += "$"
    return re.compile(regex)


class _Rule:
    __slots__ = ("allow", "raw", "regex", "weight")

    def __init__(self, allow, raw):
        self.allow = allow
        self.raw = raw
        self.regex = _pattern_to_regex(raw)
        # 「最長規則優先」：長度以樣式字元數計，萬用字元不計入
        self.weight = len(raw.replace("*", "").replace("$", ""))


class RobotsRules:
    """某個網站對某個 user-agent 的 robots.txt 規則。"""

    def __init__(self, rules=None, crawl_delay=None, fetched=True, reason=""):
        self.rules = rules or []
        self.crawl_delay = crawl_delay
        # fetched=False 代表 robots.txt 抓不到。依慣例視為全部允許，
        # 但保留原因字串，讓呼叫端能在紀錄中說明清楚。
        self.fetched = fetched
        self.reason = reason

    def is_allowed(self, url):
        """回傳 (是否允許, 命中的規則原文)。未命中任何規則即為允許。"""
        path = urllib.parse.urlsplit(url).path or "/"
        query = urllib.parse.urlsplit(url).query
        if query:
            path = path + "?" + query

        best = None
        for rule in self.rules:
            if rule.regex.match(path):
                if best is None or rule.weight > best.weight:
                    best = rule
                elif rule.weight == best.weight and rule.allow and not best.allow:
                    # 長度相同時 Allow 優先，這是 REP 的慣例
                    best = rule
        if best is None:
            return True, ""
        verb = "Allow" if best.allow else "Disallow"
        return best.allow, f"{verb}: {best.raw}"


def parse_robots(text, user_agent="*"):
    """解析 robots.txt 內容，取出適用於 user_agent 的規則。

    比對順序：先找完全相符的 user-agent 區段，找不到才用 ``*`` 區段。
    """
    groups = {}          # user-agent（小寫） -> {"rules": [...], "delay": float|None}
    current_agents = []
    expecting_agent = True

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field = field.strip().lower()
        value = value.strip()

        if field == "user-agent":
            if not expecting_agent:
                current_agents = []
                expecting_agent = True
            current_agents.append(value.lower())
            groups.setdefault(value.lower(), {"rules": [], "delay": None})
            continue

        if field in ("allow", "disallow"):
            expecting_agent = False
            if not value and field == "disallow":
                continue          # 「Disallow:」空值代表全部允許，忽略即可
            if not value:
                continue
            for agent in current_agents:
                groups[agent]["rules"].append(_Rule(field == "allow", value))
            continue

        if field == "crawl-delay":
            expecting_agent = False
            try:
                delay = float(value)
            except ValueError:
                continue
            for agent in current_agents:
                groups[agent]["delay"] = delay

    key = user_agent.lower()
    group = groups.get(key) or groups.get("*")
    if group is None:
        return RobotsRules()
    return RobotsRules(group["rules"], group["delay"])

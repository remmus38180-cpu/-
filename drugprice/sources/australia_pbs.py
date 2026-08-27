# -*- coding: utf-8 -*-
"""澳洲 — PBS（Pharmaceutical Benefits Scheme）公開資料 API。

為什麼不用整批 zip 檔
--------------------
報告中原記載的下載網址為::

    https://www.pbs.gov.au/downloads/YYYY/MM/YYYY-MM-01-PBS-API-CSV-files.zip

但 www.pbs.gov.au 的 robots.txt 明確禁止自動化存取該路徑::

    Disallow: /downloads/
    Disallow: /*.zip$

且官方「Data Distribution Project」頁面已載明舊有的 XML 與純文字檔散布
方式全部由 API 取代（legacy outputs have been discontinued）。因此本模組
改用官方**公開 API**：robots.txt 允許、免帳號、有官方 Data Dictionary。

速率限制
--------
公開 API 為**每 20 秒 1 次請求，且此上限由全體使用者共用**。
本模組每頁取 5000 筆，全量約 15,000 筆、3 頁即可取完，
請勿自行調低間隔，以免影響其他使用者並被擋。

價格欄位
--------
``/items`` 端點同時提供四種價格，意義各不相同，因此各自獨立成一筆記錄::

    determined_price              官方核定價
    claimed_price                 廠商申報價
    proportional_price            比例計價
    weighted_avg_disclosed_price  加權平均揭露價

原操作手冊指定的 ``cp2p``（Commonwealth price to pharmacy）欄位在新 API
中沒有同名欄位，**對應關係尚待以官方 Data Dictionary 確認**，
在此之前不做等同對應。

官方 Data Dictionary：
https://data.pbs.gov.au/download/api/files/PBS-API-V3-Data-Dictionary-v3.7.8.pdf

僅使用 Python 標準函式庫。
"""

import csv
import io
import json
import os

from ..core.schema import Confidence, PriceCategory
from ..core.textfile import decode
from ..core.units import clean_number, parse_pack_size, parse_strength
from .base import Downloaded, Source

BASE_URL = "https://data-api.health.gov.au/pbs/api/v3"

# 公開 API 的訂閱金鑰。此金鑰隨官方公開的 Postman collection 一併發布，
# 供所有人免費使用，非個人帳號憑證。若官方更換金鑰，可用環境變數
# PBS_SUBSCRIPTION_KEY 覆寫，不必改程式。
PUBLIC_SUBSCRIPTION_KEY = "2384af7c667342ceb5a736fe29f1dc6b"

PAGE_SIZE = 5000
# 官方規定每 20 秒 1 次，多留 1 秒緩衝
MIN_INTERVAL = 21.0

PRICE_COLUMNS = [
    ("determined_price", PriceCategory.DETERMINED),
    ("claimed_price", PriceCategory.CLAIMED),
    ("proportional_price", PriceCategory.PROPORTIONAL),
    ("weighted_avg_disclosed_price", PriceCategory.WEIGHTED_AVG_DISCLOSED),
]


def subscription_key():
    return os.environ.get("PBS_SUBSCRIPTION_KEY") or PUBLIC_SUBSCRIPTION_KEY


class AustraliaPBS(Source):
    country = "AU"
    country_name = "澳洲"
    agency = "PBS（Department of Health）公開 API"
    currency = "AUD"
    field_confidence = Confidence.OFFICIAL_DOC
    field_doc_url = ("https://data.pbs.gov.au/download/api/files/"
                     "PBS-API-V3-Data-Dictionary-v3.7.8.pdf")
    probe_url = ("https://data-api.health.gov.au/pbs/api/v3/schedules?get_latest_schedule_only=true")

    def probe_headers(self):
        return self._headers("application/json")

    def _headers(self, accept="text/csv"):
        return {"subscription-key": subscription_key(), "Accept": accept}

    def _latest_schedule(self, ctx):
        url = f"{BASE_URL}/schedules?get_latest_schedule_only=true"
        ctx.log("　查詢當期 schedule")
        resp = ctx.fetcher.fetch(url, headers=self._headers("application/json"))
        payload = json.loads(resp.content.decode("utf-8"))
        rows = payload.get("data") or []
        if not rows:
            raise RuntimeError("PBS API 沒有回傳任何 schedule，無法判斷當期版本")
        row = rows[0]
        return str(row["schedule_code"]), row.get("effective_date", "")

    def download(self, ctx):
        # 公開 API 有全體共用的速率限制，強制拉長本網域的請求間隔
        ctx.fetcher.min_interval = max(ctx.fetcher.min_interval, MIN_INTERVAL)

        schedule, effective = self._latest_schedule(ctx)
        ctx.log(f"　當期 schedule {schedule}（生效日 {effective}）")

        out = []
        page = 1
        while True:
            url = (f"{BASE_URL}/items?schedule_code={schedule}"
                   f"&limit={PAGE_SIZE}&page={page}")
            ctx.log(f"　下載第 {page} 頁（每頁 {PAGE_SIZE:,} 筆，"
                    f"官方規定每 20 秒 1 次）")
            resp = ctx.fetcher.fetch(url, headers=self._headers())
            text, _ = decode(resp.content)
            rows = list(csv.reader(io.StringIO(text)))
            data_rows = max(len(rows) - 1, 0)
            if data_rows == 0:
                break

            rel, digest = ctx.store.save(
                self.country, f"items_{schedule}_p{page}.csv", resp.content,
                source_url=url, status=resp.status, ssl_mode=resp.ssl_mode,
                data_version=effective, source_track=self.track,
                notes=f"PBS items 第 {page} 頁")
            out.append(Downloaded(
                path=os.path.join(ctx.store.root, rel), rel_path=rel,
                sha256=digest, source_url=url, data_version=effective,
                label=f"items 第 {page} 頁", ssl_mode=resp.ssl_mode))
            ctx.log(f"　　{data_rows:,} 筆")

            if data_rows < PAGE_SIZE:
                break
            page += 1
        return out

    def parse(self, ctx, downloaded):
        records = []
        for item in downloaded:
            with open(item.path, "rb") as fh:
                text, _ = decode(fh.read())
            reader = csv.DictReader(io.StringIO(text))

            for row_number, row in enumerate(reader, start=2):
                strength_value, strength_unit = parse_strength(
                    row.get("li_drug_name") or row.get("drug_name") or "")
                pack_value, pack_unit, _ = parse_pack_size(row.get("pack_size") or "")
                if not pack_unit:
                    _, pack_unit, _ = parse_pack_size(row.get("unit_of_measure") or "")

                originator = ""
                if (row.get("originator_brand_indicator") or "").strip().upper() in ("Y", "YES", "TRUE", "1"):
                    originator = "原廠藥（originator brand）"
                elif (row.get("innovator_indicator") or "").strip().upper() in ("Y", "YES", "TRUE", "1"):
                    originator = "原研藥（innovator）"
                elif row.get("originator_brand_indicator"):
                    originator = "非原廠藥"

                for column, category in PRICE_COLUMNS:
                    price = clean_number(row.get(column))
                    if not price or float(price or 0) == 0:
                        continue

                    record = self._base_record(item)
                    record.native_code_type = "PBS code"
                    record.native_code = row.get("pbs_code", "")
                    record.brand_name = row.get("brand_name", "")
                    record.generic_name = (row.get("li_drug_name")
                                           or row.get("drug_name") or "")
                    record.form = (row.get("li_form")
                                   or row.get("schedule_form") or "")
                    record.strength_value = ("" if strength_value is None
                                             else f"{strength_value:g}")
                    record.strength_unit = strength_unit
                    record.pack_size_value = ("" if pack_value is None
                                              else f"{pack_value:g}")
                    record.pack_size_unit = pack_unit
                    record.price = price
                    record.price_category = category
                    record.price_category_label = PriceCategory.label(category)
                    record.marketer = row.get("manufacturer_code", "")
                    record.originator_flag = originator
                    record.first_listed_date = row.get("first_listed_date", "")
                    record.source_row = f"{item.label} 第 {row_number} 列／{column}"
                    record.notes = "；".join(part for part in (
                        f"給藥途徑：{row.get('moa_preferred_term')}"
                        if row.get("moa_preferred_term") else "",
                        f"處方集：{row.get('formulary')}"
                        if row.get("formulary") else "",
                        f"計價數量：{row.get('pricing_quantity')}"
                        if row.get("pricing_quantity") else "",
                        f"療效群組：{row.get('therapeutic_group_title')}"
                        if row.get("therapeutic_group_title") else "",
                    ) if part)
                    record.compute_unit_price()
                    records.append(record)
        return records


SOURCE = AustraliaPBS()

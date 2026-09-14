# -*- coding: utf-8 -*-
"""十國工作流總表。

**每個國家都有一條明確的路徑**，不是只有能自動化的才列出來。
自動不了的國家會產生人工待辦清單，並在介面上標示原因，
避免同仁誤以為是程式漏抓。

三種執行方式
------------
``AUTO``　　程式自動下載整批檔並轉換
``MANUAL``　程式產生待辦清單與可直接點擊的查詢網址，由人操作後登錄
``BLOCKED``　需帳號密碼或官方未公開，本工具不涵蓋，僅列出說明

兩軌來源
--------
``batch``　　整批檔來源（A 軌，可機讀）
``manual_site``　操作手冊指定的查詢網站（B 軌，逐筆查詢頁，供截圖存證）

僅使用 Python 標準函式庫。
"""

import dataclasses
import urllib.parse

__all__ = ["COUNTRIES", "Country", "AUTO", "MANUAL", "BLOCKED",
           "all_codes", "get_country", "build_worklist"]

AUTO = "AUTO"
MANUAL = "MANUAL"
BLOCKED = "BLOCKED"

METHOD_LABELS = {
    AUTO: "程式自動下載",
    MANUAL: "人工操作（程式產生待辦清單）",
    BLOCKED: "本工具不涵蓋",
}


@dataclasses.dataclass(frozen=True)
class Country:
    code: str
    name: str
    method: str
    batch_agency: str = ""
    batch_note: str = ""
    manual_site: str = ""          # 手冊指定的查詢網站名稱
    manual_url: str = ""           # 查詢頁網址
    search_template: str = ""      # 可帶查詢字串的網址，``{q}`` 會被取代
    steps: tuple = ()              # 人工操作步驟
    reason: str = ""               # 無法自動化的原因
    next_step: str = ""            # 建議的後續處理

    def search_url(self, keyword):
        """組出可直接點擊的查詢網址。沒有樣板就回傳查詢頁本身。"""
        if not self.search_template:
            return self.manual_url
        return self.search_template.replace(
            "{q}", urllib.parse.quote(str(keyword or "")))


COUNTRIES = [
    Country(
        code="JP", name="日本", method=AUTO,
        batch_agency="厚生労働省（MHLW）",
        batch_note="薬価基準収載品目リスト，每次藥價改定後網址會變，程式自動抓當期",
        manual_site="厚生労働省", manual_url="https://www.mhlw.go.jp/",
    ),
    Country(
        code="FR", name="法國（藥局零售 CIP）", method=AUTO,
        batch_agency="ANSM／HAS 公開藥品資料庫",
        batch_note="四個檔案以 Code CIS 合併，含成分組成與學名藥群組",
        manual_site="BdM_IT（CNAM 健保局）",
        manual_url="http://www.codage.ext.cnamts.fr/codif/bdm_it/index.php?p_site=AMELI",
    ),
    Country(
        code="BE", name="比利時", method=AUTO,
        batch_agency="INAMI／RIZIV 聯邦健康保險署",
        batch_note="每月 1 日發布，價格依五種交付模式分列",
        manual_site="CBIP（比利時藥物資訊中心）",
        manual_url="https://www.cbip.be/fr/start",
        search_template="https://www.cbip.be/fr/search?q={q}",
    ),
    Country(
        code="SE", name="瑞典", method=AUTO,
        batch_agency="TLV 藥物福利委員會",
        batch_note="每日更新，AIP 與 AUP 兩種價格",
        manual_site="FASS（藥廠公會資訊網）",
        manual_url="https://www.fass.se/LIF/startpage?userType=2",
        search_template="https://www.fass.se/LIF/result?query={q}&userType=2",
    ),
    Country(
        code="AU", name="澳洲", method=AUTO,
        batch_agency="PBS 公開 API（Department of Health）",
        batch_note="每 20 秒 1 次請求的速率限制由全體使用者共用",
        manual_site="PBS", manual_url="https://www.pbs.gov.au/browse/medicine-listing",
        search_template="https://www.pbs.gov.au/search?q={q}",
    ),
    Country(
        code="CA-SK", name="加拿大薩克其萬省", method=AUTO,
        batch_agency="Saskatchewan Drug Plan（DPEB／eHealth Saskatchewan）",
        batch_note="固定寬度純文字檔，附官方欄位版面說明。2026-09 重新查證後改列為可自動化",
        manual_site="Online Formulary",
        manual_url="https://formulary.drugplan.ehealthsask.ca/SearchFormulary",
    ),
    Country(
        code="DE", name="德國", method=MANUAL,
        batch_agency="BfArM（Festbeträge 法定發布平台）",
        batch_note="逐筆價格目前僅有 PDF（約 4 MB，每月 1 日與 15 日更新）",
        manual_site="ROTE LISTE（民間出版商，需帳密）",
        manual_url="https://www.rote-liste.de/",
        reason=("BfArM 的固定給付額全品項清單目前只有 PDF，沒有 CSV 或 XML。"
                "G-BA 的 XML 雖可整批下載，但內容是效益評估決議，不含價格。"),
        steps=(
            "開啟 BfArM 的 Festbeträge 頁面，下載當期的 festbetraege-YYYYMMDD.pdf",
            "在 PDF 內搜尋目標藥品的 PZN 或藥品名",
            "記下固定給付額（Festbetrag）與藥局零售價（Apothekenverkaufspreis）",
            "截圖存證，並在本工具的佐證作業頁登錄",
        ),
        next_step=("待辦：撰寫 BfArM PDF 解析程式，或洽 GKV-Spitzenverband "
                   "詢問是否有結構化資料傳輸管道。"
                   "另注意 2025 年起部分品項改採保密給付價，淨價不再公開。"),
    ),
    Country(
        code="CH", name="瑞士", method=MANUAL,
        batch_agency="BAG 聯邦衛生署",
        batch_note="原整批下載網址已失效",
        manual_site="compendium.ch（民間藥品資料庫）",
        manual_url="https://compendium.ch/",
        search_template="https://compendium.ch/search?q={q}",
        reason=("BAG 的專科藥品清單（SL）網站已改版為單頁應用程式，"
                "原本的 Publications.xlsx 網址回應 404，"
                "新的後端 API（epl.bag.admin.ch/api/sl/）需要驗證才能存取，"
                "官方資料正轉向 FHIR 格式發布。"),
        steps=(
            "開啟 sl.bag.admin.ch 的專科藥品清單查詢頁",
            "查詢目標藥品，記下 FAP（廠商出廠價）與 PP（藥局零售價）",
            "注意兩者是不同層級的價格，不可混用",
            "截圖存證並於佐證作業頁登錄",
        ),
        next_step=("待辦：洽 BAG 詢問新版整批下載或 FHIR 端點的公開存取方式。"
                   "參考 fhir.ch/ig/ch-epl 與 github.com/bag-epl。"),
    ),
    Country(
        code="UK", name="英國", method=MANUAL,
        batch_agency="NHS TRUD（dm+d）",
        batch_note="有整批 XML，但需要個人帳號與 API 金鑰",
        manual_site="NHS dm+d browser",
        manual_url="https://services.nhsbsa.nhs.uk/dmd-browser/",
        search_template="https://services.nhsbsa.nhs.uk/dmd-browser/search?q={q}",
        reason=("TRUD 的整批下載需要個人帳號與 API 金鑰。"
                "金鑰屬個人憑證，由誰申請、如何保管，屬管理決定，"
                "本工具不代為保存。"),
        steps=(
            "至 isd.digital.nhs.uk/trud 申請免費帳號並取得 API 金鑰",
            "由資訊窗口決定金鑰的保管方式後，設定環境變數 TRUD_API_KEY",
            "金鑰設定完成後，本國即可改為自動下載",
        ),
        next_step="待辦：金鑰取得後啟用自動下載並以真實檔案驗證。",
    ),
    Country(
        code="US", name="美國", method=BLOCKED,
        batch_agency="無官方免費整批來源",
        manual_site="Micromedex Red Book（需帳號密碼）",
        manual_url="https://www.micromedexsolutions.com/",
        reason=("Micromedex Red Book 為付費訂閱資料庫，需帳號密碼登入，"
                "且其使用條款通常禁止自動化擷取。本工具不涵蓋。"),
        steps=(
            "以單位訂閱帳號登入 Micromedex Red Book",
            "逐筆查詢目標藥品並記錄價格",
            "截圖存證並於佐證作業頁登錄",
        ),
        next_step="待辦：確認是否有其他官方或免費的美國藥價替代來源。",
    ),
]

BY_CODE = {country.code: country for country in COUNTRIES}


def all_codes():
    return [country.code for country in COUNTRIES]


def get_country(code):
    key = (code or "").strip().upper()
    if key not in BY_CODE:
        raise KeyError(f"沒有這個國家代碼：{code}\n"
                       f"　可用的代碼：{'、'.join(all_codes())}")
    return BY_CODE[key]


def build_worklist(queries, codes=None):
    """為需要人工處理的國家產生待辦清單。

    回傳每個國家一個項目，含原因、操作步驟，以及每個藥品可直接點擊的網址。
    """
    selected = [BY_CODE[c] for c in (codes or all_codes()) if c in BY_CODE]
    out = []
    for country in selected:
        if country.method == AUTO:
            continue
        items = []
        for query in queries:
            keyword = query.brand_name or query.generic_name
            if not keyword:
                continue
            items.append({
                "商品名": query.brand_name,
                "成分名": query.generic_name,
                "查詢網址": country.search_url(keyword),
            })
        out.append({
            "代碼": country.code,
            "國家": country.name,
            "執行方式": METHOD_LABELS[country.method],
            "原因": country.reason,
            "查詢網站": country.manual_site,
            "查詢頁": country.manual_url,
            "操作步驟": list(country.steps),
            "後續處理": country.next_step,
            "待查藥品": items,
        })
    return out

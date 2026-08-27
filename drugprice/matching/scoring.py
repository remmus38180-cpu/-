# -*- coding: utf-8 -*-
"""候選排序的計分規則。

設計原則
--------
**說明文字與計分規則來自同一張表。** 底下的 ``DRUG_RULES`` 與
``ORIGINATOR_RULES`` 既是計分依據，也是介面上顯示給人看的說明來源。
兩者同源，程式不可能算一套、講另一套。

**分成兩個獨立分數，不合併成一個。** 人在做的其實是兩件事：

1. 這筆是不是我要找的那個藥？　　→ 藥品相符度
2. 這筆是不是原廠藥？　　　　　　→ 原廠可能性

混成一個分數會讓人看不出高分是因為藥對、還是因為像原廠。分開才判讀得動。

**排序不是決定。** 所有候選都會列出，分數只影響先後順序。
最終選哪一筆由人勾選，程式不預先選定。

僅使用 Python 標準函式庫。
"""

import dataclasses

from ..core.units import normalize_name, parse_strength, strip_salt
from .kana import looks_japanese, similarity

__all__ = ["DRUG_RULES", "ORIGINATOR_RULES", "Rule", "Query",
           "score_drug_match", "score_originator", "rules_table"]


@dataclasses.dataclass(frozen=True)
class Rule:
    """一條計分規則。``points`` 為正代表加分，為負代表扣分。"""

    key: str
    points: int
    description: str
    note: str = ""


# --- 藥品相符度：這筆是不是我要找的那個藥 ---
DRUG_RULES = [
    Rule("ingredient_exact", 50, "成分名完全相符",
         "成分名是跨國唯一穩定的識別依據，因此權重最高"),
    Rule("ingredient_salt", 45, "成分名相符（去除鹽類或水合物字尾後）",
         "如 apixaban 對上 apixaban maleate"),
    Rule("ingredient_partial", 25, "成分名部分相符",
         "一方包含另一方，常見於複方藥"),
    Rule("ingredient_romaji_high", 45, "成分名以片假名轉寫後高度近似",
         "日本的藥價檔用片假名寫成分名，轉成羅馬字後比對。"
         "近似度 0.90 以上才給這個分數"),
    Rule("ingredient_romaji", 35, "成分名以片假名轉寫後近似相符",
         "近似度 0.75 以上。這是近似比對不是翻譯，請自行確認"),
    Rule("atc_exact", 30, "ATC 代碼完全相符（7 碼）"),
    Rule("atc_class", 10, "ATC 分類相符（前 5 碼）",
         "同一藥理次分類，但成分可能不同"),
    Rule("brand_exact", 45, "商品名完全相符"),
    Rule("brand_token", 35, "記錄的商品名包含查詢的商品名",
         "各國常把含量與劑型寫進商品名，如「ELIQUIS 2,5 mg, comprimé "
         "pelliculé」包含「Eliquis」"),
    Rule("brand_partial", 15, "商品名部分相符"),
    Rule("brand_romaji", 25, "商品名以片假名轉寫後近似相符"),
    Rule("strength_match", 12, "含量相符"),
    Rule("form_match", 8, "劑型相符"),
]

# 商品名同時計入兩個分數，這是刻意的：商品名相符既是「這是不是我要找的藥」
# 的證據，也是「這是不是原廠」的證據（學名藥通常不會沿用原廠商品名）。
# 兩邊的規則描述都會顯示出來，不會讓人以為只算了一次。

# --- 原廠可能性：這筆是不是原廠藥 ---
ORIGINATOR_RULES = [
    Rule("official_originator", 60, "該國官方檔案標示為原廠藥",
         "官方欄位，非推估。但各國定義不同，仍需人工確認"),
    Rule("official_innovator", 55, "該國官方檔案標示為原研藥"),
    Rule("official_bio_reference", 55, "該國官方檔案標示為生物原廠藥"),
    Rule("brand_exact", 25, "商品名與輸入完全相符"),
    Rule("brand_normalized", 20, "記錄的商品名包含查詢的商品名"),
    Rule("brand_partial", 10, "商品名部分相符"),
    Rule("marketer_match", 15, "藥商名與輸入相符"),
    Rule("official_generic", -40, "該國官方檔案標示為學名藥",
         "扣分而非排除，因為官方分類偶有例外，仍列出供人核對"),
    Rule("brand_romaji", 18, "商品名以片假名轉寫後近似相符"),
]

# 片假名轉寫的近似度門檻。以實際藥名測試，正確配對最低 0.80、
# 錯誤配對最高 0.62，門檻取 0.75 可清楚分開兩者。
ROMAJI_HIGH = 0.90
ROMAJI_MIN = 0.75

DRUG_BY_KEY = {rule.key: rule for rule in DRUG_RULES}
ORIGINATOR_BY_KEY = {rule.key: rule for rule in ORIGINATOR_RULES}

MAX_SCORE = 100


def rules_table():
    """回傳可直接顯示給使用者的規則說明，供介面與文件共用。"""
    return {
        "藥品相符度": [dataclasses.asdict(rule) for rule in DRUG_RULES],
        "原廠可能性": [dataclasses.asdict(rule) for rule in ORIGINATOR_RULES],
        "上限": MAX_SCORE,
        "排序方式": [
            "先依「藥品相符度」由高到低",
            "相同時依「原廠可能性」由高到低",
            "再相同時依「單位藥價」由低到高",
        ],
        "說明": ("分數只決定先後順序，不代表程式已經選定。"
                 "所有候選都會列出，最終由您勾選。"),
    }


@dataclasses.dataclass
class Query:
    """一列要查的藥品。除商品名外其餘欄位可留空。"""

    brand_name: str = ""
    generic_name: str = ""
    atc_code: str = ""
    strength: str = ""
    form: str = ""
    marketer: str = ""

    def __post_init__(self):
        self.brand_norm = normalize_name(self.brand_name)
        self.generic_norm = normalize_name(self.generic_name)
        self.generic_salt = strip_salt(self.generic_name)
        self.atc_norm = (self.atc_code or "").strip().upper()
        self.marketer_norm = normalize_name(self.marketer)
        self.form_norm = normalize_name(self.form)
        self.strength_value, self.strength_unit = parse_strength(self.strength)


def _brand_relation(query_brand, query_norm, record_brand):
    """判斷兩個商品名的關係，回傳規則 key 或 None。

    以「詞」為單位比對，避免 "eli" 誤中 "eliquis" 這類假相符。
    """
    if not query_brand or not record_brand:
        return None
    if record_brand.strip().lower() == query_brand.strip().lower():
        return "brand_exact"
    record_norm = normalize_name(record_brand)
    if record_norm == query_norm:
        return "brand_exact"
    query_tokens = [t for t in query_norm.split() if t]
    record_tokens = set(record_norm.split())
    if query_tokens and all(token in record_tokens for token in query_tokens):
        return "brand_token"
    if query_norm and (query_norm in record_norm or record_norm in query_norm):
        return "brand_partial"
    return None


def _hit(hits, table, key, detail=""):
    """記下一條命中的規則。detail 會顯示在排序依據裡，例如近似度數值。"""
    rule = table[key]
    hits.append((rule, detail))
    return rule.points


def score_drug_match(query, record):
    """計算藥品相符度，回傳 (分數, 命中的規則清單)。"""
    hits = []
    score = 0

    record_generic = normalize_name(record.generic_name)
    record_brand = normalize_name(record.brand_name)
    target = query.generic_norm or query.brand_norm

    # 成分名。有些國家的檔案沒有獨立成分名欄位，此時退而用商品名比對。
    haystack = record_generic or record_brand
    raw_haystack = record.generic_name or record.brand_name
    raw_target = query.generic_name or query.brand_name
    if target and haystack:
        if haystack == target:
            score += _hit(hits, DRUG_BY_KEY, "ingredient_exact")
        elif query.generic_name and strip_salt(record.generic_name) == query.generic_salt:
            score += _hit(hits, DRUG_BY_KEY, "ingredient_salt")
        elif target in haystack or haystack in target:
            score += _hit(hits, DRUG_BY_KEY, "ingredient_partial")
        elif looks_japanese(raw_haystack) or looks_japanese(raw_target):
            ratio = similarity(raw_haystack, raw_target)
            if ratio >= ROMAJI_HIGH:
                score += _hit(hits, DRUG_BY_KEY, "ingredient_romaji_high",
                              f"近似度 {ratio:.2f}")
            elif ratio >= ROMAJI_MIN:
                score += _hit(hits, DRUG_BY_KEY, "ingredient_romaji",
                              f"近似度 {ratio:.2f}")

    relation = _brand_relation(query.brand_name, query.brand_norm,
                               record.brand_name)
    if relation:
        score += _hit(hits, DRUG_BY_KEY, relation)
    elif query.brand_name and record.brand_name and (
            looks_japanese(record.brand_name) or looks_japanese(query.brand_name)):
        ratio = similarity(record.brand_name, query.brand_name)
        if ratio >= ROMAJI_MIN:
            score += _hit(hits, DRUG_BY_KEY, "brand_romaji", f"近似度 {ratio:.2f}")

    if query.atc_norm and record.atc_code:
        record_atc = record.atc_code.strip().upper()
        if record_atc == query.atc_norm:
            score += _hit(hits, DRUG_BY_KEY, "atc_exact")
        elif len(query.atc_norm) >= 5 and record_atc[:5] == query.atc_norm[:5]:
            score += _hit(hits, DRUG_BY_KEY, "atc_class")

    if query.strength_value is not None and record.strength_value:
        try:
            same_value = abs(float(record.strength_value) - query.strength_value) < 1e-9
        except ValueError:
            same_value = False
        same_unit = (not query.strength_unit or not record.strength_unit
                     or record.strength_unit.lower() == query.strength_unit.lower())
        if same_value and same_unit:
            score += _hit(hits, DRUG_BY_KEY, "strength_match")

    if query.form_norm and record.form:
        record_form = normalize_name(record.form)
        if query.form_norm in record_form or record_form in query.form_norm:
            score += _hit(hits, DRUG_BY_KEY, "form_match")

    return min(score, MAX_SCORE), hits


def score_originator(query, record, country_has_official_flag=True):
    """計算原廠可能性，回傳 (分數, 命中的規則清單, 提醒文字)。"""
    hits = []
    score = 0
    caution = ""

    flag = record.originator_flag or ""
    if flag.startswith("生物原廠藥"):
        score += _hit(hits, ORIGINATOR_BY_KEY, "official_bio_reference")
    elif flag.startswith("原研藥"):
        score += _hit(hits, ORIGINATOR_BY_KEY, "official_innovator")
    elif flag.startswith("原廠藥"):
        score += _hit(hits, ORIGINATOR_BY_KEY, "official_originator")
    elif flag.startswith(("學名藥", "非原廠藥", "仿製藥")):
        score += _hit(hits, ORIGINATOR_BY_KEY, "official_generic")

    if not country_has_official_flag:
        caution = ("此來源的官方檔案沒有原廠／學名藥註記欄位，"
                   "本欄僅依商品名與藥商名推估，可信度低於有官方註記的國家。")
        if not query.marketer:
            caution += ("清單中若補上藥商名（如 Bristol-Myers Squibb），"
                        "可把原廠與平行輸入商區分開來。")

    relation = _brand_relation(query.brand_name, query.brand_norm,
                               record.brand_name)
    if relation == "brand_exact":
        score += _hit(hits, ORIGINATOR_BY_KEY, "brand_exact")
    elif relation == "brand_token":
        score += _hit(hits, ORIGINATOR_BY_KEY, "brand_normalized")
    elif relation == "brand_partial":
        score += _hit(hits, ORIGINATOR_BY_KEY, "brand_partial")
    elif query.brand_name and record.brand_name and (
            looks_japanese(record.brand_name) or looks_japanese(query.brand_name)):
        ratio = similarity(record.brand_name, query.brand_name)
        if ratio >= ROMAJI_MIN:
            score += _hit(hits, ORIGINATOR_BY_KEY, "brand_romaji",
                          f"近似度 {ratio:.2f}")

    if query.marketer_norm and record.marketer:
        record_marketer = normalize_name(record.marketer)
        if (query.marketer_norm in record_marketer
                or record_marketer in query.marketer_norm):
            score += _hit(hits, ORIGINATOR_BY_KEY, "marketer_match")

    return max(0, min(score, MAX_SCORE)), hits, caution

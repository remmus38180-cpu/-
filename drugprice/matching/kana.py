# -*- coding: utf-8 -*-
"""片假名轉羅馬字，供跨語言的成分名比對。

為什麼需要
----------
日本的藥價檔用片假名寫成分名與商品名（アピキサバン、エリキュース），
查詢清單通常是英文（apixaban、Eliquis），直接比對一定比不到。

作法是把片假名機械轉寫成羅馬字，再做近似比對::

    アピキサバン → apikisaban → 與 apixaban 近似度 0.82

**這是近似比對，不是翻譯。** 轉寫後仍不相符的品項不會被排除，只是分數較低；
而且比對結果一律標示為「片假名轉寫近似相符」，讓人知道這一筆的依據
比完全相符弱，需要自己確認。

日文外來語的幾個規律會影響比對，已在正規化時處理：

* 日文沒有 L 音，一律寫成 ラ行 → 轉寫後 r 與 l 視為同一個音
* 長音（ー）與重複母音只是拉長同一個音 → 壓縮
* 促音（ッ）表示下一個子音加倍 → 壓縮
* 英文的 x 常寫成 キサ／クス → 轉寫後 ks 與 x 視為相近

僅使用 Python 標準函式庫。
"""

import difflib
import re
import unicodedata

__all__ = ["to_romaji", "romaji_key", "consonant_key", "similarity",
           "looks_japanese"]

# 兩字元的拗音要先換，否則會被逐字拆開
DIGRAPHS = {
    "キャ": "kya", "キュ": "kyu", "キョ": "kyo",
    "シャ": "sha", "シュ": "shu", "ショ": "sho", "シェ": "she",
    "チャ": "cha", "チュ": "chu", "チョ": "cho", "チェ": "che",
    "ニャ": "nya", "ニュ": "nyu", "ニョ": "nyo",
    "ヒャ": "hya", "ヒュ": "hyu", "ヒョ": "hyo",
    "ミャ": "mya", "ミュ": "myu", "ミョ": "myo",
    "リャ": "rya", "リュ": "ryu", "リョ": "ryo",
    "ギャ": "gya", "ギュ": "gyu", "ギョ": "gyo",
    "ジャ": "ja", "ジュ": "ju", "ジョ": "jo", "ジェ": "je",
    "ビャ": "bya", "ビュ": "byu", "ビョ": "byo",
    "ピャ": "pya", "ピュ": "pyu", "ピョ": "pyo",
    "ファ": "fa", "フィ": "fi", "フェ": "fe", "フォ": "fo", "フュ": "fyu",
    "ヴァ": "va", "ヴィ": "vi", "ヴェ": "ve", "ヴォ": "vo", "ヴュ": "vyu",
    "ティ": "ti", "トゥ": "tu", "ディ": "di", "ドゥ": "du",
    "ウィ": "wi", "ウェ": "we", "ウォ": "wo",
    "ツァ": "tsa", "ツィ": "tsi", "ツェ": "tse", "ツォ": "tso",
    "シィ": "si", "ズィ": "zi", "チィ": "chi",
}

SINGLES = {
    "ア": "a", "イ": "i", "ウ": "u", "エ": "e", "オ": "o",
    "カ": "ka", "キ": "ki", "ク": "ku", "ケ": "ke", "コ": "ko",
    "サ": "sa", "シ": "shi", "ス": "su", "セ": "se", "ソ": "so",
    "タ": "ta", "チ": "chi", "ツ": "tsu", "テ": "te", "ト": "to",
    "ナ": "na", "ニ": "ni", "ヌ": "nu", "ネ": "ne", "ノ": "no",
    "ハ": "ha", "ヒ": "hi", "フ": "fu", "ヘ": "he", "ホ": "ho",
    "マ": "ma", "ミ": "mi", "ム": "mu", "メ": "me", "モ": "mo",
    "ヤ": "ya", "ユ": "yu", "ヨ": "yo",
    "ラ": "ra", "リ": "ri", "ル": "ru", "レ": "re", "ロ": "ro",
    "ワ": "wa", "ヲ": "o", "ン": "n",
    "ガ": "ga", "ギ": "gi", "グ": "gu", "ゲ": "ge", "ゴ": "go",
    "ザ": "za", "ジ": "ji", "ズ": "zu", "ゼ": "ze", "ゾ": "zo",
    "ダ": "da", "ヂ": "ji", "ヅ": "zu", "デ": "de", "ド": "do",
    "バ": "ba", "ビ": "bi", "ブ": "bu", "ベ": "be", "ボ": "bo",
    "パ": "pa", "ピ": "pi", "プ": "pu", "ペ": "pe", "ポ": "po",
    "ヴ": "vu",
    "ァ": "a", "ィ": "i", "ゥ": "u", "ェ": "e", "ォ": "o",
    "ャ": "ya", "ュ": "yu", "ョ": "yo",
}

_KANA = re.compile(r"[゠-ヿ぀-ゟ]")


def looks_japanese(text):
    """字串裡有沒有假名。"""
    return bool(_KANA.search(str(text or "")))


def to_romaji(text):
    """把片假名轉成羅馬字。非假名的字元原樣保留。"""
    if not text:
        return ""
    # 平假名先轉片假名，全形數字與符號轉半形
    text = unicodedata.normalize("NFKC", str(text))
    text = "".join(
        chr(ord(ch) + 0x60) if "ぁ" <= ch <= "ゖ" else ch
        for ch in text)

    out = []
    index = 0
    while index < len(text):
        pair = text[index:index + 2]
        if pair in DIGRAPHS:
            out.append(DIGRAPHS[pair])
            index += 2
            continue

        char = text[index]
        if char == "ッ":                      # 促音：下一個子音加倍
            following = text[index + 1:index + 3]
            romaji = DIGRAPHS.get(following) or SINGLES.get(text[index + 1], "")
            if romaji:
                out.append(romaji[0])
            index += 1
            continue
        if char == "ー":                      # 長音：拉長前一個母音
            if out and out[-1] and out[-1][-1] in "aiueo":
                out.append(out[-1][-1])
            index += 1
            continue

        out.append(SINGLES.get(char, char))
        index += 1
    return "".join(out)


# 讓日文轉寫與英文拼寫靠攏的替換。順序有意義，由長到短。
_SOUND_RULES = [
    ("shi", "si"), ("chi", "ti"), ("tsu", "tu"), ("sha", "sya"),
    ("shu", "syu"), ("sho", "syo"), ("cha", "tya"), ("chu", "tyu"),
    ("cho", "tyo"), ("fu", "hu"), ("x", "ks"), ("qu", "ku"), ("ph", "h"),
    ("th", "t"), ("ck", "k"),
]

_VOWELS = "aiueo"


def romaji_key(text):
    """轉成可比對的鍵值，把日英拼寫的常見差異壓平。

    ``chi`` → ``ti``、``shi`` → ``si`` 這類替換，是因為日文的
    ヘボン式轉寫與外來語的原始拼法不同（スタチン 的 チ 對應的是
    statin 的 ti，不是 chi）。
    """
    key = to_romaji(text).lower()
    for source, target in _SOUND_RULES:
        key = key.replace(source, target)
    # c 在 e、i、y 前發 s，其餘發 k，與英文拼寫規則一致
    key = re.sub(r"c(?=[eiy])", "s", key)
    key = key.replace("c", "k")
    key = re.sub(r"[^a-z]", "", key)
    key = key.replace("l", "r")               # 日文沒有 L 音
    key = key.replace("v", "b")               # 日文的 V 多寫成 バ行
    key = re.sub(r"(.)\1+", r"\1", key)       # 壓掉長音與促音造成的重複
    return key


def consonant_key(text):
    """只留子音的骨架。

    日文把外來語音節化時會插入英文沒有的母音
    （statin → スタチン → sutatin），只比子音可以避開這個差異。
    """
    return "".join(ch for ch in romaji_key(text) if ch not in _VOWELS)


def similarity(left, right):
    """兩個名稱的近似度，0 到 1。任一方是日文時先轉寫再比。

    同時比「完整轉寫」與「子音骨架」，取較高者。
    """
    if not left or not right:
        return 0.0
    full = difflib.SequenceMatcher(
        None, romaji_key(left), romaji_key(right)).ratio()
    skeleton = difflib.SequenceMatcher(
        None, consonant_key(left), consonant_key(right)).ratio()
    return max(full, skeleton)

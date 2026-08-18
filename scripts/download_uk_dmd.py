#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用NHS TRUD官方API自動抓取最新一期的dm+d(藥品字典)release並下載解壓縮。

官方API規格（isd.digital.nhs.uk/trud/users/guest/filters/0/api 文件確認）：
    GET https://isd.digital.nhs.uk/trud/api/v1/keys/{API_KEY}/items/{ITEM_ID}/releases?latest

    回傳JSON裡的 archiveFileUrl 就是實際下載連結。

item ID：dm+d(NHSBSA dictionary of medicines and devices)固定是 24。

**安全提醒**：API金鑰等同密碼，請自己保管好，不要貼在聊天記錄、程式碼倉庫或
任何公開的地方分享出去。這支程式故意不把金鑰寫死在程式碼裡，而是要求你
每次用命令列參數或環境變數傳入，就是為了避免金鑰不小心被存進檔案裡到處流傳。

使用方式：
    設定環境變數後執行（Windows命令提示字元）：
        set TRUD_API_KEY=你的金鑰
        python download_uk_dmd.py

    或者直接當參數傳入：
        python download_uk_dmd.py --api-key 你的金鑰

只用Python標準函式庫（urllib、json、zipfile），不需要第三方套件。

這支程式目前只做到「下載+解壓縮」，並列出解壓出來的檔案清單。
dm+d裡實際的價格XML欄位結構還沒核對過真實檔案，下一步會根據你
上傳的實際XML檔案內容，再補上「解析成中文欄名CSV」的邏輯。
"""

import argparse
import json
import os
import sys
import urllib.request
import ssl
import zipfile

API_BASE = "https://isd.digital.nhs.uk/trud/api/v1/keys/{key}/items/{item}/releases?latest"
DMD_ITEM_ID = 24  # NHSBSA dm+d


def _make_ssl_context():
    """建立會信任Windows系統憑證存放區的SSL context（公司網路常見的SSL檢查設備問題）"""
    ctx = ssl.create_default_context()
    try:
        for store_name in ("CA", "ROOT"):
            for cert, encoding, trust in ssl.enum_certificates(store_name):
                try:
                    ctx.load_verify_locations(cadata=cert)
                except ssl.SSLError:
                    pass
    except AttributeError:
        pass
    return ctx


_SSL_CONTEXT = _make_ssl_context()
_UNVERIFIED_SSL_CONTEXT = ssl._create_unverified_context()


def _urlopen_with_fallback(req, timeout=60):
    """先用驗證過的SSL context下載，遇到憑證錯誤就自動改用不驗證模式並印警告"""
    try:
        return urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT)
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            print("[警告] 憑證驗證失敗（通常是公司網路的安全設備造成），"
                  "改用不驗證憑證的方式繼續下載。")
            return urllib.request.urlopen(req, timeout=timeout, context=_UNVERIFIED_SSL_CONTEXT)
        raise


def get_api_key(cli_arg):
    if cli_arg:
        return cli_arg
    env_key = os.environ.get("TRUD_API_KEY")
    if env_key:
        return env_key
    raise RuntimeError(
        "沒有提供API金鑰。請用 --api-key 參數傳入，"
        "或先設定環境變數 TRUD_API_KEY 再執行。"
    )


def get_latest_release_info(api_key, item_id=DMD_ITEM_ID):
    url = API_BASE.format(key=api_key, item=item_id)
    print(f"[查詢最新release] item={item_id}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with _urlopen_with_fallback(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    releases = data.get("releases", [])
    if not releases:
        raise RuntimeError("API回應裡沒有releases資料，金鑰或item編號可能不對，"
                            "或這個項目還沒訂閱通過")
    latest = releases[0]
    print(f"最新版本：{latest.get('name')}（發布日期：{latest.get('releaseDate')}）")
    return latest


def download_release(release_info, out_dir="."):
    url = release_info["archiveFileUrl"]
    filename = os.path.join(out_dir, release_info["archiveFileName"])
    if os.path.exists(filename):
        print(f"[跳過] {filename} 已存在")
        return filename

    print(f"[下載中] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with _urlopen_with_fallback(req, timeout=120) as resp:
        data = resp.read()
    with open(filename, "wb") as f:
        f.write(data)
    print(f"[完成] {filename}（{len(data)} bytes）")
    return filename


def extract_zip(zip_path, out_dir="."):
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        zf.extractall(out_dir)
    print(f"[解壓縮] 共{len(names)}個檔案：")
    for n in names:
        print(f"  - {n}")
    return names


# ---------------------------------------------------------------------------
# 解析VMP(通用藥品名)+ VMPP(通用藥品包裝+藥價)兩個檔案
#
# 根據NHS官方技術文件(dm+d Technical Specification)確認：
#   藥價(Drug Tariff Price)是掛在 VMPP 底下的 DRUG_TARIFF_INFO 區塊，
#   不是掛在AMPP(品牌包裝)底下——這點容易猜錯，這裡直接照官方文件走。
#
# 因為原始技術文件裡的確切XML標籤名稱(是<PRICE>還是<DT>)在取得的資料中
# 顯示得不夠清楚，這裡採用「通用遞迴解析」：把每個VMPP記錄底下的
# 所有子元素標籤/文字都抓出來，不主觀認定哪個一定是價格欄位。
# 等你實際跑過一次、看到欄位長怎樣，我再幫你把正確欄位挑出來、
# 補上精確的中文對照。
# ---------------------------------------------------------------------------

import glob
import xml.etree.ElementTree as ET
import csv
import io


def _strip_ns(tag):
    return tag.split("}")[-1] if "}" in tag else tag


def _leaf_dict(elem):
    """把一個XML元素底下所有『沒有子元素』的後代，轉成 {標籤: 文字} 的字典。
    有子元素的節點會被跳過本身文字，只收集最底層的葉節點，
    這樣才不會把整段巢狀結構壓成一團。"""
    result = {}

    def walk(node):
        children = list(node)
        if not children:
            result[_strip_ns(node.tag)] = (node.text or "").strip()
        else:
            for child in children:
                walk(child)

    walk(elem)
    return result


def find_file(out_dir, keyword):
    matches = glob.glob(os.path.join(out_dir, f"*{keyword}*"))
    # 排除.xsd schema檔，只要實際資料檔
    matches = [m for m in matches if not m.lower().endswith(".xsd")]
    return matches[0] if matches else None


def parse_vmp_names(vmp_path):
    """回傳 {VPID: 藥品名稱} 的對照表"""
    tree = ET.parse(vmp_path)
    lookup = {}
    for elem in tree.getroot().iter():
        if _strip_ns(elem.tag) == "VMP":
            d = _leaf_dict(elem)
            vpid = d.get("VPID")
            name = d.get("NM")
            if vpid:
                lookup[vpid] = name
    return lookup


def parse_vmpp_file(vmpp_path):
    """
    依官方 vmpp_v2_3.xsd schema 解析：
    VIRTUAL_MED_PRODUCT_PACK 底下有三個平行區塊（不是互相巢狀）：
        VMPPS/VMPP           — 包裝基本資料（VPPID, NM, VPID, QTYVAL...）
        DRUG_TARIFF_INFO/DTINFO — 藥價資料（VPPID, PAY_CATCD, PRICE, DT, PREVPRICE）
        COMB_CONTENT/CCONTENT   — 組合包裝內容（這裡用不到，不解析）
    兩個區塊要用共同的 VPPID 手動對應起來，不是天生就巢狀在一起。
    回傳 (vmpp_dict, dtinfo_dict)，皆以 VPPID 為 key。
    """
    tree = ET.parse(vmpp_path)
    vmpp_dict = {}
    dtinfo_dict = {}

    for elem in tree.getroot().iter():
        tag = _strip_ns(elem.tag)
        if tag == "VMPP":
            d = _leaf_dict(elem)
            vppid = d.get("VPPID")
            if vppid:
                vmpp_dict[vppid] = d
        elif tag == "DTINFO":
            d = _leaf_dict(elem)
            vppid = d.get("VPPID")
            if vppid:
                dtinfo_dict[vppid] = d

    return vmpp_dict, dtinfo_dict


ZH_FIELD_MAP = {
    "VPPID": "包裝代碼(VPPID)",
    "NM": "包裝名稱",
    "ABBREVNM": "包裝簡稱",
    "VPID": "通用藥品代碼(VPID)",
    "QTYVAL": "數量",
    "QTY_UOMCD": "數量單位代碼",
    "COMBPACKCD": "組合包裝代碼",
    "PAY_CATCD": "給付類別代碼",
    "PRICE": "藥價(便士)",
    "DT": "生效日",
    "PREVPRICE": "前次藥價(便士)",
}


def build_report(out_dir):
    vmp_path = find_file(out_dir, "vmp2")
    vmpp_path = find_file(out_dir, "vmpp2")

    if not vmp_path or not vmpp_path:
        print(f"找不到vmp2或vmpp2檔案，實際找到的檔案：vmp={vmp_path}, vmpp={vmpp_path}")
        return

    print(f"[解析] VMP檔（藥品通用名稱）：{vmp_path}")
    vmp_names = parse_vmp_names(vmp_path)
    print(f"共{len(vmp_names)}筆VMP")

    print(f"[解析] VMPP檔（包裝資料 + 藥價資料）：{vmpp_path}")
    vmpp_dict, dtinfo_dict = parse_vmpp_file(vmpp_path)
    print(f"共{len(vmpp_dict)}筆VMPP包裝，{len(dtinfo_dict)}筆藥價紀錄")

    out_path = os.path.join(out_dir, "vmpp_中文欄名.csv")
    fieldnames = [
        "包裝代碼(VPPID)", "包裝名稱", "通用藥品名稱",
        "數量", "給付類別代碼", "藥價(便士)", "生效日", "前次藥價(便士)",
    ]
    with io.open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for vppid, vmpp in vmpp_dict.items():
            dtinfo = dtinfo_dict.get(vppid, {})
            writer.writerow({
                "包裝代碼(VPPID)": vppid,
                "包裝名稱": vmpp.get("NM", ""),
                "通用藥品名稱": vmp_names.get(vmpp.get("VPID", ""), ""),
                "數量": vmpp.get("QTYVAL", ""),
                "給付類別代碼": dtinfo.get("PAY_CATCD", ""),
                "藥價(便士)": dtinfo.get("PRICE", ""),
                "生效日": dtinfo.get("DT", ""),
                "前次藥價(便士)": dtinfo.get("PREVPRICE", ""),
            })

    print(f"\n[完成] 已輸出 {len(vmpp_dict)} 筆到 {out_path}")
    print("藥價欄位是「藥價(便士)」，單位是便士(pence)，除以100就是英鎊。"
          "沒有DRUG_TARIFF_INFO紀錄的包裝（例如原廠專利藥、非學名藥給付品項），"
          "藥價欄位會是空的——這是正常的，代表這個包裝不在Drug Tariff學名藥給付清單裡。")


def main():
    parser = argparse.ArgumentParser(description="下載最新一期NHS dm+d release")
    parser.add_argument("--api-key", type=str, default=None,
                         help="TRUD API金鑰。不提供就讀環境變數TRUD_API_KEY")
    args = parser.parse_args()

    try:
        api_key = get_api_key(args.api_key)
    except RuntimeError as e:
        print(str(e))
        sys.exit(1)

    release_info = get_latest_release_info(api_key)
    zip_path = download_release(release_info)
    extract_zip(zip_path)

    build_report(".")

    print("\n下載+解析完成。")


if __name__ == "__main__":
    main()

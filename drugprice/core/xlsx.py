# -*- coding: utf-8 -*-
"""以標準函式庫解析 xlsx。

xlsx 本質是 zip 包 XML。讀 ``xl/sharedStrings.xml``（共用字串表）與
``xl/worksheets/sheetN.xml``（儲存格資料）即可取出內容，不需要 openpyxl。

支援：共用字串、行內字串、公式的快取值、日期序號轉換、
稀疏列（中間跳過的儲存格自動補空字串）。

僅使用 Python 標準函式庫。
"""

import datetime
import re
import xml.etree.ElementTree as ET
import zipfile

__all__ = ["read_sheet", "sheet_names", "column_index"]

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"

_CELL_REF = re.compile(r"([A-Z]+)(\d+)")

# Excel 內建的日期格式代碼
_DATE_FORMATS = set(range(14, 23)) | set(range(45, 48)) | {27, 30, 36, 50, 57}
_EPOCH = datetime.datetime(1899, 12, 30)


def column_index(ref):
    """把儲存格參照（如 ``BC12``）的欄名轉成 0 起算的欄索引。"""
    match = _CELL_REF.match(ref or "")
    if not match:
        return None
    letters = match.group(1)
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


def _shared_strings(zf):
    try:
        data = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(data)
    strings = []
    for si in root.findall(f"{NS}si"):
        # 一個字串可能被拆成多個 <t>（不同格式的片段）
        strings.append("".join(t.text or "" for t in si.iter(f"{NS}t")))
    return strings


def _date_styles(zf):
    """回傳「套用日期格式的樣式索引」集合。"""
    try:
        root = ET.fromstring(zf.read("xl/styles.xml"))
    except KeyError:
        return set()

    custom_date = set()
    fmts = root.find(f"{NS}numFmts")
    if fmts is not None:
        for fmt in fmts.findall(f"{NS}numFmt"):
            code = (fmt.get("formatCode") or "").lower()
            if any(token in code for token in ("yy", "dd", "mm:ss", "hh")):
                try:
                    custom_date.add(int(fmt.get("numFmtId")))
                except (TypeError, ValueError):
                    pass

    styles = set()
    cell_xfs = root.find(f"{NS}cellXfs")
    if cell_xfs is None:
        return styles
    for index, xf in enumerate(cell_xfs.findall(f"{NS}xf")):
        try:
            fmt_id = int(xf.get("numFmtId") or 0)
        except ValueError:
            continue
        if fmt_id in _DATE_FORMATS or fmt_id in custom_date:
            styles.add(index)
    return styles


def sheet_names(path_or_file):
    """回傳活頁簿內的工作表名稱，順序與檔案一致。"""
    with zipfile.ZipFile(path_or_file) as zf:
        root = ET.fromstring(zf.read("xl/workbook.xml"))
        sheets = root.find(f"{NS}sheets")
        return [s.get("name") for s in sheets.findall(f"{NS}sheet")]


def _sheet_path(zf, sheet):
    """找出指定工作表對應的 XML 路徑。sheet 可為名稱或 0 起算索引。"""
    root = ET.fromstring(zf.read("xl/workbook.xml"))
    entries = root.find(f"{NS}sheets").findall(f"{NS}sheet")

    target = None
    if isinstance(sheet, int):
        if sheet < len(entries):
            target = entries[sheet]
    else:
        for entry in entries:
            if entry.get("name") == sheet:
                target = entry
                break
    if target is None:
        raise KeyError(f"活頁簿內找不到工作表：{sheet!r}")

    rel_id = target.get(f"{REL_NS}id")
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    for rel in rels.findall(f"{PKG_REL_NS}Relationship"):
        if rel.get("Id") == rel_id:
            path = rel.get("Target")
            if path.startswith("/"):
                return path.lstrip("/")
            if not path.startswith("xl/"):
                path = "xl/" + path
            return path
    raise KeyError(f"找不到工作表 {sheet!r} 對應的檔案")


def read_sheet(path_or_file, sheet=0, max_rows=None):
    """讀出一個工作表，回傳 list[list[str]]。

    所有值一律轉成字串；數值不做四捨五入，日期轉為 YYYY-MM-DD。
    """
    with zipfile.ZipFile(path_or_file) as zf:
        strings = _shared_strings(zf)
        date_styles = _date_styles(zf)
        data = zf.read(_sheet_path(zf, sheet))

    rows = []
    root = ET.fromstring(data)
    sheet_data = root.find(f"{NS}sheetData")
    if sheet_data is None:
        return rows

    for row_el in sheet_data.findall(f"{NS}row"):
        cells = []
        for cell in row_el.findall(f"{NS}c"):
            index = column_index(cell.get("r") or "")
            if index is not None:
                while len(cells) < index:
                    cells.append("")
            cells.append(_cell_value(cell, strings, date_styles))
        rows.append(cells)
        if max_rows and len(rows) >= max_rows:
            break
    return rows


def _cell_value(cell, strings, date_styles):
    cell_type = cell.get("t")

    if cell_type == "inlineStr":
        is_el = cell.find(f"{NS}is")
        if is_el is None:
            return ""
        return "".join(t.text or "" for t in is_el.iter(f"{NS}t"))

    value_el = cell.find(f"{NS}v")
    if value_el is None or value_el.text is None:
        return ""
    raw = value_el.text

    if cell_type == "s":
        try:
            return strings[int(raw)]
        except (ValueError, IndexError):
            return ""
    if cell_type in ("str", "e"):
        return raw
    if cell_type == "b":
        return "TRUE" if raw == "1" else "FALSE"

    # 數值。先看是不是日期格式
    try:
        style = int(cell.get("s") or -1)
    except ValueError:
        style = -1
    if style in date_styles:
        try:
            return (_EPOCH + datetime.timedelta(days=float(raw))).strftime("%Y-%m-%d")
        except (ValueError, OverflowError):
            pass

    # 去掉浮點誤差造成的尾數，但不改變有效位數
    try:
        number = float(raw)
    except ValueError:
        return raw
    if number.is_integer() and abs(number) < 1e15:
        return str(int(number))
    return repr(number) if len(repr(number)) < len(raw) else raw

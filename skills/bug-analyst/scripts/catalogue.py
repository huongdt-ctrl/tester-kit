#!/usr/bin/env python3
"""Doc danh muc Cause / Root cause tu sheet 'Define' cua template.

Tai sao doc tu 'Define' chu khong doc tu dropdown: nhan trong dropdown duoc noi
bang dau phay, nhung ban than mot so nhan CO dau phay ben trong
("SKI1.1 ... Requirement Definition, Basic Design") -> tach theo dau phay la
tach sai. Sheet 'Define' xep moi nhan mot dong o cot C nen khong co su nhap nhang do.

Cau truc that cua sheet 'Define' (da do):
    B1  "Cause Category"   -> tu day tro xuong la danh muc Cause
    B32 "Root cause"       -> tu day tro xuong la danh muc Root cause
    cot B = ten NHOM (REQ_, DES_, ...), cot C = tung nhan cu the
"""
DEFINE_SHEET = "Define"
GROUP_COL, ITEM_COL = 2, 3
ROOT_CAUSE_MARKER = "root cause"
MAX_SCAN_ROW = 200


def read(workbook):
    """Tra ve {'cause': [...], 'rootcause': [...]} theo dung thu tu trong sheet.

    Sheet 'Define' khong co / khong doc duoc -> tra ve dict rong, KHONG nem loi:
    thieu danh muc thi chi mat buoc va cho bang thong ke, khong dang lam hong
    ca file.
    """
    if DEFINE_SHEET not in workbook.sheetnames:
        return {}
    ws = workbook[DEFINE_SHEET]
    bucket, out = "cause", {"cause": [], "rootcause": []}
    for row in range(1, MAX_SCAN_ROW + 1):
        group = ws.cell(row=row, column=GROUP_COL).value
        if group and ROOT_CAUSE_MARKER in str(group).strip().lower():
            bucket = "rootcause"
            continue
        item = ws.cell(row=row, column=ITEM_COL).value
        if item is None:
            continue
        text = str(item).strip()
        if text and text not in out[bucket]:
            out[bucket].append(text)
    return {key: val for key, val in out.items() if val}


def complete(existing, full):
    """Nhan dang co trong bang thong ke + nhan co trong danh muc ma bang bo sot.

    Giu NGUYEN cach viet cua bang thong ke cho nhung nhan da co (template co o
    dat 2 dau cach, doi thanh 1 dau cach la COUNTIF khong khop nua), chi noi
    them nhung nhan that su thieu.
    """
    kept = [str(v).strip() for v in (existing or []) if v not in (None, "")]
    seen = set(kept)
    for label in (full or []):
        if label not in seen:
            kept.append(label)
            seen.add(label)
    return kept

#!/usr/bin/env python3
"""Sinh lai toan bo cong thuc thong ke cua sheet 'List bug'.

Skill KHONG dich cong thuc cu cua template -- no viet lai tu dau theo Layout.
Ly do: template goc co san 2 loi cong thuc, dich cong thuc sai chi tao ra cong
thuc sai o toa do moi.

Hai loi cua template duoc sua o day:
  - Section III (Milestone) dem $G$ (Priority) thay vi $E$ (Milestone), va chia
    phan tram cho $B$76 (TOTAL cua Priority) thay vi TOTAL cua chinh no.
  - Section VII (Root cause) viet COUNTIF($K$3:$K$39, $A$126:$A$151) -- tham so
    thu hai la ca dai o, khien moi dong tra ve cung mot so.
"""
from template_layout import DATA_START

PERCENT_FORMAT = "0.0%"


def clear_data_region(ws, layout, last_col=13):
    """Xoa du lieu mau cua template. Style + dropdown giu nguyen."""
    for row in layout.data_rows:
        for col in range(1, last_col + 1):
            ws.cell(row=row, column=col).value = None


def write_data_rows(ws, layout, rows):
    """Do danh sach bug da map vao vung data. rows: list dict theo key cot."""
    from template_layout import (COL_CAUSE, COL_EGG_ID, COL_EGG_NAME,
                                 COL_MILESTONE, COL_NO, COL_NOTE, COL_PRIORITY,
                                 COL_ROOT_CAUSE, COL_SCREEN, COL_SEVERITY,
                                 COL_TITLE, COL_TYPE)
    mapping = (
        (COL_NO, "no"), (COL_EGG_ID, "egg_id"), (COL_EGG_NAME, "egg_name"),
        (COL_SCREEN, "screen"), (COL_MILESTONE, "milestone"), (COL_TITLE, "title"),
        (COL_PRIORITY, "priority"), (COL_SEVERITY, "severity"), (COL_TYPE, "bug_type"),
        (COL_CAUSE, "cause"), (COL_ROOT_CAUSE, "root_cause"), (COL_NOTE, "note"),
    )
    capacity = layout.data_end - DATA_START + 1
    if len(rows) > capacity:
        # Ghi qua vung data la de len bang thong ke ben duoi -> hong file ma
        # khong bao gi. Chan o day de thanh loi ro rang.
        raise ValueError("Vung data chi chua duoc %d dong nhung co %d bug -- "
                         "Layout tinh thieu dong" % (capacity, len(rows)))
    for idx, item in enumerate(rows):
        row = DATA_START + idx
        for col, key in mapping:
            value = normalize_cell(item.get(key))
            ws["%s%d" % (col, row)] = value


def normalize_cell(value):
    """Cat dau cach dau/cuoi cua moi gia tri chu truoc khi ghi.

    BAT BUOC, khong phai lam dep: nhan cua bang thong ke duoc sinh tu chinh du
    lieu nay va da bi strip. Ghi "Sprint 3 " (con dau cach cuoi) trong khi nhan
    la "Sprint 3" thi COUNTIF cua Excel KHONG khop -- Excel bo qua hoa/thuong
    nhung KHONG bo qua dau cach -> bug do bien mat khoi thong ke, TOTAL im lang
    nho hon so bug.
    """
    if isinstance(value, str):
        value = value.strip()
    return value if value not in ("", None) else None


def write_block(ws, layout, block, labels=None):
    """Viet nhan + cong thuc COUNTIF/percent + dong TOTAL cho mot bang thong ke.

    Nhan duoc ghi cho MOI block, khong chi block dong: bang danh muc co dinh
    cung can ghi lai vi co the vua duoc noi them dong cho nhung muc ma template
    bo sot (vd 5 muc "... Other" cua bang Cause).
    """
    first, last, total = block["first"], block["last"], block["total"]
    label_col, count_col = block["label_col"], block["count_col"]
    pct_col, src_col = block["pct_col"], block["src_col"]
    ds, de = DATA_START, layout.data_end

    if labels is not None:
        labels = list(labels)
        for offset in range(block["slots"]):
            row = first + offset
            ws["%s%d" % (label_col, row)] = labels[offset] if offset < len(labels) else None

    for row in range(first, last + 1):
        ws["%s%d" % (count_col, row)] = (
            "=COUNTIF($%s$%d:$%s$%d,$%s%d)" % (src_col, ds, src_col, de, label_col, row))
        pct = ws["%s%d" % (pct_col, row)]
        # Chia cho TOTAL cua CHINH block nay -- template goc chia nham block khac.
        pct.value = "=IF($%s$%d=0,0,%s%d/$%s$%d)" % (
            count_col, total, count_col, row, count_col, total)
        pct.number_format = PERCENT_FORMAT

    ws["%s%d" % (label_col, total)] = "TOTAL"
    ws["%s%d" % (count_col, total)] = "=SUM(%s%d:%s%d)" % (count_col, first, count_col, last)
    total_pct = ws["%s%d" % (pct_col, total)]
    total_pct.value = "=SUM(%s%d:%s%d)" % (pct_col, first, pct_col, last)
    total_pct.number_format = PERCENT_FORMAT


def read_fixed_labels(ws, block):
    """Nhan danh muc co dinh (priority/severity/cause/root cause) doc thang tu
    template -- khong hardcode lai, tranh lech vi template co o dat 2 dau cach."""
    out = []
    for row in range(block["first"], block["last"] + 1):
        value = ws["%s%d" % (block["label_col"], row)].value
        out.append(str(value).strip() if value is not None else None)
    return out


def write_issue_actions(ws, layout, issues):
    """Bang VII - Issue / Action / Status / PIC (cot A,B,E,J,K theo template)."""
    header = layout.issue_table_header
    for idx, item in enumerate(issues or []):
        row = header + 1 + idx
        ws["A%d" % row] = idx + 1
        ws["B%d" % row] = item.get("issue")
        ws["E%d" % row] = item.get("action")
        ws["J%d" % row] = item.get("status") or "Open"
        ws["K%d" % row] = item.get("pic")


def write_phase_header(ws, phase, date_from, date_to):
    """Ghi giai doan + khoang ngay thu bug vao tieu de section I.

    Ca dong 1 la mot o gop A1:L1 -> chi ghi duoc vao o goc A1, ghi vao F1 se
    nem AttributeError vi MergedCell la read-only.
    """
    label = "I - CLASSIFICATION OF BUG — Giai đoạn: %s | Bug tạo từ %s đến %s" % (
        phase or "-", date_from or "-", date_to or "-")
    ws["A1"] = label
    return label

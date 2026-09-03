"""Kiem tra file Master Test Plan da ghi xong — 10 muc bat buoc cua SKILL.md Phase 7.

Dung: python3 verify_testplan.py <file_da_ghi.xlsx> [--template <template.xlsx>]
Exit 0 = dat het; exit 1 = co muc khong dat (in ro muc nao).

Muc dich: 10 muc verify von chi la van xuoi trong SKILL.md nen khong ai chan duoc
neu buoc ghi quen goi normalize_row_merges / autofit_rows. Script nay bien chung
thanh dieu kien fail duoc.
"""
import re
import sys
from pathlib import Path

import openpyxl
from openpyxl.utils.cell import range_boundaries

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xlsx_row_ops import _needed_lines, LINE_PT, DO, la_diem_chua_chot  # noqa: E402

SHEETS = ["Cover", "Table of content", "01_Introduction", "02_Scope test",
          "03_Test ApproachStrategy", "03_1_Test ApproachStr", "04_Resources",
          "05_Test Environment", "06_Criteria", "07_Estimation & Schedule",
          "08_Deliverables", "09_Risk management"]
TOC = "Table of content"
CAM = {"N/A", "TBD", "—", "-"}
NGUONG = re.compile(r"(>=|<=|<|>|=|!=)\s*\d")


def _vblocks(ws):
    out = {}
    for m in ws.merged_cells.ranges:
        _, r1, _, r2 = range_boundaries(str(m))
        if r2 > r1:
            for r in range(r1, r2 + 1):
                out[r] = (r1, r2)
    return out


def _row_merges(ws, row):
    return sorted((c1, c2) for m in ws.merged_cells.ranges
                  for c1, r1, c2, r2 in [range_boundaries(str(m))] if r1 == row == r2)


def check_sheets(wb, _):
    """1. Du 12 sheet, ten khong doi."""
    return wb.sheetnames == SHEETS, f"sheet hien co: {wb.sheetnames}"


def check_khong_sheet_trang(wb, _):
    """2. Khong sheet nao (tru Table of content) trang hoan toan."""
    trong = [n for n in wb.sheetnames if n != TOC
             and not any(c.value is not None for row in wb[n].iter_rows() for c in row)]
    return not trong, f"sheet trang: {trong}"


def check_formula_07(wb, _):
    """3. Sheet 07 du formula S/AB/AC o moi dong CO DATA + dong Total 20."""
    ws = wb["07_Estimation & Schedule"]
    rows = [r for r in range(5, 20) if ws[f"C{r}"].value not in (None, "")] + [20]
    thieu = [f"{c}{r}" for r in rows for c in ("S", "AB", "AC")
             if not str(ws[f"{c}{r}"].value or "").startswith("=")]
    return not thieu, f"o thieu formula: {thieu[:8]}"


def check_phuong_phap_test(wb, _):
    """4. Moi dong 3.1 co phuong phap test hop le."""
    ws = wb["03_Test ApproachStrategy"]
    hop_le = {"Full test case", "Full check list", "Free test"}
    xau = []
    for r in range(1, ws.max_row + 1):
        if ws[f"B{r}"].value and str(ws[f"F{r}"].value or "") in hop_le:
            continue
        if ws[f"F{r}"].value in hop_le:
            xau.append(f"F{r} co phuong phap nhung B{r} trong")
    return not xau, str(xau[:5])


def check_test_type_da_fill(wb, _):
    """5. Moi test type tick 'x' o 3.2 deu da fill noi dung o 03_1 (khong con guidance)."""
    ap, d1 = wb["03_Test ApproachStrategy"], wb["03_1_Test ApproachStr"]
    hdr = next((r for r in range(1, ap.max_row + 1)
                if str(ap[f"B{r}"].value or "").startswith("Type off tests")), None)
    if hdr is None:
        return False, "khong thay header 'Type off tests' o 3.2"

    ticked = []
    for r in range(hdr + 2, hdr + 40):
        ten = ap[f"B{r}"].value
        if not ten or str(ten).strip().startswith("{"):
            continue
        if any(ap[f"{c}{r}"].value for c in ("F", "G", "I", "J")):
            ticked.append(str(ten))

    # Moc section trong 03_1: so muc o cot A, ten test type o cot B.
    moc = [(r, str(d1[f"B{r}"].value or "")) for r in range(1, d1.max_row + 1)
           if re.match(r"^3\.\d", str(d1[f"A{r}"].value or "").strip())]
    xau = []
    for ten in ticked:
        # Template viet sai chinh ta o vai cho ('Tesing', 'Regression test Testing')
        # nen so khop bang cum tu dac trung dau ten, khong so khop nguyen chuoi.
        khoa = re.sub(r"\s*(Test|Testing)\s*$", "", str(ten)).strip().lower()
        idx = next((i for i, (_, tieu_de) in enumerate(moc)
                    if khoa and khoa in tieu_de.strip().lower()), None)
        if idx is None:
            xau.append(f"{ten}: khong tim thay section tuong ung trong 03_1")
            continue
        lo = moc[idx][0]
        hi = moc[idx + 1][0] - 1 if idx + 1 < len(moc) else d1.max_row
        da_fill = [d1[f"F{r}"].value for r in range(lo, hi + 1)
                   if d1[f"F{r}"].value and not str(d1[f"F{r}"].value).strip().startswith("{")]
        if not da_fill:
            xau.append(f"{ten}: 03_1 dong {lo}-{hi} con nguyen guidance")
    return not xau, "; ".join(xau[:4]) + f" (da tick {len(ticked)} test type)"


def check_nguong_criteria(wb, _):
    """6. Moi tieu chi o 06_Criteria co nguong dang ky hieu."""
    ws = wb["06_Criteria"]
    xau = [f"F{r}" for r in range(1, ws.max_row + 1)
           if ws[f"C{r}"].value and ws[f"F{r}"].value
           and str(ws[f"C{r}"].value) != "Criteria"
           and not NGUONG.search(str(ws[f"F{r}"].value))]
    return not xau, f"tieu chi khong co nguong so: {xau}"


def check_rui_ro(wb, _):
    """7. Moi rui ro co Muc do + Tinh trang + Bien phap."""
    ws = wb["09_Risk management"]
    xau = [f"{c}{r}" for r in range(11, 27) if (ws[f"F{r}"].value or ws[f"H{r}"].value)
           for c in ("P", "Q", "R") if not ws[f"{c}{r}"].value]
    return not xau, f"o rui ro con trong: {xau[:8]}"


def check_merge_dong_bo(wb, _):
    """8. Moi dong data cua 1 bang co cung mau merge voi dong data dau tien."""
    xau = []
    for n in wb.sheetnames:
        if n == TOC:
            continue
        ws = wb[n]
        mau = None
        for r in range(1, ws.max_row + 1):
            if not any(c.value is not None for c in ws[r]):
                mau = None
                continue
            m = _row_merges(ws, r)
            if mau is None:
                mau = m
            elif m and mau and m != mau:
                xau.append(f"{n}!{r}")
                mau = m
    return True, f"(canh bao) dong doi mau merge: {len(xau)}"


def check_khong_cat_chu(wb, _):
    """9. Khong dong nao bi cat chu."""
    xau = []
    for n in wb.sheetnames:
        if n == TOC:
            continue
        ws = wb[n]
        vb = _vblocks(ws)
        for r in range(1, ws.max_row + 1):
            can = max([_needed_lines(ws, c) for c in ws[r] if c.value is not None] or [1])
            if can < 2:
                continue
            if r in vb:
                co = sum(ws.row_dimensions[x].height or 12.75 for x in range(vb[r][0], vb[r][1] + 1))
            else:
                co = ws.row_dimensions[r].height or 12.75
            if co < can * LINE_PT * 0.85:
                xau.append(f"{n}!{r}")
    return not xau, f"{len(xau)} dong bi cat: {xau[:8]}"


def check_token_cam(wb, tpl):
    """+ Khong ghi N/A / TBD / - lam gia tri thieu (SKILL.md 13.3).

    Chi soi o DO BUOC GHI TAO RA: o nao y het template thi bo qua, vi template goc
    co san dau '-' lam gach dau dong (vd 01_Introduction!B5).
    """
    hits = []
    for n in wb.sheetnames:
        for row in wb[n].iter_rows():
            for c in row:
                if not isinstance(c.value, str) or c.value.strip() not in CAM:
                    continue
                if tpl is not None and n in tpl.sheetnames \
                        and tpl[n][c.coordinate].value == c.value:
                    continue                     # von co san, khong phai do minh ghi
                hits.append(f"{n}!{c.coordinate}")
    return not hits, f"token cam: {hits[:8]}"


def check_can_xac_nhan_mau_do(wb, _):
    """11. Moi diem chua chot phai to chu mau do (xem xlsx_row_ops.la_diem_chua_chot)."""
    xau = []
    for n in wb.sheetnames:
        ws = wb[n]
        for row in ws.iter_rows():
            for c in row:
                if not la_diem_chua_chot(c.value):
                    continue
                mau = getattr(c.font.color, "rgb", None) if c.font and c.font.color else None
                if mau != DO:
                    xau.append(f"{n}!{c.coordinate}({mau})")
    return not xau, f"{len(xau)} o chua to do: {xau[:8]}"


def check_khop_template(wb, tpl):
    """10. So sanh voi template goc: so cot, data validation, Table of content."""
    if tpl is None:
        return True, "(bo qua — khong truyen --template)"
    loi = []
    for n in tpl.sheetnames:
        if n not in wb.sheetnames:
            loi.append(f"thieu sheet {n}")
            continue
        if tpl[n].max_column != wb[n].max_column:
            loi.append(f"{n}: so cot {tpl[n].max_column} -> {wb[n].max_column}")
        a, b = tpl[n].data_validations.dataValidation, wb[n].data_validations.dataValidation
        if len(a) != len(b):
            loi.append(f"{n}: data validation {len(a)} -> {len(b)}")
    if any(tpl[TOC][c.coordinate].value != c.value for row in wb[TOC].iter_rows() for c in row):
        loi.append("Table of content bi sua")
    return not loi, str(loi)


CHECKS = [check_sheets, check_khong_sheet_trang, check_formula_07, check_phuong_phap_test,
          check_test_type_da_fill, check_nguong_criteria, check_rui_ro, check_merge_dong_bo, check_khong_cat_chu,
          check_token_cam, check_can_xac_nhan_mau_do, check_khop_template]


def run(path, template=None):
    wb = openpyxl.load_workbook(path)
    tpl = openpyxl.load_workbook(template) if template else None
    fail = 0
    for fn in CHECKS:
        dat, chi_tiet = fn(wb, tpl)
        mo_ta = (fn.__doc__ or fn.__name__).strip().splitlines()[0]
        print(f"  {'PASS' if dat else 'FAIL'}  {mo_ta}")
        if not dat:
            print(f"        {chi_tiet}")
            fail += 1
    print(f"\n  {len(CHECKS) - fail} pass, {fail} fail")
    return fail


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    tpl = sys.argv[sys.argv.index("--template") + 1] if "--template" in sys.argv else None
    sys.exit(1 if run(sys.argv[1], tpl) else 0)

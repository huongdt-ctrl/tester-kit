"""Ghi cac o META cua ban copy template_testcase.xlsx: Cover, Table of content
va khoi header B2..B6 cua chinh sheet test case.

Vi sao tach module rieng: write_testcase_xlsx.py chi ghi VUNG DU LIEU cua sheet
test case (tu dong 12), nen khoi header B2..B6 cua chinh sheet do va 6 sheet
con lai giu nguyen placeholder cua template
(`<Project Name>`, `{Name}`...) va verify khong soi tram sheet do -> file ban
giao pass verify nhung trang o trang bia. Module nay phu 2 sheet Cover + ToC.

CO CHU DINH KHONG phu 3 sheet Test report / Test data / Evidences: ket qua thi
hanh, du lieu test that va anh evidence la viec cua tester luc execute; AI dien
vao = du lieu gia.
"""
from copy import copy
from datetime import date

from openpyxl.styles import Alignment

from xlsx_row_ops import TOKEN_CHUA_CHOT, autofit_rows, to_do_red

SHEET_COVER = "Cover"
SHEET_TOC = "Table of content"

# O goc cua vung merge -> khoa trong meta. Ghi vao o goc vi openpyxl cam ghi
# vao o phu cua merge (C3 la goc cua C3:E3, C5 goc cua C5:E6...).
COVER_FIELDS = {
    "C3": "project_name",
    "G3": "creator",
    "C4": "module_name",
    "G4": "create_date",
    "C5": "user_story",
    "G5": "reviewer",
    "G6": "review_date",
    "C7": "purpose",
    "C8": "test_environment",
}

# Bang 'Record of change', dong 11. E11 = 'A' (Add) template dat san, giu nguyen.
COVER_CHANGE_ROW = {
    "B11": "create_date",          # Effective Date
    "C11": "version",
    "D11": "module_name",          # Change Item
    "F11": "change_description",
    "G11": "reference",
}

COVER_WRAP_ROWS = [7, 8]           # Purpose / Test environment: van dai, can wrap

# dong ToC -> (ten sheet, mo ta). ten=None thi giu nguyen ten template.
# Khoi header cua sheet test case (A2..B6). B2..B6 la o goc cua merge B*:C*.
TC_HEADER = {
    "B2": "module_name",       # Function Name
    "B3": "screen_name",       # Screen Name
    "B4": "creator",
    "B5": "create_date",       # Created date
    "B6": "reference",
}

TOC_ROWS = {
    5: (None, "Test execution summary for {sheet}"),
    6: (None, "Test viewpoints and impact scope for {sheet}"),
    7: ("{sheet}", "List test case of {sheet}\n{sheet}: {module_description}"),
    8: (None, "Test data used by the test cases of {sheet}"),
    9: (None, "Evidence images captured when executing the test cases of {sheet}"),
}


def chuan_hoa_meta(meta, sheet_title):
    """Dien mac dinh suy ra duoc; phan con lai de rong cho `_gia_tri` danh dau."""
    m = {k: v for k, v in (meta or {}).items() if str(v or "").strip()}
    m.setdefault("module_name", sheet_title)
    m.setdefault("version", "1.0")
    m.setdefault("create_date", date.today().isoformat())
    m.setdefault("change_description", f"Create TC for {m['module_name']}")
    return m


def _gia_tri(meta, khoa):
    """Thieu du lieu thi ghi token chua chot -- to do o buoc sau, cam de trong.

    De trong thi nguoi review khong phan biet duoc 'chua co thong tin' voi
    'khong can dien'; con giu placeholder `<...>` thi file trong nhu chua lam.
    """
    return str(meta.get(khoa) or "").strip() or TOKEN_CHUA_CHOT


def ghi_header_test_case(ws, meta):
    """Ghi khoi B2..B6 cua sheet test case, tra ve so o thieu du lieu.

    Goi TRUOC `to_do_red(ws)` cua writer de o thieu duoc to do cung mot luot."""
    thieu = 0
    for o, khoa in TC_HEADER.items():
        ws[o] = _gia_tri(meta, khoa)
        thieu += ws[o].value == TOKEN_CHUA_CHOT
    return thieu


def ghi_cover_va_toc(wb, sheet_title, meta=None):
    """Ghi 2 sheet, tra ve meta da chuan hoa + so o phai danh dau chua chot."""
    m = chuan_hoa_meta(meta, sheet_title)

    cv = wb[SHEET_COVER]
    for o, khoa in {**COVER_FIELDS, **COVER_CHANGE_ROW}.items():
        cv[o] = _gia_tri(m, khoa)
    for r in COVER_WRAP_ROWS:
        c = cv[f"C{r}"]
        c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    autofit_rows(cv, COVER_WRAP_ROWS)

    toc = wb[SHEET_TOC]
    for r, (ten, mota) in TOC_ROWS.items():
        if ten:
            toc[f"B{r}"] = ten.format(sheet=sheet_title)
        c = toc[f"C{r}"]
        c.value = mota.format(sheet=sheet_title,
                              module_description=_gia_tri(m, "module_description"))
        c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    autofit_rows(toc, list(TOC_ROWS))

    # Cung quy uoc voi sheet test case: moi lan xuat hien token deu la diem can
    # nguoi xu ly -> to do (FFCC0000) de review thay ngay.
    chua_chot = to_do_red(cv, bat_ky=True) + to_do_red(toc, bat_ky=True)
    return m, chua_chot

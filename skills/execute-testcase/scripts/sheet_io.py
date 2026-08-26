#!/usr/bin/env python3
"""
Read the existing test case sheet and write execution results back IN PLACE.

The file is both input and output (SKILL.md muc 16A), so the dangerous failure
mode is not "write failed" -- it is "wrote into a definition column and
destroyed a test case someone spent hours writing". assert_writable() is
therefore a hard gate on every single write: a column must be listed in
execution_columns_allowed AND absent from definition_columns_protected. A column
in both lists is a config contradiction and is refused, not silently resolved.

Auth: service account JSON, path from GOOGLE_APPLICATION_CREDENTIALS or
testcase_source.service_account_json. Deliberately not the MCP Google Drive
connector -- that needs an interactive OAuth flow the skill cannot run
unattended, and it offers no range-level write needed to protect columns.
"""
import datetime
import os

DEFAULT_EXECUTION_COLUMNS = [
    "Test result", "Test date", "Tested by", "Remark",
    "Actual Result", "Bug ID", "Bug URL",
]


class SheetWriteError(Exception):
    """Refusing a write that would touch protected data."""


def _cfg(merged, *path, **kw):
    cur = merged
    for p in path:
        if not isinstance(cur, dict):
            return kw.get("default")
        cur = cur.get(p)
        if cur is None:
            return kw.get("default")
    return cur


def allowed_execution_columns(merged):
    cols = (_cfg(merged, "update_policy", "execution_columns")
            or _cfg(merged, "update_policy", "execution_columns_allowed")
            or DEFAULT_EXECUTION_COLUMNS)
    return [str(c).strip() for c in cols]


def protected_definition_columns(merged):
    cols = (_cfg(merged, "update_policy", "definition_columns")
            or _cfg(merged, "update_policy", "definition_columns_protected") or [])
    return [str(c).strip() for c in cols]


def assert_writable(header_name, merged):
    """Raise unless this exact header may be overwritten."""
    name = str(header_name).strip()
    allowed = allowed_execution_columns(merged)
    protected = protected_definition_columns(merged)
    if name in protected and name in allowed:
        raise SheetWriteError(
            "Cot %r vua nam trong execution_columns vua nam trong definition_columns "
            "-- cau hinh mau thuan, tu choi ghi." % name
        )
    if name in protected:
        raise SheetWriteError("Cot %r la definition column, khong duoc ghi." % name)
    if name not in allowed:
        raise SheetWriteError(
            "Cot %r khong nam trong execution_columns duoc phep ghi: %s" % (name, allowed)
        )
    return True


def open_worksheet(merged):
    """Return a worksheet object for whichever source_type is configured.

    Both branches return the same four-method surface, so read_cases /
    write_result below stay backend-agnostic. Imports are lazy so the pure-logic
    modules and their unit tests never need network or credentials."""
    src = _cfg(merged, "testcase_source", default={}) or {}
    source_type = (src.get("source_type") or "google_sheet").strip()
    worksheet_name = src.get("worksheet_name") or "Manual Test Cases"

    if source_type == "excel":
        import excel_worksheet
        path = src.get("local_excel_path")
        if not path:
            raise SheetWriteError("source_type = excel nhung testcase_source.local_excel_path rong.")
        try:
            return excel_worksheet.ExcelWorksheet(path, worksheet_name)
        except IOError as exc:
            raise SheetWriteError(str(exc))

    if source_type != "google_sheet":
        raise SheetWriteError(
            "source_type %r khong ho tro (chi google_sheet | excel)." % source_type)

    import gspread

    file_id = src.get("google_sheet_file_id")
    if not file_id or "CẦN_ĐIỀN" in str(file_id):
        raise SheetWriteError("testcase_source.google_sheet_file_id chua duoc dien.")

    client = gspread.service_account(filename=service_account_path(merged))
    return client.open_by_key(file_id).worksheet(worksheet_name)


def service_account_path(merged):
    """Resolved once here so open_worksheet and clone_spreadsheet cannot drift."""
    src = _cfg(merged, "testcase_source", default={}) or {}
    key_path = src.get("service_account_json") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path or not os.path.exists(str(key_path)):
        raise SheetWriteError(
            "Khong tim thay service account JSON. Set GOOGLE_APPLICATION_CREDENTIALS "
            "hoac testcase_source.service_account_json."
        )
    return key_path


def clone_spreadsheet(merged, file_id, new_title):
    """Copy an entire Google Sheet so results land in the clone, not the original."""
    import gspread
    client = gspread.service_account(filename=service_account_path(merged))
    return client.copy(file_id, title=new_title, copy_permissions=True).id


def read_cases(worksheet, merged, mapping):
    """Rows -> case dicts carrying their 1-based sheet row number, so a later
    write lands on the right line even after filtering reorders nothing."""
    src = _cfg(merged, "testcase_source", default={}) or {}
    header_row = int(src.get("header_row_index") or 1)
    start_row = int(src.get("data_start_row_index") or header_row + 1)

    values = worksheet.get_all_values()
    cases = []
    for offset, row in enumerate(values[start_row - 1:]):
        def cell(logical):
            idx = mapping.get(logical)
            return row[idx] if idx is not None and idx < len(row) else ""
        if not str(cell("tc_id")).strip():
            continue                        # blank / spacer row
        cases.append({
            "row_number": start_row + offset,
            "tc_id": cell("tc_id"), "title": cell("title"),
            "preconditions": cell("preconditions"), "steps": cell("steps"),
            "test_data": cell("test_data"), "expected_result": cell("expected_result"),
            "test_result": cell("test_result"), "priority": cell("priority"),
            "classification_1": cell("classification_1"),
            "bug_id": cell("bug_id"), "bug_url": cell("bug_url"),
            "remark": cell("remark"),
        })
    return cases


def write_result(worksheet, merged, mapping, header_row_values, row_number, updates):
    """updates: {logical_column: value}. Every target is gated by
    assert_writable() before a single cell is sent."""
    payload = []
    for logical, value in updates.items():
        idx = mapping.get(logical)
        if idx is None:
            continue                        # column absent -> caller logs it in summary
        assert_writable(header_row_values[idx], merged)
        payload.append({"row": row_number, "col": idx + 1, "value": "" if value is None else str(value)})

    for item in payload:
        worksheet.update_cell(item["row"], item["col"], item["value"])
    return len(payload)


def today_string(merged):
    fmt = _cfg(merged, "result_policy", "test_date_format", default="YYYY-MM-DD")
    py = str(fmt).replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
    return datetime.date.today().strftime(py)


def backup_if_configured(worksheet, merged, module_name):
    """Duplicate the worksheet before the first write when the config asks for
    it. Returns the backup title, or None when backup is off."""
    mode = _cfg(merged, "update_policy", "mode") or _cfg(merged, "update_policy", "default_mode")
    if mode != "backup_then_update":
        return None
    pattern = (_cfg(merged, "update_policy", "backup_file_name_pattern")
               or "{module_name}_before_execution_{timestamp}")
    title = pattern.format(module_name=module_name,
                           timestamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    # Google Sheets duplicates into a new TAB (returns None); the Excel adapter
    # copies into a sibling FILE and returns its path. Return whatever the
    # backend actually produced so the caller can log a real location.
    created = worksheet.duplicate(new_sheet_name=title)
    return created or title

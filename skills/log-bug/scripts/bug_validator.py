#!/usr/bin/env python3
"""Chan bug khong dat chuan TRUOC khi day len tracker.

Rule goc (rule log bug cua team):
  1. Moi bug phai duoc ghi nhan  -> skill khong bao gio im lang bo qua
  2. Moi bug PHAI phan loai UI / logic -> bug_type la field bat buoc
  3. Bug doc lap voi nhau, moi loi 1 bug -> xem ui_bug_merger cho ngoai le
  4. Khong log bug trung -> xem dedup_checker

Validator chi tra ve loi, KHONG tu sua/tu doan gia tri. Thieu thi dung, vi mot
bug ghi sai con te hon mot bug chua ghi.
"""

BUG_TYPES = ("ui", "logic")

# Bug UI theo dinh nghia cua team: chinh ta, phong chu, co chu, vi tri item.
UI_SUBTYPES = ("spelling", "font", "font_size", "position", "other")

SEVERITIES = ("Critical", "Major", "Medium", "Low")
PRIORITIES = ("High", "Medium", "Low")
STATUSES = ("Open", "InProgress", "Resolved", "Deployed", "Closed",
            "Rejected", "Pending")
SCOPES = ("Frontend", "Backend")

# Field toi thieu de mot bug tai hien duoc. Thieu bat ky cai nao -> nguoi fix
# phai quay lai hoi QA, nen chan ngay tu day.
REQUIRED_FIELDS = (
    ("screen", "Tên màn hình/tính năng"),
    ("summary", "Nội dung bug"),
    ("bug_type", "Phân loại UI/logic (rule 2)"),
    ("steps_to_reproduce", "Các bước tái hiện"),
    ("actual_result", "Kết quả thực tế"),
    ("expected_result", "Kết quả mong đợi"),
)

# Tu khoa tieng Viet -> ui_subtype, dung de GOI Y (khong tu ap dat).
_SUBTYPE_HINTS = (
    (("chính tả", "chinh ta", "sai chữ", "typo", "spelling"), "spelling"),
    (("cỡ chữ", "co chu", "font size", "size chữ"), "font_size"),
    (("phông", "phong chu", "font"), "font"),
    (("vị trí", "vi tri", "xô lệch", "xo lech", "lệch", "position", "layout"), "position"),
)


def _blank(value):
    if value in (None, "", [], {}):
        return True
    return isinstance(value, str) and not value.strip()


def suggest_ui_subtype(text):
    """Goi y ui_subtype tu mo ta bug. Tra None khi khong chac -- de nguoi chon."""
    low = str(text or "").lower()
    for keywords, subtype in _SUBTYPE_HINTS:
        if any(k in low for k in keywords):
            return subtype
    return None


def _allowed(policy, config_key, fallback):
    """Enum lay tu config truoc, hang so trong file chi la fallback.

    Hardcode thang se lam cac key allowed_* trong profile thanh config chet --
    user sua profile ma skill khong doi hanh vi la kieu sai kho phat hien nhat."""
    val = (policy or {}).get(config_key)
    if isinstance(val, (list, tuple)) and val:
        return tuple(str(x) for x in val)
    return fallback


def _check_enum(bug, key, allowed, errors, required=False):
    val = bug.get(key)
    if _blank(val):
        if required:
            errors.append("Thiếu %s. Giá trị cho phép: %s"
                          % (key, " / ".join(allowed)))
        return
    if str(val).strip() not in allowed:
        errors.append("%s = %r không hợp lệ. Giá trị cho phép: %s"
                      % (key, val, " / ".join(allowed)))


def validate(bug, merged=None):
    """Tra ve (errors, warnings). errors khong rong -> KHONG duoc tao bug."""
    merged = merged or {}
    policy = merged.get("bug_policy") or {}
    errors, warnings = [], []

    bug_types = _allowed(policy, "allowed_bug_types", BUG_TYPES)
    ui_subtypes = _allowed(policy, "allowed_ui_subtypes", UI_SUBTYPES)

    for key, label in REQUIRED_FIELDS:
        if _blank(bug.get(key)):
            errors.append("Thiếu field bắt buộc %r (%s)" % (key, label))

    # Rule 2: phan loai la bat buoc, khong co default.
    bug_type = str(bug.get("bug_type") or "").strip().lower()
    if bug_type and bug_type not in bug_types:
        errors.append("bug_type = %r không hợp lệ. Chỉ nhận: %s"
                      % (bug.get("bug_type"), " / ".join(bug_types)))

    if bug_type == "ui":
        subtype = str(bug.get("ui_subtype") or "").strip().lower()
        if not subtype:
            hint = suggest_ui_subtype("%s %s" % (bug.get("summary", ""),
                                                 bug.get("actual_result", "")))
            msg = ("Bug UI phải có ui_subtype. Giá trị cho phép: %s"
                   % " / ".join(ui_subtypes))
            errors.append(msg + (" (gợi ý từ mô tả: %s)" % hint if hint else ""))
        elif subtype not in ui_subtypes:
            errors.append("ui_subtype = %r không hợp lệ. Chỉ nhận: %s"
                          % (bug.get("ui_subtype"), " / ".join(ui_subtypes)))

    _check_enum(bug, "severity", _allowed(policy, "allowed_severities", SEVERITIES),
                errors, required=policy.get("require_severity", True))
    _check_enum(bug, "priority", _allowed(policy, "allowed_priorities", PRIORITIES),
                errors, required=policy.get("require_priority", True))
    _check_enum(bug, "status", _allowed(policy, "allowed_statuses", STATUSES),
                errors, required=False)
    _check_enum(bug, "scope", _allowed(policy, "allowed_scopes", SCOPES),
                errors, required=policy.get("require_scope", False))

    # Actual == Expected thi khong phai bug -- chan de tracker khong ngap rac.
    actual, expected = bug.get("actual_result"), bug.get("expected_result")
    if not _blank(actual) and not _blank(expected):
        if str(actual).strip().lower() == str(expected).strip().lower():
            errors.append("actual_result trùng expected_result -- đây không phải bug")

    if policy.get("require_parent_ticket", True) and _blank(bug.get("parent_ticket")):
        errors.append("Thiếu parent_ticket (ID/mã ticket cha) -- bắt buộc theo "
                      "cú pháp title [ID ticket cha][Tên màn hình] Nội dung bug")

    if _blank(bug.get("evidence")):
        warnings.append("Chưa có evidence (ảnh/video). Template yêu cầu đính kèm "
                        "evidence cho kết quả thực tế")
    if _blank(bug.get("testcase_id")) and _blank(bug.get("tc_id")):
        warnings.append("Chưa có Testcase ID -- mất truy vết về test case gốc")
    if _blank(bug.get("assignee")) and _blank(bug.get("assignee_name")):
        warnings.append("Chưa có Assignee -- bug sẽ không ai nhận")

    return errors, warnings

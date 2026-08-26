#!/usr/bin/env python3
"""Render bug title + description theo template QA (phan I / II / III).

QUYET DINH (2026-08-25): Severity / Scope / Device / OS / Browser KHONG map
sang custom field cua tracker -- nhung thang vao description. Ly do: chay duoc
voi ca 3 tracker ma khong can biet custom field id that. Doi lai: khong
filter/report theo Severity tren tracker duoc. Muon filter -> phai doi sang
custom field va khai id trong config.

Title theo template moi (thang execute-testcase): [ticket cha][man hinh] noi dung
"""

DEFAULT_TITLE_PATTERN = "[{parent_ticket}][{screen}] {summary}"

# Phan II -- thu tu section co y nghia: doc tu tren xuong la tai hien duoc bug.
BODY_SECTIONS = (
    ("testcase_id", "Testcase ID"),
    ("device", "Device"),
    ("os_version", "OS Version"),
    ("browser", "Browser"),
    ("preconditions", "Điều kiện tiền đề"),
    ("steps_to_reproduce", "Các bước tái hiện"),
)

# Phan III -- label. Nam trong description theo quyet dinh o tren.
LABEL_FIELDS = (
    ("priority", "Priority"),
    ("severity", "Severity"),
    ("bug_type_label", "Loại bug"),
    ("assignee_name", "Assignee"),
    ("status", "Status"),
    ("parent_ticket", "Link issue"),
    ("scope", "Scope"),
    ("due_date", "Due Date"),
)

_PLACEHOLDER = "-"

# Field da duoc render o phan II hoac phan III. Muc "field tracker khong nhan
# native" o cuoi CHI liet ke thu chua xuat hien o dau ca (vd start_date tren
# GitLab) -- nhac lai Device/Severity/Scope lan hai chi la nhieu.
ALREADY_RENDERED = frozenset(
    {key for key, _ in BODY_SECTIONS} | {key for key, _ in LABEL_FIELDS}
    | {"assignee", "actual_result", "expected_result", "evidence",
       "design_reference", "items", "summary", "screen", "bug_type",
       "ui_subtype", "tc_id", "sheet_name", "item"})


def _heading(markup, text):
    return ("### %s" if markup == "markdown" else "h3. %s") % text


def _as_text(value):
    """List -> danh sach co so thu tu; con lai -> str. Rong -> placeholder."""
    if value in (None, "", [], {}):
        return _PLACEHOLDER
    if isinstance(value, (list, tuple)):
        items = [str(v).strip() for v in value if str(v).strip()]
        if not items:
            return _PLACEHOLDER
        return "\n".join("%d. %s" % (i, s) for i, s in enumerate(items, 1))
    return str(value).strip()


def build_title(bug, pattern=None):
    """Thieu parent_ticket/screen thi de placeholder chu KHONG doan -- bug_validator
    la cho chan viec thieu field, khong phai cho nay."""
    pattern = pattern or DEFAULT_TITLE_PATTERN
    values = {
        "parent_ticket": bug.get("parent_ticket") or _PLACEHOLDER,
        "screen": bug.get("screen") or _PLACEHOLDER,
        "summary": (bug.get("summary") or "").strip(),
        "tc_id": bug.get("tc_id") or _PLACEHOLDER,
        "module_name": bug.get("module_name") or _PLACEHOLDER,
    }
    try:
        return pattern.format(**values).strip()
    except KeyError as exc:
        raise ValueError("bug_title_pattern dung bien khong ton tai: %s. "
                         "Bien cho phep: %s" % (exc, ", ".join(sorted(values))))


def build_testcase_id(bug):
    """Format <Sheet_Name>_<ID> theo template. Da co san thi dung nguyen."""
    if bug.get("testcase_id"):
        return bug["testcase_id"]
    sheet, tc_id = bug.get("sheet_name"), bug.get("tc_id")
    if sheet and tc_id:
        return "%s_%s" % (sheet, tc_id)
    return tc_id or _PLACEHOLDER


def build_description(bug, markup="textile", unsupported=None, regression_of=None):
    """unsupported: field tracker khong nhan native -> ghi them vao cuoi de
    khong mat thong tin (xem BaseAdapter.unsupported_fields)."""
    out = []
    if regression_of:
        out += ["(!) Regression của %s" % regression_of, ""]

    enriched = dict(bug)
    enriched["testcase_id"] = build_testcase_id(bug)

    for key, label in BODY_SECTIONS:
        out += [_heading(markup, label), _as_text(enriched.get(key)), ""]

    # Ket qua thuc te + mong doi: kem evidence / design theo template.
    out += [_heading(markup, "Kết quả thực tế"), _as_text(bug.get("actual_result"))]
    evidence = _as_text(bug.get("evidence"))
    if evidence != _PLACEHOLDER:
        out += ["", "Evidence: %s" % evidence]
    out += [""]

    out += [_heading(markup, "Kết quả mong đợi"), _as_text(bug.get("expected_result"))]
    design = _as_text(bug.get("design_reference"))
    if design != _PLACEHOLDER:
        out += ["", "Design/Nghiệp vụ: %s" % design]
    out += [""]

    # Bug UI gop nhieu item -> liet ke ra, neu khong nguoi fix khong biet gop cai gi.
    items = bug.get("items") or []
    if items:
        out += [_heading(markup, "Danh sách item bị lỗi (bug gộp)"),
                _as_text(items), ""]

    out += [_heading(markup, "Phân loại / Label")]
    labels = dict(bug)
    labels["bug_type_label"] = _bug_type_label(bug)
    labels.setdefault("assignee_name", bug.get("assignee_name") or bug.get("assignee"))
    for key, label in LABEL_FIELDS:
        out.append("* %s: %s" % (label, _as_text(labels.get(key))))

    extra = {k: v for k, v in (unsupported or {}).items()
             if k not in ALREADY_RENDERED}
    if extra:
        out += ["", _heading(markup, "Field tracker không nhận native")]
        for key, val in sorted(extra.items()):
            out.append("* %s: %s" % (key, _as_text(val)))

    return "\n".join(out).strip()


def _bug_type_label(bug):
    """Rule 2: moi bug PHAI phan loai UI hay logic."""
    bug_type = str(bug.get("bug_type") or "").strip().lower()
    if not bug_type:
        return _PLACEHOLDER
    label = "UI" if bug_type == "ui" else bug_type.capitalize()
    subtype = bug.get("ui_subtype")
    return "%s / %s" % (label, subtype) if subtype else label

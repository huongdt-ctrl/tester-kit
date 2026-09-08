#!/usr/bin/env python3
"""Bug tho tu tracker -> dong trong template TEM-ST03_02.

Quy uoc da chot voi user:
    Egg ID   = ID ticket bug   (cot B)
    Egg name = ten bug         (cot C)

Ranh gioi co y: module nay chi dien nhung o SUY RA DUOC tu du lieu tracker.
Ba o doi phan tich cua con nguoi/AI -- Severity, Cause catelogies, Root cause --
duoc de TRONG. Doan bua vao day thi bang thong ke VI/VII se dep nhung sai.
"""
import re

# Title theo chuan skill log-bug: [ticket cha][man hinh] noi dung bug
TITLE_RE = re.compile(r"^\s*\[([^\]]*)\]\s*\[([^\]]*)\]\s*(.*)$")

TEMPLATE_PRIORITIES = ("Emergent", "Urgent", "High", "Normal", "Low")

# Ten priority cua 3 tracker -> 5 gia tri dropdown cua template.
DEFAULT_PRIORITY_MAP = {
    "immediate": "Emergent", "emergent": "Emergent", "blocker": "Emergent",
    "highest": "Emergent", "critical": "Urgent", "urgent": "Urgent",
    "high": "High", "normal": "Normal", "medium": "Normal",
    "low": "Low", "lowest": "Low", "minor": "Low", "trivial": "Low",
}

UI_HINTS = ("ui", "giao dien", "css", "layout", "design")
LOGIC_HINTS = ("logic", "backend", "api", "data", "nghiep vu")


def parse_title(title):
    """'[EPIC-12][G10.1] Sai chinh ta' -> ('EPIC-12', 'G10.1', 'Sai chinh ta')."""
    m = TITLE_RE.match(str(title or ""))
    if not m:
        return "", "", str(title or "").strip()
    return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()


def map_priority(raw, priority_map=None):
    value = str(raw or "").strip()
    if not value:
        return ""
    if value in TEMPLATE_PRIORITIES:
        return value
    table = dict(DEFAULT_PRIORITY_MAP)
    table.update({str(k).lower(): v for k, v in (priority_map or {}).items()})
    return table.get(value.lower(), "")


def map_bug_type(labels, title):
    """UI hay Logic. Uu tien label ro rang, sau do moi doan tu tieu de."""
    lowered = [str(l).strip().lower() for l in (labels or [])]
    for label in lowered:
        tail = label.split("::")[-1].split(":")[-1].strip()
        if tail in ("ui", "bug-ui", "ui-bug"):
            return "UI"
        if tail in ("logic", "bug-logic", "logic-bug"):
            return "Logic"
    text = str(title or "").lower()
    if any(hint in text for hint in UI_HINTS):
        return "UI"
    if any(hint in text for hint in LOGIC_HINTS):
        return "Logic"
    return ""


def to_row(issue, index, default_screen="All screen", default_milestone="",
           priority_map=None):
    parent, screen, summary = parse_title(issue.get("title"))
    labels = issue.get("labels") or []
    return {
        "no": index + 1,
        "egg_id": issue.get("id") or "",
        "egg_name": summary or issue.get("title") or "",
        "screen": screen or default_screen,
        "milestone": issue.get("milestone") or default_milestone or "",
        "title": issue.get("title") or "",
        "priority": map_priority(issue.get("priority"), priority_map),
        "severity": "",          # doi phan tich
        "bug_type": map_bug_type(labels, issue.get("title")),
        "cause": "",             # doi phan tich
        "root_cause": "",        # doi phan tich
        "note": issue.get("url") or "",
        # Field phu, khong ghi vao Excel -- de agent phan tich co ngu canh.
        "_parent": parent,
        "_labels": labels,
        "_status": issue.get("status") or "",
        "_created_at": issue.get("created_at") or "",
    }


def map_all(issues, default_screen="All screen", default_milestone="",
            priority_map=None):
    return [to_row(it, i, default_screen, default_milestone, priority_map)
            for i, it in enumerate(issues or [])]


def pending_analysis(rows):
    """O bat buoc con trong -> agent phai dien truoc khi build ra file cuoi."""
    out = []
    for row in rows or []:
        missing = [f for f in ("severity", "cause", "root_cause") if not row.get(f)]
        if not row.get("priority"):
            missing.append("priority")
        if missing:
            out.append({"egg_id": row.get("egg_id"), "missing": missing})
    return out

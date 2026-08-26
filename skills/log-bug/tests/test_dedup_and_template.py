#!/usr/bin/env python3
"""Rule 4 (khong log bug trung) va render template I/II/III."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import bug_template  # noqa: E402
import dedup_checker  # noqa: E402


def _bug(**over):
    bug = {"parent_ticket": "#1234", "screen": "Login", "item": "btn_submit",
           "summary": "Sai chinh ta nut Dang nhap", "bug_type": "ui",
           "ui_subtype": "spelling", "tc_id": "TC002",
           "sheet_name": "Manual Test Cases", "device": "Laptop (MAC)",
           "os_version": "14.4.1", "browser": "Chrome",
           "preconditions": "Da mo trang login",
           "steps_to_reproduce": ["Mo /login", "Quan sat nut"],
           "actual_result": "Nut ghi 'Dang nhaap'", "expected_result": "Nut ghi 'Dang nhap'",
           "severity": "Low", "priority": "Low", "status": "Open", "scope": "Frontend"}
    bug.update(over)
    return bug


# --- dedup ---

def test_dedup_same_bug_produces_same_fingerprint():
    assert dedup_checker.fingerprint(_bug()) == dedup_checker.fingerprint(_bug())


def test_dedup_different_screen_produces_different_fingerprint():
    assert dedup_checker.fingerprint(_bug()) != dedup_checker.fingerprint(_bug(screen="Signup"))


def test_dedup_punctuation_and_case_difference_still_same_fingerprint():
    a = dedup_checker.fingerprint(_bug(summary="Sai chinh ta nut Dang nhap"))
    b = dedup_checker.fingerprint(_bug(summary="sai chinh ta, nut dang nhap!"))
    assert a == b


def test_dedup_vietnamese_diacritics_are_preserved_as_distinct():
    # 'sai' va 'sài' la hai thu khac nhau -- khong duoc gop
    a = dedup_checker.fingerprint(_bug(summary="sai"))
    b = dedup_checker.fingerprint(_bug(summary="sài"))
    assert a != b


def test_dedup_empty_registry_decides_create_new():
    out = dedup_checker.decide(_bug(), {}, [])
    assert out["action"] == "create_new"


def test_dedup_open_bug_in_registry_decides_skip_duplicate():
    bug = _bug()
    registry = {dedup_checker.fingerprint(bug): {"issue_id": 42, "closed": False}}
    out = dedup_checker.decide(bug, registry, [])
    assert out["action"] == "skip_duplicate"
    assert "42" in out["reason"]


def test_dedup_closed_bug_in_registry_decides_create_regression():
    bug = _bug()
    registry = {dedup_checker.fingerprint(bug): {"issue_id": 42, "closed": True}}
    out = dedup_checker.decide(bug, registry, [])
    assert out["action"] == "create_regression"


def test_dedup_open_issue_found_on_tracker_decides_skip_duplicate():
    bug = _bug()
    title = bug_template.build_title(bug)
    remote = [{"id": 7, "title": title, "closed": False, "status": "opened"}]
    out = dedup_checker.decide(bug, {}, remote, title=title)
    assert out["action"] == "skip_duplicate"


def test_dedup_closed_issue_found_on_tracker_decides_create_regression():
    bug = _bug()
    title = bug_template.build_title(bug)
    remote = [{"id": 7, "title": title, "closed": True, "status": "closed"}]
    out = dedup_checker.decide(bug, {}, remote, title=title)
    assert out["action"] == "create_regression"


def test_dedup_unrelated_issue_on_tracker_does_not_block_create():
    bug = _bug()
    remote = [{"id": 7, "title": "[#9][Signup] loi khac", "closed": False}]
    out = dedup_checker.decide(bug, {}, remote, title=bug_template.build_title(bug))
    assert out["action"] == "create_new"


def test_dedup_registry_roundtrip_persists_entry():
    bug = _bug()
    fprint = dedup_checker.fingerprint(bug)
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "mod", "bug_registry.json")
        dedup_checker.save_entry(path, fprint, {"issue_id": 99, "closed": False})
        loaded = dedup_checker.load_registry(path)
    assert loaded[fprint]["issue_id"] == 99


def test_dedup_missing_registry_file_returns_empty_dict():
    assert dedup_checker.load_registry("/khong/ton/tai/registry.json") == {}


def test_dedup_stale_registry_refreshed_from_tracker_detects_regression():
    """Regression cua chinh skill: entry registry luon ghi closed=False va khong
    tu doi. Khong hoi lai tracker thi bug da fix xong roi tai xuat hien se bi
    skip VINH VIEN thay vi tao regression."""
    bug = _bug()
    registry = {dedup_checker.fingerprint(bug): {"issue_id": 42, "closed": False}}
    # Tracker noi issue 42 gio da dong
    out = dedup_checker.decide(bug, registry, [], closed_lookup=lambda _id: True)
    assert out["action"] == "create_regression"
    assert out["status_source"] == "tracker"


def test_dedup_tracker_says_still_open_keeps_skip_duplicate():
    bug = _bug()
    registry = {dedup_checker.fingerprint(bug): {"issue_id": 42, "closed": False}}
    out = dedup_checker.decide(bug, registry, [], closed_lookup=lambda _id: False)
    assert out["action"] == "skip_duplicate"
    assert out["status_source"] == "tracker"


def test_dedup_tracker_unreadable_falls_back_to_registry_value():
    """closed_lookup tra None (mat mang / khong doc duoc) -> tin registry, tha
    skip con hon tao trung."""
    bug = _bug()
    registry = {dedup_checker.fingerprint(bug): {"issue_id": 42, "closed": False}}
    out = dedup_checker.decide(bug, registry, [], closed_lookup=lambda _id: None)
    assert out["action"] == "skip_duplicate"
    assert out["status_source"] == "registry"


def test_dedup_closed_lookup_receives_the_stored_issue_id():
    bug = _bug()
    registry = {dedup_checker.fingerprint(bug): {"issue_id": "GET-9", "closed": False}}
    seen = []

    def lookup(issue_id):
        seen.append(issue_id)
        return True

    dedup_checker.decide(bug, registry, [], closed_lookup=lookup)
    assert seen == ["GET-9"]


def test_dedup_closed_lookup_not_called_when_no_local_hit():
    """Khong duoc goi API cho bug moi -- chi goi khi thuc su co nghi van trung."""
    called = []
    dedup_checker.decide(_bug(), {}, [], closed_lookup=lambda i: called.append(i))
    assert called == []


def test_dedup_registry_entry_without_issue_id_does_not_call_lookup():
    bug = _bug()
    registry = {dedup_checker.fingerprint(bug): {"closed": False}}
    called = []
    out = dedup_checker.decide(bug, registry, [],
                               closed_lookup=lambda i: called.append(i))
    assert called == []
    assert out["action"] == "skip_duplicate"


# --- template ---

def test_template_title_follows_parent_ticket_screen_summary_syntax():
    assert bug_template.build_title(_bug()) == "[#1234][Login] Sai chinh ta nut Dang nhap"


def test_template_title_custom_pattern_can_include_tc_id():
    title = bug_template.build_title(_bug(), "[{parent_ticket}][{screen}][{tc_id}] {summary}")
    assert title == "[#1234][Login][TC002] Sai chinh ta nut Dang nhap"


def test_template_title_unknown_variable_raises_clear_error():
    try:
        bug_template.build_title(_bug(), "[{khong_ton_tai}] {summary}")
    except ValueError as exc:
        assert "khong ton tai" in str(exc)
    else:
        raise AssertionError("phai raise ValueError")


def test_template_testcase_id_built_from_sheet_and_tc_id():
    assert bug_template.build_testcase_id(_bug()) == "Manual Test Cases_TC002"


def test_template_description_contains_all_required_sections():
    desc = bug_template.build_description(_bug(), markup="textile")
    for section in ("Testcase ID", "Device", "OS Version", "Browser",
                    "Điều kiện tiền đề", "Các bước tái hiện",
                    "Kết quả thực tế", "Kết quả mong đợi", "Phân loại / Label"):
        assert "h3. %s" % section in desc, section


def test_template_description_labels_include_severity_and_scope():
    desc = bug_template.build_description(_bug())
    assert "* Severity: Low" in desc
    assert "* Scope: Frontend" in desc
    assert "* Loại bug: UI / spelling" in desc


def test_template_markdown_markup_uses_hash_headings():
    desc = bug_template.build_description(_bug(), markup="markdown")
    assert "### Device" in desc
    assert "h3. Device" not in desc


def test_template_steps_list_rendered_as_numbered_list():
    desc = bug_template.build_description(_bug())
    assert "1. Mo /login" in desc
    assert "2. Quan sat nut" in desc


def test_template_regression_note_prepended_when_regression():
    desc = bug_template.build_description(_bug(), regression_of=42)
    assert desc.startswith("(!) Regression của 42")


def test_template_unsupported_fields_embedded_so_nothing_is_lost():
    desc = bug_template.build_description(_bug(), unsupported={"start_date": "2026-08-25"})
    assert "Field tracker không nhận native" in desc
    assert "start_date: 2026-08-25" in desc


def test_template_unsupported_field_already_in_body_is_not_repeated():
    """Severity/Device da co o phan II va III -> khong nhac lai lan hai o cuoi."""
    desc = bug_template.build_description(
        _bug(), unsupported={"severity": "Low", "device": "Laptop (MAC)",
                             "scope": "Frontend"})
    assert "Field tracker không nhận native" not in desc
    assert desc.count("Severity") == 1


def test_template_mixed_unsupported_lists_only_uncovered_field():
    desc = bug_template.build_description(
        _bug(), unsupported={"severity": "Low", "start_date": "2026-08-25"})
    assert "Field tracker không nhận native" in desc
    assert "start_date" in desc
    tail = desc.split("Field tracker không nhận native")[1]
    assert "severity" not in tail


def test_template_merged_bug_lists_affected_items():
    desc = bug_template.build_description(_bug(items=["btn: sai chu", "label: sai chu"]))
    assert "Danh sách item bị lỗi" in desc
    assert "1. btn: sai chu" in desc


def test_template_missing_optional_field_renders_placeholder_not_crash():
    desc = bug_template.build_description({"summary": "x", "bug_type": "logic"})
    assert "-" in desc

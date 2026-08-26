#!/usr/bin/env python3
"""Rule log bug: moi bug phai phan loai UI/logic, du field tai hien."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import bug_validator  # noqa: E402


def _valid_bug(**over):
    bug = {"parent_ticket": "#1234", "screen": "Login", "summary": "Sai mat khau van vao duoc",
           "bug_type": "logic", "steps_to_reproduce": ["Mo /login", "Nhap sai pass"],
           "actual_result": "Vao duoc dashboard", "expected_result": "Bao loi sai mat khau",
           "severity": "Critical", "priority": "High"}
    bug.update(over)
    return bug


def test_validator_full_valid_logic_bug_returns_no_error():
    # Arrange / Act
    errors, _ = bug_validator.validate(_valid_bug())
    # Assert
    assert errors == [], errors


def test_validator_missing_bug_type_reports_error():
    errors, _ = bug_validator.validate(_valid_bug(bug_type=""))
    assert any("bug_type" in e for e in errors), errors


def test_validator_ui_bug_without_subtype_reports_error():
    errors, _ = bug_validator.validate(_valid_bug(bug_type="ui", ui_subtype=""))
    assert any("ui_subtype" in e for e in errors), errors


def test_validator_ui_bug_without_subtype_suggests_from_description():
    errors, _ = bug_validator.validate(
        _valid_bug(bug_type="ui", ui_subtype="", summary="Sai chinh ta o nut Dang nhap"))
    assert any("spelling" in e for e in errors), errors


def test_validator_invalid_ui_subtype_reports_allowed_values():
    errors, _ = bug_validator.validate(_valid_bug(bug_type="ui", ui_subtype="mau_sac"))
    assert any("ui_subtype" in e and "spelling" in e for e in errors), errors


def test_validator_actual_equals_expected_rejected_as_not_a_bug():
    errors, _ = bug_validator.validate(
        _valid_bug(actual_result="Bao loi", expected_result="bao loi"))
    assert any("không phải bug" in e for e in errors), errors


def test_validator_missing_parent_ticket_reports_error_when_required():
    errors, _ = bug_validator.validate(_valid_bug(parent_ticket=""))
    assert any("parent_ticket" in e for e in errors), errors


def test_validator_missing_parent_ticket_allowed_when_policy_off():
    errors, _ = bug_validator.validate(
        _valid_bug(parent_ticket=""), {"bug_policy": {"require_parent_ticket": False}})
    assert errors == [], errors


def test_validator_invalid_severity_reports_allowed_values():
    errors, _ = bug_validator.validate(_valid_bug(severity="Blocker"))
    assert any("severity" in e and "Critical" in e for e in errors), errors


def test_validator_missing_evidence_is_warning_not_error():
    errors, warnings = bug_validator.validate(_valid_bug())
    assert errors == []
    assert any("evidence" in w for w in warnings), warnings


def test_validator_missing_steps_reports_error():
    errors, _ = bug_validator.validate(_valid_bug(steps_to_reproduce=[]))
    assert any("steps_to_reproduce" in e for e in errors), errors


def test_suggest_ui_subtype_detects_vietnamese_keywords():
    assert bug_validator.suggest_ui_subtype("chữ bị xô lệch vị trí") == "position"
    assert bug_validator.suggest_ui_subtype("cỡ chữ quá nhỏ") == "font_size"
    assert bug_validator.suggest_ui_subtype("sai chính tả") == "spelling"
    assert bug_validator.suggest_ui_subtype("hoàn toàn không liên quan") is None

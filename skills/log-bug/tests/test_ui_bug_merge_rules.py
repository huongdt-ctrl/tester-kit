#!/usr/bin/env python3
"""Ngoai le gop bug UI: Case A (cung loai loi, nhieu item) va Case B (cung item,
3-5 loi nho). Va rule cung: bug logic khong bao gio gop."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import ui_bug_merger  # noqa: E402


def _ui(screen, subtype, item, summary):
    return {"bug_type": "ui", "screen": screen, "ui_subtype": subtype,
            "item": item, "summary": summary}


def _indices(groups):
    return sorted(sorted(g["indices"]) for g in groups)


def test_merge_case_a_same_screen_same_subtype_many_items_merges():
    # Arrange: 3 loi chinh ta tren cung man hinh Login, khac item
    bugs = [_ui("Login", "spelling", "btn_submit", "Sai chinh ta nut"),
            _ui("Login", "spelling", "label_email", "Sai chinh ta label"),
            _ui("Login", "spelling", "title", "Sai chinh ta tieu de")]
    # Act
    plan = ui_bug_merger.plan_merge(bugs)
    # Assert
    assert _indices(plan["merge"]) == [[0, 1, 2]]
    assert plan["merge"][0]["case"] == "A"


def test_merge_case_a_different_screen_not_merged():
    bugs = [_ui("Login", "spelling", "a", "x"), _ui("Signup", "spelling", "b", "y")]
    plan = ui_bug_merger.plan_merge(bugs)
    assert plan["merge"] == []
    assert len(plan["separate"]) == 2


def test_merge_case_a_same_screen_different_subtype_not_merged_as_case_a():
    bugs = [_ui("Login", "spelling", "a", "x"), _ui("Login", "position", "b", "y")]
    plan = ui_bug_merger.plan_merge(bugs)
    assert plan["merge"] == []


def test_merge_case_b_same_item_three_small_errors_merges():
    # Arrange: cung 1 item, 3 loi nho khac loai -> dat nguong Case B
    bugs = [_ui("Login", "spelling", "btn_submit", "sai chu"),
            _ui("Login", "font", "btn_submit", "sai font"),
            _ui("Login", "position", "btn_submit", "lech vi tri")]
    plan = ui_bug_merger.plan_merge(bugs)
    assert _indices(plan["merge"]) == [[0, 1, 2]]
    assert plan["merge"][0]["case"] == "B"


def test_merge_case_b_same_item_two_errors_below_threshold_stays_separate():
    bugs = [_ui("Login", "spelling", "btn", "a"), _ui("Login", "font", "btn", "b")]
    plan = ui_bug_merger.plan_merge(bugs)
    assert plan["merge"] == []
    assert len(plan["separate"]) == 2


def test_merge_case_b_same_item_over_five_errors_requires_user_confirm():
    # Arrange: 6 loi tren CUNG 1 item -> vuot nguong 3-5 ma rule phu
    bugs = [_ui("Login", "spelling", "btn", "loi chinh ta %d" % i) for i in range(6)]
    # Act
    plan = ui_bug_merger.plan_merge(bugs)
    assert plan["merge"] == []
    assert len(plan["needs_confirm"]) == 1
    assert plan["needs_confirm"][0]["case"] == "B-overflow"


def test_merge_logic_bug_never_merged_even_when_identical():
    bugs = [{"bug_type": "logic", "screen": "Login", "item": "x", "summary": "a"},
            {"bug_type": "logic", "screen": "Login", "item": "x", "summary": "b"},
            {"bug_type": "logic", "screen": "Login", "item": "x", "summary": "c"}]
    plan = ui_bug_merger.plan_merge(bugs)
    assert plan["merge"] == []
    assert len(plan["separate"]) == 3
    assert all("rule 3" in g["reason"] for g in plan["separate"])


def test_merge_same_subtype_on_single_item_is_case_b_not_case_a():
    # Case A yeu cau NHIEU item. Cung 1 item thi thuoc Case B (nguong 3-5).
    bugs = [_ui("Login", "spelling", "btn", "a"), _ui("Login", "spelling", "btn", "b"),
            _ui("Login", "spelling", "btn", "c")]
    plan = ui_bug_merger.plan_merge(bugs)
    assert len(plan["merge"]) == 1
    assert plan["merge"][0]["case"] == "B"


def test_merge_case_a_takes_precedence_when_spanning_multiple_items():
    # Cung subtype trai tren 2 item khac nhau -> Case A thang
    bugs = [_ui("Login", "spelling", "btn", "a"), _ui("Login", "spelling", "label", "b"),
            _ui("Login", "spelling", "title", "c")]
    plan = ui_bug_merger.plan_merge(bugs)
    assert len(plan["merge"]) == 1
    assert plan["merge"][0]["case"] == "A"
    assert plan["merge"][0]["item_count"] == 3


def test_merge_case_a_two_errors_same_item_below_case_b_threshold_stays_separate():
    # 2 loi cung subtype cung item: khong du item cho Case A, khong du 3 cho Case B
    bugs = [_ui("Login", "spelling", "btn", "a"), _ui("Login", "spelling", "btn", "b")]
    plan = ui_bug_merger.plan_merge(bugs)
    assert plan["merge"] == []
    assert len(plan["separate"]) == 2


def test_merge_ui_bug_without_item_field_stays_separate():
    bugs = [_ui("Login", "spelling", "", "a"), _ui("Login", "font", "", "b")]
    plan = ui_bug_merger.plan_merge(bugs)
    assert plan["merge"] == []
    assert all("item" in g["reason"] for g in plan["separate"])


def test_build_merged_bug_case_a_lists_all_items():
    bugs = [_ui("Login", "spelling", "btn", "sai chu nut"),
            _ui("Login", "spelling", "label", "sai chu label")]
    plan = ui_bug_merger.plan_merge(bugs)
    merged = ui_bug_merger.build_merged_bug(bugs, plan["merge"][0])
    assert merged["merged_from_count"] == 2
    assert len(merged["items"]) == 2
    assert "spelling" in merged["summary"]
    assert "Login" in merged["summary"]


def test_build_merged_bug_does_not_mutate_input():
    bugs = [_ui("Login", "spelling", "btn", "a"), _ui("Login", "spelling", "lbl", "b")]
    plan = ui_bug_merger.plan_merge(bugs)
    ui_bug_merger.build_merged_bug(bugs, plan["merge"][0])
    assert "items" not in bugs[0]
    assert bugs[0]["summary"] == "a"

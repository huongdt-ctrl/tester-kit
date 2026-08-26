#!/usr/bin/env python3
"""Unit tests cho column_mapper + case_filter -- hai cho tung sinh ra ket qua
'0 test case' im lang. Khong network, du lieu dinh nghia ngay trong test."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import case_filter  # noqa: E402
import column_mapper  # noqa: E402

HEADER = ["Classification 1", "TC ID", "Title", "Priority", "Preconditions", "Test Steps",
          "Test Data", "Expected Results", "Result", "Executed Date", "Executed by", "Notes"]

ALIAS_CFG = {
    "column_header_aliases": {
        "tc_id": ["TC ID"], "title": ["Title"], "preconditions": ["Preconditions"],
        "steps": ["Steps", "Test Steps"], "test_data": ["Test data", "Test Data"],
        "expected_result": ["Expected Result", "Expected Results"],
        "test_result": ["Test result", "Result"], "test_date": ["Test date", "Executed Date"],
        "tested_by": ["Tested by", "Executed by"], "remark": ["Remark", "Notes"],
    }
}


def _cases():
    return [
        {"tc_id": "TC001", "test_result": "Untested", "priority": "High", "classification_1": "Common Test Cases"},
        {"tc_id": "TC002", "test_result": "Fail", "priority": "High", "classification_1": "Functional Test Cases"},
        {"tc_id": "TC003", "test_result": "Pass", "priority": "Low", "classification_1": "Functional Test Cases"},
        {"tc_id": "TC004", "test_result": "Pending", "priority": "Medium", "classification_1": "Other"},
    ]


class ColumnMapperTests(unittest.TestCase):
    def test_column_mapper_matches_alias_spelling_case_insensitively(self):
        # Arrange + Act
        mapping = column_mapper.map_columns(HEADER, ALIAS_CFG)
        # Assert
        self.assertEqual(mapping["steps"], HEADER.index("Test Steps"))
        self.assertEqual(mapping["expected_result"], HEADER.index("Expected Results"))
        self.assertEqual(mapping["remark"], HEADER.index("Notes"))

    def test_column_mapper_manifest_exact_mapping_wins_over_profile_alias(self):
        # Arrange
        cfg = dict(ALIAS_CFG); cfg["column_mapping"] = {"test_result": "Result"}
        # Act
        mapping = column_mapper.map_columns(HEADER, cfg)
        # Assert
        self.assertEqual(mapping["test_result"], HEADER.index("Result"))

    def test_column_mapper_missing_required_column_raises(self):
        # Arrange
        header = [h for h in HEADER if h != "TC ID"]
        mapping = column_mapper.map_columns(header, ALIAS_CFG)
        # Act + Assert
        with self.assertRaises(column_mapper.ColumnMappingError) as ctx:
            column_mapper.validate_mapping(mapping, ALIAS_CFG)
        self.assertIn("tc_id", str(ctx.exception))

    def test_column_mapper_missing_priority_column_raises_when_priority_filter_active(self):
        # Arrange -- day chinh la bug cu: filter Priority tren sheet khong co cot Priority
        header = [h for h in HEADER if h != "Priority"]
        cfg = dict(ALIAS_CFG); cfg["case_filter"] = {"include_priorities": ["High"]}
        mapping = column_mapper.map_columns(header, cfg)
        # Act + Assert
        with self.assertRaises(column_mapper.ColumnMappingError) as ctx:
            column_mapper.validate_mapping(mapping, cfg)
        self.assertIn("filter", str(ctx.exception).lower())

    def test_column_mapper_missing_priority_column_allowed_when_filter_empty(self):
        # Arrange
        header = [h for h in HEADER if h != "Priority"]
        cfg = dict(ALIAS_CFG); cfg["case_filter"] = {"include_priorities": []}
        mapping = column_mapper.map_columns(header, cfg)
        # Act
        result = column_mapper.validate_mapping(mapping, cfg)
        # Assert
        self.assertEqual(result, [])


class ExecutionModeTests(unittest.TestCase):
    def test_case_filter_baseline_keeps_only_configured_statuses(self):
        # Arrange
        cfg = {"run": {"execution_mode": "baseline", "execute_only_statuses": ["Untested", "Pending"]}}
        # Act
        selected, _ = case_filter.select_cases(_cases(), cfg)
        # Assert
        self.assertEqual([c["tc_id"] for c in selected], ["TC001", "TC004"])

    def test_case_filter_rerun_failed_ignores_status_filter_and_keeps_fail_only(self):
        # Arrange -- status filter [Untested, Pending] khong duoc loai bo case Fail
        cfg = {"run": {"execution_mode": "rerun_failed", "execute_only_statuses": ["Untested", "Pending"]}}
        # Act
        selected, _ = case_filter.select_cases(_cases(), cfg)
        # Assert
        self.assertEqual([c["tc_id"] for c in selected], ["TC002"])

    def test_case_filter_selected_cases_without_ids_raises(self):
        # Arrange
        cfg = {"run": {"execution_mode": "selected_cases"}, "case_filter": {"include_tc_ids": []}}
        # Act + Assert
        with self.assertRaises(case_filter.CaseFilterError):
            case_filter.select_cases(_cases(), cfg)

    def test_case_filter_invalid_execution_mode_raises(self):
        # Arrange
        cfg = {"run": {"execution_mode": "everything"}}
        # Act + Assert
        with self.assertRaises(case_filter.CaseFilterError):
            case_filter.select_cases(_cases(), cfg)


class FilterSemanticsTests(unittest.TestCase):
    def test_case_filter_empty_list_means_no_filter_not_exclude_all(self):
        # Arrange
        cfg = {"run": {"execution_mode": "baseline"},
               "case_filter": {"include_priorities": [], "include_classification_1": []}}
        # Act
        selected, _ = case_filter.select_cases(_cases(), cfg)
        # Assert
        self.assertEqual(len(selected), 4)

    def test_case_filter_exclude_beats_include_on_same_tc_id(self):
        # Arrange
        cfg = {"run": {"execution_mode": "baseline"},
               "case_filter": {"include_tc_ids": ["TC001", "TC002"], "exclude_tc_ids": ["TC002"]}}
        # Act
        selected, _ = case_filter.select_cases(_cases(), cfg)
        # Assert
        self.assertEqual([c["tc_id"] for c in selected], ["TC001"])

    def test_case_filter_trail_records_count_after_every_step(self):
        # Arrange
        cfg = {"run": {"execution_mode": "baseline"}, "case_filter": {"include_priorities": ["High"]}}
        # Act
        selected, trail = case_filter.select_cases(_cases(), cfg)
        # Assert -- trail phai phan biet duoc 'khong case nao thoa' voi 'map sai cot'
        self.assertEqual(trail[0], ("tong so case trong worksheet", 4))
        self.assertEqual(trail[-1][1], len(selected))
        self.assertGreaterEqual(len(trail), 5)

    def test_case_filter_priority_filter_selects_matching_cases_only(self):
        # Arrange
        cfg = {"run": {"execution_mode": "baseline"}, "case_filter": {"include_priorities": ["High"]}}
        # Act
        selected, _ = case_filter.select_cases(_cases(), cfg)
        # Assert
        self.assertEqual([c["tc_id"] for c in selected], ["TC001", "TC002"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

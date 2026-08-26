#!/usr/bin/env python3
"""Integration test: doc file test case that (fixtures/*.xlsx) -> filter -> ghi
ket qua -> doc lai de xac nhan.

Tu don dep: moi test copy fixture ra tempdir rieng va xoa sau khi chay, nen
fixture goc khong bao gio bi ghi vao (test_standards.md: integration test phai
tu don dep)."""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import case_filter  # noqa: E402
import column_mapper  # noqa: E402
import sheet_io  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "sample_testcases_event_editing.xlsx")

BASE_CFG = {
    "testcase_source": {"source_type": "excel", "worksheet_name": "Manual Test Cases",
                        "header_row_index": 1, "data_start_row_index": 2},
    "column_mapping": {
        "tc_id": "TC ID", "title": "Title", "preconditions": "Preconditions",
        "steps": "Steps", "test_data": "Test data", "expected_result": "Expected Result",
        "test_result": "Test result", "test_date": "Test date", "tested_by": "Tested by",
        "remark": "Remark", "bug_id": "Bug ID", "bug_url": "Bug URL",
        "actual_result": "Actual Result", "priority": "Priority",
        "classification_1": "Classification 1",
    },
    "update_policy": {
        "execution_columns": ["Test result", "Test date", "Tested by", "Remark",
                              "Actual Result", "Bug ID", "Bug URL"],
        "definition_columns": ["Classification 1", "TC ID", "Title", "Priority",
                               "Preconditions", "Steps", "Test data", "Expected Result"],
    },
    "result_policy": {"test_date_format": "YYYY-MM-DD"},
}


class ExcelRoundtripTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="exec_tc_")
        self.path = os.path.join(self.tmpdir, "testcases.xlsx")
        shutil.copy2(FIXTURE, self.path)
        self.cfg = {k: (dict(v) if isinstance(v, dict) else v) for k, v in BASE_CFG.items()}
        self.cfg["testcase_source"] = dict(BASE_CFG["testcase_source"])
        self.cfg["testcase_source"]["local_excel_path"] = self.path

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _open(self):
        ws = sheet_io.open_worksheet(self.cfg)
        header = ws.row_values(1)
        mapping = column_mapper.map_columns(header, self.cfg)
        column_mapper.validate_mapping(mapping, self.cfg)
        return ws, header, mapping

    def test_excel_read_returns_five_cases_with_row_numbers(self):
        # Arrange
        ws, _, mapping = self._open()
        # Act
        cases = sheet_io.read_cases(ws, self.cfg, mapping)
        # Assert
        self.assertEqual([c["tc_id"] for c in cases], ["TC001", "TC002", "TC003", "TC004", "TC005"])
        self.assertEqual([c["row_number"] for c in cases], [2, 3, 4, 5, 6])

    def test_excel_read_carries_existing_bug_id_for_failed_case(self):
        # Arrange
        ws, _, mapping = self._open()
        # Act
        cases = sheet_io.read_cases(ws, self.cfg, mapping)
        tc003 = [c for c in cases if c["tc_id"] == "TC003"][0]
        # Assert -- day la du lieu ma rule chong bug trung (muc 12A) can
        self.assertEqual(tc003["test_result"], "Fail")
        self.assertEqual(tc003["bug_id"], "1234")

    def test_excel_baseline_filter_selects_untested_and_pending_only(self):
        # Arrange
        ws, _, mapping = self._open()
        cases = sheet_io.read_cases(ws, self.cfg, mapping)
        cfg = dict(self.cfg)
        cfg["run"] = {"execution_mode": "baseline", "execute_only_statuses": ["Untested", "Pending"]}
        # Act
        selected, trail = case_filter.select_cases(cases, cfg)
        # Assert
        self.assertEqual([c["tc_id"] for c in selected], ["TC001", "TC002", "TC005"])
        self.assertEqual(trail[0][1], 5)

    def test_excel_rerun_failed_filter_selects_only_failed_case(self):
        # Arrange
        ws, _, mapping = self._open()
        cases = sheet_io.read_cases(ws, self.cfg, mapping)
        cfg = dict(self.cfg)
        cfg["run"] = {"execution_mode": "rerun_failed", "execute_only_statuses": ["Untested"]}
        # Act
        selected, _ = case_filter.select_cases(cases, cfg)
        # Assert
        self.assertEqual([c["tc_id"] for c in selected], ["TC003"])

    def test_excel_write_result_persists_and_is_readable_again(self):
        # Arrange
        ws, header, mapping = self._open()
        updates = {"test_result": "Pass", "test_date": "2026-08-24",
                   "tested_by": "huongdt", "remark": ""}
        # Act
        written = sheet_io.write_result(ws, self.cfg, mapping, header, 2, updates)
        ws2, _, mapping2 = self._open()          # mo lai tu disk
        cases = sheet_io.read_cases(ws2, self.cfg, mapping2)
        tc001 = [c for c in cases if c["tc_id"] == "TC001"][0]
        # Assert
        self.assertEqual(written, 4)
        self.assertEqual(tc001["test_result"], "Pass")

    def test_excel_write_refuses_to_touch_expected_result_column(self):
        # Arrange -- guard quan trong nhat: khong duoc pha test case goc
        ws, header, mapping = self._open()
        # Act + Assert
        with self.assertRaises(sheet_io.SheetWriteError):
            sheet_io.write_result(ws, self.cfg, mapping, header, 2,
                                  {"expected_result": "bi ghi de"})
        # va noi dung goc van con nguyen
        cases = sheet_io.read_cases(ws, self.cfg, mapping)
        tc001 = [c for c in cases if c["tc_id"] == "TC001"][0]
        self.assertIn("Màn hình Edit Event mở ra", tc001["expected_result"])

    def test_excel_missing_local_path_raises_clear_error(self):
        # Arrange
        cfg = dict(self.cfg)
        cfg["testcase_source"] = dict(self.cfg["testcase_source"])
        cfg["testcase_source"]["local_excel_path"] = ""
        # Act + Assert
        with self.assertRaises(sheet_io.SheetWriteError) as ctx:
            sheet_io.open_worksheet(cfg)
        self.assertIn("local_excel_path", str(ctx.exception))

    def test_excel_backup_creates_sibling_file_when_configured(self):
        # Arrange
        ws, _, _ = self._open()
        cfg = dict(self.cfg)
        cfg["update_policy"] = dict(self.cfg["update_policy"])
        cfg["update_policy"]["mode"] = "backup_then_update"
        # Act
        target = sheet_io.backup_if_configured(ws, cfg, "event_editing")
        # Assert
        self.assertTrue(os.path.exists(target))
        self.assertNotEqual(target, self.path)


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Test: hai subcommand collect va build -- ghi gi, chan gi, dat ten file the nao."""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helpers import (PROFILE_ENV, PROFILE_PLAINTEXT, TEMPLATE, bug_row,
                     run_cli, write)

class TestCollectCommand(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["BUG_ANALYST_TEST_TOKEN"] = "t"
        self.addCleanup(os.environ.pop, "BUG_ANALYST_TEST_TOKEN", None)

    def test_collect_writes_rows_and_flags_cells_awaiting_analysis(self):
        # Arrange
        profile = write(self.tmp, "p.yaml", PROFILE_ENV)
        out = os.path.join(self.tmp, "bugs.json")
        issues = [{"id": "#501", "title": "[GET-1][G10.1] sai chinh ta", "url": "u",
                   "labels": ["bug", "type::UI"], "milestone": "Sprint 3",
                   "priority": "High", "status": "opened", "created_at": "2026-08-05"}]
        # Act
        with mock.patch("adapters.gitlab_adapter.GitLabAdapter.list_bugs",
                        return_value=issues):
            code, payload = run_cli(["--profile", profile, "--date-from", "2026-08-01",
                                     "--date-to", "2026-08-31", "collect", "--out", out])
        # Assert
        self.assertEqual(code, 0)
        self.assertEqual(payload["collected"], 1)
        with open(out, encoding="utf-8") as fh:
            saved = json.load(fh)
        row = saved["rows"][0]
        self.assertEqual((row["egg_id"], row["egg_name"]), ("#501", "sai chinh ta"))
        self.assertEqual((row["screen"], row["bug_type"]), ("G10.1", "UI"))
        self.assertEqual(payload["pending_analysis"][0]["missing"],
                         ["severity", "cause", "root_cause"])


class TestBuildCommand(unittest.TestCase):
    def setUp(self):
        if not os.path.exists(TEMPLATE):
            self.skipTest("khong tim thay template goc")
        self.tmp = tempfile.mkdtemp()

    def _bugs_file(self, analysed):
        path = os.path.join(self.tmp, "bugs.json")
        data = {"phase": "Sprint 3", "date_from": "2026-08-01", "date_to": "2026-08-31",
                "rows": [bug_row(i, analysed) for i in range(1, 4)]}
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)
        return path

    def test_build_refuses_when_analysis_cells_are_still_empty(self):
        # Arrange
        bugs = self._bugs_file(analysed=False)
        # Act
        code, payload = run_cli(["build", "--bugs-file", bugs,
                                 "--out", os.path.join(self.tmp, "o.xlsx")])
        # Assert
        self.assertEqual(code, 1)
        self.assertIn("chua phan tich du", payload["error"])
        self.assertEqual(len(payload["pending_analysis"]), 3)

    def test_build_proceeds_on_incomplete_data_only_when_explicitly_allowed(self):
        # Arrange
        bugs = self._bugs_file(analysed=False)
        out = os.path.join(self.tmp, "o.xlsx")
        # Act
        code, payload = run_cli(["build", "--bugs-file", bugs, "--out", out,
                                 "--allow-incomplete"])
        # Assert
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(out))
        self.assertEqual(len(payload["pending_analysis"]), 3)

    def test_build_names_output_file_by_phase_and_date_window(self):
        # Arrange
        bugs = self._bugs_file(analysed=True)
        # Act
        code, payload = run_cli(["build", "--bugs-file", bugs,
                                 "--out", os.path.join(self.tmp, "x.xlsx")])
        # Assert
        self.assertEqual(code, 0)
        import workbook_builder
        self.assertEqual(
            workbook_builder.output_filename("Sprint 3", "2026-08-01", "2026-08-31"),
            "Sprint 3_Phân tích Bug_20260801-20260831.xlsx")

    def test_cli_returns_json_even_for_unexpected_internal_error(self):
        # Arrange: template tro vao file rac -> openpyxl nem loi rieng cua no
        bugs = self._bugs_file(analysed=True)
        junk = os.path.join(self.tmp, "junk.xlsx")
        with open(junk, "w", encoding="utf-8") as fh:
            fh.write("khong phai xlsx")
        # Act
        code, payload = run_cli(["build", "--bugs-file", bugs, "--template", junk,
                                 "--out", os.path.join(self.tmp, "o.xlsx")])
        # Assert -- van la JSON, van exit 1, khong phai traceback
        self.assertEqual(code, 1)
        self.assertFalse(payload["ok"])
        self.assertIn("error", payload)

    def test_build_on_empty_bug_list_fails_with_clear_message(self):
        # Arrange
        path = os.path.join(self.tmp, "empty.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"rows": []}, fh)
        # Act
        code, payload = run_cli(["build", "--bugs-file", path])
        # Assert
        self.assertEqual(code, 1)
        self.assertIn("khong co dong bug nao", payload["error"])



if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestReviewFollowUps(unittest.TestCase):
    """Regression cho cac phat hien cua vong code review."""

    def setUp(self):
        if not os.path.exists(TEMPLATE):
            self.skipTest("khong tim thay template goc")
        self.tmp = tempfile.mkdtemp()

    def _write(self, rows):
        path = os.path.join(self.tmp, "bugs.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"phase": "Sprint 3", "date_from": "2026-08-01",
                       "date_to": "2026-08-31", "rows": rows}, fh, ensure_ascii=False)
        return path

    def test_build_on_empty_list_is_blocked_but_escapable(self):
        # 0 bug thuong la loc sai -> chan; nhung van phai xuat duoc khi user chac.
        # Arrange
        bugs = self._write([])
        out = os.path.join(self.tmp, "empty.xlsx")
        # Act
        blocked, payload = run_cli(["build", "--bugs-file", bugs, "--out", out])
        allowed, _ = run_cli(["build", "--bugs-file", bugs, "--out", out,
                              "--allow-empty"])
        # Assert
        self.assertEqual(blocked, 1)
        self.assertIn("--allow-empty", payload["error"])
        self.assertEqual(allowed, 0)
        self.assertTrue(os.path.exists(out))

    def test_uncounted_ignores_letter_case_like_excel_countif(self):
        # COUNTIF dem duoc "major" cho nhan "Major" -> khong duoc bao nham la
        # bug se khong duoc dem.
        # Arrange
        row = bug_row(1)
        row["severity"] = "major"
        row["cause"] = "cod1.2 coding logic mistake"
        bugs = self._write([row])
        # Act
        code, payload = run_cli(["build", "--bugs-file", bugs,
                                 "--out", os.path.join(self.tmp, "c.xlsx")])
        # Assert
        self.assertEqual(code, 0)
        self.assertEqual(payload["uncounted"], [])

    def test_uncounted_still_reports_value_absent_from_catalogue(self):
        # Arrange
        row = bug_row(1)
        row["severity"] = "Nghiem trong"
        bugs = self._write([row])
        # Act
        code, payload = run_cli(["build", "--bugs-file", bugs,
                                 "--out", os.path.join(self.tmp, "d.xlsx")])
        # Assert
        self.assertEqual(code, 0)
        self.assertEqual([u["value"] for u in payload["uncounted"]], ["Nghiem trong"])

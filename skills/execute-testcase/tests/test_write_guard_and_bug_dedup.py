#!/usr/bin/env python3
"""Unit tests cho hai guard quan trong nhat:
  - sheet_io.assert_writable: khong bao gio ghi vao cot definition
  - redmine_client.decide_duplicate_action: rerun khong tao bug trung
Khong network (chi test ham quyet dinh thuan), khong credential."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import redmine_client  # noqa: E402
import sheet_io  # noqa: E402

CFG = {
    "update_policy": {
        "execution_columns": ["Test result", "Test date", "Tested by", "Remark",
                              "Actual Result", "Bug ID", "Bug URL"],
        "definition_columns": ["Classification 1", "TC ID", "Title", "Priority",
                               "Preconditions", "Steps", "Test data", "Expected Result"],
    }
}


class WriteGuardTests(unittest.TestCase):
    def test_sheet_io_allows_write_to_execution_column(self):
        # Arrange + Act + Assert
        self.assertTrue(sheet_io.assert_writable("Test result", CFG))
        self.assertTrue(sheet_io.assert_writable("Remark", CFG))

    def test_sheet_io_refuses_write_to_definition_column(self):
        # Act + Assert
        with self.assertRaises(sheet_io.SheetWriteError) as ctx:
            sheet_io.assert_writable("Expected Result", CFG)
        self.assertIn("definition", str(ctx.exception))

    def test_sheet_io_refuses_write_to_unlisted_column(self):
        # Act + Assert
        with self.assertRaises(sheet_io.SheetWriteError):
            sheet_io.assert_writable("Some Random Column", CFG)

    def test_sheet_io_refuses_column_listed_in_both_lists(self):
        # Arrange -- cau hinh mau thuan phai bi tu choi, khong duoc tu chon ben nao
        cfg = {"update_policy": {"execution_columns": ["Remark", "Title"],
                                 "definition_columns": ["Title"]}}
        # Act + Assert
        with self.assertRaises(sheet_io.SheetWriteError) as ctx:
            sheet_io.assert_writable("Title", cfg)
        self.assertIn("mau thuan", str(ctx.exception))

    def test_sheet_io_trims_whitespace_before_matching_header(self):
        # Act + Assert
        self.assertTrue(sheet_io.assert_writable("  Test date  ", CFG))

    def test_sheet_io_today_string_follows_configured_date_format(self):
        # Arrange
        cfg = {"result_policy": {"test_date_format": "YYYY-MM-DD"}}
        # Act
        value = sheet_io.today_string(cfg)
        # Assert
        self.assertRegex(value, r"^\d{4}-\d{2}-\d{2}$")


class BugCreationPolicyTests(unittest.TestCase):
    def test_redmine_should_create_bug_true_for_fail(self):
        # Arrange
        cfg = {"redmine_policy": {"create_bug_when_status_is": ["Fail"],
                                  "never_create_bug_when_status_is": ["Pending", "Untested", "N/A"]}}
        # Act + Assert
        self.assertTrue(redmine_client.should_create_bug("Fail", cfg))

    def test_redmine_should_create_bug_false_for_pending_blocker(self):
        # Arrange -- loi moi truong khong duoc thanh bug ung dung
        cfg = {"redmine_policy": {"create_bug_when_status_is": ["Fail"],
                                  "never_create_bug_when_status_is": ["Pending", "Untested", "N/A"]}}
        # Act + Assert
        for status in ("Pending", "Untested", "N/A"):
            self.assertFalse(redmine_client.should_create_bug(status, cfg))


class DuplicateBugTests(unittest.TestCase):
    def test_redmine_dedup_creates_new_when_no_existing_bug(self):
        self.assertEqual(redmine_client.decide_duplicate_action("", None), "create_new")

    def test_redmine_dedup_reuses_when_existing_bug_still_open(self):
        self.assertEqual(redmine_client.decide_duplicate_action("1234", "New"), "reuse_open")
        self.assertEqual(redmine_client.decide_duplicate_action("1234", "In Progress"), "reuse_open")

    def test_redmine_dedup_creates_regression_when_existing_bug_closed(self):
        for closed in ("Closed", "Rejected", "closed", "Resolved"):
            self.assertEqual(redmine_client.decide_duplicate_action("1234", closed),
                             "create_regression")

    def test_redmine_dedup_reuses_when_status_unreadable(self):
        # Arrange -- khong doc duoc status thi tha bo sot hon la spam bug trung
        self.assertEqual(redmine_client.decide_duplicate_action("1234", None), "reuse_open")

    def test_redmine_bug_description_marks_regression_of_old_bug(self):
        # Arrange
        fields = {"Module": "event_editing", "TC ID": "TC002"}
        # Act
        body = redmine_client.build_bug_description(fields, regression_of="1234")
        # Assert
        self.assertTrue(body.startswith("Regression cua 1234"))
        self.assertIn("TC002", body)

    def test_redmine_bug_title_follows_configured_pattern(self):
        # Act
        title = redmine_client.build_bug_title(
            "[TEST][{module_name}][{tc_id}] {short_summary}", "event_editing", "TC002", "luu duoc ngay sai")
        # Assert
        self.assertEqual(title, "[TEST][event_editing][TC002] luu duoc ngay sai")

    def test_redmine_settings_raises_when_api_key_not_resolved(self):
        # Arrange -- config_loader phai resolve truoc; con 'env:' la da bo buoc do
        cfg = {"redmine": {"enabled": True, "base_url": "https://r.example.com",
                           "api_key": "env:RM_KEY", "project_id": "p1"}}
        # Act + Assert
        with self.assertRaises(redmine_client.RedmineError) as ctx:
            redmine_client.redmine_settings(cfg)
        self.assertIn("resolve", str(ctx.exception))

    def test_redmine_settings_returns_none_when_disabled(self):
        self.assertIsNone(redmine_client.redmine_settings({"redmine": {"enabled": False}}))


if __name__ == "__main__":
    unittest.main(verbosity=2)

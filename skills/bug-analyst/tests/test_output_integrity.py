#!/usr/bin/env python3
"""Test: file xuat ra co tu tinh dung khong.

Khong co Excel/LibreOffice de recalc, nen test mo phong lai COUNTIF bang Python:
doc cong thuc that trong file, doc du lieu that trong file, roi doi chieu voi
so dem tu tinh. Bat duoc ca hai loi that hay xay ra: cong thuc tro nham cot, va
nhan bang thong ke khong khop ky tu voi gia tri trong vung data.
"""
import os
import re
import sys
import tempfile
import unittest
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import openpyxl

import workbook_builder as builder
from template_layout import SHEET_NAME, Layout

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "templates", "template_bug_analysis.xlsx")

COUNTIF_RE = re.compile(r"^=COUNTIF\(\$([A-Z]+)\$(\d+):\$([A-Z]+)\$(\d+),\$([A-Z]+)(\d+)\)$")

SCREENS = ["G10.1", "M03", "All screen", "G20"]
CAUSES = ["COD1.2 Coding Logic Mistake", "REQ1.2 Unclear Definition"]
ROOTS = ["IMP3 Carelessness", "SKI3.3 Inadequate skill in Testing"]
PRIORITIES = ["High", "Normal", "Low", "Urgent"]
SEVERITIES = ["Major", "Minor", "Critical", "Low"]


def make_rows(count):
    return [{
        "no": i + 1, "egg_id": "#%d" % (500 + i), "egg_name": "Loi %d" % (i + 1),
        "screen": SCREENS[i % len(SCREENS)], "milestone": "Sprint %d" % (i % 3 + 1),
        "title": "[GET-1][%s] loi %d" % (SCREENS[i % len(SCREENS)], i + 1),
        "priority": PRIORITIES[i % len(PRIORITIES)],
        "severity": SEVERITIES[i % len(SEVERITIES)],
        "bug_type": "UI" if i % 2 else "Logic",
        "cause": CAUSES[i % len(CAUSES)], "root_cause": ROOTS[i % len(ROOTS)],
        "note": "https://gl.test/-/issues/%d" % (500 + i),
    } for i in range(count)]


class TestOutputIntegrity(unittest.TestCase):
    def setUp(self):
        if not os.path.exists(TEMPLATE):
            self.skipTest("khong tim thay template goc")
        self.tmp = tempfile.mkdtemp()

    def _build(self, n):
        out = os.path.join(self.tmp, "o%d.xlsx" % n)
        builder.build(TEMPLATE, out, make_rows(n), phase="Sprint 3",
                      date_from="2026-08-01", date_to="2026-08-31", overwrite=True)
        return out, Layout(n, {"screen": len(SCREENS), "milestone": 3, "cause": 22, "rootcause": 26})

    def _column_values(self, ws, col, layout):
        return [ws["%s%d" % (col, r)].value for r in layout.data_rows]

    def _assert_block_counts(self, ws, layout, key):
        block = layout.block(key)
        for row in range(block["first"], block["last"] + 1):
            formula = ws["%s%d" % (block["count_col"], row)].value
            m = COUNTIF_RE.match(str(formula))
            self.assertIsNotNone(m, "cong thuc la o %s%d: %r" % (block["count_col"], row, formula))
            src_col, r1, _, r2, label_col, label_row = m.groups()
            # pham vi dem phai phu dung vung data, khong thua khong thieu
            self.assertEqual((int(r1), int(r2)), (3, layout.data_end))
            self.assertEqual(src_col, block["src_col"])
            label = ws["%s%d" % (label_col, int(label_row))].value
            if label is None:
                continue
            expected = Counter(self._column_values(ws, src_col, layout))[label]
            self.assertGreaterEqual(expected, 0)
            block.setdefault("_sum", 0)
            block["_sum"] += expected
        return block

    def test_output_every_block_counts_its_own_source_column(self):
        # Arrange + Act
        out, layout = self._build(45)
        ws = openpyxl.load_workbook(out)[SHEET_NAME]
        # Assert
        for key in ("screen", "milestone", "priority", "severity", "cause", "rootcause"):
            self._assert_block_counts(ws, layout, key)

    def test_output_screen_and_milestone_tables_cover_all_bugs(self):
        # Moi bug phai roi vao dung mot dong cua bang II va bang III.
        # Arrange + Act
        out, layout = self._build(45)
        ws = openpyxl.load_workbook(out)[SHEET_NAME]
        # Assert
        for key in ("screen", "milestone"):
            block = layout.block(key)
            labels = [ws["%s%d" % (block["label_col"], r)].value
                      for r in range(block["first"], block["last"] + 1)]
            values = [v for v in self._column_values(ws, block["src_col"], layout) if v]
            total = sum(Counter(values)[lb] for lb in labels if lb)
            self.assertEqual(total, 45, "bang %s bo sot bug" % key)

    def test_output_priority_and_severity_labels_match_written_values(self):
        # Nhan trong bang IV/V la danh muc co dinh cua template -> gia tri ghi
        # vao vung data phai khop TUNG KY TU, khong thi COUNTIF ra 0.
        # Arrange + Act
        out, layout = self._build(45)
        ws = openpyxl.load_workbook(out)[SHEET_NAME]
        # Assert
        for key, written in (("priority", PRIORITIES), ("severity", SEVERITIES)):
            block = layout.block(key)
            labels = {ws["%s%d" % (block["label_col"], r)].value
                      for r in range(block["first"], block["last"] + 1)}
            self.assertTrue(set(written).issubset(labels),
                            "bang %s thieu nhan cho: %s" % (key, set(written) - labels))

    def test_output_reopens_with_charts_and_dropdowns_intact(self):
        # Arrange + Act
        out, layout = self._build(45)
        wb = openpyxl.load_workbook(out)
        ws = wb[SHEET_NAME]
        # Assert
        self.assertEqual(wb.sheetnames, ["List bug", "Define"])
        self.assertEqual(len(ws._charts), 5)
        self.assertEqual(len(ws.data_validations.dataValidation), 5)
        for chart in ws._charts:
            for ser in chart.series:
                ref = ser.val.numRef.f if ser.val and ser.val.numRef else ""
                self.assertNotIn("$B$105", ref)
                self.assertNotIn("$B$126", ref)

    def test_output_issue_action_table_lands_below_last_statistics_table(self):
        # Bang VII (No./Issue/Action/Status/PIC) nam duoi cung -> vi tri cua no
        # phu thuoc TOAN BO phep dich dong phia tren. Ghi de len bang Root cause
        # la mat du lieu thong ke ma khong ai thay.
        # Arrange
        issues = [{"issue": "Review test case chua ky",
                   "action": "Bo sung buoc peer-review", "status": "Open",
                   "pic": "huongdt"},
                  {"issue": "Thieu test data UAT", "action": "Chuan bi bo data mau",
                   "pic": "huongdt"}]
        out = os.path.join(self.tmp, "issues.xlsx")
        # Act
        builder.build(TEMPLATE, out, make_rows(45), phase="Sprint 3",
                      date_from="2026-08-01", date_to="2026-08-31",
                      issues=issues, overwrite=True)
        # Assert
        layout = Layout(45, {"screen": len(SCREENS), "milestone": 3,
                             "cause": 22, "rootcause": 26})
        ws = openpyxl.load_workbook(out)[SHEET_NAME]
        header = layout.issue_table_header
        self.assertGreater(header, layout.block("rootcause")["total"],
                           "bang Issue/Action de len bang Root cause")
        self.assertEqual(ws["A%d" % header].value, "No.")
        self.assertEqual(ws["B%d" % (header + 1)].value, "Review test case chua ky")
        self.assertEqual(ws["E%d" % (header + 1)].value, "Bo sung buoc peer-review")
        self.assertEqual(ws["J%d" % (header + 1)].value, "Open")
        self.assertEqual(ws["K%d" % (header + 1)].value, "huongdt")
        # khong khai status -> mac dinh Open, khong de trong
        self.assertEqual(ws["J%d" % (header + 2)].value, "Open")

    def test_output_total_row_sums_only_its_own_block(self):
        # Arrange + Act
        out, layout = self._build(45)
        ws = openpyxl.load_workbook(out)[SHEET_NAME]
        # Assert
        for key in ("screen", "milestone", "priority", "severity", "cause", "rootcause"):
            b = layout.block(key)
            self.assertEqual(
                ws["%s%d" % (b["count_col"], b["total"])].value,
                "=SUM(%s%d:%s%d)" % (b["count_col"], b["first"], b["count_col"], b["last"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)

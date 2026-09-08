#!/usr/bin/env python3
"""Regression: nhan bang thong ke phai khop gia tri trong vung data theo dung
luat so sanh cua Excel COUNTIF.

Luat that cua COUNTIF voi tieu chi la chu:
  - BO QUA hoa/thuong  ("G10" khop ca "g10")
  - KHONG bo qua dau cach ("Sprint 3" khong khop "Sprint 3 ")

Hai bug goc bat duoc o day:
  1. "G10" va "g10" tao HAI dong nhan -> moi dong dem ca hai -> TOTAL dem doi (7/4)
  2. Nhan bi strip nhung o du lieu ghi raw -> "Sprint 3 " khong duoc dem (3/4)
"""
import os
import sys
import tempfile
import unittest
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import openpyxl

import workbook_builder as builder
from helpers import TEMPLATE
from template_layout import SHEET_NAME, Layout


def bug(idx, screen, milestone):
    return {"no": idx, "egg_id": "#%d" % idx, "egg_name": "loi %d" % idx,
            "screen": screen, "milestone": milestone, "title": "t",
            "priority": "High", "severity": "Major", "bug_type": "UI",
            "cause": "COD1.2 Coding Logic Mistake",
            "root_cause": "IMP3 Carelessness", "note": ""}


def countif_total(labels, cells):
    """Mo phong SUM(COUNTIF(...)) dung luat Excel: casefold, giu dau cach."""
    counter = Counter(str(v).lower() for v in cells if v not in (None, ""))
    return sum(counter[str(lb).lower()] for lb in labels if lb)


class TestValueNormalization(unittest.TestCase):
    def setUp(self):
        if not os.path.exists(TEMPLATE):
            self.skipTest("khong tim thay template goc")
        self.tmp = tempfile.mkdtemp()

    def _build(self, rows):
        out = os.path.join(self.tmp, "n.xlsx")
        report = builder.build(TEMPLATE, out, rows, phase="Sprint 3",
                               date_from="2026-08-01", date_to="2026-08-31",
                               overwrite=True)
        layout = Layout(len(rows), {"screen": len(report["screens"]),
                                    "milestone": len(report["milestones"]),
                                    "cause": 22, "rootcause": 26})
        return openpyxl.load_workbook(out)[SHEET_NAME], layout, report

    def _read(self, ws, layout, key):
        block = layout.block(key)
        labels = [ws["%s%d" % (block["label_col"], r)].value
                  for r in range(block["first"], block["last"] + 1)]
        cells = [ws["%s%d" % (block["src_col"], r)].value for r in layout.data_rows]
        return labels, cells

    def test_screen_differing_only_by_letter_case_is_counted_once(self):
        # Arrange: G10 / g10 / G10 / M03 -- truoc khi sua: TOTAL = 7 cho 4 bug
        rows = [bug(1, "G10", "Sprint 3"), bug(2, "g10", "Sprint 3"),
                bug(3, "G10", "Sprint 3"), bug(4, "M03", "Sprint 3")]
        # Act
        ws, layout, report = self._build(rows)
        # Assert
        self.assertEqual(report["screens"], ["G10", "M03"])
        labels, cells = self._read(ws, layout, "screen")
        self.assertEqual(countif_total(labels, cells), 4)

    def test_milestone_with_trailing_space_is_still_counted(self):
        # Arrange: "Sprint 3 " -- truoc khi sua Excel dem duoc 3/4
        rows = [bug(1, "G10", "Sprint 3"), bug(2, "G10", "Sprint 3 "),
                bug(3, "G10", " Sprint 3"), bug(4, "M03", "Sprint 3")]
        # Act
        ws, layout, report = self._build(rows)
        # Assert
        self.assertEqual(report["milestones"], ["Sprint 3"])
        labels, cells = self._read(ws, layout, "milestone")
        self.assertEqual(countif_total(labels, cells), 4)
        self.assertTrue(all(v == "Sprint 3" for v in cells if v),
                        "o du lieu con dau cach -> COUNTIF cua Excel se truot")

    def test_catalogue_value_with_stray_space_still_matches_its_row(self):
        # Cause/Root cause la danh muc co dinh -> lech dau cach la truot han,
        # khong co dong nhan nao de gop vao.
        # Arrange
        rows = [bug(1, "G10", "Sprint 3"), bug(2, "G10", "Sprint 3")]
        rows[0]["cause"] = " COD1.2 Coding Logic Mistake "
        rows[1]["root_cause"] = "IMP3 Carelessness "
        # Act
        ws, layout, report = self._build(rows)
        # Assert
        self.assertEqual(report["uncounted"], [])
        for key in ("cause", "rootcause"):
            labels, cells = self._read(ws, layout, key)
            self.assertEqual(countif_total(labels, cells), 2,
                             "bang %s bo sot bug vi lech dau cach" % key)

    def test_every_bug_reaches_all_four_fixed_catalogue_tables(self):
        # Chot lai bat bien: khong bang nao duoc dem thieu hay dem doi.
        # Arrange
        rows = [bug(i, "G1%d" % (i % 3), "Sprint %d" % (i % 2 + 1))
                for i in range(1, 13)]
        # Act
        ws, layout, _ = self._build(rows)
        # Assert
        for key in ("screen", "milestone", "priority", "severity",
                    "cause", "rootcause"):
            labels, cells = self._read(ws, layout, key)
            self.assertEqual(countif_total(labels, cells), 12,
                             "bang %s dem sai" % key)


if __name__ == "__main__":
    unittest.main(verbosity=2)

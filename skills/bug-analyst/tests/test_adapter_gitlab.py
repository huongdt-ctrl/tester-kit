#!/usr/bin/env python3
"""Test GitLab adapter: loc label=bug + khoang ngay, phan trang, bao loi ro."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helpers import FakeResponse

from adapters import TrackerError, build_adapter
from adapters.gitlab_adapter import GitLabAdapter
from adapters.jira_adapter import JiraAdapter
from adapters.redmine_adapter import RedmineAdapter

GITLAB_CFG = {"base_url": "https://gl.test", "token": "t",
              "project_path": "a/b", "page_size": 2}
JIRA_CFG = {"base_url": "https://x.atlassian.net", "email": "e@example.test",
            "api_token": "t", "project_key": "GET", "page_size": 2}
REDMINE_CFG = {"base_url": "https://redmine.test", "api_key": "k",
               "project_id": "prj", "bug_tracker_id": 1, "page_size": 2}


def gitlab_issue(iid, labels=None):
    return {"iid": iid, "title": "[GET-1][G10] loi %s" % iid,
            "web_url": "https://gl.test/-/issues/%s" % iid,
            "labels": labels or ["bug", "priority::High"],
            "milestone": {"title": "Sprint 3"},
            "state": "opened", "created_at": "2026-08-0%dT10:00:00Z" % (iid % 9 + 1)}


class TestGitLabCollect(unittest.TestCase):
    def test_gitlab_filters_by_bug_label_and_created_date_window(self):
        # Arrange
        adapter = GitLabAdapter(dict(GITLAB_CFG))
        captured = {}

        def fake_get(url, headers=None, params=None, timeout=None):
            captured.update(params or {})
            return FakeResponse([])

        # Act
        with mock.patch("adapters.gitlab_adapter.requests.get", fake_get):
            adapter.list_bugs("2026-08-01", "2026-08-31")

        # Assert
        self.assertEqual(captured["labels"], "bug")
        self.assertEqual(captured["state"], "all")
        self.assertEqual(captured["created_after"], "2026-08-01T00:00:00Z")
        self.assertEqual(captured["created_before"], "2026-08-31T23:59:59Z")

    def test_gitlab_paginates_until_short_page_without_dropping_bugs(self):
        # Arrange: 2 trang day + 1 trang le
        pages = [[gitlab_issue(1), gitlab_issue(2)], [gitlab_issue(3), gitlab_issue(4)],
                 [gitlab_issue(5)]]
        adapter = GitLabAdapter(dict(GITLAB_CFG))

        def fake_get(url, headers=None, params=None, timeout=None):
            idx = int(params["page"]) - 1
            return FakeResponse(pages[idx] if idx < len(pages) else [])

        # Act
        with mock.patch("adapters.gitlab_adapter.requests.get", fake_get):
            bugs = adapter.list_bugs("2026-08-01", "2026-08-31")

        # Assert
        self.assertEqual([b["id"] for b in bugs], ["#1", "#2", "#3", "#4", "#5"])
        self.assertEqual(bugs[0]["priority"], "High")
        self.assertEqual(bugs[0]["milestone"], "Sprint 3")

    def test_gitlab_raises_readable_error_on_http_failure(self):
        # Arrange
        adapter = GitLabAdapter(dict(GITLAB_CFG))
        # Act + Assert
        with mock.patch("adapters.gitlab_adapter.requests.get",
                        lambda *a, **k: FakeResponse(None, 403, "forbidden")):
            with self.assertRaises(TrackerError) as ctx:
                adapter.list_bugs("2026-08-01", "2026-08-31")
        self.assertIn("403", str(ctx.exception))

    def test_gitlab_missing_token_stops_before_calling_api(self):
        # Arrange
        cfg = dict(GITLAB_CFG)
        cfg.pop("token")
        adapter = GitLabAdapter(cfg)
        # Act + Assert
        with self.assertRaises(TrackerError) as ctx:
            adapter.list_bugs("2026-08-01", "2026-08-31")
        self.assertIn("token", str(ctx.exception))





class TestGitLabMultiLabel(unittest.TestCase):
    """GitLab loc `labels=a,b` theo AND -> nhieu label phai goi rieng tung cai."""

    def _adapter(self, **extra):
        cfg = dict(GITLAB_CFG)
        cfg.update(extra)
        return GitLabAdapter(cfg)

    def test_gitlab_hai_label_goi_rieng_tung_label_khong_gop_vao_mot_request(self):
        # Arrange
        adapter = self._adapter(bug_labels=["bug", "Egg"])
        goi = []

        def fake_get(url, headers=None, params=None, timeout=None):
            goi.append(params["labels"])
            return FakeResponse([])

        # Act
        with mock.patch("adapters.gitlab_adapter.requests.get", fake_get):
            adapter.list_bugs("2026-08-01", "2026-08-31")

        # Assert: 2 request rieng, KHONG phai mot request "bug,Egg" (= AND)
        self.assertEqual(goi, ["bug", "Egg"])

    def test_gitlab_issue_mang_ca_hai_label_chi_duoc_dem_mot_lan(self):
        # Arrange: #2 dinh ca 'bug' lan 'Egg' -> ve o ca hai vong
        theo_label = {
            "bug": [[gitlab_issue(1), gitlab_issue(2, ["bug", "Egg"])]],
            "Egg": [[gitlab_issue(2, ["bug", "Egg"]), gitlab_issue(3, ["Egg"])]],
        }
        adapter = self._adapter(bug_labels=["bug", "Egg"], page_size=5)

        def fake_get(url, headers=None, params=None, timeout=None):
            pages = theo_label[params["labels"]]
            idx = int(params["page"]) - 1
            return FakeResponse(pages[idx] if idx < len(pages) else [])

        # Act
        with mock.patch("adapters.gitlab_adapter.requests.get", fake_get):
            bugs = adapter.list_bugs("2026-08-01", "2026-08-31")

        # Assert: gop du 3 bug, #2 khong bi dem doi, sap xep theo created_at
        self.assertEqual([b["id"] for b in bugs], ["#1", "#2", "#3"])

    def test_gitlab_bug_labels_dang_chuoi_phan_cach_bang_dau_phay_van_tach_dung(self):
        # Arrange
        adapter = self._adapter(bug_labels="bug, Egg ,")
        # Act + Assert
        self.assertEqual(adapter.bug_labels(), ["bug", "Egg"])

    def test_gitlab_khong_khai_bug_labels_thi_dung_key_cu_bug_label(self):
        # Arrange: profile cu chi co bug_label -> khong duoc vo
        adapter = self._adapter(bug_label="defect")
        # Act + Assert
        self.assertEqual(adapter.bug_labels(), ["defect"])

    def test_gitlab_bug_labels_rong_ve_mac_dinh_bug_chu_khong_lay_het_issue(self):
        # Arrange: list rong -> khong loc gi = keo ve toan bo issue project
        adapter = self._adapter(bug_labels=[])
        # Act + Assert
        self.assertEqual(adapter.bug_labels(), ["bug"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

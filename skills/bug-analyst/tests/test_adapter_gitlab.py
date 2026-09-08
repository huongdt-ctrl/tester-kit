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


def gitlab_issue(iid):
    return {"iid": iid, "title": "[GET-1][G10] loi %s" % iid,
            "web_url": "https://gl.test/-/issues/%s" % iid,
            "labels": ["bug", "priority::High"], "milestone": {"title": "Sprint 3"},
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



if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Test Jira/Redmine adapter + factory: loc dung loai bug, phan trang, tra tracker_id."""
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


class TestJiraCollect(unittest.TestCase):
    def test_jira_builds_jql_with_bug_issuetype_and_date_bounds(self):
        # Arrange
        adapter = JiraAdapter(dict(JIRA_CFG))
        # Act
        jql = adapter._jql("2026-08-01", "2026-08-31")
        # Assert
        self.assertIn('issuetype = "Bug"', jql)
        self.assertIn('created >= "2026-08-01"', jql)
        self.assertIn('created <= "2026-08-31 23:59"', jql)

    def test_jira_paginates_using_total_and_normalizes_fields(self):
        # Arrange
        def issue(key):
            return {"key": key, "fields": {"summary": "[GET-1][M03] loi %s" % key,
                                           "priority": {"name": "Highest"},
                                           "status": {"name": "Open"},
                                           "labels": ["ui"],
                                           "fixVersions": [{"name": "Sprint 3"}],
                                           "created": "2026-08-05T10:00:00.000+0700"}}
        batches = [{"issues": [issue("GET-1"), issue("GET-2")], "total": 3},
                   {"issues": [issue("GET-3")], "total": 3}]
        calls = {"n": 0}
        adapter = JiraAdapter(dict(JIRA_CFG))

        def fake_get(url, auth=None, params=None, headers=None, timeout=None):
            payload = batches[calls["n"]]
            calls["n"] += 1
            return FakeResponse(payload)

        # Act
        with mock.patch("adapters.jira_adapter.requests.get", fake_get):
            bugs = adapter.list_bugs("2026-08-01", "2026-08-31")

        # Assert
        self.assertEqual([b["id"] for b in bugs], ["GET-1", "GET-2", "GET-3"])
        self.assertEqual(bugs[0]["priority"], "Highest")
        self.assertEqual(bugs[0]["milestone"], "Sprint 3")

class TestRedmineCollect(unittest.TestCase):
    def test_redmine_filters_by_tracker_id_and_created_on_range(self):
        # Arrange
        adapter = RedmineAdapter(dict(REDMINE_CFG))
        captured = {}

        def fake_get(url, headers=None, params=None, timeout=None):
            captured.update(params or {})
            return FakeResponse({"issues": [], "total_count": 0})

        # Act
        with mock.patch("adapters.redmine_adapter.requests.get", fake_get):
            adapter.list_bugs("2026-08-01", "2026-08-31")

        # Assert
        self.assertEqual(captured["tracker_id"], 1)
        self.assertEqual(captured["status_id"], "*")
        self.assertEqual(captured["created_on"], "><2026-08-01|2026-08-31")

    def test_redmine_resolves_tracker_id_from_name_when_not_configured(self):
        # Arrange
        cfg = dict(REDMINE_CFG)
        cfg.pop("bug_tracker_id")
        cfg["bug_tracker_name"] = "Bug"
        adapter = RedmineAdapter(cfg)
        captured = {}

        def fake_get(url, headers=None, params=None, timeout=None):
            if url.endswith("/trackers.json"):
                return FakeResponse({"trackers": [{"id": 7, "name": "Bug"},
                                                  {"id": 2, "name": "Feature"}]})
            captured.update(params or {})
            return FakeResponse({"issues": [], "total_count": 0})

        # Act
        with mock.patch("adapters.redmine_adapter.requests.get", fake_get):
            adapter.list_bugs("2026-08-01", "2026-08-31")

        # Assert -- ten tracker "Bug" phai duoc tra thanh id 7 va dung de loc
        self.assertEqual(captured["tracker_id"], 7)

    def test_redmine_unknown_tracker_name_fails_loudly(self):
        # Arrange
        cfg = dict(REDMINE_CFG)
        cfg.pop("bug_tracker_id")
        cfg["bug_tracker_name"] = "Khiem khuyet"
        adapter = RedmineAdapter(cfg)
        # Act + Assert
        with mock.patch("adapters.redmine_adapter.requests.get",
                        lambda *a, **k: FakeResponse({"trackers": [{"id": 1, "name": "Bug"}]})):
            with self.assertRaises(TrackerError):
                adapter.list_bugs("2026-08-01", "2026-08-31")

class TestFactory(unittest.TestCase):
    def test_factory_returns_adapter_matching_configured_system(self):
        # Arrange + Act + Assert
        for system, klass in (("gitlab", GitLabAdapter), ("jira", JiraAdapter),
                              ("redmine", RedmineAdapter)):
            adapter = build_adapter({"tracker": {"system": system}})
            self.assertIsInstance(adapter, klass)

    def test_factory_rejects_unsupported_tracker_with_supported_list(self):
        # Arrange + Act + Assert
        with self.assertRaises(TrackerError) as ctx:
            build_adapter({"tracker": {"system": "trello"}})
        self.assertIn("gitlab", str(ctx.exception))



if __name__ == "__main__":
    unittest.main(verbosity=2)

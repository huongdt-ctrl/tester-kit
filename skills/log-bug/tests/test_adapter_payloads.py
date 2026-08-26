#!/usr/bin/env python3
"""Kiem payload gui len tung tracker, bang cach mock requests (test-standards:
mock external dependency -- test phai nhanh va deterministic, khong goi mang)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from adapters import TrackerError, build_adapter  # noqa: E402
from adapters import gitlab_adapter, jira_adapter, redmine_adapter  # noqa: E402


class _Resp:
    def __init__(self, status, payload=None, text=""):
        self.status_code = status
        self._payload = payload if payload is not None else {}
        self.text = text or json.dumps(self._payload)

    def json(self):
        return self._payload


class _Recorder:
    """Ghi lai lan goi HTTP cuoi cung de assert, thay vi goi that."""

    def __init__(self, response):
        self.response = response
        self.calls = []

    def __call__(self, url, **kwargs):
        self.calls.append(dict(kwargs, url=url))
        return self.response

    @property
    def last(self):
        return self.calls[-1]


FIELDS = {"priority": "High", "assignee": 42, "start_date": "2026-08-25",
          "due_date": "2026-08-28", "status": 1, "tracker": "Bug",
          "parent_ticket": "1200", "labels": ["qa", "bug ui"],
          "severity": "Major", "scope": "Frontend"}


# --- Redmine ---

def test_redmine_create_issue_sends_expected_payload_and_returns_url(monkeypatch):
    rec = _Recorder(_Resp(201, {"issue": {"id": 777}}))
    monkeypatch.setattr(redmine_adapter.requests, "post", rec)
    adapter = build_adapter({"tracker": {"system": "redmine", "base_url": "https://rm.test/",
                                         "api_key": "k", "project_id": "demo"}})
    issue_id, url = adapter.create_issue("tieu de", "mo ta", FIELDS)

    assert (issue_id, url) == (777, "https://rm.test/issues/777")
    body = json.loads(rec.last["data"])["issue"]
    assert body["project_id"] == "demo"
    assert body["subject"] == "tieu de"
    assert body["start_date"] == "2026-08-25"      # Redmine nhan native
    assert body["assigned_to_id"] == 42
    assert body["parent_issue_id"] == "1200"
    assert rec.last["url"] == "https://rm.test/issues.json"
    # Severity/Scope KHONG duoc gui len như field -> nam trong description
    assert "severity" not in body and "scope" not in body


def test_redmine_create_issue_http_error_raises_tracker_error(monkeypatch):
    monkeypatch.setattr(redmine_adapter.requests, "post",
                        _Recorder(_Resp(422, {}, "validation failed")))
    adapter = build_adapter({"tracker": {"system": "redmine", "base_url": "https://rm.test",
                                         "api_key": "k", "project_id": "demo"}})
    try:
        adapter.create_issue("t", "d", {})
    except TrackerError as exc:
        assert "422" in str(exc)
    else:
        raise AssertionError("phai raise TrackerError")


def test_redmine_create_issue_missing_config_raises_before_any_http(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("khong duoc goi HTTP khi thieu cau hinh")
    monkeypatch.setattr(redmine_adapter.requests, "post", _boom)
    adapter = build_adapter({"tracker": {"system": "redmine", "base_url": "https://rm.test"}})
    try:
        adapter.create_issue("t", "d", {})
    except TrackerError as exc:
        assert "api_key" in str(exc)
    else:
        raise AssertionError("phai raise TrackerError")


def test_redmine_search_returns_normalised_hits(monkeypatch):
    payload = {"issues": [{"id": 5, "subject": "loi A", "status": {"name": "Closed"}},
                          {"id": 6, "subject": "loi B", "status": {"name": "New"}}]}
    monkeypatch.setattr(redmine_adapter.requests, "get", _Recorder(_Resp(200, payload)))
    adapter = build_adapter({"tracker": {"system": "redmine", "base_url": "https://rm.test",
                                         "api_key": "k", "project_id": "demo"}})
    hits = adapter.search_issues("loi")
    assert [h["closed"] for h in hits] == [True, False]
    assert hits[0]["url"] == "https://rm.test/issues/5"


def test_redmine_search_network_error_returns_empty_not_raise(monkeypatch):
    def _raise(*a, **k):
        raise redmine_adapter.requests.RequestException("mat mang")
    monkeypatch.setattr(redmine_adapter.requests, "get", _raise)
    adapter = build_adapter({"tracker": {"system": "redmine", "base_url": "https://rm.test",
                                         "api_key": "k", "project_id": "demo"}})
    assert adapter.search_issues("x") == []


# --- GitLab ---

def test_gitlab_create_issue_url_encodes_project_path(monkeypatch):
    rec = _Recorder(_Resp(201, {"iid": 12, "web_url": "https://gl.test/x/-/issues/12"}))
    monkeypatch.setattr(gitlab_adapter.requests, "post", rec)
    adapter = build_adapter({"tracker": {"system": "gitlab", "base_url": "https://gl.test",
                                         "token": "t", "project_path": "grp/sub/proj"}})
    issue_id, url = adapter.create_issue("tieu de", "mo ta", FIELDS)

    assert (issue_id, url) == (12, "https://gl.test/x/-/issues/12")
    assert "grp%2Fsub%2Fproj" in rec.last["url"]
    body = rec.last["data"]
    assert body["due_date"] == "2026-08-28"
    assert body["labels"] == "qa,bug ui"          # list -> chuoi phay
    assert body["assignee_ids"] == [42]
    assert "start_date" not in body               # GitLab issue khong co start_date


def test_gitlab_non_numeric_assignee_raises_actionable_error(monkeypatch):
    monkeypatch.setattr(gitlab_adapter.requests, "post",
                        _Recorder(_Resp(201, {"iid": 1})))
    adapter = build_adapter({"tracker": {"system": "gitlab", "base_url": "https://gl.test",
                                         "token": "t", "project_path": "a/b"}})
    try:
        adapter.create_issue("t", "d", {"assignee": "nguyenvana"})
    except TrackerError as exc:
        assert "user ID dang so" in str(exc)
    else:
        raise AssertionError("phai raise TrackerError")


def test_gitlab_search_maps_state_to_closed_flag(monkeypatch):
    payload = [{"iid": 1, "title": "a", "state": "closed", "web_url": "u1"},
               {"iid": 2, "title": "b", "state": "opened", "web_url": "u2"}]
    monkeypatch.setattr(gitlab_adapter.requests, "get", _Recorder(_Resp(200, payload)))
    adapter = build_adapter({"tracker": {"system": "gitlab", "base_url": "https://gl.test",
                                         "token": "t", "project_path": "a/b"}})
    assert [h["closed"] for h in adapter.search_issues("x")] == [True, False]


# --- Jira ---

def test_jira_create_issue_uses_api_v2_and_string_description(monkeypatch):
    rec = _Recorder(_Resp(201, {"key": "GET-9"}))
    monkeypatch.setattr(jira_adapter.requests, "post", rec)
    adapter = build_adapter({"tracker": {"system": "jira", "base_url": "https://x.atlassian.net",
                                         "email": "qa@nal.vn", "api_token": "t",
                                         "project_key": "GET"}})
    issue_id, url = adapter.create_issue("tieu de", "mo ta", FIELDS)

    assert (issue_id, url) == ("GET-9", "https://x.atlassian.net/browse/GET-9")
    assert rec.last["url"].endswith("/rest/api/2/issue")   # v2, khong phai v3
    body = json.loads(rec.last["data"])["fields"]
    assert body["description"] == "mo ta"      # string thuan, khong phai ADF
    assert body["project"] == {"key": "GET"}
    assert body["issuetype"] == {"name": "Bug"}
    assert body["priority"] == {"name": "High"}
    assert body["duedate"] == "2026-08-28"
    assert body["parent"] == {"key": "1200"}
    assert body["labels"] == ["qa", "bug-ui"]  # khoang trang -> '-'
    assert body["assignee"] == {"accountId": "42"}


def test_jira_assignee_field_switchable_for_server_edition(monkeypatch):
    rec = _Recorder(_Resp(201, {"key": "GET-1"}))
    monkeypatch.setattr(jira_adapter.requests, "post", rec)
    adapter = build_adapter({"tracker": {"system": "jira", "base_url": "https://jira.local",
                                         "email": "a@b.c", "api_token": "t",
                                         "project_key": "GET", "assignee_field": "name"}})
    adapter.create_issue("t", "d", {"assignee": "nguyenvana"})
    body = json.loads(rec.last["data"])["fields"]
    assert body["assignee"] == {"name": "nguyenvana"}


def test_jira_search_escapes_quotes_in_jql(monkeypatch):
    rec = _Recorder(_Resp(200, {"issues": []}))
    monkeypatch.setattr(jira_adapter.requests, "get", rec)
    adapter = build_adapter({"tracker": {"system": "jira", "base_url": "https://x.test",
                                         "email": "a@b.c", "api_token": "t",
                                         "project_key": "GET"}})
    adapter.search_issues('loi "nghiem trong"')
    assert '\\"nghiem trong\\"' in rec.last["params"]["jql"]


def test_jira_uses_basic_auth_header_not_url_credential(monkeypatch):
    rec = _Recorder(_Resp(201, {"key": "GET-1"}))
    monkeypatch.setattr(jira_adapter.requests, "post", rec)
    adapter = build_adapter({"tracker": {"system": "jira", "base_url": "https://x.test",
                                         "email": "qa@nal.vn", "api_token": "secret",
                                         "project_key": "GET"}})
    adapter.create_issue("t", "d", {})
    assert rec.last["headers"]["Authorization"].startswith("Basic ")
    # credential khong duoc lot vao URL (se bi log lai o proxy/server)
    assert "secret" not in rec.last["url"]

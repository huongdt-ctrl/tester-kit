#!/usr/bin/env python3
"""Preflight tu bat cau hinh tracker sai TRUOC khi tao bug that.

Muc dich: project_path go nham hay priority_map dung ten khong co tren tracker
truoc day chi lo ra luc dang tao bug (HTTP 400/404 giua chung, sau khi vai ticket
that da duoc tao). Cac test nay khoa lai hanh vi "biet truoc, khi chua tao gi".
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import preflight_checks  # noqa: E402
from adapters import build_adapter  # noqa: E402
from adapters import gitlab_adapter, jira_adapter, redmine_adapter  # noqa: E402


class _Resp:
    def __init__(self, status, payload=None):
        self.status_code = status
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


def _redmine(cfg=None):
    base = {"system": "redmine", "base_url": "https://rm.test",
            "api_key": "k", "project_id": "demo"}
    base.update(cfg or {})
    return build_adapter({"tracker": base})


def _gitlab():
    return build_adapter({"tracker": {"system": "gitlab", "base_url": "https://gl.test",
                                      "token": "t", "project_path": "grp/sub/proj"}})


def _jira():
    return build_adapter({"tracker": {"system": "jira", "base_url": "https://x.test",
                                      "email": "a@b.c", "api_token": "t",
                                      "project_key": "GET"}})


# --- verify_project ---

def test_project_exists_reports_ok_with_project_name(monkeypatch):
    monkeypatch.setattr(redmine_adapter.requests, "get",
                        lambda *a, **k: _Resp(200, {"project": {"name": "Acme"}}))
    out = preflight_checks.check_project(_redmine())
    assert out["ok"] is True
    assert "Acme" in out["detail"]


def test_project_not_found_is_blocking_and_names_the_bad_value(monkeypatch):
    monkeypatch.setattr(redmine_adapter.requests, "get", lambda *a, **k: _Resp(404))
    out = preflight_checks.check_project(_redmine({"project_id": "go-nham"}))
    assert out["ok"] is False
    assert "go-nham" in out["detail"]
    assert preflight_checks.blocking_reasons({"project": out})


def test_project_forbidden_is_blocking_and_blames_the_token(monkeypatch):
    monkeypatch.setattr(gitlab_adapter.requests, "get", lambda *a, **k: _Resp(403))
    out = preflight_checks.check_project(_gitlab())
    assert out["ok"] is False
    assert "token" in out["detail"]


def test_project_network_error_is_warning_not_blocking(monkeypatch):
    def _raise(*a, **k):
        raise gitlab_adapter.requests.RequestException("mat mang")
    monkeypatch.setattr(gitlab_adapter.requests, "get", _raise)
    out = preflight_checks.check_project(_gitlab())
    assert out["ok"] is None            # khong chac -> khong chan
    assert preflight_checks.blocking_reasons({"project": out}) == []


def test_jira_project_key_not_found_is_blocking(monkeypatch):
    monkeypatch.setattr(jira_adapter.requests, "get", lambda *a, **k: _Resp(404))
    out = preflight_checks.check_project(_jira())
    assert out["ok"] is False
    assert "GET" in out["detail"]


# --- priority_map ---

REDMINE_PRIORITIES = {"issue_priorities": [{"name": "Low"}, {"name": "Normal"},
                                           {"name": "High"}, {"name": "Urgent"}]}


def test_priority_map_matching_tracker_is_ok(monkeypatch):
    monkeypatch.setattr(redmine_adapter.requests, "get",
                        lambda *a, **k: _Resp(200, REDMINE_PRIORITIES))
    out = preflight_checks.check_priority_map(
        _redmine(), {"priority_map": {"High": "High", "Medium": "Normal", "Low": "Low"}})
    assert out["ok"] is True


def test_priority_map_with_unknown_value_is_blocking_and_lists_valid_ones(monkeypatch):
    """Day la cai gay HTTP 400 luc tao bug neu khong bat o preflight."""
    monkeypatch.setattr(redmine_adapter.requests, "get",
                        lambda *a, **k: _Resp(200, REDMINE_PRIORITIES))
    out = preflight_checks.check_priority_map(
        _redmine(), {"priority_map": {"Medium": "Binh thuong"}})
    assert out["ok"] is False
    assert "Binh thuong" in out["detail"]
    assert "Normal" in out["detail"]     # goi y gia tri dung
    assert preflight_checks.blocking_reasons({"priority_map": out})


def test_priority_map_unreadable_list_is_warning_not_blocking(monkeypatch):
    monkeypatch.setattr(redmine_adapter.requests, "get", lambda *a, **k: _Resp(500))
    out = preflight_checks.check_priority_map(
        _redmine(), {"priority_map": {"High": "High"}})
    assert out["ok"] is None
    assert preflight_checks.blocking_reasons({"priority_map": out}) == []


def test_priority_map_skipped_on_gitlab_which_has_no_priority():
    out = preflight_checks.check_priority_map(_gitlab(), {"priority_map": {"High": "X"}})
    assert out["ok"] is None
    assert "gitlab" in out["detail"]


def test_priority_map_absent_is_not_an_error():
    out = preflight_checks.check_priority_map(_gitlab(), {})
    assert out["ok"] is None
    assert preflight_checks.blocking_reasons({"priority_map": out}) == []


def test_jira_priority_list_parsed_from_flat_array(monkeypatch):
    monkeypatch.setattr(jira_adapter.requests, "get",
                        lambda *a, **k: _Resp(200, [{"name": "Highest"}, {"name": "Low"}]))
    out = preflight_checks.check_priority_map(_jira(), {"priority_map": {"High": "Highest"}})
    assert out["ok"] is True


def test_check_project_never_raises_even_if_adapter_explodes():
    """Preflight khong duoc chet -- no la buoc chan loi, khong phai buoc gay loi."""
    class _Boom:
        name = "boom"

        def verify_project(self):
            raise RuntimeError("hong")

    out = preflight_checks.check_project(_Boom())
    assert out["ok"] is None
    assert "hong" in out["detail"]


def test_blocking_reasons_only_counts_explicit_false():
    checks = {"a": {"ok": True, "detail": "x"}, "b": {"ok": None, "detail": "y"},
              "c": {"ok": False, "detail": "z"}}
    reasons = preflight_checks.blocking_reasons(checks)
    assert len(reasons) == 1
    assert "c: z" in reasons[0]

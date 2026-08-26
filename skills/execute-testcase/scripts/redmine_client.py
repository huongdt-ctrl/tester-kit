#!/usr/bin/env python3
"""
Create Redmine bugs for genuine Fail cases -- and, more importantly, refuse to
create the ones that must not exist.

Two guards, both from the review:

  1. should_create_bug() -- only status Fail qualifies. Environment/permission/
     missing-data blockers are Pending and never become application bugs. This
     is the rule that keeps the tracker trustworthy.

  2. resolve_duplicate() -- a rerun of a still-failing case must NOT open a
     second ticket. When the row already carries a Bug ID, the issue's current
     state decides: open -> reuse, closed -> new ticket marked as a regression
     of the old one.

Network calls live in _get/_post only, so decide_* logic is unit-testable
without a server.
"""
import json

import requests

CLOSED_STATUS_NAMES = ("closed", "rejected", "resolved", "done", "won't fix", "wontfix", "duplicate")


class RedmineError(Exception):
    pass


def _headers(api_key):
    return {"X-Redmine-API-Key": api_key, "Content-Type": "application/json"}


def should_create_bug(status, merged):
    """True only for a status the config marks as bug-worthy."""
    policy = (merged.get("redmine_policy") or {})
    create_when = policy.get("create_bug_when_status_is") or ["Fail"]
    never_when = policy.get("never_create_bug_when_status_is") or ["Pending", "Untested", "N/A"]
    s = str(status or "").strip()
    if s in never_when:
        return False
    return s in create_when


def is_closed(status_name):
    return str(status_name or "").strip().lower() in CLOSED_STATUS_NAMES


def decide_duplicate_action(existing_bug_id, issue_status_name):
    """Pure decision so it can be tested without Redmine.

    Returns one of: "create_new" (no prior bug), "reuse_open" (prior bug still
    open -> do not create), "create_regression" (prior bug closed)."""
    if not str(existing_bug_id or "").strip():
        return "create_new"
    if issue_status_name is None:
        # Bug ID present but unreadable -> treat as open. Better a missing
        # duplicate than a duplicate flood.
        return "reuse_open"
    return "create_regression" if is_closed(issue_status_name) else "reuse_open"


def build_bug_title(pattern, module_name, tc_id, short_summary):
    pattern = pattern or "[TEST][{module_name}][{tc_id}] {short_summary}"
    return pattern.format(module_name=module_name, tc_id=tc_id, short_summary=short_summary)


def build_bug_description(fields, regression_of=None):
    """fields: ordered dict-like of section title -> text."""
    lines = []
    if regression_of:
        lines.append("Regression cua %s" % regression_of)
        lines.append("")
    for section, value in fields.items():
        lines.append("h3. %s" % section)
        lines.append(str(value if value not in (None, "") else "-"))
        lines.append("")
    return "\n".join(lines).strip()


def get_issue_status(base_url, api_key, issue_id, timeout=30):
    """Status name of an existing issue, or None when unreadable."""
    url = "%s/issues/%s.json" % (str(base_url).rstrip("/"), str(issue_id).strip())
    try:
        r = requests.get(url, headers=_headers(api_key), timeout=timeout)
        if r.status_code != 200:
            return None
        return (((r.json() or {}).get("issue") or {}).get("status") or {}).get("name")
    except (requests.RequestException, ValueError):
        return None


def create_issue(base_url, api_key, project_id, subject, description,
                 tracker_id=None, status_id=None, priority_id=None,
                 assigned_to_id=None, category_id=None, timeout=30):
    """Returns (issue_id, issue_url)."""
    payload = {"issue": {"project_id": project_id, "subject": subject, "description": description}}
    for key, val in (("tracker_id", tracker_id), ("status_id", status_id),
                     ("priority_id", priority_id), ("assigned_to_id", assigned_to_id),
                     ("category_id", category_id)):
        if val not in (None, ""):
            payload["issue"][key] = val

    url = "%s/issues.json" % str(base_url).rstrip("/")
    r = requests.post(url, headers=_headers(api_key), data=json.dumps(payload), timeout=timeout)
    if r.status_code not in (200, 201):
        raise RedmineError("Tao bug that bai: HTTP %s -- %s" % (r.status_code, r.text[:300]))
    issue = (r.json() or {}).get("issue") or {}
    issue_id = issue.get("id")
    if not issue_id:
        raise RedmineError("Redmine tra ve response khong co issue id: %s" % r.text[:300])
    return issue_id, "%s/issues/%s" % (str(base_url).rstrip("/"), issue_id)


def redmine_settings(merged):
    """Pull + validate the Redmine block. api_key is already resolved from env
    by config_loader, so a literal 'env:' here means resolution was skipped."""
    rm = (merged.get("redmine") or {})
    if not rm.get("enabled", False):
        return None
    missing = [f for f in ("base_url", "api_key", "project_id") if not rm.get(f)]
    if missing:
        raise RedmineError("Thieu cau hinh Redmine: %s" % ", ".join(missing))
    if str(rm.get("api_key")).startswith("env:"):
        raise RedmineError("redmine.api_key chua duoc resolve tu environment variable.")
    return rm

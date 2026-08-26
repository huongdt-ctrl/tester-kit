#!/usr/bin/env python3
"""Redmine adapter -- REST API /issues.json, auth bang X-Redmine-API-Key.

Redmine la tracker DUY NHAT trong ba cai nhan native ca start_date lan due_date,
nen o day supports rong nhat.
"""
import json

import requests

from .base_adapter import BaseAdapter, TrackerError

REQUIRED = ("base_url", "api_key", "project_id")


class RedmineAdapter(BaseAdapter):
    name = "redmine"
    markup = "textile"          # Redmine dung textile -> heading la "h3. "
    supports = frozenset({"priority", "assignee", "start_date", "due_date",
                          "tracker", "status", "parent_ticket"})
    required = REQUIRED

    def _headers(self):
        return {"X-Redmine-API-Key": self.cfg.get("api_key"),
                "Content-Type": "application/json"}

    def _timeout(self):
        return int(self.cfg.get("timeout_seconds") or 30)

    def create_issue(self, title, description, fields):
        miss = self.missing_config(REQUIRED)
        if miss:
            raise TrackerError("Redmine thieu cau hinh: %s" % ", ".join(miss))

        issue = {"project_id": self.cfg.get("project_id"),
                 "subject": title, "description": description}
        # Map field canonical -> ten field Redmine. id lay tu config vi Redmine
        # nhan id chu khong nhan ten cho tracker/priority/status.
        mapping = (("tracker", "tracker_id"), ("status", "status_id"),
                   ("priority", "priority_id"), ("assignee", "assigned_to_id"),
                   ("parent_ticket", "parent_issue_id"))
        for canon, rm_key in mapping:
            val = fields.get(canon)
            if val not in (None, ""):
                issue[rm_key] = val
        for key in ("start_date", "due_date"):
            if fields.get(key):
                issue[key] = fields[key]

        url = "%s/issues.json" % self.base_url
        try:
            resp = requests.post(url, headers=self._headers(),
                                 data=json.dumps({"issue": issue}),
                                 timeout=self._timeout())
        except requests.RequestException as exc:
            raise TrackerError("Redmine khong ket noi duoc: %s" % exc)
        if resp.status_code not in (200, 201):
            raise TrackerError("Redmine tao bug that bai: HTTP %s -- %s"
                               % (resp.status_code, resp.text[:300]))
        created = (resp.json() or {}).get("issue") or {}
        issue_id = created.get("id")
        if not issue_id:
            raise TrackerError("Redmine tra ve response khong co issue id: %s"
                               % resp.text[:300])
        return issue_id, "%s/issues/%s" % (self.base_url, issue_id)

    def get_issue_status(self, issue_id):
        url = "%s/issues/%s.json" % (self.base_url, str(issue_id).strip())
        try:
            resp = requests.get(url, headers=self._headers(), timeout=self._timeout())
            if resp.status_code != 200:
                return None
            issue = (resp.json() or {}).get("issue") or {}
            return (issue.get("status") or {}).get("name")
        except (requests.RequestException, ValueError):
            return None

    def verify_project(self):
        url = "%s/projects/%s.json" % (self.base_url, self.cfg.get("project_id"))
        try:
            resp = requests.get(url, headers=self._headers(), timeout=self._timeout())
        except requests.RequestException as exc:
            return {"ok": None, "detail": "khong ket noi duoc: %s" % exc}
        if resp.status_code == 200:
            name = (((resp.json() or {}).get("project") or {}).get("name"))
            return {"ok": True, "detail": "project_id %r -> %r"
                                          % (self.cfg.get("project_id"), name)}
        if resp.status_code in (401, 403):
            return {"ok": False, "detail": "api_key khong co quyen doc project %r "
                                           "(HTTP %s)" % (self.cfg.get("project_id"),
                                                          resp.status_code)}
        if resp.status_code == 404:
            return {"ok": False, "detail": "project_id %r khong ton tai tren %s"
                                           % (self.cfg.get("project_id"), self.base_url)}
        return {"ok": None, "detail": "HTTP %s" % resp.status_code}

    def list_priorities(self):
        try:
            resp = requests.get("%s/enumerations/issue_priorities.json" % self.base_url,
                                headers=self._headers(), timeout=self._timeout())
            if resp.status_code != 200:
                return None
            return [p.get("name") for p in
                    ((resp.json() or {}).get("issue_priorities") or [])]
        except (requests.RequestException, ValueError):
            return None

    def search_issues(self, text, limit=20):
        # subject=~text la cu phap "contains" cua Redmine; status_id=* de lay
        # ca issue da dong (can biet closed de quyet dinh regression).
        params = {"project_id": self.cfg.get("project_id"), "status_id": "*",
                  "subject": "~%s" % text, "limit": limit}
        try:
            resp = requests.get("%s/issues.json" % self.base_url,
                                headers=self._headers(), params=params,
                                timeout=self._timeout())
            if resp.status_code != 200:
                return []
            issues = (resp.json() or {}).get("issues") or []
        except (requests.RequestException, ValueError):
            return []
        out = []
        for it in issues:
            status = (it.get("status") or {}).get("name")
            out.append({"id": it.get("id"), "title": it.get("subject"),
                        "url": "%s/issues/%s" % (self.base_url, it.get("id")),
                        "status": status, "closed": self.is_closed(status)})
        return out

#!/usr/bin/env python3
"""Jira adapter -- REST API v2, auth Basic (email + api_token).

QUYET DINH CO CHU Y: dung /rest/api/2/ chu KHONG dung /rest/api/3/.
Ly do: v3 bat description phai la ADF (Atlassian Document Format) -- mot cay
JSON long nhau, khong the dung chung bo render text voi Redmine/GitLab. v2 nhan
description la string wiki-markup thuan, van con duoc support tren Jira Cloud.
Doi sang v3 = phai viet rieng bo serialize ADF.
"""
import base64
import json

import requests

from .base_adapter import BaseAdapter, TrackerError

REQUIRED = ("base_url", "email", "api_token", "project_key")


class JiraAdapter(BaseAdapter):
    name = "jira"
    markup = "textile"     # wiki markup cua Jira cung dung "h3. "
    supports = frozenset({"priority", "assignee", "due_date", "labels",
                          "tracker", "parent_ticket"})
    required = REQUIRED

    def _headers(self):
        raw = "%s:%s" % (self.cfg.get("email"), self.cfg.get("api_token"))
        token = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        return {"Authorization": "Basic %s" % token,
                "Content-Type": "application/json", "Accept": "application/json"}

    def _timeout(self):
        return int(self.cfg.get("timeout_seconds") or 30)

    def create_issue(self, title, description, fields):
        miss = self.missing_config(REQUIRED)
        if miss:
            raise TrackerError("Jira thieu cau hinh: %s" % ", ".join(miss))

        jf = {"project": {"key": self.cfg.get("project_key")},
              "summary": title, "description": description,
              "issuetype": {"name": fields.get("tracker") or "Bug"}}
        if fields.get("priority"):
            jf["priority"] = {"name": str(fields["priority"])}
        if fields.get("due_date"):
            jf["duedate"] = fields["due_date"]
        if fields.get("labels"):
            labels = fields["labels"]
            # Jira label khong cho phep khoang trang -> thay bang '-'.
            jf["labels"] = [str(x).replace(" ", "-")
                            for x in (labels if isinstance(labels, list) else [labels])]
        if fields.get("assignee") not in (None, ""):
            # Jira Cloud dung accountId; Server/DC dung name. Config chon kieu.
            key = "accountId" if self.cfg.get("assignee_field", "accountId") == "accountId" else "name"
            jf["assignee"] = {key: str(fields["assignee"])}
        if fields.get("parent_ticket"):
            jf["parent"] = {"key": str(fields["parent_ticket"])}

        try:
            resp = requests.post("%s/rest/api/2/issue" % self.base_url,
                                 headers=self._headers(),
                                 data=json.dumps({"fields": jf}),
                                 timeout=self._timeout())
        except requests.RequestException as exc:
            raise TrackerError("Jira khong ket noi duoc: %s" % exc)
        if resp.status_code not in (200, 201):
            raise TrackerError("Jira tao bug that bai: HTTP %s -- %s"
                               % (resp.status_code, resp.text[:300]))
        issue = resp.json() or {}
        key = issue.get("key")
        if not key:
            raise TrackerError("Jira tra ve response khong co issue key: %s"
                               % resp.text[:300])
        return key, "%s/browse/%s" % (self.base_url, key)

    def get_issue_status(self, issue_id):
        url = "%s/rest/api/2/issue/%s" % (self.base_url, str(issue_id).strip())
        try:
            resp = requests.get(url, headers=self._headers(),
                                params={"fields": "status"}, timeout=self._timeout())
            if resp.status_code != 200:
                return None
            fields = (resp.json() or {}).get("fields") or {}
            return (fields.get("status") or {}).get("name")
        except (requests.RequestException, ValueError):
            return None

    def verify_project(self):
        url = "%s/rest/api/2/project/%s" % (self.base_url, self.cfg.get("project_key"))
        try:
            resp = requests.get(url, headers=self._headers(), timeout=self._timeout())
        except requests.RequestException as exc:
            return {"ok": None, "detail": "khong ket noi duoc: %s" % exc}
        if resp.status_code == 200:
            return {"ok": True, "detail": "project_key %r -> %r"
                    % (self.cfg.get("project_key"), (resp.json() or {}).get("name"))}
        if resp.status_code in (401, 403):
            return {"ok": False, "detail": "api_token khong co quyen doc project %r "
                                           "(HTTP %s)" % (self.cfg.get("project_key"),
                                                          resp.status_code)}
        if resp.status_code == 404:
            return {"ok": False, "detail": "project_key %r khong ton tai tren %s"
                    % (self.cfg.get("project_key"), self.base_url)}
        return {"ok": None, "detail": "HTTP %s" % resp.status_code}

    def list_priorities(self):
        try:
            resp = requests.get("%s/rest/api/2/priority" % self.base_url,
                                headers=self._headers(), timeout=self._timeout())
            if resp.status_code != 200:
                return None
            return [p.get("name") for p in (resp.json() or [])]
        except (requests.RequestException, ValueError):
            return None

    def search_issues(self, text, limit=20):
        # Escape dau nhay de khong pha cu phap JQL.
        safe = str(text).replace('"', '\\"')
        jql = 'project = "%s" AND summary ~ "%s" ORDER BY created DESC' % (
            self.cfg.get("project_key"), safe)
        try:
            resp = requests.get("%s/rest/api/2/search" % self.base_url,
                                headers=self._headers(),
                                params={"jql": jql, "maxResults": limit,
                                        "fields": "summary,status"},
                                timeout=self._timeout())
            if resp.status_code != 200:
                return []
            issues = (resp.json() or {}).get("issues") or []
        except (requests.RequestException, ValueError):
            return []
        out = []
        for it in issues:
            fields = it.get("fields") or {}
            status = (fields.get("status") or {}).get("name")
            out.append({"id": it.get("key"), "title": fields.get("summary"),
                        "url": "%s/browse/%s" % (self.base_url, it.get("key")),
                        "status": status, "closed": self.is_closed(status)})
        return out

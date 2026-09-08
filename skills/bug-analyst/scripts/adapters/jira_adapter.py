#!/usr/bin/env python3
"""Jira: bug = issue co issuetype 'Bug'. REST API v2, Basic auth (email + token).

Dung v2 chu khong phai v3 -- giong quyet dinh cua skill log-bug: v3 tra
description dang ADF (cay JSON), khong dung chung duoc bo xu ly text.
"""
import requests
from requests.auth import HTTPBasicAuth

from .base_adapter import MAX_PAGES, BaseAdapter, TrackerError, normalize

REQUIRED = ("base_url", "email", "api_token", "project_key")
FIELDS = "summary,priority,created,labels,status,fixVersions,components"


class JiraAdapter(BaseAdapter):
    name = "jira"
    required = REQUIRED

    def _auth(self):
        return HTTPBasicAuth(self.cfg.get("email"), self.cfg.get("api_token"))

    def _jql(self, date_from, date_to):
        issue_type = self.cfg.get("bug_issue_type") or "Bug"
        parts = ['project = "%s"' % self.cfg.get("project_key"),
                 'issuetype = "%s"' % issue_type]
        if date_from:
            parts.append('created >= "%s"' % date_from)
        if date_to:
            parts.append('created <= "%s 23:59"' % date_to)
        return " AND ".join(parts) + " ORDER BY created ASC"

    def list_bugs(self, date_from, date_to):
        self._require()
        jql = self._jql(date_from, date_to)
        page_size = self._page_size()
        out, start = [], 0
        for _ in range(MAX_PAGES):
            data = self._get("/rest/api/2/search",
                             {"jql": jql, "startAt": start,
                              "maxResults": page_size, "fields": FIELDS})
            issues = data.get("issues") or []
            for it in issues:
                fields = it.get("fields") or {}
                out.append(normalize(
                    issue_id=it.get("key"), title=fields.get("summary"),
                    url="%s/browse/%s" % (self.base_url, it.get("key")),
                    labels=fields.get("labels") or [],
                    milestone=_first_name(fields.get("fixVersions")),
                    priority=((fields.get("priority") or {}) or {}).get("name"),
                    status=((fields.get("status") or {}) or {}).get("name"),
                    created_at=fields.get("created")))
            start += len(issues)
            if len(issues) < page_size or start >= int(data.get("total") or 0):
                break
        else:
            self.truncated = True
        return out

    def _get(self, path, params):
        try:
            resp = requests.get("%s%s" % (self.base_url, path), auth=self._auth(),
                                params=params, headers={"Accept": "application/json"},
                                timeout=self._timeout())
        except requests.RequestException as exc:
            raise TrackerError("Jira khong ket noi duoc: %s" % exc)
        if resp.status_code != 200:
            raise TrackerError("Jira doc issue that bai: HTTP %s -- %s"
                               % (resp.status_code, resp.text[:300]))
        try:
            return resp.json() or {}
        except ValueError:
            raise TrackerError("Jira tra ve response khong phai JSON")

    def verify(self):
        miss = self.missing_config()
        if miss:
            return {"ok": False, "detail": "thieu cau hinh: %s" % ", ".join(miss)}
        try:
            data = self._get("/rest/api/2/search",
                             {"jql": 'project = "%s"' % self.cfg.get("project_key"),
                              "maxResults": 1, "fields": "summary"})
        except TrackerError as exc:
            return {"ok": False, "detail": str(exc)}
        return {"ok": True, "detail": "project %r co %s issue"
                % (self.cfg.get("project_key"), data.get("total"))}


def _first_name(items):
    for item in (items or []):
        name = (item or {}).get("name")
        if name:
            return name
    return ""

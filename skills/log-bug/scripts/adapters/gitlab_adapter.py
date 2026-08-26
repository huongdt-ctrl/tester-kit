#!/usr/bin/env python3
"""GitLab adapter -- API v4 /projects/:id/issues, auth bang PRIVATE-TOKEN.

Tracker pho bien nhat o cac du an dung GitLab self-hosted.

Han che that cua GitLab, da xu ly bang cach nhung xuong description:
  - KHONG co start_date (chi Epic co, issue thi khong)
  - KHONG co field Severity/Scope rieng -> di vao description
  - assignee can user ID dang so, khong nhan username o field assignee_ids
"""
import urllib.parse

import requests

from .base_adapter import BaseAdapter, TrackerError

REQUIRED = ("base_url", "token", "project_path")


class GitLabAdapter(BaseAdapter):
    name = "gitlab"
    markup = "markdown"        # GitLab dung markdown -> heading la "### "
    supports = frozenset({"assignee", "due_date", "labels"})
    required = REQUIRED

    def _headers(self):
        return {"PRIVATE-TOKEN": self.cfg.get("token")}

    def _timeout(self):
        return int(self.cfg.get("timeout_seconds") or 30)

    def _project(self):
        # GitLab nhan project path da url-encode ("grp%2Fsub%2Fproj").
        return urllib.parse.quote(str(self.cfg.get("project_path") or ""), safe="")

    def _api(self, suffix):
        return "%s/api/v4/projects/%s%s" % (self.base_url, self._project(), suffix)

    def create_issue(self, title, description, fields):
        miss = self.missing_config(REQUIRED)
        if miss:
            raise TrackerError("GitLab thieu cau hinh: %s" % ", ".join(miss))

        payload = {"title": title, "description": description}
        if fields.get("due_date"):
            payload["due_date"] = fields["due_date"]
        if fields.get("labels"):
            labels = fields["labels"]
            payload["labels"] = ",".join(labels) if isinstance(labels, list) else str(labels)
        assignee = fields.get("assignee")
        if assignee not in (None, ""):
            try:
                payload["assignee_ids"] = [int(assignee)]
            except (TypeError, ValueError):
                raise TrackerError(
                    "GitLab assignee phai la user ID dang so, nhan duoc %r. "
                    "Khai assignee_id trong config thay vi username." % assignee)

        try:
            resp = requests.post(self._api("/issues"), headers=self._headers(),
                                 data=payload, timeout=self._timeout())
        except requests.RequestException as exc:
            raise TrackerError("GitLab khong ket noi duoc: %s" % exc)
        if resp.status_code not in (200, 201):
            raise TrackerError("GitLab tao bug that bai: HTTP %s -- %s"
                               % (resp.status_code, resp.text[:300]))
        issue = resp.json() or {}
        iid = issue.get("iid")
        if not iid:
            raise TrackerError("GitLab tra ve response khong co iid: %s" % resp.text[:300])
        return iid, issue.get("web_url") or "%s/-/issues/%s" % (self.base_url, iid)

    def get_issue_status(self, issue_id):
        try:
            resp = requests.get(self._api("/issues/%s" % str(issue_id).strip()),
                                headers=self._headers(), timeout=self._timeout())
            if resp.status_code != 200:
                return None
            # GitLab state chi co "opened"/"closed".
            return (resp.json() or {}).get("state")
        except (requests.RequestException, ValueError):
            return None

    def verify_project(self):
        try:
            resp = requests.get(self._api(""), headers=self._headers(),
                                timeout=self._timeout())
        except requests.RequestException as exc:
            return {"ok": None, "detail": "khong ket noi duoc: %s" % exc}
        if resp.status_code == 200:
            return {"ok": True, "detail": "project_path %r -> %r"
                    % (self.cfg.get("project_path"),
                       (resp.json() or {}).get("path_with_namespace"))}
        if resp.status_code in (401, 403):
            return {"ok": False, "detail": "token khong co quyen doc project %r "
                                           "(HTTP %s)" % (self.cfg.get("project_path"),
                                                          resp.status_code)}
        if resp.status_code == 404:
            return {"ok": False, "detail": "project_path %r khong ton tai tren %s "
                                           "(hoac token khong thay duoc)"
                    % (self.cfg.get("project_path"), self.base_url)}
        return {"ok": None, "detail": "HTTP %s" % resp.status_code}

    # GitLab issue khong co field priority -> khong co gi de doi chieu.
    def list_priorities(self):
        return None

    def search_issues(self, text, limit=20):
        params = {"search": text, "in": "title", "state": "all", "per_page": limit}
        try:
            resp = requests.get(self._api("/issues"), headers=self._headers(),
                                params=params, timeout=self._timeout())
            if resp.status_code != 200:
                return []
            issues = resp.json() or []
        except (requests.RequestException, ValueError):
            return []
        out = []
        for it in issues:
            state = it.get("state")
            out.append({"id": it.get("iid"), "title": it.get("title"),
                        "url": it.get("web_url"), "status": state,
                        "closed": str(state).lower() == "closed"})
        return out

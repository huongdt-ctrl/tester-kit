#!/usr/bin/env python3
"""GitLab: bug = issue co label 'bug'. API v4, auth PRIVATE-TOKEN.

GitLab KHONG co field priority cho issue -> doc tu label dang 'priority::high'.
Khong co label do thi de trong, KHONG doan Normal (doan thi thong ke sai ma
khong ai biet).
"""
import urllib.parse

import requests

from .base_adapter import MAX_PAGES, BaseAdapter, TrackerError, normalize

REQUIRED = ("base_url", "token", "project_path")


class GitLabAdapter(BaseAdapter):
    name = "gitlab"
    required = REQUIRED

    def _headers(self):
        return {"PRIVATE-TOKEN": self.cfg.get("token")}

    def _api(self, suffix=""):
        project = urllib.parse.quote(str(self.cfg.get("project_path") or ""), safe="")
        return "%s/api/v4/projects/%s%s" % (self.base_url, project, suffix)

    def list_bugs(self, date_from, date_to):
        self._require()
        label = self.cfg.get("bug_label") or "bug"
        params = {"labels": label, "state": "all", "per_page": self._page_size(),
                  "order_by": "created_at", "sort": "asc"}
        if date_from:
            params["created_after"] = "%sT00:00:00Z" % date_from
        if date_to:
            params["created_before"] = "%sT23:59:59Z" % date_to

        out = []
        for page in range(1, MAX_PAGES + 1):
            params["page"] = page
            batch = self._get("/issues", params)
            if not batch:
                break
            for it in batch:
                out.append(normalize(
                    issue_id="#%s" % it.get("iid"), title=it.get("title"),
                    url=it.get("web_url"), labels=it.get("labels") or [],
                    milestone=((it.get("milestone") or {}) or {}).get("title"),
                    priority=_priority_from_labels(it.get("labels") or []),
                    status=it.get("state"), created_at=it.get("created_at")))
            if len(batch) < params["per_page"]:
                break
        else:
            # Chay het MAX_PAGES ma khong lan nao gap trang ngan -> con du lieu.
            self.truncated = True
        return out

    def _get(self, suffix, params):
        try:
            resp = requests.get(self._api(suffix), headers=self._headers(),
                                params=params, timeout=self._timeout())
        except requests.RequestException as exc:
            raise TrackerError("GitLab khong ket noi duoc: %s" % exc)
        if resp.status_code != 200:
            raise TrackerError("GitLab doc issue that bai: HTTP %s -- %s"
                               % (resp.status_code, resp.text[:300]))
        try:
            return resp.json() or []
        except ValueError:
            raise TrackerError("GitLab tra ve response khong phai JSON")

    def verify(self):
        miss = self.missing_config()
        if miss:
            return {"ok": False, "detail": "thieu cau hinh: %s" % ", ".join(miss)}
        try:
            resp = requests.get(self._api(), headers=self._headers(),
                                timeout=self._timeout())
        except requests.RequestException as exc:
            return {"ok": None, "detail": "khong ket noi duoc: %s" % exc}
        if resp.status_code == 200:
            return {"ok": True, "detail": "project %r doc duoc"
                    % self.cfg.get("project_path")}
        if resp.status_code in (401, 403):
            return {"ok": False, "detail": "token khong co quyen doc project (HTTP %s)"
                    % resp.status_code}
        if resp.status_code == 404:
            return {"ok": False, "detail": "project_path %r khong ton tai tren %s"
                    % (self.cfg.get("project_path"), self.base_url)}
        return {"ok": None, "detail": "HTTP %s" % resp.status_code}


def _priority_from_labels(labels):
    """Label 'priority::High' / 'prio::urgent' -> ten priority."""
    for raw in labels:
        text = str(raw)
        for sep in ("::", ":", "/"):
            if sep in text:
                head, _, tail = text.partition(sep)
                if head.strip().lower() in ("priority", "prio", "p"):
                    return tail.strip()
    return ""

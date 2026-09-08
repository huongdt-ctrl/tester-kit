#!/usr/bin/env python3
"""Redmine: bug = issue co tracker 'Bug'. API /issues.json, header X-Redmine-API-Key.

Redmine loc theo tracker_id (so), khong loc theo ten tracker -> skill tu tra
tracker_id tu /trackers.json neu config chi khai ten.
"""
import requests

from .base_adapter import MAX_PAGES, BaseAdapter, TrackerError, normalize

REQUIRED = ("base_url", "api_key", "project_id")


class RedmineAdapter(BaseAdapter):
    name = "redmine"
    required = REQUIRED

    def _headers(self):
        return {"X-Redmine-API-Key": self.cfg.get("api_key")}

    def _tracker_id(self):
        if self.cfg.get("bug_tracker_id"):
            return self.cfg["bug_tracker_id"]
        wanted = str(self.cfg.get("bug_tracker_name") or "Bug").strip().lower()
        data = self._get("/trackers.json", {})
        for tracker in data.get("trackers") or []:
            if str(tracker.get("name", "")).strip().lower() == wanted:
                return tracker.get("id")
        raise TrackerError(
            "Redmine khong co tracker ten %r. Khai bug_tracker_id truc tiep trong config."
            % self.cfg.get("bug_tracker_name", "Bug"))

    def list_bugs(self, date_from, date_to):
        self._require()
        params = {"project_id": self.cfg.get("project_id"),
                  "tracker_id": self._tracker_id(), "status_id": "*",
                  "limit": self._page_size(), "sort": "created_on:asc"}
        if date_from and date_to:
            params["created_on"] = "><%s|%s" % (date_from, date_to)
        elif date_from:
            params["created_on"] = ">=%s" % date_from
        elif date_to:
            params["created_on"] = "<=%s" % date_to

        out, offset = [], 0
        for _ in range(MAX_PAGES):
            params["offset"] = offset
            data = self._get("/issues.json", params)
            issues = data.get("issues") or []
            for it in issues:
                out.append(normalize(
                    issue_id="#%s" % it.get("id"), title=it.get("subject"),
                    url="%s/issues/%s" % (self.base_url, it.get("id")),
                    labels=[], milestone=((it.get("fixed_version") or {}) or {}).get("name"),
                    priority=((it.get("priority") or {}) or {}).get("name"),
                    status=((it.get("status") or {}) or {}).get("name"),
                    created_at=it.get("created_on")))
            offset += len(issues)
            if len(issues) < params["limit"] or offset >= int(data.get("total_count") or 0):
                break
        else:
            self.truncated = True
        return out

    def _get(self, path, params):
        try:
            resp = requests.get("%s%s" % (self.base_url, path), headers=self._headers(),
                                params=params, timeout=self._timeout())
        except requests.RequestException as exc:
            raise TrackerError("Redmine khong ket noi duoc: %s" % exc)
        if resp.status_code != 200:
            raise TrackerError("Redmine doc issue that bai: HTTP %s -- %s"
                               % (resp.status_code, resp.text[:300]))
        try:
            return resp.json() or {}
        except ValueError:
            raise TrackerError("Redmine tra ve response khong phai JSON")

    def verify(self):
        miss = self.missing_config()
        if miss:
            return {"ok": False, "detail": "thieu cau hinh: %s" % ", ".join(miss)}
        try:
            data = self._get("/projects/%s.json" % self.cfg.get("project_id"), {})
        except TrackerError as exc:
            return {"ok": False, "detail": str(exc)}
        return {"ok": True, "detail": "project %r doc duoc"
                % ((data.get("project") or {}).get("name"))}

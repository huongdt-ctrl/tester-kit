#!/usr/bin/env python3
"""Factory chon adapter theo config -- CHO DUY NHAT trong skill biet ten tracker
cu the. Them tracker moi chi sua file nay."""
from .base_adapter import BaseAdapter, TrackerError, normalize
from .gitlab_adapter import GitLabAdapter
from .jira_adapter import JiraAdapter
from .redmine_adapter import RedmineAdapter

ADAPTERS = {"redmine": RedmineAdapter, "gitlab": GitLabAdapter, "jira": JiraAdapter}


def build_adapter(merged):
    tracker = merged.get("tracker") or {}
    system = str(tracker.get("system") or "").strip().lower()
    if not system:
        raise TrackerError("Thieu tracker.system. Chon mot trong: %s"
                           % ", ".join(sorted(ADAPTERS)))
    if system not in ADAPTERS:
        raise TrackerError("tracker.system khong ho tro: %r. Chi ho tro: %s"
                           % (system, ", ".join(sorted(ADAPTERS))))
    return ADAPTERS[system](tracker)


__all__ = ["BaseAdapter", "TrackerError", "normalize", "GitLabAdapter",
           "JiraAdapter", "RedmineAdapter", "ADAPTERS", "build_adapter"]

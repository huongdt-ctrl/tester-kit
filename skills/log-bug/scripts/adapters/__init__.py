#!/usr/bin/env python3
"""Factory chon adapter theo config. Day la CHO DUY NHAT trong skill biet ten
cac tracker cu the -- them tracker moi chi can sua file nay."""
from .base_adapter import BaseAdapter, TrackerError
from .gitlab_adapter import GitLabAdapter
from .jira_adapter import JiraAdapter
from .redmine_adapter import RedmineAdapter

ADAPTERS = {"redmine": RedmineAdapter, "gitlab": GitLabAdapter, "jira": JiraAdapter}


def build_adapter(merged):
    """Dung adapter tu block 'tracker' cua config da merge."""
    tracker = (merged.get("tracker") or {})
    system = str(tracker.get("system") or "").strip().lower()
    if not system:
        raise TrackerError("Thieu tracker.system. Chon mot trong: %s"
                           % ", ".join(sorted(ADAPTERS)))
    if system not in ADAPTERS:
        raise TrackerError("tracker.system khong ho tro: %r. Chi ho tro: %s"
                           % (system, ", ".join(sorted(ADAPTERS))))
    return ADAPTERS[system](tracker)


__all__ = ["BaseAdapter", "TrackerError", "RedmineAdapter", "GitLabAdapter",
           "JiraAdapter", "ADAPTERS", "build_adapter"]

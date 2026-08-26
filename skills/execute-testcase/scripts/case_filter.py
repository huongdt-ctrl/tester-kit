#!/usr/bin/env python3
"""
Select which test cases a run touches, in the exact 5-step order SKILL.md
Phase 3 fixes. Order matters: applying status filters before execution_mode
would make rerun_failed meaningless.

Every step records how many cases survived it. That trail is what lets a reader
of execution_summary.md tell "no case matched the filter" apart from "the column
mapping was wrong" -- previously indistinguishable, both showed up as 0 cases.

Two conventions that were ambiguous before and are now pinned:
  - An EMPTY list means "do not apply this filter", never "exclude everything".
  - exclude_* always beats include_*.
"""


class CaseFilterError(Exception):
    """Filter configuration is self-contradictory."""


def _vals(cfg, key):
    v = cfg.get(key)
    return [str(x).strip() for x in v] if v else []


def _keep(value, includes, excludes):
    v = str(value or "").strip()
    if excludes and v in excludes:
        return False
    if includes and v not in includes:
        return False
    return True


def select_cases(cases, merged_cfg):
    """cases: list of dicts with keys tc_id, test_result, priority,
    classification_1 (missing keys tolerated -> treated as empty).

    Returns (selected_cases, trail) where trail is a list of
    (step_name, count_after) for the summary report."""
    run = merged_cfg.get("run") or {}
    case_filter = merged_cfg.get("case_filter") or {}
    mode = run.get("execution_mode") or "baseline"

    trail = [("tong so case trong worksheet", len(cases))]
    current = list(cases)

    # --- step 1: execution_mode picks the base set
    if mode == "baseline":
        pass
    elif mode == "rerun_failed":
        current = [c for c in current if str(c.get("test_result") or "").strip() == "Fail"]
    elif mode == "selected_cases":
        ids = _vals(case_filter, "include_tc_ids")
        if not ids:
            raise CaseFilterError(
                "execution_mode = selected_cases nhung include_tc_ids rong -- "
                "loi cau hinh, khong duoc hieu thanh 'chay het'."
            )
        current = [c for c in current if str(c.get("tc_id") or "").strip() in ids]
    else:
        raise CaseFilterError(
            "execution_mode khong hop le: %r (chi nhan baseline | rerun_failed | selected_cases)" % mode
        )
    trail.append(("sau execution_mode=%s" % mode, len(current)))

    # --- step 2: status filter. Skipped for the two modes that already imply a
    # status, otherwise rerun_failed would filter its own Fail cases away when
    # execute_only_statuses is [Untested, Pending].
    statuses = _vals(run, "execute_only_statuses")
    if statuses and mode == "baseline":
        current = [c for c in current
                   if str(c.get("test_result") or "").strip() in statuses
                   or not str(c.get("test_result") or "").strip()]
        trail.append(("sau execute_only_statuses", len(current)))
    else:
        trail.append(("execute_only_statuses: khong ap dung (mode=%s)" % mode, len(current)))

    # --- step 3: explicit TC ID list
    inc_ids, exc_ids = _vals(case_filter, "include_tc_ids"), _vals(case_filter, "exclude_tc_ids")
    if mode == "selected_cases":
        inc_ids = []                       # already applied in step 1
    if inc_ids or exc_ids:
        current = [c for c in current if _keep(c.get("tc_id"), inc_ids, exc_ids)]
    trail.append(("sau filter TC ID", len(current)))

    # --- step 4: classification
    inc_cls, exc_cls = (_vals(case_filter, "include_classification_1"),
                        _vals(case_filter, "exclude_classification_1"))
    if inc_cls or exc_cls:
        current = [c for c in current if _keep(c.get("classification_1"), inc_cls, exc_cls)]
    trail.append(("sau filter Classification 1", len(current)))

    # --- step 5: priority
    inc_pri, exc_pri = _vals(case_filter, "include_priorities"), _vals(case_filter, "exclude_priorities")
    if inc_pri or exc_pri:
        current = [c for c in current if _keep(c.get("priority"), inc_pri, exc_pri)]
    trail.append(("sau filter Priority", len(current)))

    return current, trail


def format_trail(trail):
    """Markdown lines for execution_summary.md."""
    return "\n".join("- %s: %d case" % (name, n) for name, n in trail)

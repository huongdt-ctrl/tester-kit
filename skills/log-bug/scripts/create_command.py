#!/usr/bin/env python3
"""Subcommand `create` -- cai duy nhat tao issue THAT tren tracker va ghi registry.

Tach khoi commands.py vi day la buoc co tac dung phu ra ngoai: sai o day la tao
bug rac tren tracker cua khach, khong phai chi in sai output.
"""
import datetime

import bug_batch
import bug_template
import bug_validator
import cli_io
import dedup_checker
from adapters import TrackerError, build_adapter


def _closed_lookup(adapter):
    """Boc adapter thanh callable(issue_id) -> True/False/None cho dedup_checker,
    de dedup_checker khong phai biet gi ve tracker."""
    def lookup(issue_id):
        status = adapter.get_issue_status(issue_id)
        return None if status is None else adapter.is_closed(status)
    return lookup


def create(args):
    merged = cli_io.load_config(args)
    adapter = build_adapter(merged)
    module = (merged.get("run") or {}).get("module_name")
    reg_path = dedup_checker.registry_path(merged, module)
    registry = dedup_checker.load_registry(reg_path)
    dry_run = bool(args.dry_run or (merged.get("run") or {}).get("dry_run"))
    today = datetime.date.today().isoformat()
    policy = cli_io.policy(merged)
    # warn_only: van tao bug du nghi trung, nhung ghi ro canh bao. Dung khi QA
    # muon tu review thay vi de skill tu quyet.
    warn_only = str(policy.get("duplicate_handling") or "skip").lower() == "warn_only"
    use_registry = policy.get("check_registry_before_create", True) is not False
    use_search = policy.get("check_tracker_search_before_create", True) is not False

    bugs = cli_io.read_bugs(args.bug_file, merged)
    merge_plan = None
    if args.apply_merge:
        bugs, merge_plan = bug_batch.apply_merge(bugs, cli_io.ui_merge_cfg(merged))
        if bugs is None:
            cli_io.fail(
                "Co nhom bug UI vuot nguong Case B -> phai hoi user truoc khi gop. "
                "Xem `merge-check` roi chay lai: bo --apply-merge de log rieng, "
                "hoac sua lai bug file.",
                plan=merge_plan)

    created, skipped, failed = [], [], []
    for bug in bugs:
        errors, warnings = bug_validator.validate(bug, merged)
        if errors:
            failed.append({"summary": bug.get("summary"), "errors": errors,
                           "warnings": warnings})
            continue

        title = cli_io.title(bug, merged)
        # dry_run khong goi mang -> khong search, khong hoi trang thai issue cu.
        remote = [] if dry_run else adapter.search_issues(title)
        decision = dedup_checker.decide(
            bug, registry, remote, title=title,
            closed_lookup=None if dry_run else _closed_lookup(adapter))
        if decision["action"] == "skip_duplicate":
            skipped.append(dict(decision, title=title))
            continue

        fields = cli_io.tracker_fields(bug, merged)
        regression_of = ((decision["existing"] or {}).get("issue_id")
                         if decision["action"] == "create_regression" else None)
        description = bug_template.build_description(
            bug, markup=adapter.markup,
            unsupported=adapter.unsupported_fields(fields),
            regression_of=regression_of)

        if dry_run:
            created.append({"action": decision["action"], "dry_run": True,
                            "title": title, "description": description,
                            "fingerprint": decision["fingerprint"],
                            "warnings": warnings})
            continue

        try:
            issue_id, issue_url = adapter.create_issue(title, description, fields)
        except TrackerError as exc:
            failed.append({"summary": bug.get("summary"), "errors": [str(exc)]})
            continue

        entry = {"issue_id": issue_id, "issue_url": issue_url, "title": title,
                 "screen": bug.get("screen"), "bug_type": bug.get("bug_type"),
                 "ui_subtype": bug.get("ui_subtype"), "tracker": adapter.name,
                 "logged_at": today, "closed": False, "regression_of": regression_of}
        # Bug THAT da duoc tao tren tracker roi. Ghi registry that bai (het dia,
        # thieu quyen) KHONG duoc lam mat bao cao ve bug vua tao -- bao cao lai
        # kem canh bao, khong crash de lai issue mo co ma khong ai biet.
        entry_warnings = list(warnings)
        try:
            registry = dedup_checker.save_entry(reg_path, decision["fingerprint"], entry)
        except OSError as exc:
            entry_warnings.append(
                "Bug da tao thanh cong nhung GHI REGISTRY THAT BAI (%s). Lan chay "
                "sau se khong biet bug nay da ton tai -> co the tao trung. "
                "Ghi lai %s vao registry bang tay." % (exc, issue_id))
        created.append(dict(entry, action=decision["action"], warnings=entry_warnings))

    cli_io.out({"ok": not failed, "tracker": adapter.name, "dry_run": dry_run,
                "registry_path": reg_path, "created": created, "skipped": skipped,
                "failed": failed, "applied_merge": bool(args.apply_merge),
                "merge_plan": merge_plan,
                "duplicate_handling": "warn_only" if warn_only else "skip",
                "counts": {"input_bugs": len(bugs), "created": len(created),
                           "skipped_duplicate": len(skipped),
                           "failed": len(failed)}}, 1 if failed else 0)

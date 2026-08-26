#!/usr/bin/env python3
"""Handler cho cac subcommand doc/kiem tra. `create` nam rieng o create_command.py
vi no la subcommand duy nhat ghi ra ngoai (tao issue that + ghi registry)."""
import bug_batch
import bug_template
import bug_validator
import cli_io
import config_loader
import dedup_checker
import preflight_checks
import ui_bug_merger
from adapters import build_adapter

def preflight(args):
    merged = cli_io.load_config(args)
    adapter = build_adapter(merged)
    miss = adapter.missing_config()
    if miss:
        cli_io.fail("Tracker %s thieu cau hinh: %s" % (adapter.name, ", ".join(miss)),
                    tracker=adapter.name)
    dry_run = (merged.get("run") or {}).get("dry_run")
    reachable, note, checks = True, "khong goi API vi dang dry_run", {}
    if not dry_run:
        hits = adapter.search_issues("__log_bug_preflight__", limit=1)
        reachable = hits is not None
        note = "search API tra ve %d ket qua" % len(hits or [])
        # Bat config sai TAI DAY, truoc khi tao bug that dau tien.
        checks = {"project": preflight_checks.check_project(adapter),
                  "priority_map": preflight_checks.check_priority_map(
                      adapter, cli_io.policy(merged))}
        blocking = preflight_checks.blocking_reasons(checks)
        if blocking:
            cli_io.fail("Cau hinh tracker sai: %s" % " | ".join(blocking),
                        tracker=adapter.name, checks=checks)
    cli_io.out({"ok": True, "tracker": adapter.name, "markup": adapter.markup,
                "native_fields": sorted(adapter.supports),
                "fields_embedded_in_description":
                    sorted(adapter.unsupported_fields(
                        cli_io.tracker_fields({"severity": "Major", "scope": "Frontend",
                                               "device": "PC", "os_version": "14.4",
                                               "browser": "Chrome"}, merged))),
                "reachable": reachable, "note": note, "checks": checks,
                "warnings": [
                    "%s: %s" % (k, v.get("detail")) for k, v in checks.items()
                    if v.get("ok") is None],
                "effective_config": config_loader.effective_config(merged)})


def validate(args):
    merged = cli_io.load_config(args)
    results, blocked = [], 0
    for idx, bug in enumerate(cli_io.read_bugs(args.bug_file, merged)):
        errors, warnings = bug_validator.validate(bug, merged)
        blocked += 1 if errors else 0
        results.append({"index": idx, "summary": bug.get("summary"),
                        "errors": errors, "warnings": warnings,
                        "can_create": not errors})
    cli_io.out({"ok": blocked == 0, "total": len(results), "blocked": blocked,
                "results": results}, 1 if blocked else 0)


def render(args):
    merged = cli_io.load_config(args)
    adapter = build_adapter(merged)
    rendered = []
    for bug in cli_io.read_bugs(args.bug_file, merged):
        fields = cli_io.tracker_fields(bug, merged)
        rendered.append({
            "title": cli_io.title(bug, merged),
            "description": bug_template.build_description(
                bug, markup=adapter.markup,
                unsupported=adapter.unsupported_fields(fields)),
            "fingerprint": dedup_checker.fingerprint(bug)})
    cli_io.out({"ok": True, "tracker": adapter.name, "markup": adapter.markup,
                "bugs": rendered})


def merge_check(args):
    merged = cli_io.load_config(args)
    bugs = cli_io.read_bugs(args.bug_file, merged)
    plan = bug_batch.merge_plan(bugs, cli_io.ui_merge_cfg(merged))
    if plan is None:
        cli_io.out({"ok": True, "enabled": False,
                    "note": "ui_merge.enabled = false -> moi loi log 1 bug (rule 3)",
                    "plan": {"merge": [], "needs_confirm": [],
                             "separate": [{"indices": [i]} for i in range(len(bugs))]}})
    previews = [{"group_key": g.get("group_key"), "case": g.get("case"),
                 "indices": g["indices"],
                 "merged_title": cli_io.title(
                     ui_bug_merger.build_merged_bug(bugs, g), merged)}
                for g in plan["merge"]]
    cli_io.out({"ok": True, "enabled": True, "total": len(bugs), "plan": plan,
                "merged_previews": previews,
                "needs_user_confirm": bool(plan["needs_confirm"]),
                "hint": "Chay `create --apply-merge` de tao dung ke hoach nay; "
                        "khong co co nay thi create tao 1 ticket moi dong."})


def registry(args):
    merged = cli_io.load_config(args)
    module = (merged.get("run") or {}).get("module_name")
    path = dedup_checker.registry_path(merged, module)
    entries = dedup_checker.load_registry(path)
    cli_io.out({"ok": True, "registry_path": path, "total": len(entries),
                "entries": entries})

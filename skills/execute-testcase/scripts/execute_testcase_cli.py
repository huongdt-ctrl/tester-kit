#!/usr/bin/env python3
"""
The one entry point the skill agent calls. The agent drives the browser (via the
chrome-devtools / browser-automation skills) and decides Pass/Fail; every piece
of deterministic I/O -- config merge, sheet read/write, Redmine -- goes through
here, so those parts are reproducible and unit-tested rather than improvised per
run.

Subcommands
  preflight    merge config, resolve credentials, run the production safety gate
  load-cases   map columns, apply the 5-step filter, emit cases + filter trail
  write-result write execution columns for ONE case (protected columns refused)
  log-bug      create a Redmine bug with duplicate resolution

Every subcommand prints JSON on stdout: {"ok": bool, ...}. Exit code 0 on ok,
1 on a handled error, so the agent can branch on either.

Vi du goi cu the: xem SKILL.md muc 4A.
"""
import collections
import datetime
import json
import sys

import case_filter
import cli_parser
import column_mapper
import config_loader
import redmine_client
import result_validator
import sheet_io
import target_resolver


def _emit(payload, code=0):
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(code)


def _load(args):
    bundle = config_loader.load(args.profile, args.manifest)
    return bundle, bundle["merged"]


def _resolve_target(merged):
    """Chot file dich cho run nay (in_place / backup_then_update / clone_then_write)."""
    module_name = (merged.get("run") or {}).get("module_name")
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    state = target_resolver.resolve(
        merged, module_name, stamp,
        clone_google_sheet=lambda fid, title: sheet_io.clone_spreadsheet(merged, fid, title))
    return state, target_resolver.apply_target(merged, state)


def _sheet_context(merged):
    """worksheet + header row + logical->index mapping, validated."""
    ws = sheet_io.open_worksheet(merged)
    src = merged.get("testcase_source") or {}
    header_idx = int(src.get("header_row_index") or 1)
    header = ws.row_values(header_idx)
    mapping = column_mapper.map_columns(header, merged)
    column_mapper.validate_mapping(mapping, merged)
    return ws, header, mapping


def cmd_preflight(args):
    bundle, merged = _load(args)
    reasons = config_loader.check_environment_safety(merged)
    env = merged.get("environment") or {}
    _emit({
        "ok": not reasons,
        "requires_user_confirmation": bool(reasons),
        "environment": {"name": env.get("name"), "base_url": env.get("base_url")},
        "production_risk_reasons": reasons,
        "effective_config": bundle["effective_table"],
        "execution_mode": (merged.get("run") or {}).get("execution_mode"),
        "redmine_enabled": bool((merged.get("redmine") or {}).get("enabled")),
        "write_mode": target_resolver.mode_of(merged),
        "target_state_file": target_resolver.state_path(
            merged, (merged.get("run") or {}).get("module_name")),
        "note": ("DUNG LAI va hoi user truoc khi chay." if reasons
                 else "An toan de chay."),
    }, 0 if not reasons else 1)


def cmd_load_cases(args):
    _, merged = _load(args)
    ws, header, mapping = _sheet_context(merged)
    cases = sheet_io.read_cases(ws, merged, mapping)
    selected, trail = case_filter.select_cases(cases, merged)
    _emit({
        "ok": True,
        "selected_count": len(selected),
        "filter_trail": [{"step": s, "count": n} for s, n in trail],
        "filter_trail_markdown": case_filter.format_trail(trail),
        "cases": selected,
    })


def cmd_write_result(args):
    _, merged = _load(args)
    if args.reset_target:
        target_resolver.reset(merged, (merged.get("run") or {}).get("module_name"))
    state, merged_target = _resolve_target(merged)
    ws, header, mapping = _sheet_context(merged_target)
    merged = merged_target

    policy = merged.get("result_policy") or {}
    status, remark = args.status, (args.remark or "")
    try:
        result_validator.validate(status, remark, args.actual, mapping, merged)
    except result_validator.ResultValidationError as exc:
        _emit({"ok": False, "error": str(exc)}, 1)

    updates = collections.OrderedDict()
    updates["test_result"] = status
    updates["test_date"] = args.test_date or sheet_io.today_string(merged)
    if policy.get("write_tested_by", True):
        updates["tested_by"] = args.tested_by or ((merged.get("run") or {}).get("tested_by") or "")
    if remark:
        updates["remark"] = remark
    if args.actual:
        updates["actual_result"] = args.actual
    if args.bug_id:
        updates["bug_id"] = args.bug_id
    if args.bug_url:
        updates["bug_url"] = args.bug_url

    try:
        written = sheet_io.write_result(ws, merged, mapping, header, args.row, updates)
    except sheet_io.SheetWriteError as exc:
        _emit({"ok": False, "error": str(exc)}, 1)
    skipped = [k for k in updates if k not in mapping]
    _emit({"ok": True, "row": args.row, "cells_written": written,
           "columns_absent_logged_to_summary": skipped,
           "write_mode": state["mode"], "target": state["target"],
           "source": state["source"], "source_untouched": state["source_untouched"],
           "backup": state.get("backup")})


def cmd_log_bug(args):
    _, merged = _load(args)
    rm = redmine_client.redmine_settings(merged)
    if not rm:
        _emit({"ok": False, "error": "redmine.enabled = false, khong tao bug"}, 1)

    if not redmine_client.should_create_bug("Fail", merged):
        _emit({"ok": False, "error": "Config khong cho tao bug cho status Fail"}, 1)

    status_name = None
    if args.existing_bug_id:
        status_name = redmine_client.get_issue_status(rm["base_url"], rm["api_key"], args.existing_bug_id)
    action = redmine_client.decide_duplicate_action(args.existing_bug_id, status_name)

    if action == "reuse_open":
        _emit({"ok": True, "action": action, "bug_id": args.existing_bug_id,
               "existing_status": status_name,
               "remark_suggestion": "Fail lặp lại — bug đã tồn tại",
               "note": "Khong tao bug moi (muc 12A)."})

    env = merged.get("environment") or {}
    fields = collections.OrderedDict([
        ("Module", (merged.get("run") or {}).get("module_name")),
        ("TC ID", args.tc_id), ("Test Case Title", args.title),
        ("Environment", env.get("base_url")), ("Preconditions", args.preconditions),
        ("Steps Executed", args.steps), ("Test Data", args.test_data),
        ("Expected Result", args.expected), ("Actual Result", args.actual),
        ("Tested By", args.tested_by), ("Test Date", args.test_date or sheet_io.today_string(merged)),
        ("Evidence", args.evidence),
    ])
    title = redmine_client.build_bug_title(
        rm.get("bug_title_pattern"), (merged.get("run") or {}).get("module_name"),
        args.tc_id, args.summary)
    body = redmine_client.build_bug_description(
        fields, regression_of=args.existing_bug_id if action == "create_regression" else None)

    try:
        issue_id, issue_url = redmine_client.create_issue(
            rm["base_url"], rm["api_key"], rm["project_id"], title, body,
            tracker_id=rm.get("tracker_id"), status_id=rm.get("status_id"),
            priority_id=rm.get("priority_id"), assigned_to_id=rm.get("assigned_to_id"),
            category_id=rm.get("category_id"))
    except redmine_client.RedmineError as exc:
        _emit({"ok": False, "error": str(exc)}, 1)
    _emit({"ok": True, "action": action, "bug_id": issue_id, "bug_url": issue_url,
           "regression_of": args.existing_bug_id if action == "create_regression" else None})


def main(argv=None):
    args = cli_parser.build_parser().parse_args(argv)
    try:
        {"preflight": cmd_preflight, "load-cases": cmd_load_cases,
         "write-result": cmd_write_result, "log-bug": cmd_log_bug}[args.cmd](args)
    except (config_loader.ConfigError, column_mapper.ColumnMappingError,
            case_filter.CaseFilterError, sheet_io.SheetWriteError,
            redmine_client.RedmineError, target_resolver.TargetError,
            result_validator.ResultValidationError) as exc:
        _emit({"ok": False, "error": str(exc), "error_type": type(exc).__name__}, 1)


if __name__ == "__main__":
    main()

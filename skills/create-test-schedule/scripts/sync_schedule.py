#!/usr/bin/env python3
"""
Merge an existing schedule with a fresh estimate extract, producing tasks.json
for schedule_capacity.py.

Three things it protects, none of which a plain rebuild would:

  1. What the tester typed -- Status, Actual Start/End, Actual (h), % Done and
     any hand-written Note survive the rebuild untouched.
  2. History -- rows already DONE or CANCEL keep their planned dates (emitted as
     frozen tasks). Only unfinished work is re-planned.
  3. The estimate change itself -- when a module's phase effort moved since the
     last build, the delta is recorded in the row's Note and in the report, so
     nobody has to diff two spreadsheets by eye.

It also prints the calibration signal the whole exercise is for: Actual (h) vs
Est (h) per phase over completed rows. That ratio is what feeds back into
estimate-test's base rates.

Usage:
    python3 sync_schedule.py --estimates <estimates.json> --config <config.json> \
        --out <tasks.json> [--old <existing.xlsx>] [--report <report.json>]

config.json shape:
{
  "project_name": "Test Schedule - ...",
  "start_date": "2026-08-24",
  "daily_capacity_hours": 6.5,
  "work_days": [0, 1, 2, 3, 4],
  "holidays": [],
  "tester_by_phase": {"1": "NgocTTB", "2": "NgocTTB", "3": "HaoNTT", "4": "HaoNTT"},
  "tester_overrides": {"event_edit_schedule": {"3": "NgocTTB"}}
}
"""
import argparse
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openpyxl import load_workbook

from schedule_format import DATA_START, FROZEN_STATUSES, iso, resolve_columns

CARRY = ("actual_start", "actual_end", "actual_hours", "pct_done")
EST_MARK = re.compile(r"\s*\|\s*est [\d.]+h → [\d.]+h \(\d{4}-\d{2}-\d{2}\)")


def read_old(path):
    """Existing schedule -> {(module, phase_order): row dict}. openpyxl only: this
    machine has no pandas/markitdown, and the skill must not depend on them.

    Columns are located by header text, so a schedule written by an older layout
    still reads correctly -- missing columns simply come back as None."""
    ws = load_workbook(path, data_only=True).active
    col = resolve_columns(ws)
    missing = [k for k in ("module", "phase", "status") if k not in col]
    if missing:
        raise SystemExit(f"{path}: header row is missing required column(s): {missing}")

    def get(r, key):
        idx = col.get(key)
        return ws.cell(row=r, column=idx).value if idx else None

    old = {}
    for r in range(DATA_START, ws.max_row + 1):
        module, phase = get(r, "module"), get(r, "phase")
        if not module or not phase:
            continue
        m = re.match(r"\s*(\d+)", str(phase))
        if not m:
            continue
        old[(module, int(m.group(1)))] = {
            "phase": phase,
            "tester": get(r, "tester"),
            "est": get(r, "effort_hours"),
            "plan_start": iso(get(r, "start_date")),
            "plan_end": iso(get(r, "end_date")),
            "actual_start": iso(get(r, "actual_start")),
            "actual_end": iso(get(r, "actual_end")),
            "actual_hours": get(r, "actual_hours"),
            "pct_done": get(r, "pct_done"),
            "status": str(get(r, "status") or "TODO").upper(),
            "note": get(r, "note") or "",
        }
    return old


def pick_tester(cfg, module, phase_order, old_row):
    # whoever actually did finished work stays credited with it
    if old_row and old_row["status"] in FROZEN_STATUSES and old_row["tester"]:
        return old_row["tester"]
    override = cfg.get("tester_overrides", {}).get(module, {})
    return override.get(str(phase_order)) or cfg["tester_by_phase"][str(phase_order)]


def remaining_hours(est, old_row):
    """Capacity still to spend. DOING at 60% only needs its leftover 40%."""
    if not old_row:
        return est
    if old_row["status"] in FROZEN_STATUSES:
        return 0.0
    pct = old_row.get("pct_done")
    if old_row["status"] == "DOING" and isinstance(pct, (int, float)) and 0 <= pct <= 100:
        return round(est * (1 - pct / 100.0), 2)
    return est


def build_note(old_row, meta, est_old, est_new, today, frozen):
    """Keep the human's note; refresh only the machine-written est-change tail."""
    if old_row is None:
        return meta
    note = EST_MARK.sub("", old_row["note"]).strip()
    if est_old is not None and abs(float(est_old) - est_new) > 0.01:
        if frozen:
            # the Est column stays at the planned figure -- see make_tasks
            mark = f"est mới {est_new:.2f}h, giữ {float(est_old):.2f}h vì đã {old_row['status']} ({today})"
        else:
            mark = f"est {float(est_old):.2f}h → {est_new:.2f}h ({today})"
        note = f"{note} | {mark}" if note else mark
    return note


def make_tasks(estimates, cfg, old):
    today = date.today().isoformat()
    labels = estimates["phase_labels"]
    tasks, changes = [], []

    for mod in estimates["modules"]:
        module = mod["module"]
        meta = f"{mod['system']}/{mod['complexity']}/{mod['test_cases']} TC" + \
               ("" if mod["has_requirement"] else " · ⚠️ chưa có requirement, est là placeholder")
        for p in (1, 2, 3, 4):
            est = mod["phases"][str(p)]
            old_row = old.get((module, p))
            est_old = old_row["est"] if old_row else None
            if est_old is not None and abs(float(est_old) - est) > 0.01:
                changes.append({"module": module, "phase": p,
                                "est_old": round(float(est_old), 2), "est_new": est,
                                "delta": round(est - float(est_old), 2),
                                "status": old_row["status"],
                                "applied_to_est_column":
                                    old_row["status"] not in FROZEN_STATUSES})
            frozen = bool(old_row and old_row["status"] in FROZEN_STATUSES)
            # Est for finished work stays at the figure it was planned with: the
            # point of the column is Variance = actual - what we predicted, and
            # comparing today's estimate against yesterday's actual measures
            # nothing. The new estimate is recorded in the Note instead.
            est_reported = float(est_old) if (frozen and est_old is not None) else est
            task = {
                "module": module,
                "phase": labels[str(p)],
                "phase_order": p,
                "tester": pick_tester(cfg, module, p, old_row),
                "effort_hours": est_reported,
                "remaining_hours": remaining_hours(est, old_row),
                "frozen": frozen,
                "frozen_start": old_row["plan_start"] if frozen else None,
                "frozen_end": old_row["plan_end"] if frozen else None,
                "status": old_row["status"] if old_row else "TODO",
                "note": build_note(old_row, meta if p == 1 else "", est_old, est, today, frozen),
            }
            for key in CARRY:
                task[key] = old_row[key] if old_row else None
            tasks.append(task)

    # rows the new estimate no longer covers: drop the untouched ones, keep any
    # that already carry recorded work rather than deleting evidence
    known = {(t["module"], t["phase_order"]) for t in tasks}
    dropped, kept = [], []
    for (module, p), row in sorted(old.items()):
        if (module, p) in known:
            continue
        has_work = row["status"] != "TODO" or any(row[k] not in (None, "") for k in CARRY)
        (kept if has_work else dropped).append(module)
        if has_work:
            tasks.append({
                "module": module, "phase": row["phase"], "phase_order": p,
                "tester": row["tester"] or "?", "effort_hours": row["est"] or 0,
                "remaining_hours": 0.0, "frozen": True,
                "frozen_start": row["plan_start"], "frozen_end": row["plan_end"],
                "status": row["status"],
                "note": (row["note"] + " | ⚠️ không còn trong estimate hiện tại").strip(" |"),
                **{k: row[k] for k in CARRY},
            })
    return tasks, changes, sorted(set(dropped)), sorted(set(kept))


def calibration(old):
    """Actual vs Est per phase over finished rows -- the re-estimate input."""
    per_phase = {}
    for (_module, p), row in old.items():
        if row["status"] != "DONE":
            continue
        est, act = row["est"], row["actual_hours"]
        if not isinstance(est, (int, float)) or not isinstance(act, (int, float)):
            continue
        agg = per_phase.setdefault(str(p), {"rows": 0, "est_h": 0.0, "actual_h": 0.0})
        agg["rows"] += 1
        agg["est_h"] = round(agg["est_h"] + est, 2)
        agg["actual_h"] = round(agg["actual_h"] + act, 2)
    for agg in per_phase.values():
        agg["ratio"] = round(agg["actual_h"] / agg["est_h"], 3) if agg["est_h"] else None
    return per_phase


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--estimates", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--old")
    ap.add_argument("--report")
    args = ap.parse_args()

    estimates = json.load(open(args.estimates, encoding="utf-8"))
    cfg = json.load(open(args.config, encoding="utf-8"))
    old = read_old(args.old) if args.old and os.path.exists(args.old) else {}

    tasks, changes, dropped, kept = make_tasks(estimates, cfg, old)

    out = {
        "project_name": cfg.get("project_name", "Test Schedule"),
        "start_date": cfg["start_date"],
        "daily_capacity_hours": cfg.get("daily_capacity_hours", 6.5),
        "work_days": cfg.get("work_days", [0, 1, 2, 3, 4]),
        "holidays": cfg.get("holidays", []),
        "tasks": tasks,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    report = {
        "status": "ok",
        "old_rows_read": len(old),
        "tasks_written": len(tasks),
        "frozen_tasks": sum(1 for t in tasks if t["frozen"]),
        "est_changes": changes,
        "dropped_modules": dropped,
        "kept_out_of_scope_with_work": kept,
        "calibration_by_phase": calibration(old),
    }
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

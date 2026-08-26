#!/usr/bin/env python3
"""
Turn a flat list of QA tasks (module, phase, tester, effort in hours) into dated
schedule rows, respecting:

  1. Each module's 4 phases run in order (phase N can't start before phase N-1
     of the SAME module has finished).
  2. No tester is scheduled for more than `daily_capacity_hours` (default 6.5)
     of work on any single calendar day, even if they're juggling tasks from
     several modules at once.

A task that doesn't fit in one day is automatically split across consecutive
working days for that tester.

FROZEN TASKS: a task carrying "frozen": true keeps the dates it already has
(frozen_start / frozen_end) and consumes no capacity. sync_schedule.py sets this
for rows already DONE or CANCEL -- re-planning finished work would rewrite
history and destroy the plan-vs-actual comparison. Its frozen_end still gates
the next phase of the same module.

PARTIAL PROGRESS: "remaining_hours" overrides effort_hours for capacity purposes,
so a DOING task at 60% only takes its leftover 40% of a tester's day.
effort_hours is still what lands in the Est (h) column.

Usage:
    python3 schedule_capacity.py <tasks.json> <rows.json>

tasks.json shape:
{
  "project_name": "Optional title",
  "start_date": "2026-08-24",
  "daily_capacity_hours": 6.5,
  "work_days": [0, 1, 2, 3, 4],       // Mon=0 .. Sun=6, default Mon-Fri
  "holidays": ["2026-09-02"],          // optional, ISO dates to skip
  "tasks": [
    {
      "module": "Login",
      "phase": "1. Phan tich yeu cau & Confirm Q&A",
      "phase_order": 1,               // 1-4, sequences phases within a module
      "tester": "Lan",
      "effort_hours": 4,
      "remaining_hours": 1.6,         // optional, defaults to effort_hours
      "frozen": false,                // optional, see above
      "frozen_start": null,
      "frozen_end": null,
      "actual_start": null,           // carried through untouched
      "actual_end": null,
      "actual_hours": null,
      "pct_done": null,
      "status": "TODO",               // optional, defaults TODO
      "note": ""                      // optional
    },
    ...
  ]
}

Writes rows.json in the schema build_schedule.py expects, with project_name
carried through.
"""
import json
import sys
from datetime import datetime, timedelta

EPS = 1e-9

# fields copied from task to row without the scheduler touching them
PASSTHROUGH = ("actual_start", "actual_end", "actual_hours", "pct_done")


def parse_date(s):
    if s in (None, ""):
        return None
    return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()


def is_workday(d, work_days, holidays):
    return d.weekday() in work_days and d.isoformat() not in holidays


def next_workday(d, work_days, holidays):
    d = d + timedelta(days=1)
    while not is_workday(d, work_days, holidays):
        d += timedelta(days=1)
    return d


def first_workday_on_or_after(d, work_days, holidays):
    while not is_workday(d, work_days, holidays):
        d += timedelta(days=1)
    return d


def schedule(data, allocation=None):
    """Date the tasks. Pass a list as `allocation` to receive the day-by-day
    ledger of hours charged to each tester -- the daily-capacity rule can then be
    asserted against what was actually charged, instead of being inferred from
    start/end dates (a greedy allocator does not spread a task evenly across the
    days it spans, so inference gets it wrong)."""
    start_date = parse_date(data["start_date"])
    daily_cap = float(data.get("daily_capacity_hours", 6.5))
    work_days = set(data.get("work_days", [0, 1, 2, 3, 4]))
    holidays = set(data.get("holidays", []))
    tasks = data["tasks"]

    start_date = first_workday_on_or_after(start_date, work_days, holidays)

    by_module = {}
    for i, t in enumerate(tasks):
        t["_idx"] = i
        t.setdefault("effort_hours", 0)
        t["_remaining"] = float(t.get("remaining_hours", t["effort_hours"]))
        t["_start"] = None
        t["_end"] = None
        if t.get("frozen"):
            # keep the dates this row already had; fall back to project start when
            # a cancelled row never had any, so dependents aren't blocked forever
            t["_start"] = parse_date(t.get("frozen_start")) or start_date
            t["_end"] = parse_date(t.get("frozen_end")) or t["_start"]
            t["_remaining"] = 0.0
        by_module.setdefault(t["module"], {})[t["phase_order"]] = t

    def dependency(t):
        return by_module.get(t["module"], {}).get(t["phase_order"] - 1)

    def earliest_start(t):
        dep = dependency(t)
        if dep is None:
            return start_date
        if dep["_end"] is not None:
            # a frozen predecessor that ran late must not drag its successor
            # back before the project start
            return max(next_workday(dep["_end"], work_days, holidays), start_date)
        return None  # dependency not finished yet -> not ready

    current_day = start_date
    days_iterated = 0
    max_days = 3650  # safety valve against bad input (e.g. circular deps)

    while any(t["_remaining"] > EPS for t in tasks) and days_iterated < max_days:
        if is_workday(current_day, work_days, holidays):
            cap_left = {}
            ready_today = []
            for t in tasks:
                if t["_remaining"] <= EPS:
                    continue
                es = earliest_start(t)
                if es is None or es > current_day:
                    continue
                ready_today.append(t)
            ready_today.sort(key=lambda t: t["_idx"])

            for t in ready_today:
                tester = t["tester"]
                cap_left.setdefault(tester, daily_cap)
                if cap_left[tester] <= EPS:
                    continue
                if t["_start"] is None:
                    t["_start"] = current_day
                consume = min(t["_remaining"], cap_left[tester])
                t["_remaining"] -= consume
                cap_left[tester] -= consume
                if allocation is not None:
                    allocation.append({"date": current_day.isoformat(), "tester": tester,
                                       "module": t["module"], "phase_order": t["phase_order"],
                                       "hours": round(consume, 6)})
                if t["_remaining"] <= EPS:
                    t["_end"] = current_day

        current_day += timedelta(days=1)
        days_iterated += 1

    unscheduled = [t for t in tasks if t["_end"] is None]

    rows = []
    for t in sorted(tasks, key=lambda t: t["_idx"]):
        row = {
            "module": t["module"],
            "phase": t["phase"],
            "tester": t["tester"],
            "effort_hours": t["effort_hours"],
            "start_date": t["_start"].isoformat() if t["_start"] else None,
            "end_date": t["_end"].isoformat() if t["_end"] else None,
            "status": t.get("status", "TODO"),
            "note": t.get("note", ""),
        }
        for key in PASSTHROUGH:
            row[key] = t.get(key)
        rows.append(row)

    return rows, unscheduled


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 schedule_capacity.py <tasks.json> <rows.json>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    rows, unscheduled = schedule(data)

    out = {
        "project_name": data.get("project_name", "Test Schedule"),
        "daily_capacity_hours": data.get("daily_capacity_hours", 6.5),
        "rows": rows,
    }
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    result = {"status": "ok" if not unscheduled else "incomplete", "rows_written": len(rows)}
    if unscheduled:
        result["unscheduled_count"] = len(unscheduled)
        result["unscheduled_modules"] = sorted({t["module"] for t in unscheduled})
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

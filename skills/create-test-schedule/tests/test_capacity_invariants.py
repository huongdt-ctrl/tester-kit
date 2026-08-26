#!/usr/bin/env python3
"""
Guards the scheduler's two hard rules, which every other feature is built on top
of and which a refactor of the day loop can silently break:

  1. No tester is allocated more than daily_capacity_hours on any working day.
  2. Phase N of a module never starts before phase N-1 of that module ends.

Plus the invariants added for the sync flow: frozen tasks keep their dates and
consume no capacity; remaining_hours drives allocation while effort_hours stays
the reported estimate.

    python3 tests/test_capacity_invariants.py
"""
import os
import sys
from collections import defaultdict
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

import schedule_capacity as sc

CAP = 6.5
PHASES = ["1. Analyse", "2. Gen TC", "3. Execute", "4. Verify"]

failures = []


def check(name, condition, detail=""):
    print(f"{'PASS' if condition else 'FAIL'}  {name}" + (f"  -- {detail}" if detail and not condition else ""))
    if not condition:
        failures.append(name)


def make_tasks(specs, start="2026-08-24"):
    """specs: list of (module, phase_order, tester, hours, extra_dict)"""
    tasks = []
    for module, order, tester, hours, extra in specs:
        task = {"module": module, "phase": PHASES[order - 1], "phase_order": order,
                "tester": tester, "effort_hours": hours, "status": "TODO"}
        task.update(extra)
        tasks.append(task)
    return {"start_date": start, "daily_capacity_hours": CAP,
            "work_days": [0, 1, 2, 3, 4], "holidays": [], "tasks": tasks}


def daily_load(allocation):
    """Hours actually charged per (tester, day), straight from the scheduler."""
    load = defaultdict(float)
    for entry in allocation:
        load[(entry["tester"], entry["date"])] += entry["hours"]
    return load


def test_capacity_never_exceeded_across_interleaved_modules():
    # Arrange: two testers, four modules whose phases compete for the same days
    specs = []
    for i, module in enumerate(["m1", "m2", "m3", "m4"]):
        for order, hours in enumerate([2.5, 3.0, 7.0, 4.0], start=1):
            tester = "A" if order <= 2 else "B"
            specs.append((module, order, tester, hours, {}))
    data = make_tasks(specs)

    # Act
    allocation = []
    rows, unscheduled = sc.schedule(data, allocation=allocation)

    # Assert
    check("test_capacity_all_tasks_get_dates", not unscheduled, f"{len(unscheduled)} unscheduled")
    over = {k: round(v, 4) for k, v in daily_load(allocation).items() if v > CAP + 1e-6}
    check("test_capacity_no_tester_day_exceeds_6h5", not over, str(over))
    total_in = sum(t["effort_hours"] for t in data["tasks"])
    total_out = sum(r["effort_hours"] for r in rows)
    check("test_capacity_total_effort_is_conserved", abs(total_in - total_out) < 1e-6,
          f"{total_in} vs {total_out}")


def test_phase_order_is_respected_within_each_module():
    specs = [(m, o, "A" if o <= 2 else "B", 3.0, {})
             for m in ("m1", "m2") for o in (1, 2, 3, 4)]
    rows, _ = sc.schedule(make_tasks(specs))
    by_key = {(r["module"], int(r["phase"][0])): r for r in rows}

    violations = []
    for module in ("m1", "m2"):
        for order in (2, 3, 4):
            prev_end = sc.parse_date(by_key[(module, order - 1)]["end_date"])
            this_start = sc.parse_date(by_key[(module, order)]["start_date"])
            if this_start <= prev_end:
                violations.append(f"{module} p{order}: {this_start} <= {prev_end}")
    check("test_phase_order_next_phase_starts_after_previous_ends", not violations, str(violations))


def test_frozen_task_keeps_dates_and_frees_capacity():
    # Arrange: phase 1 already done on dates that predate the planning window
    specs = [
        ("m1", 1, "A", 6.0, {"frozen": True, "frozen_start": "2026-08-17",
                             "frozen_end": "2026-08-18", "status": "DONE",
                             "remaining_hours": 0.0}),
        ("m1", 2, "A", 6.0, {}),
        ("m2", 1, "A", 6.0, {}),
    ]
    data = make_tasks(specs, start="2026-08-24")
    allocation = []
    rows, unscheduled = sc.schedule(data, allocation=allocation)
    by_key = {(r["module"], int(r["phase"][0])): r for r in rows}
    charged_frozen = [a for a in allocation if (a["module"], a["phase_order"]) == ("m1", 1)]

    check("test_frozen_task_dates_survive_scheduling",
          by_key[("m1", 1)]["start_date"] == "2026-08-17"
          and by_key[("m1", 1)]["end_date"] == "2026-08-18",
          f"{by_key[('m1', 1)]['start_date']} -> {by_key[('m1', 1)]['end_date']}")
    # its successor must not be dragged back before the planning window
    check("test_frozen_predecessor_does_not_pull_successor_before_start_date",
          sc.parse_date(by_key[("m1", 2)]["start_date"]) >= date(2026, 8, 24),
          by_key[("m1", 2)]["start_date"])
    # tester A had 12h of live work; a frozen 6h task must not eat into the cap
    check("test_frozen_task_is_never_charged_to_a_day", not charged_frozen, str(charged_frozen))
    check("test_frozen_task_consumes_no_capacity", not unscheduled
          and by_key[("m1", 2)]["start_date"] == "2026-08-24"
          and by_key[("m2", 1)]["start_date"] == "2026-08-24",
          f"{by_key[('m1', 2)]['start_date']} / {by_key[('m2', 1)]['start_date']}")


def test_remaining_hours_shortens_a_partially_done_task():
    # 6h task at 75% done -> 1.5h left, so it finishes inside one day
    specs = [("m1", 1, "A", 6.0, {"remaining_hours": 1.5, "status": "DOING", "pct_done": 75})]
    rows, _ = sc.schedule(make_tasks(specs))
    row = rows[0]
    check("test_remaining_hours_task_finishes_in_one_day",
          row["start_date"] == row["end_date"] == "2026-08-24",
          f"{row['start_date']} -> {row['end_date']}")
    check("test_remaining_hours_est_column_still_reports_full_estimate",
          row["effort_hours"] == 6.0, str(row["effort_hours"]))


if __name__ == "__main__":
    test_capacity_never_exceeded_across_interleaved_modules()
    test_phase_order_is_respected_within_each_module()
    test_frozen_task_keeps_dates_and_frees_capacity()
    test_remaining_hours_shortens_a_partially_done_task()
    print(f"\n{len(failures)} failure(s)" + (f": {failures}" if failures else ""))
    sys.exit(1 if failures else 0)

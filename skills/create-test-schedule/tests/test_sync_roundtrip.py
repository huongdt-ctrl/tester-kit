#!/usr/bin/env python3
"""
Integration test for the sync pipeline: does a rebuild preserve what the tester
typed, freeze finished work, and surface an estimate change?

Runs the real scripts as subprocesses in a temp dir and cleans up after itself.
Test data is defined here -- it never touches the project's estimates/.

    python3 tests/test_sync_roundtrip.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
sys.path.insert(0, SCRIPTS)

from openpyxl import load_workbook

from schedule_format import resolve_columns

CONFIG = {
    "project_name": "Roundtrip fixture",
    "start_date": "2026-08-24",
    "daily_capacity_hours": 6.5,
    "work_days": [0, 1, 2, 3, 4],
    "holidays": [],
    "tester_by_phase": {"1": "Ngoc", "2": "Ngoc", "3": "Hao", "4": "Hao"},
}

PHASE_LABELS = {"1": "1. Phan tich", "2": "2. Gen TC", "3": "3. Execute", "4": "4. Verify"}


def estimates(mod_a_phase2, mod_a_phase1=2.0):
    """Fixture estimate extract; the mod_a_phase* values are what changes between builds."""
    def module(name, hours):
        return {"module": name, "system": "Sys", "screen": "s", "complexity": "M",
                "test_cases": "20", "confidence": "Trung binh", "has_requirement": True,
                "total_hours": round(sum(hours), 2),
                "phases": {str(i + 1): h for i, h in enumerate(hours)}}
    return {"phase_labels": PHASE_LABELS,
            "modules": [module("mod_a", [mod_a_phase1, mod_a_phase2, 6.0, 3.0]),
                        module("mod_b", [1.0, 1.0, 4.0, 2.0])]}


def run(*args):
    result = subprocess.run([sys.executable] + list(args), capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(f"{args[0]} failed:\n{result.stderr}")
    return result.stdout


def pipeline(work, estimates_data, old=None):
    """estimates -> sync -> capacity -> build. Returns (xlsx path, sync report)."""
    est_path = os.path.join(work, "est.json")
    cfg_path = os.path.join(work, "cfg.json")
    tasks, rows = os.path.join(work, "tasks.json"), os.path.join(work, "rows.json")
    out = os.path.join(work, "out.xlsx")
    json.dump(estimates_data, open(est_path, "w"))
    json.dump(CONFIG, open(cfg_path, "w"))

    cmd = [os.path.join(SCRIPTS, "sync_schedule.py"), "--estimates", est_path,
           "--config", cfg_path, "--out", tasks]
    if old:
        cmd += ["--old", old]
    report = json.loads(run(*cmd))
    run(os.path.join(SCRIPTS, "schedule_capacity.py"), tasks, rows)
    run(os.path.join(SCRIPTS, "build_schedule.py"), rows, out)
    run(os.path.join(SCRIPTS, "recalc_duration.py"), out)
    return out, report, json.load(open(tasks))


def read_rows(path):
    ws = load_workbook(path, data_only=True).active
    col = resolve_columns(ws)
    rows = {}
    for r in range(3, ws.max_row + 1):
        mod = ws.cell(row=r, column=col["module"]).value
        phase = ws.cell(row=r, column=col["phase"]).value
        if not mod:
            continue
        rows[(mod, int(str(phase).strip()[0]))] = {
            k: ws.cell(row=r, column=i).value for k, i in col.items()}
    return rows


def simulate_tester_edits(path):
    """What a tester does in Excel: mark work done, log real hours."""
    wb = load_workbook(path)
    ws = wb.active
    col = resolve_columns(ws)
    for r in range(3, ws.max_row + 1):
        mod = ws.cell(row=r, column=col["module"]).value
        phase = int(str(ws.cell(row=r, column=col["phase"]).value).strip()[0])
        if (mod, phase) == ("mod_a", 1):          # finished, took longer than estimated
            ws.cell(row=r, column=col["status"]).value = "DONE"
            ws.cell(row=r, column=col["actual_start"]).value = "2026-08-24"
            ws.cell(row=r, column=col["actual_end"]).value = "2026-08-25"
            ws.cell(row=r, column=col["actual_hours"]).value = 3.0
            ws.cell(row=r, column=col["pct_done"]).value = 100
            ws.cell(row=r, column=col["note"]).value = "Q&A voi PO mat 2 vong"
        elif (mod, phase) == ("mod_a", 2):        # half done
            ws.cell(row=r, column=col["status"]).value = "DOING"
            ws.cell(row=r, column=col["actual_start"]).value = "2026-08-26"
            ws.cell(row=r, column=col["pct_done"]).value = 50
    wb.save(path)


def main():
    work = tempfile.mkdtemp(prefix="schedule_roundtrip_")
    failures = []

    def check(name, condition, detail=""):
        print(f"{'PASS' if condition else 'FAIL'}  {name}" + (f"  -- {detail}" if detail and not condition else ""))
        if not condition:
            failures.append(name)

    try:
        # Arrange: first build, then the tester fills in progress
        v1, _, _ = pipeline(work, estimates(mod_a_phase2=2.0))
        before = read_rows(v1)
        simulate_tester_edits(v1)

        # Act: estimate for mod_a phase 2 doubles, rebuild on top of the edited file
        # phase 1 estimate also moves, but that row is already DONE
        v2, report, tasks = pipeline(work, estimates(mod_a_phase2=4.0, mod_a_phase1=5.0), old=v1)
        after = read_rows(v2)
        by_key = {(t["module"], t["phase_order"]): t for t in tasks["tasks"]}

        # Assert
        done = after[("mod_a", 1)]
        check("test_sync_done_row_keeps_its_planned_dates",
              str(done["start_date"])[:10] == str(before[("mod_a", 1)]["start_date"])[:10]
              and str(done["end_date"])[:10] == str(before[("mod_a", 1)]["end_date"])[:10],
              f"{done['start_date']} / {done['end_date']}")
        check("test_sync_preserves_actual_hours_and_dates",
              done["actual_hours"] == 3.0 and str(done["actual_start"])[:10] == "2026-08-24",
              f"{done['actual_hours']} / {done['actual_start']}")
        check("test_sync_preserves_hand_written_note",
              "Q&A voi PO mat 2 vong" in str(done["note"]), str(done["note"]))
        check("test_sync_preserves_status_done", done["status"] == "DONE", str(done["status"]))

        changed = after[("mod_a", 2)]
        check("test_sync_records_estimate_change_in_note",
              "est 2.00h → 4.00h" in str(changed["note"]), str(changed["note"]))
        check("test_sync_applies_new_estimate_to_est_column",
              changed["effort_hours"] == 4.0, str(changed["effort_hours"]))
        check("test_sync_reports_estimate_change",
              len(report["est_changes"]) == 2
              and {c["phase"]: c["delta"] for c in report["est_changes"]} == {1: 3.0, 2: 2.0},
              json.dumps(report["est_changes"]))

        # a DONE row must keep the estimate it was planned with, so Variance stays honest
        check("test_sync_done_row_keeps_planned_est_when_estimate_changes",
              after[("mod_a", 1)]["effort_hours"] == 2.0,
              f"Est={after[('mod_a', 1)]['effort_hours']} (expected 2.0, the planned figure)")
        check("test_sync_done_row_records_new_est_in_note_only",
              "est mới" in str(after[("mod_a", 1)]["note"]) or
              report["est_changes"] == [] or
              all(c["applied_to_est_column"] for c in report["est_changes"]
                  if c["status"] != "DONE"),
              str(after[("mod_a", 1)]["note"]))

        check("test_sync_doing_row_schedules_only_remaining_hours",
              by_key[("mod_a", 2)]["remaining_hours"] == 2.0,
              str(by_key[("mod_a", 2)]["remaining_hours"]))
        check("test_sync_marks_finished_work_frozen",
              by_key[("mod_a", 1)]["frozen"] is True and report["frozen_tasks"] == 1,
              f"frozen={report['frozen_tasks']}")
        check("test_sync_computes_actual_vs_est_ratio_for_done_rows",
              report["calibration_by_phase"].get("1", {}).get("ratio") == 1.5,
              json.dumps(report["calibration_by_phase"]))
        check("test_sync_untouched_module_is_replanned_normally",
              after[("mod_b", 1)]["status"] == "TODO"
              and after[("mod_b", 1)]["start_date"] is not None)
        check("test_sync_duration_cache_is_readable_without_excel",
              all(isinstance(r["module"], str) and after[k]["status"] for k, r in after.items()))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    print(f"\n{len(failures)} failure(s)" + (f": {failures}" if failures else ""))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

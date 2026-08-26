---
name: create-test-schedule
description: Build an Excel (.xlsx) test activity schedule for QA testers, covering the full test cycle for each feature/module (requirement analysis & Q&A confirmation, test case generation & review, test execution & bug logging, bug verification/retest) with dates, tester assignment, status, and actual-vs-estimate tracking. Use this whenever the user asks to create, build, or update a "lich test", "test schedule", "test plan theo lich", or a schedule/timeline for testers or QA activities -- even if they don't spell out every column, or if they only give an estimate file and a list of testers. Also use it to re-plan an existing schedule after estimates changed or after testers logged progress ("cap nhat lich test", "re-est lai lich"). This is a SCHEDULE (who does what test activity, when), not a test-case document -- do not confuse this with writing actual test cases/test scripts. Trigger even when the request is short, like "tạo lịch test cho tester" or "làm schedule test cho sprint này".
---

# QA Test Schedule Generator

**Deliverable:** one `.xlsx` file. Each row = one tester doing one test phase on
one module, with planned dates, actuals, and status. Not a test-case document,
not a test plan narrative.

**Fixed rule:** no tester exceeds **6.5 working hours/day**, even across
multiple modules. Dates are computed from this constraint, not picked by hand.

**Second fixed rule:** never overwrite what a tester typed. The four ACTUAL
columns, Status, and hand-written notes are theirs; rows already `DONE` keep
their planned dates. `sync_schedule.py` enforces both — use it instead of
rebuilding from scratch whenever a schedule already exists.

**Pipeline:**

```
estimates/  --extract_estimates.py-->  estimates.json
                                            |
            existing .xlsx (if any) ---> sync_schedule.py <--- config.json
                                            |
                                        tasks.json
                                            |
                                   schedule_capacity.py
                                            |
                                         rows.json
                                            |
                                    build_schedule.py
                                            |
                                    recalc_duration.py --> deliver
```

---

## 1. The four test phases

Default phase list, in order, for every module:

| # | Phase label | What it covers |
|---|---|---|
| 1 | Phân tích yêu cầu & Confirm Q&A | Requirement analysis, clarifying Q&A with stakeholders |
| 2 | Gen & Review Test Case | Generate test cases, then review/update them |
| 3 | Execute Test Case & Log Bug | Run test cases, log defects |
| 4 | Verify Bug | Retest fixed defects |

If the user names different stages (smoke test, UAT, regression, perf test),
use theirs instead — this list is the default, not a hard requirement.

## 2. Gather the inputs

| Input | Where to look first | Fallback |
|---|---|---|
| Modules + effort (hours) | `estimates/<module>/estimate_summary.md` from the `estimate-test` skill — run `extract_estimates.py` | An estimate `.xlsx`/`.md` given in chat; else ask for module list + hours |
| Existing schedule | `schedules/*.xlsx` — pass the newest as `--old` | None on a first build |
| Tester assignment | Staffing plan in chat or a file | Ask who's on the team and whether assignment is by module or by phase |

Notes:
- Effort in the estimate file is already in **hours** — no unit conversion.
- **Read Excel with `openpyxl`, never `pandas` or `markitdown`** — neither is
  installed in this workspace. Use `data_only=True` to read cached formula values.
- Don't assume one tester owns all 4 phases of a module — execution and
  verify-bug commonly go to a different person than analysis. Confirm with
  the user if unclear.
- If a start date isn't given, use the estimate file's date or today.
- Carry the estimate's own confidence warnings into the Note column. A module
  with no requirement package has a placeholder estimate, and a schedule built on
  it must not read as a commitment.

## 3. Extract the estimates

```bash
python3 scripts/extract_estimates.py <estimates_dir> <estimates.json> [--only mod1,mod2]
```

Maps the 18 `estimate-test` activity codes onto the 4 phases (see `PHASE_MAP`)
and scales each phase so the four sum to the module's TOTAL — the 15% buffer
gets distributed rather than dropped. Modules come out sorted biggest-first so
the critical path gets scheduling priority.

Check the printed `phase_totals` against the estimate's own rollup before
continuing. `warnings` lists activity codes it couldn't place; an unmapped code
means its hours were silently excluded — fix `PHASE_MAP`, don't ignore it.

## 4. Write `config.json` and sync

```json
{
  "project_name": "Test Schedule — <project/release name>",
  "start_date": "YYYY-MM-DD",
  "daily_capacity_hours": 6.5,
  "work_days": [0, 1, 2, 3, 4],
  "holidays": [],
  "tester_by_phase": {"1": "Lan", "2": "Lan", "3": "Hao", "4": "Hao"},
  "tester_overrides": {"event_edit_schedule": {"3": "Lan"}}
}
```

| Field | Rule |
|---|---|
| `tester_by_phase` | Who owns each phase by default. Same tester can span modules — the scheduler interleaves without exceeding the daily cap. |
| `tester_overrides` | Per-module, per-phase exception. Use for rebalancing rather than editing the sheet by hand. |
| `work_days` | Default Mon-Fri (`[0,1,2,3,4]`, Mon=0). Change only if the user specifies otherwise. |
| `holidays` | Optional list of ISO dates to skip. |

```bash
python3 scripts/sync_schedule.py --estimates <estimates.json> --config <config.json> \
    --out <tasks.json> [--old <existing.xlsx>] [--report <report.json>]
```

Omit `--old` only on a first build. With it, the script:

- carries Status, Actual Start/End, Actual (h), % Done and hand-written notes forward;
- emits rows that are `DONE`/`CANCEL` as **frozen** tasks — dates kept, capacity freed;
- charges a `DOING` row only its leftover hours (`est × (1 − %done)`);
- writes `est 6.07h → 8.20h (date)` into the Note of any row whose estimate moved;
- **keeps Est (h) at the planned figure on `DONE`/`CANCEL` rows** even when the
  estimate moved, recording the new number in the Note instead — `Variance` must
  compare the actual against what was predicted, not against a later revision;
- keeps out-of-scope rows that already carry logged work, and reports the rest as dropped.

**Read the report before building.** `est_changes` is the answer to "what moved
since last time"; `calibration_by_phase` gives Actual÷Est per phase over
completed rows — that ratio is the feedback the `estimate-test` model needs, so
surface it to the user rather than burying it.

## 5. Run the scheduler

```bash
python3 scripts/schedule_capacity.py <tasks.json> <rows.json>
```

Check the printed JSON:
- `"status": "ok"` → every task got dates, proceed.
- `"status": "incomplete"` → a task never got scheduled. Almost always a
  `phase_order` that doesn't exist for that module, or a dependency cycle.
  Fix the input and rerun — never hand-patch `rows.json`.

Pass a list as `allocation=` when calling `schedule()` from Python to get the
day-by-day ledger of hours charged per tester. Assert the capacity rule against
that ledger, not against start/end dates: the allocator is greedy, so a 7h task
spanning two days is 6.5h + 0.5h, and inferring an even split reports phantom
violations.

## 6. Build the Excel file

```bash
python3 scripts/build_schedule.py <rows.json> <output.xlsx>
```

15 columns in two groups — layout lives in `scripts/schedule_format.py`, the one
place to change it:

| Group | Columns | Who writes them |
|---|---|---|
| Plan (blue header) | No, Module / Feature, Test Phase, Tester, Est (h), Plan Start, Plan End, Duration (days) | This skill |
| Actual (green header, tinted cells) | Actual Start, Actual End, Actual (h), % Done, Variance (h) | The tester, in Excel |
| | Status, Note | Either |

`Duration (days)` (`=G-F+1`) and `Variance (h)` (`=IF(K="","",K-E)`) are
**formulas** — never hardcode them. Status has a dropdown + colour coding;
% Done is validated to 0-100. Panes freeze at `E3` so module/phase/tester stay
visible while scrolling to the actuals.

Plan and actual sit side by side deliberately: `Variance (h)` is the only thing
that makes the next estimate better than the last one. Overwriting Plan dates
with real ones destroys it.

## 7. Recalculate (mandatory)

openpyxl writes formulas without cached values, so `Duration` reads blank
until recalculated:

```bash
python3 scripts/recalc_duration.py <output.xlsx>
```

Use the platform script instead when it's present — it recalculates every
formula, not just `Duration`:

```bash
python3 /mnt/skills/public/xlsx/scripts/recalc.py <output.xlsx>
```

Confirm `"status": "success"` and `"total_errors": 0` before delivering. An
error here is almost always a bad date string — fix the row, not the script.
`Variance (h)` stays uncached by design: it is blank until a tester enters
Actual (h), and Excel/Sheets recalculate it on open (`fullCalcOnLoad` is set).

## 8. Deliver

Write the file to `schedules/` (or `/mnt/user-data/outputs/` + `present_files`
when that path exists). State assumptions in 2-3 sentences — start date used,
how testers were split across phases, and anything the estimate flagged as low
confidence. Don't restate the table in chat; the file speaks for itself.

Report the imbalance if one tester's total is far above the other's. It decides
the end date, and the user is the one who can approve a rebalance.

## Tests

```bash
python3 tests/test_capacity_invariants.py   # daily cap, phase order, frozen tasks
python3 tests/test_sync_roundtrip.py        # actuals survive a rebuild, est diffs surface
```

Run both after touching any script here. They use their own fixtures, write only
to a temp dir, and clean up after themselves.

#!/usr/bin/env python3
"""
Read the per-module estimate reports produced by the `estimate-test` skill and
return effort in hours, split into the four test phases this skill schedules.

Input: a directory holding one sub-directory per module, each containing an
`estimate_summary.md` with a "18 dòng" activity table (columns: # | Code |
Function | Cx | Volume | Đơn vị | Base | Mult | Adjusted).

The 18 activity codes are grouped into phases via PHASE_MAP. Each phase total
is scaled up so the four phases sum to the module's **TOTAL** row -- that
distributes the 15% buffer proportionally instead of dropping it.

Usage:
    python3 extract_estimates.py <estimates_dir> <out.json> [--only mod1,mod2]
"""
import argparse
import glob
import json
import os
import re

# 18 activity codes from estimate-test -> the 4 phases in SKILL.md section 1.
# S1/S2 (environment + shared test data) sit in phase 3: whoever executes needs
# the environment standing before they can run a case.
PHASE_MAP = {
    "G1": 1, "A1": 1, "G2": 1, "A2": 1, "A2b": 1,   # ticket, requirement analysis, Q&A rounds
    "G3": 2, "A3": 2,                                # gen test case, review test case
    "S1": 3, "S2": 3, "A4": 3, "G4": 3, "A4b": 3,    # env + data setup, execute, log bug
    "A5": 4, "S3": 4, "S4": 4, "R1": 4, "G5": 4, "A6": 4,  # verify, follow-up, regression, rework, report
}

PHASE_LABEL = {
    1: "1. Phân tích yêu cầu & Confirm Q&A",
    2: "2. Gen & Review Test Case",
    3: "3. Execute Test Case & Log Bug",
    4: "4. Verify Bug",
}

ACTIVITY_ROW = re.compile(r"^\|\s*\d+\s*\|\s*([A-Z]\d[a-z]?)\s*\|.*\|\s*([\d.]+)\s*\|\s*$", re.M)


def field(text, pattern, default=""):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else default


def parse_module(path):
    module = os.path.basename(os.path.dirname(path))
    text = open(path, encoding="utf-8").read()

    total = float(field(text, r"\| \*\*TOTAL\*\* \| \*\*([\d.]+)\*\*", "0"))
    phases = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    unmapped = []
    for code, adjusted in ACTIVITY_ROW.findall(text):
        phase = PHASE_MAP.get(code)
        if phase is None:
            unmapped.append(code)
            continue
        phases[phase] += float(adjusted)

    raw = sum(phases.values())
    if raw <= 0:
        return None, [f"{module}: no activity rows matched -- check the '18 dòng' table format"]
    # scale so the phases add up to TOTAL (spreads the buffer across phases)
    scale = total / raw
    result = {
        "module": module,
        "system": field(text, r"\| Hệ thống \| (.+?) \|"),
        "screen": field(text, r"\| Màn hình \| (.+?) \|"),
        "complexity": field(text, r"\| Complexity \| \*\*(.+?)\*\*"),
        "test_cases": field(text, r"\| Volume test case \| \*\*([\d.]+)\*\*"),
        "confidence": field(text, r"\| Độ tin cậy \| \*\*(.+?)\*\*"),
        "has_requirement": "✅ có" in text,
        "total_hours": round(total, 2),
        "phases": {str(k): round(v * scale, 2) for k, v in phases.items()},
    }
    warns = [f"{module}: unmapped activity codes {sorted(set(unmapped))}"] if unmapped else []
    return result, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("estimates_dir")
    ap.add_argument("out_json")
    ap.add_argument("--only", help="comma-separated module names to keep")
    args = ap.parse_args()

    keep = set(args.only.split(",")) if args.only else None
    modules, warnings = [], []
    for path in sorted(glob.glob(os.path.join(args.estimates_dir, "*", "estimate_summary.md"))):
        if keep and os.path.basename(os.path.dirname(path)) not in keep:
            continue
        parsed, warns = parse_module(path)
        warnings += warns
        if parsed:
            modules.append(parsed)

    # biggest first: the critical path should get scheduling priority downstream
    modules.sort(key=lambda m: -m["total_hours"])

    out = {"phase_labels": {str(k): v for k, v in PHASE_LABEL.items()}, "modules": modules}
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    summary = {
        "status": "ok" if not warnings else "ok_with_warnings",
        "modules": len(modules),
        "total_hours": round(sum(m["total_hours"] for m in modules), 2),
        "phase_totals": {
            str(p): round(sum(m["phases"][str(p)] for m in modules), 2) for p in (1, 2, 3, 4)
        },
    }
    if warnings:
        summary["warnings"] = warnings
    if keep:
        missing = sorted(keep - {m["module"] for m in modules})
        if missing:
            summary["missing_modules"] = missing
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Argument surface for execute_testcase_cli.py, split out to keep that module
focused on behaviour (dev-rules: file duoi 200 dong).
"""
import argparse

WRITE_OPTIONS = ("remark", "actual", "tested-by", "test-date", "bug-id", "bug-url")
BUG_OPTIONS = ("title", "preconditions", "steps", "test-data", "expected", "actual",
               "tested-by", "test-date", "evidence", "existing-bug-id")


def _common(parser):
    parser.add_argument("--manifest", required=True, help="inputs/test_execution_manifest.yaml")
    parser.add_argument("--profile", required=True, help="configs/test_execution_project_profile.yaml")


def build_parser():
    ap = argparse.ArgumentParser(description="Deterministic I/O helper cho skill execute-testcase")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("preflight", "load-cases"):
        _common(sub.add_parser(name))

    w = sub.add_parser("write-result")
    _common(w)
    w.add_argument("--row", type=int, required=True, help="so dong 1-based trong worksheet")
    w.add_argument("--status", required=True)
    for opt in WRITE_OPTIONS:
        w.add_argument("--" + opt, default="")
    w.add_argument("--reset-target", action="store_true",
                   help="bat dau run moi: quen file dich da chot o run truoc")

    b = sub.add_parser("log-bug")
    _common(b)
    b.add_argument("--tc-id", required=True)
    b.add_argument("--summary", required=True)
    for opt in BUG_OPTIONS:
        b.add_argument("--" + opt, default="")

    return ap

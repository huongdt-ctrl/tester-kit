#!/usr/bin/env python3
"""Entry point duy nhat cua skill bug-analyst. Output LUON la JSON, exit 0/1.

Ba buoc, tach doi rach roi giua may va nguoi:
    collect  -- may: goi tracker, lay bug theo nhan/loai + khoang ngay -> JSON
    build    -- may: clone template, do du lieu, sinh cong thuc, va chart
    verify   -- may: kiem tra config truoc khi goi that
Buoc phan tich (Severity / Cause / Root cause) do AGENT lam giua collect va
build, bang cach sua file JSON. Co y khong nhet vao script: do la phan xet
doan, khong phai I/O xac dinh.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bug_mapper
import cli_io
import workbook_builder as builder
from adapters import TrackerError, build_adapter
from config_loader import effective_config, load_config

# Template di kem skill -> chay duoc ngay khong can config paths.template.
DEFAULT_TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "templates", "template_bug_analysis.xlsx")


def _load(args, need_credentials=True):
    overrides = {"run": {}, "tracker": {}}
    for key in ("phase", "date_from", "date_to"):
        if getattr(args, key, None):
            overrides["run"][key] = getattr(args, key)
    if getattr(args, "system", None):
        overrides["tracker"]["system"] = args.system
    merged, missing, plaintext = load_config(args.profile, args.manifest, overrides)
    if plaintext:
        raise ValueError(
            "Credential ghi plaintext trong config: %s. Chi duoc ghi dang "
            "'env:TEN_BIEN'." % ", ".join(plaintext))
    # Plaintext credential la loi bao mat cua config -> chan MOI lenh, ke ca lenh
    # khong goi mang. Con thieu bien env thi chi chan lenh THAT SU goi tracker:
    # `build` doc file JSON + template tren dia, doi token la chan oan nguoi gen
    # lai bao cao offline.
    if missing and need_credentials:
        raise ValueError("Chua set bien moi truong: %s" % ", ".join(missing))
    return merged


def _run_block(merged):
    run = dict(merged.get("run") or {})
    run["date_from"] = cli_io.validate_date(run.get("date_from"), "--date-from")
    run["date_to"] = cli_io.validate_date(run.get("date_to"), "--date-to")
    if run["date_from"] and run["date_to"] and run["date_from"] > run["date_to"]:
        raise ValueError("--date-from (%s) sau --date-to (%s)"
                         % (run["date_from"], run["date_to"]))
    return run


def cmd_verify(args):
    merged = _load(args)
    adapter = build_adapter(merged)
    return cli_io.emit({"command": "verify", "tracker": adapter.name,
                        "check": adapter.verify(),
                        "config": effective_config(merged)})


def cmd_collect(args):
    merged = _load(args)
    run = _run_block(merged)
    adapter = build_adapter(merged)
    issues = adapter.list_bugs(run.get("date_from"), run.get("date_to"))
    policy = merged.get("mapping") or {}
    rows = bug_mapper.map_all(issues,
                              default_screen=policy.get("default_screen") or "All screen",
                              default_milestone=run.get("phase") or "",
                              priority_map=policy.get("priority_map"))
    payload = {"phase": run.get("phase"), "date_from": run.get("date_from"),
               "date_to": run.get("date_to"), "tracker": adapter.name,
               "collected": len(rows), "rows": rows}
    out = args.out or os.path.join(
        (merged.get("paths") or {}).get("output_root") or ".", "collected_bugs.json")
    cli_io.write_json(out, payload)
    payload_out = {"command": "collect", "tracker": adapter.name,
                   "collected": len(rows), "bugs_file": out,
                   "pending_analysis": bug_mapper.pending_analysis(rows),
                   "next": "Dien Severity / Cause catelogies / Root cause vao "
                           "%s roi chay 'build'." % out}
    if getattr(adapter, "truncated", False):
        payload_out["truncated"] = True
        payload_out["warning"] = (
            "Cham tran phan trang -- tracker VAN con bug chua lay het. Thu hep "
            "khoang ngay hoac tang tracker.page_size roi chay lai.")
    return cli_io.emit(payload_out)


def cmd_build(args):
    merged = _load(args, need_credentials=False) if (args.profile or args.manifest) else {}
    data = cli_io.read_json(args.bugs_file)
    rows = data.get("rows") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError("File %s khong co danh sach bug" % args.bugs_file)
    if not rows and not args.allow_empty:
        # 0 bug gan nhu luon la sai cau hinh (nham label / nham khoang ngay /
        # nham project) chu hiem khi la giai doan sach that -> chan mac dinh,
        # nhung van cho xuat bao cao rong khi user khang dinh dung la vay.
        raise ValueError(
            "File %s khong co dong bug nao. Thuong la do loc sai (label/loai "
            "bug, khoang ngay, project). Neu giai doan that su khong co bug, "
            "them --allow-empty de van xuat bao cao rong." % args.bugs_file)

    phase = args.phase or (data or {}).get("phase") or (merged.get("run") or {}).get("phase")
    date_from = args.date_from or (data or {}).get("date_from")
    date_to = args.date_to or (data or {}).get("date_to")
    paths = merged.get("paths") or {}
    template = args.template or paths.get("template") or DEFAULT_TEMPLATE
    out_path = args.out or os.path.join(
        paths.get("output_root") or ".",
        builder.output_filename(phase, date_from, date_to))

    pending = bug_mapper.pending_analysis(rows)
    if pending and not args.allow_incomplete:
        return cli_io.fail(
            "Con %d bug chua phan tich du (Severity / Cause / Root cause). "
            "Dien tiep hoac them --allow-incomplete de xuat ban thieu."
            % len(pending), pending_analysis=pending)

    report = builder.build(template, out_path, rows, phase=phase,
                           date_from=date_from, date_to=date_to,
                           issues=(data or {}).get("issues"),
                           overwrite=args.overwrite)
    report.update({"command": "build", "phase": phase,
                   "template": template, "pending_analysis": pending})
    return cli_io.emit(report)


def build_parser():
    parser = argparse.ArgumentParser(prog="bug_analyst_cli.py",
                                     description="Thu thap va phan tich bug theo giai doan")
    parser.add_argument("--profile")
    parser.add_argument("--manifest")
    parser.add_argument("--system", choices=("gitlab", "jira", "redmine"))
    parser.add_argument("--phase")
    parser.add_argument("--date-from", dest="date_from")
    parser.add_argument("--date-to", dest="date_to")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("verify", help="Kiem tra config tracker truoc khi goi that")

    collect = sub.add_parser("collect", help="Lay bug tu tracker theo khoang ngay")
    collect.add_argument("--out")

    build_cmd = sub.add_parser("build", help="Clone template va do du lieu vao")
    build_cmd.add_argument("--bugs-file", dest="bugs_file", required=True)
    build_cmd.add_argument("--template")
    build_cmd.add_argument("--out")
    build_cmd.add_argument("--overwrite", action="store_true")
    build_cmd.add_argument("--allow-incomplete", action="store_true",
                           help="Xuat file du con o phan tich bo trong")
    build_cmd.add_argument("--allow-empty", action="store_true",
                           help="Xuat bao cao rong khi giai doan that su khong co bug")
    return parser


HANDLERS = {"verify": cmd_verify, "collect": cmd_collect, "build": cmd_build}


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return HANDLERS[args.command](args)
    except TrackerError as exc:
        return cli_io.fail(exc, kind="tracker")
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        return cli_io.fail(exc, kind=type(exc).__name__)
    except Exception as exc:                                  # noqa: BLE001
        # Hop dong cua CLI la LUON tra JSON. Mot exception khong luong truoc
        # (openpyxl doi hanh vi, template bi sua tay, loi lap trinh) khong duoc
        # phep thoat ra thanh traceback voi stdout rong -- agent goi skill nay
        # parse stdout, khong parse stderr.
        return cli_io.fail("Loi khong luong truoc: %s" % exc,
                           kind=type(exc).__name__)


if __name__ == "__main__":
    sys.exit(main())

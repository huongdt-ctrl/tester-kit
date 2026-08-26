#!/usr/bin/env python3
"""Entry point duy nhat cua skill log-bug. Output luon la JSON, exit 0 ok / 1 loi.

  preflight     kiem tra config + credential + ket noi tracker
  validate      soi bug theo rule log bug (khong goi mang)
  render        xem truoc title/description da render
  merge-check   xet nhom bug UI nao duoc gop
  create        dedup roi tao bug that tren tracker (--dry-run de thu)
  registry      liet ke bug da log

Phan cong: agent quan sat bug + dien field + quyet dinh severity/priority.
Script validate / render / dedup / goi API -- agent khong improvise cac buoc nay.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse  # noqa: E402

import cli_io  # noqa: E402
import commands  # noqa: E402
import create_command  # noqa: E402

SUBCOMMANDS = (
    # (ten, handler, co can --bug-file)
    ("preflight", commands.preflight, False),
    ("validate", commands.validate, True),
    ("render", commands.render, True),
    ("merge-check", commands.merge_check, True),
    ("create", create_command.create, True),
    ("registry", commands.registry, False),
)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="log_bug_cli.py",
        description="Log bug len Redmine / GitLab / Jira theo template QA")
    subs = parser.add_subparsers(dest="command", required=True)
    for name, handler, needs_bugs in SUBCOMMANDS:
        sub = subs.add_parser(name)
        sub.add_argument("--manifest", help="inputs/log_bug_manifest.yaml")
        sub.add_argument("--profile", help="configs/log_bug_project_profile.yaml")
        sub.add_argument("--module", help="ghi de run.module_name")
        if needs_bugs:
            sub.add_argument("--bug-file", required=True, dest="bug_file",
                             help="JSON: 1 bug, list bug, hoac {\"bugs\": [...]}")
        if name == "create":
            sub.add_argument("--dry-run", action="store_true",
                             help="render + dedup nhung KHONG tao issue that")
            # Gop la MAC DINH: rule cho phep gop ton tai chinh vi log rieng
            # tung loi UI qua mat thoi gian. Bat opt-in thi QA quen co -> lai ra
            # ticket rac, dung cai vua phai sua.
            sub.add_argument("--no-merge", action="store_false", dest="apply_merge",
                             help="TAT gop bug UI, tao 1 ticket moi dong")
            sub.set_defaults(apply_merge=True)
        else:
            sub.set_defaults(apply_merge=False)
        sub.set_defaults(func=handler)
    return parser


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except (SystemExit, KeyboardInterrupt):
        # SystemExit: cli_io.out/fail da in JSON va chon exit code.
        # KeyboardInterrupt: Ctrl+C phai huy that su, khong duoc bien thanh
        # "loi JSON exit 1" -- nguoi dung se tuong lenh chay xong va that bai.
        raise
    except Exception as exc:       # noqa: BLE001
        # Hop dong cua CLI la "luon tra JSON, exit 0/1". Mot exception lot ra
        # ngoai se thanh traceback tren stderr voi stdout RONG -- caller khong
        # parse duoc gi ca. Bat het o day de hop dong khong bao gio bi pha.
        cli_io.fail("%s: %s" % (type(exc).__name__, exc))


if __name__ == "__main__":
    main()

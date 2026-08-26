#!/usr/bin/env python3
"""Ba nhom vua duoc sua sau review lan 2:

  1. `create --apply-merge` THUC SU gop -- truoc day merge-check chi la bao cao
     de doc, create van tao 1 ticket moi dong (8 bug UI gop duoc -> 8 ticket).
  2. Cac key allowed_* / duplicate_handling / check_*_before_create trong config
     duoc code doc that, khong phai config chet.
  3. Ctrl+C phai huy that, khong bien thanh loi JSON exit 1.
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import bug_batch  # noqa: E402
import bug_validator  # noqa: E402

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
CLI = os.path.join(SCRIPTS, "log_bug_cli.py")

MANIFEST = """
run: {module_name: m, dry_run: true}
tracker:
  system: gitlab
  base_url: https://gl.test
  project_path: a/b
  token: env:AM_TOKEN
bug_policy:
  bug_title_pattern: "[{parent_ticket}][{screen}] {summary}"
  ui_merge: {enabled: true, min_errors_same_item: 3, max_errors_same_item: 5}
%(extra)s
paths: {bug_reports_root: "%(reports)s"}
"""


def _ui(item, subtype="spelling", screen="Login", summary=None):
    return {"parent_ticket": "#1", "screen": screen, "item": item, "bug_type": "ui",
            "ui_subtype": subtype, "summary": summary or "loi %s %s" % (subtype, item),
            "steps_to_reproduce": ["mo trang"], "actual_result": "sai",
            "expected_result": "dung", "severity": "Low", "priority": "Low"}


def _logic(summary):
    return {"parent_ticket": "#1", "screen": "Settlement", "item": "total",
            "bug_type": "logic", "summary": summary,
            "steps_to_reproduce": ["nhap so"], "actual_result": "sai",
            "expected_result": "dung", "severity": "Critical", "priority": "High"}


def _run(tmp, *args, **kw):
    env = dict(os.environ, AM_TOKEN="dummy")
    proc = subprocess.run([sys.executable, CLI] + list(args), capture_output=True,
                          text=True, env=env, cwd=tmp)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except ValueError:
        raise AssertionError("CLI khong tra JSON.\nstdout=%s\nstderr=%s"
                             % (proc.stdout, proc.stderr))


def _setup(tmp, bugs, extra=""):
    man = os.path.join(tmp, "man.yaml")
    with open(man, "w", encoding="utf-8") as fh:
        fh.write(MANIFEST % {"reports": os.path.join(tmp, "r"), "extra": extra})
    bug_file = os.path.join(tmp, "bugs.json")
    with open(bug_file, "w", encoding="utf-8") as fh:
        json.dump({"bugs": bugs}, fh, ensure_ascii=False)
    return man, bug_file


# --- 1. apply-merge ---

MIXED = ([_ui("btn"), _ui("label"), _ui("title")]                      # Case A: 3 item
         + [_ui("apply", "position", "Lottery"), _ui("apply", "font", "Lottery"),
            _ui("apply", "font_size", "Lottery")]                      # Case B: 1 item
         + [_logic("tong tien sai"), _logic("lam tron sai")])          # khong gop


def test_create_merges_by_default_without_any_flag():
    """Gop la MAC DINH -- QA khong phai nho co nao."""
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, MIXED)
        code, out = _run(tmp, "create", "--manifest", man, "--bug-file", bug_file,
                         "--dry-run")
    assert code == 0, out
    assert out["applied_merge"] is True
    # 3 bug Case A -> 1, 3 bug Case B -> 1, 2 bug logic -> 2 => 4 ticket
    assert out["counts"]["created"] == 4, [c["title"] for c in out["created"]]


def test_create_with_no_merge_flag_creates_one_ticket_per_row():
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, MIXED)
        code, out = _run(tmp, "create", "--manifest", man, "--bug-file", bug_file,
                         "--dry-run", "--no-merge")
    assert code == 0, out
    assert out["applied_merge"] is False
    assert out["counts"]["created"] == 8


def test_create_apply_merge_matches_merge_check_plan_count():
    """So ticket sau create phai KHOP ke hoach cua merge-check -- day la cai
    truoc day lech nhau (plan noi 4, create tao 8)."""
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, MIXED)
        _, plan_out = _run(tmp, "merge-check", "--manifest", man, "--bug-file", bug_file)
        _, create_out = _run(tmp, "create", "--manifest", man, "--bug-file", bug_file,
                             "--dry-run")
    planned = len(plan_out["plan"]["merge"]) + len(plan_out["plan"]["separate"])
    assert create_out["counts"]["created"] == planned == 4


def test_create_apply_merge_halts_when_group_needs_user_confirm():
    """6 loi cung 1 item -> vuot nguong Case B -> KHONG duoc tu gop."""
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, [_ui("btn", summary="loi %d" % i) for i in range(6)])
        code, out = _run(tmp, "create", "--manifest", man, "--bug-file", bug_file,
                         "--dry-run")
    assert code == 1
    assert out["ok"] is False
    assert "hoi user" in out["error"]
    assert out["plan"]["needs_confirm"]


def test_create_merge_noop_when_ui_merge_disabled_in_config():
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, MIXED, extra="  ui_merge: {enabled: false}")
        code, out = _run(tmp, "create", "--manifest", man, "--bug-file", bug_file,
                         "--dry-run")
    assert code == 0, out
    assert out["counts"]["created"] == 8


def test_create_no_merge_escapes_the_needs_confirm_hard_stop():
    """Nhom vuot nguong chan create; --no-merge la duong thoat de van log rieng."""
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, [_ui("btn", summary="loi %d" % i) for i in range(6)])
        code, out = _run(tmp, "create", "--manifest", man, "--bug-file", bug_file,
                         "--dry-run", "--no-merge")
    assert code == 0, out
    assert out["counts"]["created"] == 6


def test_apply_merge_preserves_every_input_bug():
    """Khong duoc lam roi bug nao: tong so bug goc phai xuat hien het, hoac o
    ticket gop hoac o ticket rieng."""
    out, plan = bug_batch.apply_merge(MIXED, {"enabled": True})
    covered = sum(b.get("merged_from_count", 1) for b in out)
    assert covered == len(MIXED)
    assert len(out) == 4


def test_apply_merge_returns_none_on_needs_confirm():
    bugs = [_ui("btn", summary="loi %d" % i) for i in range(6)]
    out, plan = bug_batch.apply_merge(bugs, {"enabled": True})
    assert out is None
    assert plan["needs_confirm"]


def test_apply_merge_disabled_returns_input_unchanged():
    out, plan = bug_batch.apply_merge(MIXED, {"enabled": False})
    assert plan is None
    assert len(out) == len(MIXED)


# --- 2. config khong con chet ---

def test_validator_reads_allowed_severities_from_config():
    bug = dict(_logic("x"), severity="Blocker")
    policy = {"bug_policy": {"allowed_severities": ["Blocker", "Trivial"]}}
    errors, _ = bug_validator.validate(bug, policy)
    assert not [e for e in errors if "severity" in e], errors


def test_validator_config_severity_list_rejects_value_outside_it():
    bug = dict(_logic("x"), severity="Major")
    policy = {"bug_policy": {"allowed_severities": ["Blocker", "Trivial"]}}
    errors, _ = bug_validator.validate(bug, policy)
    assert any("severity" in e and "Blocker" in e for e in errors), errors


def test_validator_reads_allowed_ui_subtypes_from_config():
    bug = dict(_ui("btn"), ui_subtype="mau_sac")
    policy = {"bug_policy": {"allowed_ui_subtypes": ["mau_sac"]}}
    errors, _ = bug_validator.validate(bug, policy)
    assert not [e for e in errors if "ui_subtype" in e], errors


def test_validator_falls_back_to_builtin_enum_when_config_absent():
    bug = dict(_logic("x"), severity="Blocker")
    errors, _ = bug_validator.validate(bug, {})
    assert any("severity" in e and "Critical" in e for e in errors), errors


def test_create_duplicate_handling_warn_only_creates_despite_suspected_dup():
    """warn_only: van tao nhung PHAI ghi ro canh bao, khong im lang."""
    bug = _logic("tong tien sai")
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, [bug, bug],
                               extra='  duplicate_handling: "warn_only"')
        code, out = _run(tmp, "create", "--manifest", man, "--bug-file", bug_file,
                         "--dry-run")
    assert code == 0, out
    assert out["duplicate_handling"] == "warn_only"
    assert out["counts"]["created"] == 2


def test_create_default_skip_mode_reported():
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, [_logic("x")])
        _, out = _run(tmp, "create", "--manifest", man, "--bug-file", bug_file,
                      "--dry-run")
    assert out["duplicate_handling"] == "skip"


def test_preflight_uses_adapter_declared_required_fields():
    """commands.py khong con giu bang required rieng -> adapter la nguon duy nhat."""
    with tempfile.TemporaryDirectory() as tmp:
        man = os.path.join(tmp, "m.yaml")
        with open(man, "w", encoding="utf-8") as fh:
            fh.write("tracker: {system: jira, base_url: https://x, email: a@b.c,\n"
                     "         api_token: env:AM_TOKEN}\n")
        code, out = _run(tmp, "preflight", "--manifest", man)
    assert code == 1
    assert "project_key" in out["error"]


# --- 3. Ctrl+C ---

def test_keyboard_interrupt_is_not_swallowed_into_json_error():
    """Ctrl+C phai huy that. Bien thanh {"ok": false} exit 1 se lam nguoi dung
    tuong lenh da chay xong va that bai."""
    code = (
        "import sys, os; sys.path.insert(0, %r)\n"
        "import log_bug_cli, cli_io\n"
        "log_bug_cli.build_parser = lambda: type('P', (), "
        "  {'parse_args': staticmethod(lambda: type('A', (), "
        "  {'func': staticmethod(lambda a: (_ for _ in ()).throw(KeyboardInterrupt()))})())})()\n"
        "log_bug_cli.main()\n" % SCRIPTS)
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert "KeyboardInterrupt" in proc.stderr
    assert proc.stdout.strip() == ""      # khong in JSON "loi"

#!/usr/bin/env python3
"""Chay THAT CLI end-to-end o che do dry_run (khong goi mang).

Dung dry_run vi test khong duoc phu thuoc external state (test-standards.md).
Cac subcommand duoc kiem: preflight, validate, render, merge-check, create, registry.
"""
import json
import os
import subprocess
import sys
import tempfile

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
CLI = os.path.join(SCRIPTS, "log_bug_cli.py")

MANIFEST = """
run:
  module_name: event_editing
  dry_run: true
tracker:
  system: gitlab
  base_url: https://git.example.com
  project_path: grp/sub/demo
  token: env:LOG_BUG_IT_TOKEN
bug_policy:
  bug_title_pattern: "[{parent_ticket}][{screen}] {summary}"
  require_severity: true
  require_priority: true
  require_parent_ticket: true
  ui_merge:
    enabled: true
    min_errors_same_item: 3
    max_errors_same_item: 5
defaults:
  device: "Laptop (MAC)"
  os_version: "14.4.1"
  browser: Chrome
  status: Open
  scope: Frontend
  sheet_name: "Manual Test Cases"
paths:
  bug_reports_root: "%(reports)s"
"""

GOOD_BUG = {
    "parent_ticket": "#1234", "screen": "Login", "item": "btn_submit",
    "summary": "Dang nhap khong thanh cong khi nhap sai mat khau",
    "bug_type": "logic", "tc_id": "TC002",
    "preconditions": "Da co account test",
    "steps_to_reproduce": ["Mo /login", "Nhap sai mat khau", "Bam Dang nhap"],
    "actual_result": "Man hinh trang, khong bao loi",
    "expected_result": "Hien message 'Mat khau khong dung'",
    "severity": "Major", "priority": "High", "evidence": "evidence/login_fail.png",
}

BAD_BUG = {"screen": "Login", "summary": "thieu het field", "bug_type": "ui"}


def _run(tmp, *args):
    env = dict(os.environ, LOG_BUG_IT_TOKEN="dummy-token-for-dry-run")
    proc = subprocess.run([sys.executable, CLI] + list(args), capture_output=True,
                          text=True, env=env, cwd=tmp)
    try:
        payload = json.loads(proc.stdout)
    except ValueError:
        raise AssertionError("CLI khong tra JSON.\nstdout=%s\nstderr=%s"
                             % (proc.stdout, proc.stderr))
    return proc.returncode, payload


def _setup(tmp, bugs):
    reports = os.path.join(tmp, "bug_reports")
    man = os.path.join(tmp, "manifest.yaml")
    with open(man, "w", encoding="utf-8") as fh:
        fh.write(MANIFEST % {"reports": reports})
    bug_file = os.path.join(tmp, "bugs.json")
    with open(bug_file, "w", encoding="utf-8") as fh:
        json.dump({"bugs": bugs}, fh, ensure_ascii=False)
    return man, bug_file


def test_cli_preflight_with_valid_config_reports_ok_and_effective_config():
    with tempfile.TemporaryDirectory() as tmp:
        man, _ = _setup(tmp, [GOOD_BUG])
        code, out = _run(tmp, "preflight", "--manifest", man)
    assert code == 0, out
    assert out["ok"] is True
    assert out["tracker"] == "gitlab"
    assert out["markup"] == "markdown"
    # Severity/Scope phai nam trong nhom nhung vao description
    assert "severity" in out["fields_embedded_in_description"]
    assert any(r["key"] == "tracker.system" for r in out["effective_config"])


def test_cli_preflight_missing_env_credential_exits_nonzero():
    with tempfile.TemporaryDirectory() as tmp:
        man, _ = _setup(tmp, [GOOD_BUG])
        proc = subprocess.run(
            [sys.executable, CLI, "preflight", "--manifest", man],
            capture_output=True, text=True, cwd=tmp,
            env={k: v for k, v in os.environ.items() if k != "LOG_BUG_IT_TOKEN"})
    assert proc.returncode == 1
    assert "LOG_BUG_IT_TOKEN" in proc.stdout


def test_cli_validate_good_bug_passes():
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, [GOOD_BUG])
        code, out = _run(tmp, "validate", "--manifest", man, "--bug-file", bug_file)
    assert code == 0, out
    assert out["blocked"] == 0
    assert out["results"][0]["can_create"] is True


def test_cli_validate_incomplete_bug_blocks_with_reasons():
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, [BAD_BUG])
        code, out = _run(tmp, "validate", "--manifest", man, "--bug-file", bug_file)
    assert code == 1
    assert out["blocked"] == 1
    errors = " ".join(out["results"][0]["errors"])
    assert "ui_subtype" in errors
    assert "parent_ticket" in errors
    assert "steps_to_reproduce" in errors


def test_cli_render_applies_manifest_defaults_into_description():
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, [GOOD_BUG])
        code, out = _run(tmp, "render", "--manifest", man, "--bug-file", bug_file)
    assert code == 0, out
    bug = out["bugs"][0]
    assert bug["title"] == "[#1234][Login] Dang nhap khong thanh cong khi nhap sai mat khau"
    # defaults tu manifest phai duoc dien vao
    assert "Laptop (MAC)" in bug["description"]
    assert "14.4.1" in bug["description"]
    assert "Chrome" in bug["description"]
    # GitLab -> markdown heading
    assert "### Kết quả thực tế" in bug["description"]
    # testcase_id ghep tu sheet_name default + tc_id
    assert "Manual Test Cases_TC002" in bug["description"]


def test_cli_merge_check_groups_ui_bugs_and_keeps_logic_separate():
    ui = [{"bug_type": "ui", "ui_subtype": "spelling", "screen": "Login",
           "item": it, "summary": "sai chinh ta %s" % it}
          for it in ("btn", "label", "title")]
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, ui + [GOOD_BUG])
        code, out = _run(tmp, "merge-check", "--manifest", man, "--bug-file", bug_file)
    assert code == 0, out
    assert len(out["plan"]["merge"]) == 1
    assert out["plan"]["merge"][0]["case"] == "A"
    assert sorted(out["plan"]["merge"][0]["indices"]) == [0, 1, 2]
    # bug logic (index 3) phai nam rieng
    assert [3] in [g["indices"] for g in out["plan"]["separate"]]
    assert out["needs_user_confirm"] is False


def test_cli_create_dry_run_does_not_write_registry():
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, [GOOD_BUG])
        code, out = _run(tmp, "create", "--manifest", man, "--bug-file", bug_file)
        assert code == 0, out
        assert out["dry_run"] is True
        assert out["counts"]["created"] == 1
        assert out["created"][0]["action"] == "create_new"
        # dry_run -> KHONG duoc ghi registry, vi bug that chua he duoc tao
        assert not os.path.exists(out["registry_path"])


def test_cli_create_invalid_bug_exits_nonzero_and_creates_nothing():
    with tempfile.TemporaryDirectory() as tmp:
        man, bug_file = _setup(tmp, [BAD_BUG])
        code, out = _run(tmp, "create", "--manifest", man, "--bug-file", bug_file)
    assert code == 1
    assert out["counts"]["created"] == 0
    assert out["counts"]["failed"] == 1


def test_cli_registry_on_fresh_module_reports_empty():
    with tempfile.TemporaryDirectory() as tmp:
        man, _ = _setup(tmp, [GOOD_BUG])
        code, out = _run(tmp, "registry", "--manifest", man)
    assert code == 0, out
    assert out["total"] == 0


def test_cli_malformed_bug_file_exits_nonzero_with_message():
    with tempfile.TemporaryDirectory() as tmp:
        man, _ = _setup(tmp, [GOOD_BUG])
        bad = os.path.join(tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write("{khong phai json}")
        code, out = _run(tmp, "validate", "--manifest", man, "--bug-file", bad)
    assert code == 1
    assert "JSON" in out["error"]


def test_cli_accepts_single_bare_bug_object_not_wrapped_in_bugs_key():
    """Regression: bug file la 1 object don le (khong boc trong {"bugs": [...]})
    tung bi bao "list bug khong rong" du tai lieu noi la nhan duoc."""
    with tempfile.TemporaryDirectory() as tmp:
        man, _ = _setup(tmp, [GOOD_BUG])
        bare = os.path.join(tmp, "bare.json")
        with open(bare, "w", encoding="utf-8") as fh:
            json.dump(GOOD_BUG, fh, ensure_ascii=False)
        code, out = _run(tmp, "render", "--manifest", man, "--bug-file", bare)
    assert code == 0, out
    assert len(out["bugs"]) == 1
    assert out["bugs"][0]["title"].startswith("[#1234][Login]")


def test_cli_accepts_bare_list_of_bugs():
    with tempfile.TemporaryDirectory() as tmp:
        man, _ = _setup(tmp, [GOOD_BUG])
        bare = os.path.join(tmp, "list.json")
        with open(bare, "w", encoding="utf-8") as fh:
            json.dump([GOOD_BUG, GOOD_BUG], fh, ensure_ascii=False)
        code, out = _run(tmp, "render", "--manifest", man, "--bug-file", bare)
    assert code == 0, out
    assert len(out["bugs"]) == 2


def test_cli_empty_bugs_list_exits_nonzero():
    with tempfile.TemporaryDirectory() as tmp:
        man, _ = _setup(tmp, [GOOD_BUG])
        empty = os.path.join(tmp, "empty.json")
        with open(empty, "w", encoding="utf-8") as fh:
            json.dump({"bugs": []}, fh)
        code, out = _run(tmp, "render", "--manifest", man, "--bug-file", empty)
    assert code == 1
    assert "khong rong" in out["error"]


# --- hop dong "luon tra JSON, exit 0/1" khong duoc pha ---

def test_cli_malformed_yaml_manifest_returns_json_error_not_traceback():
    """Truoc day: yaml.YAMLError thoat ra -> traceback tren stderr, stdout RONG."""
    with tempfile.TemporaryDirectory() as tmp:
        bad = os.path.join(tmp, "bad.yaml")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write("tracker:\n  system: [unclosed\n")
        code, out = _run(tmp, "preflight", "--manifest", bad)
    assert code == 1
    assert out["ok"] is False
    assert "YAML" in out["error"]


def test_cli_non_dict_entry_in_bugs_list_returns_json_error_not_traceback():
    """Truoc day: bug_validator goi bug.get() tren str -> AttributeError."""
    with tempfile.TemporaryDirectory() as tmp:
        man, _ = _setup(tmp, [GOOD_BUG])
        bad = os.path.join(tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as fh:
            json.dump({"bugs": ["chi la string", None]}, fh)
        code, out = _run(tmp, "validate", "--manifest", man, "--bug-file", bad)
    assert code == 1
    assert out["ok"] is False
    assert "index 0, 1" in out["error"]


def test_cli_plaintext_credential_in_manifest_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        man = os.path.join(tmp, "plain.yaml")
        with open(man, "w", encoding="utf-8") as fh:
            fh.write("tracker:\n  system: gitlab\n  base_url: https://x\n"
                     "  project_path: a/b\n  token: khong-nen-ghi-the-nay\n")
        code, out = _run(tmp, "preflight", "--manifest", man)
    assert code == 1
    assert "PLAINTEXT" in out["error"]
    assert "tracker.token" in out["error"]
    # gia tri that KHONG duoc lot vao output
    assert "khong-nen-ghi-the-nay" not in json.dumps(out)


def test_cli_missing_manifest_file_returns_json_error():
    with tempfile.TemporaryDirectory() as tmp:
        code, out = _run(tmp, "preflight", "--manifest",
                         os.path.join(tmp, "khong-ton-tai.yaml"))
    assert code == 1
    assert out["ok"] is False

#!/usr/bin/env python3
"""Merge config profile<manifest<CLI, resolve credential tu env, chon adapter."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import config_loader  # noqa: E402
from adapters import TrackerError, build_adapter  # noqa: E402


def _write(tmp, name, text):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def test_config_manifest_overrides_profile_for_same_key():
    with tempfile.TemporaryDirectory() as tmp:
        prof = _write(tmp, "p.yaml", "tracker:\n  system: redmine\n  base_url: http://a\n")
        man = _write(tmp, "m.yaml", "tracker:\n  system: gitlab\n")
        merged, _, _ = config_loader.load_config(prof, man)
    # manifest thang system, nhung base_url cua profile van con (merge lom)
    assert merged["tracker"]["system"] == "gitlab"
    assert merged["tracker"]["base_url"] == "http://a"


def test_config_cli_override_beats_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        man = _write(tmp, "m.yaml", "run:\n  module_name: aaa\n")
        merged, _, _ = config_loader.load_config(None, man, {"run": {"module_name": "bbb"}})
    assert merged["run"]["module_name"] == "bbb"


def test_config_list_is_replaced_not_appended():
    with tempfile.TemporaryDirectory() as tmp:
        prof = _write(tmp, "p.yaml", "bug_policy:\n  default_labels: [a, b]\n")
        man = _write(tmp, "m.yaml", "bug_policy:\n  default_labels: [c]\n")
        merged, _, _ = config_loader.load_config(prof, man)
    assert merged["bug_policy"]["default_labels"] == ["c"]


def test_config_env_credential_resolved_from_environment():
    os.environ["LOG_BUG_TEST_TOKEN"] = "secret-123"
    try:
        with tempfile.TemporaryDirectory() as tmp:
            man = _write(tmp, "m.yaml",
                         "tracker:\n  system: gitlab\n  token: env:LOG_BUG_TEST_TOKEN\n")
            merged, missing, _ = config_loader.load_config(None, man)
        assert missing == []
        assert merged["tracker"]["token"] == "secret-123"
    finally:
        del os.environ["LOG_BUG_TEST_TOKEN"]


def test_config_missing_env_credential_is_reported_not_silently_empty():
    os.environ.pop("LOG_BUG_ABSENT_TOKEN", None)
    with tempfile.TemporaryDirectory() as tmp:
        man = _write(tmp, "m.yaml",
                     "tracker:\n  system: gitlab\n  token: env:LOG_BUG_ABSENT_TOKEN\n")
        merged, missing, _ = config_loader.load_config(None, man)
    assert len(missing) == 1
    assert "LOG_BUG_ABSENT_TOKEN" in missing[0]
    # Gia tri con nguyen 'env:' -> adapter se chan lai, khong goi API voi token rong
    assert merged["tracker"]["token"].startswith("env:")


def test_config_missing_file_raises_clear_error():
    try:
        config_loader.load_config("/khong/ton/tai.yaml", None)
    except FileNotFoundError as exc:
        assert "Khong tim thay" in str(exc)
    else:
        raise AssertionError("phai raise FileNotFoundError")


def test_config_effective_config_masks_credential():
    merged = {"tracker": {"system": "gitlab", "token": "secret-123"}}
    rows = {r["key"]: r["value"] for r in config_loader.effective_config(merged)}
    assert "secret-123" not in str(rows)
    assert rows["tracker.credential"] == "***da-resolve-tu-env***"


# --- adapter factory ---

def test_adapter_factory_returns_matching_adapter_per_system():
    for system, name, markup in (("redmine", "redmine", "textile"),
                                 ("gitlab", "gitlab", "markdown"),
                                 ("jira", "jira", "textile")):
        adapter = build_adapter({"tracker": {"system": system}})
        assert adapter.name == name
        assert adapter.markup == markup


def test_adapter_factory_unknown_system_raises_with_supported_list():
    try:
        build_adapter({"tracker": {"system": "bugzilla"}})
    except TrackerError as exc:
        assert "gitlab" in str(exc) and "redmine" in str(exc) and "jira" in str(exc)
    else:
        raise AssertionError("phai raise TrackerError")


def test_adapter_factory_missing_system_raises():
    try:
        build_adapter({"tracker": {}})
    except TrackerError as exc:
        assert "tracker.system" in str(exc)
    else:
        raise AssertionError("phai raise TrackerError")


def test_adapter_missing_config_reports_unresolved_env_credential():
    adapter = build_adapter({"tracker": {"system": "gitlab", "base_url": "http://a",
                                         "project_path": "x/y", "token": "env:NOPE"}})
    miss = adapter.missing_config(("base_url", "token", "project_path"))
    assert any("chua resolve" in m for m in miss)


def test_adapter_gitlab_treats_start_date_as_unsupported():
    # GitLab issue khong co start_date -> phai bi day xuong description
    adapter = build_adapter({"tracker": {"system": "gitlab"}})
    unsupported = adapter.unsupported_fields({"start_date": "2026-08-25",
                                              "due_date": "2026-08-28"})
    assert "start_date" in unsupported
    assert "due_date" not in unsupported


def test_adapter_redmine_supports_start_date_natively():
    adapter = build_adapter({"tracker": {"system": "redmine"}})
    assert "start_date" not in adapter.unsupported_fields({"start_date": "2026-08-25"})


def test_adapter_severity_and_scope_unsupported_on_all_three_trackers():
    # Quyet dinh 2026-08-25: severity/scope luon nhung vao description
    for system in ("redmine", "gitlab", "jira"):
        adapter = build_adapter({"tracker": {"system": system}})
        unsupported = adapter.unsupported_fields({"severity": "Major", "scope": "Frontend"})
        assert "severity" in unsupported, system
        assert "scope" in unsupported, system


def test_adapter_is_closed_recognises_common_closed_statuses():
    adapter = build_adapter({"tracker": {"system": "redmine"}})
    for name in ("Closed", "closed", "Rejected", "Done", "WontFix"):
        assert adapter.is_closed(name), name
    for name in ("Open", "In Progress", "opened", None):
        assert not adapter.is_closed(name), name


# --- credential plaintext bi chan (rule bao mat) ---

def test_config_plaintext_credential_is_reported():
    with tempfile.TemporaryDirectory() as tmp:
        man = _write(tmp, "m.yaml",
                     "tracker:\n  system: gitlab\n  token: abc123secret\n")
        merged, missing, plaintext = config_loader.load_config(None, man)
    assert plaintext == ["tracker.token"]
    assert missing == []


def test_config_env_indirection_is_not_flagged_as_plaintext():
    os.environ["LOG_BUG_OK_TOKEN"] = "v"
    try:
        with tempfile.TemporaryDirectory() as tmp:
            man = _write(tmp, "m.yaml",
                         "tracker:\n  system: gitlab\n  token: env:LOG_BUG_OK_TOKEN\n")
            _, missing, plaintext = config_loader.load_config(None, man)
        assert (missing, plaintext) == ([], [])
    finally:
        del os.environ["LOG_BUG_OK_TOKEN"]


def test_config_plaintext_detected_for_every_credential_field_name():
    with tempfile.TemporaryDirectory() as tmp:
        man = _write(tmp, "m.yaml",
                     "tracker:\n  api_key: k1\n  api_token: k2\n  password: k3\n")
        _, _, plaintext = config_loader.load_config(None, man)
    assert sorted(plaintext) == ["tracker.api_key", "tracker.api_token",
                                 "tracker.password"]


def test_config_malformed_yaml_raises_value_error_not_yaml_error():
    """yaml.YAMLError khong phai subclass ValueError -> phai doi, neu khong no
    thoat ra thanh traceback tho."""
    with tempfile.TemporaryDirectory() as tmp:
        bad = _write(tmp, "bad.yaml", "tracker:\n  system: [unclosed\n")
        try:
            config_loader.load_config(None, bad)
        except ValueError as exc:
            assert "YAML" in str(exc)
        else:
            raise AssertionError("phai raise ValueError")


def test_config_non_mapping_yaml_raises_value_error():
    with tempfile.TemporaryDirectory() as tmp:
        bad = _write(tmp, "list.yaml", "- a\n- b\n")
        try:
            config_loader.load_config(None, bad)
        except ValueError as exc:
            assert "mapping" in str(exc)
        else:
            raise AssertionError("phai raise ValueError")

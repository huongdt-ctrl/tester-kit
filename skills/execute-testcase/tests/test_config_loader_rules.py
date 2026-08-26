#!/usr/bin/env python3
"""Unit tests cho config_loader: precedence, env credential, safety gate.
Khong network, khong credential thuc -- chi tempfile + dict."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import config_loader  # noqa: E402


def _yaml_file(text):
    fd, path = tempfile.mkstemp(suffix=".yaml")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


class ConfigPrecedenceTests(unittest.TestCase):
    def test_config_loader_manifest_key_overrides_profile_key(self):
        # Arrange
        profile = _yaml_file('result_policy:\n  status_when_not_testable: "Untested"\n')
        manifest = _yaml_file('result_policy:\n  status_when_not_testable: "Pending"\n')
        # Act
        merged = config_loader.load(profile, manifest)["merged"]
        # Assert
        self.assertEqual(merged["result_policy"]["status_when_not_testable"], "Pending")

    def test_config_loader_profile_only_key_survives_merge(self):
        # Arrange
        profile = _yaml_file('result_policy:\n  fail_remark_prefix: "Actual khac Expected:"\n')
        manifest = _yaml_file('result_policy:\n  test_date_format: "YYYY-MM-DD"\n')
        # Act
        merged = config_loader.load(profile, manifest)["merged"]
        # Assert
        self.assertEqual(merged["result_policy"]["fail_remark_prefix"], "Actual khac Expected:")
        self.assertEqual(merged["result_policy"]["test_date_format"], "YYYY-MM-DD")

    def test_config_loader_effective_table_marks_manifest_as_winner(self):
        # Arrange
        profile = _yaml_file('update_policy:\n  default_mode: "in_place"\n')
        manifest = _yaml_file('update_policy:\n  mode: "backup_then_update"\n')
        # Act
        rows = config_loader.load(profile, manifest)["effective_table"]
        # Assert
        row = [r for r in rows if r["key"] == "update_policy"][0]
        self.assertEqual(row["winner"], "manifest")


class CredentialResolutionTests(unittest.TestCase):
    def test_config_loader_env_ref_resolves_from_environment(self):
        # Arrange
        profile, manifest = _yaml_file("{}\n"), _yaml_file('environment:\n  password: "env:QA_PWD"\n')
        # Act
        merged = config_loader.load(profile, manifest, environ={"QA_PWD": "s3cret"})["merged"]
        # Assert
        self.assertEqual(merged["environment"]["password"], "s3cret")

    def test_config_loader_missing_env_var_raises_and_lists_all(self):
        # Arrange
        profile = _yaml_file("{}\n")
        manifest = _yaml_file(
            'environment:\n  password: "env:QA_PWD"\n'
            'redmine:\n  enabled: true\n  api_key: "env:RM_KEY"\n')
        # Act + Assert
        with self.assertRaises(config_loader.ConfigError) as ctx:
            config_loader.load(profile, manifest, environ={})
        self.assertIn("QA_PWD", str(ctx.exception))
        self.assertIn("RM_KEY", str(ctx.exception))

    def test_config_loader_empty_env_var_treated_as_missing(self):
        # Arrange
        profile, manifest = _yaml_file("{}\n"), _yaml_file('environment:\n  password: "env:QA_PWD"\n')
        # Act + Assert
        with self.assertRaises(config_loader.ConfigError):
            config_loader.load(profile, manifest, environ={"QA_PWD": ""})


class EnvironmentSafetyTests(unittest.TestCase):
    def test_safety_gate_flags_production_environment_name(self):
        # Arrange
        cfg = {"environment": {"name": "PROD", "base_url": "https://uat.example.com"},
               "environment_safety": {"forbid_production": True}}
        # Act
        reasons = config_loader.check_environment_safety(cfg)
        # Assert
        self.assertTrue(any("PROD" in r for r in reasons))

    def test_safety_gate_flags_url_without_test_marker(self):
        # Arrange
        cfg = {"environment": {"name": "UAT", "base_url": "https://acme.com"},
               "environment_safety": {"forbid_production": True, "allowed_environment_names": ["UAT"]}}
        # Act
        reasons = config_loader.check_environment_safety(cfg)
        # Assert
        self.assertEqual(len(reasons), 1)
        self.assertIn("acme.com", reasons[0])

    def test_safety_gate_passes_clean_uat_environment(self):
        # Arrange
        cfg = {"environment": {"name": "UAT", "base_url": "https://uat.example.com"},
               "environment_safety": {"forbid_production": True,
                                      "allowed_environment_names": ["UAT", "STG"]}}
        # Act
        reasons = config_loader.check_environment_safety(cfg)
        # Assert
        self.assertEqual(reasons, [])


class SelectedCasesGuardTests(unittest.TestCase):
    def test_config_loader_selected_cases_without_tc_ids_raises(self):
        # Arrange
        profile = _yaml_file("{}\n")
        manifest = _yaml_file('run:\n  execution_mode: "selected_cases"\ncase_filter:\n  include_tc_ids: []\n')
        # Act + Assert
        with self.assertRaises(config_loader.ConfigError) as ctx:
            config_loader.load(profile, manifest, environ={})
        self.assertIn("selected_cases", str(ctx.exception))



class DisabledBlockCredentialTests(unittest.TestCase):
    """redmine.enabled = false thi khong duoc doi REDMINE_API_KEY."""

    def test_config_loader_skips_env_ref_of_disabled_redmine_block(self):
        # Arrange
        profile = _yaml_file("{}\n")
        manifest = _yaml_file('redmine:\n  enabled: false\n  api_key: "env:RM_KEY"\n')
        # Act
        merged = config_loader.load(profile, manifest, environ={})["merged"]
        # Assert -- khong raise, va gia tri giu nguyen dang env: de redmine_client tu chan
        self.assertEqual(merged["redmine"]["api_key"], "env:RM_KEY")

    def test_config_loader_still_requires_env_ref_of_enabled_redmine_block(self):
        # Arrange
        profile = _yaml_file("{}\n")
        manifest = _yaml_file('redmine:\n  enabled: true\n  api_key: "env:RM_KEY"\n')
        # Act + Assert
        with self.assertRaises(config_loader.ConfigError):
            config_loader.load(profile, manifest, environ={})

    def test_config_loader_still_requires_non_redmine_env_ref_when_redmine_disabled(self):
        # Arrange
        profile = _yaml_file("{}\n")
        manifest = _yaml_file(
            'environment:\n  password: "env:QA_PWD"\nredmine:\n  enabled: false\n  api_key: "env:RM_KEY"\n')
        # Act + Assert
        with self.assertRaises(config_loader.ConfigError) as ctx:
            config_loader.load(profile, manifest, environ={})
        self.assertIn("QA_PWD", str(ctx.exception))
        self.assertNotIn("RM_KEY", str(ctx.exception))

if __name__ == "__main__":
    unittest.main(verbosity=2)

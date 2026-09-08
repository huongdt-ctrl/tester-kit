#!/usr/bin/env python3
"""Test: CLI phai DUNG truoc khi goi tracker khi config/credential/ngay sai."""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helpers import (PROFILE_ENV, PROFILE_PLAINTEXT, TEMPLATE, bug_row,
                     run_cli, write)

class TestCredentialRules(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ.pop("BUG_ANALYST_TEST_TOKEN", None)

    def test_cli_rejects_plaintext_credential_in_config(self):
        # Arrange
        profile = write(self.tmp, "p.yaml", PROFILE_PLAINTEXT)
        # Act
        code, payload = run_cli(["--profile", profile, "verify"])
        # Assert
        self.assertEqual(code, 1)
        self.assertIn("plaintext", payload["error"])
        self.assertFalse(payload["ok"])

    def test_cli_stops_when_env_var_for_credential_is_not_set(self):
        # Arrange
        profile = write(self.tmp, "p.yaml", PROFILE_ENV)
        # Act
        code, payload = run_cli(["--profile", profile, "verify"])
        # Assert
        self.assertEqual(code, 1)
        self.assertIn("BUG_ANALYST_TEST_TOKEN", payload["error"])

    def test_cli_never_echoes_resolved_credential_in_output(self):
        # Arrange
        profile = write(self.tmp, "p.yaml", PROFILE_ENV)
        os.environ["BUG_ANALYST_TEST_TOKEN"] = "secret-value-123"
        self.addCleanup(os.environ.pop, "BUG_ANALYST_TEST_TOKEN", None)
        # Act
        import requests
        with mock.patch("adapters.gitlab_adapter.requests.get",
                        side_effect=requests.RequestException("khong goi that")):
            code, payload = run_cli(["--profile", profile, "verify"])
        # Assert
        self.assertNotIn("secret-value-123", json.dumps(payload))

    def test_cli_rejects_malformed_date_before_touching_tracker(self):
        # Arrange
        profile = write(self.tmp, "p.yaml", PROFILE_ENV)
        os.environ["BUG_ANALYST_TEST_TOKEN"] = "t"
        self.addCleanup(os.environ.pop, "BUG_ANALYST_TEST_TOKEN", None)
        # Act
        code, payload = run_cli(["--profile", profile, "--date-from", "01/08/2026",
                                 "--date-to", "2026-08-31", "collect"])
        # Assert
        self.assertEqual(code, 1)
        self.assertIn("YYYY-MM-DD", payload["error"])

    def test_cli_rejects_reversed_date_window(self):
        # Arrange
        profile = write(self.tmp, "p.yaml", PROFILE_ENV)
        os.environ["BUG_ANALYST_TEST_TOKEN"] = "t"
        self.addCleanup(os.environ.pop, "BUG_ANALYST_TEST_TOKEN", None)
        # Act
        code, payload = run_cli(["--profile", profile, "--date-from", "2026-08-31",
                                 "--date-to", "2026-08-01", "collect"])
        # Assert
        self.assertEqual(code, 1)
        self.assertIn("sau", payload["error"])



if __name__ == "__main__":
    unittest.main(verbosity=2)

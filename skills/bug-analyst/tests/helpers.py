#!/usr/bin/env python3
"""Do dung chung cho test cua skill bug-analyst."""
import io
import json
import os
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "templates", "template_bug_analysis.xlsx")

PROFILE_ENV = """
tracker:
  system: "gitlab"
  base_url: "https://gl.test"
  project_path: "a/b"
  token: "env:BUG_ANALYST_TEST_TOKEN"
  bug_label: "bug"
run:
  phase: "Sprint 3"
"""

PROFILE_PLAINTEXT = PROFILE_ENV.replace('"env:BUG_ANALYST_TEST_TOKEN"', '"plaintext-token-123"')


class FakeResponse:
    """Thay cho requests.Response -- test khong duoc cham mang."""

    def __init__(self, payload, status_code=200, text=""):
        self._payload, self.status_code, self.text = payload, status_code, text

    def json(self):
        if self._payload is None:
            raise ValueError("not json")
        return self._payload


def run_cli(argv):
    """Chay CLI, tra ve (exit_code, payload_json)."""
    import bug_analyst_cli as cli
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = cli.main(argv)
    return code, json.loads(buf.getvalue())


def write(tmp, name, text):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def bug_row(idx, analysed=True):
    return {
        "no": idx, "egg_id": "#%d" % (500 + idx), "egg_name": "Loi %d" % idx,
        "screen": "G10.1", "milestone": "Sprint 3",
        "title": "[GET-1][G10.1] loi %d" % idx, "priority": "High",
        "severity": "Major" if analysed else "",
        "bug_type": "Logic",
        "cause": "COD1.2 Coding Logic Mistake" if analysed else "",
        "root_cause": "IMP3 Carelessness" if analysed else "",
        "note": "",
    }

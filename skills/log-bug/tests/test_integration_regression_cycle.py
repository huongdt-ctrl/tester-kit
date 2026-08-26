#!/usr/bin/env python3
"""Chu trinh THAT: log bug -> dev fix (issue dong) -> bug tai xuat hien.

Day la test bat duoc dung con bug ma review tim ra: entry registry ghi
closed=False mot lan roi khong bao gio doi, nen bug regression bi skip vinh vien.
Test nay chay `create` HAI lan qua HTTP that (stub Redmine tren localhost) va
doi trang thai issue o giua.

Stub tu dung tu tat (test-standards: integration test phai tu don dep).
"""
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
CLI = os.path.join(SCRIPTS, "log_bug_cli.py")

# Trang thai chia se giua stub va test. Khong phai shared mutable global giua
# cac test -- moi test tu dung stub rieng qua _stub().
STATE = {}


class _RedmineStub(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass                     # im lang, khong spam output test

    def _send(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        STATE["next_id"] += 1
        issue_id = STATE["next_id"]
        STATE["issues"][issue_id] = "New"
        STATE["created"].append(issue_id)
        self._send(201, {"issue": {"id": issue_id}})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/issues.json":
            # search: luon rong, de test ep dedup di qua tang registry (tang 1)
            return self._send(200, {"issues": []})
        if path.startswith("/issues/"):
            issue_id = int(path.split("/")[2].replace(".json", ""))
            status = STATE["issues"].get(issue_id)
            if status is None:
                return self._send(404, {})
            return self._send(200, {"issue": {"status": {"name": status}}})
        self._send(404, {})


class _stub:
    """Context manager: dung stub server, tra ve base_url, tat khi xong."""

    def __enter__(self):
        STATE.clear()
        STATE.update({"next_id": 100, "issues": {}, "created": []})
        self.httpd = HTTPServer(("127.0.0.1", 0), _RedmineStub)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        return "http://127.0.0.1:%d" % self.httpd.server_address[1]

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)


MANIFEST = """
run:
  module_name: login
  dry_run: false
tracker:
  system: redmine
  base_url: %(base_url)s
  project_id: demo
  api_key: env:STUB_KEY
bug_policy:
  bug_title_pattern: "[{parent_ticket}][{screen}] {summary}"
paths:
  bug_reports_root: %(reports)s
"""

BUG = {"parent_ticket": "#1234", "screen": "Login", "item": "form",
       "summary": "Dang nhap sai mat khau van vao duoc", "bug_type": "logic",
       "steps_to_reproduce": ["Mo /login", "Nhap sai mat khau"],
       "actual_result": "Vao duoc dashboard", "expected_result": "Bao loi",
       "severity": "Critical", "priority": "High", "evidence": "e.png"}


def _create(tmp, man, bug_file):
    proc = subprocess.run([sys.executable, CLI, "create", "--manifest", man,
                           "--bug-file", bug_file],
                          capture_output=True, text=True, cwd=tmp,
                          env=dict(os.environ, STUB_KEY="stub"))
    try:
        return proc.returncode, json.loads(proc.stdout)
    except ValueError:
        raise AssertionError("CLI khong tra JSON.\nstdout=%s\nstderr=%s"
                             % (proc.stdout, proc.stderr))


def _setup(tmp, base_url):
    man = os.path.join(tmp, "man.yaml")
    with open(man, "w", encoding="utf-8") as fh:
        fh.write(MANIFEST % {"base_url": base_url,
                             "reports": os.path.join(tmp, "reports")})
    bug_file = os.path.join(tmp, "bug.json")
    with open(bug_file, "w", encoding="utf-8") as fh:
        json.dump(BUG, fh)
    return man, bug_file


def test_regression_cycle_closed_bug_reappearing_creates_new_ticket(tmp_path):
    tmp = str(tmp_path)
    with _stub() as base_url:
        man, bug_file = _setup(tmp, base_url)

        # Lan 1: bug moi -> tao ticket that
        code, out = _create(tmp, man, bug_file)
        assert code == 0, out
        assert out["counts"]["created"] == 1
        first_id = out["created"][0]["issue_id"]
        assert out["created"][0]["action"] == "create_new"
        assert os.path.exists(out["registry_path"])

        # Lan 2: bug y nguyen, issue con OPEN -> phai skip, khong tao trung
        code, out = _create(tmp, man, bug_file)
        assert code == 0, out
        assert out["counts"]["created"] == 0
        assert out["counts"]["skipped_duplicate"] == 1
        assert out["skipped"][0]["status_source"] == "tracker"

        # Dev fix xong -> issue dong tren tracker (registry VAN ghi closed=False)
        STATE["issues"][first_id] = "Closed"

        # Lan 3: bug tai xuat hien -> phai tao ticket moi danh dau regression
        code, out = _create(tmp, man, bug_file)
        assert code == 0, out
        assert out["counts"]["created"] == 1
        entry = out["created"][0]
        assert entry["action"] == "create_regression"
        assert entry["regression_of"] == first_id
        assert entry["issue_id"] != first_id

        assert STATE["created"] == [first_id, entry["issue_id"]]


def test_regression_cycle_registry_points_at_newest_ticket(tmp_path):
    tmp = str(tmp_path)
    with _stub() as base_url:
        man, bug_file = _setup(tmp, base_url)
        _, out1 = _create(tmp, man, bug_file)
        first_id = out1["created"][0]["issue_id"]
        STATE["issues"][first_id] = "Rejected"          # cung tinh la dong
        _, out2 = _create(tmp, man, bug_file)
        new_id = out2["created"][0]["issue_id"]

        with open(out2["registry_path"], "r", encoding="utf-8") as fh:
            registry = json.load(fh)
        entries = list(registry.values())
        # Cung dau van tay -> 1 entry, tro vao ticket MOI NHAT
        assert len(entries) == 1
        assert entries[0]["issue_id"] == new_id
        assert entries[0]["regression_of"] == first_id


def test_regression_cycle_tracker_unreachable_falls_back_to_registry(tmp_path):
    """Stub tat giua duong: search + get status that bai -> tin registry, skip.
    Tha bo sot mot bug con hon lam ngap tracker bang ticket trung."""
    tmp = str(tmp_path)
    with _stub() as base_url:
        man, bug_file = _setup(tmp, base_url)
        code, out = _create(tmp, man, bug_file)
        assert code == 0, out
    # ra khoi block -> server da tat
    code, out = _create(tmp, man, bug_file)
    assert code == 0, out
    assert out["counts"]["created"] == 0
    assert out["counts"]["skipped_duplicate"] == 1
    assert out["skipped"][0]["status_source"] == "registry"

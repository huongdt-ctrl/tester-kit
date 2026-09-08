#!/usr/bin/env python3
"""I/O chung cho CLI: luon in JSON, khong bao gio nem traceback tho ra stdout."""
import json
import os
import sys


def emit(payload, ok=True):
    body = dict(payload or {})
    body["ok"] = bool(ok)
    sys.stdout.write(json.dumps(body, ensure_ascii=False, indent=2) + "\n")
    return 0 if ok else 1


def fail(message, **extra):
    payload = {"error": str(message)}
    payload.update(extra)
    return emit(payload, ok=False)


def read_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError("Khong tim thay file: %s" % path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as exc:
        raise ValueError("File %s khong phai JSON hop le: %s" % (path, exc))


def write_json(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    return path


def validate_date(value, label):
    """Bat dinh dang YYYY-MM-DD ngay tai CLI, thay vi de tracker tra 400."""
    import datetime
    if not value:
        return None
    try:
        datetime.date.fromisoformat(str(value))
    except ValueError:
        raise ValueError("%s phai dang YYYY-MM-DD, nhan duoc %r" % (label, value))
    return str(value)

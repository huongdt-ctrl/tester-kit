#!/usr/bin/env python3
"""Vao/ra dung chung cho CLI: doc bug file, in JSON, nap config.

Tach rieng de commands.py khong lap lai, va de log_bug_cli.py chi con viec
parse argument.
"""
import json
import os
import sys

import bug_template
import config_loader


def out(payload, code=0):
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    sys.exit(code)


def fail(message, **extra):
    out(dict({"ok": False, "error": message}, **extra), 1)


def load_config(args):
    merged, missing, plaintext = config_loader.load_config(args.profile, args.manifest)
    if plaintext:
        fail("Credential dang ghi PLAINTEXT trong file cau hinh: %s. Chi duoc "
             "ghi dang 'env:TEN_BIEN'; doi lai roi set bien moi truong. Neu key "
             "nay la key that, coi nhu da bi lo -> revoke ngay."
             % ", ".join(plaintext))
    if missing:
        fail("Credential chua co trong environment variable: %s. Set bien roi "
             "chay lai; skill khong goi API voi credential rong."
             % ", ".join(missing))
    if getattr(args, "module", None):
        merged.setdefault("run", {})["module_name"] = args.module
    return merged


def apply_defaults(bugs, merged):
    """Dien gia tri tu block 'defaults' cua config vao field con trong.

    Muc dich: Device/OS/Browser/parent_ticket thuong giong nhau ca dot test,
    khai 1 lan o manifest thay vi lap lai trong tung bug. Gia tri khai TRONG
    bug luon thang default -- default chi lap cho cho trong."""
    defaults = merged.get("defaults") or {}
    if not defaults:
        return bugs
    out = []
    for bug in bugs:
        filled = dict(bug)
        for key, val in defaults.items():
            if val in (None, "", [], {}):
                continue
            if filled.get(key) in (None, "", [], {}):
                filled[key] = val
        out.append(filled)
    return out


def read_bugs(path, merged=None):
    """Nhan 1 bug (object), list bug, hoac {"bugs": [...]}.

    merged co truyen vao thi ap default tu config (xem apply_defaults)."""
    if not os.path.exists(path):
        fail("Khong tim thay bug file: %s" % path)
    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except ValueError as exc:
            fail("Bug file khong phai JSON hop le: %s" % exc)
    if isinstance(data, dict):
        # Co key "bugs" -> lay list ben trong. Khong co -> chinh dict nay LA
        # mot bug don le (dang duoc tai lieu hoa, dung bo sot).
        bugs = data.get("bugs", data)
    else:
        bugs = data
    if isinstance(bugs, dict):
        bugs = [bugs]
    if not isinstance(bugs, list) or not bugs:
        fail("Bug file phai chua 1 bug (object) hoac list bug khong rong")
    # Phan tu khong phai dict se lam bug_validator no AttributeError -> chan
    # ngay day de tra ve loi JSON tu te thay vi traceback.
    bad = [i for i, b in enumerate(bugs) if not isinstance(b, dict)]
    if bad:
        fail("Bug file co phan tu khong phai object tai index %s -- moi bug phai "
             "la mot JSON object" % ", ".join(str(i) for i in bad))
    return apply_defaults(bugs, merged) if merged else bugs


def policy(merged):
    return merged.get("bug_policy") or {}


def title(bug, merged):
    return bug_template.build_title(bug, policy(merged).get("bug_title_pattern"))


def ui_merge_cfg(merged):
    return policy(merged).get("ui_merge") or {}


def tracker_fields(bug, merged):
    """Field canonical -> adapter tu map sang field native cua no. Field nao
    tracker khong nhan se bi nhung vao description, khong bi danh roi."""
    pmap = (policy(merged).get("priority_map") or {})
    priority = bug.get("priority")
    return {"priority": pmap.get(str(priority), priority),
            "severity": bug.get("severity"), "scope": bug.get("scope"),
            "device": bug.get("device"), "os_version": bug.get("os_version"),
            "browser": bug.get("browser"), "assignee": bug.get("assignee"),
            "start_date": bug.get("start_date"), "due_date": bug.get("due_date"),
            "status": bug.get("status"), "tracker": bug.get("tracker") or "Bug",
            "parent_ticket": bug.get("parent_ticket"),
            "labels": bug.get("labels") or policy(merged).get("default_labels")}

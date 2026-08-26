#!/usr/bin/env python3
"""Nap cau hinh: profile < manifest < CLI param (nguon sau ghi de nguon truoc).

Rule bao mat credential (giong execute-testcase): api_key / token / api_token
KHONG BAO GIO ghi plaintext trong file config. Chi ghi ten bien moi truong dang
'env:TEN_BIEN'; skill doc gia tri that luc chay. Thieu bien -> DUNG, khong thu
goi API voi credential rong (se tra 401 kho hieu).
"""
import copy
import os

import yaml

# Field credential can resolve tu env, theo tung block config.
CREDENTIAL_FIELDS = ("api_key", "token", "api_token", "password")

ENV_PREFIX = "env:"


def deep_merge(base, override):
    """Merge lom. dict thi merge de quy; list/scalar thi GHI DE han.

    Co y: list ghi de chu khong noi duoi. Neu noi duoi thi khong the nao xoa
    mot phan tu ma profile da khai -- manifest mat quyen quyet dinh.
    """
    out = copy.deepcopy(base) if isinstance(base, dict) else {}
    for key, val in (override or {}).items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], val)
        elif val is not None:
            out[key] = copy.deepcopy(val)
    return out


def load_yaml(path):
    if not path:
        return {}
    if not os.path.exists(path):
        raise FileNotFoundError("Khong tim thay file cau hinh: %s" % path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        # YAMLError KHONG phai subclass cua ValueError -> khong doi thanh
        # ValueError thi no thoat ra ngoai thanh traceback tho.
        raise ValueError("File cau hinh %s sai cu phap YAML: %s" % (path, exc))
    except OSError as exc:
        raise ValueError("Khong doc duoc file cau hinh %s: %s" % (path, exc))
    if not isinstance(data, dict):
        raise ValueError("File cau hinh %s khong phai mapping YAML" % path)
    return data


def resolve_credentials(merged):
    """Doi moi gia tri 'env:X' thanh os.environ['X'].

    Tra ve (merged, missing, plaintext).
      missing   -- bien env chua set
      plaintext -- field credential ghi thang gia tri thay vi 'env:TEN_BIEN'
    Caller phai DUNG khi bat ky list nao khong rong."""
    missing, plaintext = [], []

    def walk(node, trail):
        if not isinstance(node, dict):
            return
        for key, val in list(node.items()):
            if isinstance(val, dict):
                walk(val, trail + [key])
            elif key in CREDENTIAL_FIELDS and isinstance(val, str) and val.strip():
                where = ".".join(trail + [key])
                if val.startswith(ENV_PREFIX):
                    env_name = val[len(ENV_PREFIX):].strip()
                    actual = os.environ.get(env_name)
                    if not actual:
                        missing.append("%s (cho %s)" % (env_name, where))
                    else:
                        node[key] = actual
                else:
                    # Rule bao mat: credential chi duoc ghi dang env:TEN_BIEN.
                    # Chan o day de mot key that lo commit vao manifest khong
                    # troi qua ma khong ai biet.
                    plaintext.append(where)

    walk(merged, [])
    return merged, missing, plaintext


def load_config(profile_path=None, manifest_path=None, cli_overrides=None):
    """Tra ve (merged, missing_credentials, plaintext_credentials). Khong tu tao
    gia tri mac dinh cho key bat buoc -- thieu thi bao, khong doan."""
    merged = deep_merge(load_yaml(profile_path), load_yaml(manifest_path))
    merged = deep_merge(merged, cli_overrides or {})
    return resolve_credentials(merged)


def _mask(value):
    return "***da-resolve-tu-env***" if value else "(chua set)"


def effective_config(merged):
    """Bang gia tri hieu luc de in ra report. Credential luon bi mask -- khong
    bao gio de credential roi vao report/evidence."""
    tracker = merged.get("tracker") or {}
    policy = merged.get("bug_policy") or {}
    run = merged.get("run") or {}
    rows = [
        ("tracker.system", tracker.get("system")),
        ("tracker.base_url", tracker.get("base_url")),
        ("tracker.project", tracker.get("project_id") or tracker.get("project_key")
         or tracker.get("project_path")),
        ("tracker.credential", _mask(tracker.get("api_key") or tracker.get("token")
                                     or tracker.get("api_token"))),
        ("bug_title_pattern", policy.get("bug_title_pattern")),
        ("duplicate_handling", policy.get("duplicate_handling")),
        ("ui_merge.enabled", (policy.get("ui_merge") or {}).get("enabled")),
        ("run.module_name", run.get("module_name")),
        ("run.dry_run", run.get("dry_run")),
        ("paths.bug_reports_root", (merged.get("paths") or {}).get("bug_reports_root")),
    ]
    return [{"key": k, "value": v} for k, v in rows]

#!/usr/bin/env python3
"""Nap cau hinh: profile < manifest < CLI param (nguon sau ghi de nguon truoc).

Rule bao mat giu nguyen nhu skill log-bug / execute-testcase: token / api_key /
api_token KHONG BAO GIO ghi plaintext trong file config. Chi ghi ten bien moi
truong dang 'env:TEN_BIEN'. Thieu bien -> DUNG, khong goi API voi credential
rong (se tra 401 kho hieu).
"""
import copy
import os

import yaml

CREDENTIAL_FIELDS = ("api_key", "token", "api_token", "password")
ENV_PREFIX = "env:"


def deep_merge(base, override):
    """dict merge de quy; list/scalar GHI DE han (de manifest xoa duoc gia tri
    ma profile khai)."""
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
        # YAMLError khong phai subclass ValueError -> khong doi thi no thoat ra
        # ngoai thanh traceback tho, CLI mat hop dong "luon tra JSON".
        raise ValueError("File cau hinh %s sai cu phap YAML: %s" % (path, exc))
    except OSError as exc:
        raise ValueError("Khong doc duoc file cau hinh %s: %s" % (path, exc))
    if not isinstance(data, dict):
        raise ValueError("File cau hinh %s khong phai mapping YAML" % path)
    return data


def resolve_credentials(merged):
    """'env:X' -> os.environ['X']. Tra ve (merged, missing, plaintext)."""
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
                    plaintext.append(where)

    walk(merged, [])
    return merged, missing, plaintext


def load_config(profile_path=None, manifest_path=None, cli_overrides=None):
    merged = deep_merge(load_yaml(profile_path), load_yaml(manifest_path))
    merged = deep_merge(merged, cli_overrides or {})
    return resolve_credentials(merged)


def _mask(value):
    return "***da-resolve-tu-env***" if value else "(chua set)"


def effective_config(merged):
    """Bang gia tri hieu luc de in ra report. Credential LUON bi mask."""
    tracker = merged.get("tracker") or {}
    run = merged.get("run") or {}
    paths = merged.get("paths") or {}
    rows = [
        ("tracker.system", tracker.get("system")),
        ("tracker.base_url", tracker.get("base_url")),
        ("tracker.project", tracker.get("project_path") or tracker.get("project_key")
         or tracker.get("project_id")),
        ("tracker.bug_filter", tracker.get("bug_label") or tracker.get("bug_issue_type")
         or tracker.get("bug_tracker_name")),
        ("tracker.credential", _mask(tracker.get("token") or tracker.get("api_key")
                                     or tracker.get("api_token"))),
        ("run.phase", run.get("phase")),
        ("run.date_from", run.get("date_from")),
        ("run.date_to", run.get("date_to")),
        ("paths.template", paths.get("template")),
        ("paths.output_root", paths.get("output_root")),
    ]
    return [{"key": k, "value": v} for k, v in rows]

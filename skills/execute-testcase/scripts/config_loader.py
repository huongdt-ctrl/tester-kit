#!/usr/bin/env python3
"""
Merge the two config sources of execute-testcase into ONE effective config, so
no downstream code ever has to ask "profile hay manifest thang?".

Precedence (SKILL.md muc 2A): profile < manifest < CLI override.

Three jobs beyond merging, each closing a real defect the review found:

  1. env: credential resolution (SKILL.md muc 3A) -- `password: "env:FOO"` is
     replaced by os.environ["FOO"]. A missing variable raises instead of
     silently logging in with the literal string "env:FOO", which would look
     like a wrong-password failure and waste a debugging session.

  2. Production safety gate (SKILL.md muc 13A) -- refuses to hand back a config
     pointing at prod. The skill drives a real browser and can mutate data, so
     this is a hard stop, not a warning.

  3. effective_config_table() -- the merged value of every key that exists in
     BOTH files, for writing into execution_summary.md. Without it a reader of
     the report cannot tell which file won.
"""
import copy
import os
import re

import yaml

# Keys duplicated across profile + manifest. Reported in the summary so the
# reader can see which source won for each one.
OVERLAPPING_KEYS = [
    "result_policy", "update_policy", "redmine.enabled", "redmine.bug_title_pattern",
    "output.execution_reports_root", "paths.execution_reports_root",
    "output.execution_evidence_root", "paths.execution_evidence_root",
]

# A base_url must contain one of these to be considered non-production.
NON_PROD_URL_MARKERS = ("uat", "stg", "staging", "dev", "test", "localhost", "127.0.0.1")
PROD_ENV_NAMES = ("PROD", "PRODUCTION", "LIVE")


class ConfigError(Exception):
    """Config is unusable -- caller must stop, never guess a default."""


def _deep_merge(base, override):
    """dict-wise merge; override wins. Lists are replaced whole, not concatenated
    (concatenating execution_columns across sources would silently widen the set
    of columns we are allowed to overwrite)."""
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _get_path(cfg, dotted):
    cur = cfg
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def resolve_env_refs(cfg, environ=None, skip_prefixes=()):
    """Replace every "env:NAME" string with the real value. Collects ALL missing
    variables before raising so the user fixes them in one pass.

    skip_prefixes: dotted config paths left unresolved -- used for blocks that
    are switched off (redmine.enabled = false must not demand a Redmine API key
    the run will never use)."""
    environ = os.environ if environ is None else environ
    missing = []

    def skipped(path):
        return any(path == p or path.startswith(p + ".") for p in skip_prefixes)

    def walk(node, path):
        if isinstance(node, dict):
            return {k: walk(v, "%s.%s" % (path, k) if path else k) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v, path) for v in node]
        if isinstance(node, str) and node.startswith("env:"):
            if skipped(path):
                return node
            name = node[4:].strip()
            if not name:
                missing.append("%s (ten bien rong)" % path)
                return node
            if name not in environ or environ[name] == "":
                missing.append("%s -> $%s" % (path, name))
                return node
            return environ[name]
        return node

    out = walk(cfg, "")
    if missing:
        raise ConfigError(
            "Thieu environment variable cho credential:\n  - " + "\n  - ".join(missing)
            + "\nSet cac bien nay roi chay lai. Khong login, khong tao bug."
        )
    return out


def check_environment_safety(cfg):
    """Return a list of reasons the target looks like production. Empty list ==
    safe to proceed. Caller must ask the user before continuing on non-empty."""
    env = cfg.get("environment") or {}
    safety = cfg.get("environment_safety") or {}
    if not safety.get("forbid_production", True):
        return []

    reasons = []
    name = str(env.get("name") or "").upper()
    if name in PROD_ENV_NAMES:
        reasons.append("environment.name = %s" % name)

    allowed = safety.get("allowed_environment_names")
    if allowed and name and name not in [str(a).upper() for a in allowed]:
        reasons.append("environment.name %s khong nam trong allowed_environment_names" % name)

    markers = safety.get("require_confirm_when_url_not_matching") or NON_PROD_URL_MARKERS
    url = str(env.get("base_url") or "").lower()
    if url and not any(m.lower() in url for m in markers):
        reasons.append("base_url %s khong chua dau hieu moi truong test nao" % url)
    return reasons


def effective_config_table(profile, manifest, merged):
    """Rows of (key, profile value, manifest value, effective value, winner) for
    keys present in both sources -- goes into execution_summary.md."""
    rows = []
    for key in OVERLAPPING_KEYS:
        p, m = _get_path(profile, key), _get_path(manifest, key)
        if p is None and m is None:
            continue
        winner = "manifest" if m is not None else "profile"
        rows.append({
            "key": key, "profile": p, "manifest": m,
            "effective": _get_path(merged, key), "winner": winner,
        })
    return rows


def load(profile_path, manifest_path, cli_overrides=None, environ=None):
    """Load -> merge -> resolve credentials. Does NOT enforce the safety gate;
    the caller runs check_environment_safety() so it can prompt the user."""
    with open(profile_path, encoding="utf-8") as fh:
        profile = yaml.safe_load(fh) or {}
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh) or {}
    merged = _deep_merge(_deep_merge(profile, manifest), cli_overrides or {})
    # A disabled block's credentials are irrelevant to this run.
    skip = () if (merged.get("redmine") or {}).get("enabled") else ("redmine",)
    merged = resolve_env_refs(merged, environ=environ, skip_prefixes=skip)

    mode = ((merged.get("run") or {}).get("execution_mode") or "baseline")
    if mode == "selected_cases" and not ((merged.get("case_filter") or {}).get("include_tc_ids")):
        raise ConfigError(
            "execution_mode = selected_cases nhung case_filter.include_tc_ids rong. "
            "Day la loi cau hinh, KHONG duoc hieu thanh 'chay het'."
        )
    return {
        "profile": profile, "manifest": manifest, "merged": merged,
        "effective_table": effective_config_table(profile, manifest, merged),
    }

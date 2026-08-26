#!/usr/bin/env python3
"""
Decide WHICH file the run writes results into, and keep that decision stable for
the whole run.

Three modes (update_policy.mode):

  in_place            -- ghi thang vao chinh file test case. Default.
  backup_then_update  -- copy file goc ra 1 ban backup, roi van ghi vao file goc.
  clone_then_write    -- clone file test case ra ban moi, ghi vao BAN CLONE,
                         file goc khong bi sua mot o nao.

None of them ever invents a new result file with its own layout: the target is
always the test case file itself or a byte-for-byte clone of it, so every column
the QA team wrote stays exactly where it was.

Why the state file: write-result is invoked once PER CASE. Without remembering
the target, clone_then_write would clone a fresh copy on every case and scatter
results across N files. resolve() clones on first call, records the target under
execution_runtime_root, and reuses it for the rest of the run. Starting a new run
means calling reset() first.
"""
import json
import os
import shutil

VALID_MODES = ("in_place", "backup_then_update", "clone_then_write")


class TargetError(Exception):
    pass


def _cfg(merged, *path, **kw):
    cur = merged
    for p in path:
        if not isinstance(cur, dict):
            return kw.get("default")
        cur = cur.get(p)
        if cur is None:
            return kw.get("default")
    return cur


def mode_of(merged):
    mode = (_cfg(merged, "update_policy", "mode")
            or _cfg(merged, "update_policy", "default_mode") or "in_place")
    mode = str(mode).strip()
    if mode not in VALID_MODES:
        raise TargetError("update_policy.mode %r khong hop le (chi %s)" % (mode, ", ".join(VALID_MODES)))
    return mode


def state_path(merged, module_name):
    root = (_cfg(merged, "paths", "execution_runtime_root")
            or _cfg(merged, "output", "execution_runtime_root") or "execution_runtime")
    return os.path.join(root, str(module_name or "unknown"), "target.json")


def read_state(merged, module_name):
    path = state_path(merged, module_name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_state(merged, module_name, state):
    path = state_path(merged, module_name)
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    return path


def reset(merged, module_name):
    """Forget the previous run's target so the next resolve() starts fresh."""
    path = state_path(merged, module_name)
    if os.path.exists(path):
        os.remove(path)
        return path
    return None


def _clone_excel(source_path, module_name, timestamp):
    if not source_path or not os.path.exists(source_path):
        raise TargetError("Khong tim thay file test case nguon: %r" % source_path)
    base, ext = os.path.splitext(source_path)
    target = "%s__executed_%s_%s%s" % (base, module_name, timestamp, ext)
    shutil.copy2(source_path, target)
    return target


def resolve(merged, module_name, timestamp, clone_google_sheet=None):
    """Return the state dict describing this run's write target.

    clone_google_sheet: callable(file_id, new_title) -> new_file_id. Injected by
    the caller so this module needs neither gspread nor network to be tested.
    """
    existing = read_state(merged, module_name)
    if existing:
        return existing                      # target da chot cho run nay

    mode = mode_of(merged)
    src = _cfg(merged, "testcase_source", default={}) or {}
    source_type = (src.get("source_type") or "google_sheet").strip()

    state = {"mode": mode, "source_type": source_type, "module_name": module_name,
             "source": src.get("local_excel_path") if source_type == "excel"
                       else src.get("google_sheet_file_id")}

    if mode == "clone_then_write":
        title = "%s__executed_%s" % (str(state["source"] or "testcases"), timestamp)
        if source_type == "excel":
            state["target"] = _clone_excel(state["source"], module_name, timestamp)
        else:
            if clone_google_sheet is None:
                raise TargetError("Thieu ham clone cho Google Sheet.")
            state["target"] = clone_google_sheet(state["source"], title)
        state["source_untouched"] = True
    else:
        state["target"] = state["source"]
        state["source_untouched"] = False
        if mode == "backup_then_update" and source_type == "excel":
            state["backup"] = _clone_excel(state["source"], module_name, "backup_" + timestamp)

    write_state(merged, module_name, state)
    return state


def apply_target(merged, state):
    """Return a copy of merged whose testcase_source points at the resolved
    target, so sheet_io.open_worksheet opens the right file without knowing
    anything about modes."""
    out = {k: v for k, v in merged.items()}
    src = dict(_cfg(merged, "testcase_source", default={}) or {})
    if state.get("source_type") == "excel":
        src["local_excel_path"] = state["target"]
    else:
        src["google_sheet_file_id"] = state["target"]
    out["testcase_source"] = src
    return out

#!/usr/bin/env python3
"""Rule 4: khong log bug trung.

Hai tang chan, vi mot tang khong du:

  Tang 1 -- registry local (<reports>/<module>/bug_registry.json). Nhanh, khong
            can mang, va bat duoc ca bug vua log 5 giay truoc trong cung run.
  Tang 2 -- search tren tracker. Bat duoc bug do NGUOI KHAC log tay, thu ma
            registry local khong the biet.

Khi bug cu da CLOSED -> khong skip ma tao bug moi danh dau regression. Bug tai
xuat hien sau khi da fix la thong tin quan trong, khong duoc lang di.

QUAN TRONG: entry trong registry duoc ghi voi closed=False luc tao va KHONG tu
doi khi issue duoc fix tren tracker. Nen khi co local hit, phai hoi lai tracker
trang thai hien tai qua closed_lookup. Thieu buoc nay thi mot bug da fix xong roi
tai xuat hien se bi skip VINH VIEN -- dung cai ma rule regression can bat.
"""
import hashlib
import json
import os
import re
import unicodedata

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)


def normalize(text):
    """Chuan hoa de so sanh: casefold + bo dau cau + gom khoang trang.
    GIU dau tieng Viet -- 'sai' va 'sài' la hai thu khac nhau."""
    norm = unicodedata.normalize("NFC", str(text or ""))
    norm = _PUNCT.sub(" ", norm.casefold())
    return _WS.sub(" ", norm).strip()


def fingerprint(bug):
    """Dau van tay cua mot bug. Cung man hinh + cung loai + cung noi dung
    => cung bug, du title co viet khac nhau chut.

    QUYET DINH (2026-08-26) -- parent_ticket CO Y KHONG nam trong day:
    hai bug trung khit noi dung nhung khac ticket cha van la CUNG MOT loi, va
    rule 4 noi "khong log bug trung". Truong hop chinh dang can ticket thu hai
    la bug da fix roi tai xuat hien -- cai do da co nhanh create_regression lo,
    khong can dua parent_ticket vao chu ky. Dua vao se lam moi vong test duoi
    ticket cha moi deu log lai y nguyen bo bug cu."""
    parts = [normalize(bug.get("screen")),
             normalize(bug.get("bug_type")),
             normalize(bug.get("ui_subtype")),
             normalize(bug.get("item")),
             normalize(bug.get("summary"))]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]


def registry_path(merged, module_name):
    root = ((merged.get("paths") or {}).get("bug_reports_root") or "bug_reports")
    return os.path.join(root, module_name or "_unknown", "bug_registry.json")


def load_registry(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        # Registry hong thi coi nhu rong, nhung KHONG ghi de mat du lieu cu:
        # caller se thay warning va nguoi doc quyet dinh.
        return {}


def save_entry(path, fprint, entry):
    registry = load_registry(path)
    registry[fprint] = entry
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(registry, fh, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, path)   # atomic: khong de lai registry nua vien khi crash
    return registry


def decide(bug, registry, remote_hits=None, title=None, closed_lookup=None):
    """Tra ve dict {action, reason, existing}.

    action: "create_new" | "skip_duplicate" | "create_regression"

    closed_lookup(issue_id) -> True/False/None: hoi tracker xem issue da dong
    chua. None = khong doc duoc -> tin gia tri luu trong registry. Bo qua tham so
    nay thi khong bao gio phat hien duoc regression (xem docstring dau file)."""
    fprint = fingerprint(bug)
    local = (registry or {}).get(fprint)

    if local:
        closed = bool(local.get("closed"))
        source = "registry"
        issue_id = local.get("issue_id")
        if closed_lookup and issue_id not in (None, ""):
            fresh = closed_lookup(issue_id)
            if fresh is not None:
                closed, source = bool(fresh), "tracker"
        if closed:
            return {"action": "create_regression", "fingerprint": fprint,
                    "existing": local, "status_source": source,
                    "reason": "Bug %s cùng dấu vân tay đã CLOSED (theo %s) — "
                              "tạo bug mới đánh dấu regression" % (issue_id, source)}
        return {"action": "skip_duplicate", "fingerprint": fprint,
                "existing": local, "status_source": source,
                "reason": "Bug %s cùng dấu vân tay vẫn còn OPEN (theo %s) — "
                          "không tạo bug trùng (rule 4)" % (issue_id, source)}

    # Tang 2: doi chieu title voi ket qua search tren tracker.
    norm_title = normalize(title or bug.get("summary"))
    for hit in (remote_hits or []):
        if normalize(hit.get("title")) != norm_title:
            continue
        if hit.get("closed"):
            return {"action": "create_regression", "fingerprint": fprint,
                    "existing": hit,
                    "reason": "Tracker: issue %s cùng title đã CLOSED — tạo bug "
                              "mới đánh dấu regression" % hit.get("id")}
        return {"action": "skip_duplicate", "fingerprint": fprint, "existing": hit,
                "reason": "Tracker: issue %s cùng title vẫn còn OPEN — không tạo "
                          "bug trùng (rule 4)" % hit.get("id")}

    return {"action": "create_new", "fingerprint": fprint, "existing": None,
            "reason": "Không tìm thấy bug trùng ở registry local lẫn trên tracker"}

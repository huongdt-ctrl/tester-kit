#!/usr/bin/env python3
"""Kiem tra truoc khi cham vao tracker.

Ly do ton tai: config sai (project_path go nham, priority_map dung ten khong co
tren tracker) truoc day chi lo ra luc DANG tao bug -- HTTP 400/404 giua chung,
sau khi mot vai ticket that da duoc tao. Kiem o day de biet truoc, khi chua tao
gi ca.
"""


def check_project(adapter):
    """{ok: True/False/None, detail}. None = khong kiem duoc -> canh bao."""
    try:
        return adapter.verify_project()
    except Exception as exc:            # noqa: BLE001 -- preflight khong duoc chet
        return {"ok": None, "detail": "loi khi kiem tra project: %s" % exc}


def check_priority_map(adapter, policy):
    """Doi chieu gia tri priority_map voi ten priority that tren tracker.

    Chi bao loi khi CHAC CHAN sai (doc duoc danh sach va gia tri khong co trong
    do). Khong doc duoc -> bo qua, khong doan."""
    pmap = (policy or {}).get("priority_map") or {}
    if not pmap:
        return {"ok": None, "detail": "khong khai priority_map"}
    try:
        valid = adapter.list_priorities()
    except Exception as exc:            # noqa: BLE001
        return {"ok": None, "detail": "khong doc duoc danh sach priority: %s" % exc}
    if valid is None:
        return {"ok": None,
                "detail": "tracker %s khong co khai niem priority de doi chieu"
                          % adapter.name}
    valid_set = {str(v) for v in valid if v}
    bad = sorted({str(v) for v in pmap.values() if v and str(v) not in valid_set})
    if bad:
        return {"ok": False,
                "detail": "priority_map tro toi gia tri khong co tren tracker: %s. "
                          "Gia tri hop le: %s"
                          % (", ".join(bad), ", ".join(sorted(valid_set)))}
    return {"ok": True, "detail": "priority_map khop tracker (%d gia tri)" % len(pmap)}


def blocking_reasons(checks):
    """Chi cai ok=False moi chan. ok=None la canh bao, van cho chay tiep."""
    return ["%s: %s" % (name, res.get("detail"))
            for name, res in checks.items() if res.get("ok") is False]

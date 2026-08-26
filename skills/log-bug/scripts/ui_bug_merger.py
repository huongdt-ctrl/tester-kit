#!/usr/bin/env python3
"""Quyet dinh nhom bug UI nao duoc GOP thanh 1 ticket.

Rule goc: nguyen tac chung la moi loi 1 bug (rule 3). Nhung log rieng tung bug
UI thi mat qua nhieu thoi gian, nen team cho phep DUNG HAI ngoai le:

  Case A -- cung 1 test object (man hinh/tinh nang), NHIEU ITEM nhung CUNG 1
            loai bug. VD: 5 cho sai chinh ta tren cung man hinh Login.
  Case B -- cung 1 item co 3 den 5 loi nho.

Ba dieu duoc quyet dinh co chu y o day:
  - Bug LOGIC khong bao gio gop. Ngoai le chi danh cho UI; gop bug logic la lam
    mat kha nang track tung loi mot.
  - Case A BAT BUOC trai tren >= 2 item KHAC NHAU. Rule goc noi ro "bug xay ra
    o nhieu item nhung cung 1 loai bug" -- nhieu loi CUNG loai tren CUNG 1 item
    la dia hat cua Case B, khong phai Case A. Thieu dieu kien nay thi Case A se
    an het nhom cua Case B va nguong 3-5 tro thanh vo nghia.
  - Case A xet TRUOC Case B. Cung 1 loai loi tren nhieu item la nhom sach hon,
    it gay tranh cai khi fix.
  - Cung 1 item nhung > 5 loi thi KHONG tu gop -> tra ve needs_confirm. Rule chi
    phu 3->5; qua nguong do co the la man hinh lam sai hang loat, dang mot bug
    rieng chu khong phai mot bug gop.
"""
from collections import OrderedDict

MIN_SAME_ITEM = 3      # Case B: tu 3 loi nho tro len moi dang gop
MAX_SAME_ITEM = 5      # Case B: tren 5 thi phai hoi nguoi


def _key(bug, *fields):
    return tuple(str(bug.get(f) or "").strip().lower() for f in fields)


def _group(bugs, indices, *fields):
    buckets = OrderedDict()
    for idx in indices:
        buckets.setdefault(_key(bugs[idx], *fields), []).append(idx)
    return buckets


def plan_merge(bugs, min_same_item=MIN_SAME_ITEM, max_same_item=MAX_SAME_ITEM):
    """bugs: list dict. Tra ve ke hoach gop, khong sua input.

    {"merge": [...], "separate": [...], "needs_confirm": [...]}
    """
    merge, separate, needs_confirm = [], [], []

    ui_idx, logic_idx = [], []
    for idx, bug in enumerate(bugs):
        if str(bug.get("bug_type") or "").strip().lower() == "ui":
            ui_idx.append(idx)
        else:
            logic_idx.append(idx)

    # Bug logic: moi loi 1 bug, khong ngoai le.
    for idx in logic_idx:
        separate.append({"indices": [idx],
                         "reason": "Bug logic — rule 3: mỗi lỗi log 1 bug, "
                                   "không áp dụng ngoại lệ gộp"})

    # Case A: cung (man hinh, loai loi UI) VA trai tren >= 2 item khac nhau.
    used = set()
    for key, idxs in _group(bugs, ui_idx, "screen", "ui_subtype").items():
        items = {str(bugs[i].get("item") or "").strip().lower() for i in idxs}
        items.discard("")
        if len(idxs) >= 2 and len(items) >= 2:
            merge.append({
                "indices": list(idxs), "case": "A",
                "group_key": {"screen": key[0], "ui_subtype": key[1]},
                "item_count": len(items),
                "reason": "Case A: cùng test object %r, cùng loại bug UI %r trên "
                          "%d item khác nhau — gộp 1 bug"
                          % (key[0], key[1], len(items)),
            })
            used.update(idxs)

    # Case B: cung (man hinh, item), 3..5 loi nho.
    rest = [i for i in ui_idx if i not in used]
    for key, idxs in _group(bugs, rest, "screen", "item").items():
        count = len(idxs)
        if not key[1]:
            for idx in idxs:
                separate.append({"indices": [idx],
                                 "reason": "Chưa khai field 'item' nên không xét "
                                           "được Case B — log riêng"})
            continue
        if min_same_item <= count <= max_same_item:
            merge.append({
                "indices": list(idxs), "case": "B",
                "group_key": {"screen": key[0], "item": key[1]},
                "reason": "Case B: cùng item %r có %d lỗi nhỏ (ngưỡng %d-%d) — "
                          "gộp 1 bug" % (key[1], count, min_same_item, max_same_item),
            })
        elif count > max_same_item:
            needs_confirm.append({
                "indices": list(idxs), "case": "B-overflow",
                "group_key": {"screen": key[0], "item": key[1]},
                "reason": "Cùng item %r có %d lỗi, vượt ngưỡng %d của Case B. "
                          "Rule chỉ phủ %d-%d lỗi — HỎI user trước khi gộp"
                          % (key[1], count, max_same_item, min_same_item, max_same_item),
            })
        else:
            for idx in idxs:
                separate.append({
                    "indices": [idx],
                    "reason": "Chỉ %d lỗi trên item %r, chưa đạt ngưỡng gộp %d — "
                              "log riêng" % (count, key[1], min_same_item)})

    return {"merge": merge, "separate": separate, "needs_confirm": needs_confirm}


def build_merged_bug(bugs, group):
    """Dung 1 bug dai dien tu mot nhom. Giu bug dau lam goc, gom summary cac
    bug con lai vao 'items' de nguoi fix thay du danh sach."""
    idxs = group["indices"]
    base = dict(bugs[idxs[0]])
    items = []
    for idx in idxs:
        bug = bugs[idx]
        label = bug.get("item") or bug.get("screen") or "?"
        items.append("%s: %s" % (label, bug.get("summary") or "-"))
    base["items"] = items
    base["merged_from_count"] = len(idxs)

    if group.get("case") == "A":
        subtype = group["group_key"].get("ui_subtype") or "UI"
        base["summary"] = ("Lỗi UI %s tại %d vị trí trên %s"
                           % (subtype, len(idxs), base.get("screen") or "?"))
    else:
        base["summary"] = ("%d lỗi UI nhỏ tại %s"
                           % (len(idxs), group["group_key"].get("item") or "?"))
    return base

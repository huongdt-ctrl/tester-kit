#!/usr/bin/env python3
"""Bien danh sach bug tho thanh danh sach bug SE TAO (da gop theo rule UI).

Tach rieng khoi commands.py vi day la quyet dinh nghiep vu (gop cai gi), khong
phai viec dieu phoi CLI. Nhan thang dict `ui_cfg` chu khong nhan config da merge
-> test duoc ma khong can dung ca bo config.
"""
import ui_bug_merger


def merge_plan(bugs, ui_cfg):
    """None = ui_merge bi tat -> moi loi 1 bug (rule 3)."""
    ui_cfg = ui_cfg or {}
    if ui_cfg.get("enabled", True) is False:
        return None
    return ui_bug_merger.plan_merge(
        bugs, min_same_item=int(ui_cfg.get("min_errors_same_item", 3)),
        max_same_item=int(ui_cfg.get("max_errors_same_item", 5)))


def apply_merge(bugs, ui_cfg):
    """Tra ve (bugs_to_create, plan).

    Khong co buoc nay thi merge-check chi la bao cao de doc: `create` van tao 1
    ticket cho moi dong, 8 bug UI gop duoc van thanh 8 ticket.

    bugs_to_create = None khi plan co needs_confirm -> caller phai DUNG hoi user,
    khong duoc tu gop vuot nguong ma rule khong phu.
    """
    plan = merge_plan(bugs, ui_cfg)
    if plan is None:
        return list(bugs), None
    if plan["needs_confirm"]:
        return None, plan

    out, used = [], set()
    for group in plan["merge"]:
        out.append(ui_bug_merger.build_merged_bug(bugs, group))
        used.update(group["indices"])
    # Bug khong thuoc nhom nao giu nguyen thu tu ban dau.
    out.extend(bugs[i] for i in range(len(bugs)) if i not in used)
    return out, plan

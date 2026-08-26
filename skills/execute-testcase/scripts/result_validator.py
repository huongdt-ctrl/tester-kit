#!/usr/bin/env python3
"""
Validate a result BEFORE it reaches the sheet.

These are the rules the review found spread across three places with three
different strictness levels (SKILL.md muc 9A/9B). Centralising them here means
the CLI cannot accidentally write a Fail with no evidence, and the rules are
testable without a sheet.
"""

DEFAULT_STATUSES = ("Pass", "Fail", "N/A", "Untested", "Pending")
NOT_TESTABLE_STATUSES = ("Pending", "Untested")


class ResultValidationError(Exception):
    pass


def validate(status, remark, actual, mapping, merged):
    """Raise ResultValidationError on anything that must not be written."""
    policy = merged.get("result_policy") or {}
    allowed = policy.get("allowed_statuses") or list(DEFAULT_STATUSES)
    status = str(status or "").strip()
    remark = remark or ""
    actual = actual or ""

    if status not in allowed:
        raise ResultValidationError(
            "status %r khong hop le, chi nhan %s" % (status, allowed))

    if status in NOT_TESTABLE_STATUSES and policy.get("mandatory_remark_when_not_testable", True):
        if not remark.strip():
            prefix = policy.get("not_testable_remark_prefix") or "Chưa test được:"
            raise ResultValidationError(
                "Status %s bat buoc co Remark dang '%s <ly do>'" % (status, prefix))

    if status == "Fail":
        if policy.get("mandatory_remark_when_fail", True) and not remark.strip():
            prefix = policy.get("fail_remark_prefix") or "Actual khác Expected:"
            raise ResultValidationError(
                "Case Fail bat buoc co Remark dang '%s <mo ta>'" % prefix)
        # Chi doi Actual Result khi template that su co cot do.
        if "actual_result" in mapping and not actual.strip():
            raise ResultValidationError("Case Fail bat buoc ghi ca Actual Result (muc 9B)")

    return True

#!/usr/bin/env python3
"""Interface chung cho 3 tracker khi THU THAP bug theo giai doan.

Khac voi adapter cua skill log-bug (chuyen TAO issue), bo adapter nay chi DOC:
list bug theo nhan/loai + khoang ngay tao. Khong co method nao ghi len tracker.

Moi adapter tra ve list dict da chuan hoa -- phan con lai cua skill khong biet
minh dang doc tracker nao:
    {id, title, url, labels, milestone, priority, status, created_at}
"""

DEFAULT_PAGE_SIZE = 100
MAX_PAGES = 50          # chan vong lap vo han khi tracker tra page la


class TrackerError(Exception):
    """Loi khi goi tracker. Message phai noi ro tracker nao + HTTP code."""


class BaseAdapter:
    name = "base"
    required = ()

    def __init__(self, cfg):
        self.cfg = cfg or {}
        self.base_url = str(self.cfg.get("base_url") or "").rstrip("/")
        # True khi vong phan trang cham tran MAX_PAGES ma tracker VAN con du
        # lieu -> danh sach bug tra ve bi cat. Khong co co nay thi bao cao
        # thieu bug ma khong ai biet.
        self.truncated = False

    def missing_config(self, keys=None):
        return [k for k in (keys or self.required) if not self.cfg.get(k)]

    def _timeout(self):
        return int(self.cfg.get("timeout_seconds") or 30)

    def _page_size(self):
        return int(self.cfg.get("page_size") or DEFAULT_PAGE_SIZE)

    def _require(self):
        miss = self.missing_config()
        if miss:
            raise TrackerError("%s thieu cau hinh: %s" % (self.name, ", ".join(miss)))

    def list_bugs(self, date_from, date_to):
        """Bug duoc TAO trong [date_from, date_to] (YYYY-MM-DD, bao gom 2 dau)."""
        raise NotImplementedError

    def verify(self):
        """Kiem tra config truoc khi goi that. {ok, detail}; ok=None = khong kiem duoc."""
        return {"ok": None, "detail": "adapter chua ho tro kiem tra"}


def normalize(issue_id, title, url, labels=None, milestone=None, priority=None,
              status=None, created_at=None):
    return {
        "id": str(issue_id), "title": str(title or "").strip(), "url": url or "",
        "labels": list(labels or []), "milestone": milestone or "",
        "priority": priority or "", "status": status or "", "created_at": created_at or "",
    }

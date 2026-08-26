#!/usr/bin/env python3
"""Interface chung cho moi tracker (Redmine / GitLab / Jira).

Muc dich cua lop nay: phan con lai cua skill KHONG BAO GIO biet minh dang noi
voi tracker nao. Doi tracker = doi 1 dong config, khong sua logic dedup/template.

Hai thu moi adapter phai khai bao:
  markup   -- "textile" hay "markdown", quyet dinh cach render heading
  supports -- set field ma tracker nhan NATIVE. Field khong nam trong set nay
              se bi day xuong description (quyet dinh 2026-08-25), thay vi bi
              am tham danh roi.
"""

CLOSED_STATUS_NAMES = (
    "closed", "rejected", "resolved", "done", "won't fix", "wontfix",
    "duplicate", "invalid", "da dong", "đã đóng",
)


class TrackerError(Exception):
    """Loi khi goi tracker. Message phai noi ro tracker nao + HTTP code."""


class BaseAdapter:
    name = "base"
    markup = "markdown"
    # Field tracker nhan native. Cai gi khong co o day -> nhung vao description.
    supports = frozenset()
    # Field config bat buoc de goi duoc tracker nay. Moi adapter tu khai -> chi
    # co MOT nguon su that, caller khong phai giu bang thu hai roi lech nhau.
    required = ()

    def __init__(self, cfg):
        self.cfg = cfg or {}
        self.base_url = str(self.cfg.get("base_url") or "").rstrip("/")

    # --- cac method con phai override ---

    def create_issue(self, title, description, fields):
        """Tao issue. Tra ve (issue_id, issue_url)."""
        raise NotImplementedError

    def get_issue_status(self, issue_id):
        """Ten status hien tai, hoac None khi khong doc duoc."""
        raise NotImplementedError

    def verify_project(self):
        """Project khai trong config co that va token co quyen doc khong?

        Tra ve dict {ok, detail}. ok=None nghia la khong kiem duoc (mat mang...)
        -- caller coi la canh bao chu khong phai loi.

        Muc dich: bien mot cai 404/403 luc dang tao bug (khi da muon) thanh mot
        loi preflight ro rang truoc khi cham vao tracker."""
        return {"ok": None, "detail": "adapter chua ho tro kiem tra project"}

    def list_priorities(self):
        """Ten priority hop le tren tracker, hoac None khi tracker khong co khai
        niem nay (GitLab) / khong doc duoc. Dung de doi chieu priority_map."""
        return None

    def search_issues(self, text, limit=20):
        """Tim issue theo text trong title. Tra ve list dict:
        {id, title, url, status, closed}. Loi mang -> tra [] (khong raise),
        vi dedup thieu con do hon la chan dung ca run."""
        raise NotImplementedError

    # --- helper dung chung ---

    @staticmethod
    def is_closed(status_name):
        return str(status_name or "").strip().lower() in CLOSED_STATUS_NAMES

    def unsupported_fields(self, fields):
        """Field co gia tri nhung tracker khong nhan native -> caller nhung
        vao description de khong mat thong tin."""
        out = {}
        for key, val in (fields or {}).items():
            if val in (None, "", [], {}):
                continue
            if key not in self.supports:
                out[key] = val
        return out

    def missing_config(self, required=None):
        required = required if required is not None else self.required
        miss = [f for f in required if not self.cfg.get(f)]
        # 'env:' con nguyen nghia la config_loader chua resolve credential.
        for f in required:
            if str(self.cfg.get(f) or "").startswith("env:"):
                miss.append("%s (chua resolve tu environment variable)" % f)
        return miss

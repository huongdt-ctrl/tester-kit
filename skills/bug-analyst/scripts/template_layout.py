#!/usr/bin/env python3
"""Toa do sheet 'List bug' (TEM-ST03_02) + toan bo phep dich dong.

Template goc chi chua 37 dong bug (row 3..39), 12 slot man hinh (43..54) va 5
slot milestone (61..65). Giai doan nao vuot nguong do thi skill CHEN them dong,
va MOI toa do nam duoi diem chen bi day xuong.

Module nay la NGUON SU THAT DUY NHAT ve toa do. Khong module nao duoc tu hardcode
so dong -- hoi Layout, neu khong thi sua template mot cho se vo mot cho khac.
"""
from collections import namedtuple

SHEET_NAME = "List bug"
HEADER_ROW = 2
DATA_START = 3
DATA_SLOTS = 37                 # row 3..39 trong template goc
DATA_LAST_COL = 13              # den cot M

# Cot vung data, theo header row 2 cua template.
COL_NO, COL_EGG_ID, COL_EGG_NAME = "A", "B", "C"
COL_SCREEN, COL_MILESTONE, COL_TITLE = "D", "E", "F"
COL_PRIORITY, COL_SEVERITY, COL_TYPE = "G", "H", "I"
COL_CAUSE, COL_ROOT_CAUSE, COL_NOTE = "J", "K", "L"

# Cot co dropdown -> sqref phai gian theo so dong bug that.
VALIDATED_COLS = (COL_PRIORITY, COL_SEVERITY, COL_TYPE, COL_CAUSE, COL_ROOT_CAUSE)

# first  : dong dau tien cua bang thong ke (toa do GOC)
# slots  : so dong template chua san
# total  : dong TOTAL (toa do GOC)
# src_col: cot trong vung data ma COUNTIF dem
# dynamic: nhan lay tu du lieu that (True) hay giu nguyen nhan template (False)
Block = namedtuple(
    "Block", "key first slots total label_col count_col pct_col src_col dynamic")

BLOCKS = (
    # II  - theo man hinh
    Block("screen",     43, 12,  55, "A", "B", "C", COL_SCREEN,     True),
    # III - theo milestone. src_col = E: template goc ghi nham G (Priority).
    Block("milestone",  61,  5,  66, "A", "B", "C", COL_MILESTONE,  True),
    # IV  - theo priority
    Block("priority",   71,  5,  76, "A", "B", "C", COL_PRIORITY,   False),
    # V   - theo severity
    Block("severity",   88,  5,  93, "A", "B", "C", COL_SEVERITY,   False),
    # VI  - theo cause category
    Block("cause",     105, 17, 122, "A", "D", "E", COL_CAUSE,      False),
    # VII - theo root cause
    Block("rootcause", 126, 26, 152, "A", "D", "E", COL_ROOT_CAUSE, False),
)
BLOCK_BY_KEY = {b.key: b for b in BLOCKS}
BLOCK_KEYS = tuple(b.key for b in BLOCKS)

ISSUE_TABLE_HEADER = 154        # bang No./Issue/Action/Status/PIC (toa do GOC)


class Layout:
    """Toa do THAT SU cua file output, sau khi da chen du dong.

    block_rows: {ten_block: so dong CAN CO}. Thieu key nao thi block do dung
    dung so dong template co san. MOI block deu gian duoc -- khong chi bang
    man hinh / milestone: bang Cause cung phai gian de chua het 22 muc danh muc
    (template chi liet ke 17).
    """

    def __init__(self, n_bugs=0, block_rows=None):
        self.n_bugs = int(n_bugs or 0)
        needed = dict(block_rows or {})
        self.extra = {"data": max(0, self.n_bugs - DATA_SLOTS)}
        for key in BLOCK_KEYS:
            self.extra[key] = max(0, int(needed.get(key) or 0) - BLOCK_BY_KEY[key].slots)

        # (chen TRUOC dong nay theo toa do GOC, so dong chen).
        self.insertions = []
        if self.extra["data"]:
            self.insertions.append((DATA_START + DATA_SLOTS, self.extra["data"]))
        for key in BLOCK_KEYS:
            if self.extra[key]:
                # Chen ngay truoc dong TOTAL -> bang dai them, TOTAL tut xuong.
                self.insertions.append((BLOCK_BY_KEY[key].total, self.extra[key]))

    def shift(self, base_row):
        """Toa do GOC -> toa do file output."""
        return base_row + sum(c for pos, c in self.insertions if pos <= base_row)

    def insertions_bottom_up(self):
        """Chen tu duoi len: nhu vay moi vi tri chen con lai van dung toa do GOC."""
        return sorted(self.insertions, key=lambda pair: -pair[0])

    @property
    def data_end(self):
        return DATA_START + DATA_SLOTS - 1 + self.extra["data"]

    @property
    def data_rows(self):
        return range(DATA_START, self.data_end + 1)

    def block(self, key):
        b = BLOCK_BY_KEY[key]
        first = self.shift(b.first)
        slots = b.slots + self.extra.get(key, 0)
        return {
            "key": key, "first": first, "last": first + slots - 1,
            "total": self.shift(b.total), "slots": slots,
            "header": first - 1,
            "label_col": b.label_col, "count_col": b.count_col,
            "pct_col": b.pct_col, "src_col": b.src_col, "dynamic": b.dynamic,
        }

    def blocks(self):
        return [self.block(b.key) for b in BLOCKS]

    @property
    def issue_table_header(self):
        return self.shift(ISSUE_TABLE_HEADER)

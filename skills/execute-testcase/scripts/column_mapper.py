#!/usr/bin/env python3
"""
Map the sheet's real header row onto logical column names.

Closes the defect where a missing Priority / Classification column made every
case_filter match nothing and the run reported "0 test cases" as if that were a
legitimate result (SKILL.md muc 6A). Here a column the filter needs but the
sheet lacks is an ERROR, never an empty result set.

Alias sources, in order: column_mapping (exact header from manifest), then
column_header_aliases (profile). Matching is case-insensitive and
whitespace-tolerant because real QA sheets drift ("Test data" vs "Test Data").
"""

# Columns every run needs regardless of configuration.
REQUIRED_LOGICAL = [
    "tc_id", "title", "preconditions", "steps", "test_data",
    "expected_result", "test_result", "test_date", "tested_by", "remark",
]

# filter config key -> logical column it reads. Required ONLY when that filter
# is actually in use (non-empty list).
FILTER_COLUMN_DEPS = {
    "include_priorities": "priority",
    "exclude_priorities": "priority",
    "include_classification_1": "classification_1",
    "exclude_classification_1": "classification_1",
}

# Fallback aliases for columns the config files don't alias but filters need.
_BUILTIN_ALIASES = {
    "priority": ["Priority", "Prio", "Do uu tien"],
    "classification_1": ["Classification 1", "Classification1", "Category", "Phan loai 1"],
}


class ColumnMappingError(Exception):
    """Header row cannot satisfy what the config asks for."""


def _norm(s):
    return " ".join(str(s or "").split()).strip().lower()


def build_alias_index(merged_cfg):
    """logical name -> list of acceptable header spellings."""
    aliases = {}
    for logical, names in (merged_cfg.get("column_header_aliases") or {}).items():
        aliases[logical] = list(names or [])
    # manifest's exact mapping is the strongest hint -> put it first
    for logical, header in (merged_cfg.get("column_mapping") or {}).items():
        aliases.setdefault(logical, [])
        if header and header not in aliases[logical]:
            aliases[logical].insert(0, header)
    for logical, names in _BUILTIN_ALIASES.items():
        aliases.setdefault(logical, [])
        for n in names:
            if n not in aliases[logical]:
                aliases[logical].append(n)
    return aliases


def map_columns(header_row, merged_cfg):
    """Return {logical_name: zero-based column index} for every column found."""
    aliases = build_alias_index(merged_cfg)
    by_norm = {}
    for idx, cell in enumerate(header_row):
        key = _norm(cell)
        if key and key not in by_norm:      # first occurrence wins on duplicates
            by_norm[key] = idx

    mapping = {}
    for logical, names in aliases.items():
        for name in names:
            idx = by_norm.get(_norm(name))
            if idx is not None:
                mapping[logical] = idx
                break
    return mapping


def active_filter_requirements(merged_cfg):
    """Logical columns that are mandatory because a filter actually uses them."""
    case_filter = merged_cfg.get("case_filter") or {}
    needed = {}
    for cfg_key, logical in FILTER_COLUMN_DEPS.items():
        if case_filter.get(cfg_key):        # non-empty list only
            needed.setdefault(logical, []).append(cfg_key)
    return needed


def validate_mapping(mapping, merged_cfg):
    """Raise on anything that would corrupt the run or silently empty it.

    Returns the list of filter keys that the caller may drop only after the user
    explicitly agrees (never dropped automatically)."""
    missing_required = [c for c in REQUIRED_LOGICAL if c not in mapping]
    if missing_required:
        raise ColumnMappingError(
            "Thieu cot bat buoc trong header: %s" % ", ".join(missing_required)
        )

    blocked = []
    for logical, filter_keys in active_filter_requirements(merged_cfg).items():
        if logical not in mapping:
            for fk in filter_keys:
                blocked.append((fk, logical))
    if blocked:
        detail = "; ".join("filter %s can cot '%s'" % (fk, lg) for fk, lg in blocked)
        raise ColumnMappingError(
            "Thieu cot dung de filter: %s. KHONG duoc tra ve 0 test case. "
            "Chi chay tiep khi user dong y bo filter tuong ung." % detail
        )
    return []

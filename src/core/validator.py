"""Kiểm tra toàn bộ segment table."""
from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_MEM_SIZE = 5000
INVALID_RANGE = "INVALID_RANGE"
INVALID_PERM = "INVALID_PERM"
EXCEEDS_MEMORY = "EXCEEDS_MEMORY"
OVERLAP = "OVERLAP"
_PERM_RE = re.compile(r"^[R-][W-][X-]$")


@dataclass(frozen=True)
class ValidationIssue:
    kind: str
    seg_ids: tuple
    message: str


def get_segments(table):
    if isinstance(table, dict):
        return list(table.values())
    return list(table)


def find_overlaps(segments):
    ordered = sorted(segments, key=lambda s: (s.base, s.seg_id))
    issues = []
    for i, a in enumerate(ordered):
        a_end = a.base + a.limit
        j = i + 1
        while j < len(ordered) and ordered[j].base < a_end:
            b = ordered[j]
            b_end = b.base + b.limit
            lo, hi = b.base, min(a_end, b_end)
            issues.append(ValidationIssue(OVERLAP, (a.seg_id, b.seg_id),
                f"Segment {a.seg_id} [{a.base}, {a_end}) chồng lấn segment {b.seg_id} "
                f"tại vùng [{lo}, {hi})"))
            j += 1
    return issues


def validate_table(table, mem_size=None):
    if mem_size is None:
        mem_size = getattr(table, "mem_size", DEFAULT_MEM_SIZE)
    if mem_size <= 0:
        raise ValueError("mem_size phải > 0")

    issues = []
    usable = []
    for seg in get_segments(table):
        perm = str(getattr(seg, "perm", "---")).strip()
        if not _PERM_RE.fullmatch(perm):
            issues.append(ValidationIssue(
                INVALID_PERM,
                (seg.seg_id,),
                f"Segment {seg.seg_id} có perm '{perm}' không hợp lệ "
                f"(chỉ nhận chữ hoa đúng dạng R/-, W/-, X-; ví dụ R-X)",
            ))
        if seg.base < 0 or seg.limit <= 0:
            issues.append(ValidationIssue(INVALID_RANGE, (seg.seg_id,),
                f"Segment {seg.seg_id} có base={seg.base}, limit={seg.limit} không hợp lệ"))
            continue
        end = seg.base + seg.limit
        if end > mem_size:
            issues.append(ValidationIssue(EXCEEDS_MEMORY, (seg.seg_id,),
                f"Segment {seg.seg_id} [{seg.base}, {end}) vượt kích thước bộ nhớ {mem_size} byte"))
        usable.append(seg)

    issues.extend(find_overlaps(usable))
    return issues


def is_valid(table, mem_size=None):
    return not validate_table(table, mem_size)

"""validator.py - TV5: kiểm tra tổng thể segment table so với bộ nhớ vật lý.

Hợp đồng:
    validate_table(table, mem_size=None) -> list[ValidationIssue]

`table` là core.result_types.SegmentTable (duyệt được, mỗi phần tử là Segment).
Nếu không truyền mem_size thì lấy table.mem_size (mặc định 5000 byte).

Mỗi segment chiếm khoảng nửa mở [base, base + limit) trong bộ nhớ vật lý.
Các vấn đề được báo cáo (khớp mục "Xử lý dữ liệu sai" trong README):
    INVALID_RANGE   : base < 0 hoặc limit <= 0
    INVALID_PERM    : perm không đúng dạng 3 ký tự [R-][W-][X-]
    EXCEEDS_MEMORY  : base + limit > mem_size
    OVERLAP         : hai segment dùng chung ít nhất một byte vật lý

Hai segment chỉ "chạm nhau" (end của segment này == base của segment kia)
thì KHÔNG phải overlap, vì khoảng là nửa mở.

Độ phức tạp: O(n log n) cho bước sắp xếp + O(k) với k là số cặp overlap.
"""
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
    """Lấy danh sách Segment từ table (SegmentTable, dict hoặc iterable)."""
    if isinstance(table, dict):
        return list(table.values())
    return list(table)


def find_overlaps(segments):
    """Trả về mọi cặp segment chồng lấn nhau (mỗi cặp một lần)."""
    ordered = sorted(segments, key=lambda s: (s.base, s.seg_id))
    issues = []
    for i, a in enumerate(ordered):
        a_end = a.base + a.limit
        j = i + 1
        # ordered theo base tăng dần nên có thể dừng ngay khi b.base >= a_end
        while j < len(ordered) and ordered[j].base < a_end:
            b = ordered[j]
            b_end = b.base + b.limit
            lo, hi = b.base, min(a_end, b_end)
            issues.append(
                ValidationIssue(
                    OVERLAP,
                    (a.seg_id, b.seg_id),
                    f"Segment {a.seg_id} [{a.base}, {a_end}) chồng lấn "
                    f"segment {b.seg_id} [{b.base}, {b_end}) "
                    f"tại vùng [{lo}, {hi})",
                )
            )
            j += 1
    return issues


def validate_table(table, mem_size=None):
    """Phát hiện segment sai khoảng, sai perm, vượt bộ nhớ vật lý và chồng lấn."""
    if mem_size is None:
        mem_size = getattr(table, "mem_size", DEFAULT_MEM_SIZE)
    if mem_size <= 0:
        raise ValueError("mem_size phải > 0")

    issues = []
    usable = []
    for seg in get_segments(table):
        perm = getattr(seg, "perm", "---")
        if not _PERM_RE.match(str(perm)):
            issues.append(
                ValidationIssue(
                    INVALID_PERM,
                    (seg.seg_id,),
                    f"Segment {seg.seg_id} có perm '{perm}' không hợp lệ "
                    f"(cần 3 ký tự dạng R/-, W/-, X/-, ví dụ R-X)",
                )
            )
        if seg.base < 0 or seg.limit <= 0:
            issues.append(
                ValidationIssue(
                    INVALID_RANGE,
                    (seg.seg_id,),
                    f"Segment {seg.seg_id} có base={seg.base}, limit={seg.limit} "
                    f"không hợp lệ (cần base >= 0 và limit > 0)",
                )
            )
            continue
        end = seg.base + seg.limit
        if end > mem_size:
            issues.append(
                ValidationIssue(
                    EXCEEDS_MEMORY,
                    (seg.seg_id,),
                    f"Segment {seg.seg_id} [{seg.base}, {end}) vượt kích thước "
                    f"bộ nhớ vật lý {mem_size} byte",
                )
            )
        usable.append(seg)

    issues.extend(find_overlaps(usable))
    return issues


def is_valid(table, mem_size=None):
    return not validate_table(table, mem_size)

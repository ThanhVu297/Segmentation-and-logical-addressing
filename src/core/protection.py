from .result_types import ACCESS_TYPES, FaultResult, Status


def check_permission(perm: str, access: str) -> bool:
    """Kiểm tra quyền theo định dạng [R-][W-][X-]."""
    if not isinstance(perm, str) or len(perm) != len(ACCESS_TYPES):
        return False
    if not isinstance(access, str) or access not in ACCESS_TYPES:
        return False
    if any(char not in (expected, "-")
           for char, expected in zip(perm, ACCESS_TYPES)):
        return False

    return perm[ACCESS_TYPES.index(access)] == access


def check_fault(table, seg_id: int, offset: int, access: str) -> FaultResult:
    """Kiểm tra lỗi theo thứ tự: segment, offset, rồi quyền truy cập."""
    seg = table.get(seg_id)
    if seg is None:
        return FaultResult(
            status=Status.SEGMENT_FAULT,
            reason=f"Segment {seg_id} không tồn tại trong bảng phân đoạn",
        )

    if isinstance(seg, dict):
        limit = seg.get("limit")
        perm = seg.get("perm")
    else:
        limit = getattr(seg, "limit", None)
        perm = getattr(seg, "perm", None)

    if offset < 0 or offset >= limit:
        return FaultResult(
            status=Status.OFFSET_OUT_OF_RANGE,
            reason=(
                f"Offset {offset} vượt quá giới hạn limit {limit} "
                f"của segment {seg_id}"
            ),
        )

    if not check_permission(perm, access):
        return FaultResult(
            status=Status.PROTECTION_FAULT,
            reason=(
                f"Thao tác {access} không hợp lệ với quyền {perm} "
                f"của segment {seg_id}"
            ),
        )

    return FaultResult(status=Status.OK, reason="")

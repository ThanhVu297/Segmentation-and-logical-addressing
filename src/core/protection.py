from .result_types import ACCESS_TYPES, FaultResult, Status


def check_permission(perm: object, access: object) -> bool:
    """Kiểm tra quyền theo đúng định dạng [R-][W-][X-]; chỉ nhận chữ hoa."""
    if not isinstance(perm, str) or not isinstance(access, str):
        return False

    perm = perm.strip()
    access = access.strip()

    if len(perm) != len(ACCESS_TYPES):
        return False
    if access not in ACCESS_TYPES:
        return False
    if any(char not in (expected, "-")
           for char, expected in zip(perm, ACCESS_TYPES)):
        return False

    return perm[ACCESS_TYPES.index(access)] == access


def check_fault(table, seg_id: int, offset: int, access: str) -> FaultResult:
    """Kiểm tra lỗi theo thứ tự: segment, offset, rồi quyền truy cập."""
    if isinstance(offset, bool) or not isinstance(offset, int):
        return FaultResult(Status.INVALID_INPUT, "Offset phải là số nguyên")

    seg = table.get(seg_id)
    if seg is None:
        return FaultResult(Status.SEGMENT_FAULT, f"Segment {seg_id} không tồn tại trong bảng phân đoạn")

    if isinstance(seg, dict):
        limit = seg.get("limit")
        perm = seg.get("perm")
    else:
        limit = getattr(seg, "limit", None)
        perm = getattr(seg, "perm", None)

    if isinstance(limit, bool) or not isinstance(limit, int):
        return FaultResult(Status.INVALID_INPUT, f"Limit của segment {seg_id} phải là số nguyên")

    if offset < 0 or offset >= limit:
        return FaultResult(
            Status.OFFSET_OUT_OF_RANGE,
            f"Offset {offset} vượt quá giới hạn limit {limit} của segment {seg_id}",
        )

    if not check_permission(perm, access):
        return FaultResult(
            Status.PROTECTION_FAULT,
            f"Thao tác {access} không hợp lệ với quyền {perm} của segment {seg_id}",
        )

    return FaultResult(Status.OK, "")

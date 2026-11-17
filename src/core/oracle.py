"""Reference oracle for segmentation protection checks.

This implementation intentionally does not import the production protection
module so tests can compare its results against an independent implementation.
"""
from .result_types import ACCESS_TYPES, FaultResult, SegmentTable, Status


def reference_check_permission(perm: object, access: object) -> bool:
    """Return whether a permission string grants the requested access."""
    if not isinstance(perm, str) or len(perm) != 3:
        return False
    if not isinstance(access, str) or access not in ACCESS_TYPES:
        return False

    for index, expected in enumerate(ACCESS_TYPES):
        if perm[index] not in (expected, "-"):
            return False

    return perm[ACCESS_TYPES.index(access)] == access


def reference_check_fault(
    table: SegmentTable,
    seg_id: int,
    offset: int,
    access: str,
) -> FaultResult:
    """Return the first fault in segment, offset, and permission order."""
    segment = table.get(seg_id)
    if segment is None:
        return FaultResult(
            status=Status.SEGMENT_FAULT,
            reason=f"Segment {seg_id} không tồn tại trong bảng phân đoạn",
        )

    if isinstance(segment, dict):
        limit = segment.get("limit")
        permission = segment.get("perm")
    else:
        limit = getattr(segment, "limit", None)
        permission = getattr(segment, "perm", None)

    if offset < 0 or offset >= limit:
        return FaultResult(
            status=Status.OFFSET_OUT_OF_RANGE,
            reason=(
                f"Offset {offset} vượt quá giới hạn limit {limit} "
                f"của segment {seg_id}"
            ),
        )

    if not reference_check_permission(permission, access):
        return FaultResult(
            status=Status.PROTECTION_FAULT,
            reason=(
                f"Thao tác {access} không hợp lệ với quyền {permission} "
                f"của segment {seg_id}"
            ),
        )

    return FaultResult(status=Status.OK, reason="")

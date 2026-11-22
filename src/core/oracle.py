"""Independent reference implementation for segmentation protection checks."""

from itertools import product

from .result_types import FaultResult, SegmentTable, Status

_ACCESS_POSITION = {"R": 0, "W": 1, "X": 2}
_WELL_FORMED_PERMISSIONS = {
    "".join(chars)
    for chars in product(("R", "-"), ("W", "-"), ("X", "-"))
}


def reference_check_permission(perm: object, access: object) -> bool:
    """Return whether a well-formed permission string grants the access."""
    if not isinstance(perm, str) or not isinstance(access, str):
        return False

    perm = perm.strip().upper()
    access = access.strip().upper()

    position = _ACCESS_POSITION.get(access)
    return (
        position is not None
        and perm in _WELL_FORMED_PERMISSIONS
        and perm[position] == access
    )


def reference_check_fault(
    table: SegmentTable,
    seg_id: int,
    offset: object,
    access: object,
) -> FaultResult:
    """Compute a fault result independently from the production checker."""
    if isinstance(offset, bool) or not isinstance(offset, int):
        return FaultResult(
            status=Status.INVALID_INPUT,
            reason="Offset phải là số nguyên",
        )

    record = table.get(seg_id)
    if record is None:
        return FaultResult(
            status=Status.SEGMENT_FAULT,
            reason=f"Segment {seg_id} không tồn tại trong bảng phân đoạn",
        )

    if isinstance(record, dict):
        bound = record.get("limit")
        permission = record.get("perm")
    else:
        bound = getattr(record, "limit", None)
        permission = getattr(record, "perm", None)

    if isinstance(bound, bool) or not isinstance(bound, int):
        return FaultResult(
            status=Status.INVALID_INPUT,
            reason=f"Limit của segment {seg_id} phải là số nguyên",
        )

    if offset not in range(bound):
        return FaultResult(
            status=Status.OFFSET_OUT_OF_RANGE,
            reason=(
                f"Offset {offset} vượt quá giới hạn limit {bound} "
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

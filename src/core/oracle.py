"""Independent reference implementation for uppercase-only permissions."""
from itertools import product

from .result_types import FaultResult, SegmentTable, Status

_ACCESS_POSITION = {"R": 0, "W": 1, "X": 2}
_WELL_FORMED_PERMISSIONS = {
    "".join(chars)
    for chars in product(("R", "-"), ("W", "-"), ("X", "-"))
}


def reference_check_permission(perm: object, access: object) -> bool:
    if not isinstance(perm, str) or not isinstance(access, str):
        return False

    perm = perm.strip()
    access = access.strip()
    position = _ACCESS_POSITION.get(access)
    return position is not None and perm in _WELL_FORMED_PERMISSIONS and perm[position] == access


def reference_check_fault(table: SegmentTable, seg_id: int, offset: object, access: object) -> FaultResult:
    if isinstance(offset, bool) or not isinstance(offset, int):
        return FaultResult(Status.INVALID_INPUT, "Offset phải là số nguyên")

    record = table.get(seg_id)
    if record is None:
        return FaultResult(Status.SEGMENT_FAULT, f"Segment {seg_id} không tồn tại trong bảng phân đoạn")

    if isinstance(record, dict):
        bound = record.get("limit")
        permission = record.get("perm")
    else:
        bound = getattr(record, "limit", None)
        permission = getattr(record, "perm", None)

    if isinstance(bound, bool) or not isinstance(bound, int):
        return FaultResult(Status.INVALID_INPUT, f"Limit của segment {seg_id} phải là số nguyên")

    if offset not in range(bound):
        return FaultResult(Status.OFFSET_OUT_OF_RANGE,
            f"Offset {offset} vượt quá giới hạn limit {bound} của segment {seg_id}")

    if not reference_check_permission(permission, access):
        return FaultResult(Status.PROTECTION_FAULT,
            f"Thao tác {access} không hợp lệ với quyền {permission} của segment {seg_id}")

    return FaultResult(Status.OK, "")

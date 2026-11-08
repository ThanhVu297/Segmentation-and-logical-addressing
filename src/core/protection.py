from core.result_types import FaultResult, Status , SegmentTable

def check_permission(perm: str, access: str) -> bool:
    """
    Kiểm tra vi phạm quyền dựa trên quy ước chuỗi perm 3 ký tự (Ví dụ: 'R-X', 'RW-')
    """
    if access == 'R' and perm[0] == 'R':
        return True
    if access == 'W' and perm[1] == 'W':
        return True
    if access == 'X' and perm[2] == 'X':
        return True
    return False

def check_fault(table: dict, seg_id: int, offset: int, access: str) -> FaultResult:
    # THỨ TỰ 1: Segment không tồn tại -> SEGMENT_FAULT
    seg = table.get(seg_id)
    if seg_id is None:
        return FaultResult(
            status=Status.SEGMENT_FAULT, 
            reason=f"Segment {seg_id} không tồn tại trong bảng phân đoạn"
        )
    
    seg = table[seg_id]
    limit = seg.limit if hasattr(seg, 'limit') else seg.get('limit')
    perm = seg.perm if hasattr(seg, 'perm') else seg.get('perm')
    
    # THỨ TỰ 2: Độ lệch < 0 hoặc Độ lệch >= giới hạn -> OFFSET_OUT_OF_RANGE
    if offset < 0 or offset >= limit:
        return FaultResult(
            status=Status.OFFSET_OUT_OF_RANGE,
            reason=f"Offset {offset} vượt quá giới hạn limit {seg.limit} của segment {seg_id}"
        )
    
    # THỨ TỰ 3: Quyền truy cập không hợp lệ -> PROTECTION_FAULT
    if not check_permission(segh.perm, access):
        return FaultResult(
            status=Status.PROTECTION_FAULT, 
            reason=f"Thao tác {access} không hợp lệ với quyền {seg.perm} của segment {seg_id}"
        )
    
    # HỢP LỆ
    return FaultResult(status=Status.OK, reason="")

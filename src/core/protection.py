from core.result_types import FaultResult

def check_permission(perm: str, access: str) -> bool:
    """
    Kiểm tra vi phạm quyền dựa trên quy ước chuỗi perm 3 ký tự (Ví dụ: 'RX-', 'RW-')
    """
    if not perm or len(perm) < 3:
        return False
        
    if access == 'R' and perm[0] == 'R':
        return True
    if access == 'W' and perm[1] == 'W':
        return True
    if access == 'X' and perm[2] == 'X':
        return True
        
    return False


def check_fault(table: dict, seg_id: int, offset: int, access: str) -> FaultResult:
    """
    HÀM TUẦN 3-4: Nhận diện 3 hệ thống lỗi theo thứ tự chính xác.
    """
    # THỨ TỰ 1: Đoạn không tồn tại -> SEGMENT_FAULT
    if seg_id not in table:
        return FaultResult(status="SEGMENT_FAULT", reason="Segment does not exist")
        
    seg = table[seg_id]
    
    limit = seg.limit if hasattr(seg, 'limit') else seg.get('limit')
    perm = seg.perm if hasattr(seg, 'perm') else seg.get('perm')
    
    # THỨ TỰ 2: Độ lệch < 0 hoặc Độ lệch >= giới hạn -> OFFSET_OUT_OF_RANGE
    if offset < 0 or (limit is not None and offset >= limit):
        return FaultResult(status="OFFSET_OUT_OF_RANGE", reason="Offset out of range or exceeds limit")
        
    # THỨ TỰ 3: Quyền truy cập không hợp lệ -> PROTECTION_FAULT
    if not check_permission(perm, access):
        return FaultResult(status="PROTECTION_FAULT", reason="Access denied by protection rules")
        
    # HỢP LỆ
    return FaultResult(status="OK", reason="Success")

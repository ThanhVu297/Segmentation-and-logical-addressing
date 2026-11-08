# src/core/protection.py
# TV3: Trần Tường Nguyên - Nhiệm vụ Tuần 3-4

from core.result_types import FaultResult

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
    """
    HÀM TUẦN 3-4: Nhận diện 3 loại lỗi hệ thống theo đúng thứ tự quy ước.
    """
    # THỨ TỰ 1: Segment không tồn tại -> SEGMENT_FAULT
    if seg_id not in table:
        return FaultResult(status="FAULT", reason="SEGMENT_FAULT")
    
    seg = table[seg_id]
    limit = seg.limit if hasattr(seg, 'limit') else seg.get('limit')
    perm = seg.perm if hasattr(seg, 'perm') else seg.get('perm')
    
    # THỨ TỰ 2: Độ lệch < 0 hoặc Độ lệch >= giới hạn -> OFFSET_OUT_OF_RANGE
    if offset < 0 or offset >= limit:
        return FaultResult(status="FAULT", reason="OFFSET_OUT_OF_RANGE")
    
    # THỨ TỰ 3: Quyền truy cập không hợp lệ -> PROTECTION_FAULT
    if not check_permission(perm, access):
        return FaultResult(status="FAULT", reason="PROTECTION_FAULT")
    
    # HỢP LỆ
    return FaultResult(status="SUCCESS", reason=None)
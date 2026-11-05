from core.result_types import FaultResult

def oracle_check(table: dict, seg_id: int, offset: int, access: str) -> dict:
    if seg_id not in table:
        return {"status": "SEGMENT_FAULT", "valid": False}
        
    seg = table[seg_id]
    
    limit = seg.limit if hasattr(seg, 'limit') else seg.get('limit')
    if offset < 0 or (limit is not None and offset >= limit):
        return {"status": "OFFSET_OUT_OF_RANGE", "valid": False}
        
    perm = seg.perm if hasattr(seg, 'perm') else seg.get('perm', '')
    access_upper = access.upper()
    perm_upper = perm.upper()
    
    has_perm = False
    if access_upper == 'R' and 'R' in perm_upper:
        has_perm = True
    elif access_upper == 'W' and 'W' in perm_upper:
        has_perm = True
    elif access_upper == 'X' and 'X' in perm_upper:
        has_perm = True
        
    if not has_perm:
        return {"status": "PROTECTION_FAULT", "valid": False}
        
    return {"status": "OK", "valid": True}

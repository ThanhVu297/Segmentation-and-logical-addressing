"""Kiểu dữ liệu dùng chung cho cả nhóm (TV1 quản lý, mọi người chỉ import).

Không sửa file này nếu chưa báo nhóm: TV2, TV3, TV4, TV5 đều phụ thuộc vào nó.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

# Các loại truy cập hợp lệ: R = đọc, W = ghi, X = thực thi
ACCESS_TYPES = ("R", "W", "X")


class Status(str, Enum):
    """4 trạng thái duy nhất của một lần dịch địa chỉ."""
    OK = "OK"
    SEGMENT_NOT_FOUND = "SEGMENT_NOT_FOUND"        # segment không tồn tại
    OFFSET_OUT_OF_RANGE = "OFFSET_OUT_OF_RANGE"    # offset < 0 hoặc offset >= limit
    PROTECTION_VIOLATION = "PROTECTION_VIOLATION"  # sai quyền R/W/X


@dataclass
class Step:
    """Một bước trong quá trình dịch, để GUI hiển thị và ghi trace."""
    description: str   # ví dụ: "So sánh offset 1200 với limit 1000"
    ok: bool = True    # False nếu bước này gây lỗi


@dataclass
class FaultResult:
    """Kết quả của check_fault (TV3). status = OK nghĩa là không có lỗi."""
    status: Status
    reason: str = ""   # ví dụ: "Offset 1200 vượt limit 1000 của segment 1"


@dataclass
class TranslationResult:
    """Kết quả của translate (TV2). Một dòng của trace.csv."""
    seg_id: int
    offset: int
    access: str
    base: Optional[int] = None      # None nếu segment không tồn tại
    limit: Optional[int] = None     # None nếu segment không tồn tại
    physical: Optional[int] = None  # None nếu có lỗi
    status: Status = Status.OK
    reason: str = ""
    steps: List[Step] = field(default_factory=list)

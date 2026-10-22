"""Kiểu dữ liệu dùng chung cho cả nhóm (TV1 quản lý, mọi người chỉ import).

Không sửa file này nếu chưa báo nhóm: TV2, TV3, TV4, TV5 đều phụ thuộc vào nó.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional

# Các loại truy cập hợp lệ: R = đọc, W = ghi, X = thực thi
ACCESS_TYPES = ("R", "W", "X")


class Status(str, Enum):
    """5 trạng thái của một lần dịch địa chỉ."""
    OK = "OK"
    SEGMENT_FAULT = "SEGMENT_FAULT"
    OFFSET_OUT_OF_RANGE = "OFFSET_OUT_OF_RANGE"
    PROTECTION_FAULT = "PROTECTION_FAULT"
    INVALID_INPUT = "INVALID_INPUT"


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
    seg_id: Any
    offset: Any
    access: Any
    base: Optional[int] = None      # None nếu segment không tồn tại
    limit: Optional[int] = None     # None nếu segment không tồn tại
    physical: Optional[int] = None  # None nếu có lỗi
    status: Status = Status.OK
    reason: str = ""
    steps: List[Step] = field(default_factory=list)


@dataclass(frozen=True)
class Segment:
    seg_id: int
    base: int
    limit: int
    perm: str  # ví dụ "R-X"


class SegmentTable:
    def __init__(self, mem_size: int = 5000):
        self.mem_size = mem_size
        self._segs = {}

    def add(self, seg: Segment) -> None:
        self._segs[seg.seg_id] = seg

    def remove(self, seg_id: int) -> None:
        self._segs.pop(seg_id, None)

    def get(self, seg_id):
        return self._segs.get(seg_id)  # None nếu không có

    def __iter__(self):
        return iter(self._segs.values())

    def __len__(self):
        return len(self._segs)

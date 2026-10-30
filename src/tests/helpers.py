"""Tiện ích dùng chung cho test của TV5 (chạy bằng unittest, không cần pandas/Tk).

reference_translate / buggy_* chỉ là bản dịch tham chiếu để test độc lập với
translator.py của TV2. Khi core/translator.py đã merge, test_benchmark có thêm
một test tích hợp chạy trên translate() thật.
"""
import csv
from pathlib import Path

from core.result_types import Segment, SegmentTable, Status, TranslationResult

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = REPO_ROOT / "input"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"


def make_table(rows, mem_size=5000):
    """rows: danh sách (seg_id, base, limit, perm)."""
    table = SegmentTable(mem_size)
    for seg_id, base, limit, perm in rows:
        table.add(Segment(seg_id, base, limit, perm))
    return table


def example_table():
    """Bảng ở mục 2 của kế hoạch nhóm (bộ nhớ vật lý 5000 byte)."""
    return make_table([(0, 1000, 400, "R-X"), (1, 2000, 1000, "RW-"),
                       (2, 3500, 500, "R--")])


def load_table(path, mem_size=5000):
    """Đọc segments.csv bằng csv chuẩn (không validate), dựng SegmentTable."""
    table = SegmentTable(mem_size)
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            table.add(Segment(int(row["seg_id"]), int(row["base"]),
                              int(row["limit"]), row["perm"].strip()))
    return table


def reference_translate(table, seg_id, offset, access):
    """Dịch đúng theo README: segment -> offset -> quyền -> base + offset."""
    seg = table.get(seg_id)
    if seg is None:
        return TranslationResult(seg_id, offset, access,
                                 status=Status.SEGMENT_FAULT)
    if offset < 0 or offset >= seg.limit:
        return TranslationResult(seg_id, offset, access, seg.base, seg.limit,
                                 status=Status.OFFSET_OUT_OF_RANGE)
    if seg.perm["RWX".index(access)] != access:
        return TranslationResult(seg_id, offset, access, seg.base, seg.limit,
                                 status=Status.PROTECTION_FAULT)
    return TranslationResult(seg_id, offset, access, seg.base, seg.limit,
                             seg.base + offset, Status.OK)


def buggy_off_by_one(table, seg_id, offset, access):
    """Cố ý sai biên: chấp nhận offset == limit."""
    seg = table.get(seg_id)
    if seg is not None and offset == seg.limit:
        return TranslationResult(seg_id, offset, access, seg.base, seg.limit,
                                 seg.base + offset, Status.OK)
    return reference_translate(table, seg_id, offset, access)


def buggy_ignore_permission(table, seg_id, offset, access):
    """Cố ý sai: bỏ qua bước kiểm tra quyền."""
    seg = table.get(seg_id)
    if seg is not None and 0 <= offset < seg.limit:
        return TranslationResult(seg_id, offset, access, seg.base, seg.limit,
                                 seg.base + offset, Status.OK)
    return reference_translate(table, seg_id, offset, access)


def translate_without_access(table, seg_id, offset):
    """Chữ ký 3 tham số (không có access), để test bộ điều hợp chữ ký."""
    return reference_translate(table, seg_id, offset, "R")


class FakeCanvas:
    """Canvas giả ghi lại các lệnh vẽ, để test mà không cần Tk."""

    def __init__(self, width=600, height=480):
        self._size = {"width": str(width), "height": str(height)}
        self.calls = []

    def winfo_width(self):
        return 1

    def winfo_height(self):
        return 1

    def cget(self, key):
        return self._size[key]

    def _record(self, name):
        def method(*args, **kwargs):
            self.calls.append((name, args, kwargs))
        return method

    def __getattr__(self, name):
        if name.startswith("create_") or name == "delete":
            return self._record(name)
        raise AttributeError(name)

    def named(self, name):
        return [c for c in self.calls if c[0] == name]

    def texts(self):
        return [c[2].get("text", "") for c in self.named("create_text")]

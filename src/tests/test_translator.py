
"""Unit tests cho src/core/translator.py (TV2)."""

import sys
import unittest
from pathlib import Path

# Cho phép chạy unittest từ thư mục gốc dự án.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.result_types import Segment, SegmentTable, Status
from src.core.translator import translate, translate_many


def create_table():
    """Tạo bảng phân đoạn dùng chung cho các trường hợp kiểm thử."""
    table = SegmentTable(mem_size=5000)

    table.add(Segment(0, 1000, 400, "R-X"))
    table.add(Segment(1, 2000, 1000, "RW-"))
    table.add(Segment(2, 3500, 500, "R--"))

    return table


class TestTranslate(unittest.TestCase):

    def setUp(self):
        self.table = create_table()

    # Test 1: Dịch địa chỉ thành công
    def test_translate_success_calculates_physical_address(self):
        result = translate(self.table, 0, 100, "R")

        self.assertEqual(result.status, Status.OK)
        self.assertEqual(result.physical, 1100)
        self.assertEqual(result.base, 1000)
        self.assertEqual(result.limit, 400)

    # Test 2: Kiểm tra các quyền truy cập hợp lệ
    def test_translate_valid_access_types(self):
        cases = [
            (0, 10, "R", 1010),
            (0, 10, "X", 1010),
            (1, 10, "W", 2010),
            (1, 10, "R", 2010),
            (2, 10, "R", 3510),
        ]

        for seg_id, offset, access, expected in cases:
            with self.subTest(seg_id=seg_id, access=access):
                result = translate(
                    self.table, seg_id, offset, access
                )

                self.assertEqual(result.status, Status.OK)
                self.assertEqual(result.physical, expected)

    # Test 3: Segment không tồn tại
    def test_translate_segment_not_found(self):
        result = translate(self.table, 9, 10, "R")

        self.assertEqual(result.status, Status.SEGMENT_FAULT)
        self.assertIsNone(result.physical)
        self.assertIn("không tồn tại", result.reason)
    # Test 4: Offset nằm ngoài giới hạn
    def test_translate_offset_out_of_range(self):
        cases = [
            (-1, Status.OFFSET_OUT_OF_RANGE),
            (400, Status.OFFSET_OUT_OF_RANGE),
        ]

        for offset, expected_status in cases:
            with self.subTest(offset=offset):
                result = translate(self.table, 0, offset, "R")

                self.assertEqual(result.status, expected_status)
                self.assertIsNone(result.physical)

    # Test 5: Không đủ quyền truy cập
    def test_translate_protection_fault(self):
        result = translate(self.table, 2, 10, "W")

        self.assertEqual(result.status, Status.PROTECTION_FAULT)
        self.assertIsNone(result.physical)

    # Test 6: Dữ liệu đầu vào không hợp lệ
    def test_translate_invalid_input(self):
        cases = [
            ("0", 10, "R"),
            (0, 10.5, "R"),
            (0, 10, "Q"),
        ]

        for seg_id, offset, access in cases:
            with self.subTest(
                seg_id=seg_id,
                offset=offset,
                access=access
            ):
                result = translate(
                    self.table, seg_id, offset, access
                )

                self.assertEqual(result.status, Status.INVALID_INPUT)
                self.assertIsNone(result.physical)

    # Test 7: Kiểm tra ghi vết từng bước
    def test_translate_records_step_by_step_trace(self):
        result = translate(self.table, 0, 100, "R")

        self.assertGreaterEqual(len(result.steps), 5)

        descriptions = [
            step.description for step in result.steps
        ]

        self.assertTrue(
            any(
                "Physical = 1000 + 100 = 1100" in s
                for s in descriptions
            )
        )

        self.assertTrue(
            all(step.ok for step in result.steps)
        )


class TestTranslateMany(unittest.TestCase):

    def setUp(self):
        self.table = create_table()

    # Test 8: Dịch nhiều địa chỉ dạng tuple
    def test_translate_many_handles_tuple_addresses_in_order(self):
        addresses = [
            (0, 100, "R"),
            (1, 20, "W"),
            (9, 10, "R")
        ]

        results = translate_many(self.table, addresses)

        self.assertEqual(len(results), 3)

        self.assertEqual(
            [result.status for result in results],
            [
                Status.OK,
                Status.OK,
                Status.SEGMENT_FAULT
            ]
        )

        self.assertEqual(results[0].physical, 1100)
        self.assertEqual(results[1].physical, 2020)

    # Test 9: Dịch nhiều địa chỉ dạng dict và dữ liệu sai
    def test_translate_many_handles_dict_and_invalid_format(self):
        addresses = [
            {"seg_id": 0, "offset": 5, "access": "R"},
            {"seg_id": 1, "offset": 5},
            (0, 5)
        ]

        results = translate_many(self.table, addresses)

        self.assertEqual(len(results), 3)

        self.assertEqual(results[0].status, Status.OK)
        self.assertEqual(results[0].physical, 1005)

        self.assertEqual(
            results[1].status, Status.INVALID_INPUT
        )

        self.assertEqual(
            results[2].status, Status.INVALID_INPUT
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.core.result_types import Segment, SegmentTable, Status
from src.core.translator import translate


class TestLogic(unittest.TestCase):
    def create_table(self):
        table = SegmentTable(mem_size=5000)
        table.add(Segment(0, 1000, 400, "R-X"))
        table.add(Segment(1, 2000, 1000, "RW-"))
        table.add(Segment(2, 3500, 500, "R--"))
        return table

    def test_translate_success(self):
        result = translate(self.create_table(), 0, 100, "R")
        self.assertEqual(result.status, Status.OK)
        self.assertEqual(result.physical, 1100)

    def test_segment_not_found(self):
        result = translate(self.create_table(), 9, 10, "R")
        self.assertEqual(result.status, Status.SEGMENT_FAULT)

    def test_offset_out_of_range(self):
        result = translate(self.create_table(), 0, 400, "R")
        self.assertEqual(result.status, Status.OFFSET_OUT_OF_RANGE)

    def test_protection_fault(self):
        result = translate(self.create_table(), 2, 10, "W")
        self.assertEqual(result.status, Status.PROTECTION_FAULT)

import unittest

from core.benchmark import make_oracle
from tests.helpers import example_table


class TestOracle(unittest.TestCase):
    def setUp(self):
        self.oracle = make_oracle(example_table())

    def test_translates_valid_addresses_to_physical_addresses(self):
        self.assertEqual(self.oracle(0, 0, "R"), ("OK", 1000))
        self.assertEqual(self.oracle(0, 399, "X"), ("OK", 1399))
        self.assertEqual(self.oracle(1, 999, "W"), ("OK", 2999))

    def test_unknown_segment_is_a_segment_fault(self):
        self.assertEqual(self.oracle(99, 0, "R"), ("SEGMENT_FAULT", None))

    def test_negative_and_limit_offsets_are_out_of_range(self):
        self.assertEqual(self.oracle(0, -1, "R"), ("OFFSET_OUT_OF_RANGE", None))
        self.assertEqual(self.oracle(0, 400, "R"), ("OFFSET_OUT_OF_RANGE", None))

    def test_disallowed_access_is_a_protection_fault(self):
        self.assertEqual(self.oracle(0, 10, "W"), ("PROTECTION_FAULT", None))
        self.assertEqual(self.oracle(2, 10, "X"), ("PROTECTION_FAULT", None))

    def test_offset_error_takes_precedence_over_permission_error(self):
        # Segment 0 does not allow W, but an invalid offset is reported first.
        self.assertEqual(
            self.oracle(0, 400, "W"), ("OFFSET_OUT_OF_RANGE", None)
        )


if __name__ == "__main__":
    unittest.main()

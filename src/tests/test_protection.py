import unittest

from core.oracle import reference_check_fault, reference_check_permission
from core.protection import check_fault, check_permission
from core.result_types import Segment, SegmentTable, Status


class TestCheckFault(unittest.TestCase):
    def setUp(self):
        self.table = SegmentTable()
        self.table.add(Segment(1, 100, 10, "RWX"))
        self.table.add(Segment(2, 200, 5, "---"))
        self.table.add(Segment(3, 300, 5, "RAB"))

    def test_fault_valid_read(self):
        self.assertEqual(check_fault(self.table, 1, 4, "R").status, Status.OK)

    def test_fault_valid_write(self):
        self.assertEqual(check_fault(self.table, 1, 4, "W").status, Status.OK)

    def test_fault_valid_execute(self):
        self.assertEqual(check_fault(self.table, 1, 4, "X").status, Status.OK)

    def test_fault_zero_offset_is_in_range(self):
        self.assertEqual(check_fault(self.table, 1, 0, "R").status, Status.OK)

    def test_fault_negative_offset(self):
        self.assertEqual(
            check_fault(self.table, 1, -1, "R").status,
            Status.OFFSET_OUT_OF_RANGE,
        )

    def test_fault_offset_equal_to_limit(self):
        self.assertEqual(
            check_fault(self.table, 1, 10, "R").status,
            Status.OFFSET_OUT_OF_RANGE,
        )

    def test_fault_offset_greater_than_limit(self):
        self.assertEqual(
            check_fault(self.table, 1, 11, "R").status,
            Status.OFFSET_OUT_OF_RANGE,
        )

    def test_fault_missing_segment(self):
        self.assertEqual(
            check_fault(self.table, 99, 1, "R").status,
            Status.SEGMENT_FAULT,
        )

    def test_fault_denied_read(self):
        self.assertEqual(
            check_fault(self.table, 2, 1, "R").status,
            Status.PROTECTION_FAULT,
        )

    def test_fault_denied_write(self):
        self.assertEqual(
            check_fault(self.table, 2, 1, "W").status,
            Status.PROTECTION_FAULT,
        )

    def test_fault_malformed_permission(self):
        self.assertEqual(
            check_fault(self.table, 3, 1, "R").status,
            Status.PROTECTION_FAULT,
        )

    def test_fault_missing_segment_precedes_offset_and_permission(self):
        self.assertEqual(
            check_fault(self.table, 99, -1, "Q").status,
            Status.SEGMENT_FAULT,
        )

    def test_fault_offset_precedes_denied_permission(self):
        self.assertEqual(
            check_fault(self.table, 2, 5, "W").status,
            Status.OFFSET_OUT_OF_RANGE,
        )

    def test_fault_supports_mapping_segment_values(self):
        table = {4: {"limit": 2, "perm": "R--"}}
        self.assertEqual(check_fault(table, 4, 1, "R").status, Status.OK)

    def test_fault_matches_independent_reference_oracle(self):
        cases = (
            (1, 4, "R"),
            (1, 10, "W"),
            (2, -1, "R"),
            (2, 2, "X"),
            (3, 1, "R"),
            (99, -1, "Q"),
        )
        for args in cases:
            with self.subTest(args=args):
                self.assertEqual(
                    check_fault(self.table, *args),
                    reference_check_fault(self.table, *args),
                )


class TestCheckPermission(unittest.TestCase):
    def test_permission_grants_read(self):
        self.assertTrue(check_permission("R--", "R"))

    def test_permission_grants_write(self):
        self.assertTrue(check_permission("-W-", "W"))

    def test_permission_grants_execute(self):
        self.assertTrue(check_permission("--X", "X"))

    def test_permission_denies_unlisted_access(self):
        self.assertFalse(check_permission("R--", "W"))

    def test_permission_rejects_malformed_string(self):
        self.assertFalse(check_permission("RAB", "R"))

    def test_permission_rejects_invalid_access(self):
        self.assertFalse(check_permission("RWX", "Q"))

    def test_permission_rejects_non_string_values(self):
        self.assertFalse(check_permission(None, "R"))
        self.assertFalse(check_permission("RWX", None))

    def test_permission_matches_independent_reference_oracle(self):
        cases = (
            ("R-X", "R"),
            ("R-X", "W"),
            ("R-X", "X"),
            ("ABC", "R"),
            ("RWX", "Q"),
        )
        for perm, access in cases:
            with self.subTest(perm=perm, access=access):
                self.assertEqual(
                    check_permission(perm, access),
                    reference_check_permission(perm, access),
                )


if __name__ == "__main__":
    unittest.main()

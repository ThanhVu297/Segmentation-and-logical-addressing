import random
import unittest

from core.validator import (EXCEEDS_MEMORY, INVALID_PERM, INVALID_RANGE,
                            OVERLAP, is_valid, validate_table)
from tests.helpers import INPUT_DIR, example_table, load_table, make_table


def kinds(issues):
    return sorted(i.kind for i in issues)


def pairs(issues):
    return sorted(tuple(sorted(i.seg_ids)) for i in issues if i.kind == OVERLAP)


class TestValidateTable(unittest.TestCase):
    def test_example_table_is_valid(self):
        self.assertEqual(validate_table(example_table(), 5000), [])
        self.assertTrue(is_valid(example_table()))

    def test_simple_overlap_detected(self):
        table = make_table([(0, 1000, 500, "R--"), (1, 1400, 300, "RW-")])
        issues = validate_table(table)
        self.assertEqual(kinds(issues), [OVERLAP])
        self.assertEqual(pairs(issues), [(0, 1)])
        self.assertIn("[1400, 1500)", issues[0].message)  # vùng chồng lấn

    def test_touching_segments_are_not_overlap(self):
        # [1000,1500) và [1500,1600): end == base của segment sau => hợp lệ (biên)
        table = make_table([(0, 1000, 500, "R--"), (1, 1500, 100, "RW-")])
        self.assertEqual(validate_table(table), [])

    def test_exceeds_memory_and_exact_fit(self):
        over = make_table([(0, 4800, 300, "R--")])    # end = 5100 > 5000
        self.assertEqual(kinds(validate_table(over)), [EXCEEDS_MEMORY])
        exact = make_table([(0, 4800, 200, "R--")])   # end = 5000 == mem_size
        self.assertEqual(validate_table(exact), [])

    def test_mem_size_defaults_to_table_and_can_be_overridden(self):
        table = make_table([(0, 900, 200, "R--")], mem_size=1000)  # end = 1100
        self.assertEqual(kinds(validate_table(table)), [EXCEEDS_MEMORY])
        self.assertEqual(validate_table(table, 2000), [])

    def test_nested_segments_report_every_overlapping_pair(self):
        # A bao cả B và C; B và C không chạm nhau
        table = make_table([(0, 0, 1000, "R--"), (1, 100, 100, "R--"),
                            (2, 300, 100, "R--")])
        self.assertEqual(pairs(validate_table(table)), [(0, 1), (0, 2)])

    def test_identical_ranges_overlap(self):
        table = make_table([(0, 1000, 200, "R--"), (1, 1000, 200, "R--")])
        self.assertEqual(pairs(validate_table(table)), [(0, 1)])

    def test_empty_table_has_no_issues(self):
        self.assertEqual(validate_table(make_table([])), [])

    def test_invalid_range_reported_without_crash(self):
        table = make_table([(0, -5, 100, "R--"), (1, 1000, 0, "R--")])
        self.assertEqual(kinds(validate_table(table)),
                         [INVALID_RANGE, INVALID_RANGE])

    def test_invalid_perm_reported(self):
        for perm in ("ABC", "RW", "R-XX", "r--", ""):
            with self.subTest(perm=perm):
                table = make_table([(0, 1000, 400, perm)])
                self.assertEqual(kinds(validate_table(table)), [INVALID_PERM])

    def test_valid_perm_variants(self):
        for perm in ("---", "R--", "-W-", "--X", "R-X", "RW-", "RWX"):
            with self.subTest(perm=perm):
                self.assertEqual(validate_table(make_table([(0, 0, 10, perm)])), [])

    def test_non_positive_mem_size_raises(self):
        with self.assertRaises(ValueError):
            validate_table(example_table(), 0)

    def test_result_independent_of_input_order(self):
        rows = [(0, 1000, 500, "R--"), (1, 1400, 300, "R--"),
                (2, 1600, 600, "R--"), (3, 4800, 400, "R--")]
        expected = validate_table(make_table(rows))
        shuffled = rows[:]
        random.Random(1).shuffle(shuffled)
        got = validate_table(make_table(shuffled))
        self.assertEqual(sorted((i.kind, i.seg_ids) for i in got),
                         sorted((i.kind, i.seg_ids) for i in expected))


class TestRepoSampleFiles(unittest.TestCase):
    """Chạy validator trên CSV mẫu của nhóm (input/edge_cases, input/error_cases)."""

    def test_valid_sample_files(self):
        for name in ("segments.csv", "edge_cases/segments_adjacent.csv",
                     "edge_cases/segments_memory_boundary.csv"):
            with self.subTest(file=name):
                self.assertEqual(validate_table(load_table(INPUT_DIR / name)), [])

    def test_invalid_sample_files_are_rejected_with_expected_kind(self):
        expected = {
            "segments_overlap.csv": OVERLAP,
            "segments_exceeds_memory.csv": EXCEEDS_MEMORY,
            "segments_exceeds_memory_by_one.csv": EXCEEDS_MEMORY,
            "segments_zero_limit.csv": INVALID_RANGE,
            "segments_negative_base.csv": INVALID_RANGE,
            "segments_negative_limit.csv": INVALID_RANGE,
            "segments_invalid_perm_chars.csv": INVALID_PERM,
            "segments_invalid_perm_length.csv": INVALID_PERM,
        }
        for name, kind in expected.items():
            with self.subTest(file=name):
                issues = validate_table(load_table(INPUT_DIR / "error_cases" / name))
                self.assertIn(kind, kinds(issues))


if __name__ == "__main__":
    unittest.main()

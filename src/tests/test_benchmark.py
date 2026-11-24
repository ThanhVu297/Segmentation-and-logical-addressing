import csv
import tempfile
import unittest
from pathlib import Path

from core.benchmark import (_takes_access, default_extract, format_rows,
                            generate_addresses, make_oracle, run_benchmark,
                            table_from_dataframe, write_csv)
from core.result_types import Status, TranslationResult
from core.validator import validate_table
from tests.helpers import (EXPECTED_DIR, INPUT_DIR, buggy_ignore_permission,
                           buggy_off_by_one, example_table, load_table,
                           reference_translate, translate_without_access)

try:  # TV1 dùng pandas trong csv_input
    from core.csv_input import ValidationError, read_and_validate_segments
except Exception:  # pragma: no cover - thiếu pandas
    read_and_validate_segments = None
    ValidationError = None

try:  # TV2 chưa chắc đã merge vào branch này
    from core.translator import translate as real_translate
except Exception:  # pragma: no cover
    real_translate = None


def read_expected(name):
    with open(EXPECTED_DIR / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestGenerateAddresses(unittest.TestCase):
    def test_reproducible_with_same_seed(self):
        a = generate_addresses(example_table(), 500, seed=7)
        b = generate_addresses(example_table(), 500, seed=7)
        c = generate_addresses(example_table(), 500, seed=8)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(len(a), 500)

    def test_contains_both_ok_and_faults_for_every_kind(self):
        oracle = make_oracle(example_table())
        statuses = {oracle(*addr)[0]
                    for addr in generate_addresses(example_table(), 2000, seed=1)}
        self.assertEqual(statuses, {"OK", "SEGMENT_FAULT",
                                    "OFFSET_OUT_OF_RANGE", "PROTECTION_FAULT"})

    def test_table_without_usable_segment_raises(self):
        from tests.helpers import make_table
        with self.assertRaises(ValueError):
            generate_addresses(make_table([(0, 0, 0, "R--")]), 10)


class TestOracle(unittest.TestCase):
    def test_hand_computed_examples_from_readme(self):
        oracle = make_oracle(example_table())
        self.assertEqual(oracle(0, 100, "R"), ("OK", 1100))             # 1000 + 100
        self.assertEqual(oracle(0, 400, "R"), ("OFFSET_OUT_OF_RANGE", None))
        self.assertEqual(oracle(3, 10, "R"), ("SEGMENT_FAULT", None))


class TestRunBenchmark(unittest.TestCase):
    pass


@unittest.skipIf(read_and_validate_segments is None, "cần pandas và core.csv_input")
class TestWithRealCsvInput(unittest.TestCase):
    def test_sample_segments_pass_csv_input_and_validator(self):
        df = read_and_validate_segments(str(INPUT_DIR / "segments.csv"))
        table = table_from_dataframe(df)
        self.assertEqual(len(table), 3)
        self.assertEqual(validate_table(table), [])

    def test_csv_input_rejects_overlap_and_memory_errors_before_validator(self):
        for name in ("segments_overlap.csv", "segments_exceeds_memory.csv",
                     "segments_exceeds_memory_by_one.csv"):
            with self.subTest(file=name):
                with self.assertRaises(ValidationError):
                    read_and_validate_segments(
                        str(INPUT_DIR / "error_cases" / name))

    def test_csv_input_rejects_invalid_values_before_validator(self):
        for name in ("segments_zero_limit.csv", "segments_invalid_perm_chars.csv",
                     "segments_invalid_perm_length.csv"):
            with self.subTest(file=name):
                with self.assertRaises(ValidationError):
                    read_and_validate_segments(
                        str(INPUT_DIR / "error_cases" / name))

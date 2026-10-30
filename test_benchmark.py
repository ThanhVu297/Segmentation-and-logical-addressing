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
    from core.csv_input import read_and_validate_segments
except Exception:  # pragma: no cover - thiếu pandas
    read_and_validate_segments = None

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
        self.assertEqual(oracle(0, 200, "W"), ("PROTECTION_FAULT", None))
        self.assertEqual(oracle(3, 10, "R"), ("SEGMENT_FAULT", None))
        self.assertEqual(oracle(1, 999, "R"), ("OK", 2999))             # biên trên
        self.assertEqual(oracle(1, 1000, "R"), ("OFFSET_OUT_OF_RANGE", None))
        self.assertEqual(oracle(1, -1, "R"), ("OFFSET_OUT_OF_RANGE", None))

    def test_error_order_segment_then_offset_then_permission(self):
        oracle = make_oracle(example_table())
        # offset sai VÀ quyền sai: phải báo lỗi offset trước (README mục 2 < 3)
        self.assertEqual(oracle(2, 9999, "W")[0], "OFFSET_OUT_OF_RANGE")

    def test_oracle_matches_team_expected_trace_files(self):
        cases = [
            ("expected_trace.csv", INPUT_DIR / "segments.csv"),
            ("expected_trace_memory_boundary.csv",
             INPUT_DIR / "edge_cases" / "segments_memory_boundary.csv"),
        ]
        for trace_name, segments_path in cases:
            oracle = make_oracle(load_table(segments_path))
            for row in read_expected(trace_name):
                with self.subTest(trace=trace_name, row=row):
                    physical = int(row["physical"]) if row["physical"] else None
                    got = oracle(int(row["seg_id"]), int(row["offset"]),
                                 row["access"])
                    self.assertEqual(got, (row["status"], physical))


class TestRunBenchmark(unittest.TestCase):
    def test_correct_translator_has_no_mismatch(self):
        rows = run_benchmark(example_table(), reference_translate,
                             sizes=(100, 1000), repeats=2)
        self.assertEqual([r.n for r in rows], [100, 1000])
        self.assertTrue(all(r.mismatches == 0 for r in rows))
        self.assertTrue(all(r.median_s > 0 and r.min_s <= r.median_s for r in rows))
        self.assertIsNone(rows[0].ratio_prev)
        self.assertIsNone(rows[0].expected_ratio)
        self.assertEqual(rows[1].expected_ratio, 10)
        self.assertEqual(rows[1].valid + rows[1].faults, 1000)

    def test_oracle_catches_off_by_one_boundary_bug(self):
        rows = run_benchmark(example_table(), buggy_off_by_one,
                             sizes=(1000,), repeats=1)
        self.assertGreater(rows[0].mismatches, 0)

    def test_oracle_catches_missing_permission_check(self):
        rows = run_benchmark(example_table(), buggy_ignore_permission,
                             sizes=(1000,), repeats=1)
        self.assertGreater(rows[0].mismatches, 0)

    def test_three_argument_translate_is_supported(self):
        self.assertFalse(_takes_access(translate_without_access))
        self.assertTrue(_takes_access(reference_translate))
        rows = run_benchmark(example_table(), translate_without_access,
                             sizes=(200,), repeats=1)
        self.assertEqual(rows[0].n, 200)

    def test_empty_sizes_returns_empty_list(self):
        self.assertEqual(run_benchmark(example_table(), reference_translate,
                                       sizes=()), [])

    def test_invalid_arguments_raise(self):
        for kwargs in ({"sizes": (0,)}, {"sizes": (-5,)}, {"repeats": 0}):
            with self.subTest(**kwargs):
                with self.assertRaises(ValueError):
                    run_benchmark(example_table(), reference_translate, **kwargs)

    def test_write_csv_and_format(self):
        rows = run_benchmark(example_table(), reference_translate,
                             sizes=(100, 200), repeats=1)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "benchmark.csv"
            write_csv(rows, out)
            with open(out, encoding="utf-8") as f:
                data = list(csv.DictReader(f))
        self.assertEqual([int(r["n"]) for r in data], [100, 200])
        self.assertTrue({"n", "median_s", "per_addr_us", "mismatches"} <= set(data[0]))
        self.assertIn("median", format_rows(rows))


class TestExtract(unittest.TestCase):
    def test_default_extract_reads_status_and_physical(self):
        ok = TranslationResult(0, 100, "R", 1000, 400, 1100, Status.OK)
        fault = TranslationResult(3, 10, "R", status=Status.SEGMENT_FAULT)
        self.assertEqual(default_extract(ok), ("OK", 1100))
        self.assertEqual(default_extract(fault), ("SEGMENT_FAULT", None))

    def test_default_extract_accepts_plain_string_status(self):
        class R:
            status = "OK"
            physical = 5
        self.assertEqual(default_extract(R()), ("OK", 5))


@unittest.skipIf(read_and_validate_segments is None, "cần pandas và core.csv_input")
class TestWithRealCsvInput(unittest.TestCase):
    def test_sample_segments_pass_csv_input_and_validator(self):
        df = read_and_validate_segments(str(INPUT_DIR / "segments.csv"))
        table = table_from_dataframe(df)
        self.assertEqual(len(table), 3)
        self.assertEqual(validate_table(table), [])

    def test_validator_catches_what_csv_input_lets_through(self):
        # csv_input chỉ chặn số âm/trùng ID/thiếu cột; các lỗi dưới đây
        # phải do validate_table (TV5) bắt, đúng như README yêu cầu.
        for name in ("segments_overlap.csv", "segments_exceeds_memory.csv",
                     "segments_exceeds_memory_by_one.csv",
                     "segments_zero_limit.csv", "segments_invalid_perm_chars.csv",
                     "segments_invalid_perm_length.csv"):
            with self.subTest(file=name):
                df = read_and_validate_segments(
                    str(INPUT_DIR / "error_cases" / name))
                self.assertNotEqual(validate_table(table_from_dataframe(df)), [])


@unittest.skipIf(real_translate is None, "core.translator chưa có trong branch này")
class TestWithRealTranslator(unittest.TestCase):
    def test_real_translate_agrees_with_oracle(self):
        rows = run_benchmark(example_table(), real_translate,
                             sizes=(1000,), repeats=1)
        self.assertEqual(rows[0].mismatches, 0)


if __name__ == "__main__":
    unittest.main()

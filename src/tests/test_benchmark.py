import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path

from core.benchmark import (_takes_access, default_extract, format_rows,
                            generate_addresses, make_oracle, run_benchmark,
                            table_from_dataframe, write_csv)
from core.benchmark import main as benchmark_main
from core.result_types import Status, TranslationResult
from core.validator import validate_table
from tests.helpers import (EXPECTED_DIR, INPUT_DIR, buggy_ignore_permission,
                           buggy_off_by_one, example_table, load_table,
                           reference_translate, translate_without_access)

try:  # TV1 dùng pandas trong csv_input
    from core.csv_input import ValidationError, read_and_validate_segments
except Exception:  # pragma: no cover - thiếu pandas hoặc csv_input lỗi
    read_and_validate_segments = None
    ValidationError = ValueError

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

    def test_error_files_are_blocked_by_both_layers(self):
        # Hai lớp bảo vệ độc lập cho mỗi file lỗi mẫu:
        #  (1) validate_table (TV5) phải báo lỗi khi đọc CSV KHÔNG validate;
        #  (2) csv_input (TV1) phải từ chối file ngay khi đọc.
        for name in ("segments_overlap.csv", "segments_exceeds_memory.csv",
                     "segments_exceeds_memory_by_one.csv",
                     "segments_zero_limit.csv", "segments_negative_base.csv",
                     "segments_negative_limit.csv",
                     "segments_invalid_perm_chars.csv",
                     "segments_invalid_perm_length.csv"):
            path = INPUT_DIR / "error_cases" / name
            with self.subTest(file=name, layer="validator"):
                self.assertNotEqual(validate_table(load_table(path)), [])
            with self.subTest(file=name, layer="csv_input"):
                with self.assertRaises(ValidationError):
                    read_and_validate_segments(str(path))


@unittest.skipIf(real_translate is None, "core.translator chưa có trong branch này")
class TestWithRealTranslator(unittest.TestCase):
    def test_real_translate_agrees_with_oracle(self):
        rows = run_benchmark(example_table(), real_translate,
                             sizes=(1000,), repeats=1)
        self.assertEqual(rows[0].mismatches, 0)


@unittest.skipIf(read_and_validate_segments is None or real_translate is None,
                 "cần pandas, core.csv_input và core.translator")
class TestBenchmarkCli(unittest.TestCase):
    """benchmark.py main(): lỗi file phải báo gọn, không in traceback."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = str(Path(self.tmp.name) / "benchmark.csv")

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = benchmark_main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_missing_segments_file(self):
        code, _, err = self.run_cli(
            "--segments", str(Path(self.tmp.name) / "khong_co.csv"),
            "--out", self.out)
        self.assertEqual(code, 1)
        self.assertIn("Không tìm thấy file", err)
        self.assertNotIn("Traceback", err)

    def test_invalid_segments_file(self):
        code, _, err = self.run_cli(
            "--segments", str(INPUT_DIR / "error_cases" / "segments_overlap.csv"),
            "--out", self.out)
        self.assertEqual(code, 1)
        self.assertIn("không hợp lệ", err)
        self.assertNotIn("Traceback", err)

    def test_valid_run_writes_csv_with_no_mismatch(self):
        code, _, _ = self.run_cli(
            "--segments", str(INPUT_DIR / "segments.csv"), "--sizes", "100", "200",
            "--repeats", "1", "--out", self.out)
        self.assertEqual(code, 0)
        with open(self.out, encoding="utf-8") as f:
            self.assertEqual([int(r["mismatches"]) for r in csv.DictReader(f)],
                             [0, 0])


if __name__ == "__main__":
    unittest.main()

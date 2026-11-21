"""Test cho core/gen_workload.py (TV5).

Mọi lần chạy CLI đều dùng thư mục tạm làm cwd và đặt PYTHONPATH tới src/,
nên không bao giờ tạo/ghi file trong repo. File mẫu input/addresses.csv còn
được khôi phục bằng addCleanup ngay cả khi assertion thất bại.
"""
import csv
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.gen_workload import DEFAULT_OUTPUT, generate_workload
from tests.helpers import INPUT_DIR, REPO_ROOT

SEGMENTS = str(INPUT_DIR / "segments.csv")
SRC_DIR = REPO_ROOT / "src"
SAMPLE_ADDRESSES = INPUT_DIR / "addresses.csv"

try:
    import pandas  # noqa: F401
except Exception:  # pragma: no cover
    pandas = None


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@unittest.skipIf(pandas is None, "cần pandas (csv_input)")
class TestGenerateWorkload(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = str(Path(self.tmp.name) / "addr.csv")

    def test_schema_count_and_stats(self):
        stats = generate_workload(SEGMENTS, self.out, count=200,
                                  error_rate=0.25, seed=1)
        rows = read_rows(self.out)
        self.assertEqual(len(rows), 200)
        self.assertEqual(list(rows[0]), ["seg_id", "offset", "access"])
        self.assertEqual(stats["expected_errors"], 50)
        self.assertEqual(stats["expected_ok"], 150)

    def test_same_seed_is_reproducible(self):
        generate_workload(SEGMENTS, self.out, 100, 0.1, seed=5)
        first = Path(self.out).read_text(encoding="utf-8")
        generate_workload(SEGMENTS, self.out, 100, 0.1, seed=5)
        self.assertEqual(first, Path(self.out).read_text(encoding="utf-8"))

    def test_invalid_arguments(self):
        for kwargs in ({"count": 0}, {"count": True}, {"error_rate": -0.1},
                       {"error_rate": 1.5}, {"error_rate": float("nan")},
                       {"error_rate": True}, {"error_rate": "0.1"}):
            with self.subTest(kwargs=kwargs):
                args = {"count": 10, "error_rate": 0.1, **kwargs}
                with self.assertRaises(ValueError):
                    generate_workload(SEGMENTS, self.out, **args)

    def test_rejects_bad_segment_files_as_value_error(self):
        for name in ("segments_overlap.csv", "segments_duplicate_id.csv",
                     "segments_exceeds_memory.csv", "segments_empty.csv",
                     "segments_invalid_perm_chars.csv"):
            with self.subTest(file=name):
                with self.assertRaises(ValueError):
                    generate_workload(
                        str(INPUT_DIR / "error_cases" / name), self.out, 10)

    def test_missing_segments_file_is_os_error(self):
        with self.assertRaises(OSError):
            generate_workload(str(Path(self.tmp.name) / "khong_co.csv"),
                              self.out, 10)

    def test_mem_size_smaller_than_table_is_rejected(self):
        # bảng mẫu dùng tới địa chỉ 3999 nên mem_size = 1000 phải bị từ chối
        with self.assertRaises(ValueError) as ctx:
            generate_workload(SEGMENTS, self.out, 10, mem_size=1000)
        self.assertIn("vượt kích thước bộ nhớ vật lý 1000", str(ctx.exception))
        self.assertFalse(Path(self.out).exists())  # lỗi thì không tạo file

    def test_mem_size_exact_fit_and_default_are_accepted(self):
        generate_workload(SEGMENTS, self.out, 10, seed=1, mem_size=4000)  # vừa khít
        generate_workload(SEGMENTS, self.out, 10, seed=1)                 # mặc định 5000
        self.assertEqual(len(read_rows(self.out)), 10)

    def test_invalid_mem_size_values(self):
        for mem_size in (0, -1, True, 5001, "5000", 4999.5):
            with self.subTest(mem_size=mem_size):
                with self.assertRaises(ValueError):
                    generate_workload(SEGMENTS, self.out, 10, mem_size=mem_size)

    def test_generated_addresses_match_requested_error_count(self):
        from core.benchmark import make_oracle
        from tests.helpers import load_table

        stats = generate_workload(SEGMENTS, self.out, count=300,
                                  error_rate=0.2, seed=3)
        oracle = make_oracle(load_table(SEGMENTS))
        faults = sum(1 for r in read_rows(self.out)
                     if oracle(int(r["seg_id"]), int(r["offset"]),
                               r["access"])[0] != "OK")
        self.assertEqual(faults, stats["expected_errors"])


@unittest.skipIf(pandas is None, "cần pandas (csv_input)")
class TestCommandLine(unittest.TestCase):
    """Chạy `python -m core.gen_workload` trong thư mục tạm."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cwd = Path(self.tmp.name)
        # đảm bảo file mẫu của cả nhóm luôn được trả về nguyên vẹn
        self.sample_before = SAMPLE_ADDRESSES.read_bytes()
        self.addCleanup(SAMPLE_ADDRESSES.write_bytes, self.sample_before)

    def run_cli(self, *args):
        env = dict(os.environ, PYTHONPATH=str(SRC_DIR))
        return subprocess.run(
            [sys.executable, "-B", "-m", "core.gen_workload", *args],
            cwd=self.cwd, env=env, capture_output=True, text=True)

    def test_default_output_does_not_touch_sample_input(self):
        result = self.run_cli("--count", "3", "--seed", "1",
                              "--segments", SEGMENTS)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.sample_before, SAMPLE_ADDRESSES.read_bytes())
        generated = self.cwd / DEFAULT_OUTPUT
        self.assertTrue(generated.exists())
        self.assertEqual(len(read_rows(generated)), 3)
        self.assertFalse((self.cwd / "input").exists())

    def test_explicit_output_is_respected(self):
        target = self.cwd / "tu_chon" / "addr.csv"
        result = self.run_cli("--count", "5", "--seed", "2",
                              "--segments", SEGMENTS, "--output", str(target))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(read_rows(target)), 5)
        self.assertFalse((self.cwd / DEFAULT_OUTPUT).exists())
        self.assertEqual(self.sample_before, SAMPLE_ADDRESSES.read_bytes())

    def test_bad_segments_file_gives_clean_error(self):
        result = self.run_cli(
            "--segments", str(INPUT_DIR / "error_cases" / "segments_overlap.csv"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("chồng lấn", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((self.cwd / DEFAULT_OUTPUT).exists())

    def test_mem_size_option(self):
        result = self.run_cli("--segments", SEGMENTS, "--mem-size", "1000")
        self.assertEqual(result.returncode, 2)
        self.assertIn("vượt kích thước bộ nhớ vật lý 1000", result.stderr)


if __name__ == "__main__":
    unittest.main()

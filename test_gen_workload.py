"""Test cho core/gen_workload.py (TV5)."""
import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.gen_workload import generate_workload
from tests.helpers import INPUT_DIR, REPO_ROOT

SEGMENTS = str(INPUT_DIR / "segments.csv")

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
                       {"error_rate": True}):
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

    def test_mem_size_is_respected(self):
        with self.assertRaises(ValueError):
            generate_workload(SEGMENTS, self.out, 10, mem_size=1000)

    def test_default_output_does_not_touch_sample_input(self):
        sample = INPUT_DIR / "addresses.csv"
        before = sample.read_bytes()
        subprocess.run(
            [sys.executable, "-m", "core.gen_workload", "--count", "3",
             "--seed", "1", "--segments", SEGMENTS],
            cwd=REPO_ROOT / "src", check=True, capture_output=True)
        self.assertEqual(before, sample.read_bytes())
        generated = REPO_ROOT / "src" / "output" / "addresses_generated.csv"
        if generated.exists():
            generated.unlink()
            try:
                generated.parent.rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()

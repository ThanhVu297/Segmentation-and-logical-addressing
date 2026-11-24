import csv
import tempfile
import unittest
from pathlib import Path

from core.benchmark import make_oracle
from core.gen_workload import generate_workload
from tests.helpers import load_table


SEGMENTS_CSV = """seg_id,base,limit,perm
0,1000,400,R-X
1,2000,1000,RW-
2,3500,500,R--
"""


class TestGenerateWorkload(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.segments_path = self.root / "segments.csv"
        self.segments_path.write_text(SEGMENTS_CSV, encoding="utf-8")

    def read_rows(self, path):
        with path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            self.assertEqual(reader.fieldnames, ["seg_id", "offset", "access"])
            return list(reader)

    def test_generates_expected_row_count_and_error_rate(self):
        output_path = self.root / "nested" / "addresses.csv"
        stats = generate_workload(
            self.segments_path, output_path, count=20, error_rate=0.25, seed=7
        )

        rows = self.read_rows(output_path)
        oracle = make_oracle(load_table(self.segments_path))
        statuses = [
            oracle(int(row["seg_id"]), int(row["offset"]), row["access"])[0]
            for row in rows
        ]

        self.assertEqual(len(rows), 20)
        self.assertEqual(stats["total"], 20)
        self.assertEqual(stats["expected_errors"], 5)
        self.assertEqual(stats["expected_ok"], 15)
        self.assertEqual(statuses.count("OK"), stats["expected_ok"])
        self.assertEqual(sum(status != "OK" for status in statuses), stats["expected_errors"])
        self.assertEqual(stats["output_path"], str(output_path))

    def test_same_seed_produces_identical_workload(self):
        first = self.root / "first.csv"
        second = self.root / "second.csv"
        generate_workload(self.segments_path, first, count=30, error_rate=0.4, seed=42)
        generate_workload(self.segments_path, second, count=30, error_rate=0.4, seed=42)

        self.assertEqual(self.read_rows(first), self.read_rows(second))

    def test_error_rate_zero_generates_only_valid_addresses(self):
        output_path = self.root / "valid-only.csv"
        stats = generate_workload(
            self.segments_path, output_path, count=12, error_rate=0, seed=1
        )
        oracle = make_oracle(load_table(self.segments_path))
        statuses = [
            oracle(int(row["seg_id"]), int(row["offset"]), row["access"])[0]
            for row in self.read_rows(output_path)
        ]

        self.assertEqual(stats["expected_errors"], 0)
        self.assertEqual(statuses, ["OK"] * 12)

    def test_invalid_count_and_error_rate_raise_value_error(self):
        for count, error_rate in ((0, 0.1), (-1, 0.1), (10, -0.1), (10, 1.1)):
            with self.subTest(count=count, error_rate=error_rate):
                with self.assertRaises(ValueError):
                    generate_workload(
                        self.segments_path,
                        self.root / "invalid.csv",
                        count=count,
                        error_rate=error_rate,
                    )

    def test_no_readable_or_executable_access_raises_value_error(self):
        restricted_path = self.root / "restricted.csv"
        restricted_path.write_text(
            "seg_id,base,limit,perm\n0,100,10,---\n", encoding="utf-8"
        )
        with self.assertRaises(ValueError):
            generate_workload(
                restricted_path, self.root / "never-created.csv", count=1
            )


if __name__ == "__main__":
    unittest.main()

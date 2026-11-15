import csv
import tempfile
import unittest
from pathlib import Path

from core.csv_output import write_steps_csv, write_trace_csv
from core.result_types import Status, Step, TranslationResult


class TestCsvOutput(unittest.TestCase):
    def test_writes_summary_and_each_trace_step(self):
        results = [TranslationResult(
            seg_id=0,
            offset=100,
            access="R",
            base=1000,
            limit=400,
            physical=1100,
            status=Status.OK,
            steps=[Step("Input hợp lệ"), Step("Physical = 1000 + 100 = 1100")],
        )]
        with tempfile.TemporaryDirectory() as temp_dir:
            summary = write_trace_csv(results, Path(temp_dir) / "trace.csv")
            steps = write_steps_csv(results, Path(temp_dir) / "trace_steps.csv")
            with summary.open(newline="", encoding="utf-8-sig") as file:
                summary_rows = list(csv.DictReader(file))
            with steps.open(newline="", encoding="utf-8-sig") as file:
                step_rows = list(csv.DictReader(file))

        self.assertEqual(len(summary_rows), 1)
        self.assertEqual(summary_rows[0]["physical"], "1100")
        self.assertEqual(len(step_rows), 2)
        self.assertEqual(step_rows[1]["step_no"], "2")
        self.assertEqual(step_rows[1]["step_description"], "Physical = 1000 + 100 = 1100")
        self.assertEqual(step_rows[1]["status"], "OK")

    def test_writes_a_row_for_invalid_result_without_steps(self):
        result = TranslationResult(
            seg_id=None,
            offset=None,
            access=None,
            status=Status.INVALID_INPUT,
            reason="Dòng 2: offset không hợp lệ",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output = write_steps_csv([result], Path(temp_dir) / "steps.csv")
            with output.open(newline="", encoding="utf-8-sig") as file:
                rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "INVALID_INPUT")
        self.assertEqual(rows[0]["reason"], "Dòng 2: offset không hợp lệ")
        self.assertEqual(rows[0]["step_no"], "")


if __name__ == "__main__":
    unittest.main()

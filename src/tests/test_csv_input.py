import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.csv_input import (
    ValidationError,
    read_and_validate_addresses,
    read_and_validate_segments,
)


class TestCsvInput(unittest.TestCase):
    def write_temp_csv(self, directory, name, content):
        path = Path(directory) / name
        path.write_text(content, encoding="utf-8")
        return str(path)

    def test_completely_empty_segments_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_temp_csv(temp_dir, "segments.csv", "")

            with self.assertRaises(ValidationError):
                read_and_validate_segments(path)

    def test_segments_with_header_but_no_rows_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_temp_csv(
                temp_dir, "segments.csv", "seg_id,base,limit,perm\n"
            )

            with self.assertRaises(ValidationError):
                read_and_validate_segments(path)

    def test_completely_empty_addresses_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_temp_csv(temp_dir, "addresses.csv", "")

            with self.assertRaises(ValidationError):
                read_and_validate_addresses(path)

    def test_addresses_with_header_but_no_rows_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_temp_csv(
                temp_dir, "addresses.csv", "seg_id,offset,access\n"
            )

            with self.assertRaises(ValidationError):
                read_and_validate_addresses(path)

    def test_missing_address_column_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_temp_csv(
                temp_dir, "addresses.csv", "seg_id,offset\n0,10\n"
            )

            with self.assertRaises(ValidationError):
                read_and_validate_addresses(path)

    def test_bad_address_rows_are_marked_invalid_and_other_rows_are_kept(self):
        content = (
            "seg_id,offset,access\n"
            "0,10,R\n"
            "1,not-a-number,R\n"
            "2,20,Q\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_temp_csv(temp_dir, "addresses.csv", content)
            result = read_and_validate_addresses(path)

        self.assertEqual(len(result), 3)
        self.assertEqual(result.iloc[0]["status"], "OK")
        self.assertEqual(result.iloc[1]["status"], "INVALID_INPUT")
        self.assertEqual(result.iloc[2]["status"], "INVALID_INPUT")


if __name__ == "__main__":
    unittest.main()

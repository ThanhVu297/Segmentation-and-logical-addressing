import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.csv_input import read_and_validate_addresses, read_and_validate_segments
from core.csv_output import write_trace_csv
from core.result_types import Segment, SegmentTable
from core.translator import translate


class TestTranslationIntegration(unittest.TestCase):
    def test_csv_to_translation_to_trace_csv(self):
        segments_csv = (
            "seg_id,base,limit,perm\n"
            "0,1000,400,R-X\n"
        )
        addresses_csv = (
            "seg_id,offset,access\n"
            "0,100,R\n"
            "0,400,R\n"
            "0,20,W\n"
            "3,10,R\n"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            segments_path = temp_dir / "segments.csv"
            addresses_path = temp_dir / "addresses.csv"
            trace_path = temp_dir / "trace.csv"

            segments_path.write_text(segments_csv, encoding="utf-8")
            addresses_path.write_text(addresses_csv, encoding="utf-8")

            segments_df = read_and_validate_segments(str(segments_path))
            addresses_df = read_and_validate_addresses(str(addresses_path))

            table = SegmentTable(mem_size=5000)
            for row in segments_df.itertuples(index=False):
                table.add(
                    Segment(
                        int(row.seg_id),
                        int(row.base),
                        int(row.limit),
                        str(row.perm),
                    )
                )

            results = [
                translate(table, int(row.seg_id), int(row.offset), str(row.access))
                for row in addresses_df.itertuples(index=False)
            ]
            write_trace_csv(results, trace_path)

            with trace_path.open(newline="", encoding="utf-8-sig") as file:
                actual = list(csv.DictReader(file))

        expected = [
            ("OK", "1100"),
            ("OFFSET_OUT_OF_RANGE", ""),
            ("PROTECTION_FAULT", ""),
            ("SEGMENT_FAULT", ""),
        ]
        actual_summary = [
            (row["status"], row["physical"])
            for row in actual
        ]

        self.assertEqual(actual_summary, expected)


if __name__ == "__main__":
    unittest.main()

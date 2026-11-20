import csv

from core.app import SegmentationController
from core.result_types import Status


def test_controller_loads_translates_and_exports_trace(tmp_path):
    segments_file = tmp_path / "segments.csv"
    addresses_file = tmp_path / "addresses.csv"
    trace_file = tmp_path / "trace.csv"

    segments_file.write_text(
        "seg_id,base,limit,perm\n"
        "0,1000,400,R-X\n",
        encoding="utf-8",
    )
    addresses_file.write_text(
        "seg_id,offset,access\n"
        "0,100,R\n"
        "0,400,R\n"
        "x,10,R\n",
        encoding="utf-8",
    )

    controller = SegmentationController(mem_size=5000)

    controller.load_files(str(segments_file), str(addresses_file))
    results = controller.translate_batch()
    summary_path, steps_path = controller.export_trace(results, trace_file)

    assert [result.status for result in results] == [
        Status.OK,
        Status.OFFSET_OUT_OF_RANGE,
        Status.INVALID_INPUT,
    ]
    assert results[0].physical == 1100
    assert summary_path.exists()
    assert steps_path.exists()

    with summary_path.open(newline="", encoding="utf-8-sig") as file:
        trace_rows = list(csv.DictReader(file))

    assert len(trace_rows) == 3
    assert trace_rows[0]["physical"] == "1100"
    assert trace_rows[0]["status"] == "OK"
    assert trace_rows[2]["status"] == "INVALID_INPUT"

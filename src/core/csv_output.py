"""Write translation results and detailed algorithm steps to CSV files."""

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CSV_COLUMNS = [
    "seg_id",
    "offset",
    "access",
    "base",
    "limit",
    "physical",
    "status",
    "reason",
]

STEP_CSV_COLUMNS = [
    "result_no",
    "seg_id",
    "offset",
    "access",
    "base",
    "limit",
    "physical",
    "status",
    "reason",
    "step_no",
    "step_description",
    "step_ok",
]


def _output_path(output_path=None, default_name="trace.csv"):
    if output_path is None:
        file_path = PROJECT_ROOT / "output" / default_name
    else:
        file_path = Path(output_path)
        if not file_path.is_absolute():
            file_path = PROJECT_ROOT / file_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def _status_value(result):
    return result.status.value if hasattr(result.status, "value") else result.status


def write_trace_csv(results, output_path=None):
    """Write one summary row per TranslationResult."""
    file_path = _output_path(output_path)
    with file_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for result in results:
            writer.writerow({
                "seg_id": result.seg_id,
                "offset": result.offset,
                "access": result.access,
                "base": result.base,
                "limit": result.limit,
                "physical": result.physical,
                "status": _status_value(result),
                "reason": result.reason,
            })
    return file_path


def write_steps_csv(results, output_path=None):
    """Write one row per algorithm step, retaining the related result fields."""
    file_path = _output_path(output_path, "trace_steps.csv")
    with file_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=STEP_CSV_COLUMNS)
        writer.writeheader()
        for result_no, result in enumerate(results, start=1):
            steps = result.steps or [None]
            for step_no, step in enumerate(steps, start=1):
                writer.writerow({
                    "result_no": result_no,
                    "seg_id": result.seg_id,
                    "offset": result.offset,
                    "access": result.access,
                    "base": result.base,
                    "limit": result.limit,
                    "physical": result.physical,
                    "status": _status_value(result),
                    "reason": result.reason,
                    "step_no": step_no if step is not None else "",
                    "step_description": step.description if step is not None else "",
                    "step_ok": step.ok if step is not None else "",
                })
    return file_path

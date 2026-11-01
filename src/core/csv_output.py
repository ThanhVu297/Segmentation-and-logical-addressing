
"""Ghi ket qua dich dia chi ra file CSV."""

import csv
from pathlib import Path


# Thu muc goc cua project
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Cau truc cot CSV theo README
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


def write_trace_csv(results, output_path=None):
    """
    Ghi danh sach TranslationResult vao file CSV.

    Args:
        results: Danh sach ket qua dich dia chi.
        output_path: Duong dan file CSV (mac dinh output/trace.csv).

    Returns:
        Duong dan file CSV da ghi.
    """

    # Neu khong truyen duong dan, su dung output/trace.csv
    if output_path is None:
        file_path = PROJECT_ROOT / "output" / "trace.csv"
    else:
        file_path = Path(output_path)

        if not file_path.is_absolute():
            file_path = PROJECT_ROOT / file_path

    # Tao thu muc output neu chua ton tai
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Ghi du lieu vao CSV
    with file_path.open(
        mode="w",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=CSV_COLUMNS,
        )

        # Ghi dong tieu de
        writer.writeheader()

        # Ghi tung ket qua
        for result in results:
            status = result.status

            # Chuyen Enum Status thanh chuoi
            if hasattr(status, "value"):
                status = status.value

            writer.writerow({
                "seg_id": result.seg_id,
                "offset": result.offset,
                "access": result.access,
                "base": result.base,
                "limit": result.limit,
                "physical": result.physical,
                "status": status,
                "reason": result.reason,
            })

    return file_path

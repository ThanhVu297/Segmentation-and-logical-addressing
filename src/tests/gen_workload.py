"""Sinh workload addresses.csv ngẫu nhiên cho mô phỏng phân đoạn.

Tỷ lệ lỗi là tỷ lệ các dòng được cố ý tạo ra để phát sinh một trong ba lỗi
khi dịch địa chỉ: SEGMENT_FAULT, OFFSET_OUT_OF_RANGE hoặc PROTECTION_FAULT.
File đầu ra vẫn giữ đúng schema: seg_id,offset,access.

Mặc định ghi ra output/addresses_generated.csv để KHÔNG ghi đè file mẫu
input/addresses.csv; muốn thay file mẫu thì truyền --output input/addresses.csv.

Segment table được đọc và kiểm tra bằng core.csv_input (cùng luật với GUI);
nếu truyền mem_size nhỏ hơn 5000 thì kiểm tra thêm bằng core.validator.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from pathlib import Path

if __package__ in (None, ""):  # chạy trực tiếp: python src/core/gen_workload.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ACCESS_TYPES = ("R", "W", "X")
ACCESS_INDEX = {"R": 0, "W": 1, "X": 2}
MEMORY_SIZE = 5000  # kích thước bộ nhớ vật lý của đề bài (cũng là giới hạn csv_input)
DEFAULT_OUTPUT = "output/addresses_generated.csv"


def _load_segments(segments_path, mem_size=MEMORY_SIZE):
    """Đọc segment table bằng csv_input rồi kiểm tra thêm với mem_size.

    Mọi lỗi dữ liệu được đổi thành ValueError (thông báo giữ nguyên của
    csv_input/validator) để nơi gọi chỉ cần bắt (OSError, ValueError).
    """
    from core.csv_input import ValidationError, read_and_validate_segments
    from core.result_types import Segment, SegmentTable
    from core.validator import validate_table

    try:
        frame = read_and_validate_segments(str(segments_path))
    except ValidationError as error:
        raise ValueError(str(error)) from None

    table = SegmentTable(mem_size)
    segments = []
    for row in frame.itertuples(index=False):
        segment = {
            "seg_id": int(row.seg_id),
            "base": int(row.base),
            "limit": int(row.limit),
            "perm": str(row.perm).strip().upper(),
        }
        segments.append(segment)
        table.add(Segment(**segment))

    issues = validate_table(table, mem_size)
    if issues:
        raise ValueError("; ".join(issue.message for issue in issues))
    if not segments:
        raise ValueError("segments.csv không có segment nào")
    return segments


def generate_workload(
    segments_path="input/segments.csv",
    output_path=DEFAULT_OUTPUT,
    count=100,
    error_rate=0.1,
    seed=None,
    mem_size=MEMORY_SIZE,
):
    """Sinh addresses.csv và trả về thống kê số dòng OK/lỗi được dự kiến.

    Args:
        segments_path: Đường dẫn đến segments.csv.
        output_path: Đường dẫn file addresses.csv cần tạo.
        count: Tổng số địa chỉ cần sinh (số nguyên dương).
        error_rate: Tỷ lệ dòng lỗi trong khoảng 0.0 đến 1.0; số dòng lỗi
            được làm tròn đến số nguyên gần nhất (nửa làm tròn lên).
        seed: Seed tùy chọn để có thể tái tạo cùng một workload.
        mem_size: Kích thước bộ nhớ vật lý dùng để kiểm tra segment table
            (1 đến 5000; 5000 là giới hạn hiện tại của csv_input).

    Raises:
        ValueError: tham số sai hoặc segments.csv không hợp lệ.
        OSError: không đọc/ghi được file.
    """
    if type(count) is not int or count <= 0:
        raise ValueError("count phải là số nguyên > 0")
    if type(mem_size) is not int or not 0 < mem_size <= MEMORY_SIZE:
        raise ValueError(f"mem_size phải là số nguyên trong khoảng 1 đến {MEMORY_SIZE}")
    if isinstance(error_rate, bool):
        raise ValueError("error_rate phải là số trong khoảng 0.0 đến 1.0, không phải True/False")
    if not isinstance(error_rate, (int, float)) or not math.isfinite(error_rate):
        raise ValueError("error_rate phải là số hữu hạn trong khoảng 0.0 đến 1.0")
    if not 0 <= error_rate <= 1:
        raise ValueError("error_rate phải nằm trong khoảng 0.0 đến 1.0")

    rng = random.Random(seed)
    segments = _load_segments(segments_path, mem_size)

    # Chỉ tạo địa chỉ hợp lệ ở nhóm OK: access phải được segment cho phép.
    valid_choices = [
        (segment, access)
        for segment in segments
        for access in ACCESS_TYPES
        if segment["perm"][ACCESS_INDEX[access]] == access
    ]
    if not valid_choices:
        raise ValueError(
            "Không có segment nào cho phép R, W hoặc X để sinh địa chỉ hợp lệ"
        )

    missing_id = max(segment["seg_id"] for segment in segments) + 1

    # Các lỗi khả thi phụ thuộc vào segment table hiện tại.
    fault_types = ["SEGMENT_FAULT", "OFFSET_OUT_OF_RANGE"]
    denied_choices = [
        (segment, access)
        for segment in segments
        for access in ACCESS_TYPES
        if segment["perm"][ACCESS_INDEX[access]] != access
    ]
    if denied_choices:
        fault_types.append("PROTECTION_FAULT")

    # Làm tròn nửa lên để số dòng lỗi ổn định, dễ dự đoán (không dùng
    # round() vì round dùng quy tắc ties-to-even của Python).
    error_count = int(count * error_rate + 0.5)
    rows = []

    for _ in range(count - error_count):
        segment, access = rng.choice(valid_choices)
        rows.append((segment["seg_id"], rng.randrange(segment["limit"]), access))

    for _ in range(error_count):
        fault = rng.choice(fault_types)
        if fault == "SEGMENT_FAULT":
            rows.append((missing_id, rng.randrange(0, 100), rng.choice(ACCESS_TYPES)))
        elif fault == "OFFSET_OUT_OF_RANGE":
            segment = rng.choice(segments)
            # offset == limit là trường hợp biên không hợp lệ.
            rows.append(
                (segment["seg_id"], segment["limit"], rng.choice(ACCESS_TYPES))
            )
        else:
            segment, access = rng.choice(denied_choices)
            rows.append((segment["seg_id"], rng.randrange(segment["limit"]), access))

    rng.shuffle(rows)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["seg_id", "offset", "access"])
        writer.writerows(rows)

    return {
        "total": count,
        "expected_errors": error_count,
        "expected_ok": count - error_count,
        "error_rate": error_rate,
        "output_path": str(output),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Sinh addresses.csv ngẫu nhiên với tỷ lệ lỗi tùy chỉnh."
    )
    parser.add_argument(
        "--segments", default="input/segments.csv", help="Đường dẫn segments.csv"
    )
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT,
        help=f"Đường dẫn addresses.csv đầu ra (mặc định: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--mem-size", type=int, default=MEMORY_SIZE,
        help=f"Kích thước bộ nhớ vật lý để kiểm tra segment (mặc định: {MEMORY_SIZE})",
    )
    parser.add_argument(
        "--count", type=int, default=100,
        help="Tổng số địa chỉ cần sinh (mặc định: 100)",
    )
    parser.add_argument(
        "--error-rate", type=float, default=0.1,
        help="Tỷ lệ lỗi từ 0 đến 1; số dòng lỗi được làm tròn nửa lên (mặc định: 0.1)",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Seed để tái tạo dữ liệu"
    )
    args = parser.parse_args()

    try:
        stats = generate_workload(
            args.segments, args.output, args.count, args.error_rate, args.seed,
            args.mem_size,
        )
    except (OSError, ValueError, ImportError) as error:
        parser.error(str(error))

    print("Đã sinh workload thành công!")
    print(f"- Tổng số dòng: {stats['total']}")
    print(f"- Dòng lỗi dự kiến: {stats['expected_errors']}")
    print(f"- Dòng hợp lệ dự kiến: {stats['expected_ok']}")
    print(f"- File: {stats['output_path']}")


if __name__ == "__main__":
    main()

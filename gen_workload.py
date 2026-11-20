"""Sinh workload addresses.csv ngẫu nhiên cho mô phỏng phân đoạn.

Tỷ lệ lỗi là tỷ lệ các dòng được cố ý tạo ra để phát sinh một trong ba lỗi
khi dịch địa chỉ: SEGMENT_FAULT, OFFSET_OUT_OF_RANGE hoặc PROTECTION_FAULT.
File đầu ra vẫn giữ đúng schema: seg_id,offset,access.
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
MEMORY_SIZE = 5000


def _load_segments(segments_path, mem_size=MEMORY_SIZE):
    """Đọc segment table bằng csv_input (một nguồn kiểm tra duy nhất).

    Tái dùng read_and_validate_segments để quy tắc hợp lệ giống hệt chương
    trình chính (số nguyên, trùng seg_id, perm, vượt bộ nhớ, chồng lấn...).
    Mọi lỗi được đổi thành ValueError để CLI báo lỗi gọn.
    """
    try:
        from core.csv_input import ValidationError, read_and_validate_segments
    except ImportError as error:  # thiếu pandas hoặc chạy sai thư mục
        raise ValueError(f"Không import được core.csv_input: {error}") from None

    try:
        df = read_and_validate_segments(str(segments_path))
    except ValidationError as error:
        raise ValueError(str(error)) from None

    segments = [
        {
            "seg_id": int(row.seg_id),
            "base": int(row.base),
            "limit": int(row.limit),
            "perm": str(row.perm).strip().upper(),
        }
        for row in df.itertuples(index=False)
    ]
    if not segments:
        raise ValueError("segments.csv không có segment nào")
    for segment in segments:
        if segment["base"] + segment["limit"] > mem_size:
            raise ValueError(
                f"segment {segment['seg_id']} vượt quá kích thước bộ nhớ {mem_size}"
            )
    return segments


def generate_workload(
    segments_path="input/segments.csv",
    output_path="output/addresses_generated.csv",
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
        mem_size: Kích thước bộ nhớ vật lý để kiểm tra segment (mặc định 5000).

    Mặc định ghi vào output/ để không ghi đè file mẫu input/addresses.csv.
    """
    if type(count) is not int or count <= 0:
        raise ValueError("count phải là số nguyên > 0")
    if (
        isinstance(error_rate, bool)
        or not isinstance(error_rate, (int, float))
        or not math.isfinite(error_rate)
    ):
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
    if not valid_choices and error_rate < 1:
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
        "--output", default="output/addresses_generated.csv",
        help="Đường dẫn file đầu ra (mặc định: output/addresses_generated.csv)",
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
    parser.add_argument(
        "--mem-size", type=int, default=MEMORY_SIZE,
        help="Kích thước bộ nhớ vật lý (mặc định: 5000)",
    )
    args = parser.parse_args()

    try:
        stats = generate_workload(
            args.segments, args.output, args.count, args.error_rate, args.seed,
            args.mem_size,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))

    print("Đã sinh workload thành công!")
    print(f"- Tổng số dòng: {stats['total']}")
    print(f"- Dòng lỗi dự kiến: {stats['expected_errors']}")
    print(f"- Dòng hợp lệ dự kiến: {stats['expected_ok']}")
    print(f"- File: {stats['output_path']}")


if __name__ == "__main__":
    main()

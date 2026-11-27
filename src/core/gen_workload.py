"""Sinh workload với access và perm chỉ viết hoa."""
from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path

ACCESS_TYPES = ("R", "W", "X")
ACCESS_INDEX = {"R": 0, "W": 1, "X": 2}
MEMORY_SIZE = 5000


def _load_segments(segments_path):
    segments = []
    with open(segments_path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != ["seg_id", "base", "limit", "perm"]:
            raise ValueError("segments.csv phải có đúng các cột theo thứ tự: seg_id,base,limit,perm")

        seen_ids = set()
        used_ranges = []
        for line_no, row in enumerate(reader, start=2):
            try:
                seg_id = int(row["seg_id"])
                base = int(row["base"])
                limit = int(row["limit"])
                perm = row["perm"].strip()
            except (TypeError, ValueError):
                raise ValueError(f"Dữ liệu không hợp lệ tại dòng {line_no}") from None

            if seg_id < 0 or base < 0 or limit <= 0 or seg_id in seen_ids:
                raise ValueError(f"seg_id/base/limit không hợp lệ tại dòng {line_no}")
            if len(perm) != 3 or any(char not in allowed for char, allowed in zip(perm, ("R-", "W-", "X-"))):
                raise ValueError(f"perm không hợp lệ tại dòng {line_no}; chỉ nhận chữ hoa")
            if base + limit > MEMORY_SIZE:
                raise ValueError(f"segment tại dòng {line_no} vượt quá kích thước bộ nhớ {MEMORY_SIZE}")

            start, end = base, base + limit
            overlaps = any(existing_start < end and start < existing_end
                           for existing_start, existing_end in used_ranges)
            if overlaps:
                raise ValueError(f"segment chồng lấn với segment khác tại dòng {line_no}")

            seen_ids.add(seg_id)
            used_ranges.append((start, end))
            segments.append({"seg_id": seg_id, "base": base, "limit": limit, "perm": perm})

    if not segments:
        raise ValueError("segments.csv không có segment nào")
    return segments


def generate_workload(segments_path="input/segments.csv", output_path="input/addresses.csv",
                      count=100, error_rate=0.1, seed=None):
    if type(count) is not int or count <= 0:
        raise ValueError("count phải là số nguyên > 0")
    if not isinstance(error_rate, (int, float)) or not math.isfinite(error_rate):
        raise ValueError("error_rate phải là số hữu hạn trong khoảng 0.0 đến 1.0")
    if not 0 <= error_rate <= 1:
        raise ValueError("error_rate phải nằm trong khoảng 0.0 đến 1.0")

    rng = random.Random(seed)
    segments = _load_segments(segments_path)
    valid_choices = [(segment, access) for segment in segments for access in ACCESS_TYPES
                     if segment["perm"][ACCESS_INDEX[access]] == access]
    if not valid_choices:
        raise ValueError("Không có segment nào cho phép R, W hoặc X để sinh địa chỉ hợp lệ")

    missing_id = max(segment["seg_id"] for segment in segments) + 1
    fault_types = ["SEGMENT_FAULT", "OFFSET_OUT_OF_RANGE"]
    denied_choices = [(segment, access) for segment in segments for access in ACCESS_TYPES
                      if segment["perm"][ACCESS_INDEX[access]] != access]
    if denied_choices:
        fault_types.append("PROTECTION_FAULT")

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
            rows.append((segment["seg_id"], segment["limit"], rng.choice(ACCESS_TYPES)))
        else:
            segment, access = rng.choice(denied_choices)
            rows.append((segment["seg_id"], rng.randrange(segment["limit"]), access))

    rng.shuffle(rows)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig ghi BOM để Excel nhận diện đúng encoding; reader utf-8-sig
    # cũng đọc được cả CSV có BOM lẫn không có BOM.
    with output.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["seg_id", "offset", "access"])
        writer.writerows(rows)

    return {"total": count, "expected_errors": error_count,
            "expected_ok": count - error_count, "error_rate": error_rate,
            "output_path": str(output)}


def main():
    parser = argparse.ArgumentParser(description="Sinh addresses.csv chỉ dùng R, W, X viết hoa")
    parser.add_argument("--segments", default="input/segments.csv")
    parser.add_argument("--output", default="input/addresses.csv")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--error-rate", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    try:
        stats = generate_workload(args.segments, args.output, args.count, args.error_rate, args.seed)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print("Đã sinh workload thành công!")
    print(f"- Tổng số dòng: {stats['total']}")
    print(f"- Dòng lỗi dự kiến: {stats['expected_errors']}")
    print(f"- Dòng hợp lệ dự kiến: {stats['expected_ok']}")
    print(f"- File: {stats['output_path']}")


if __name__ == "__main__":
    main()

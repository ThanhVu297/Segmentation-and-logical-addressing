"""benchmark.py - TV5: đo hiệu năng dịch địa chỉ và đối chiếu với oracle.

Chạy từ thư mục gốc repo:
    python src/core/benchmark.py --segments input/segments.csv

Phương pháp đo (ghi vào báo cáo Q5):
  * Cùng một seed => cùng bộ địa chỉ ở mọi lần chạy (tái lập được).
  * Sinh địa chỉ và tính kết quả mong đợi (oracle) NGOÀI vùng đo thời gian.
  * Dùng time.perf_counter, lặp `repeats` lần, báo min và median.
  * Vòng đo không giữ lại kết quả (tránh tốn RAM với 1.000.000 địa chỉ);
    việc đối chiếu với oracle chạy ở một lượt riêng, không tính thời gian.
  * ratio_prev = median(n) / median(n_trước); nếu thuật toán O(n) thì
    ratio_prev xấp xỉ expected_ratio = n / n_trước.

Oracle viết độc lập với translator.py/protection.py, theo đúng thứ tự kiểm
tra trong README: segment -> offset -> quyền R/W/X. Mỗi địa chỉ được so cả
status lẫn physical với kết quả của translate().
"""
from __future__ import annotations

import argparse
import csv
import inspect
import random
import statistics
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from time import perf_counter

if __package__ in (None, ""):  # chạy trực tiếp: python src/core/benchmark.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.validator import get_segments, validate_table  # noqa: E402

DEFAULT_SIZES = (1_000, 10_000, 100_000, 1_000_000)
ACCESS_TYPES = ("R", "W", "X")
_PERM_INDEX = {"R": 0, "W": 1, "X": 2}


@dataclass
class BenchRow:
    n: int
    repeats: int
    min_s: float
    median_s: float
    per_addr_us: float
    ratio_prev: float | None
    expected_ratio: float | None
    valid: int          # số địa chỉ oracle cho là OK
    faults: int         # số địa chỉ oracle cho là lỗi
    mismatches: int     # số địa chỉ translate() trả khác oracle


def generate_addresses(table, n, seed=42, invalid_ratio=0.2):
    """Sinh n bộ (seg_id, offset, access) có thể tái lập.

    Với xác suất invalid_ratio địa chỉ bị lỗi về segment/offset, gồm 4 loại:
    offset == limit (biên), offset > limit, segment không tồn tại, offset âm.
    access luôn chọn ngẫu nhiên R/W/X nên PROTECTION_FAULT xuất hiện tự nhiên.
    """
    rng = random.Random(seed)
    segs = [(s.seg_id, s.limit) for s in get_segments(table) if s.limit > 0]
    if not segs:
        raise ValueError("Segment table không có segment hợp lệ để sinh địa chỉ")
    missing_id = max(sid for sid, _ in segs) + 1
    out = []
    for _ in range(n):
        sid, limit = rng.choice(segs)
        access = rng.choice(ACCESS_TYPES)
        if rng.random() < invalid_ratio:
            kind = rng.randrange(4)
            if kind == 0:
                out.append((sid, limit, access))
            elif kind == 1:
                out.append((sid, limit + rng.randint(1, limit), access))
            elif kind == 2:
                out.append((missing_id, rng.randrange(limit), access))
            else:
                out.append((sid, -rng.randint(1, limit), access))
        else:
            out.append((sid, rng.randrange(limit), access))
    return out


def make_oracle(table):
    """Oracle độc lập: trả về (status, physical) theo đúng quy ước README."""
    spec = {s.seg_id: (s.base, s.limit, s.perm) for s in get_segments(table)}

    def oracle(seg_id, offset, access):
        entry = spec.get(seg_id)
        if entry is None:
            return ("SEGMENT_FAULT", None)
        base, limit, perm = entry
        if offset < 0 or offset >= limit:
            return ("OFFSET_OUT_OF_RANGE", None)
        if perm[_PERM_INDEX[access]] != access:
            return ("PROTECTION_FAULT", None)
        return ("OK", base + offset)

    return oracle


def default_extract(result):
    """Lấy (status, physical) từ TranslationResult của TV2.

    status có thể là Status (str Enum) hoặc chuỗi; physical là None khi lỗi.
    """
    status = getattr(result, "status", None)
    status = getattr(status, "value", status)
    return (None if status is None else str(status), getattr(result, "physical", None))


def _takes_access(translate_fn):
    """translate(table, seg_id, offset, access) hay translate(table, seg_id, offset)?"""
    try:
        params = [
            p for p in inspect.signature(translate_fn).parameters.values()
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
    except (TypeError, ValueError):
        return True
    return len(params) >= 4


def _time_pass(translate_fn, table, addrs, with_access):
    t0 = perf_counter()
    if with_access:
        for seg_id, offset, access in addrs:
            translate_fn(table, seg_id, offset, access)
    else:
        for seg_id, offset, _ in addrs:
            translate_fn(table, seg_id, offset)
    return perf_counter() - t0


def run_benchmark(table, translate_fn, sizes=DEFAULT_SIZES, repeats=3, seed=42,
                  invalid_ratio=0.2, extract=default_extract, progress=None):
    """Đo thời gian translate_fn cho từng kích thước và đối chiếu với oracle."""
    if repeats < 1:
        raise ValueError("repeats phải >= 1")
    oracle = make_oracle(table)
    with_access = _takes_access(translate_fn)
    rows = []
    prev_n = prev_median = None
    for n in sizes:
        if n <= 0:
            raise ValueError("kích thước phải > 0")
        addrs = generate_addresses(table, n, seed, invalid_ratio)

        times = [_time_pass(translate_fn, table, addrs, with_access)
                 for _ in range(repeats)]

        # lượt đối chiếu oracle (không tính thời gian, không giữ kết quả)
        valid = faults = mismatches = 0
        for seg_id, offset, access in addrs:
            expected = oracle(seg_id, offset, access)
            if with_access:
                result = translate_fn(table, seg_id, offset, access)
            else:
                result = translate_fn(table, seg_id, offset)
            if expected[0] == "OK":
                valid += 1
            else:
                faults += 1
            if extract(result) != expected:
                mismatches += 1

        median = statistics.median(times)
        row = BenchRow(
            n=n,
            repeats=repeats,
            min_s=min(times),
            median_s=median,
            per_addr_us=median / n * 1e6,
            ratio_prev=(median / prev_median) if prev_median else None,
            expected_ratio=(n / prev_n) if prev_n else None,
            valid=valid,
            faults=faults,
            mismatches=mismatches,
        )
        rows.append(row)
        if progress:
            progress(row)
        prev_n, prev_median = n, median
    return rows


def write_csv(rows, path):
    fields = list(BenchRow.__dataclass_fields__)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def format_rows(rows):
    head = (f"{'n':>10} {'min (s)':>10} {'median (s)':>11} {'us/addr':>9} "
            f"{'ratio':>7} {'expected':>9} {'mismatch':>9}")
    lines = [head]
    for r in rows:
        ratio = f"{r.ratio_prev:.2f}" if r.ratio_prev is not None else "-"
        exp = f"{r.expected_ratio:.1f}" if r.expected_ratio is not None else "-"
        lines.append(f"{r.n:>10} {r.min_s:>10.4f} {r.median_s:>11.4f} "
                     f"{r.per_addr_us:>9.3f} {ratio:>7} {exp:>9} {r.mismatches:>9}")
    return "\n".join(lines)


def table_from_dataframe(df, mem_size=5000):
    """Đổi DataFrame của csv_input.read_and_validate_segments thành SegmentTable."""
    from core.result_types import Segment, SegmentTable

    table = SegmentTable(mem_size)
    for row in df.itertuples(index=False):
        table.add(Segment(int(row.seg_id), int(row.base), int(row.limit),
                          str(row.perm)))
    return table


def main(argv=None):
    parser = argparse.ArgumentParser(description="Benchmark dịch địa chỉ segmentation")
    parser.add_argument("--segments", default="input/segments.csv")
    parser.add_argument("--mem-size", type=int, default=5000)
    parser.add_argument("--sizes", type=int, nargs="+", default=list(DEFAULT_SIZES))
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="output/benchmark.csv")
    args = parser.parse_args(argv)

    try:
        from core.csv_input import read_and_validate_segments
        from core.translator import translate
    except ImportError as exc:
        print(f"Không import được module của TV1/TV2: {exc}", file=sys.stderr)
        return 1

    table = table_from_dataframe(read_and_validate_segments(args.segments),
                                 args.mem_size)
    issues = validate_table(table, args.mem_size)
    for issue in issues:
        print("CẢNH BÁO:", issue.message)
    if issues:
        print("Segment table không hợp lệ, dừng benchmark.", file=sys.stderr)
        return 1

    rows = run_benchmark(
        table, translate, sizes=args.sizes, repeats=args.repeats, seed=args.seed,
        progress=lambda r: print(f"đã xong n={r.n}"))
    print(format_rows(rows))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    write_csv(rows, args.out)
    print(f"Đã ghi {args.out}")
    return 0 if all(r.mismatches == 0 for r in rows) else 2


if __name__ == "__main__":
    sys.exit(main())

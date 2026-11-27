"""Benchmark dịch địa chỉ segmentation và đối chiếu kết quả với oracle."""
"""Benchmark chỉ dùng perm và access viết hoa."""
from __future__ import annotations

import argparse
import csv
import inspect
import random
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.validator import get_segments, validate_table

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
    valid: int
    faults: int
    mismatches: int


def generate_addresses(table, n, seed=42, invalid_ratio=0.2):
    rng = random.Random(seed)
    segs = [(s.seg_id, s.limit) for s in get_segments(table) if s.limit > 0]
    if not segs:
        raise ValueError("Segment table không có segment hợp lệ để sinh địa chỉ")
    missing_id = max(seg_id for seg_id, _ in segs) + 1
    addresses = []
    for _ in range(n):
        seg_id, limit = rng.choice(segs)
        access = rng.choice(ACCESS_TYPES)
        if rng.random() < invalid_ratio:
            kind = rng.randrange(4)
            if kind == 0:
                addresses.append((seg_id, limit, access))
            elif kind == 1:
                addresses.append((seg_id, limit + rng.randint(1, limit), access))
            elif kind == 2:
                addresses.append((missing_id, rng.randrange(limit), access))
            else:
                addresses.append((seg_id, -rng.randint(1, limit), access))
        else:
            addresses.append((seg_id, rng.randrange(limit), access))
    return addresses


def make_oracle(table):
    spec = {
        seg.seg_id: (seg.base, seg.limit, str(seg.perm).strip().upper())
        for seg in get_segments(table)
    }
    spec = {s.seg_id: (s.base, s.limit, str(s.perm).strip())
            for s in get_segments(table)}

    def oracle(seg_id, offset, access):
        entry = spec.get(seg_id)
        if entry is None:
            return ("SEGMENT_FAULT", None)
        base, limit, perm = entry
        if offset < 0 or offset >= limit:
            return ("OFFSET_OUT_OF_RANGE", None)
        access = str(access).strip()
        position = _PERM_INDEX.get(access)
        if position is None or len(perm) != 3 or perm[position] != access:
            return ("PROTECTION_FAULT", None)
        return ("OK", base + offset)

    return oracle


def default_extract(result):
    status = getattr(result, "status", None)
    status = getattr(status, "value", status)
    return (None if status is None else str(status), getattr(result, "physical", None))


def _takes_access(translate_fn):
    """Return True for translate(table, seg_id, offset, access) signatures."""
    try:
        parameters = [
            parameter for parameter in inspect.signature(translate_fn).parameters.values()
            if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
        ]
    except (TypeError, ValueError):
        return True
    return len(parameters) >= 4


def _time_pass(translate_fn, table, addresses, with_access):
    start = perf_counter()
    if with_access:
        for seg_id, offset, access in addresses:
            translate_fn(table, seg_id, offset, access)
    else:
        for seg_id, offset, _ in addresses:
            translate_fn(table, seg_id, offset)
    return perf_counter() - start


def run_benchmark(table, translate_fn, sizes=DEFAULT_SIZES, repeats=3, seed=42,
                  invalid_ratio=0.2, extract=default_extract, progress=None):
    if repeats < 1:
        raise ValueError("repeats phải >= 1")
    oracle = make_oracle(table)
    with_access = _takes_access(translate_fn)
    rows = []
    previous_n = previous_median = None

    for n in sizes:
        if n <= 0:
            raise ValueError("kích thước phải > 0")
        addresses = generate_addresses(table, n, seed, invalid_ratio)
        times = [
            _time_pass(translate_fn, table, addresses, with_access)
            for _ in range(repeats)
        ]
        valid = faults = mismatches = 0
        for seg_id, offset, access in addresses:
            expected = oracle(seg_id, offset, access)
            result = (translate_fn(table, seg_id, offset, access) if with_access
                      else translate_fn(table, seg_id, offset))
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
            ratio_prev=median / previous_median if previous_median else None,
            expected_ratio=n / previous_n if previous_n else None,
            valid=valid,
            faults=faults,
            mismatches=mismatches,
        )
        rows.append(row)
        if progress:
            progress(row)
        previous_n, previous_median = n, median
    return rows


def write_csv(rows, path):
    fields = list(BenchRow.__dataclass_fields__)
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def format_rows(rows):
    header = (f"{'n':>10} {'min (s)':>10} {'median (s)':>11} {'us/addr':>9} "
              f"{'ratio':>7} {'expected':>9} {'mismatch':>9}")
    lines = [header]
    for row in rows:
        ratio = f"{row.ratio_prev:.2f}" if row.ratio_prev is not None else "-"
        expected = f"{row.expected_ratio:.1f}" if row.expected_ratio is not None else "-"
        lines.append(
            f"{row.n:>10} {row.min_s:>10.4f} {row.median_s:>11.4f} "
            f"{row.per_addr_us:>9.3f} {ratio:>7} {expected:>9} {row.mismatches:>9}"
        )
    return "\n".join(lines)


def table_from_dataframe(df, mem_size=5000):
    from core.result_types import Segment, SegmentTable

    table = SegmentTable(mem_size)
    for row in df.itertuples(index=False):
        table.add(Segment(int(row.seg_id), int(row.base), int(row.limit), str(row.perm).upper()))
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
        from core.csv_input import ValidationError, read_and_validate_segments
        from core.translator import translate
    except ImportError as exc:
        print(f"Không import được module: {exc}", file=sys.stderr)
        return 1

    try:
        table = table_from_dataframe(read_and_validate_segments(args.segments), args.mem_size)
    except FileNotFoundError:
        print(f"Không tìm thấy file: {args.segments}", file=sys.stderr)
        return 1
    except ValidationError as exc:
        print(f"segments.csv không hợp lệ:\n{exc}", file=sys.stderr)
        return 1

    issues = validate_table(table, args.mem_size)
    for issue in issues:
        print("CẢNH BÁO:", issue.message)
    if issues:
        print("Segment table không hợp lệ, dừng benchmark.", file=sys.stderr)
        return 1

    rows = run_benchmark(
        table, translate, sizes=args.sizes, repeats=args.repeats, seed=args.seed,
        progress=lambda row: print(f"đã xong n={row.n}"),
    )
    print(format_rows(rows))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    write_csv(rows, args.out)
    print(f"Đã ghi {args.out}")
    return 0 if all(row.mismatches == 0 for row in rows) else 2


if __name__ == "__main__":
    sys.exit(main())

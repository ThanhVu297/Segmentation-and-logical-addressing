"""Benchmark chỉ dùng perm và access viết hoa."""
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

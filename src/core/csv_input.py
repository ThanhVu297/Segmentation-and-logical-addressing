import csv
import os
import re
import sys
from typing import Dict, List, Tuple

import pandas as pd

SEGMENT_COLS = ["seg_id", "base", "limit", "perm"]
ADDRESS_COLS = ["seg_id", "offset", "access"]

VALID_ACCESS = {"R", "W", "X"}  # input được tự chuyển thành chữ hoa trước khi kiểm tra
PERM_PATTERN = re.compile(r"^[R-][W-][X-]$")
INT_PATTERN = re.compile(r"^[+-]?[0-9]+$")

STATUS_OK = "OK"
STATUS_INVALID_INPUT = "INVALID_INPUT"


class ValidationError(Exception):


def _parse_int(text: str):
    text = text.strip()
    if INT_PATTERN.match(text):
        return int(text)
    return None


def _read_csv(filepath: str, required_cols: List[str]) -> Tuple[Dict[str, int], int, List[Tuple[int, List[str]]]]:
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Không tìm thấy file: {filepath}")

    header = None
    rows: List[Tuple[int, List[str]]] = []
    try:
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            for line_no, fields in enumerate(csv.reader(f), start=1):
                if not any(cell.strip() for cell in fields):
                    continue
                if header is None:
                    header = [c.strip() for c in fields]
                else:
                    rows.append((line_no, fields))
    except (UnicodeDecodeError, csv.Error) as e:
        raise ValidationError(f"File '{filepath}' không đọc được: {e}")

    if header is None:
        raise ValidationError(f"File '{filepath}' rỗng.")

    missing = [c for c in required_cols if c not in header]
    if missing:
        raise ValidationError(f"File '{filepath}' thiếu các cột: {', '.join(missing)}")

    # Spec 2.0: tên cột phân biệt hoa/thường và phải đúng thứ tự mô tả
    if header != required_cols:
        raise ValidationError(
            f"File '{filepath}' có tiêu đề {header}, cần đúng thứ tự {required_cols}."
        )

    return {name: header.index(name) for name in required_cols}, len(header), rows


def read_and_validate_segments(filepath: str) -> pd.DataFrame:
    idx, n_cols, rows = _read_csv(filepath, SEGMENT_COLS)

    if not rows:
        raise ValidationError(f"File '{filepath}' chỉ có dòng tiêu đề, bảng segment rỗng.")

    errors: List[str] = []
    records = []
    seen_ids: Dict[int, int] = {}

    for line_no, fields in rows:
        if len(fields) != n_cols:
            errors.append(f"Dòng {line_no}: có {len(fields)} ô, cần {n_cols} ô.")
            continue

        seg_id = _parse_int(fields[idx["seg_id"]])
        base = _parse_int(fields[idx["base"]])
        limit = _parse_int(fields[idx["limit"]])
        perm = fields[idx["perm"]].strip().upper()

        row_ok = True
        if seg_id is None:
            errors.append(f"Dòng {line_no}: seg_id '{fields[idx['seg_id']]}' không phải số nguyên.")
            row_ok = False
        elif seg_id < 0:
            errors.append(f"Dòng {line_no}: seg_id phải >= 0 (nhận {seg_id}).")
            row_ok = False
        elif seg_id in seen_ids:
            errors.append(f"Dòng {line_no}: seg_id {seg_id} bị trùng với dòng {seen_ids[seg_id]}.")
            row_ok = False
        else:
            seen_ids[seg_id] = line_no

        if base is None:
            errors.append(f"Dòng {line_no}: base '{fields[idx['base']]}' không phải số nguyên.")
            row_ok = False
        elif base < 0:
            errors.append(f"Dòng {line_no}: base phải >= 0 (nhận {base}).")
            row_ok = False

        if limit is None:
            errors.append(f"Dòng {line_no}: limit '{fields[idx['limit']]}' không phải số nguyên.")
            row_ok = False
        elif limit <= 0:
            errors.append(f"Dòng {line_no}: limit phải > 0 (nhận {limit}).")
            row_ok = False

        if not PERM_PATTERN.match(perm):
            errors.append(f"Dòng {line_no}: perm '{perm}' sai định dạng (cần dạng như 'RW-', 'R-X', '---').")
            row_ok = False

        if row_ok:
            records.append({"seg_id": seg_id, "base": base, "limit": limit, "perm": perm})

    if errors:
        raise ValidationError(f"File '{filepath}' có {len(errors)} lỗi:\n  - " + "\n  - ".join(errors))

    return pd.DataFrame(records, columns=SEGMENT_COLS)


def read_and_validate_addresses(filepath: str) -> pd.DataFrame:
    idx, n_cols, rows = _read_csv(filepath, ADDRESS_COLS)

    records = []
    for line_no, fields in rows:
        rec = {"line": line_no, "seg_id": None, "offset": None, "access": None,
               "status": STATUS_OK, "error": ""}

        if len(fields) != n_cols:
            rec["status"] = STATUS_INVALID_INPUT
            rec["error"] = f"có {len(fields)} ô, cần {n_cols} ô"
            records.append(rec)
            continue

        raw_seg = fields[idx["seg_id"]]
        raw_off = fields[idx["offset"]]
        access = fields[idx["access"]].strip().upper()

        seg_id = _parse_int(raw_seg)
        offset = _parse_int(raw_off)
        rec["seg_id"], rec["offset"], rec["access"] = seg_id, offset, access

        problems = []
        if seg_id is None:
            problems.append(f"seg_id '{raw_seg}' không phải số nguyên")
        if offset is None:
            problems.append("offset để trống" if not raw_off.strip()
                            else f"offset '{raw_off}' không phải số nguyên")
        if access not in VALID_ACCESS:
            problems.append(f"access '{access}' không hợp lệ (chỉ nhận R, W, X)")

        if problems:
            rec["status"] = STATUS_INVALID_INPUT
            rec["error"] = "; ".join(problems)

        records.append(rec)

    df = pd.DataFrame(records, columns=["line", "seg_id", "offset", "access", "status", "error"])
    df["seg_id"] = df["seg_id"].astype("Int64")
    df["offset"] = df["offset"].astype("Int64")
    return df


def load_input_files(segments_path: str, addresses_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Đọc và validate cả 2 file CSV."""
    return read_and_validate_segments(segments_path), read_and_validate_addresses(addresses_path)


if __name__ == "__main__":
    seg_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join("input", "segments.csv")
    addr_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join("input", "addresses.csv")

    try:
        df_seg, df_addr = load_input_files(seg_file, addr_file)
    except (FileNotFoundError, ValidationError) as e:
        print(f"Lỗi: {e}")
        sys.exit(1)

    n_bad = int((df_addr["status"] == STATUS_INVALID_INPUT).sum())
    print("Validate dữ liệu thành công!")
    print(f"- Số segment: {len(df_seg)}")
    print(f"- Số địa chỉ cần dịch: {len(df_addr)} (INVALID_INPUT: {n_bad})")
    if df_addr.empty:
        print("Không có địa chỉ để dịch.")

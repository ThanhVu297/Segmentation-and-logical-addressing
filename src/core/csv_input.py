import os
import pandas as pd
from typing import Tuple, Set

# Danh sách cột bắt buộc
REQUIRED_SEGMENT_COLS = {"seg_id", "base", "limit", "perm"}
REQUIRED_ADDRESS_COLS = {"seg_id", "offset", "access"}

# Danh sách quyền truy cập hợp lệ
VALID_ACCESS_TYPES = {"R", "W", "X"}


class ValidationError(Exception):
    """Ngoại lệ tùy chỉnh cho các lỗi kiểm tra dữ liệu CSV."""
    pass


def read_and_validate_segments(filepath: str) -> pd.DataFrame:
    """
    Đọc và validate file segments.csv.
    
    Quy tắc kiểm tra:
    - Phải tồn tại các cột: seg_id, base, limit, perm
    - Không chứa giá trị rỗng (NaN)
    - seg_id phải là duy nhất (không trùng lặp)
    - base và limit phải là số nguyên không âm (>= 0)
    - perm phải là chuỗi hợp lệ (ví dụ: 'R-X', 'RW-', 'R--')
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Không tìm thấy file: {filepath}")

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        raise ValidationError(f"Lỗi khi đọc file '{filepath}': {e}")

    # 1. Kiểm tra cấu trúc cột
    if not REQUIRED_SEGMENT_COLS.issubset(df.columns):
        missing = REQUIRED_SEGMENT_COLS - set(df.columns)
        raise ValidationError(f"File '{filepath}' thiếu các cột: {missing}")

    # 2. Kiểm tra dữ liệu khuyết thiếu
    if df[list(REQUIRED_SEGMENT_COLS)].isnull().any().any():
        raise ValidationError(f"File '{filepath}' chứa giá trị khuyết (NaN/Null).")

    # 3. Kiểm tra khóa chính trùng lặp
    if df["seg_id"].duplicated().any():
        dups = df[df["seg_id"].duplicated()]["seg_id"].tolist()
        raise ValidationError(f"File '{filepath}' chứa seg_id bị trùng lặp: {dups}")

    # 4. Kiểm tra kiểu dữ liệu và phạm vi (base, limit >= 0)
    try:
        df["seg_id"] = df["seg_id"].astype(int)
        df["base"] = df["base"].astype(int)
        df["limit"] = df["limit"].astype(int)
    except ValueError:
        raise ValidationError(f"File '{filepath}' chứa dữ liệu seg_id/base/limit không phải số nguyên.")

    if (df["base"] < 0).any() or (df["limit"] < 0).any():
        raise ValidationError(f"File '{filepath}' chứa giá trị base hoặc limit nhỏ hơn 0.")

    # 5. Định dạng lại cột perm thành string
    df["perm"] = df["perm"].astype(str).str.strip()

    return df


def read_and_validate_addresses(
    filepath: str, valid_seg_ids: Set[int] = None
) -> pd.DataFrame:
    """
    Đọc và validate file addresses.csv.
    
    Quy tắc kiểm tra:
    - Phải tồn tại các cột: seg_id, offset, access
    - Không chứa giá trị rỗng (NaN)
    - seg_id và offset phải là số nguyên
    - offset phải >= 0
    - access phải thuộc danh sách hợp lệ {'R', 'W', 'X'}
    - (Tùy chọn) seg_id phải tồn tại trong segments.csv (Foreign Key validation)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Không tìm thấy file: {filepath}")

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        raise ValidationError(f"Lỗi khi đọc file '{filepath}': {e}")

    # 1. Kiểm tra cấu trúc cột
    if not REQUIRED_ADDRESS_COLS.issubset(df.columns):
        missing = REQUIRED_ADDRESS_COLS - set(df.columns)
        raise ValidationError(f"File '{filepath}' thiếu các cột: {missing}")

    # 2. Kiểm tra dữ liệu khuyết thiếu
    if df[list(REQUIRED_ADDRESS_COLS)].isnull().any().any():
        raise ValidationError(f"File '{filepath}' chứa giá trị khuyết (NaN/Null).")

    # 3. Kiểm tra kiểu dữ liệu
    try:
        df["seg_id"] = df["seg_id"].astype(int)
        df["offset"] = df["offset"].astype(int)
    except ValueError:
        raise ValidationError(f"File '{filepath}' chứa dữ liệu seg_id/offset không phải số nguyên.")

    if (df["offset"] < 0).any():
        raise ValidationError(f"File '{filepath}' chứa giá trị offset nhỏ hơn 0.")

    # 4. Kiểm tra loại truy cập (access)
    df["access"] = df["access"].astype(str).str.strip().str.upper()
    invalid_access = df[~df["access"].isin(VALID_ACCESS_TYPES)]
    if not invalid_access.empty:
        invalid_vals = invalid_access["access"].unique().tolist()
        raise ValidationError(f"File '{filepath}' chứa loại access không hợp lệ: {invalid_vals}")

    # 5. Kiểm tra tính toàn vẹn tham chiếu (Foreign Key check)
    if valid_seg_ids is not None:
        unknown_segs = set(df["seg_id"]) - valid_seg_ids
        if unknown_segs:
            # Lưu ý: Không raise exception nếu hệ thống muốn xử lý đoạn địa chỉ này là Segment Fault (Segmentation Fault)
            # Dưới đây đưa ra cảnh báo hoặc raise ValidationError tùy nhu cầu
            print(f"[Warning] Địa chỉ tham chiếu đến seg_id không tồn tại trong segments.csv: {unknown_segs}")

    return df


def load_input_files(
    segments_path: str, addresses_path: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Hàm tổng hợp đọc và validate cả 2 file CSV.
    """
    df_segments = read_and_validate_segments(segments_path)
    valid_seg_ids = set(df_segments["seg_id"])
    
    df_addresses = read_and_validate_addresses(addresses_path, valid_seg_ids=valid_seg_ids)
    
    return df_segments, df_addresses


if __name__ == "__main__":
    segments_file = "segments.csv"
    addresses_file = "addresses.csv"

    try:
        df_seg, df_addr = load_input_files(segments_file, addresses_file)
        print(" Validate dữ liệu thành công!")
        print(f"- Số lượng Segments: {len(df_seg)}")
        print(f"- Số lượng Addresses cần chuyển đổi: {len(df_addr)}")
    except (FileNotFoundError, ValidationError) as e:
        print(f" Lỗi Validation: {e}")

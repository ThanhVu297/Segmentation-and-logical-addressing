# Báo cáo tiến độ Tuần 6

TV3:
- Rà soát và hoàn thiện 100% mã nguồn các file phụ trách (`src/core/protection.py`, `src/core/oracle.py`, `src/tests/test_protection.py`).
- Kiểm chứng tích hợp với luồng dịch địa chỉ trên bộ dữ liệu chuẩn (`input/segments.csv` và `input/addresses.csv`), đảm bảo khớp 100% với `src/tests/expected/expected_trace.csv`.

TV5:
- Chạy stress test và đo hiệu năng bằng `benchmark.py` với 1.000 / 10.000 / 100.000 / 1.000.000 địa chỉ, đối chiếu từng kết quả với oracle độc lập: 0 sai lệch.
- Chạy kiểm thử tổng hợp toàn bộ unit test của nhóm bằng `unittest`.
- Sửa `test_benchmark.py` cho khớp `csv_input.py` mới (lỗi `limit = 0` và `perm` sai đã bị `csv_input.py` chặn từ lúc đọc file).

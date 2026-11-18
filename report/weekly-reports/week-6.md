# Báo cáo tiến độ Tuần 6

TV2:
- Xây dựng Pseudocode mô tả các bước thực hiện thuật toán dịch địa chỉ.
- Thiết kế Flowchart thể hiện luồng xử lý của chương trình.
- Xây dựng bài toán mẫu tính tay (Trace).
- Trình bày các bước kiểm tra địa chỉ, xác định Base và Offset, sau đó tính địa chỉ vật lý.
- Lưu tài liệu vào thư mục docs của dự án.
- Thực hiện cập nhật tài liệu lên GitHub thông qua branch riêng.

TV3:
- Rà soát và hoàn thiện 100% mã nguồn các file phụ trách (`src/core/protection.py`, `src/core/oracle.py`, `src/tests/test_protection.py`).
- Kiểm chứng tích hợp với luồng dịch địa chỉ trên bộ dữ liệu chuẩn (`input/segments.csv` và `input/addresses.csv`), đảm bảo khớp 100% với `src/tests/expected/expected_trace.csv`.

TV4:
- Rà soát các thành phần giao diện trong `src/gui/gui_panels.py` và `src/gui/gui.py`.
- Kiểm tra thủ công các chức năng giao diện theo danh sách kiểm tra (GUI Checklist).
- Kiểm tra thao tác mở tệp CSV, hiển thị bảng phân đoạn và nhập địa chỉ logic.
- Kiểm tra các nút chức năng Dịch địa chỉ, Bước tiếp và Xuất kết quả.
- Kiểm tra hộp thoại cảnh báo khi dữ liệu CSV không hợp lệ.
- Ghi nhận kết quả kiểm tra, phát hiện lỗi giao diện và đề xuất hướng khắc phục.

TV5:
- Chạy stress test và đo hiệu năng bằng `benchmark.py` với 1.000 / 10.000 / 100.000 / 1.000.000 địa chỉ, đối chiếu từng kết quả với oracle độc lập: 0 sai lệch.
- Chạy kiểm thử tổng hợp toàn bộ unit test của nhóm bằng `unittest`.
- Sửa `test_benchmark.py` cho khớp `csv_input.py` mới (lỗi `limit = 0` và `perm` sai đã bị `csv_input.py` chặn từ lúc đọc file).

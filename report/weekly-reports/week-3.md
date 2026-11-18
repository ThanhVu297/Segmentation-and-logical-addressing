# Báo cáo tiến độ Tuần 3
TV1:
- Điều chỉnh file `csv_input` để phù hợp với định dạng dữ liệu mà chương trình yêu cầu.
- Duyệt và điều chỉnh các pr của các thành viên

TV3:
- Hoàn thiện bản thật của hàm `check_fault()` trong `src/core/protection.py` kiểm tra tuần tự qua 3 tầng: `SEGMENT_FAULT` -> `OFFSET_OUT_OF_RANGE` -> `PROTECTION_FAULT` -> `OK`.
- Cập nhật mục quy ước thứ tự ưu tiên kiểm tra lỗi của TV3 vào tài liệu `README.md` của dự án.

TV5:
- Hiện thực `validate_table(table, mem_size)` trong `src/core/validator.py`: sắp xếp segment theo `base` và so sánh với các segment đứng sau để phát hiện chồng lấp (overlap), kiểm tra `base + limit` không vượt kích thước bộ nhớ vật lý (5000 byte).
- Xử lý các ca biên: hai segment chạm nhau tại biên (hợp lệ), segment vừa khít bộ nhớ (hợp lệ), segment lồng nhau, bảng rỗng.
- Bắt đầu viết unit test cho validator bằng `unittest` dựa trên bảng segment mẫu ở mục 2 của kế hoạch.

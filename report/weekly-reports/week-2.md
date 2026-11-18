# Báo cáo tiến độ Tuần 2
TV1:
- Chuẩn bị và viết các file CSV đầu vào cho dự án:`input/segments.csv`,`input/addresses.csv`,`input/edge_cases`,`input/eror_cases`.
- Xây dựng `src/core/csv_input.py` để đọc và kiểm tra định dạng `segments.csv`, `addresses.csv`.
- Báo lỗi rõ ràng với dữ liệu không hợp lệ; đánh dấu dòng lỗi trong `addresses.csv` là `INVALID_INPUT` và tiếp tục xử lý.
- Kiểm tra chồng lấp và giới hạn bộ nhớ thuộc phần `validator.py` của TV5.

TV2:
- Xây dựng chức năng chuyển đổi địa chỉ logic sang địa chỉ vật lý trong translator.py.
- Cài đặt hàm translate() và translate_many().
- Viết và chạy kiểm thử trong test_logic.py, các test đều PASSED.

TV3:
- Khởi tạo khung hàm `check_fault(table, seg_id, offset, access)` phiên bản stub trong `src/core/protection.py`.
- Định nghĩa cấu trúc trả về `FaultResult` nhận diện 3 nhóm lỗi cơ bản: `SEGMENT_FAULT`, `OFFSET_OUT_OF_RANGE`, và `PROTECTION_FAULT` để các module khác (`translator.py`, `app.py`) tích hợp sớm.

TV5:
- Thiết kế hàm `validate_table(table, mem_size)` trong `src/core/validator.py`: mỗi segment chiếm khoảng nửa mở `[base, base + limit)`, phát hiện hai segment chồng lấp (overlap) và segment vượt kích thước bộ nhớ vật lý (5000 byte).
- Xác định các ca kiểm thử cho validator: hai segment chồng lấp, hai segment chạm nhau tại biên (hợp lệ), segment vừa khít bộ nhớ, segment vượt bộ nhớ, bảng rỗng.
- Tạo bản stub cho `draw_memory_map(canvas, table, mem_size)` trong `src/gui/memory_map.py` và phác thảo cách vẽ bản đồ bộ nhớ bằng Canvas (mỗi segment là một khối, đánh dấu địa chỉ vừa dịch, cảnh báo khi fault).
- Lập kế hoạch đo hiệu năng trong `src/core/benchmark.py`: dịch 1.000 / 10.000 / 100.000 / 1.000.000 địa chỉ, đo thời gian bằng `perf_counter`, ghi kết quả vào bảng.

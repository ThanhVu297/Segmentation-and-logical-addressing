# Báo cáo tiến độ Tuần 2
TV1:
- Chuẩn bị và viết các file CSV đầu vào cho dự án:`input/segments.csv`,`input/addresses.csv`,`input/edge_cases`,`input/eror_cases`.
- Xây dựng `src/core/csv_input.py` để đọc và kiểm tra định dạng `segments.csv`, `addresses.csv`.
- Báo lỗi rõ ràng với dữ liệu không hợp lệ; đánh dấu dòng lỗi trong `addresses.csv` là `INVALID_INPUT` và tiếp tục xử lý.
- Kiểm tra chồng lấp và giới hạn bộ nhớ thuộc phần `validator.py` của TV5.

TV2:
- Nghiên cứu thuật toán dịch địa chỉ logic sang địa chỉ vật lý.
- Tìm hiểu các thành phần của bảng phân đoạn như Base, Limit và quyền truy cập.
- Bắt đầu xây dựng file src/core/translator.py.
- Xây dựng hàm translate(table, seg_id, offset, access) để thực hiện dịch địa chỉ.
- Xác định các trường hợp địa chỉ hợp lệ và không hợp lệ.

TV3:
- Khởi tạo khung hàm `check_fault(table, seg_id, offset, access)` phiên bản stub trong `src/core/protection.py`.
- Định nghĩa cấu trúc trả về `FaultResult` nhận diện 3 nhóm lỗi cơ bản: `SEGMENT_FAULT`, `OFFSET_OUT_OF_RANGE`, và `PROTECTION_FAULT` để các module khác (`translator.py`, `app.py`) tích hợp sớm.

TV4:
- Tiếp tục phát triển giao diện trong `src/gui/gui_panels.py` bằng Tkinter.
- Thiết kế bảng hiển thị thông tin phân đoạn (Segment Table).
- Xây dựng biểu mẫu nhập địa chỉ đơn lẻ trên GUI.
- Bố trí các trường nhập Segment ID, Offset và Access (R/W/X).
- Sắp xếp bố cục giao diện để thuận tiện cho việc nhập và hiển thị thông tin phân đoạn.

TV5:
- Thiết kế hàm `validate_table(table, mem_size)` trong `src/core/validator.py`: mỗi segment chiếm khoảng nửa mở `[base, base + limit)`, phát hiện hai segment chồng lấp (overlap) và segment vượt kích thước bộ nhớ vật lý (5000 byte).
- Xác định các ca kiểm thử cho validator: hai segment chồng lấp, hai segment chạm nhau tại biên (hợp lệ), segment vừa khít bộ nhớ, segment vượt bộ nhớ, bảng rỗng.
- Tạo bản stub cho `draw_memory_map(canvas, table, mem_size)` trong `src/gui/memory_map.py` và phác thảo cách vẽ bản đồ bộ nhớ bằng Canvas (mỗi segment là một khối, đánh dấu địa chỉ vừa dịch, cảnh báo khi fault).
- Lập kế hoạch đo hiệu năng trong `src/core/benchmark.py`: dịch 1.000 / 10.000 / 100.000 / 1.000.000 địa chỉ, đo thời gian bằng `perf_counter`, ghi kết quả vào bảng.

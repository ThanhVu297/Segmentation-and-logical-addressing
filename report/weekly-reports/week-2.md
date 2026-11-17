# Báo cáo tiến độ Tuần 2
TV1:
- Chuẩn bị và viết các file CSV đầu vào cho dự án:`input/segments.csv`,`input/addresses.csv`,`input/edge_cases`,`input/eror_cases`.
- Xây dựng `src/core/csv_input.py` để đọc và kiểm tra định dạng `segments.csv`, `addresses.csv`.
- Báo lỗi rõ ràng với dữ liệu không hợp lệ; đánh dấu dòng lỗi trong `addresses.csv` là `INVALID_INPUT` và tiếp tục xử lý.
- Kiểm tra chồng lấp và giới hạn bộ nhớ thuộc phần `validator.py` của TV5.

TV3:
- Khởi tạo khung hàm `check_fault(table, seg_id, offset, access)` phiên bản stub trong `src/core/protection.py`.
- Định nghĩa cấu trúc trả về `FaultResult` nhận diện 3 nhóm lỗi cơ bản: `SEGMENT_FAULT`, `OFFSET_OUT_OF_RANGE`, và `PROTECTION_FAULT` để các module khác (`translator.py`, `app.py`) tích hợp sớm.

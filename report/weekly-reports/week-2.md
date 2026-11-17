# Báo cáo tiến độ Tuần 2

TV3:
- Khởi tạo khung hàm `check_fault(table, seg_id, offset, access)` phiên bản stub trong `src/core/protection.py`.
- Định nghĩa cấu trúc trả về `FaultResult` nhận diện 3 nhóm lỗi cơ bản: `SEGMENT_FAULT`, `OFFSET_OUT_OF_RANGE`, và `PROTECTION_FAULT` để các module khác (`translator.py`, `app.py`) tích hợp sớm.

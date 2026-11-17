# Báo cáo tiến độ Tuần 5

TV3:
- Xây dựng bộ kiểm thử đơn vị tại `src/tests/test_protection.py` bằng thư viện `unittest` với tổng cộng 23 test cases (vượt chỉ tiêu 17 ca):
  - 15 test cases trong lớp `TestCheckFault` kiểm tra các thao tác R/W/X, biên `offset = 0`, `offset = limit - 1`, `offset = limit`, lỗi chồng chéo đa tầng và đối chiếu Oracle.
  - 8 test cases trong lớp `TestCheckPermission` kiểm tra phân quyền, chuỗi sai định dạng (`'RAB'`), giá trị `None` và đối chiếu Oracle.
- Phối hợp chuẩn hóa dữ liệu đối chiếu trong `src/tests/expected/`.
- Chạy kiểm thử tự động đạt 23/23 PASS (100%).

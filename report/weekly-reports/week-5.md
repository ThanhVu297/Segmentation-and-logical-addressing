# Báo cáo tiến độ Tuần 5
TV1:
- Tạo `src/main.py` làm điểm khởi chạy ứng dụng. Tệp này khởi tạo các thành phần cần thiết và mở giao diện GUI, giúp người dùng chạy chương trình từ một điểm thống nhất.
- Tích hợp `src/gui/app.py` với controller trong `src/core/app.py`: GUI tiếp nhận thao tác và dữ liệu từ người dùng, gọi controller để thực hiện luồng xử lý, sau đó hiển thị kết quả hoặc thông báo lỗi.

TV3:
- Xây dựng bộ kiểm thử đơn vị tại `src/tests/test_protection.py` bằng thư viện `unittest` với tổng cộng 23 test cases (vượt chỉ tiêu 17 ca):
  - 15 test cases trong lớp `TestCheckFault` kiểm tra các thao tác R/W/X, biên `offset = 0`, `offset = limit - 1`, `offset = limit`, lỗi chồng chéo đa tầng và đối chiếu Oracle.
  - 8 test cases trong lớp `TestCheckPermission` kiểm tra phân quyền, chuỗi sai định dạng (`'RAB'`), giá trị `None` và đối chiếu Oracle.
- Phối hợp chuẩn hóa dữ liệu đối chiếu trong `src/tests/expected/`.
- Chạy kiểm thử tự động đạt 23/23 PASS (100%).

TV5:
- Hoàn thành `benchmark.py`: đo thời gian dịch 1.000 / 10.000 / 100.000 / 1.000.000 địa chỉ và đối chiếu từng kết quả với oracle độc lập.
- Chạy stress test với `translate()` của TV2: 0 sai lệch ở cả 4 kích thước, thời gian tăng gần tuyến tính theo số địa chỉ.
- Nộp 44 unit test (`unittest`) cho `validator.py`, `memory_map.py`, `benchmark.py` vào `src/tests/`.
- Merge các module vào `main` qua pull request.

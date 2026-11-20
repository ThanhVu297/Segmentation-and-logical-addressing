# Báo cáo tiến độ Tuần 4
TV1:
- Tạo `src/core/app.py` làm controller điều phối luồng xử lý chính: nạp CSV → kiểm tra dữ liệu → dịch địa chỉ → tạo trace → xuất kết quả.
- Thiết kế module độc lập với GUI để giao diện và các bài kiểm thử có thể cùng gọi, giúp tách biệt phần xử lý nghiệp vụ khỏi phần hiển thị.

TV2:
- Tìm hiểu thư viện csv trong Python.
- Xây dựng file src/core/csv_output.py.
- Thiết kế chức năng ghi kết quả dịch địa chỉ vào file CSV.
- Bổ sung thông tin chi tiết về quá trình dịch địa chỉ vào file kết quả.
- Xác định đường dẫn lưu kết quả tại output/trace.csv.

TV3:
- Xây dựng module đối chiếu độc lập `src/core/oracle.py` với hai hàm `reference_check_fault()` và `reference_check_permission()`.
- Đảm bảo thuật toán Oracle không import từ `protection.py` nhằm phục vụ kiểm chứng chéo (Differential Testing).

TV4:
- Tiếp tục hoàn thiện giao diện người dùng trong `src/gui`.
- Xây dựng file `src/gui/gui.py`, tạo cửa sổ chính `MainWindow` cho chương trình.
- Thiết kế menu và bố cục cửa sổ chính, sắp xếp các khu vực chức năng.
- Kết nối các thành phần giao diện từ `gui_panels.py` vào cửa sổ chính.
- Tạo khu vực hiển thị bản đồ bộ nhớ (Memory Map), chuẩn bị tích hợp với module `memory_map.py` của TV5.
- Xây dựng các hàm xử lý sự kiện cho các nút chức năng.

TV5:
- Hoàn thiện `validator.py`: phát hiện segment chồng lấp, vượt bộ nhớ vật lý, sai khoảng và `perm` sai định dạng.
- Xây dựng `memory_map.py`: vẽ bản đồ bộ nhớ bằng Canvas, đánh dấu địa chỉ vừa dịch và cảnh báo khi có fault.
- Xây dựng bản đầu của `benchmark.py`: đo thời gian dịch 1.000 đến 1.000.000 địa chỉ và đối chiếu với oracle.

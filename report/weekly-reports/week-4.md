# Báo cáo tiến độ Tuần 4
TV1:
- Tạo `src/core/app.py` làm controller điều phối luồng xử lý chính: nạp CSV → kiểm tra dữ liệu → dịch địa chỉ → tạo trace → xuất kết quả.
- Thiết kế module độc lập với GUI để giao diện và các bài kiểm thử có thể cùng gọi, giúp tách biệt phần xử lý nghiệp vụ khỏi phần hiển thị.

TV3:
- Xây dựng module đối chiếu độc lập `src/core/oracle.py` với hai hàm `reference_check_fault()` và `reference_check_permission()`.
- Đảm bảo thuật toán Oracle không import từ `protection.py` nhằm phục vụ kiểm chứng chéo (Differential Testing).

TV5:
- Hoàn thiện `validator.py`: phát hiện segment chồng lấp, vượt bộ nhớ vật lý, sai khoảng và `perm` sai định dạng.
- Xây dựng `memory_map.py`: vẽ bản đồ bộ nhớ bằng Canvas, đánh dấu địa chỉ vừa dịch và cảnh báo khi có fault.
- Xây dựng bản đầu của `benchmark.py`: đo thời gian dịch 1.000 đến 1.000.000 địa chỉ và đối chiếu với oracle.

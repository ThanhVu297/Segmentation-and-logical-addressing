# OS_MEM_12 – Segmentation và địa chỉ logic
Ứng dụng mô phỏng cơ chế quản lý bộ nhớ phân đoạn (Segmentation), kiểm tra tính hợp lệ, phân quyền truy cập và ánh xạ địa chỉ logic sang địa chỉ vật lý trên giao diện đồ họa (GUI).
## Thành viên
- TV1 (nhóm trưởng):Vũ Duy Thành
- TV2: Phạm Uyên Trang
- TV3: Trần Tường Nguyên
- TV4: Trần Thị Ngọc Giàu
- TV5: Nguyễn Thanh Dũng

## Mô hình bài toán & Đặc tả dữ liệu

Tài liệu đặc tả chi tiết: https://docs.google.com/document/d/19Lc-90aaxNOjiAAXL8eQFG_M3rYb4pnTkkm4-1a4jMg/edit?usp=sharing

## Cấu trúc thư mục dự án: [DATA_SPEC.md](DATA_SPEC.md)

```text
  ├── report/         # Báo cáo đồ án
  ├── input/          # Dữ liệu mẫu (segments.csv, addresses.csv), edge_cases/ và error_cases/ 
  ├── output/         # Kết quả xuất ra (trace.csv và trace_steps.csv)
  └── src/
      ├── core/       # Thuật toán ánh xạ, đọc/ghi CSV, kiểm tra dữ liệu và oracle đối chiếu
      ├── gui/        # Giao diện người dùng (Tkinter)
      └── tests/      # Bộ kiểm thử đơn vị (Unit tests) và dữ liệu kỳ vọng
  ├── DATA_SPEC.md    # Đặc tả Dữ liệu & Thuật toán
  └── README.md
```

## Cài đặt và chạy

Yêu cầu hệ thống: 
- Git
- Python 3.10 trở lên(có sẵn thư viện tkinter).

Các bước chạy chương trình
1. Clone mã nguồn và cài đặt thư viện:

```bash
git clone https://github.com/ThanhVu297/Segmentation-and-logical-addressing.git
cd Segmentation-and-logical-addressing
python -m pip install pandas
```

2. Khởi chạy ứng dụng:
```bash
python src/main.py
```

3. Thao tác trên giao diện:
- Bước 1: Chọn file `input/segments.csv` và `input/addresses.csv.`

- Bước 2: Nhấn Dịch toàn bộ `addresses.csv` để thực hiện quá trình dịch địa chỉ.

- Bước 3: Quan sát Bảng kết quả tổng hợp (toàn bộ địa chỉ) và Bảng kết quả dịch địa chỉ(trace chi tiết của địa chỉ đang chọn).

- Bước 4: Nhấn `Xuất kết quả` để lưu dữ liệu ra `output/trace.csv` và `output/trace_steps.csv`.

## Chạy kiểm thử tự động (Unit Tests)

Hệ thống kiểm thử trong `src/tests/`
1. Kiểm tra cú pháp và chạy toàn bộ bộ test (khuyên dùng):

```bash
python -m compileall src
python -m unittest discover -s src/tests -t src -v
```

2.Chạy riêng từng nhóm kiểm thử (tùy chọn):

...


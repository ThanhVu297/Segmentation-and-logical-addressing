# Q1 — Mô hình hệ thống, giả định và dữ liệu I/O

**Tên dự án:** Mô phỏng Segmentation và địa chỉ hóa logic  
**Mã dự án:** OS_MEM_12  
**Tài liệu:** Báo cáo Q1

---

## 1. Mục tiêu và phạm vi

Dự án mô phỏng cơ chế phân đoạn bộ nhớ (`Segmentation`) và quá trình chuyển đổi địa chỉ logic thành địa chỉ vật lý. Chương trình đọc dữ liệu bảng phân đoạn và danh sách địa chỉ logic từ file CSV, kiểm tra tính hợp lệ, dịch địa chỉ, tạo trace và ghi kết quả ra file CSV.

Phạm vi của hệ thống bao gồm:

- Nạp và kiểm tra định dạng dữ liệu đầu vào.
- Kiểm tra chồng lấn và giới hạn bộ nhớ của các phân đoạn.
- Kiểm tra segment, offset và quyền truy cập.
- Tính địa chỉ vật lý theo công thức `physical = base + offset`.
- Ghi kết quả dịch địa chỉ và lý do lỗi ra `output/trace.csv`.
- Cung cấp giao diện Tkinter để người dùng tương tác và xem kết quả.

## 2. Mô hình hệ thống

Hệ thống được tổ chức theo kiến trúc tách biệt GUI và Core Logic:

```text
┌─────────────────────────────┐
│        Tkinter GUI          │
│  src/gui/app.py, gui.py     │
└──────────────┬──────────────┘
               │ gọi controller
               ▼
┌─────────────────────────────┐
│        Core app             │
│       src/core/app.py       │
└──────────────┬──────────────┘
               │ điều phối
   ┌───────────┼───────────────┐
   ▼           ▼               ▼
CSV Input   Validator       Translator
csv_input   validator        translator
   │           │               │
   └───────────┴───────┬───────┘
                       ▼
                 CSV Output
                 csv_output
```

### 2.1. Tầng giao diện

Các module trong `src/gui/` chịu trách nhiệm hiển thị và tương tác:

- `app.py`, `gui.py`, `gui_panels.py`: xây dựng cửa sổ, panel và sự kiện Tkinter.
- `memory_map.py`: hỗ trợ hiển thị bản đồ bộ nhớ.
- GUI không thực hiện thuật toán dịch địa chỉ trực tiếp mà gọi tầng Core.

### 2.2. Tầng Core

Các module chính trong `src/core/` gồm:

- `app.py`: controller điều phối luồng nạp CSV, validate, dịch địa chỉ và xuất kết quả.
- `csv_input.py`: đọc và validate định dạng hai file CSV.
- `validator.py`: kiểm tra chồng lấn, giới hạn bộ nhớ và các ràng buộc toàn bảng.
- `translator.py`: dịch địa chỉ logic và tạo trace từng bước.
- `protection.py`: kiểm tra quyền truy cập.
- `result_types.py`: định nghĩa các kiểu dữ liệu dùng chung.
- `csv_output.py`: ghi kết quả ra CSV.
- `oracle.py`, `benchmark.py`, `gen_workload.py`: hỗ trợ đối soát, sinh dữ liệu và đánh giá.

## 3. Giả định ban đầu

1. Bộ nhớ vật lý mặc định có kích thước `5000` byte; địa chỉ vật lý hợp lệ nằm trong khoảng `[0, 4999]`.
2. Mỗi segment chiếm vùng nửa mở `[base, base + limit)`.
3. Các segment không được chồng lấn; hai segment liền kề được phép.
4. Địa chỉ logic được biểu diễn bằng ba thành phần: `seg_id`, `offset` và `access`.
5. Công thức dịch địa chỉ là:

   ```text
   physical_address = base + offset
   ```

6. Offset hợp lệ phải thỏa mãn `0 <= offset < limit`.
7. `seg_id` của segment phải là số nguyên không âm và duy nhất trong bảng segment.
8. `base` không âm và `limit` phải lớn hơn 0.
9. `perm` gồm đúng 3 ký tự theo thứ tự `R`, `W`, `X`; ký tự không có quyền được biểu diễn bằng `-`. Ví dụ: `R-X`, `RW-`, `R--`.
10. `access` chỉ nhận `R`, `W` hoặc `X`, không phân biệt chữ hoa/thường.
11. File đầu vào mặc định dùng mã hóa UTF-8, có thể có BOM; dòng đầu là header.
12. Tên cột và thứ tự cột trong CSV phải đúng với đặc tả.
13. Khoảng trắng ở đầu/cuối ô dữ liệu được loại bỏ trước khi validate.
14. Dòng trống hoặc dòng có số ô khác số cột header được coi là dữ liệu không hợp lệ.
15. Kiểm tra định dạng thuộc `csv_input.py`; kiểm tra chồng lấn và vượt bộ nhớ thuộc `validator.py`.
16. Dòng sai trong `addresses.csv` không làm dừng toàn bộ chương trình mà được đánh dấu `INVALID_INPUT` và tiếp tục xử lý dòng sau.

## 4. Cấu trúc dữ liệu đầu vào

### 4.1. `input/segments.csv`

Header chính xác:

```csv
seg_id,base,limit,perm
```

| Cột | Kiểu dữ liệu | Quy tắc |
|---|---|---|
| `seg_id` | Số nguyên | Không âm, duy nhất trong file |
| `base` | Số nguyên | Không âm |
| `limit` | Số nguyên | Lớn hơn 0 |
| `perm` | Chuỗi | Đúng 3 ký tự theo dạng R/W/X hoặc `-` |

Ví dụ:

```csv
seg_id,base,limit,perm
0,1000,400,R-X
1,2000,1000,RW-
2,3500,500,R--
```

Điều kiện toàn bảng:

- Không trùng `seg_id`.
- Không có segment nào vượt quá giới hạn bộ nhớ `5000` byte.
- Các segment không chồng lấn.
- File không được rỗng và không chỉ có header.

### 4.2. `input/addresses.csv`

Header chính xác:

```csv
seg_id,offset,access
```

| Cột | Kiểu dữ liệu | Quy tắc |
|---|---|---|
| `seg_id` | Số nguyên | Phải tìm thấy trong bảng segment; lỗi định dạng là `INVALID_INPUT` |
| `offset` | Số nguyên | Không phải số hoặc để trống là `INVALID_INPUT`; số âm hoặc ngoài giới hạn được xử lý là lỗi dịch |
| `access` | Ký tự | Chấp nhận `R`, `W`, `X`, không phân biệt chữ hoa/thường |

Ví dụ:

```csv
seg_id,offset,access
0,100,R
1,500,W
2,499,R
```

## 5. Cấu trúc dữ liệu dùng chung

Các kiểu dữ liệu dùng chung nằm trong `src/core/result_types.py`:

- `Status`: liệt kê trạng thái dịch địa chỉ.
- `Segment`: biểu diễn một phân đoạn gồm `base`, `limit` và `perm`.
- `SegmentTable`: tập hợp các segment theo `seg_id`.
- `Step`: ghi một bước trong quá trình trace.
- `FaultResult`: lưu thông tin khi gặp lỗi.
- `TranslationResult`: lưu kết quả dịch địa chỉ, gồm segment, base, limit, địa chỉ vật lý, trạng thái và trace.

## 6. Trạng thái xử lý

Hệ thống sử dụng các trạng thái sau:

| Trạng thái | Ý nghĩa |
|---|---|
| `OK` | Dịch địa chỉ thành công |
| `SEGMENT_FAULT` | Không tìm thấy `seg_id` trong bảng segment |
| `OFFSET_OUT_OF_RANGE` | Offset âm hoặc lớn hơn hoặc bằng limit |
| `PROTECTION_FAULT` | Segment không cấp quyền truy cập yêu cầu |
| `INVALID_INPUT` | Dữ liệu đầu vào của dòng địa chỉ không hợp lệ |

Thứ tự kiểm tra dịch địa chỉ:

1. Kiểm tra `seg_id` và `offset` có đúng kiểu số và `access` hợp lệ.
2. Kiểm tra `seg_id` có tồn tại trong bảng segment.
3. Kiểm tra offset nằm trong giới hạn segment.
4. Kiểm tra quyền truy cập trong `perm`.
5. Nếu tất cả điều kiện hợp lệ, tính địa chỉ vật lý bằng `base + offset`.

## 7. Cấu trúc dữ liệu đầu ra

Kết quả được ghi trong `output/trace.csv` với header:

```csv
stt,seg_id,offset,access,base,limit,physical,status,reason
```

| Cột | Ý nghĩa |
|---|---|
| `stt` | Số thứ tự dòng địa chỉ |
| `seg_id` | Mã phân đoạn |
| `offset` | Địa chỉ tương đối |
| `access` | Quyền truy cập yêu cầu |
| `base` | Địa chỉ cơ sở của segment |
| `limit` | Giới hạn của segment |
| `physical` | Địa chỉ vật lý; để trống nếu không dịch thành công |
| `status` | Trạng thái kết quả |
| `reason` | Lý do chi tiết của trạng thái |

Ví dụ:

```csv
stt,seg_id,offset,access,base,limit,physical,status,reason
1,0,100,R,1000,400,1100,OK,
2,0,400,R,1000,400,,OFFSET_OUT_OF_RANGE,offset >= limit
3,2,10,W,3500,500,,PROTECTION_FAULT,access W not permitted
```

## 8. Chính sách xử lý lỗi

### 8.1. Lỗi ở `segments.csv`

File segment không hợp lệ sẽ bị từ chối nạp. Các trường hợp gồm:

- File rỗng hoặc chỉ có header.
- Thiếu cột hoặc sai thứ tự header.
- Số ô trong dòng không khớp header.
- Giá trị không phải số.
- `seg_id` âm hoặc trùng.
- `base` âm.
- `limit` nhỏ hơn hoặc bằng 0.
- `perm` sai độ dài hoặc ký tự.
- Segment vượt giới hạn bộ nhớ.
- Các segment chồng lấn nhau.

### 8.2. Lỗi ở `addresses.csv`

- File rỗng, thiếu cột hoặc header sai: từ chối nạp toàn bộ file.
- Dòng có `seg_id`, `offset` hoặc `access` sai định dạng: ghi `INVALID_INPUT`.
- `seg_id` hợp lệ nhưng không tồn tại: ghi `SEGMENT_FAULT`.
- Offset ngoài phạm vi: ghi `OFFSET_OUT_OF_RANGE`.
- Access không được segment cho phép: ghi `PROTECTION_FAULT`.
- Mỗi địa chỉ vẫn được xuất thành một dòng trace theo đúng thứ tự ban đầu.

## 9. Luồng xử lý chính

```text
Nạp segments.csv
       │
       ▼
Validate định dạng segment
       │
       ▼
Validate bảng segment, giới hạn bộ nhớ và chồng lấn
       │
       ▼
Nạp addresses.csv
       │
       ▼
Xử lý từng dòng địa chỉ
       │
       ├── Dữ liệu sai định dạng → INVALID_INPUT
       ├── Không có segment     → SEGMENT_FAULT
       ├── Offset ngoài limit    → OFFSET_OUT_OF_RANGE
       ├── Thiếu quyền           → PROTECTION_FAULT
       └── Hợp lệ                → physical = base + offset
       ▼
Tạo trace
       │
       ▼
Ghi output/trace.csv và trả kết quả cho GUI
```

## 10. Kiểm thử dữ liệu

Thư mục `src/tests/` chứa các unit test cho từng module. Đặc biệt, module `test_csv_input.py` kiểm tra tối thiểu các nhóm:

- Đọc file segment hợp lệ.
- File segment rỗng.
- Thiếu cột.
- Giá trị số không hợp lệ.
- Base âm hoặc limit bằng âm/0.
- Trùng `seg_id`.
- Permission sai định dạng.
- Dòng địa chỉ sai định dạng được đánh dấu `INVALID_INPUT`.

Các file dữ liệu mẫu, edge-case và error-case được đặt dưới `input/`. Các trace expected trong `src/tests/expected/` được dùng làm oracle để đối chiếu kết quả.

## 11. Kết luận

Báo cáo đã xác định mô hình ba tầng của hệ thống, các giả định về bộ nhớ và địa chỉ, cấu trúc dữ liệu đầu vào/đầu ra và chính sách xử lý lỗi. Việc tách Core Logic khỏi Tkinter GUI giúp từng thành phần có thể được kiểm thử độc lập, dễ bảo trì và thuận tiện khi thay đổi hoặc mở rộng giao diện.

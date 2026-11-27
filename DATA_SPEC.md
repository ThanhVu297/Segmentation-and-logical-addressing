# ĐẶC TẢ DỮ LIỆU & KIỂM THỬ – OS_MEM_12

**Tên dự án:** Mô phỏng Segmentation và Dịch địa chỉ logic

## 1. Bộ nhớ vật lý & giả định hệ thống

- Kích thước bộ nhớ mặc định: `5000` byte, địa chỉ vật lý hợp lệ từ `0` đến `4999`.
- Mỗi segment chiếm vùng nửa mở `[base, base + limit)`.
- Các segment không được chồng lấn; segment liền kề được phép.

## 2. Định dạng các file CSV

### 2.0. Quy tắc đọc và ghi file chung

- Mã hóa văn bản của CSV là **UTF-8-SIG** (UTF-8 có BOM ở đầu file khi ghi).
- Khi đọc, chương trình dùng `utf-8-sig`, nên chấp nhận cả file UTF-8 có BOM lẫn UTF-8 không có BOM.
- Khi xuất CSV (kết quả dịch và workload sinh tự động), chương trình ghi UTF-8-SIG để Excel nhận diện đúng tiếng Việt và ký tự Unicode.
- Dòng đầu là header, tên cột phân biệt hoa/thường và phải đúng thứ tự.
- Loại bỏ khoảng trắng ở đầu/cuối ô khi kiểm tra; bỏ qua dòng trống hoàn toàn.
- Dòng có số ô khác số cột header bị coi là sai định dạng.

### 2.1. `input/segments.csv` — Segment Table

Header chính xác: `seg_id,base,limit,perm`.

| Cột | Kiểu dữ liệu | Quy tắc |
|---|---|---|
| `seg_id` | Số nguyên | `>= 0`, duy nhất trong file. |
| `base` | Số nguyên | `>= 0`. |
| `limit` | Số nguyên | `> 0`. |
| `perm` | Chuỗi 3 ký tự | Chỉ nhận `R`, `W`, `X` viết hoa hoặc `-` đúng vị trí. Không nhận chữ thường. |

`perm` không được chuẩn hóa: `R-X`, `RW-`, `R--`, `---` hợp lệ; `r-x`, `rW-`, `Rw-` không hợp lệ. Segment chứa `perm` sai làm toàn bộ file bị từ chối.

Điều kiện toàn bảng: `base + limit <= 5000`, không trùng ID và không chồng lấn.

### 2.2. `input/addresses.csv` — Danh sách địa chỉ logic

Header chính xác: `seg_id,offset,access`.

| Cột | Kiểu dữ liệu | Quy tắc |
|---|---|---|
| `seg_id` | Số nguyên | Không phải số nguyên → `INVALID_INPUT`; số nguyên không có trong bảng → `SEGMENT_FAULT`. |
| `offset` | Số nguyên | Âm hoặc bằng/lớn hơn limit → `OFFSET_OUT_OF_RANGE`; không phải số hoặc để trống → `INVALID_INPUT`. |
| `access` | Ký tự | Chỉ chấp nhận `R`, `W`, `X` viết hoa. `r/w/x` và ký tự khác hoặc để trống → `INVALID_INPUT`; không chuẩn hóa. |

Từng dòng địa chỉ sai vẫn được giữ đúng thứ tự và đánh dấu `INVALID_INPUT`; các dòng còn lại tiếp tục xử lý.

### 2.3. Kết quả `output/trace.csv`

Header: `stt,seg_id,offset,access,base,limit,physical,status,reason`.

- Access hợp lệ được xuất nguyên giá trị `R`, `W` hoặc `X`.
- Không có bước chuyển đổi chữ thường sang chữ hoa.
- File kết quả được ghi bằng UTF-8-SIG để hỗ trợ Excel.

## 3. Chính sách xử lý dữ liệu sai

- Segment CSV không hợp lệ: từ chối toàn bộ file.
- Address CSV sai header hoặc không có dòng địa chỉ: từ chối nạp file.
- Dòng address sai access/seg_id/offset: đánh dấu `INVALID_INPUT` và tiếp tục.

## 4. Quyền truy cập

Chuỗi `perm` gồm 3 ký tự theo thứ tự R–W–X:

- `R-X`: cho phép đọc và thực thi.
- `RW-`: cho phép đọc và ghi.
- `R--`: chỉ cho phép đọc.
- `---`: không cấp quyền.

Chữ thường `r`, `w`, `x` không được phép ở `perm` và `access`.

## 5. Bộ dữ liệu kiểm thử

Các test cần bao phủ:

- `perm` viết hoa hợp lệ: `R-X`, `RW-`, `R--`, `---`.
- `perm` có chữ thường hoặc pha hoa như `r-x`, `rW-`, `Rw-` phải bị từ chối.
- `access` hợp lệ: `R`, `W`, `X`.
- `access` chữ thường: `r`, `w`, `x` phải trả `INVALID_INPUT`.
- Không tồn tại logic `.upper()` hoặc `.lower()` trong đường xử lý permission/access.
- CSV đầu ra được kiểm tra có BOM UTF-8-SIG; CSV đầu vào vẫn đọc được cả khi có hoặc không có BOM.

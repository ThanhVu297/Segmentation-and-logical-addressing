# ĐẶC TẢ DỮ LIỆU & KIỂM THỬ – OS_MEM_12
**Tên dự án:** Mô phỏng Segmentation và Dịch địa chỉ logic

---

## 1. Bộ nhớ vật lý & giả định hệ thống

- Kích thước bộ nhớ mặc định: `5000` byte, địa chỉ vật lý hợp lệ từ `0` đến `4999`.
- Mỗi segment chiếm vùng nửa mở `[base, base + limit)`, tương ứng các địa chỉ byte từ `base` đến `base + limit - 1`.
- Các segment không được chồng lấn; segment liền kề được phép.
- Dữ liệu chuẩn để chạy ứng dụng là `input/segments.csv` cùng `input/addresses.csv`.

---

## 2. Định dạng các file CSV

### 2.0. Quy tắc đọc file chung

- Mã hóa UTF-8 (có thể có BOM). Dòng đầu là header, tên cột phân biệt hoa/thường và phải đúng thứ tự.
- Loại bỏ khoảng trắng ở đầu/cuối ô khi kiểm tra; bỏ qua dòng trống hoàn toàn.
- Dòng có số ô khác số cột header bị coi là sai định dạng.

### 2.1. `input/segments.csv` — Segment Table

Header chính xác: `seg_id,base,limit,perm`.

| Cột | Kiểu dữ liệu | Quy tắc |
|---|---|---|
| `seg_id` | Số nguyên | `>= 0`, duy nhất trong file. |
| `base` | Số nguyên | `>= 0`. |
| `limit` | Số nguyên | `> 0`. |
| `perm` | Chuỗi 3 ký tự | Vị trí 1 là `R` hoặc `-`, vị trí 2 là `W` hoặc `-`, vị trí 3 là `X` hoặc `-`. |

`csv_input.py` chuẩn hóa `perm` thành chữ hoa trước khi kiểm tra và trả về DataFrame. Vì vậy `r-x`, `rW-` được chấp nhận và chuẩn hóa lần lượt thành `R-X`, `RW-`. Các ký tự vẫn phải đúng vị trí sau chuẩn hóa.

Điều kiện toàn bảng: `base + limit <= 5000`, không trùng ID và không chồng lấn. File rỗng hoặc chỉ có header bị từ chối.

### 2.2. `input/addresses.csv` — Danh sách địa chỉ logic

Header chính xác: `seg_id,offset,access`.

| Cột | Kiểu dữ liệu | Quy tắc |
|---|---|---|
| `seg_id` | Số nguyên | Không phải số nguyên → `INVALID_INPUT`; số nguyên không có trong bảng → `SEGMENT_FAULT`. |
| `offset` | Số nguyên | Có thể âm hoặc lớn hơn/ bằng limit; các giá trị này được dịch thành `OFFSET_OUT_OF_RANGE`. Không phải số hoặc để trống → `INVALID_INPUT`. |
| `access` | Ký tự | Chấp nhận `R`, `W`, `X`, không phân biệt hoa/thường. `r/w/x` được chuẩn hóa thành `R/W/X`; ký tự khác hoặc để trống → `INVALID_INPUT`. |

Từng dòng địa chỉ không hợp lệ vẫn được giữ đúng thứ tự và đánh dấu `INVALID_INPUT`; các dòng còn lại tiếp tục xử lý. Theo hành vi hiện tại của `csv_input.py`, file địa chỉ rỗng hoàn toàn hoặc chỉ có header bị từ chối vì không có dòng địa chỉ để xử lý.

### 2.3. Kết quả `output/trace.csv`

Header: `seg_id,offset,access,base,limit,physical,status,reason`.

- Mỗi địa chỉ đầu vào tạo một dòng kết quả theo đúng thứ tự.
- `base`, `limit` để trống nếu segment không tồn tại hoặc địa chỉ `INVALID_INPUT`.
- `physical` để trống nếu trạng thái khác `OK`.
- Access hợp lệ được xuất theo ký tự chuẩn hóa chữ hoa.

### 2.4. Kết quả `output/trace_steps.csv`

Header: `address_position,seg_id,offset,access,base,limit,physical,status,reason,step,step_description,step_passed`.
Mỗi bước dịch được ghi thành một dòng; địa chỉ `INVALID_INPUT` không đi qua các bước dịch.

---

## 3. Kiểu dữ liệu dùng chung

Các kiểu dùng chung nằm trong `src/core/result_types.py`: `Status`, `Step`, `FaultResult`, `TranslationResult`, `Segment`, `SegmentTable`.

---

## 4. Thứ tự dịch và trạng thái

Với một địa chỉ có định dạng hợp lệ, kiểm tra theo thứ tự:

1. Không tìm thấy `seg_id` → `SEGMENT_FAULT`.
2. `offset < 0` hoặc `offset >= limit` → `OFFSET_OUT_OF_RANGE`.
3. Quyền không được cấp trong `perm` → `PROTECTION_FAULT`.
4. Nếu qua cả ba bước → `OK`, `physical = base + offset`.

| Trạng thái | Ý nghĩa |
|---|---|
| `OK` | Dịch thành công. |
| `SEGMENT_FAULT` | Segment không tồn tại. |
| `OFFSET_OUT_OF_RANGE` | Offset nằm ngoài segment. |
| `PROTECTION_FAULT` | Segment không cấp quyền truy cập yêu cầu. |
| `INVALID_INPUT` | Dòng địa chỉ sai định dạng hoặc có trường không hợp lệ. |

---

## 5. Chính sách xử lý dữ liệu sai

- Segment CSV không hợp lệ: từ chối nạp toàn bộ file và báo lỗi kèm dòng/lý do.
- Address CSV không có header đúng hoặc không có dòng địa chỉ: từ chối nạp file.
- Dòng địa chỉ riêng lẻ sai định dạng: đánh dấu `INVALID_INPUT`, giữ nguyên vị trí và tiếp tục xử lý các dòng khác.

---

## 6. Bộ dữ liệu và các trường hợp kiểm thử

```text
input/
├── segments.csv                         # Input chuẩn, hợp lệ
├── addresses.csv                        # Input chuẩn; 18 địa chỉ
├── edge_cases/
│   ├── segments_adjacent.csv            # Hai segment liền kề
│   ├── segments_memory_boundary.csv     # Segment kết thúc đúng ở byte 4999
│   ├── addresses_memory_boundary.csv   # Offset biên, quyền, access chữ thường
│   ├── segments_case_normalization.csv  # perm thường/pha hoa
│   ├── addresses_case_normalization.csv # Access thường, biên và lỗi dòng
│   ├── segments_permissions_mixed.csv   # R/W/X permission pha hoa/thường
│   └── addresses_permissions_mixed.csv  # Kiểm tra từng quyền và các lỗi dịch
└── error_cases/                         # CSV cố ý sai để chạy kiểm tra lỗi
```

`input/segments.csv` chuẩn có 3 segment hợp lệ. `input/addresses.csv` giữ 18 dòng, bao phủ: dịch thành công, offset bằng 0/limit/âm, quyền bị từ chối, segment không tồn tại và access chữ thường. Access chữ thường được chuẩn hóa trước khi dịch. Expected trace chuẩn nằm ở `src/tests/expected/expected_trace.csv`.

### 6.1. Các bộ edge-case

| Cặp file | Nội dung cần kiểm tra |
|---|---|
| `segments_adjacent.csv` (nạp riêng) | Hai segment liền nhau hợp lệ, không bị coi là overlap. |
| `segments_memory_boundary.csv` + `addresses_memory_boundary.csv` | Segment `[4600,5000)` kết thúc tại byte `4999`; kiểm tra offset `0`, `399`, `400`, `-1`, quyền và access thường. |
| `segments_case_normalization.csv` + `addresses_case_normalization.csv` | `perm` chữ thường/pha hoa và access `r/w/x`; gồm `OK`, `OFFSET_OUT_OF_RANGE`, `PROTECTION_FAULT`, `SEGMENT_FAULT`, `INVALID_INPUT`. |
| `segments_permissions_mixed.csv` + `addresses_permissions_mixed.csv` | Thử từng quyền R/W/X viết hoa và thường trên các permission khác nhau. |

### 6.2. Segment CSV lỗi (`input/error_cases/`)

Các file segment lỗi phải bị từ chối khi nạp. Bộ file hiện có gồm: `segments_empty.csv`, `segments_missing_column.csv`, `segments_invalid_number.csv`, `segments_zero_limit.csv`, `segments_negative_base.csv`, `segments_negative_limit.csv`, `segments_duplicate_id.csv`, `segments_overlap.csv`, `segments_exceeds_memory.csv`, `segments_exceeds_memory_by_one.csv`, `segments_invalid_perm_length.csv`, `segments_invalid_perm_chars.csv`.

`segments_perm_lowercase_invalid.csv` được giữ làm ca kiểm tra permission sai độ dài: nội dung có bốn ký tự (`r-xz`), nên bị từ chối vì độ dài/ký tự không hợp lệ. Permission chỉ khác hoa/thường nhưng đúng mẫu, ví dụ `r-x`, là hợp lệ theo bộ đọc hiện tại.

### 6.3. Address CSV lỗi (`input/error_cases/`)

- `addresses_invalid_access.csv`: có access hợp lệ `R`, access sai `Z`, và access thường `r` hợp lệ.
- `addresses_access_variants.csv`: kiểm tra `R/r`, `W/w`, `X/x`, access không hợp lệ, access nhiều ký tự và access để trống; dòng sai được đánh dấu `INVALID_INPUT`.
- `addresses_invalid_offset.csv`: offset không phải số hoặc để trống; các dòng đó là `INVALID_INPUT`.
- `addresses_boundary_invalid.csv`: kết hợp offset biên/âm/vượt limit, access thường, segment không tồn tại, offset sai và offset trống.
- `addresses_missing_column.csv`: thiếu cột, toàn file bị từ chối.
- `addresses_empty.csv`: file rỗng, bị từ chối.

### 6.4. Đáp án chuẩn

Các trace expected hiện có trong `src/tests/expected/` là oracle cho các bộ dữ liệu tương ứng, gồm `expected_trace.csv` và `expected_trace_memory_boundary.csv` cùng các trace kiểm thử đã có. Với các cặp edge-case mới chưa có trace oracle riêng, cần kiểm tra trực tiếp status/physical theo quy tắc ở Mục 4.

---

## 7. Quy tắc validate `segments.csv` tóm tắt

Từ chối bảng segment nếu file không đọc được/không có dữ liệu, header sai, số ô sai, trường số không hợp lệ, `seg_id < 0` hoặc trùng, `base < 0`, `limit <= 0`, permission sai mẫu sau chuẩn hóa, segment vượt `base + limit <= 5000`, hoặc có segment chồng lấn.

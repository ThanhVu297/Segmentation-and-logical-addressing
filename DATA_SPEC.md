# ĐẶC TẢ DỮ LIỆU & KIỂM THỬ – OS_MEM_12
**Tên dự án:** Mô phỏng Segmentation và Dịch địa chỉ logic

---

## 1. Bộ nhớ vật lý & Giả định hệ thống
* **Kích thước bộ nhớ mặc định:** `5000` byte (địa chỉ vật lý hợp lệ từ `0` đến `4999`).
* **Không gian phân đoạn:** Mỗi segment chiếm một vùng nhớ liên tục `[base, base + limit - 1]`.
* **Tính tái lập:** Để tái lập kết quả, sử dụng đúng cặp CSV đầu vào cùng phiên bản đặc tả này.

---

## 2. Định dạng các file dữ liệu (CSV)

### 2.0. Quy tắc đọc file chung
* Mã hóa **UTF-8**. Dòng đầu tiên là dòng tiêu đề (tên cột), phân biệt chữ hoa/thường và phải đúng thứ tự.
* Tiêu đề phải khớp chính xác danh sách cột, không thừa hoặc thiếu cột.
* Tự động loại bỏ khoảng trắng ở đầu/cuối mỗi ô trước khi kiểm tra; bỏ qua các dòng trống.
* Dòng có số ô khác số cột tiêu đề bị coi là sai định dạng.

### 2.1. File `input/segments.csv` (Segment Table)
Cấu trúc cột: `seg_id,base,limit,perm`

| Cột | Kiểu dữ liệu | Ràng buộc dữ liệu |
| :--- | :--- | :--- |
| `seg_id` | Số nguyên `>= 0` | Định danh phân đoạn, duy nhất trong file. |
| `base` | Số nguyên `>= 0` | Địa chỉ vật lý bắt đầu của segment. |
| `limit` | Số nguyên `> 0` | Kích thước segment (byte). |
| `perm` | Chuỗi 3 ký tự | Vị trí 1: `R` hoặc `-`; Vị trí 2: `W` hoặc `-`; Vị trí 3: `X` hoặc `-`. |

* **Ràng buộc toàn bảng:**
  * Mỗi segment thỏa mãn `base + limit <= 5000`.
  * Các segment không được chồng lấn nhau (overlap). Hai segment liền kề nhau (Segment A kết thúc tại `base + limit - 1`, Segment B bắt đầu tại `base + limit`) là **hợp lệ**.

### 2.2. File `input/addresses.csv` (Danh sách địa chỉ logic)
Cấu trúc cột: `seg_id,offset,access`

| Cột | Kiểu dữ liệu | Ràng buộc dữ liệu |
| :--- | :--- | :--- |
| `seg_id` | Số nguyên | Không phải số nguyên $\rightarrow$ `INVALID_INPUT`. Là số nguyên nhưng không có trong bảng $\rightarrow$ `SEGMENT_FAULT`. |
| `offset` | Số nguyên | Có thể âm hoặc vượt `limit` (xử lý ở bước dịch: `OFFSET_OUT_OF_RANGE`). Không phải số hoặc để trống $\rightarrow$ `INVALID_INPUT`. |
| `access` | Ký tự | Nhận một trong ba ký tự R, W, X, không phân biệt chữ hoa/chữ thường. Trước khi kiểm tra quyền, chương trình chuẩn hóa giá trị thành chữ hoa (r → R, w → W, x → X). Ký tự khác $\rightarrow$ `INVALID_INPUT`. |

* **Trường hợp file chỉ có dòng tiêu đề (0 dòng dữ liệu):**
  * `segments.csv`: Bị từ chối (bảng segment rỗng).
  * `addresses.csv`: Hợp lệ; xuất `trace.csv` chỉ có tiêu đề và hiển thị thông báo `"Không có địa chỉ để dịch"`.

### 2.3. File `output/trace.csv` (Kết quả tổng hợp)
Cấu trúc cột: `seg_id,offset,access,base,limit,physical,status,reason`

* Xuất đúng 1 dòng cho mỗi địa chỉ trong `addresses.csv` theo đúng thứ tự.
* Để trống `base`, `limit` nếu `seg_id` không tồn tại hoặc dòng lỗi `INVALID_INPUT`.
* Để trống `physical` nếu `status` khác `OK`.
* Dòng `INVALID_INPUT` giữ nguyên chuỗi gốc ở 3 cột `seg_id`, `offset`, `access`.
* Cột `reason` để trống khi `OK`; khi lỗi ghi lý do ngắn gọn, **tuyệt đối không chứa dấu phẩy (`,`)**.
* *Ví dụ OK:* `0,100,R,1000,400,1100,OK,`
* *Ví dụ lỗi:* `0,400,R,1000,400,,OFFSET_OUT_OF_RANGE,Offset vuot qua limit`

### 2.4. File `output/trace_steps.csv` (Truy vết chi tiết từng bước)
Cấu trúc cột: `result_no,seg_id,offset,access,base,limit,physical,status,reason,step_no,step_description,step_ok`

* Lưu chi tiết từng bước kiểm tra thuật toán (mỗi bước một dòng); các trường tổng hợp được lặp lại để tiện lọc/đối chiếu.
* Địa chỉ bị `INVALID_INPUT` (không đi qua các bước thuật toán) vẫn xuất 1 dòng với các trường bước (`step_no`, `step_description`, `step_ok`) để trống.

---

## 3. Kiểu dữ liệu dùng chung

Nằm trong `src/core/result_types.py`, **chỉ TV1 được sửa**. Mọi người chỉ import, không tự định nghĩa lại:

    from core.result_types import Status, TranslationResult, FaultResult, Segment, SegmentTable

Gồm: `Status` (5 trạng thái), `Step`, `FaultResult`, `TranslationResult`, `Segment`, `SegmentTable`.

Muốn thêm hoặc đổi gì, nhắn TV1. Mỗi lần file này đổi sẽ có thông báo trong nhóm chat, mọi người `git pull` về rồi mới code tiếp.

## 4. Thứ tự kiểm tra lỗi & Danh sách mã trạng thái

Hệ thống kiểm tra theo **thứ tự ưu tiên cố định 4 bước** và dừng ngay khi gặp lỗi đầu tiên:

1. **Bước 1 – Segment:** `seg_id` không có trong Segment Table $\rightarrow$ `SEGMENT_FAULT`.
2. **Bước 2 – Offset:** `offset < 0` hoặc `offset >= limit` $\rightarrow$ `OFFSET_OUT_OF_RANGE`.
3. **Bước 3 – Quyền truy cập:** `R` khớp `perm[0]`, `W` khớp `perm[1]`, `X` khớp `perm[2]`. Không thỏa $\rightarrow$ `PROTECTION_FAULT`.
4. **Bước 4 – Thành công:** Vượt qua cả 3 bước $\rightarrow$ `OK`, tính $\text{physical} = \text{base} + \text{offset}$[cite: 8].

| Mã trạng thái (`status`) | Ý nghĩa |
| :--- | :--- |
| **`OK`** | Dịch địa chỉ thành công[cite: 8]. |
| **`SEGMENT_FAULT`** | `seg_id` không tồn tại trong bảng phân đoạn[cite: 8]. |
| **`OFFSET_OUT_OF_RANGE`** | `offset < 0` hoặc `offset >= limit`[cite: 8]. |
| **`PROTECTION_FAULT`** | `access` không khớp quyền `perm` của segment[cite: 8]. |
| **`INVALID_INPUT`** | Dòng trong `addresses.csv` sai định dạng (kiểu dữ liệu, ký tự quyền, thừa/thiếu ô...)[cite: 8]. |

---

## 5. Chính sách xử lý dữ liệu sai (Error Handling)

| Tình huống lỗi | Cách xử lý của ứng dụng |
| :--- | :--- |
| `segments.csv` vi phạm quy tắc validate (Mục 6) | Từ chối nạp toàn bộ file, báo lỗi kèm số dòng và lý do. Không thực hiện dịch[cite: 8]. |
| `addresses.csv` rỗng hoàn toàn hoặc sai/thiếu tiêu đề | Từ chối nạp toàn bộ file và hiển thị thông báo lỗi[cite: 8]. |
| Một dòng trong `addresses.csv` sai định dạng | Đánh dấu dòng đó là `INVALID_INPUT`, giữ nguyên vị trí và tiếp tục dịch các dòng sau[cite: 8]. |

---

## 6. Tổ chức dữ liệu kiểm thử & Oracle đối chiếu

```text
input/
├── segments.csv        # Dữ liệu phân đoạn chuẩn
├── addresses.csv       # 18 địa chỉ phủ đầy đủ các trạng thái status
├── edge_cases/         # Dữ liệu hợp lệ nằm ở khu vực biên bộ nhớ
└── error_cases/        # Dữ liệu lỗi, dùng kiểm thử chức năng bắt lỗi

src/tests/expected/     # Bộ đáp án chuẩn (Oracle), tính tay độc lập
├── expected_trace.csv
├── expected_trace_invalid_access.csv
├── expected_trace_invalid_offset.csv
├── expected_trace_invalid_seg_id.csv
├── expected_trace_negative_offset.csv
└── expected_trace_memory_boundary.csv
```

### 6.1. Kết quả mong đợi cho bộ dữ liệu chuẩn (`input/segments.csv` + `input/addresses.csv`)
Đối chiếu với `src/tests/expected/expected_trace.csv` (tổng 18 dòng)[cite: 8]:
* **8** dòng `OK`[cite: 8]
* **5** dòng `OFFSET_OUT_OF_RANGE`[cite: 8]
* **3** dòng `PROTECTION_FAULT`[cite: 8]
* **2** dòng `SEGMENT_FAULT`[cite: 8]
* **0** dòng `INVALID_INPUT`[cite: 8]

### 6.2. Test Cases biên (`input/edge_cases/`)

| File Test Case | Chạy kèm với | Kết quả mong đợi |
| :--- | :--- | :--- |
| `segments_adjacent.csv` | *(Chỉ nạp bảng)* | Hợp lệ: hai segment liền kề (`1000–1399` và `1400–1799`)[cite: 8]. |
| `segments_memory_boundary.csv` | `addresses_memory_boundary.csv` | Hợp lệ: segment kết thúc đúng tại byte `4999`. Khớp `expected_trace_memory_boundary.csv`[cite: 8]. |

### 6.3. Test Cases lỗi cho `segments.csv` (`input/error_cases/`)
Tất cả các trường hợp dưới đây đều phải **từ chối nạp file** và hiển thị thông báo lỗi chi tiết[cite: 8]:

| File Test Case | Mô tả lỗi | Kết quả mong đợi |
| :--- | :--- | :--- |
| `segments_empty.csv` | File rỗng[cite: 8] | Từ chối file[cite: 8] |
| `segments_missing_column.csv` | Thiếu cột `limit`[cite: 8] | Từ chối file[cite: 8] |
| `segments_invalid_number.csv` | `limit = abc`[cite: 8] | Từ chối file[cite: 8] |
| `segments_zero_limit.csv` | `limit = 0`[cite: 8] | Từ chối file[cite: 8] |
| `segments_negative_base.csv` | `base = -100`[cite: 8] | Từ chối file[cite: 8] |
| `segments_negative_limit.csv` | `limit = -400`[cite: 8] | Từ chối file[cite: 8] |
| `segments_duplicate_id.csv` | Trùng `seg_id = 0`[cite: 8] | Từ chối file[cite: 8] |
| `segments_overlap.csv` | Segment 0 (`1000–1399`) chồng lấn Segment 1 (`1300–1699`)[cite: 8] | Từ chối file[cite: 8] |
| `segments_exceeds_memory.csv` | Segment 1 kết thúc ở byte `5199` (`> 4999`)[cite: 8] | Từ chối file[cite: 8] |
| `segments_exceeds_memory_by_one.csv` | `base + limit = 5001` (vượt đúng 1 byte)[cite: 8] | Từ chối file[cite: 8] |
| `segments_invalid_perm_length.csv` | `perm = RW` (thiếu độ dài)[cite: 8] | Từ chối file[cite: 8] |
| `segments_invalid_perm_chars.csv` | `perm = ABC`[cite: 8] | Từ chối file[cite: 8] |

### 6.4. Test Cases lỗi cho `addresses.csv` (`input/error_cases/`)
*(Chạy trên nền `input/segments.csv` chuẩn)*[cite: 8]

| File Test Case | Mô tả lỗi / Trường hợp kiểm thử | Kết quả mong đợi |
| :--- | :--- | :--- |
| `addresses_empty.csv` | File rỗng[cite: 8] | Từ chối file[cite: 8] |
| `addresses_missing_column.csv` | Thiếu cột `access`[cite: 8] | Từ chối file[cite: 8] |
| `addresses_invalid_access.csv` | `access = Z` (sai ký tự) và `access = r` (chữ thường hợp lệ)[cite: 8] | Dòng chứa `Z` ghi `INVALID_INPUT`; dòng chứa `r` được chuẩn hóa thành `R` và dịch `OK`. Khớp `expected_trace_invalid_access.csv`. |
| `addresses_invalid_offset.csv` | `offset = abc` hoặc để trống[cite: 8] | Dòng 1, 3 ghi `INVALID_INPUT`, dòng 2 ghi `OK`. Khớp `expected_trace_invalid_offset.csv`[cite: 8]. |
| `addresses_invalid_seg_id.csv` | `seg_id = abc`[cite: 8] | Dòng đó ghi `INVALID_INPUT`, các dòng khác dịch bình thường. Khớp `expected_trace_invalid_seg_id.csv`[cite: 8]. |
| `addresses_negative_offset.csv` | `offset = -5` (hợp lệ về cấu trúc)[cite: 8] | Ghi `OFFSET_OUT_OF_RANGE`, không phải `INVALID_INPUT`. Khớp `expected_trace_negative_offset.csv`[cite: 8]. |

---

## 7. Tổng hợp quy tắc Validate bảng `segments.csv`
File `segments.csv` bị từ chối ngay lập tức nếu vi phạm một trong các điều kiện[cite: 8]:
1. File rỗng, không có dòng dữ liệu, hoặc thiếu tiêu đề cột[cite: 8].
2. `base`, `limit`, `seg_id` không phải số nguyên[cite: 8].
3. `base < 0`[cite: 8].
4. `limit <= 0`[cite: 8].
5. Trùng `seg_id`[cite: 8].
6. `perm` sai quy chuẩn (khác 3 ký tự hoặc chứa ký tự khác `R`, `W`, `X`, `-`, hoặc sai vị trí)[cite: 8].
7. Vượt bộ nhớ vật lý (`base + limit > 5000`)[cite: 8].
8. Có từ 2 segment trở lên chồng lấn nhau[cite: 8].

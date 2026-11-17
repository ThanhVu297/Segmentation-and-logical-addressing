# OS_MEM_12 – Segmentation và địa chỉ logic
## Thành viên
- TV1 (nhóm trưởng):Vũ Duy Thành
- TV2: Phạm Uyên Trang
- TV3: Trần Tường Nguyên
- TV4: Trần Thị Ngọc Giàu
- TV5: Nguyễn Thanh Dũng

## Kiểu dữ liệu dùng chung

Nằm trong `src/core/result_types.py`, **chỉ TV1 được sửa**. Mọi người chỉ import, không tự định nghĩa lại:

    from core.result_types import Status, TranslationResult, FaultResult, Segment, SegmentTable

Gồm: `Status` (5 trạng thái), `Step`, `FaultResult`, `TranslationResult`, `Segment`, `SegmentTable`.

Muốn thêm hoặc đổi gì, nhắn TV1. Mỗi lần file này đổi sẽ có thông báo trong nhóm chat, mọi người `git pull` về rồi mới code tiếp.

## Cài đặt và chạy

Yêu cầu: Git và Python 3.10 trở lên. Ứng dụng sử dụng Tkinter để hiển thị giao diện.

```bash
git clone https://github.com/ThanhVu297/Segmentation-and-logical-addressing.git
cd Segmentation-and-logical-addressing
python -m pip install -r requirements.txt
python src/main.py
```

Chọn `input/segments.csv` và `input/addresses.csv`, sau đó chọn **Dịch toàn bộ addresses.csv** để xử lý danh sách. Bảng **Kết quả tổng hợp** hiển thị kết quả của toàn bộ địa chỉ; bảng từng bước dùng để xem trace của địa chỉ hiện tại. Chọn **Xuất kết quả** để tạo `output/trace.csv` và `output/trace_steps.csv` (hoặc các tên file tương ứng đã chọn).

### TV3: module `protection.py` và unit test

`src/core/protection.py` kiểm tra địa chỉ theo thứ tự ưu tiên cố định và trả về lỗi đầu tiên gặp phải:

1. **`SEGMENT_FAULT`** — `seg_id` không tồn tại trong segment table. Khi segment không tồn tại, không tiếp tục kiểm tra offset hoặc quyền.
2. **`OFFSET_OUT_OF_RANGE`** — segment tồn tại nhưng `offset < 0` hoặc `offset >= limit`. Offset bằng `limit` cũng nằm ngoài phạm vi. Lỗi này được ưu tiên hơn lỗi quyền truy cập.
3. **`PROTECTION_FAULT`** — segment tồn tại, offset hợp lệ nhưng quyền không cho phép thao tác. Quyền sai định dạng hoặc thao tác không hợp lệ cũng bị từ chối.
4. **`OK`** — segment tồn tại, offset hợp lệ và quyền cho phép thao tác.

Do đó, nếu có nhiều điều kiện lỗi cùng lúc thì chỉ trạng thái có ưu tiên cao nhất được trả về: segment không tồn tại cùng offset sai vẫn là `SEGMENT_FAULT`; offset ngoài phạm vi cùng thao tác bị cấm vẫn là `OFFSET_OUT_OF_RANGE`. Chỉ khi hai bước đầu hợp lệ, module mới xét quyền truy cập.

Chạy riêng unit test của TV3 (`test_protection.py`) từ thư mục gốc dự án:

```bash
python -m unittest discover -s src/tests -t src -p "test_protection.py" -v
```

Chạy toàn bộ unit test của dự án:

```bash
python -m compileall src
python -m unittest discover -s src/tests -t src -v
```

## Định dạng CSV

Input gồm hai file; thứ tự cột phải đúng như dưới đây, tên cột phân biệt hoa/thường:

```csv
# segments.csv
seg_id,base,limit,perm
0,1000,400,R-X

# addresses.csv
seg_id,offset,access
0,100,R
```

- `seg_id`, `base`, `limit`, `offset`: số nguyên; `seg_id` và `base` không âm, `limit` lớn hơn 0.
- `perm`: đúng 3 ký tự: vị trí 1 là `R` hoặc `-`, vị trí 2 là `W` hoặc `-`, vị trí 3 là `X` hoặc `-`; ví dụ `R-X`, `RW-`, `R--`.
- `access`: `R` (đọc), `W` (ghi), hoặc `X` (thực thi). Chương trình chuẩn hóa chữ hoa trước khi kiểm tra.
- Kích thước bộ nhớ vật lý được cố định trong chương trình là **5000 byte** (địa chỉ 0–4999); không phải tham số trong CSV. Vì vậy, để tái lập kết quả cần dùng đúng hai CSV input và cùng phiên bản/đặc tả chương trình. Mỗi segment phải thỏa `base + limit <= 5000`, và các segment không chồng lấn.

`output/trace.csv` có một dòng cho mỗi địa chỉ, với các cột:

```csv
seg_id,offset,access,base,limit,physical,status,reason
```

`output/trace_steps.csv` lưu trace chi tiết, một dòng cho mỗi bước. Các trường kết quả được lặp lại trên mỗi bước để có thể lọc/đối chiếu; địa chỉ không có bước thuật toán vẫn có một dòng với các trường bước để trống:

```csv
result_no,seg_id,offset,access,base,limit,physical,status,reason,step_no,step_description,step_ok
```

## Thứ tự kiểm tra và trạng thái

1. Segment không tồn tại: `SEGMENT_FAULT`.
2. Offset < 0 hoặc offset >= limit: `OFFSET_OUT_OF_RANGE`.
3. Quyền truy cập không được phép: `PROTECTION_FAULT`.
4. Hợp lệ: `OK`, `physical = base + offset`.

| status | Ý nghĩa |
|---|---|
| OK | Dịch thành công |
| SEGMENT_FAULT | `seg_id` không có trong segment table |
| OFFSET_OUT_OF_RANGE | `offset < 0` hoặc `offset >= limit` |
| PROTECTION_FAULT | Quyền truy cập không được phép bởi `perm` |
| INVALID_INPUT | Dòng trong `addresses.csv` sai định dạng |

## Xử lý dữ liệu sai

- `segments.csv` rỗng/sai cấu trúc, có giá trị không hợp lệ, ID trùng, quyền sai, segment vượt kích thước bộ nhớ hoặc chồng lấn: từ chối file và báo lỗi.
- `addresses.csv` rỗng hoặc thiếu/sai tiêu đề: từ chối file.
- Dòng địa chỉ không hợp lệ: đánh dấu `INVALID_INPUT`, giữ nguyên vị trí trong kết quả và tiếp tục xử lý các dòng khác.

## Ví dụ kết quả

Với segment `0,1000,400,R-X`:

| Địa chỉ | Kết quả | Giải thích |
|---|---|---|
| `0,100,R` | `OK`, physical = 1100 | 1000 + 100 |
| `0,400,R` | `OFFSET_OUT_OF_RANGE` | Offset bằng limit |
| `0,200,W` | `PROTECTION_FAULT` | Segment không cho phép ghi |
| `3,10,R` | `SEGMENT_FAULT` | Segment 3 không tồn tại |

## Cấu trúc thư mục

```text
src/core/      thuật toán, đọc/ghi CSV, kiểm tra dữ liệu và oracle đối chiếu độc lập
src/gui/       giao diện
src/tests/     kiểm thử (bao gồm TV3 protection/oracle) và expected results
input/         CSV mẫu, edge_cases/ và error_cases/
output/        trace.csv và trace_steps.csv
report/        báo cáo
```

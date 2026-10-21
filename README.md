# OS_MEM_12 – Segmentation và địa chỉ logic
## Thành viên
- TV1 (nhóm trưởng):Vũ Duy Thành
- TV2: Phạm Uyên Trang
- TV3: Trần Tường Nguyên
- TV4: Trần Thị Ngọc Giàu
- TV5: Nguyễn Thanh Dũng
## Cài đặt và chạy

Yêu cầu: Windows, Python [3.x], thư viện GUI: [Tkinter (có sẵn trong Python) / PyQt...].
```bash
git clone https://github.com/ThanhVu297/Segmentation-and-logical-addressing.git
cd Segmentation-and-logical-addressing
pip install -r requirements.txt # bỏ qua nếu không có thư viện ngoài
python src/main.py
```
Cách dùng: mở ứng dụng, chọn segments.csv và addresses.csv (có sẵn trong thư mục input/), bấm dịch, xem kết quả trên màn hình, xuất trace.csv vào thư mục output/.
Chạy kiểm thử:
```bash
python -m unittest discover -s src/tests -v

```
## Định dạng CSV (chốt từ tuần 1, không đổi cột)
```
segments.csv:  seg_id,base,limit,perm
addresses.csv: seg_id,offset,access
trace.csv:     seg_id,offset,access,base,limit,physical,status,reason
```

- `perm`: gồm 3 ký tự. Ký tự 1 là `R` hoặc `-`, ký tự 2 là `W` hoặc `-`, ký tự 3 là `X` hoặc `-`. Ví dụ: `R-X`, `RW-`, `R--`.
- `access`: chỉ nhận chữ hoa `R` (đọc), `W` (ghi) hoặc `X` (thực thi).
- Bộ nhớ vật lý mặc định: 5000 byte (địa chỉ 0–4999). Mỗi segment phải thỏa `base + limit <= 5000`, `limit > 0`, và các segment không chồng lấn.

Đặc tả đầy đủ (ràng buộc từng cột, chính sách xử lý lỗi, danh sách file test): xem (https://docs.google.com/document/d/1-_8HaR0ZQqNwXhnGUSofY7TJcu7rtokn05q3U1j_u0o/edit?usp=sharing).



## Thứ tự kiểm tra lỗi

1. Segment không tồn tại: `SEGMENT_FAULT`
2. Offset < 0 hoặc offset >= limit: `OFFSET_OUT_OF_RANGE`
3. Quyền truy cập không hợp lệ (`R` cần `perm[0] = R`, `W` cần `perm[1] = W`, `X` cần `perm[2] = X`): `PROTECTION_FAULT`
4. Qua cả ba bước: `OK`, `physical = base + offset`

| status | Ý nghĩa |
|---|---|
| OK | Dịch thành công |
| SEGMENT_FAULT | `seg_id` không có trong segment table |
| OFFSET_OUT_OF_RANGE | `offset < 0` hoặc `offset >= limit` |
| PROTECTION_FAULT | Quyền truy cập không được phép bởi `perm` |
| INVALID_INPUT | Dòng trong `addresses.csv` sai định dạng |

## Xử lý dữ liệu sai

- `segments.csv` sai (rỗng, thiếu cột, không phải số, trùng `seg_id`, `perm` sai, vượt 5000 byte, chồng lấn): từ chối cả file, báo lỗi rõ ràng, không dịch địa chỉ.
- `addresses.csv` rỗng hoặc thiếu cột: từ chối cả file.
- Một dòng của `addresses.csv` sai định dạng: ghi dòng đó là `INVALID_INPUT` và tiếp tục các dòng còn lại.

## Ví dụ

`segments.csv`:

```
seg_id,base,limit,perm
0,1000,400,R-X
```

| addresses.csv | Kết quả | Giải thích |
|---|---|---|
| `0,100,R` | `OK`, physical = 1100 | 1000 + 100 |
| `0,400,R` | `OFFSET_OUT_OF_RANGE` | offset = limit |
| `0,200,W` | `PROTECTION_FAULT` | `R-X` không có quyền ghi |
| `3,10,R` | `SEGMENT_FAULT` | segment 3 không tồn tại |

## Cấu trúc thư mục

```text
src/
  core/      thuật toán dịch địa chỉ (không phụ thuộc GUI)
  gui/       giao diện
  tests/     kiểm thử, kèm expected/ (kết quả mong đợi tính tay)
  main.py    điểm khởi chạy
input/       CSV mẫu: segments.csv, addresses.csv, edge_cases/, error_cases/
output/      trace.csv do ứng dụng xuất ra
report/      báo cáo
docs/        đặc tả dữ liệu và bằng chứng tiến độ hàng tuần (docs/progress/)
```
## Kiểm thử

- Đối chiếu kết quả thực tế (actual) với `src/tests/expected/*.csv` (oracle tính tay).
- Dữ liệu biên trong `input/edge_cases/`, dữ liệu sai trong `input/error_cases/`.
- Bảng kiểm thử, số liệu hiệu năng: xem trong báo cáo ([report/](report/)).

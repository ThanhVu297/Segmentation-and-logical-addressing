# Bảng kiểm thử – Ứng dụng phân đoạn địa chỉ logic

> Bảng này là checklist để ghi nhận kiểm thử thủ công và đối chiếu với bộ test tự động trong `src/tests/`. Chưa điền cột **Kết quả thực tế** hoặc **Trạng thái** nếu chưa chạy kiểm thử trên máy; không đánh dấu PASS chỉ dựa trên kết quả mong đợi.

## A. Kiểm thử chức năng dịch địa chỉ

| ID | Trường hợp kiểm thử | Dữ liệu / thao tác | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|---|
| T01 | Địa chỉ hợp lệ, quyền đọc được cấp | Segment `0`: base=1000, limit=400, perm=`R-X`; địa chỉ `(0,100,R)` | `OK`, physical=`1100` | Chưa chạy | ☐ Chưa kiểm thử |
| T02 | Offset bằng 0 | `(0,0,R)` | `OK`, physical=`1000` | Chưa chạy | ☐ Chưa kiểm thử |
| T03 | Offset lớn nhất còn hợp lệ | `(0,399,X)` | `OK`, physical=`1399` | Chưa chạy | ☐ Chưa kiểm thử |
| T04 | Offset bằng limit | `(0,400,R)` | `OFFSET_OUT_OF_RANGE` | Chưa chạy | ☐ Chưa kiểm thử |
| T05 | Offset âm | `(1,-1,R)` | `OFFSET_OUT_OF_RANGE` | Chưa chạy | ☐ Chưa kiểm thử |
| T06 | Không đủ quyền truy cập | Segment `0` có perm=`R-X`; địa chỉ `(0,200,W)` | `PROTECTION_FAULT` | Chưa chạy | ☐ Chưa kiểm thử |
| T07 | Segment không tồn tại | `(3,10,R)` | `SEGMENT_FAULT` | Chưa chạy | ☐ Chưa kiểm thử |
| T08 | Quyền truy cập sai định dạng | Thử access khác `R`, `W`, `X` | `INVALID_INPUT` | Chưa chạy | ☐ Chưa kiểm thử |

## B. Kiểm thử bảng segment và dữ liệu CSV

| ID | Trường hợp kiểm thử | File / dữ liệu | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|---|
| T09 | CSV segment mẫu hợp lệ | `input/segments.csv` | Đọc được 3 segment; bảng segment hợp lệ | Chưa chạy | ☐ Chưa kiểm thử |
| T10 | Hai segment kề nhau, không chồng lấn | `input/edge_cases/segments_adjacent.csv` | Chấp nhận; không báo `OVERLAP` | Chưa chạy | ☐ Chưa kiểm thử |
| T11 | Segment chạm đúng giới hạn bộ nhớ | `input/edge_cases/segments_memory_boundary.csv` | Chấp nhận nếu `base + limit = mem_size` | Chưa chạy | ☐ Chưa kiểm thử |
| T12 | Segment chồng lấn | `input/error_cases/segments_overlap.csv` | Báo lỗi `OVERLAP` | Chưa chạy | ☐ Chưa kiểm thử |
| T13 | Segment vượt bộ nhớ | `input/error_cases/segments_exceeds_memory.csv` | Báo lỗi `EXCEEDS_MEMORY` | Chưa chạy | ☐ Chưa kiểm thử |
| T14 | Limit bằng 0 hoặc base âm | Các CSV tương ứng trong `input/error_cases/` | Báo `INVALID_RANGE` hoặc từ chối file với thông báo rõ ràng | Chưa chạy | ☐ Chưa kiểm thử |
| T15 | Quyền perm sai định dạng | Các CSV `segments_invalid_perm_*.csv` | Từ chối dữ liệu và nêu lỗi định dạng quyền | Chưa chạy | ☐ Chưa kiểm thử |
| T16 | Thiếu cột hoặc CSV rỗng | Các CSV tương ứng trong `input/error_cases/` | Từ chối file, thông báo lỗi; không làm ứng dụng thoát đột ngột | Chưa chạy | ☐ Chưa kiểm thử |
| T17 | Một dòng địa chỉ không hợp lệ | CSV địa chỉ có dòng sai định dạng | Dòng sai mang trạng thái `INVALID_INPUT`; các dòng khác vẫn được xử lý theo đặc tả | Chưa chạy | ☐ Chưa kiểm thử |

## C. Kiểm thử xuất kết quả và giao diện

| ID | Trường hợp kiểm thử | Thao tác | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|---|
| T18 | Dịch toàn bộ CSV địa chỉ | Mở `input/segments.csv` và `input/addresses.csv`, chọn dịch toàn bộ | Có một kết quả tương ứng với từng dòng địa chỉ | Chưa chạy | ☐ Chưa kiểm thử |
| T19 | Xuất trace CSV | Chọn xuất kết quả vào `output/trace.csv` | Tạo được file; có tiêu đề `seg_id,offset,access,base,limit,physical,status,reason` và dữ liệu khớp trên màn hình | Chưa chạy | ☐ Chưa kiểm thử |
| T20 | Xuất khi chưa có kết quả | Bấm xuất trước khi dịch địa chỉ | Ứng dụng báo chưa có kết quả; không tạo trace rỗng ngoài ý muốn | Chưa chạy | ☐ Chưa kiểm thử |
| T21 | Xem từng bước dịch | Dịch một địa chỉ và bấm nút xem bước tiếp theo | Các bước kiểm tra được hiển thị đúng thứ tự; kết luận khớp trạng thái cuối | Chưa chạy | ☐ Chưa kiểm thử |
| T22 | Hiển thị bản đồ bộ nhớ | Nạp bảng segment hợp lệ và dịch địa chỉ thành công | Hiển thị segment; đánh dấu địa chỉ vật lý tương ứng | Chưa chạy | ☐ Chưa kiểm thử |

## Ghi nhận kết quả

- Ngày kiểm thử: ____________________
- Người kiểm thử: ____________________
- Hệ điều hành / phiên bản Python: ____________________
- Phiên bản commit được kiểm thử: ____________________
- Tổng số PASS: ______  FAIL: ______  Chưa kiểm thử: ______
- Lỗi phát hiện và ghi chú: ______________________________________________

### Quy ước trạng thái

- ☐ Chưa kiểm thử
- PASS — kết quả thực tế đúng như mong đợi
- FAIL — kết quả thực tế khác mong đợi; ghi chi tiết lỗi ở phần ghi chú
- N/A — không áp dụng; nêu lý do

### Đối chiếu với test tự động

Bộ kiểm thử tự động hiện nằm trong `src/tests/`, gồm kiểm thử logic dịch, validator, bản đồ bộ nhớ và benchmark. Khi chạy test, ghi lại chính xác lệnh và kết quả trong báo cáo; bảng checklist này không thay thế log kiểm thử tự động.

# Bảng kiểm thử – Ứng dụng phân đoạn địa chỉ logic

> Bảng này ghi nhận kết quả kiểm thử tự động hiện có trong `src/tests/`. PASS chỉ áp dụng cho hành vi thực sự được test; N/A nghĩa là hiện chưa có test tự động cho thao tác đó.

## A. Kiểm thử chức năng dịch địa chỉ

| ID | Trường hợp kiểm thử | Dữ liệu / thao tác | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|---|
| T01 | Địa chỉ hợp lệ, quyền đọc được cấp | Segment `0`: base=1000, limit=400, perm=`R-X`; địa chỉ `(0,100,R)` | `OK`, physical=`1100` | `OK`, physical=`1100` | PASS |
| T02 | Offset bằng 0 | `(0,0,R)` | `OK`, physical=`1000` | `OK`, physical=`1000` | PASS |
| T03 | Offset lớn nhất còn hợp lệ | `(0,399,X)` | `OK`, physical=`1399` | `OK`, physical=`1399` | PASS |
| T04 | Offset bằng limit | `(0,400,R)` | `OFFSET_OUT_OF_RANGE` | `OFFSET_OUT_OF_RANGE` | PASS |
| T05 | Offset âm | `(1,-1,R)` | `OFFSET_OUT_OF_RANGE` | `OFFSET_OUT_OF_RANGE` | PASS |
| T06 | Không đủ quyền truy cập | Segment `0` có perm=`R-X`; địa chỉ `(0,200,W)` | `PROTECTION_FAULT` | `PROTECTION_FAULT` | PASS |
| T07 | Segment không tồn tại | `(3,10,R)` | `SEGMENT_FAULT` | `SEGMENT_FAULT` | PASS |
| T08 | Quyền truy cập sai định dạng | Thử access khác `R`, `W`, `X` (ví dụ `Q`, `r`, `None`); access được kiểm tra **trước** bước tìm segment nên `(9,10,Q)` vẫn là `INVALID_INPUT`, không phải `SEGMENT_FAULT` | `INVALID_INPUT` | `INVALID_INPUT` (`test_translator.py`: `test_translate_invalid_input_more_cases`, `test_translate_invalid_access_checked_before_segment_lookup`) | PASS |
## B. Kiểm thử bảng segment và dữ liệu CSV

| ID | Trường hợp kiểm thử | File / dữ liệu | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|---|
| T09 | CSV segment mẫu hợp lệ | `input/segments.csv` | Đọc được 3 segment; bảng segment hợp lệ | Đọc được 3 segment; validator không trả issue (`test_benchmark.py`) | PASS |
| T10 | Hai segment kề nhau, không chồng lấn | `input/edge_cases/segments_adjacent.csv` | Chấp nhận; không báo overlap | Validator trả danh sách issue rỗng (`test_validator.py`) | PASS |
| T11 | Segment chạm đúng giới hạn bộ nhớ | `input/edge_cases/segments_memory_boundary.csv` | Chấp nhận nếu `base + limit = mem_size` | Validator chấp nhận segment vừa khít bộ nhớ (`test_validator.py`) | PASS |
| T12 | Segment chồng lấn | `input/error_cases/segments_overlap.csv` | Đọc CSV bị từ chối bằng ngoại lệ `ValidationError`, thông báo tiếng Việt có nội dung “chồng lấn”; không trả mã `OVERLAP` | Reader ném đúng ngoại lệ tiếng Việt; test CSV thất bại vì so khớp hoa/thường `"Dòng 2"` với `"dòng 2"`, và test benchmark còn kỳ vọng reader cho qua file lỗi (`test_csv_input.py`, `test_benchmark.py`) | FAIL |
| T13 | Segment vượt bộ nhớ | `input/error_cases/segments_exceeds_memory.csv` | Đọc CSV bị từ chối bằng ngoại lệ `ValidationError`, thông báo tiếng Việt “vượt kích thước bộ nhớ”; không trả mã `EXCEEDS_MEMORY` | Reader ném `ValidationError` với thông báo tiếng Việt; test benchmark thất bại do kỳ vọng reader cho qua file lỗi (`test_csv_input.py`, `test_benchmark.py`) | FAIL |
| T14 | Limit bằng 0 hoặc base âm | Các CSV tương ứng trong `input/error_cases/` | Đọc CSV bị từ chối bằng `ValidationError` tiếng Việt; kiểm tra validator độc lập có thể báo `INVALID_RANGE` | Reader từ chối dữ liệu; validator độc lập báo `INVALID_RANGE`, nhưng test benchmark kỳ vọng reader cho qua các CSV này (`test_validator.py`, `test_benchmark.py`) | FAIL |
| T15 | Quyền perm sai định dạng | Các CSV `segments_invalid_perm_*.csv` | Đọc CSV bị từ chối bằng `ValidationError` tiếng Việt; kiểm tra validator độc lập có thể báo `INVALID_PERM` | Reader từ chối dữ liệu; validator độc lập báo `INVALID_PERM`, nhưng test benchmark kỳ vọng reader cho qua các CSV này (`test_validator.py`, `test_benchmark.py`) | FAIL |
| T16 | Thiếu cột hoặc CSV rỗng | CSV địa chỉ rỗng, chỉ có header hoặc thiếu cột | Từ chối file bằng `ValidationError` | Các trường hợp file rỗng/không có dòng/thiếu cột bị từ chối (`test_csv_input.py`) | PASS |
| T17 | Một dòng địa chỉ không hợp lệ | CSV địa chỉ có dòng sai định dạng | Dòng sai mang trạng thái `INVALID_INPUT`; các dòng khác vẫn được giữ lại | Giữ 3 dòng; dòng offset sai và access sai có trạng thái `INVALID_INPUT` (`test_csv_input.py`) | PASS |

## C. Kiểm thử xuất kết quả và giao diện

| ID | Trường hợp kiểm thử | Thao tác | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|---|
| T18 | Dịch toàn bộ CSV địa chỉ | Nạp hai CSV, dịch cả danh sách | Có một kết quả tương ứng với từng dòng địa chỉ | Controller xử lý 3 dòng gồm OK, offset ngoài phạm vi và input lỗi (`test_app_integration.py`) | PASS |
| T19 | Xuất trace CSV | Ghi kết quả ra trace CSV | Tạo file trace và trace bước với kết quả đúng | CSV summary và từng bước được ghi/đọc lại; controller cũng xác nhận file được tạo (`test_csv_output.py`, `test_app_integration.py`) | PASS |
| T20 | Xuất khi chưa có kết quả | Bấm xuất trước khi dịch địa chỉ | Ứng dụng báo chưa có kết quả; không tạo trace rỗng ngoài ý muốn | Chưa có test tự động cho thao tác này | N/A |
| T21 | Xem từng bước dịch | Dịch một địa chỉ và bấm nút xem bước tiếp theo | Các bước được hiển thị đúng thứ tự; kết luận khớp trạng thái cuối | Chưa có test tương tác GUI cho nút xem bước; test CSV chỉ kiểm tra dữ liệu trace bước | N/A |
| T22 | Hiển thị bản đồ bộ nhớ | Nạp bảng segment và đánh dấu địa chỉ vật lý | Hiển thị segment; đánh dấu địa chỉ tương ứng | FakeCanvas xác nhận các segment và đường highlight được vẽ (`test_memory_map.py`) | PASS |

## Ghi nhận kết quả

- Ngày kiểm thử: ____________________
- Người kiểm thử: ____________________
- Hệ điều hành / phiên bản Python: ____________________
- Phiên bản commit được kiểm thử: ____________________
- Tổng số PASS: ______  FAIL: ______  Chưa kiểm thử: ______
- Lỗi phát hiện và ghi chú: ______________________________________________

### Quy ước trạng thái

- PASS — kết quả thực tế đúng như mong đợi
- FAIL — kết quả thực tế khác mong đợi; ghi chi tiết lỗi ở phần ghi chú
- N/A — chưa có test tự động bao phủ thao tác; nêu lý do

### Đối chiếu với test tự động

Bộ kiểm thử tự động hiện nằm trong `src/tests/`, gồm kiểm thử logic dịch, validator, bản đồ bộ nhớ và benchmark. Khi chạy test, ghi lại chính xác lệnh và kết quả trong báo cáo; bảng checklist này không thay thế log kiểm thử tự động.

Kết quả T09–T22 ở lần chạy pytest gần nhất: **8 PASS, 4 FAIL, 2 N/A**. Toàn bộ test TV3 trong `test_protection.py` pass; các FAIL CSV ghi rõ nguyên nhân tại từng dòng.

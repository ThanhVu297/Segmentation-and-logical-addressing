# Báo cáo Q5 – TV5 (Nguyễn Thanh Dũng)

Đề tài OS\_MEM\_12: Segmentation và địa chỉ logic. Phần Q5 phụ trách kiểm tra bảng segment (`validator.py`), bản đồ bộ nhớ (`memory_map.py`) và đo hiệu năng dịch địa chỉ (`benchmark.py`).

## 0. Nguồn số liệu và môi trường đo

Số liệu trong báo cáo này do **Claude đo trong môi trường thử nghiệm**, không phải trên máy cá nhân của TV5. TV5 cần chạy lại lệnh ở mục 2 trên máy mình, thay các bảng số và ghi lại cấu hình máy trước khi nộp bản chính thức.

| Mục | Giá trị |
| --- | --- |
| Hệ điều hành | Linux 6.18 (Ubuntu 24.04) |
| CPU | Intel Xeon 2,10 GHz, 1 lõi khả dụng |
| Python | 3.12.3 |
| pandas | 3.0.6 |
| Seed | 42 |
| Tỉ lệ địa chỉ lỗi cố ý (`invalid_ratio`) | 0,2 |
| Bảng segment | `input/segments.csv` (3 segment: 0 → \[1000, 1400) R-X, 1 → \[2000, 3000) RW-, 2 → \[3500, 4000) R--) |
| Số lần lặp mỗi kích thước | 5 (hai lần chạy độc lập, ký hiệu A và B) |

## 1. Chỉ số đo

- **Thời gian dịch n địa chỉ:** đo bằng `time.perf_counter`, lặp nhiều lần, báo cả `min` và `median`.
- **µs trên mỗi địa chỉ:** `median / n × 1.000.000`.
- **Ratio so với lần trước:** `median(n) / median(n trước)`. Nếu thuật toán là O(n) thì ratio xấp xỉ `n / n trước` = 10 khi n tăng 10 lần.
- **Mismatch với oracle:** số địa chỉ mà `translate()` trả khác oracle (cả `status` lẫn địa chỉ vật lý). Kỳ vọng bằng 0.
- **Thời gian `validate_table`:** đo riêng theo số segment.

## 2. Phương pháp đo

Lệnh chạy từ thư mục gốc repo:

```text
python src/core/benchmark.py --segments input/segments.csv --repeats 5 --out output/benchmark.csv
```

Các nguyên tắc để số đo tái lập và công bằng:

1. **Cùng seed cho cùng bộ địa chỉ** ở mọi lần chạy.
2. **Sinh địa chỉ và tính kết quả oracle nằm ngoài vùng đo thời gian**, nên thời gian chỉ phản ánh `translate()`.
3. **Vòng đo không giữ kết quả**, tránh tốn RAM khi n = 1.000.000. Việc đối chiếu với oracle chạy ở một lượt riêng, không tính thời gian.
4. **Oracle viết độc lập** với `translator.py`, theo thứ tự kiểm tra trong README: segment, offset, rồi quyền R/W/X.
5. Bộ địa chỉ gồm cả địa chỉ hợp lệ và lỗi: offset bằng limit (biên), offset lớn hơn limit, segment không tồn tại, offset âm. `access` chọn ngẫu nhiên R/W/X nên `PROTECTION_FAULT` cũng xuất hiện tự nhiên.

## 3. Độ phức tạp

| Hàm | Độ phức tạp | Giải thích |
| --- | --- | --- |
| `translate` (một địa chỉ) | O(1) | Tra segment bằng dict (`SegmentTable.get`), vài phép so sánh và một phép cộng. |
| `translate_batch` (n địa chỉ) | O(n) | Gọi `translate` n lần. |
| `validate_table` (n segment) | O(n log n + k) | Sắp xếp n segment theo `base`, rồi mỗi segment chỉ so với các segment đứng sau cho tới khi `b.base >= a_end`. k là số cặp chồng lấn được báo. |
| `benchmark` (n địa chỉ) | O(n) | Sinh địa chỉ, đo, rồi đối chiếu oracle, mỗi bước tuyến tính. |

## 4. Kết quả đo dịch địa chỉ

Bảng dưới là `median` (giây) và µs trên mỗi địa chỉ, hai lần chạy độc lập (mỗi lần 5 lặp). Mismatch với oracle bằng **0** ở mọi dòng.

| n (số địa chỉ) | Lần A: median (s) | Lần A: µs/địa chỉ | Lần A: ratio | Lần B: median (s) | Lần B: µs/địa chỉ | Lần B: ratio |
| --- | --- | --- | --- | --- | --- | --- |
| 1.000 | 0,0030 | 2,97 | – | 0,0032 | 3,19 | – |
| 10.000 | 0,0285 | 2,85 | 9,59 | 0,0318 | 3,18 | 9,96 |
| 100.000 | 0,2956 | 2,96 | 10,38 | 0,2864 | 2,86 | 9,00 |
| 1.000.000 | 2,8394 | 2,84 | 9,61 | 2,9746 | 2,98 | 10,39 |

Giá trị `min` (giây):

| n | Lần A | Lần B |
| --- | --- | --- |
| 1.000 | 0,0027 | 0,0028 |
| 10.000 | 0,0274 | 0,0274 |
| 100.000 | 0,2844 | 0,2696 |
| 1.000.000 | 2,7248 | 2,8208 |

**Nhận xét.** Chi phí mỗi địa chỉ gần như không đổi, quanh 2,8 đến 3,2 µs, khi n tăng từ 1.000 lên 1.000.000. Ratio đo được nằm trong khoảng 9,0 đến 10,4, sát giá trị kỳ vọng 10. Kết luận: thời gian dịch **tăng gần tuyến tính theo n**, phù hợp phân tích O(n). Mức 3 µs mỗi địa chỉ cao hơn mức tối thiểu của một phép tra dict vì mỗi lần dịch còn tạo danh sách các bước trace phục vụ GUI và file `trace_steps.csv`.

## 5. Giải thích ratio 7,76 ở n = 1.000.000

Trong một lần chạy trước (3 lặp, ghi ở file công việc `TV5_cong_viec.xlsx`), ratio ở n = 1.000.000 là 7,76, thấp hơn kỳ vọng 10 khoảng 22%. Nguyên nhân là median ở n = 100.000 (0,254 s, tức 2,54 µs mỗi địa chỉ) cao hơn bình thường, còn ở n = 1.000.000 (1,97 s, tức 1,97 µs mỗi địa chỉ) thấp hơn. Chạy lại 2 lần, mỗi lần 5 lặp, ratio quay về 9,6 và 10,4. Vì vậy lệch này là **nhiễu giữa các lần chạy**, không phải thuật toán nhanh hơn tuyến tính:

- Máy dùng chung, tải nền thay đổi giữa các lần đo.
- Chỉ 3 lặp thì median dễ bị kéo bởi một lần đo chậm bất thường.
- Ảnh hưởng của bộ nhớ đệm và trình thu gom rác (GC) của Python khác nhau theo kích thước dữ liệu.

Các nguyên nhân trên là những yếu tố thường gặp khi đo thời gian ngắn; báo cáo chưa tách riêng từng yếu tố bằng thực nghiệm. Khuyến nghị: dùng ít nhất 5 lặp và so sánh nhiều lần chạy trước khi kết luận về độ lệch.

## 6. Kết quả đo `validate_table`

Dựng bảng gồm n segment không chồng lấn (mỗi segment dài 2, cách nhau 3), chạy 5 lần:

| n (số segment) | min (ms) | Ratio so với lần trước | Số vấn đề báo |
| --- | --- | --- | --- |
| 1.000 | 0,43 | – | 0 |
| 10.000 | 4,72 | 11,0 | 0 |
| 100.000 | 54,84 | 11,6 | 0 |

Ratio 11 đến 12 khi n tăng 10 lần là hợp lý với O(n log n) (lý thuyết khoảng 12 đến 13). Dữ liệu thử nghiệm đã được sắp theo `base` sẵn nên bước sắp xếp chạy gần như tuyến tính; với dữ liệu xáo trộn, chi phí sắp xếp O(n log n) sẽ rõ hơn. Phép so sánh chồng lấn không bị suy biến về O(n²) vì mỗi segment dừng sớm khi gặp segment bắt đầu sau điểm kết thúc của nó.

## 7. Bản đồ bộ nhớ (`memory_map.py`)

Module vẽ các segment lên canvas theo `base` và `limit`, và đánh dấu vị trí địa chỉ vật lý của kết quả đang xem. Module dùng danh sách vấn đề từ `validator` để cảnh báo chồng lấn hoặc vượt bộ nhớ. Hiện `csv_input.py` đã chặn các file lỗi này ngay lúc đọc, nên trong GUI thường không có vấn đề nào được hiển thị; `validator` vẫn được kiểm thử độc lập bằng bảng dựng trực tiếp. Mục T22 trong checklist (xem bản đồ trên máy thật) cần TV5 xác nhận thủ công.

## 8. Trade-off

| Lựa chọn | Lợi | Đánh đổi |
| --- | --- | --- |
| Tra segment bằng dict | O(1) mỗi địa chỉ, dễ đọc | Tốn thêm bộ nhớ so với mảng, và cần `seg_id` duy nhất. |
| Tạo danh sách bước trace cho từng địa chỉ | GUI và `trace_steps.csv` giải thích được từng bước | Chi phí mỗi địa chỉ khoảng 3 µs, cao hơn một phép tra thuần. Với n rất lớn nên có chế độ không tạo trace (chưa làm). |
| Sắp xếp rồi quét sớm dừng trong `validate_table` | O(n log n) thay vì O(n²) của so sánh mọi cặp | Cần sắp xếp trước, và phải sao chép danh sách segment. |
| Oracle độc lập, chạy ngoài vùng đo | Bắt được lỗi logic của `translate`; không làm sai thời gian đo | Thêm code phải bảo trì, và phải giữ oracle đúng thứ tự kiểm tra của README. |
| Không giữ kết quả khi đo, đối chiếu ở lượt riêng | Tiết kiệm RAM với n = 1.000.000 | Mỗi kích thước chạy `translate` thêm một lượt, nên tổng thời gian chạy benchmark dài hơn. |
| Báo cả `min` và `median` | `min` ít bị nhiễu, `median` đại diện hơn | Hai con số khác nhau; cần nói rõ dùng số nào để tính ratio (báo cáo dùng `median`). |
| Seed cố định = 42 | Tái lập được | Chỉ phản ánh một bộ địa chỉ; tỉ lệ lỗi 20% có thể không đại diện cho mọi tải thực tế. |

## 9. Kiểm thử và độ chính xác

- `benchmark.py` chạy đủ 4 kích thước 1.000 / 10.000 / 100.000 / 1.000.000 và so từng địa chỉ với oracle: **0 sai lệch** ở cả hai lần chạy.
- Bộ test của nhóm sau khi áp bản sửa cuối: **100 test pass** (`python -m unittest discover -s tests -t .` trong `src/`).
- Test của TV5: `test_validator.py`, `test_memory_map.py`, `test_benchmark.py` (đã sửa để kiểm thử `validate_table` trên bảng dựng bằng `load_table`, và xác nhận `csv_input` từ chối các file lỗi) và `test_gen_workload.py` (mới).
- `gen_workload.py` mặc định ghi vào `output/addresses_generated.csv`, không ghi đè `input/addresses.csv`.

## 10. Hạn chế

- Số đo từ môi trường thử nghiệm 1 lõi, cần đo lại trên máy TV5 và ghi rõ cấu hình.
- Chưa so sánh với cách cài đặt khác (ví dụ numpy hoặc bỏ trace), nên chưa có số liệu về mức tăng tốc có thể đạt được.
- Chưa đo ảnh hưởng của tỉ lệ địa chỉ lỗi (`invalid_ratio`) lên thời gian dịch.
- Chưa kiểm tra GUI hiển thị bản đồ bộ nhớ trên máy thật.

## 11. Việc cần làm trước khi nộp

1. Chạy lại benchmark trên máy TV5, thay các bảng ở mục 0, 4 và 6, giữ nguyên các đoạn phân tích nếu số liệu mới vẫn cùng xu hướng.
2. Commit `output/benchmark.csv` hoặc dán bảng số vào báo cáo.
3. Xuất báo cáo (Word hoặc PDF) hoặc chép nội dung sang `report/main-report/Q5.md`, cùng định dạng với `Q3.md`.
4. Mở Pull Request đưa bản sửa code vào `main` (xem file `fix-all-on-main.patch`).

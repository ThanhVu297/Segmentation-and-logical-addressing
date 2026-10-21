# OS_MEM_12 – Segmentation và địa chỉ logic

Mô phỏng dịch địa chỉ logic (segment, offset) sang địa chỉ vật lý, phát hiện lỗi và bảo vệ vùng nhớ.

## Định dạng CSV (chốt từ tuần 1, không đổi cột)

segments.csv:  seg_id,base,limit,perm

addresses.csv: seg_id,offset,access

trace.csv:     seg,offset,access,base,limit,physical,status,reason

- perm: gồm 3 ký tự, ví dụ R-X, RW-, R--
- access: R (đọc), W (ghi) hoặc X (thực thi)
- Bộ nhớ vật lý mặc định: 5000 byte

## Thứ tự kiểm tra lỗi

1. Segment có tồn tại không
2. Offset có nằm trong 0 ≤ offset < limit không
3. Quyền truy cập có hợp lệ không
## Thành viên
- TV1 (nhóm trưởng):Vũ Duy Thành
- TV2: Phạm Uyên Trang
- TV3: Trần Tường Nguyên
- TV4: Trần Thị Ngọc Giàu
- TV5: Nguyễn Thanh Dũng

## Cài đặt và chạy
(sẽ bổ sung khi có code)

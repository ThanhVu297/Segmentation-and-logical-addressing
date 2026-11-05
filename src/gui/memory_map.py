"""memory_map.py - TV5: vẽ bản đồ bộ nhớ vật lý bằng Tkinter Canvas.

Hợp đồng cho TV4 (GUI), đặt trong src/gui/:
    draw_memory_map(canvas, table, mem_size,
                    highlight_addr=None, fault_msg=None, issues=()) -> list[Block]

Thiết kế: phần TÍNH TOÁN (compute_layout, addr_to_y) không phụ thuộc Tkinter
nên test được bằng unittest; draw_memory_map chỉ gọi các hàm vẽ của canvas.

Quy ước vẽ: địa chỉ 0 ở trên cùng, mem_size ở dưới cùng; chiều cao khối tỉ lệ
với limit. Segment quá nhỏ được kéo dài tới min_block_px chỉ để nhìn thấy
(chỉ ảnh hưởng hiển thị, không ảnh hưởng số liệu).
"""
from __future__ import annotations

from dataclasses import dataclass

from core.validator import get_segments

SEG_COLORS = [
    "#8ecae6", "#ffb703", "#b7e4c7", "#cdb4db",
    "#ffafcc", "#f4a261", "#a8dadc", "#e9c46a",
]

TOP_MARGIN = 30
BOTTOM_MARGIN = 60  # chừa chỗ cho banner cảnh báo
LEFT_MARGIN = 100   # chừa chỗ cho nhãn địa chỉ
RIGHT_MARGIN = 90   # chừa chỗ cho nhãn địa chỉ vừa dịch


@dataclass(frozen=True)
class Block:
    seg_id: object
    base: int
    end: int       # base + limit (loại trừ)
    y0: float
    y1: float
    label: str
    color: str


def addr_to_y(addr, mem_size, top, height):
    """Đổi địa chỉ vật lý sang tọa độ y (kẹp trong [0, mem_size])."""
    addr = max(0, min(addr, mem_size))
    return top + addr / mem_size * height


def compute_layout(table, mem_size, top=TOP_MARGIN, height=400, min_block_px=14):
    """Tính khối chữ nhật cho từng segment, sắp theo base tăng dần."""
    if mem_size <= 0:
        raise ValueError("mem_size phải > 0")
    bottom = top + height
    blocks = []
    ordered = sorted(get_segments(table), key=lambda s: (s.base, s.seg_id))
    for k, seg in enumerate(ordered):
        end = seg.base + seg.limit
        y0 = addr_to_y(seg.base, mem_size, top, height)
        y1 = addr_to_y(end, mem_size, top, height)
        if y1 - y0 < min_block_px:
            y1 = y0 + min_block_px
            if y1 > bottom:  # sát đáy: dời lên để không tràn
                y1 = bottom
                y0 = bottom - min_block_px
        color_idx = seg.seg_id if isinstance(seg.seg_id, int) else k
        perm = getattr(seg, "perm", "")
        label = f"Seg {seg.seg_id}: {seg.base}-{end - 1} (limit {seg.limit}, {perm})"
        blocks.append(
            Block(seg.seg_id, seg.base, end, y0, y1, label,
                  SEG_COLORS[color_idx % len(SEG_COLORS)])
        )
    return blocks


def draw_memory_map(canvas, table, mem_size, highlight_addr=None,
                    fault_msg=None, issues=()):
    """Vẽ bản đồ bộ nhớ lên canvas và trả về danh sách Block đã vẽ.

    highlight_addr: địa chỉ vật lý vừa dịch (đường đỏ + nhãn); bỏ qua nếu
                    nằm ngoài [0, mem_size).
    fault_msg:      nếu có, hiện banner cảnh báo màu đỏ ở đáy canvas.
    issues:         kết quả validate_table; segment liên quan được viền đỏ.
    """
    width = max(int(canvas.winfo_width()), int(float(canvas.cget("width"))))
    height = max(int(canvas.winfo_height()), int(float(canvas.cget("height"))))
    bar_height = max(height - TOP_MARGIN - BOTTOM_MARGIN, 50)
    x0, x1 = LEFT_MARGIN, max(width - RIGHT_MARGIN, LEFT_MARGIN + 60)

    flagged = set()
    for issue in issues:
        flagged.update(issue.seg_ids)

    canvas.delete("all")

    # khung bộ nhớ vật lý + nhãn 0 và mem_size
    canvas.create_rectangle(x0, TOP_MARGIN, x1, TOP_MARGIN + bar_height,
                            fill="#f1f1f1", outline="#555555")
    canvas.create_text(x0 - 6, TOP_MARGIN, text="0", anchor="e",
                       font=("Segoe UI", 8))
    canvas.create_text(x0 - 6, TOP_MARGIN + bar_height, text=str(mem_size),
                       anchor="e", font=("Segoe UI", 8))
    canvas.create_text(x0, TOP_MARGIN - 14,
                       text=f"Bộ nhớ vật lý ({mem_size} byte)",
                       anchor="w", font=("Segoe UI", 9, "bold"))

    blocks = compute_layout(table, mem_size, TOP_MARGIN, bar_height)
    for blk in blocks:
        bad = blk.seg_id in flagged
        canvas.create_rectangle(
            x0, blk.y0, x1, blk.y1, fill=blk.color,
            outline="#d00000" if bad else "#333333", width=3 if bad else 1)
        canvas.create_text(x0 + 6, (blk.y0 + blk.y1) / 2, text=blk.label,
                           anchor="w", font=("Segoe UI", 8))
        canvas.create_text(x0 - 6, blk.y0, text=str(blk.base), anchor="e",
                           font=("Segoe UI", 8))

    if highlight_addr is not None and 0 <= highlight_addr < mem_size:
        y = addr_to_y(highlight_addr, mem_size, TOP_MARGIN, bar_height)
        canvas.create_line(x0 - 10, y, x1 + 10, y, fill="#d00000", width=2)
        canvas.create_text(x1 + 14, y, text=f"{highlight_addr}", anchor="w",
                           fill="#d00000", font=("Segoe UI", 9, "bold"))

    if fault_msg:
        by = TOP_MARGIN + bar_height + 12
        canvas.create_rectangle(x0, by, x1, by + 34, fill="#ffe5e5",
                                outline="#d00000")
        canvas.create_text(x0 + 8, by + 17, text=f"CẢNH BÁO: {fault_msg}",
                           anchor="w", fill="#d00000",
                           font=("Segoe UI", 9, "bold"))
    return blocks

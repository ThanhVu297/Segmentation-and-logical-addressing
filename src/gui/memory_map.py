
"""memory_map.py - TV5: vẽ bản đồ bộ nhớ vật lý bằng Tkinter Canvas.

Hợp đồng cho TV4:
    draw_memory_map(canvas, table, mem_size,
                    highlight_addr=None, fault_msg=None,
                    issues=()) -> list[Block]

Phần tính toán compute_layout và addr_to_y không phụ thuộc Tkinter.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.validator import get_segments


SEG_COLORS = [
    "#8ecae6", "#ffb703", "#b7e4c7", "#cdb4db",
    "#ffafcc", "#f4a261", "#a8dadc", "#e9c46a",
]

TOP_MARGIN = 30
BOTTOM_MARGIN = 60
LEFT_MARGIN = 100
RIGHT_MARGIN = 90


@dataclass(frozen=True)
class Block:
    seg_id: object
    base: int
    end: int
    y0: float
    y1: float
    label: str
    color: str


def addr_to_y(addr, mem_size, top, height):
    """Đổi địa chỉ vật lý sang tọa độ y."""

    addr = max(0, min(addr, mem_size))

    return top + addr / mem_size * height


def compute_layout(
    table,
    mem_size,
    top=TOP_MARGIN,
    height=400,
    min_block_px=14
):
    """Tính các khối segment theo địa chỉ base."""

    if mem_size <= 0:
        raise ValueError("mem_size phải > 0")

    bottom = top + height
    blocks = []

    ordered = sorted(
        get_segments(table),
        key=lambda s: (s.base, s.seg_id)
    )

    for k, seg in enumerate(ordered):

        end = seg.base + seg.limit

        y0 = addr_to_y(
            seg.base,
            mem_size,
            top,
            height
        )

        y1 = addr_to_y(
            end,
            mem_size,
            top,
            height
        )

        # Kéo dài khối quá nhỏ để dễ quan sát
        if y1 - y0 < min_block_px:

            y1 = y0 + min_block_px

            if y1 > bottom:
                y1 = bottom
                y0 = bottom - min_block_px

        color_idx = (
            seg.seg_id
            if isinstance(seg.seg_id, int)
            else k
        )

        perm = getattr(seg, "perm", "")

        label = (
            f"Seg {seg.seg_id}: "
            f"{seg.base}-{end - 1} "
            f"(limit {seg.limit}, {perm})"
        )

        blocks.append(
            Block(
                seg.seg_id,
                seg.base,
                end,
                y0,
                y1,
                label,
                SEG_COLORS[color_idx % len(SEG_COLORS)]
            )
        )

    return blocks


def draw_memory_map(
    canvas,
    table,
    mem_size,
    highlight_addr=None,
    fault_msg=None,
    issues=()
):
    """Vẽ bản đồ bộ nhớ lên Canvas và trả về danh sách Block."""

    if mem_size <= 0:
        raise ValueError("mem_size phải > 0")

    # Cập nhật kích thước giao diện trước khi lấy kích thước Canvas
    canvas.update_idletasks()

    # CHỈ lấy kích thước thực tế theo pixel.
    # Không dùng canvas.cget("width") vì có thể trả về "10c".
    width = canvas.winfo_width()
    height = canvas.winfo_height()

    # Kích thước dự phòng nếu Canvas chưa hiển thị hoàn chỉnh
    if width <= 1:
        width = 650

    if height <= 1:
        height = 550

    bar_height = max(
        height - TOP_MARGIN - BOTTOM_MARGIN,
        50
    )

    x0 = LEFT_MARGIN
    x1 = max(
        width - RIGHT_MARGIN,
        LEFT_MARGIN + 60
    )

    # Lấy các segment có lỗi
    flagged = set()

    for issue in issues:
        flagged.update(issue.seg_ids)

    canvas.delete("all")

    # Khung bộ nhớ vật lý
    canvas.create_rectangle(
        x0,
        TOP_MARGIN,
        x1,
        TOP_MARGIN + bar_height,
        fill="#f1f1f1",
        outline="#555555"
    )

    # Nhãn địa chỉ đầu và cuối
    canvas.create_text(
        x0 - 6,
        TOP_MARGIN,
        text="0",
        anchor="e",
        font=("Segoe UI", 8)
    )

    canvas.create_text(
        x0 - 6,
        TOP_MARGIN + bar_height,
        text=str(mem_size),
        anchor="e",
        font=("Segoe UI", 8)
    )

    canvas.create_text(
        x0,
        TOP_MARGIN - 14,
        text=f"Bộ nhớ vật lý ({mem_size} byte)",
        anchor="w",
        font=("Segoe UI", 9, "bold")
    )

    # Tính vị trí từng segment
    blocks = compute_layout(
        table,
        mem_size,
        TOP_MARGIN,
        bar_height
    )

    # Vẽ từng segment
    for blk in blocks:

        bad = blk.seg_id in flagged

        canvas.create_rectangle(
            x0,
            blk.y0,
            x1,
            blk.y1,
            fill=blk.color,
            outline="#d00000" if bad else "#333333",
            width=3 if bad else 1
        )

        canvas.create_text(
            x0 + 6,
            (blk.y0 + blk.y1) / 2,
            text=blk.label,
            anchor="w",
            font=("Segoe UI", 8)
        )

        canvas.create_text(
            x0 - 6,
            blk.y0,
            text=str(blk.base),
            anchor="e",
            font=("Segoe UI", 8)
        )

    # Đánh dấu địa chỉ vật lý vừa dịch
    if (
        highlight_addr is not None
        and 0 <= highlight_addr < mem_size
    ):

        y = addr_to_y(
            highlight_addr,
            mem_size,
            TOP_MARGIN,
            bar_height
        )

        canvas.create_line(
            x0 - 10,
            y,
            x1 + 10,
            y,
            fill="#d00000",
            width=2
        )

        canvas.create_text(
            x1 + 14,
            y,
            text=str(highlight_addr),
            anchor="w",
            fill="#d00000",
            font=("Segoe UI", 9, "bold")
        )

    # Hiển thị cảnh báo nếu có lỗi
    if fault_msg:

        by = TOP_MARGIN + bar_height + 12

        canvas.create_rectangle(
            x0,
            by,
            x1,
            by + 34,
            fill="#ffe5e5",
            outline="#d00000"
        )

        canvas.create_text(
            x0 + 8,
            by + 17,
            text=f"CẢNH BÁO: {fault_msg}",
            anchor="w",
            fill="#d00000",
            font=("Segoe UI", 9, "bold")
        )

    return blocks

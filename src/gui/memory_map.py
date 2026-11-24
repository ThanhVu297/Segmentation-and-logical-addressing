"""memory_map.py - Ve ban do bo nho vat ly bang Tkinter Canvas (khong dau)."""
from __future__ import annotations

from dataclasses import dataclass
from core.validator import get_segments

PERM_COLORS = {
    "R-X": "#0284c7",  # Xanh duong
    "RW-": "#d97706",  # Cam dam
    "R--": "#16a34a",  # Xanh la
}
OTHER_COLOR = "#64748b"  # Xam cho quyen khac

TOP_MARGIN = 28
BOTTOM_MARGIN = 45
LEFT_MARGIN = 65
RIGHT_MARGIN = 65


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
    addr = max(0, min(addr, mem_size))
    return top + addr / mem_size * height


def compute_layout(table, mem_size, top=TOP_MARGIN, height=300, min_block_px=18):
    if mem_size <= 0:
        raise ValueError("mem_size phai > 0")
    bottom = top + height
    blocks = []
    ordered = sorted(get_segments(table), key=lambda s: (s.base, s.seg_id))
    for seg in ordered:
        end = seg.base + seg.limit
        y0 = addr_to_y(seg.base, mem_size, top, height)
        y1 = addr_to_y(end, mem_size, top, height)
        if y1 - y0 < min_block_px:
            y1 = y0 + min_block_px
            if y1 > bottom:
                y1 = bottom
                y0 = bottom - min_block_px
        perm = str(getattr(seg, "perm", "")).strip().upper()
        color = PERM_COLORS.get(perm, OTHER_COLOR)
        label = f"Seg {seg.seg_id} ({seg.base}-{end})"
        blocks.append(
            Block(seg.seg_id, seg.base, end, y0, y1, label, color)
        )
    return blocks


def draw_memory_map(canvas, table, mem_size, highlight_addr=None,
                    fault_msg=None, issues=()):
    canvas.update_idletasks()
    width = max(canvas.winfo_width(), int(float(canvas.cget("width"))))
    height = max(canvas.winfo_height(), int(float(canvas.cget("height"))))
    bar_height = max(height - TOP_MARGIN - BOTTOM_MARGIN, 80)
    x0, x1 = LEFT_MARGIN, max(width - RIGHT_MARGIN, LEFT_MARGIN + 100)

    flagged = set()
    for issue in issues:
        flagged.update(issue.seg_ids)

    canvas.delete("all")

    # Khung bo nho vat ly
    canvas.create_rectangle(
        x0, TOP_MARGIN, x1, TOP_MARGIN + bar_height,
        fill="#f8fafc", outline="#94a3b8", width=1
    )
    canvas.create_text(
        x0 - 8, TOP_MARGIN, text="0", anchor="e",
        fill="#475569", font=("Segoe UI", 8)
    )
    canvas.create_text(
        x0 - 8, TOP_MARGIN + bar_height, text=str(mem_size),
        anchor="e", fill="#475569", font=("Segoe UI", 8)
    )
    canvas.create_text(
        (x0 + x1) / 2, TOP_MARGIN - 14,
        text=f"Bo nho vat ly ({mem_size} byte)",
        anchor="center", fill="#334155", font=("Segoe UI", 9, "bold")
    )

    blocks = compute_layout(table, mem_size, TOP_MARGIN, bar_height)
    for blk in blocks:
        bad = blk.seg_id in flagged
        canvas.create_rectangle(
            x0, blk.y0, x1, blk.y1,
            fill=blk.color,
            outline="#dc2626" if bad else "#ffffff",
            width=2 if bad else 1
        )
        canvas.create_text(
            (x0 + x1) / 2, (blk.y0 + blk.y1) / 2,
            text=blk.label, anchor="center",
            fill="#ffffff", font=("Segoe UI", 9, "bold")
        )

    if highlight_addr is not None and 0 <= highlight_addr < mem_size:
        y = addr_to_y(highlight_addr, mem_size, TOP_MARGIN, bar_height)
        canvas.create_line(x0 - 12, y, x1 + 12, y, fill="#dc2626", width=2)
        canvas.create_text(
            x1 + 16, y, text=f"{highlight_addr}",
            anchor="w", fill="#dc2626", font=("Segoe UI", 9, "bold")
        )

    if fault_msg:
        by = TOP_MARGIN + bar_height + 8
        canvas.create_rectangle(
            x0, by, x1, by + 28,
            fill="#fee2e2", outline="#dc2626"
        )
        canvas.create_text(
            x0 + 8, by + 14, text=f"CANH BAO: {fault_msg}",
            anchor="w", fill="#dc2626", font=("Segoe UI", 8, "bold")
        )

    return blocks

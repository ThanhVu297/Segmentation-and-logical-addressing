"""
gui_panels.py - Các panel giao diện Tkinter thành phần (TV4 - Trần Thị Ngọc Giàu)
- Gồm đủ 5 panel: Segment Table, Logical Address Table, Step Trace, Memory Map Canvas, Batch Output.
- Hỗ trợ tô màu dòng XANH LÁ (OK) và ĐỎ (INVALID), hiển thị từng bước nhảy.
- Có sẵn create_gui_panels() để tương thích khi chạy qua gui.app.
"""

import unicodedata
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Dict, Any


def _khong_dau(text: str) -> str:
    if not text:
        return ""
    norm = unicodedata.normalize("NFD", str(text))
    no_marks = "".join(ch for ch in norm if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", no_marks).replace("đ", "d").replace("Đ", "D")


class SegmentPanel(ttk.LabelFrame):
    """Panel 1: Bảng phân đoạn (Segment Table)"""
    def __init__(self, parent, on_add_segment: Callable, on_load_csv: Callable, on_clear: Callable):
        super().__init__(parent, text="1. BẢNG PHÂN ĐOẠN (SEGMENT TABLE)", padding=8)
        self.on_add_segment = on_add_segment
        self.on_load_csv = on_load_csv
        self.on_clear = on_clear

        self._build_ui()

    def _build_ui(self):
        top_bar = ttk.Frame(self)
        top_bar.pack(fill=tk.X, pady=(0, 5))

        self.lbl_count = tk.Label(
            top_bar, text="0 SEGMENTS", font=("Segoe UI", 8, "bold"),
            bg="#e9ecef", fg="#495057", padx=6, pady=2
        )
        self.lbl_count.pack(side=tk.LEFT)

        btn_clear = tk.Button(
            top_bar, text="Xóa hết", command=self.on_clear,
            fg="#dc3545", bg="#ffffff", activeforeground="#b02a37",
            font=("Segoe UI", 9), bd=1, relief="solid", cursor="hand2", padx=8, pady=2
        )
        btn_clear.pack(side=tk.RIGHT, padx=(5, 0))

        btn_open = ttk.Button(top_bar, text="⇞ Mở file CSV", command=self.on_load_csv)
        btn_open.pack(side=tk.RIGHT)

        tree_container = ttk.Frame(self)
        tree_container.pack(fill=tk.BOTH, expand=True)

        cols = ("seg_id", "base", "limit", "permission", "action")
        self.tree = ttk.Treeview(tree_container, columns=cols, show="headings", height=4)
        self.tree.heading("seg_id", text="Segment ID")
        self.tree.heading("base", text="Base")
        self.tree.heading("limit", text="Limit")
        self.tree.heading("permission", text="Permission")
        self.tree.heading("action", text="Thao tác")

        self.tree.column("seg_id", width=80, anchor=tk.CENTER)
        self.tree.column("base", width=90, anchor=tk.CENTER)
        self.tree.column("limit", width=90, anchor=tk.CENTER)
        self.tree.column("permission", width=80, anchor=tk.CENTER)
        self.tree.column("action", width=80, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.lbl_empty = tk.Label(
            self.tree, text="Chưa có Segment nào. Hãy nhập thủ công bên dưới hoặc bấm \"Mở file CSV\".",
            font=("Segoe UI", 9, "italic"), fg="#6c757d", bg="#ffffff"
        )
        self.lbl_empty.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        form_frame = ttk.Frame(self, padding=(0, 6, 0, 0))
        form_frame.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Label(form_frame, text="Seg ID").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.ent_seg_id = ttk.Entry(form_frame, width=6)
        self.ent_seg_id.grid(row=0, column=1, padx=2, pady=2)

        ttk.Label(form_frame, text="Base (byte)").grid(row=0, column=2, padx=2, pady=2, sticky=tk.W)
        self.ent_base = ttk.Entry(form_frame, width=8)
        self.ent_base.grid(row=0, column=3, padx=2, pady=2)

        ttk.Label(form_frame, text="Limit (byte)").grid(row=0, column=4, padx=2, pady=2, sticky=tk.W)
        self.ent_limit = ttk.Entry(form_frame, width=8)
        self.ent_limit.grid(row=0, column=5, padx=2, pady=2)

        ttk.Label(form_frame, text="Permission").grid(row=0, column=6, padx=2, pady=2, sticky=tk.W)
        self.cbo_perm = ttk.Combobox(form_frame, values=["R-X", "RW-", "R--", "RNX"], width=6, state="readonly")
        self.cbo_perm.set("R-X")
        self.cbo_perm.grid(row=0, column=7, padx=2, pady=2)

        btn_add = tk.Button(
            form_frame, text="+ Thêm / Cập nhật", command=self._submit_add,
            bg="#0d6efd", fg="#ffffff", activebackground="#0b5ed7", activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2", padx=10, pady=3
        )
        btn_add.grid(row=0, column=8, padx=(5, 0), pady=2)

    def _submit_add(self):
        seg_id = self.ent_seg_id.get().strip()
        base = self.ent_base.get().strip()
        limit = self.ent_limit.get().strip()
        perm = self.cbo_perm.get().strip()

        if not seg_id or not base or not limit:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ Segment ID, Base và Limit!")
            return

        self.on_add_segment(seg_id, base, limit, perm)
        self.ent_seg_id.delete(0, tk.END)
        self.ent_base.delete(0, tk.END)
        self.ent_limit.delete(0, tk.END)

    def update_table(self, segments: List[Dict[str, Any]]):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not segments:
            self.lbl_empty.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        else:
            self.lbl_empty.place_forget()
            for seg in segments:
                if isinstance(seg, dict):
                    sid = seg.get("segment_id", seg.get("seg_id", seg.get("Segment ID", "")))
                    base = seg.get("base", seg.get("Base", ""))
                    limit = seg.get("limit", seg.get("Limit", ""))
                    perm = seg.get("permission", seg.get("perm", seg.get("Permission", "")))
                else:
                    sid, base, limit, perm = str(seg), "", "", ""
                self.tree.insert("", tk.END, values=(sid, base, limit, perm, "Sẵn sàng"))
        self.lbl_count.config(text=f"{len(segments)} SEGMENTS")


class LogicalAddressPanel(ttk.LabelFrame):
    """Panel 2: Bảng địa chỉ logic (Logical Address Table)"""
    def __init__(self, parent, on_add_address: Callable, on_load_csv: Callable, on_clear: Callable,
                 on_translate_selected: Callable, on_translate_all: Callable):
        super().__init__(parent, text="2. BẢNG ĐỊA CHỈ LOGIC (LOGICAL ADDRESS TABLE)", padding=8)
        self.on_add_address = on_add_address
        self.on_load_csv = on_load_csv
        self.on_clear = on_clear
        self.on_translate_selected = on_translate_selected
        self.on_translate_all = on_translate_all

        self._build_ui()

    def _build_ui(self):
        top_bar = ttk.Frame(self)
        top_bar.pack(fill=tk.X, pady=(0, 5))

        self.lbl_count = tk.Label(
            top_bar, text="0 ĐỊA CHỈ", font=("Segoe UI", 8, "bold"),
            bg="#e9ecef", fg="#495057", padx=6, pady=2
        )
        self.lbl_count.pack(side=tk.LEFT)

        btn_clear = tk.Button(
            top_bar, text="Xóa hết", command=self.on_clear,
            fg="#dc3545", bg="#ffffff", activeforeground="#b02a37",
            font=("Segoe UI", 9), bd=1, relief="solid", cursor="hand2", padx=8, pady=2
        )
        btn_clear.pack(side=tk.RIGHT, padx=(5, 0))

        btn_open = ttk.Button(top_bar, text="⇞ Mở file CSV", command=self.on_load_csv)
        btn_open.pack(side=tk.RIGHT)

        tree_container = ttk.Frame(self)
        tree_container.pack(fill=tk.BOTH, expand=True)

        cols = ("stt", "seg_id", "offset", "access", "action")
        self.tree = ttk.Treeview(tree_container, columns=cols, show="headings", height=4)
        self.tree.heading("stt", text="STT")
        self.tree.heading("seg_id", text="Segment ID")
        self.tree.heading("offset", text="Offset")
        self.tree.heading("access", text="Access")
        self.tree.heading("action", text="Thao tác")

        self.tree.column("stt", width=50, anchor=tk.CENTER)
        self.tree.column("seg_id", width=95, anchor=tk.CENTER)
        self.tree.column("offset", width=95, anchor=tk.CENTER)
        self.tree.column("access", width=80, anchor=tk.CENTER)
        self.tree.column("action", width=80, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.lbl_empty = tk.Label(
            self.tree, text="Chưa có địa chỉ logic nào. Hãy nhập thủ công bên dưới hoặc bấm \"Mở file CSV\".",
            font=("Segoe UI", 9, "italic"), fg="#6c757d", bg="#ffffff"
        )
        self.lbl_empty.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        bottom_frame = ttk.Frame(self, padding=(0, 6, 0, 0))
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        form_row = ttk.Frame(bottom_frame)
        form_row.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(form_row, text="Seg ID").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.ent_seg_id = ttk.Entry(form_row, width=6)
        self.ent_seg_id.grid(row=0, column=1, padx=2, pady=2)

        ttk.Label(form_row, text="Offset").grid(row=0, column=2, padx=2, pady=2, sticky=tk.W)
        self.ent_offset = ttk.Entry(form_row, width=8)
        self.ent_offset.grid(row=0, column=3, padx=2, pady=2)

        ttk.Label(form_row, text="Access").grid(row=0, column=4, padx=2, pady=2, sticky=tk.W)
        self.cbo_access = ttk.Combobox(form_row, values=["R", "W", "X"], width=6, state="readonly")
        self.cbo_access.set("R")
        self.cbo_access.grid(row=0, column=5, padx=2, pady=2)

        btn_add = tk.Button(
            form_row, text="+ Thêm địa chỉ", command=self._submit_add,
            bg="#0d6efd", fg="#ffffff", activebackground="#0b5ed7", activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2", padx=10, pady=3
        )
        btn_add.grid(row=0, column=6, padx=(5, 0), pady=2)

        btn_row = ttk.Frame(bottom_frame)
        btn_row.pack(fill=tk.X)

        btn_trans_sel = tk.Button(
            btn_row, text="Dịch dòng đang chọn", command=self._translate_selected,
            bg="#0d6efd", fg="#ffffff", activebackground="#0b5ed7", activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2", pady=5
        )
        btn_trans_sel.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 3))

        btn_trans_all = tk.Button(
            btn_row, text="Dịch tất cả", command=self.on_translate_all,
            bg="#008080", fg="#ffffff", activebackground="#006666", activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2", pady=5
        )
        btn_trans_all.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(3, 0))

    def _submit_add(self):
        seg_id = self.ent_seg_id.get().strip()
        offset = self.ent_offset.get().strip()
        access = self.cbo_access.get().strip()

        if not seg_id or not offset:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ Segment ID và Offset!")
            return

        self.on_add_address(seg_id, offset, access)
        self.ent_seg_id.delete(0, tk.END)
        self.ent_offset.delete(0, tk.END)

    def _translate_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Thông báo", "Vui lòng chọn 1 dòng địa chỉ trong bảng để dịch!")
            return
        idx = self.tree.index(selected[0])
        self.on_translate_selected(idx)

    def update_table(self, addresses: List[Dict[str, Any]]):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not addresses:
            self.lbl_empty.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        else:
            self.lbl_empty.place_forget()
            for idx, addr in enumerate(addresses, 1):
                if isinstance(addr, dict):
                    sid = addr.get("segment_id", addr.get("seg_id", addr.get("Segment ID", "")))
                    offset = addr.get("offset", addr.get("Offset", ""))
                    access = addr.get("access", addr.get("Access", ""))
                else:
                    sid, offset, access = str(addr), "", ""
                self.tree.insert("", tk.END, values=(idx, sid, offset, access, "Chờ dịch"))
        self.lbl_count.config(text=f"{len(addresses)} ĐỊA CHỈ")


class StepTracePanel(ttk.LabelFrame):
    """Panel 3: Bảng kết quả dịch địa chỉ (Từng bước single-step)"""
    def __init__(self, parent, on_next_step: Callable):
        super().__init__(parent, text="3. BẢNG KẾT QUẢ DỊCH ĐỊA CHỈ", padding=8)
        self.on_next_step = on_next_step
        self._build_ui()

    def _build_ui(self):
        self.lbl_status_badge = tk.Label(
            self, text="Chưa chọn địa chỉ", font=("Segoe UI", 8, "italic"),
            bg="#f8f9fa", fg="#6c757d", padx=6, pady=2
        )
        self.lbl_status_badge.place(relx=0.98, rely=0.0, anchor="ne")

        tree_container = ttk.Frame(self)
        tree_container.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        cols = ("step", "content", "status")
        self.tree = ttk.Treeview(tree_container, columns=cols, show="headings", height=4)
        self.tree.heading("step", text="Bước")
        self.tree.heading("content", text="Nội dung xử lý")
        self.tree.heading("status", text="Trạng thái")

        self.tree.column("step", width=60, anchor=tk.CENTER)
        self.tree.column("content", width=250, anchor=tk.W)
        self.tree.column("status", width=90, anchor=tk.CENTER)

        self.tree.tag_configure("valid", foreground="#0f5132", background="#d1e7dd")
        self.tree.tag_configure("error", foreground="#842029", background="#f8d7da")

        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.lbl_empty = tk.Label(
            self.tree, text="Thêm địa chỉ vào Bảng 2, chọn một dòng và bấm \"Dịch dòng đang chọn\" hoặc \"Bước tiếp\".",
            font=("Segoe UI", 9, "italic"), fg="#6c757d", bg="#ffffff"
        )
        self.lbl_empty.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        btn_bar = ttk.Frame(self, padding=(0, 6, 0, 0))
        btn_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.btn_next = ttk.Button(btn_bar, text="Bước tiếp ➔", command=self.on_next_step)
        self.btn_next.pack(side=tk.LEFT)

    def update_steps(self, steps: List[Dict[str, Any]], current_step_idx: int = -1):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not steps:
            self.lbl_empty.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            self.lbl_status_badge.config(text="Chưa chọn địa chỉ")
        else:
            self.lbl_empty.place_forget()
            display_count = len(steps) if current_step_idx < 0 else min(current_step_idx + 1, len(steps))
            self.lbl_status_badge.config(text=f"Bước {display_count}/{len(steps)}")

            for idx in range(display_count):
                step = steps[idx]
                if isinstance(step, dict):
                    step_num = step.get("step", idx + 1)
                    content = step.get("content", step.get("description", ""))
                    status = str(step.get("status", "")).upper()
                else:
                    step_num, content, status = idx + 1, str(step), "OK"

                tag = "valid" if (status == "OK" or "THÀNH CÔNG" in status) and "INVALID" not in status else "error"
                item_id = self.tree.insert("", tk.END, values=(step_num, content, status), tags=(tag,))

                if idx == display_count - 1:
                    self.tree.selection_set(item_id)
                    self.tree.see(item_id)


class MemoryMapPanel(ttk.LabelFrame):
    """Panel 4: Memory Map - Sơ đồ bộ nhớ Canvas chuẩn"""
    def __init__(self, parent, mem_size: int = 5000):
        super().__init__(parent, text=f"4. MEMORY MAP - SƠ ĐỒ BỘ NHỚ ({mem_size} BYTE)", padding=8)
        self.mem_size = mem_size
        self._segments = None
        self._highlight_addr = None
        self._build_ui()

    def _build_ui(self):
        self.lbl_top_right = tk.Label(
            self, text=f"0 - {self.mem_size} byte", font=("Segoe UI", 8),
            fg="#6c757d"
        )
        self.lbl_top_right.place(relx=0.98, rely=0.0, anchor="ne")

        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 5))

        self.canvas = tk.Canvas(self.canvas_frame, bg="#ffffff", highlightthickness=1, highlightbackground="#ced4da")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self._on_resize)

        legend_frame = ttk.Frame(self)
        legend_frame.pack(fill=tk.X, pady=(2, 4))

        legends = [
            ("#3b82f6", "R-X"),
            ("#f59e0b", "RW-"),
            ("#10b981", "R--"),
            ("#8b5cf6", "RWX"),
            ("#9ca3af", "Khác (-W-, --X)"),
            ("#ffffff", "Free (Trống)"),
        ]

        for color, text in legends:
            item_frame = ttk.Frame(legend_frame)
            item_frame.pack(side=tk.LEFT, padx=3)

            box = tk.Frame(item_frame, bg=color, width=12, height=12, highlightthickness=1, highlightbackground="#94a3b8")
            box.pack(side=tk.LEFT, padx=(0, 2))

            lbl = tk.Label(item_frame, text=text, font=("Segoe UI", 7), fg="#475569")
            lbl.pack(side=tk.LEFT)

        dashed_frame = ttk.Frame(legend_frame)
        dashed_frame.pack(side=tk.LEFT, padx=6)
        lbl_dashed = tk.Label(dashed_frame, text="---- Địa chỉ vật lý vừa dịch", font=("Segoe UI", 7), fg="#dc2626")
        lbl_dashed.pack(side=tk.LEFT)

        self.status_box = tk.Frame(self, bg="#f8fafc", highlightthickness=1, highlightbackground="#cbd5e1", padx=8, pady=4)
        self.status_box.pack(fill=tk.X, side=tk.BOTTOM, pady=(2, 0))

        self.lbl_status = tk.Label(
            self.status_box,
            text=f"TRẠNG THÁI: Bộ nhớ đang trống (Free 0 - {self.mem_size} byte). Hãy thêm Segment ở Bảng 1.",
            font=("Segoe UI", 8, "bold"), fg="#334155", bg="#f8fafc", anchor="w"
        )
        self.lbl_status.pack(fill=tk.X)

    def _on_resize(self, event=None):
        self._draw_map(segments=self._segments, highlight_addr=self._highlight_addr)

    def _draw_map(self, event=None, segments=None, highlight_addr=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10 or self.mem_size <= 0:
            return

        margin_left, margin_right, margin_top, margin_bottom = 50, 50, 25, 25
        rect_x1, rect_y1 = margin_left, margin_top
        rect_x2, rect_y2 = w - margin_right, h - margin_bottom

        if rect_x2 <= rect_x1 or rect_y2 <= rect_y1:
            return

        total_height = rect_y2 - rect_y1

        self.canvas.create_text((rect_x1 + rect_x2) / 2, rect_y1 - 10, text=f"Bộ nhớ vật lý ({self.mem_size} byte)", font=("Segoe UI", 8, "bold"), fill="#475569")
        self.canvas.create_rectangle(rect_x1, rect_y1, rect_x2, rect_y2, outline="#94a3b8", width=1, fill="#ffffff")
        self.canvas.create_text(rect_x1 - 15, rect_y1, text="0", font=("Segoe UI", 8), fill="#475569", anchor="e")
        self.canvas.create_text(rect_x1 - 15, rect_y2, text=str(self.mem_size), font=("Segoe UI", 8), fill="#475569", anchor="e")

        if not segments:
            self.canvas.create_text((rect_x1 + rect_x2) / 2, (rect_y1 + rect_y2) / 2, text=f"Free (0-{self.mem_size})", font=("Segoe UI", 9), fill="#94a3b8")
            self.lbl_status.config(text=f"TRẠNG THÁI: Bộ nhớ đang trống (Free 0 - {self.mem_size} byte). Hãy thêm Segment ở Bảng 1.")
        else:
            color_map = {"R-X": "#3b82f6", "RW-": "#f59e0b", "R--": "#10b981", "RWX": "#8b5cf6"}

            for seg in segments:
                try:
                    if isinstance(seg, dict):
                        base = int(seg.get("base", seg.get("Base", 0)))
                        limit = int(seg.get("limit", seg.get("Limit", 0)))
                        perm = str(seg.get("permission", seg.get("perm", seg.get("Permission", "")))).upper()
                        seg_id = str(seg.get("segment_id", seg.get("seg_id", seg.get("Segment ID", ""))))
                    else:
                        continue

                    y_start = rect_y1 + (base / self.mem_size) * total_height
                    y_end = rect_y1 + ((base + limit) / self.mem_size) * total_height

                    fill_color = color_map.get(perm, "#9ca3af")
                    self.canvas.create_rectangle(rect_x1, y_start, rect_x2, y_end, fill=fill_color, outline="#1e293b", width=1)
                    self.canvas.create_text((rect_x1 + rect_x2) / 2, (y_start + y_end) / 2, text=f"Seg {seg_id} ({base}-{base+limit})", font=("Segoe UI", 8, "bold"), fill="#ffffff")
                except (ValueError, TypeError):
                    continue

            self.lbl_status.config(text=f"TRẠNG THÁI: Đã nạp {len(segments)} Segment vào bộ nhớ vật lý.")

        if highlight_addr is not None and highlight_addr != "-":
            try:
                addr_val = float(str(highlight_addr).strip())
                clamped = max(0.0, min(float(self.mem_size), addr_val))
                y_addr = rect_y1 + (clamped / self.mem_size) * total_height
                label_val = str(int(addr_val)) if addr_val.is_integer() else str(addr_val)

                self.canvas.create_line(
                    rect_x1 - 4, y_addr, rect_x2 + 10, y_addr,
                    fill="#dc2626", width=2
                )
                self.canvas.create_text(
                    rect_x2 + 13, y_addr,
                    text=label_val,
                    font=("Segoe UI", 8, "bold"), fill="#dc2626", anchor="w"
                )
            except (ValueError, TypeError):
                pass

    def update_map(self, segments=None, mem_size=5000, highlight_addr=None):
        self._segments = segments
        self._highlight_addr = highlight_addr
        if mem_size != self.mem_size:
            self.mem_size = mem_size
            self.lbl_top_right.config(text=f"0 - {self.mem_size} byte")
            self.config(text=f"4. MEMORY MAP - SƠ ĐỒ BỘ NHỚ ({self.mem_size} BYTE)")
        self._draw_map(segments=segments, highlight_addr=highlight_addr)


class BatchResultPanel(ttk.LabelFrame):
    """Panel 5: Kết quả tổng hợp (Batch Output)"""
    def __init__(self, parent, on_export_csv: Callable):
        super().__init__(parent, text="5. KẾT QUẢ TỔNG HỢP (BATCH OUTPUT)", padding=8)
        self.on_export_csv = on_export_csv
        self._build_ui()

    def _build_ui(self):
        top_bar = ttk.Frame(self)
        top_bar.pack(fill=tk.X, pady=(0, 5))

        self.lbl_status = tk.Label(
            top_bar, text="Chưa có kết quả", font=("Segoe UI", 8, "italic"),
            fg="#6c757d"
        )
        self.lbl_status.pack(side=tk.LEFT)

        btn_export = ttk.Button(top_bar, text="Xuất kết quả CSV", command=self.on_export_csv)
        btn_export.pack(side=tk.RIGHT)

        tree_container = ttk.Frame(self)
        tree_container.pack(fill=tk.BOTH, expand=True)

        cols = ("stt", "seg_id", "offset", "access", "physical", "status", "reason")
        self.tree = ttk.Treeview(tree_container, columns=cols, show="headings", height=5)
        self.tree.heading("stt", text="STT")
        self.tree.heading("seg_id", text="SEG_ID")
        self.tree.heading("offset", text="OFFSET")
        self.tree.heading("access", text="ACCESS")
        self.tree.heading("physical", text="PHYSICAL")
        self.tree.heading("status", text="STATUS")
        self.tree.heading("reason", text="REASON")

        self.tree.column("stt", width=40, anchor=tk.CENTER)
        self.tree.column("seg_id", width=60, anchor=tk.CENTER)
        self.tree.column("offset", width=60, anchor=tk.CENTER)
        self.tree.column("access", width=60, anchor=tk.CENTER)
        self.tree.column("physical", width=80, anchor=tk.CENTER)
        self.tree.column("status", width=85, anchor=tk.CENTER)
        self.tree.column("reason", width=170, anchor=tk.W)

        self.tree.tag_configure("valid", foreground="#0f5132", background="#d1e7dd")
        self.tree.tag_configure("error", foreground="#842029", background="#f8d7da")

        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.lbl_empty = tk.Label(
            self.tree, text="Chưa có dữ liệu kết quả. Bấm \"Dịch tất cả\" hoặc \"Dịch dòng đang chọn\" để hiển thị.",
            font=("Segoe UI", 9, "italic"), fg="#6c757d", bg="#ffffff"
        )
        self.lbl_empty.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def update_results(self, results: List[Dict[str, Any]]):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not results:
            self.lbl_empty.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            self.lbl_status.config(text="Chưa có kết quả")
        else:
            self.lbl_empty.place_forget()
            self.lbl_status.config(text=f"Đã hoàn thành {len(results)} dòng kết quả")
            for idx, res in enumerate(results, 1):
                if isinstance(res, dict):
                    sid = res.get("segment_id", res.get("seg_id", res.get("SEG_ID", "")))
                    offset = res.get("offset", res.get("OFFSET", ""))
                    access = res.get("access", res.get("ACCESS", ""))
                    physical = res.get("physical_address", res.get("physical", res.get("PHYSICAL", "-")))
                    status = str(res.get("status", res.get("STATUS", ""))).upper()
                    reason = _khong_dau(res.get("reason", res.get("REASON", "")))
                else:
                    sid, offset, access, physical, status, reason = "", "", "", "-", "OK", ""

                tag = "valid" if (status == "OK" or "THÀNH CÔNG" in status) and "INVALID" not in status else "error"
                self.tree.insert("", tk.END, values=(idx, sid, offset, access, physical, status, reason), tags=(tag,))


def create_gui_panels(
    parent,
    cb_open_csv=None,
    cb_translate=None,
    cb_next_step=None,
    cb_export=None,
):
    """Tạo bộ khung tương thích với gui/app.py và trả về (main_frame, tree_seg, tree_res)."""
    main_frame = ttk.Frame(parent, padding=8)

    top_bar = ttk.Frame(main_frame)
    top_bar.pack(fill=tk.X, pady=(0, 6))

    if cb_open_csv:
        ttk.Button(top_bar, text="Mở CSV", command=cb_open_csv).pack(side=tk.LEFT, padx=(0, 6))
    if cb_next_step:
        ttk.Button(top_bar, text="Bước tiếp", command=cb_next_step).pack(side=tk.LEFT, padx=(0, 6))
    if cb_export:
        ttk.Button(top_bar, text="Xuất kết quả", command=cb_export).pack(side=tk.LEFT)

    seg_frame = ttk.LabelFrame(main_frame, text="Bảng phân đoạn", padding=6)
    seg_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))
    tree_seg = ttk.Treeview(seg_frame, columns=("seg_id", "base", "limit", "perm"), show="headings", height=5)
    for col, title in (("seg_id", "SEG_ID"), ("base", "BASE"), ("limit", "LIMIT"), ("perm", "PERM")):
        tree_seg.heading(col, text=title)
        tree_seg.column(col, width=100, anchor=tk.CENTER)
    tree_seg.pack(fill=tk.BOTH, expand=True)

    manual_frame = ttk.LabelFrame(main_frame, text="Dịch địa chỉ thủ công", padding=6)
    manual_frame.pack(fill=tk.X, pady=(0, 6))
    ttk.Label(manual_frame, text="Seg ID:").pack(side=tk.LEFT)
    ent_seg = ttk.Entry(manual_frame, width=8)
    ent_seg.pack(side=tk.LEFT, padx=(2, 8))
    ttk.Label(manual_frame, text="Offset:").pack(side=tk.LEFT)
    ent_off = ttk.Entry(manual_frame, width=10)
    ent_off.pack(side=tk.LEFT, padx=(2, 8))
    ttk.Label(manual_frame, text="Access:").pack(side=tk.LEFT)
    cbo_acc = ttk.Combobox(manual_frame, values=["R", "W", "X"], width=5, state="readonly")
    cbo_acc.set("R")
    cbo_acc.pack(side=tk.LEFT, padx=(2, 8))

    if cb_translate:
        ttk.Button(
            manual_frame,
            text="Dịch",
            command=lambda: cb_translate(ent_seg.get(), ent_off.get(), cbo_acc.get()),
        ).pack(side=tk.LEFT)

    res_frame = ttk.LabelFrame(main_frame, text="Chi tiết từng bước", padding=6)
    res_frame.pack(fill=tk.BOTH, expand=True)
    tree_res = ttk.Treeview(res_frame, columns=("step", "desc", "status"), show="headings", height=6)
    tree_res.heading("step", text="Bước")
    tree_res.heading("desc", text="Mô tả")
    tree_res.heading("status", text="Trạng thái")
    tree_res.column("step", width=80, anchor=tk.CENTER)
    tree_res.column("desc", width=420, anchor=tk.W)
    tree_res.column("status", width=100, anchor=tk.CENTER)
    tree_res.tag_configure("ok", foreground="#0f5132", background="#d1e7dd")
    tree_res.tag_configure("error", foreground="#842029", background="#f8d7da")
    tree_res.pack(fill=tk.BOTH, expand=True)

    return main_frame, tree_seg, tree_res
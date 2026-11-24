"""
gui.py - Cửa sổ chính MainWindow & Menu Bar (TV4 - Trần Thị Ngọc Giàu)
- Giữ giao diện 5 panel, tô màu trạng thái, đi từng bước ('Bước tiếp ➔') và làm mới dữ liệu.
- Không viết logic dịch địa chỉ trực tiếp trong GUI; mọi xử lý nạp/dịch/xuất đều gọi qua controller.
"""

import csv
import unicodedata
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from gui.gui_panels import (
    SegmentPanel,
    LogicalAddressPanel,
    StepTracePanel,
    MemoryMapPanel,
    BatchResultPanel,
)


def _khong_dau(text: str) -> str:
    if not text:
        return ""
    norm = unicodedata.normalize("NFD", str(text))
    no_marks = "".join(ch for ch in norm if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", no_marks).replace("đ", "d").replace("Đ", "D")


def _status_text(status_obj) -> str:
    if hasattr(status_obj, "value"):
        return str(status_obj.value)
    return str(status_obj or "")


def _extract_rows(source):
    """Chuyển dữ liệu từ controller (DataFrame / SegmentTable / list / object) thành list[dict]."""
    if source is None:
        return []
    if hasattr(source, "to_dict") and hasattr(source, "empty"):
        return [] if source.empty else source.to_dict(orient="records")
    if hasattr(source, "segments") and isinstance(source.segments, list):
        return _extract_rows(source.segments)
    if isinstance(source, (list, tuple)):
        rows = []
        for item in source:
            if isinstance(item, dict):
                rows.append(item)
            elif hasattr(item, "__dict__"):
                data = dict(item.__dict__)
                if "perm" in data and "permission" not in data:
                    data["permission"] = data["perm"]
                rows.append(data)
        return rows
    return []


def _read_csv_rows(csv_path: str) -> list[dict]:
    path = Path(csv_path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        lines = [line for line in f if line.strip() and not line.strip().lower().startswith("sep=")]
    if not lines:
        return []
    sample = "".join(lines[:5])
    delimiter = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.DictReader(lines, delimiter=delimiter)
    rows = []
    for raw in reader:
        cleaned = {str(k).strip().lower(): (str(v).strip() if v is not None else "") for k, v in raw.items() if k is not None}
        if any(cleaned.values()):
            rows.append(cleaned)
    return rows


class MainWindow(tk.Tk):
    def __init__(self, controller=None, mem_size: int = 5000):
        super().__init__()
        if controller is None:
            from core.app import SegmentationController
            controller = SegmentationController(mem_size=mem_size)

        self.controller = controller
        self.mem_size = getattr(controller, "mem_size", mem_size)

        self._seg_csv_path = None
        self._addr_csv_path = None
        self._ui_segments = []
        self._ui_addresses = []
        self._raw_results = []
        self._ui_results = []
        self._ui_steps = []
        self._step_index = -1
        self._current_res_obj = None
        self._highlight_addr = None

        self._setup_style()
        self.title("OS_MEM_12 - Segmentation và địa chỉ logic")
        self.geometry("1280x760")
        self.minsize(1024, 600)

        self._build_menu()
        self._build_top_bar()
        self._build_layout()
        self.refresh_ui()

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#ffffff",
            foreground="#000000",
            fieldbackground="#ffffff",
            font=("Segoe UI", 9),
        )
        style.map(
            "Treeview",
            background=[("selected", "#0d6efd")],
            foreground=[("selected", "#ffffff")],
        )

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Mở Segment CSV...", command=self._on_load_segment_csv)
        file_menu.add_command(label="Mở Địa chỉ CSV...", command=self._on_load_address_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Xuất kết quả CSV...", command=self._on_export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.quit)
        menubar.add_cascade(label="Tệp tin", menu=file_menu)

        action_menu = tk.Menu(menubar, tearoff=0)
        action_menu.add_command(label="Dịch dòng đang chọn", command=lambda: self._on_translate_selected(0))
        action_menu.add_command(label="Dịch tất cả", command=self._on_translate_all)
        action_menu.add_command(label="Bước tiếp ➔", command=self._on_next_step)
        action_menu.add_separator()
        action_menu.add_command(label="Làm mới toàn bộ", command=self._on_reset_all)
        menubar.add_cascade(label="Thao tác", menu=action_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Hướng dẫn sử dụng", command=self._show_help)
        help_menu.add_command(label="Giới thiệu (Nhóm OS_MEM_12)", command=self._show_about)
        menubar.add_cascade(label="Trợ giúp", menu=help_menu)

        self.config(menu=menubar)

    def _build_top_bar(self):
        top_bar = tk.Frame(self, bg="#0d1b2a", padx=12, pady=6)
        top_bar.pack(fill=tk.X, side=tk.TOP)

        tk.Label(
            top_bar,
            text="🟢 OS_MEM_12 - Segmentation và địa chỉ logic",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg="#0d1b2a",
        ).pack(side=tk.LEFT)

        tk.Button(
            top_bar,
            text="Làm mới toàn bộ",
            command=self._on_reset_all,
            bg="#0d6efd",
            fg="#ffffff",
            activebackground="#0b5ed7",
            activeforeground="#ffffff",
            font=("Segoe UI", 8, "bold"),
            bd=0,
            cursor="hand2",
            padx=8,
            pady=2,
        ).pack(side=tk.RIGHT, padx=(10, 0))

        self.lbl_mem_info = tk.Label(
            top_bar,
            text=f"Bộ nhớ vật lý: 0 - {self.mem_size} byte",
            font=("Segoe UI", 9),
            fg="#e0e1dd",
            bg="#0d1b2a",
        )
        self.lbl_mem_info.pack(side=tk.RIGHT)

    def _build_layout(self):
        main_frame = ttk.Frame(self, padding=8)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_column = ttk.Frame(main_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        right_column = ttk.Frame(main_frame)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))

        self.segment_panel = SegmentPanel(
            left_column,
            on_add_segment=self._on_add_segment,
            on_load_csv=self._on_load_segment_csv,
            on_clear=self._on_clear_segments,
        )
        self.segment_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        self.address_panel = LogicalAddressPanel(
            left_column,
            on_add_address=self._on_add_address,
            on_load_csv=self._on_load_address_csv,
            on_clear=self._on_clear_addresses,
            on_translate_selected=self._on_translate_selected,
            on_translate_all=self._on_translate_all,
        )
        self.address_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        self.step_trace_panel = StepTracePanel(
            left_column,
            on_next_step=self._on_next_step,
        )
        self.step_trace_panel.pack(fill=tk.BOTH, expand=True)

        self.memory_map_panel = MemoryMapPanel(right_column, mem_size=self.mem_size)
        self.memory_map_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        self.batch_result_panel = BatchResultPanel(
            right_column,
            on_export_csv=self._on_export_csv,
        )
        self.batch_result_panel.pack(fill=tk.BOTH, expand=True)

    # --- Lớp đồng bộ hiển thị với controller ---

    def _controller_ready(self) -> bool:
        return bool(self.controller and getattr(self.controller, "_loaded", False))

    def _current_segments(self):
        if self._ui_segments:
            return self._ui_segments
        if self._controller_ready():
            rows = _extract_rows(getattr(self.controller, "segment_table", None))
            if rows:
                return rows
            df_rows = _extract_rows(getattr(self.controller, "segment_df", None))
            if df_rows:
                return df_rows
        return []

    def _current_addresses(self):
        if self._ui_addresses:
            return self._ui_addresses
        if self._controller_ready():
            df_rows = _extract_rows(getattr(self.controller, "address_df", None))
            if df_rows:
                return df_rows
        return []

    @staticmethod
    def _to_int_if_possible(value):
        try:
            return int(str(value).strip())
        except Exception:
            return value

    def _format_result_row(self, result_obj) -> dict:
        sid = getattr(result_obj, "seg_id", "")
        offset = getattr(result_obj, "offset", "")
        access = getattr(result_obj, "access", "")
        physical = getattr(result_obj, "physical", None)
        status = _status_text(getattr(result_obj, "status", ""))
        raw_reason = getattr(result_obj, "reason", "") or ("Thanh cong" if status == "OK" else "")
        reason = _khong_dau(raw_reason)
        return {
            "seg_id": "" if sid is None else sid,
            "offset": "" if offset is None else offset,
            "access": "" if access is None else access,
            "physical": "-" if physical is None else physical,
            "status": status,
            "reason": reason,
        }

    def _format_steps(self, result_obj) -> list[dict]:
        raw_steps = getattr(result_obj, "steps", None) or []
        formatted = []
        for idx, st in enumerate(raw_steps, start=1):
            desc = getattr(st, "description", "")
            ok = bool(getattr(st, "ok", False))
            formatted.append({
                "step": idx,
                "content": str(desc),
                "status": "OK" if ok else "INVALID",
            })
        return formatted

    def _sync_highlight_for_current_step(self):
        """Chỉ hiện gạch đỏ khi bước hiện tại đã đi tới bước có địa chỉ vật lý hợp lệ."""
        res_obj = self._current_res_obj
        if res_obj is None or self._step_index < 0 or not self._ui_steps:
            self._highlight_addr = None
            return

        status = _status_text(getattr(res_obj, "status", ""))
        phys = getattr(res_obj, "physical", None)
        if status != "OK" or phys is None:
            self._highlight_addr = None
            return

        is_last_step = self._step_index >= len(self._ui_steps) - 1
        cur_desc = str(self._ui_steps[self._step_index].get("content", "")).lower()
        has_phys_step = (str(phys) in cur_desc) or ("vật lý" in cur_desc) or ("vat ly" in cur_desc) or ("base" in cur_desc and "+" in cur_desc)

        if is_last_step or has_phys_step:
            self._highlight_addr = phys
        else:
            self._highlight_addr = None

    def _sync_controller_table_from_ui_segments(self):
        if not (self.controller and hasattr(self.controller, "segment_table")):
            return
        try:
            from core.result_types import Segment, SegmentTable
            table = SegmentTable(mem_size=self.mem_size)
            for seg in self._ui_segments:
                sid = seg.get("seg_id", seg.get("segment_id", ""))
                base = seg.get("base", "")
                limit = seg.get("limit", "")
                perm = seg.get("perm", seg.get("permission", ""))
                if sid != "" and base != "" and limit != "":
                    table.add(Segment(seg_id=int(sid), base=int(base), limit=int(limit), perm=str(perm)))
            self.controller.segment_table = table
            if len(table) > 0:
                setattr(self.controller, "_loaded", True)
        except Exception:
            pass

    def _sync_loaded_pair(self, seg_path: str, addr_path: str) -> bool:
        if not (self.controller and hasattr(self.controller, "load_files")):
            return False
        try:
            seg_df, addr_df = self.controller.load_files(seg_path, addr_path)
            if addr_df is None or getattr(addr_df, "empty", False):
                raise ValueError("File địa chỉ CSV không có dòng nào để xử lý.")
            self._ui_segments = _extract_rows(seg_df)
            self._ui_addresses = _extract_rows(addr_df)
            self._raw_results.clear()
            self._ui_results.clear()
            self._ui_steps.clear()
            self._step_index = -1
            self._current_res_obj = None
            self._highlight_addr = None
            self.refresh_ui()
            return True
        except Exception as exc:
            messagebox.showerror("Lỗi nạp dữ liệu CSV", str(exc), parent=self)
            return False

    # --- Sự kiện giao diện gọi controller ---

    def _on_load_segment_csv(self):
        seg_path = filedialog.askopenfilename(
            parent=self,
            title="Chọn file CSV bảng phân đoạn (segments.csv)",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if not seg_path:
            return

        self._seg_csv_path = seg_path
        try:
            rows = _read_csv_rows(seg_path)
            normalized = []
            for r in rows:
                sid = r.get("seg_id", r.get("segment_id", r.get("id", "")))
                base = r.get("base", "")
                limit = r.get("limit", "")
                perm = r.get("perm", r.get("permission", ""))
                normalized.append({
                    "seg_id": sid,
                    "segment_id": sid,
                    "base": base,
                    "limit": limit,
                    "perm": perm,
                    "permission": perm,
                })
            self._ui_segments = normalized
            self._sync_controller_table_from_ui_segments()
            if self._addr_csv_path:
                self._sync_loaded_pair(self._seg_csv_path, self._addr_csv_path)
            else:
                self._raw_results.clear()
                self._ui_results.clear()
                self._ui_steps.clear()
                self._step_index = -1
                self._current_res_obj = None
                self._highlight_addr = None
                self.refresh_ui()
        except Exception as exc:
            messagebox.showerror("Lỗi đọc Segment CSV", str(exc), parent=self)

    def _on_load_address_csv(self):
        addr_path = filedialog.askopenfilename(
            parent=self,
            title="Chọn file CSV địa chỉ logic (addresses.csv)",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if not addr_path:
            return

        self._addr_csv_path = addr_path
        try:
            rows = _read_csv_rows(addr_path)
            normalized = []
            for r in rows:
                sid = r.get("seg_id", r.get("segment_id", ""))
                offset = r.get("offset", "")
                access = r.get("access", "R")
                normalized.append({
                    "seg_id": sid,
                    "segment_id": sid,
                    "offset": offset,
                    "access": access,
                })
            self._ui_addresses = normalized
            if self._seg_csv_path:
                self._sync_loaded_pair(self._seg_csv_path, self._addr_csv_path)
            else:
                self._raw_results.clear()
                self._ui_results.clear()
                self._ui_steps.clear()
                self._step_index = -1
                self._current_res_obj = None
                self._highlight_addr = None
                self.refresh_ui()
        except Exception as exc:
            messagebox.showerror("Lỗi đọc Địa chỉ CSV", str(exc), parent=self)

    def _on_add_segment(self, seg_id, base, limit, perm):
        if not (self.controller and hasattr(self.controller, "segment_table")):
            return
        try:
            from core.result_types import Segment
            self.controller.segment_table.add(
                Segment(
                    seg_id=int(seg_id),
                    base=int(base),
                    limit=int(limit),
                    perm=str(perm),
                )
            )
            self._ui_segments = _extract_rows(self.controller.segment_table)
            setattr(self.controller, "_loaded", True)
            self.refresh_ui()
        except Exception as exc:
            messagebox.showerror("Lỗi thêm Segment", str(exc), parent=self)

    def _on_add_address(self, seg_id, offset, access):
        self._ui_addresses.append({
            "segment_id": seg_id,
            "seg_id": seg_id,
            "offset": offset,
            "access": access,
        })
        self.refresh_ui()

    def _on_clear_segments(self):
        self._seg_csv_path = None
        self._ui_segments.clear()
        self._raw_results.clear()
        self._ui_results.clear()
        self._ui_steps.clear()
        self._step_index = -1
        self._current_res_obj = None
        self._highlight_addr = None
        if self.controller:
            try:
                from core.result_types import SegmentTable
                self.controller.segment_table = SegmentTable(mem_size=self.mem_size)
                self.controller.segment_df = None
                self.controller._loaded = False
            except Exception:
                pass
        self.refresh_ui()

    def _on_clear_addresses(self):
        self._addr_csv_path = None
        self._ui_addresses.clear()
        self._raw_results.clear()
        self._ui_results.clear()
        self._ui_steps.clear()
        self._step_index = -1
        self._current_res_obj = None
        self._highlight_addr = None
        if self.controller:
            self.controller.address_df = None
        self.refresh_ui()

    def _on_reset_all(self):
        self._seg_csv_path = None
        self._addr_csv_path = None
        self._ui_segments.clear()
        self._ui_addresses.clear()
        self._raw_results.clear()
        self._ui_results.clear()
        self._ui_steps.clear()
        self._step_index = -1
        self._current_res_obj = None
        self._highlight_addr = None
        if self.controller:
            try:
                from core.result_types import SegmentTable
                self.controller.segment_table = SegmentTable(mem_size=self.mem_size)
                self.controller.segment_df = None
                self.controller.address_df = None
                self.controller._loaded = False
            except Exception:
                pass
        self.refresh_ui()

    def _selected_address_index(self, default_idx: int, total: int) -> int:
        try:
            selected = self.address_panel.tree.selection()
            if selected:
                return self.address_panel.tree.index(selected[0])
        except Exception:
            pass
        return default_idx if 0 <= default_idx < total else 0

    def _on_translate_selected(self, idx: int):
        addresses = self._current_addresses()
        if not addresses:
            messagebox.showinfo("Thông báo", "Vui lòng thêm hoặc mở file CSV địa chỉ trước khi dịch!", parent=self)
            return

        if not (self.controller and hasattr(self.controller, "translate_one")):
            messagebox.showwarning("Thiếu Controller", "Controller chưa hỗ trợ translate_one.", parent=self)
            return

        target = addresses[self._selected_address_index(idx, len(addresses))]
        sid = self._to_int_if_possible(target.get("segment_id", target.get("seg_id", target.get("Segment ID", ""))))
        offset = self._to_int_if_possible(target.get("offset", target.get("Offset", 0)))
        access = str(target.get("access", target.get("Access", "R"))).strip().upper()

        try:
            res_obj = self.controller.translate_one(sid, offset, access)
            self._current_res_obj = res_obj
            self._ui_steps = self._format_steps(res_obj)
            self._step_index = 0 if self._ui_steps else -1
            if not self._raw_results:
                self._raw_results = [res_obj]
                self._ui_results = [self._format_result_row(res_obj)]
            self._sync_highlight_for_current_step()
            self.refresh_ui()
        except Exception as exc:
            messagebox.showerror("Lỗi dịch địa chỉ", str(exc), parent=self)

    def _on_translate_all(self):
        addresses = self._current_addresses()
        if not addresses:
            messagebox.showinfo("Thông báo", "Vui lòng thêm hoặc mở file CSV địa chỉ trước khi dịch!", parent=self)
            return

        if not (self.controller and hasattr(self.controller, "translate_batch")):
            messagebox.showwarning("Thiếu Controller", "Controller chưa hỗ trợ translate_batch.", parent=self)
            return

        try:
            res_list = self.controller.translate_batch()
            self._raw_results = list(res_list)
            self._ui_results = [self._format_result_row(item) for item in res_list]
            if res_list:
                self._current_res_obj = res_list[0]
                self._ui_steps = self._format_steps(res_list[0])
                self._step_index = len(self._ui_steps) - 1
            else:
                self._current_res_obj = None
                self._ui_steps = []
                self._step_index = -1
            self._sync_highlight_for_current_step()
            self.refresh_ui()
        except Exception as exc:
            messagebox.showerror("Lỗi dịch toàn bộ", str(exc), parent=self)

    def _on_next_step(self):
        if not self._current_addresses():
            messagebox.showinfo("Thông báo", "Vui lòng nạp địa chỉ trước khi bấm Bước tiếp!", parent=self)
            return

        if not self._ui_steps:
            self._on_translate_selected(0)
            return

        if self._step_index >= len(self._ui_steps) - 1:
            messagebox.showinfo(
                "Hoàn thành mô phỏng",
                f"Đã thực hiện xong toàn bộ {len(self._ui_steps)} bước dịch cho địa chỉ này!\n"
                "Chọn dòng địa chỉ khác hoặc bấm 'Làm mới toàn bộ' để mô phỏng địa chỉ khác.",
                parent=self,
            )
            return

        self._step_index += 1
        self._sync_highlight_for_current_step()
        self.refresh_ui()

    @staticmethod
    def _prepend_sep_to_csv(path_obj):
        p = Path(path_obj)
        if not p.exists():
            return
        content = p.read_text(encoding="utf-8-sig")
        if not content.startswith("sep=,"):
            p.write_text("sep=,\n" + content, encoding="utf-8-sig")

    def _on_export_csv(self):
        if not self._raw_results:
            messagebox.showinfo("Thông báo", "Chưa có dữ liệu kết quả để xuất CSV!", parent=self)
            return

        if not (self.controller and hasattr(self.controller, "export_trace")):
            messagebox.showwarning("Thiếu Controller", "Controller chưa hỗ trợ export_trace.", parent=self)
            return

        filepath = filedialog.asksaveasfilename(
            parent=self,
            title="Xuất kết quả CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not filepath:
            return

        try:
            summary_path, steps_path = self.controller.export_trace(self._raw_results, filepath)
            self._prepend_sep_to_csv(summary_path)
            self._prepend_sep_to_csv(steps_path)
            messagebox.showinfo(
                "Thành công",
                f"Đã xuất kết quả:\n{summary_path}\nTrace từng bước:\n{steps_path}",
                parent=self,
            )
        except Exception as exc:
            messagebox.showerror("Lỗi xuất file", str(exc), parent=self)

    def _show_help(self):
        messagebox.showinfo(
            "Hướng dẫn",
            "1. Nhập hoặc mở CSV Bảng phân đoạn (Segment Table).\n"
            "2. Nhập hoặc mở CSV Bảng địa chỉ logic.\n"
            "3. Nhấn 'Dịch dòng đang chọn' hoặc 'Dịch tất cả' để mô phỏng chuyển đổi địa chỉ.\n"
            "4. Quan sát từng bước chuyển đổi và sơ đồ bộ nhớ.",
            parent=self,
        )

    def _show_about(self):
        messagebox.showinfo(
            "Giới thiệu",
            "Chương trình Mô phỏng Segmentation và Địa chỉ logic\n"
            "Môn học: Hệ điều hành - UTH\n"
            "Nhóm thực hiện: OS_MEM_12",
            parent=self,
        )

    def refresh_ui(self):
        segments = self._current_segments()
        addresses = self._current_addresses()

        self.segment_panel.update_table(segments)
        self.address_panel.update_table(addresses)
        self.step_trace_panel.update_steps(self._ui_steps, self._step_index)
        self.batch_result_panel.update_results(self._ui_results)

        if hasattr(self, "memory_map_panel") and hasattr(self.memory_map_panel, "update_map"):
            self.memory_map_panel.update_map(segments, self.mem_size, highlight_addr=self._highlight_addr)


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
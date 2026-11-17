from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# Cho phép chạy bằng `python src/gui/app.py` hoặc import từ thư mục src.
SRC_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.app import SegmentationController  # noqa: E402
from core.result_types import Status, TranslationResult  # noqa: E402
from core.validator import validate_table  # noqa: E402
from gui.gui_panels import create_gui_panels  # noqa: E402
from gui.memory_map import draw_memory_map  # noqa: E402


class SegmentationApp:
    """Giao diện Tkinter gọi controller để xử lý nghiệp vụ."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OS_MEM_12 - Segmentation và địa chỉ logic")
        self.root.geometry("1100x850")
        self.root.minsize(850, 650)

        self.controller = SegmentationController()
        self.segment_table = self.controller.segment_table

        self.segment_df = None
        self.address_df = None
        self.segment_path: Path | None = None
        self.address_path: Path | None = None
        self.results: list[TranslationResult] = []
        self.current_result_index = 0
        self.visible_step_count = 0

        self.main_frame, self.tree_seg, self.tree_res = create_gui_panels(
            parent=root,
            cb_open_csv=self.open_csv_files,
            cb_translate=self.translate_manual,
            cb_next_step=self.show_next_step,
            cb_export=self.export_trace,
        )
        self.main_frame.pack(fill="both", expand=True)

        controls = ttk.Frame(root, padding=(10, 0, 10, 4))
        controls.pack(fill="x")

        self.batch_button = ttk.Button(
            controls,
            text="Dịch toàn bộ addresses.csv",
            command=self.translate_batch,
        )
        self.batch_button.pack(side="left")

        self.data_status = ttk.Label(controls, text="Chưa tải dữ liệu CSV")
        self.data_status.pack(side="left", padx=12)

        summary_frame = ttk.LabelFrame(root, text="Kết quả tổng hợp", padding=6)
        summary_frame.pack(fill="x", padx=10, pady=(0, 6))

        summary_columns = (
            "seg_id",
            "offset",
            "access",
            "physical",
            "status",
            "reason",
        )
        self.tree_summary = ttk.Treeview(
            summary_frame,
            columns=summary_columns,
            show="headings",
            height=5,
        )

        for column, title, width in (
            ("seg_id", "SEG_ID", 75),
            ("offset", "OFFSET", 85),
            ("access", "ACCESS", 75),
            ("physical", "PHYSICAL", 90),
            ("status", "STATUS", 190),
            ("reason", "REASON", 430),
        ):
            self.tree_summary.heading(column, text=title)
            self.tree_summary.column(
                column,
                width=width,
                anchor="w" if column == "reason" else "center",
            )

        self.tree_summary.pack(fill="x", expand=True)

        self.canvas = tk.Canvas(
            root,
            width=900,
            height=300,
            bg="white",
            highlightthickness=1,
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.root.after_idle(self.redraw_memory_map)

    def open_csv_files(self) -> None:
        """Cho người dùng chọn CSV rồi nhờ controller nạp và kiểm tra dữ liệu."""
        csv_types = [("CSV files", "*.csv"), ("All files", "*.*")]

        segments_name = filedialog.askopenfilename(
            parent=self.root,
            title="Chọn segments.csv",
            filetypes=csv_types,
            initialdir=str(PROJECT_ROOT / "input"),
        )
        if not segments_name:
            return

        addresses_name = filedialog.askopenfilename(
            parent=self.root,
            title="Chọn addresses.csv",
            filetypes=csv_types,
            initialdir=str(Path(segments_name).parent),
        )
        if not addresses_name:
            return

        try:
            segment_df, address_df = self.controller.load_files(
                segments_name,
                addresses_name,
            )
            if address_df.empty:
                raise ValueError("addresses.csv không có dòng địa chỉ nào để xử lý.")
        except Exception as exc:
            messagebox.showerror(
                "Không tải được dữ liệu",
                str(exc),
                parent=self.root,
            )
            return

        self.segment_df = segment_df
        self.address_df = address_df
        self.segment_table = self.controller.segment_table
        self.segment_path = Path(segments_name)
        self.address_path = Path(addresses_name)

        self.results.clear()
        self.current_result_index = 0
        self.visible_step_count = 0

        self._refresh_segment_table()
        self._clear_result_table()
        self._refresh_summary_table()

        self.data_status.configure(
            text=f"Đã tải {len(segment_df)} segment, {len(address_df)} địa chỉ"
        )
        self.redraw_memory_map()

        messagebox.showinfo(
            "Đã tải dữ liệu",
            "Hai file CSV đã được tải và kiểm tra.",
            parent=self.root,
        )

    def _refresh_segment_table(self) -> None:
        for item in self.tree_seg.get_children():
            self.tree_seg.delete(item)

        if self.segment_df is None:
            return

        for row in self.segment_df.itertuples(index=False):
            self.tree_seg.insert(
                "",
                "end",
                values=(row.seg_id, row.base, row.limit, row.perm),
            )

    def _clear_result_table(self) -> None:
        for item in self.tree_res.get_children():
            self.tree_res.delete(item)

    def translate_manual(
        self,
        seg_id_text: str,
        offset_text: str,
        access_text: str,
    ) -> None:
        """Dịch địa chỉ do người dùng nhập trên giao diện."""
        if len(self.segment_table) == 0:
            messagebox.showwarning(
                "Chưa có dữ liệu",
                "Hãy tải segments.csv trước.",
                parent=self.root,
            )
            return

        seg_id = self._parse_integer_or_original(seg_id_text)
        offset = self._parse_integer_or_original(offset_text)

        result = self.controller.translate_one(
            seg_id,
            offset,
            access_text.strip().upper(),
        )
        self._set_results([result])

    @staticmethod
    def _parse_integer_or_original(value: str):
        """Đổi chuỗi thành số nguyên; giữ nguyên chuỗi sai để controller báo lỗi."""
        try:
            return int(value.strip())
        except (AttributeError, ValueError):
            return value

    def translate_batch(self) -> None:
        """Nhờ controller dịch toàn bộ các dòng đã nạp từ addresses.csv."""
        if self.address_df is None or self.segment_df is None:
            messagebox.showwarning(
                "Chưa có dữ liệu",
                "Hãy mở hai file CSV trước.",
                parent=self.root,
            )
            return

        try:
            results = self.controller.translate_batch()
        except (RuntimeError, ValueError) as exc:
            messagebox.showerror(
                "Không dịch được dữ liệu",
                str(exc),
                parent=self.root,
            )
            return

        self._set_results(results)
        self.data_status.configure(text=f"Đã dịch {len(results)} địa chỉ")

    def _set_results(self, results: list[TranslationResult]) -> None:
        self.results = results
        self.current_result_index = 0
        self.visible_step_count = 0
        self._refresh_summary_table()

        if not results:
            self._clear_result_table()
            return

        self._render_current_result()

    def _refresh_summary_table(self) -> None:
        for item in self.tree_summary.get_children():
            self.tree_summary.delete(item)

        for result in self.results:
            status = (
                result.status.value
                if hasattr(result.status, "value")
                else result.status
            )
            reason = result.reason or (
                "Dịch thành công" if status == Status.OK.value else ""
            )

            self.tree_summary.insert(
                "",
                "end",
                values=(
                    result.seg_id,
                    result.offset,
                    result.access,
                    result.physical if result.physical is not None else "",
                    status,
                    reason,
                ),
            )

    def show_next_step(self) -> None:
        """Hiện bước tiếp theo, sau đó chuyển sang địa chỉ kế tiếp."""
        if not self.results:
            messagebox.showinfo(
                "Chưa có kết quả",
                "Hãy dịch một địa chỉ hoặc dịch CSV trước.",
                parent=self.root,
            )
            return

        current = self.results[self.current_result_index]

        if self.visible_step_count < len(current.steps):
            self.visible_step_count += 1
        elif self.current_result_index + 1 < len(self.results):
            self.current_result_index += 1
            self.visible_step_count = min(
                1,
                len(self.results[self.current_result_index].steps),
            )
        else:
            messagebox.showinfo(
                "Hoàn tất",
                "Đã xem hết các bước và địa chỉ.",
                parent=self.root,
            )
            return

        self._render_current_result()

    def _render_current_result(self) -> None:
        result = self.results[self.current_result_index]
        self._clear_result_table()

        for index, step in enumerate(
            result.steps[: self.visible_step_count],
            start=1,
        ):
            tag = "ok" if step.ok else "error"
            self.tree_res.insert(
                "",
                "end",
                values=(
                    index,
                    step.description,
                    "Hợp lệ" if step.ok else "Lỗi",
                ),
                tags=(tag,),
            )

        if self.visible_step_count >= len(result.steps):
            status = (
                result.status.value
                if hasattr(result.status, "value")
                else str(result.status)
            )
            tag = "ok" if status == Status.OK.value else "error"

            self.tree_res.insert(
                "",
                "end",
                values=(
                    "KẾT LUẬN",
                    result.reason or "Dịch thành công",
                    status,
                ),
                tags=(tag,),
            )

        if result.status == Status.OK:
            self.redraw_memory_map(highlight_addr=result.physical)
        else:
            status = (
                result.status.value
                if hasattr(result.status, "value")
                else str(result.status)
            )
            self.redraw_memory_map(
                fault_msg=result.reason or status,
            )

    def redraw_memory_map(self, highlight_addr=None, fault_msg=None) -> None:
        """Vẽ sơ đồ bộ nhớ; phần vẽ vẫn thuộc giao diện."""
        if not hasattr(self, "canvas"):
            return

        issues = validate_table(self.segment_table)
        draw_memory_map(
            self.canvas,
            self.segment_table,
            self.segment_table.mem_size,
            highlight_addr=highlight_addr,
            fault_msg=fault_msg,
            issues=issues,
        )

    def export_trace(self) -> None:
        """Chọn vị trí lưu trên GUI, rồi nhờ controller xuất các file trace."""
        if not self.results:
            messagebox.showinfo(
                "Chưa có kết quả",
                "Chưa có kết quả nào để xuất.",
                parent=self.root,
            )
            return

        default_path = PROJECT_ROOT / "output" / "trace.csv"
        selected = filedialog.asksaveasfilename(
            parent=self.root,
            title="Xuất trace.csv",
            initialdir=str(default_path.parent),
            initialfile=default_path.name,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not selected:
            return

        try:
            summary_path, steps_path = self.controller.export_trace(
                self.results,
                selected,
            )
        except (OSError, ValueError) as exc:
            messagebox.showerror(
                "Không xuất được CSV",
                str(exc),
                parent=self.root,
            )
            return

        messagebox.showinfo(
            "Đã xuất kết quả",
            f"Đã ghi {len(self.results)} kết quả:\n"
            f"{summary_path}\n"
            f"Trace từng bước:\n{steps_path}",
            parent=self.root,
        )


def run_app() -> None:
    """Tạo và chạy ứng dụng Tkinter."""
    root = tk.Tk()
    SegmentationApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()

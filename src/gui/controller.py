import unicodedata
from pathlib import Path
from tkinter import filedialog, messagebox

from core.app import SegmentationController as CoreController


def _khong_dau(text) -> str:
    if not text:
        return ""
    norm = unicodedata.normalize("NFD", str(text))
    no_marks = "".join(ch for ch in norm if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", no_marks).replace("đ", "d").replace("Đ", "D")


class SegmentationController:
    """Kết nối giao diện TV4 với Controller xử lý của Core."""

    def __init__(self):
        self.core = CoreController()
        self.segment_table = self.core.segment_table
        self.results = []
        self.visible_step_count = 0

    # ==================== MỞ HAI FILE CSV ====================

    def handle_open_csv(self, window):

        segments_path = filedialog.askopenfilename(
            parent=window,
            title="Chọn segments.csv",
            filetypes=[("CSV Files", "*.csv")]
        )

        if not segments_path:
            return

        addresses_path = filedialog.askopenfilename(
            parent=window,
            title="Chọn addresses.csv",
            filetypes=[("CSV Files", "*.csv")]
        )

        if not addresses_path:
            return

        try:
            segment_df, address_df = self.core.load_files(
                segments_path,
                addresses_path
            )

            if address_df.empty:
                raise ValueError(
                    "addresses.csv không có dữ liệu."
                )

        except Exception as exc:
            messagebox.showerror(
                "Lỗi CSV",
                str(exc),
                parent=window
            )
            return

        self.segment_table = self.core.segment_table
        self.results = []
        self.visible_step_count = 0

        # Hiển thị Segment Table
        for item in window.tree_seg.get_children():
            window.tree_seg.delete(item)

        for row in segment_df.itertuples(index=False):
            window.tree_seg.insert(
                "",
                "end",
                values=(
                    row.seg_id,
                    row.base,
                    row.limit,
                    row.perm
                )
            )

        # Xóa kết quả cũ
        self._clear_results(window)

        # Cập nhật bản đồ bộ nhớ
        window.update_memory_map(self.segment_table)

        messagebox.showinfo(
            "Thành công",
            f"Đã tải {len(segment_df)} segment "
            f"và {len(address_df)} địa chỉ.",
            parent=window
        )

    # ==================== DỊCH MỘT ĐỊA CHỈ ====================

    def handle_translate(self, seg, offset, access, window):

        if len(self.segment_table) == 0:
            messagebox.showwarning(
                "Chưa có dữ liệu",
                "Hãy mở hai file CSV trước.",
                parent=window
            )
            return

        try:
            seg_id = int(seg.strip())
            offset_value = int(offset.strip())

            result = self.core.translate_one(
                seg_id,
                offset_value,
                access.strip().upper()
            )

            self.results = [result]
            self.visible_step_count = min(
                1,
                len(result.steps)
            )

            self._display_result(window)

        except (ValueError, TypeError, RuntimeError) as exc:
            messagebox.showerror(
                "Lỗi dịch địa chỉ",
                str(exc),
                parent=window
            )

    # ==================== DỊCH TOÀN BỘ CSV ====================

    def handle_translate_batch(self, window):

        try:
            results = self.core.translate_batch()

            self.results = results
            self.visible_step_count = min(
                1,
                len(results[0].steps) if results else 0
            )

            self._display_result(window)

            messagebox.showinfo(
                "Hoàn thành",
                f"Đã xử lý {len(results)} địa chỉ.",
                parent=window
            )

        except (ValueError, RuntimeError) as exc:
            messagebox.showerror(
                "Lỗi xử lý",
                str(exc),
                parent=window
            )

    # ==================== HIỂN THỊ KẾT QUẢ ====================

    def _clear_results(self, window):

        for item in window.tree_res.get_children():
            window.tree_res.delete(item)

    def _display_result(self, window):

        self._clear_results(window)

        if not self.results:
            return

        result = self.results[0]

        for index, step in enumerate(
            result.steps[:self.visible_step_count],
            start=1
        ):
            window.tree_res.insert(
                "",
                "end",
                values=(
                    f"Bước {index}",
                    step.description,
                    "Hợp lệ" if step.ok else "Lỗi"
                ),
                tags=(
                    "ok" if step.ok else "error",
                )
            )

        if self.visible_step_count >= len(result.steps):

            status = result.status.value

            reason = _khong_dau(result.reason) or status

            if result.physical is not None:
                reason += (
                    f" | Dia chi vat ly: {result.physical}"
                )

            window.tree_res.insert(
                "",
                "end",
                values=(
                    "KẾT LUẬN",
                    reason,
                    status
                ),
                tags=(
                    "ok" if status == "OK" else "error",
                )
            )

        if result.status.value == "OK":
            window.update_memory_map(
                self.segment_table,
                highlight_addr=result.physical
            )
        else:
            window.update_memory_map(
                self.segment_table,
                fault_msg=_khong_dau(result.reason) or result.status.value
            )

    # ==================== BƯỚC TIẾP THEO ====================

    def handle_next_step(self, window):

        if not self.results:
            messagebox.showinfo(
                "Thông báo",
                "Hãy dịch địa chỉ trước.",
                parent=window
            )
            return

        result = self.results[0]

        if self.visible_step_count < len(result.steps):

            self.visible_step_count += 1
            self._display_result(window)

        else:
            messagebox.showinfo(
                "Hoàn tất",
                "Đã hiển thị hết các bước.",
                parent=window
            )

    # ==================== XUẤT KẾT QUẢ CSV ====================

    def handle_export_results(self, window):

        if not self.results:
            messagebox.showinfo(
                "Thông báo",
                "Chưa có kết quả để xuất.",
                parent=window
            )
            return

        filepath = filedialog.asksaveasfilename(
            parent=window,
            title="Xuất kết quả",
            defaultextension=".csv",
            initialfile="trace.csv",
            filetypes=[("CSV Files", "*.csv")]
        )

        if not filepath:
            return

        try:
            summary_path = self.core.export_trace(
                self.results,
                filepath
            )

            if isinstance(summary_path, tuple):
                summary_path, steps_path = summary_path
            else:
                summary_path = Path(summary_path)
                steps_path = summary_path.with_name(
                    f"{summary_path.stem}_steps.csv"
                )

        except (OSError, ValueError, RuntimeError) as exc:
            messagebox.showerror(
                "Lỗi xuất file",
                str(exc),
                parent=window
            )
            return

        messagebox.showinfo(
            "Xuất thành công",
            f"Đã xuất kết quả:\n"
            f"{summary_path}\n{steps_path}",
            parent=window
        )
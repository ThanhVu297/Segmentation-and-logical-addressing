from __future__ import annotations

import csv
import sys
import tempfile
import tkinter as tk
import unicodedata
from pathlib import Path
from tkinter import filedialog, messagebox

SRC_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.app import SegmentationController  # noqa: E402
from core.result_types import Status, TranslationResult  # noqa: E402
from core.validator import validate_table  # noqa: E402
from gui.gui_panels import create_gui_panels, validate_and_load_csv  # noqa: E402
from gui.memory_map import draw_memory_map  # noqa: E402


def to_ascii_vi(text: str) -> str:
    """Chuyen tieng Viet co dau thanh khong dau de xuat Excel khong loi font."""
    if not text:
        return ""
    text = str(text).replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


class SegmentationApp:
    """Giao dien Tkinter hien dai (tieng Viet khong dau)."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OS_MEM_12 - Segmentation va dia chi logic")
        self.root.geometry("1280x760")
        self.root.minsize(1024, 680)
        self.root.configure(bg="#f1f5f9")

        self.controller = SegmentationController()
        self.segment_table = self.controller.segment_table

        self.segments_data: list[dict] = []
        self.addresses_data: list[dict] = []
        self.results: list[TranslationResult] = []
        self.current_result_index = 0
        self.visible_step_count = 0

        self._build_menubar()
        self._build_top_header()

        widgets = create_gui_panels(
            parent=root,
            cb_open_seg_csv=self.open_segments_csv,
            cb_clear_seg=self.clear_segments,
            cb_add_seg=self.add_or_update_segment,
            cb_open_addr_csv=self.open_addresses_csv,
            cb_clear_addr=self.clear_addresses,
            cb_add_addr=self.add_address,
            cb_translate_selected=self.translate_selected,
            cb_translate_all=self.translate_all,
            cb_next_step=self.show_next_step,
            cb_export=self.export_trace,
        )

        self.main_frame = widgets["main_frame"]
        self.main_frame.pack(fill="both", expand=True)

        self.tree_seg = widgets["tree_seg"]
        self.lbl_seg_count = widgets["lbl_seg_count"]
        self.tree_addr = widgets["tree_addr"]
        self.lbl_addr_count = widgets["lbl_addr_count"]
        self.tree_res = widgets["tree_res"]
        self.canvas = widgets["canvas"]
        self.lbl_map_status = widgets["lbl_map_status"]
        self.tree_summary = widgets["tree_summary"]
        self.lbl_batch_status = widgets["lbl_batch_status"]
        self.inputs = widgets["inputs"]

        self.tree_seg.bind("<Double-1>", self._on_select_segment_row)
        self.root.after_idle(self.redraw_memory_map)

    def _build_menubar(self) -> None:
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Mo segments.csv...", command=self.open_segments_csv)
        file_menu.add_command(label="Mo addresses.csv...", command=self.open_addresses_csv)
        file_menu.add_command(label="Xuat ket qua CSV...", command=self.export_trace)
        file_menu.add_separator()
        file_menu.add_command(label="Thoat", command=self.root.quit)
        menubar.add_cascade(label="Tep tin", menu=file_menu)

        action_menu = tk.Menu(menubar, tearoff=0)
        action_menu.add_command(label="Dich dong dang chon", command=self.translate_selected)
        action_menu.add_command(label="Dich tat ca", command=self.translate_all)
        action_menu.add_command(label="Lam moi toan bo", command=self.reset_all)
        menubar.add_cascade(label="Thao tac", menu=action_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(
            label="Huong dan",
            command=lambda: messagebox.showinfo(
                "Tro giup",
                "1. Nhap hoac mo file segments.csv\n"
                "2. Nhap hoac mo file addresses.csv\n"
                "3. Bam 'Dich dong dang chon' hoac 'Dich tat ca'\n"
                "4. Bam 'Xuat ket qua CSV' de luu file.",
                parent=self.root,
            ),
        )
        menubar.add_cascade(label="Tro giup", menu=help_menu)
        self.root.config(menu=menubar)

    def _build_top_header(self) -> None:
        header = tk.Frame(self.root, bg="#0f172a", height=42)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="OS_MEM_12 - Segmentation va dia chi logic",
            bg="#0f172a",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=14)

        btn_reset = tk.Button(
            header,
            text="Lam moi toan bo",
            command=self.reset_all,
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            padx=10,
            pady=3,
            cursor="hand2",
        )
        btn_reset.pack(side="right", padx=14)

        self.lbl_mem_info = tk.Label(
            header,
            text=f"Bo nho vat ly: 0 - {self.segment_table.mem_size} byte",
            bg="#0f172a",
            fg="#94a3b8",
            font=("Segoe UI", 9),
        )
        self.lbl_mem_info.pack(side="right", padx=8)

    # ==================== QUAN LY SEGMENT ====================

    def open_segments_csv(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Chon segments.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=str(PROJECT_ROOT / "input"),
        )
        if not path:
            return
        rows = validate_and_load_csv(path)
        if not rows:
            return

        new_list = []
        for r in rows:
            try:
                new_list.append({
                    "seg_id": int(r[0].strip()),
                    "base": int(r[1].strip()),
                    "limit": int(r[2].strip()),
                    "perm": r[3].strip().upper(),
                })
            except (ValueError, IndexError):
                messagebox.showerror("Loi du lieu", f"Dong segment khong hop le: {r}", parent=self.root)
                return

        self.segments_data = new_list
        self._sync_segments_to_controller()
        self.lbl_map_status.configure(
            text=f"TRANG THAI: Da nap {len(self.segments_data)} Segment vao bo nho vat ly."
        )

    def add_or_update_segment(self, seg_id_s: str, base_s: str, limit_s: str, perm_s: str) -> None:
        try:
            seg_id = int(seg_id_s.strip())
            base = int(base_s.strip())
            limit = int(limit_s.strip())
            perm = perm_s.strip().upper()
            if limit <= 0 or base < 0:
                raise ValueError("Base phai >= 0 va Limit phai > 0.")
        except ValueError as exc:
            messagebox.showwarning("Du lieu khong hop le", str(exc), parent=self.root)
            return

        updated = False
        for item in self.segments_data:
            if item["seg_id"] == seg_id:
                item.update({"base": base, "limit": limit, "perm": perm})
                updated = True
                break
        if not updated:
            self.segments_data.append({"seg_id": seg_id, "base": base, "limit": limit, "perm": perm})

        self.inputs["seg_id"].set("")
        self.inputs["base"].set("")
        self.inputs["limit"].set("")
        self._sync_segments_to_controller()
        self.lbl_map_status.configure(
            text=f"TRANG THAI: Da {'cap nhat' if updated else 'them'} Segment {seg_id}."
        )

    def clear_segments(self) -> None:
        self.segments_data.clear()
        self._sync_segments_to_controller()
        self.lbl_map_status.configure(text="TRANG THAI: Da xoa toan bo Segment.")

    def _on_select_segment_row(self, _event) -> None:
        sel = self.tree_seg.selection()
        if not sel:
            return
        vals = self.tree_seg.item(sel[0], "values")
        if vals:
            self.inputs["seg_id"].set(vals[0])
            self.inputs["base"].set(vals[1])
            self.inputs["limit"].set(vals[2])
            self.inputs["perm"].set(vals[3])

    def _sync_segments_to_controller(self) -> None:
        """Nap lai du lieu Segment vao controller thong qua file CSV tam."""
        self.controller = SegmentationController()
        self.segment_table = self.controller.segment_table

        if self.segments_data:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False, encoding="utf-8", newline=""
            ) as tmp_s:
                writer = csv.writer(tmp_s)
                writer.writerow(["seg_id", "base", "limit", "perm"])
                for r in self.segments_data:
                    writer.writerow([r["seg_id"], r["base"], r["limit"], r["perm"]])
                tmp_seg_path = tmp_s.name

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False, encoding="utf-8", newline=""
            ) as tmp_a:
                writer = csv.writer(tmp_a)
                writer.writerow(["seg_id", "offset", "access"])
                writer.writerow([0, 0, "R"])
                tmp_addr_path = tmp_a.name

            try:
                self.controller.load_files(tmp_seg_path, tmp_addr_path)
                self.segment_table = self.controller.segment_table
            except Exception as exc:
                messagebox.showerror("Loi bang phan doan", to_ascii_vi(str(exc)), parent=self.root)
            finally:
                Path(tmp_seg_path).unlink(missing_ok=True)
                Path(tmp_addr_path).unlink(missing_ok=True)

        for item in self.tree_seg.get_children():
            self.tree_seg.delete(item)
        for row in self.segments_data:
            self.tree_seg.insert(
                "",
                "end",
                values=(row["seg_id"], row["base"], row["limit"], row["perm"], "San sang"),
            )
        self.lbl_seg_count.configure(text=f"{len(self.segments_data)} SEGMENTS")
        self.redraw_memory_map()

    # ==================== QUAN LY DIA CHI LOGIC ====================

    def open_addresses_csv(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Chon addresses.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=str(PROJECT_ROOT / "input"),
        )
        if not path:
            return
        rows = validate_and_load_csv(path)
        if not rows:
            return

        new_addrs = []
        for r in rows:
            new_addrs.append({
                "seg_id": self._parse_int(r[0]),
                "offset": self._parse_int(r[1]),
                "access": r[2].strip().upper(),
            })
        self.addresses_data = new_addrs
        self._refresh_address_table()

    def add_address(self, seg_s: str, offset_s: str, access_s: str) -> None:
        if not seg_s.strip() or not offset_s.strip():
            messagebox.showwarning("Thieu thong tin", "Vui long nhap Seg ID va Offset.", parent=self.root)
            return
        self.addresses_data.append({
            "seg_id": self._parse_int(seg_s),
            "offset": self._parse_int(offset_s),
            "access": access_s.strip().upper(),
        })
        self.inputs["addr_seg"].set("")
        self.inputs["addr_offset"].set("")
        self._refresh_address_table()

    def clear_addresses(self) -> None:
        self.addresses_data.clear()
        self._refresh_address_table()

    def _refresh_address_table(self) -> None:
        for item in self.tree_addr.get_children():
            self.tree_addr.delete(item)
        for idx, row in enumerate(self.addresses_data, start=1):
            self.tree_addr.insert(
                "",
                "end",
                values=(idx, row["seg_id"], row["offset"], row["access"], "Cho dich"),
            )
        self.lbl_addr_count.configure(text=f"{len(self.addresses_data)} DIA CHI")

    @staticmethod
    def _parse_int(val):
        try:
            return int(str(val).strip())
        except (ValueError, TypeError):
            return str(val).strip()

    # ==================== DICH DIA CHI ====================

    def translate_selected(self) -> None:
        if not self.segments_data:
            messagebox.showwarning("Chua co Segment", "Hay them Segment hoac mo segments.csv truoc.", parent=self.root)
            return

        sel = self.tree_addr.selection()
        if not sel:
            messagebox.showinfo("Chua chon dong", "Hay chon 1 dong trong Bang 2 de dich.", parent=self.root)
            return

        idx = self.tree_addr.index(sel[0])
        addr = self.addresses_data[idx]
        res = self.controller.translate_one(addr["seg_id"], addr["offset"], addr["access"])
        self._set_results([res])

    def translate_all(self) -> None:
        if not self.segments_data:
            messagebox.showwarning("Chua co Segment", "Hay them Segment hoac mo segments.csv truoc.", parent=self.root)
            return
        if not self.addresses_data:
            messagebox.showwarning("Chua co dia chi", "Hay them dia chi vao Bang 2 truoc.", parent=self.root)
            return

        results = [
            self.controller.translate_one(a["seg_id"], a["offset"], a["access"])
            for a in self.addresses_data
        ]
        self._set_results(results)

    def _set_results(self, results: list[TranslationResult]) -> None:
        self.results = results
        self.current_result_index = 0
        self.visible_step_count = len(results[0].steps) if results else 0
        self._refresh_summary_table()
        if results:
            self._render_current_result()

    def _refresh_summary_table(self) -> None:
        for item in self.tree_summary.get_children():
            self.tree_summary.delete(item)

        ok_count = 0
        for idx, res in enumerate(self.results, start=1):
            status = res.status.value if hasattr(res.status, "value") else str(res.status)
            if status == Status.OK.value:
                ok_count += 1
            reason = to_ascii_vi(res.reason) or ("Dich thanh cong" if status == Status.OK.value else "")
            tag = "ok" if status == Status.OK.value else "error"
            self.tree_summary.insert(
                "",
                "end",
                values=(
                    idx,
                    res.seg_id,
                    res.offset,
                    res.access,
                    res.physical if res.physical is not None else "-",
                    status,
                    reason,
                ),
                tags=(tag,),
            )

        if self.results:
            self.lbl_batch_status.configure(
                text=f"Da xu ly {len(self.results)} dia chi ({ok_count} OK, {len(self.results) - ok_count} LOI)",
                fg="#15803d",
            )
        else:
            self.lbl_batch_status.configure(text="Chua co ket qua", fg="#d97706")

    def show_next_step(self) -> None:
        if not self.results:
            messagebox.showinfo(
                "Chua co ket qua",
                "Hay bam 'Dich dong dang chon' hoac 'Dich tat ca' truoc.",
                parent=self.root,
            )
            return

        current = self.results[self.current_result_index]
        if self.visible_step_count < len(current.steps):
            self.visible_step_count += 1
        elif self.current_result_index + 1 < len(self.results):
            self.current_result_index += 1
            self.visible_step_count = 1
        else:
            messagebox.showinfo("Hoan tat", "Da xem het cac buoc dich.", parent=self.root)
            return
        self._render_current_result()

    def _render_current_result(self) -> None:
        result = self.results[self.current_result_index]
        for item in self.tree_res.get_children():
            self.tree_res.delete(item)

        for idx, step in enumerate(result.steps[: self.visible_step_count], start=1):
            tag = "ok" if step.ok else "error"
            self.tree_res.insert(
                "",
                "end",
                values=(idx, to_ascii_vi(step.description), "Hop le" if step.ok else "Loi"),
                tags=(tag,),
            )

        status = result.status.value if hasattr(result.status, "value") else str(result.status)
        reason_clean = to_ascii_vi(result.reason) or "Dich thanh cong"

        if self.visible_step_count >= len(result.steps):
            tag = "ok" if status == Status.OK.value else "error"
            self.tree_res.insert(
                "",
                "end",
                values=("KET LUAN", reason_clean, status),
                tags=(tag,),
            )

        if result.status == Status.OK:
            self.redraw_memory_map(highlight_addr=result.physical)
            self.lbl_map_status.configure(
                text=f"TRANG THAI: Dich thanh cong -> Dia chi vat ly = {result.physical}"
            )
        else:
            self.redraw_memory_map(fault_msg=reason_clean)
            self.lbl_map_status.configure(
                text=f"TRANG THAI: {status} - {reason_clean}"
            )

    def redraw_memory_map(self, highlight_addr=None, fault_msg=None) -> None:
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

    def reset_all(self) -> None:
        self.segments_data.clear()
        self.addresses_data.clear()
        self.results.clear()
        self.current_result_index = 0
        self.visible_step_count = 0
        self._sync_segments_to_controller()
        self._refresh_address_table()
        self._refresh_summary_table()
        for item in self.tree_res.get_children():
            self.tree_res.delete(item)
        self.lbl_map_status.configure(text="TRANG THAI: Da lam moi toan bo.")

    def export_trace(self) -> None:
        """Xuat ket qua ra file CSV tieng Viet khong dau (mo bang Excel khong loi font)."""
        if not self.results:
            messagebox.showinfo("Chua co ket qua", "Chua co ket qua nao de xuat.", parent=self.root)
            return

        default_path = PROJECT_ROOT / "output" / "ket_qua_dich.csv"
        default_path.parent.mkdir(parents=True, exist_ok=True)
        selected = filedialog.asksaveasfilename(
            parent=self.root,
            title="Xuat ket qua CSV",
            initialdir=str(default_path.parent),
            initialfile=default_path.name,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not selected:
            return

        try:
            with open(selected, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["STT", "SEG_ID", "OFFSET", "ACCESS", "PHYSICAL", "STATUS", "REASON"])
                for idx, res in enumerate(self.results, start=1):
                    status = res.status.value if hasattr(res.status, "value") else str(res.status)
                    reason = to_ascii_vi(res.reason) or ("Dich thanh cong" if status == Status.OK.value else "")
                    writer.writerow([
                        idx,
                        res.seg_id,
                        res.offset,
                        res.access,
                        res.physical if res.physical is not None else "",
                        status,
                        reason,
                    ])
        except OSError as exc:
            messagebox.showerror("Khong xuat duoc CSV", str(exc), parent=self.root)
            return

        messagebox.showinfo(
            "Da xuat ket qua",
            f"Da luu {len(self.results)} dong ket qua (khong dau) tai:\n{selected}",
            parent=self.root,
        )


def run_app() -> None:
    root = tk.Tk()
    SegmentationApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()

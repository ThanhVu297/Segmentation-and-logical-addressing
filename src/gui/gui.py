import csv
import tkinter as tk
import unicodedata
from tkinter import filedialog, messagebox

from core.validator import validate_table
from gui.gui_panels import create_gui_panels, validate_and_load_csv
from gui.memory_map import draw_memory_map


def to_ascii_vi(text: str) -> str:
    """Chuyen tieng Viet co dau thanh khong dau de xuat Excel khong loi font."""
    if not text:
        return ""
    text = str(text).replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


class MainWindow(tk.Tk):
    def __init__(self, controller=None):
        super().__init__()

        self.title("OS_MEM_12 - Segmentation va dia chi logic")
        self.geometry("1280x760")
        self.minsize(1024, 680)
        self.configure(bg="#f1f5f9")

        self.controller = controller
        self.segments_data = []
        self.addresses_data = []
        self.results = []
        self.current_result_index = 0
        self.visible_step_count = 0

        self.setup_menu()
        self.build_top_header()
        self.build_layout()

        self.after_idle(lambda: self.update_memory_map(None))

    # ==================== MENU & HEADER ====================

    def setup_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Mo segments.csv...", command=self.on_open_seg_csv)
        file_menu.add_command(label="Mo addresses.csv...", command=self.on_open_addr_csv)
        file_menu.add_command(label="Xuat ket qua CSV...", command=self.on_export)
        file_menu.add_separator()
        file_menu.add_command(label="Thoat", command=self.quit)
        menubar.add_cascade(label="Tep tin", menu=file_menu)

        action_menu = tk.Menu(menubar, tearoff=0)
        action_menu.add_command(label="Dich dong dang chon", command=self.on_translate_selected)
        action_menu.add_command(label="Dich tat ca", command=self.on_translate_all)
        action_menu.add_command(label="Lam moi toan bo", command=self.on_reset_all)
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
            ),
        )
        menubar.add_cascade(label="Tro giup", menu=help_menu)

        self.config(menu=menubar)

    def build_top_header(self):
        header = tk.Frame(self, bg="#0f172a", height=42)
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
            command=self.on_reset_all,
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
            text="Bo nho vat ly: 0 - 5000 byte",
            bg="#0f172a",
            fg="#94a3b8",
            font=("Segoe UI", 9),
        )
        self.lbl_mem_info.pack(side="right", padx=8)

    # ==================== BO CUC GIAO DIEN ====================

    def build_layout(self):
        widgets = create_gui_panels(
            parent=self,
            cb_open_seg_csv=self.on_open_seg_csv,
            cb_clear_seg=self.on_clear_seg,
            cb_add_seg=self.on_add_seg,
            cb_open_addr_csv=self.on_open_addr_csv,
            cb_clear_addr=self.on_clear_addr,
            cb_add_addr=self.on_add_addr,
            cb_translate_selected=self.on_translate_selected,
            cb_translate_all=self.on_translate_all,
            cb_next_step=self.on_next_step,
            cb_export=self.on_export,
        )

        self.gui_frame = widgets["main_frame"]
        self.gui_frame.pack(fill=tk.BOTH, expand=True)

        self.tree_seg = widgets["tree_seg"]
        self.lbl_seg_count = widgets["lbl_seg_count"]
        self.tree_addr = widgets["tree_addr"]
        self.lbl_addr_count = widgets["lbl_addr_count"]
        self.tree_res = widgets["tree_res"]
        self.canvas_map = widgets["canvas"]
        self.lbl_map_status = widgets["lbl_map_status"]
        self.tree_summary = widgets["tree_summary"]
        self.lbl_batch_status = widgets["lbl_batch_status"]
        self.inputs = widgets["inputs"]

        self.tree_seg.bind("<Double-1>", self._on_select_segment_row)

    # ==================== QUAN LY SEGMENT ====================

    def on_open_seg_csv(self):
        if self.controller and hasattr(self.controller, "handle_open_csv"):
            self.controller.handle_open_csv(self)
            return

        filepath = filedialog.askopenfilename(
            title="Chon file segments.csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not filepath:
            return

        rows = validate_and_load_csv(filepath)
        if rows is not None:
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
                    messagebox.showerror("Loi du lieu", f"Dong segment khong hop le: {r}")
                    return

            self.segments_data = new_list
            self._refresh_seg_table()
            self.lbl_map_status.configure(
                text=f"TRANG THAI: Da nap {len(self.segments_data)} Segment vao bo nho vat ly."
            )

    def on_add_seg(self, seg_id_s, base_s, limit_s, perm_s):
        try:
            seg_id = int(seg_id_s.strip())
            base = int(base_s.strip())
            limit = int(limit_s.strip())
            perm = perm_s.strip().upper()
            if limit <= 0 or base < 0:
                raise ValueError("Base phai >= 0 va Limit phai > 0.")
        except ValueError as exc:
            messagebox.showwarning("Du lieu khong hop le", str(exc))
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
        self._refresh_seg_table()
        self.lbl_map_status.configure(
            text=f"TRANG THAI: Da {'cap nhat' if updated else 'them'} Segment {seg_id}."
        )

    def on_clear_seg(self):
        self.segments_data.clear()
        self._refresh_seg_table()
        self.lbl_map_status.configure(text="TRANG THAI: Da xoa toan bo Segment.")

    def _on_select_segment_row(self, _event):
        sel = self.tree_seg.selection()
        if not sel:
            return
        vals = self.tree_seg.item(sel[0], "values")
        if vals:
            self.inputs["seg_id"].set(vals[0])
            self.inputs["base"].set(vals[1])
            self.inputs["limit"].set(vals[2])
            self.inputs["perm"].set(vals[3])

    def _refresh_seg_table(self):
        for item in self.tree_seg.get_children():
            self.tree_seg.delete(item)
        for row in self.segments_data:
            self.tree_seg.insert(
                "", "end",
                values=(row["seg_id"], row["base"], row["limit"], row["perm"], "San sang"),
            )
        self.lbl_seg_count.configure(text=f"{len(self.segments_data)} SEGMENTS")

        if self.controller and hasattr(self.controller, "segment_table"):
            self.update_memory_map(self.controller.segment_table)
        else:
            self._draw_from_local_segments()

    def _draw_from_local_segments(self, highlight_addr=None, fault_msg=None):
        from core.result_types import Segment, SegmentTable
        table = SegmentTable(mem_size=5000)
        for r in self.segments_data:
            seg = Segment(seg_id=r["seg_id"], base=r["base"], limit=r["limit"], perm=r["perm"])
            if hasattr(table, "add"):
                table.add(seg)
            elif hasattr(table, "segments"):
                if isinstance(table.segments, dict):
                    table.segments[r["seg_id"]] = seg
                else:
                    table.segments.append(seg)
        self.update_memory_map(table, highlight_addr=highlight_addr, fault_msg=fault_msg)

    # ==================== QUAN LY DIA CHI LOGIC ====================

    def on_open_addr_csv(self):
        filepath = filedialog.askopenfilename(
            title="Chon file addresses.csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not filepath:
            return
        rows = validate_and_load_csv(filepath)
        if rows is not None:
            self.addresses_data = [
                {
                    "seg_id": self._parse_int(r[0]),
                    "offset": self._parse_int(r[1]),
                    "access": r[2].strip().upper(),
                }
                for r in rows
            ]
            self._refresh_addr_table()

    def on_add_addr(self, seg_s, offset_s, access_s):
        if not seg_s.strip() or not offset_s.strip():
            messagebox.showwarning("Thieu thong tin", "Vui long nhap Seg ID va Offset.")
            return
        self.addresses_data.append({
            "seg_id": self._parse_int(seg_s),
            "offset": self._parse_int(offset_s),
            "access": access_s.strip().upper(),
        })
        self.inputs["addr_seg"].set("")
        self.inputs["addr_offset"].set("")
        self._refresh_addr_table()

    def on_clear_addr(self):
        self.addresses_data.clear()
        self._refresh_addr_table()

    def _refresh_addr_table(self):
        for item in self.tree_addr.get_children():
            self.tree_addr.delete(item)
        for idx, row in enumerate(self.addresses_data, start=1):
            self.tree_addr.insert(
                "", "end",
                values=(idx, row["seg_id"], row["offset"], row["access"], "Cho dich"),
            )
        self.lbl_addr_count.configure(text=f"{len(self.addresses_data)} DIA CHI")

    @staticmethod
    def _parse_int(val):
        try:
            return int(str(val).strip())
        except (ValueError, TypeError):
            return str(val).strip()

    # ==================== CAP NHAT BAN DO BO NHO ====================

    def update_memory_map(self, segment_table, highlight_addr=None, fault_msg=None):
        if segment_table is not None:
            mem_size = getattr(segment_table, "mem_size", 5000)
            issues = validate_table(segment_table)
            draw_memory_map(
                self.canvas_map,
                segment_table,
                mem_size,
                highlight_addr=highlight_addr,
                fault_msg=to_ascii_vi(fault_msg) if fault_msg else None,
                issues=issues,
            )
        else:
            from core.result_types import SegmentTable
            draw_memory_map(self.canvas_map, SegmentTable(mem_size=5000), 5000)

    # ==================== DICH DIA CHI ====================

    def on_translate_selected(self):
        sel = self.tree_addr.selection()
        if not sel:
            messagebox.showinfo("Chua chon dong", "Hay chon 1 dong trong Bang 2 de dich.")
            return
        idx = self.tree_addr.index(sel[0])
        addr = self.addresses_data[idx]

        if self.controller and hasattr(self.controller, "handle_translate"):
            self.controller.handle_translate(
                str(addr["seg_id"]),
                str(addr["offset"]),
                str(addr["access"]),
                self,
            )
        else:
            messagebox.showerror("Loi ket noi", "Controller chua duoc khoi tao!")

    def on_translate_all(self):
        if not self.addresses_data:
            messagebox.showwarning("Chua co dia chi", "Hay them dia chi vao Bang 2 truoc.")
            return
        if self.controller and hasattr(self.controller, "handle_translate_all"):
            self.controller.handle_translate_all(self.addresses_data, self)
        elif self.controller and hasattr(self.controller, "translate_one"):
            results = [
                self.controller.translate_one(a["seg_id"], a["offset"], a["access"])
                for a in self.addresses_data
            ]
            self.display_results(results)
        else:
            messagebox.showerror("Loi ket noi", "Controller chua duoc khoi tao!")

    def display_results(self, results):
        """Hien thi ket qua dich len Bang 3 va Bang 5 (khong dau)."""
        self.results = results
        self.current_result_index = 0
        self.visible_step_count = len(results[0].steps) if results else 0

        for item in self.tree_summary.get_children():
            self.tree_summary.delete(item)

        ok_count = 0
        for idx, res in enumerate(results, start=1):
            status = res.status.value if hasattr(res.status, "value") else str(res.status)
            if status == "OK":
                ok_count += 1
            reason = to_ascii_vi(res.reason) or ("Dich thanh cong" if status == "OK" else "")
            tag = "ok" if status == "OK" else "error"
            self.tree_summary.insert(
                "", "end",
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

        if results:
            self.lbl_batch_status.configure(
                text=f"Da xu ly {len(results)} dia chi ({ok_count} OK, {len(results) - ok_count} LOI)",
                fg="#15803d",
            )
            self._render_step_table()

    def _render_step_table(self):
        if not self.results:
            return
        res = self.results[self.current_result_index]
        for item in self.tree_res.get_children():
            self.tree_res.delete(item)

        for idx, step in enumerate(res.steps[: self.visible_step_count], start=1):
            tag = "ok" if step.ok else "error"
            self.tree_res.insert(
                "", "end",
                values=(idx, to_ascii_vi(step.description), "Hop le" if step.ok else "Loi"),
                tags=(tag,),
            )

        status = res.status.value if hasattr(res.status, "value") else str(res.status)
        reason_clean = to_ascii_vi(res.reason) or "Dich thanh cong"
        if self.visible_step_count >= len(res.steps):
            tag = "ok" if status == "OK" else "error"
            self.tree_res.insert(
                "", "end",
                values=("KET LUAN", reason_clean, status),
                tags=(tag,),
            )

    # ==================== BUOC TIEP THEO & RESET & XUAT CSV ====================

    def on_next_step(self):
        if self.controller and hasattr(self.controller, "handle_next_step"):
            self.controller.handle_next_step(self)
            return

        if not self.results:
            messagebox.showinfo("Chua co ket qua", "Hay dich dia chi truoc.")
            return
        cur = self.results[self.current_result_index]
        if self.visible_step_count < len(cur.steps):
            self.visible_step_count += 1
        elif self.current_result_index + 1 < len(self.results):
            self.current_result_index += 1
            self.visible_step_count = 1
        else:
            messagebox.showinfo("Hoan tat", "Da xem het cac buoc dich.")
            return
        self._render_step_table()

    def on_reset_all(self):
        self.segments_data.clear()
        self.addresses_data.clear()
        self.results.clear()
        self._refresh_seg_table()
        self._refresh_addr_table()
        for item in self.tree_res.get_children():
            self.tree_res.delete(item)
        for item in self.tree_summary.get_children():
            self.tree_summary.delete(item)
        self.lbl_batch_status.configure(text="Chua co ket qua", fg="#d97706")
        self.lbl_map_status.configure(text="TRANG THAI: Da lam moi toan bo.")

    def on_export(self):
        if self.controller and hasattr(self.controller, "handle_export_results"):
            self.controller.handle_export_results(self)
            return

        if not self.results:
            messagebox.showinfo("Chua co ket qua", "Chua co ket qua nao de xuat.")
            return

        selected = filedialog.asksaveasfilename(
            title="Xuat ket qua CSV",
            initialfile="ket_qua_dich.csv",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not selected:
            return

        with open(selected, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["STT", "SEG_ID", "OFFSET", "ACCESS", "PHYSICAL", "STATUS", "REASON"])
            for idx, res in enumerate(self.results, start=1):
                status = res.status.value if hasattr(res.status, "value") else str(res.status)
                reason = to_ascii_vi(res.reason) or ("Dich thanh cong" if status == "OK" else "")
                writer.writerow([
                    idx,
                    res.seg_id,
                    res.offset,
                    res.access,
                    res.physical if res.physical is not None else "",
                    status,
                    reason,
                ])
        messagebox.showinfo("Thanh cong", f"Da xuat file CSV khong dau tai:\n{selected}")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()

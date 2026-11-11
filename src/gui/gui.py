
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Import giao diện TV4
from gui.gui_panels import create_gui_panels, validate_and_load_csv

# Import bản đồ bộ nhớ của TV5
from gui.memory_map import draw_memory_map

# Import kiểu dữ liệu chung của nhóm
from core.result_types import Status, SegmentTable

# Import chức năng kiểm tra Segment của TV5
from core.validator import validate_table


class MainWindow(tk.Tk):

    def __init__(self, controller=None):
        super().__init__()

        self.title("Mô Phỏng Dịch Địa Chỉ Phân Đoạn - TV4 Ngọc Giàu")
        self.geometry("1150x700")

        # Nhận Controller từ bên ngoài
        self.controller = controller

        self.setup_menu()
        self.build_layout()
        self.bind_events()

    # ==================== MENU ====================

    def setup_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)

        file_menu.add_command(
            label="Mở file CSV",
            command=self.on_open_csv
        )

        file_menu.add_command(
            label="Xuất kết quả",
            command=self.on_export
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="Thoát",
            command=self.quit
        )

        menubar.add_cascade(
            label="Tệp tin",
            menu=file_menu
        )

        self.config(menu=menubar)

    # ==================== BỐ CỤC GIAO DIỆN ====================

    def build_layout(self):

        self.paned = ttk.PanedWindow(
            self,
            orient=tk.HORIZONTAL
        )

        self.paned.pack(
            fill=tk.BOTH,
            expand=True,
            padx=5,
            pady=5
        )

        # Nửa bên trái: Giao diện TV4
        self.left_frame = ttk.Frame(self.paned)

        self.paned.add(
            self.left_frame,
            weight=3
        )

        # Nhận các thành phần từ gui_panels.py
        (
            self.gui_frame,
            self.tree_seg,
            self.tree_res,
            self.seg_var,
            self.offset_var,
            self.access_var,
            self.btn_open_csv,
            self.btn_translate,
            self.btn_next_step,
            self.btn_export
        ) = create_gui_panels(self.left_frame)

        # Nửa bên phải: Bản đồ bộ nhớ của TV5
        self.right_frame = ttk.Frame(
            self.paned,
            relief="sunken",
            borderwidth=1
        )

        self.paned.add(
            self.right_frame,
            weight=2
        )

        # Canvas để TV5 vẽ bản đồ bộ nhớ
        self.canvas_map = tk.Canvas(
            self.right_frame,
            bg="white",
            highlightthickness=0
        )

        self.canvas_map.pack(
            fill=tk.BOTH,
            expand=True,
            padx=2,
            pady=2
        )

    # ==================== GẮN SỰ KIỆN ====================

    def bind_events(self):

        self.btn_open_csv.config(
            command=self.on_open_csv
        )

        self.btn_translate.config(
            command=self.on_translate
        )

        self.btn_next_step.config(
            command=self.on_next_step
        )

        self.btn_export.config(
            command=self.on_export
        )

    # ==================== CẬP NHẬT BẢN ĐỒ BỘ NHỚ ====================

    def update_memory_map(
        self,
        segment_table,
        highlight_addr=None,
        fault_msg=None
    ):
        """
        Cập nhật bản đồ bộ nhớ vật lý của TV5.

        segment_table: Bảng phân đoạn.
        highlight_addr: Địa chỉ vật lý cần đánh dấu.
        fault_msg: Thông báo lỗi nếu có.
        """

        if segment_table is not None:

            mem_size = getattr(
                segment_table,
                "mem_size",
                5000
            )

            # Kiểm tra lỗi trong Segment Table
            issues = validate_table(
                segment_table,
                mem_size
            )

            # Vẽ bản đồ bộ nhớ
            draw_memory_map(
                self.canvas_map,
                segment_table,
                mem_size,
                highlight_addr=highlight_addr,
                fault_msg=fault_msg,
                issues=issues
            )

    # ==================== MỞ FILE CSV ====================

    def on_open_csv(self):

        if self.controller:

            self.controller.handle_open_csv(self)

        else:
            filepath = filedialog.askopenfilename(
                title="Chon file CSV",
                filetypes=[("CSV Files", "*.csv")]
            )

            if filepath:
                rows = validate_and_load_csv(filepath)

                if rows is not None:
                    # Xoa du lieu cu trong bang
                    for item in self.tree_seg.get_children():
                        self.tree_seg.delete(item)

                    # Dua du lieu moi len Segment Table
                    for row in rows:
                        self.tree_seg.insert(
                            "",
                            "end",
                            values=row[:4]
                        )

                    messagebox.showinfo(
                        "Thong bao",
                        "Da nap du lieu CSV thanh cong!"
                    )
    # ==================== DỊCH ĐỊA CHỈ ====================

    def on_translate(self):

        if self.controller:

            seg = self.seg_var.get().strip()
            offset = self.offset_var.get().strip()
            access = self.access_var.get().strip()

            self.controller.handle_translate(
                seg,
                offset,
                access,
                self
            )
        else:
            messagebox.showerror(
                "Lỗi kết nối",
                "Controller chưa được khởi tạo!"
            )

    # ==================== BƯỚC TIẾP THEO ====================

    def on_next_step(self):

        if self.controller:

            self.controller.handle_next_step(self)

    # ==================== XUẤT KẾT QUẢ ====================

    def on_export(self):

        if self.controller:

            self.controller.handle_export_results(self)


# ==================== CHẠY CHƯƠNG TRÌNH ====================

if __name__ == "__main__":

    app = MainWindow()
    app.mainloop()

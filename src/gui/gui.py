import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Import cái ruộtgui_panels của bạn
from gui.gui_panels import create_gui_panels

# Nhúng bản đồ bộ nhớ của TV5 vào
from gui.memory_map import draw_memory_map
from core.result_types import Status, SegmentTable

class MainWindow(tk.Tk):
    def __init__(self, controller=None):
        super().__init__()
        self.title("Mô Phỏng Dịch Địa Chỉ Phân Đoạn - TV4 Ngọc Giàu")
        self.geometry("1150x700")

        # Nhận app.py (controller) từ ngoài truyền vào
        self.controller = controller

        self.setup_menu()
        self.build_layout()
        self.bind_events()

    def setup_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Mở file CSV", command=self.on_open_csv)
        file_menu.add_command(label="Xuất kết quả", command=self.on_export)
        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.quit)

        menubar.add_cascade(label="Tệp tin", menu=file_menu)
        self.config(menu=menubar)

    def build_layout(self):
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Nửa bên trái: Giao diện gui_panels của bạn
        self.left_frame = ttk.Frame(self.paned)
        self.paned.add(self.left_frame, weight=3)

        # Hứng lại mấy cái nút, bảng từ gui_panels.py để lát gắn sự kiện
        (self.gui_frame, self.tree_seg, self.tree_res,
         self.seg_var, self.offset_var, self.access_var,
         self.btn_open_csv, self.btn_translate, self.btn_next_step,
         self.btn_export) = create_gui_panels(self.left_frame)

        # Nửa bên phải: Khu vực Bản đồ bộ nhớ vật lý của TV5
        self.right_frame = ttk.Frame(self.paned, relief="sunken", borderwidth=1)
        self.paned.add(self.right_frame, weight=2)

        # Tạo Canvas trắng bên trong right_frame để TV5 vẽ bản đồ
        self.canvas_map = tk.Canvas(self.right_frame, bg="white", highlightthickness=0)
        self.canvas_map.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    def bind_events(self):
        self.btn_open_csv.config(command=self.on_open_csv)
        self.btn_translate.config(command=self.on_translate)
        self.btn_next_step.config(command=self.on_next_step)
        self.btn_export.config(command=self.on_export)

    def update_memory_map(self, segment_table, highlight_addr=None, fault_msg=None):
        """Hàm gọi bản đồ bộ nhớ của TV5 vẽ lên Canvas"""
        if segment_table:
            mem_size = getattr(segment_table, 'mem_size', 5000)
            draw_memory_map(self.canvas_map, segment_table, mem_size, highlight_addr, fault_msg)

    def on_open_csv(self):
        if self.controller:
            self.controller.handle_open_csv(self)
        else:
            # Fallback khi chạy test độc lập
            filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
            if filepath:
                messagebox.showinfo("Thông báo", f"Đã chọn file: {filepath}")

    def on_translate(self):
        if self.controller:
            seg = self.seg_var.get().strip()
            offset = self.offset_var.get().strip()
            access = self.access_var.get().strip()
            self.controller.handle_translate(seg, offset, access, self)

    def on_next_step(self):
        if self.controller:
            self.controller.handle_next_step(self)

    def on_export(self):
        if self.controller:
            self.controller.handle_export_results(self)


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
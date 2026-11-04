import tkinter as tk
from tkinter import ttk, messagebox
# Import cái ruột bà vừa làm ở Tuần 1-3
from .gui_panels import create_gui_panels


# Mốt thằng TV5 làm xong file memory_map.py thì mở comment dòng dưới ra
# from .memory_map import create_memory_map_panel

class MainWindow(tk.Tk):
    def __init__(self, controller=None):
        super().__init__()
        self.title("Mô Phỏng Dịch Địa Chỉ Phân Đoạn - TV4 Ngọc Giàu")
        self.geometry("1100x650")

        # Cái này là của Tuần 5: Nhận app.py từ ngoài truyền vào
        self.controller = controller

        self.setup_menu()
        self.build_layout()
        self.bind_events()

    def setup_menu(self):
        # Yêu cầu Tuần 4: Tạo menu
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Mở file CSV", command=self.on_open_csv)
        file_menu.add_command(label="Xuất kết quả", command=self.on_export)
        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.quit)

        menubar.add_cascade(label="Tệp tin", menu=file_menu)
        self.config(menu=menubar)

    def build_layout(self):
        # Yêu cầu Tuần 4: Ghép gui_panels và chừa chỗ cho panel của TV5
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Nửa bên trái: Giao diện của bà
        self.left_frame = ttk.Frame(self.paned)
        self.paned.add(self.left_frame, weight=1)

        # Hứng lại mấy cái nút, bảng từ gui_panels.py để lát gắn sự kiện
        (self.gui_frame, self.tree_seg, self.tree_res,
         self.seg_var, self.offset_var, self.access_var,
         self.btn_open_csv, self.btn_translate, self.btn_next_step,
         self.btn_export) = create_gui_panels(self.left_frame)

        # Nửa bên phải: Khu vực của TV5 (Memory Map)
        self.right_frame = ttk.Frame(self.paned, relief="sunken", borderwidth=1)
        self.paned.add(self.right_frame, weight=1)

        ttk.Label(self.right_frame, text="[Khu vực Bản đồ bộ nhớ của TV5]",
                  background="#e0e0e0").pack(fill=tk.BOTH, expand=True)
        # Mốt có code TV5 thì nhúng vào đây: create_memory_map_panel(self.right_frame, self.controller)

    def bind_events(self):
        # Gắn dây điện từ nút bấm sang các hàm ở dưới
        self.btn_open_csv.config(command=self.on_open_csv)
        self.btn_translate.config(command=self.on_translate)
        self.btn_next_step.config(command=self.on_next_step)
        self.btn_export.config(command=self.on_export)

    # ==========================================
    # YÊU CẦU TUẦN 5: GỌI HÀM TỪ CONTROLLER
    # Không tự tính toán, có gì đẩy hết cho app.py lo
    # ==========================================
    def on_open_csv(self):
        if self.controller:
            self.controller.handle_open_csv(self)
        else:
            messagebox.showwarning("Cảnh báo", "Chưa nối với Controller đâu nha.")

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
    # Để bà tự chạy test giao diện xem lên hình chưa (chưa có controller thật)
    app = MainWindow()
    app.mainloop()
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

def create_gui_panels(parent):
    """
    Tạo toàn bộ giao diện GUI cho phần Quản lý phân đoạn và Địa chỉ logic của TV4.
    Bao gồm: Segment Table, Form nhập địa chỉ đơn lẻ, Bảng kết quả từng bước và các nút điều khiển.
    """
    gui_frame = ttk.Frame(parent, padding=10)
    gui_frame.pack(fill="both", expand=True)

    # ==================== 1. SEGMENT TABLE ====================
    seg_frame = ttk.LabelFrame(gui_frame, text="1. Segment Table", padding=10)
    seg_frame.pack(fill="x", pady=5)

    btn_open_csv = ttk.Button(seg_frame, text="Mở file CSV")
    btn_open_csv.pack(side="left", padx=5)

    columns = ("seg_id", "base", "limit", "perm")
    tree_seg = ttk.Treeview(seg_frame, columns=columns, show="headings", height=4)
    tree_seg.heading("seg_id", text="SEG_ID")
    tree_seg.heading("base", text="BASE")
    tree_seg.heading("limit", text="LIMIT")
    tree_seg.heading("perm", text="PERM")

    tree_seg.column("seg_id", width=80, anchor="center")
    tree_seg.column("base", width=100, anchor="center")
    tree_seg.column("limit", width=100, anchor="center")
    tree_seg.column("perm", width=80, anchor="center")
    tree_seg.pack(side="left", fill="x", expand=True, padx=5)

    # ==================== 2. FORM NHẬP ĐỊA CHỈ ĐƠN LẺ ====================
    input_frame = ttk.LabelFrame(gui_frame, text="2. Dịch địa chỉ đơn lẻ", padding=10)
    input_frame.pack(fill="x", pady=5)

    ttk.Label(input_frame, text="Segment:").pack(side="left", padx=2)
    seg_var = tk.StringVar()
    ttk.Entry(input_frame, textvariable=seg_var, width=10).pack(side="left", padx=5)

    ttk.Label(input_frame, text="Offset:").pack(side="left", padx=2)
    offset_var = tk.StringVar()
    ttk.Entry(input_frame, textvariable=offset_var, width=10).pack(side="left", padx=5)

    ttk.Label(input_frame, text="Access (R/W/X):").pack(side="left", padx=2)
    access_var = tk.StringVar()
    ttk.Entry(input_frame, textvariable=access_var, width=10).pack(side="left", padx=5)

    btn_translate = ttk.Button(input_frame, text="Dịch địa chỉ")
    btn_translate.pack(side="left", padx=10)

    #3. BẢNG KẾT QUẢ TỪNG BƯỚC
    res_frame = ttk.LabelFrame(gui_frame, text="3. Bảng kết quả từng bước", padding=10)
    res_frame.pack(fill="both", expand=True, pady=5)

    res_columns = ("step", "detail", "status")
    tree_res = ttk.Treeview(res_frame, columns=res_columns, show="headings", height=5)
    tree_res.heading("step", text="Bước")
    tree_res.heading("detail", text="Chi tiết")
    tree_res.heading("status", text="Trạng thái")

    tree_res.column("step", width=120, anchor="center")
    tree_res.column("detail", width=350, anchor="w")
    tree_res.column("status", width=150, anchor="center")
    tree_res.pack(fill="both", expand=True, pady=5)

    tree_res.tag_configure("ok", background="#e6ffed")
    tree_res.tag_configure("error", background="#ffebe6")

    # ==================== 4. CÁC NÚT ĐIỀU KHIỂN ====================
    ctrl_frame = ttk.Frame(gui_frame, padding=5)
    ctrl_frame.pack(fill="x", pady=5)

    btn_next_step = ttk.Button(ctrl_frame, text="Bước tiếp")
    btn_next_step.pack(side="left", expand=True, padx=5)

    btn_export = ttk.Button(ctrl_frame, text="Xuất kết quả")
    btn_export.pack(side="left", expand=True, padx=5)

    return gui_frame, tree_seg, tree_res, seg_var, offset_var, access_var, btn_open_csv, btn_translate, btn_next_step, btn_export


def display_translation_result(tree_res, mock_result):
    """
    Hàm xử lý và hiển thị kết quả dịch địa chỉ lên bảng tree_res,
    tự động phân loại tag 'ok' (xanh) hoặc 'error' (đỏ) theo từng bước.
    """
    for item in tree_res.get_children():
        tree_res.delete(item)

    for idx, step in enumerate(mock_result.steps, start=1):
        current_status = getattr(mock_result, "status", "OK")
        tag = "ok" if "OK" in str(current_status) or idx == 1 else "error"

        tree_res.insert("", "end", values=(f"Bước {idx}", step.description, str(current_status)), tags=(tag,))

    tree_res.insert("", "end", values=("KẾT LUẬN", mock_result.reason, str(mock_result.status)),
                    tags=("error" if "OUT" in str(mock_result.status) or "ERROR" in str(mock_result.status) else "ok",))


def show_error_dialog(message):
    """Hàm hiển thị hộp thoại báo lỗi trực quan với Icon cảnh báo khi nạp file CSV sai định dạng."""
    messagebox.showerror("Lỗi Dữ Liệu CSV", message)
def validate_and_load_csv(filepath):
    """
    Hàm hỗ trợ nạp và kiểm tra tính hợp lệ của file CSV trước khi đưa lên GUI.
    Nếu file bị lỗi cấu trúc, kích hoạt ngay hộp thoại show_error_dialog.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)

            # Kiểm tra định dạng cơ bản: Phải có đủ 4 cột
            if not header or len(header) < 4:
                raise ValueError("File CSV không đủ 4 cột tiêu chuẩn (seg_id, base, limit, perm).")

            return list(reader)
    except Exception as e:
        show_error_dialog(f"Không thể đọc file CSV!\nNguyên nhân: {str(e)}")
        return None
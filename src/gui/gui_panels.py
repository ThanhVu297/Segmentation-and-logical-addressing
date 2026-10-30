import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
#
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.result_types import Status, Step, TranslationResult


def create_gui_panels(parent, cb_open_csv=None, cb_translate=None, cb_next_step=None, cb_export=None):
    """Hàm tạo giao diện, nhận parent (root/frame) và các callback từ main.py"""
    main_frame = tk.Frame(parent)

    # --- 1. BẢNG SEGMENT TABLE ---
    frame_top = tk.LabelFrame(main_frame, text="1. Segment Table", font=("Arial", 10, "bold"))
    frame_top.pack(pady=10, padx=10, fill="x")

    tk.Button(frame_top, text="Mở file CSV", command=cb_open_csv).pack(side="left", padx=10, pady=5)

    columns_seg = ("seg_id", "base", "limit", "perm")
    tree_seg = ttk.Treeview(frame_top, columns=columns_seg, show="headings", height=5)
    for col in columns_seg:
        tree_seg.heading(col, text=col.upper())
    tree_seg.pack(padx=10, pady=5, fill="x")

    # --- 2. FORM NHẬP ĐỊA CHỈ (Sử dụng StringVar) ---
    frame_mid = tk.LabelFrame(main_frame, text="2. Dịch địa chỉ đơn lẻ", font=("Arial", 10, "bold"))
    frame_mid.pack(pady=10, padx=10, fill="x")

    seg_var = tk.StringVar()
    offset_var = tk.StringVar()
    access_var = tk.StringVar()

    tk.Label(frame_mid, text="Segment:").grid(row=0, column=0, padx=5, pady=10)
    tk.Entry(frame_mid, textvariable=seg_var, width=10).grid(row=0, column=1, padx=5)

    tk.Label(frame_mid, text="Offset:").grid(row=0, column=2, padx=5)
    tk.Entry(frame_mid, textvariable=offset_var, width=10).grid(row=0, column=3, padx=5)

    tk.Label(frame_mid, text="Access (R/W/X):").grid(row=0, column=4, padx=5)
    tk.Entry(frame_mid, textvariable=access_var, width=10).grid(row=0, column=5, padx=5)

    # Đóng gói dữ liệu từ StringVar truyền ra ngoài qua callback cb_translate
    def on_translate():
        if cb_translate:
            cb_translate(seg_var.get(), offset_var.get(), access_var.get())

    tk.Button(frame_mid, text="Dịch địa chỉ", bg="lightblue", command=on_translate).grid(row=0, column=6, padx=15)

    # --- 3. BẢNG KẾT QUẢ TỪNG BƯỚC ---
    frame_bot = tk.LabelFrame(main_frame, text="3. Bảng kết quả từng bước", font=("Arial", 10, "bold"))
    frame_bot.pack(pady=10, padx=10, fill="both", expand=True)

    columns_res = ("step", "detail", "status")
    tree_res = ttk.Treeview(frame_bot, columns=columns_res, show="headings", height=8)
    tree_res.heading("step", text="Bước")
    tree_res.heading("detail", text="Chi tiết")
    tree_res.heading("status", text="Trạng thái")

    tree_res.tag_configure("error", background="#ffcccc")
    tree_res.tag_configure("ok", background="#ccffcc")
    tree_res.pack(padx=10, pady=5, fill="both", expand=True)

    # --- 4. CÁC NÚT ĐIỀU KHIỂN ---
    frame_ctrl = tk.Frame(main_frame)
    frame_ctrl.pack(pady=10)

    tk.Button(frame_ctrl, text="Bước tiếp", width=15, command=cb_next_step).pack(side="left", padx=15)
    tk.Button(frame_ctrl, text="Xuất kết quả", width=15, command=cb_export).pack(side="left", padx=15)

    return main_frame, tree_seg, tree_res


# =======================================================
# KHU VỰC CHẠY THỬ (Chỉ chạy khi mở trực tiếp file này)
# =======================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("OS_MEM_12  -  Test GUI Panels")
    root.geometry("800x600")


    # Các hàm giả để test callback
    def mock_open_csv():
        messagebox.showinfo("Test", "Main: Đã nhận lệnh mở CSV!")


    def mock_translate(seg, offset, acc):
        messagebox.showinfo("Test", f"Main nhận dữ liệu: Seg={seg}, Offset={offset}, Access={acc}")


    # Gọi UI, gắn parent là root
    gui_frame, tree_seg, tree_res = create_gui_panels(
        parent=root,
        cb_open_csv=mock_open_csv,
        cb_translate=mock_translate
    )
    gui_frame.pack(fill="both", expand=True)

    # Sử dụng dữ liệu giả từ core/result_types.py theo yêu cầu
    step1 = Step(description="Tra bảng Segment ID = 0", ok=True)
    step2 = Step(description="Kiểm tra Offset > Limit", ok=False)

    mock_result = TranslationResult(
        seg_id=0, offset=400, access="R",
        status=Status.OFFSET_OUT_OF_RANGE,
        reason="Độ lệch vượt giới hạn",
        steps=[step1, step2]
    )

    # Chèn dữ liệu giả vào bảng
    tree_res.insert("", "end", values=("1", mock_result.steps[0].description, Status.OK.value), tags=("ok",))
    tree_res.insert("", "end", values=("2", mock_result.steps[1].description, mock_result.status.value),
                    tags=("error",))

    root.mainloop()
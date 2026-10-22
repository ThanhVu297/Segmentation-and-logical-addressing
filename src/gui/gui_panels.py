import tkinter as tk
from tkinter import ttk, messagebox

def mock_open_csv():
    # Hộp thoại báo lỗi trực quan khi nạp file CSV sai
    messagebox.showerror("Lỗi file CSV", "File CSV sai định dạng hoặc bị rỗng!")

root = tk.Tk()
root.title("OS_MEM_12 - Phân đoạn và địa chỉ logic")
root.geometry("800x600")

# --- 1. BẢNG HIỂN THỊ SEGMENT TABLE & NÚT MỞ CSV ---
frame_top = tk.LabelFrame(root, text="1. Segment Table", font=("Arial", 10, "bold"))
frame_top.pack(pady=10, padx=10, fill="x")

btn_open_csv = tk.Button(frame_top, text="Mở file CSV", command=mock_open_csv)
btn_open_csv.pack(side="left", padx=10, pady=5)

columns_seg = ("seg_id", "base", "limit", "perm")
tree_seg = ttk.Treeview(frame_top, columns=columns_seg, show="headings", height=5)
for col in columns_seg:
    tree_seg.heading(col, text=col.upper())
tree_seg.pack(padx=10, pady=5, fill="x")

# --- 2. FORM NHẬP ĐỊA CHỈ ĐƠN LẺ ---
frame_mid = tk.LabelFrame(root, text="2. Dịch địa chỉ đơn lẻ", font=("Arial", 10, "bold"))
frame_mid.pack(pady=10, padx=10, fill="x")

tk.Label(frame_mid, text="Segment:").grid(row=0, column=0, padx=5, pady=10)
tk.Entry(frame_mid, width=10).grid(row=0, column=1, padx=5)

tk.Label(frame_mid, text="Offset:").grid(row=0, column=2, padx=5)
tk.Entry(frame_mid, width=10).grid(row=0, column=3, padx=5)

tk.Label(frame_mid, text="Access (R/W/X):").grid(row=0, column=4, padx=5)
tk.Entry(frame_mid, width=10).grid(row=0, column=5, padx=5)

tk.Button(frame_mid, text="Dịch địa chỉ", bg="lightblue", font=("Arial", 9, "bold")).grid(row=0, column=6, padx=15)

# --- 3. BẢNG KẾT QUẢ TỪNG BƯỚC ---
frame_bot = tk.LabelFrame(root, text="3. Bảng kết quả từng bước", font=("Arial", 10, "bold"))
frame_bot.pack(pady=10, padx=10, fill="both", expand=True)

columns_res = ("step", "detail", "status")
tree_res = ttk.Treeview(frame_bot, columns=columns_res, show="headings", height=8)
tree_res.heading("step", text="Bước")
tree_res.heading("detail", text="Chi tiết")
tree_res.heading("status", text="Trạng thái")

# Cấu hình màu highlight xanh/đỏ cho dòng lỗi và hợp lệ
tree_res.tag_configure("error", background="#ffcccc")
tree_res.tag_configure("ok", background="#ccffcc")

# Chèn thử 2 dòng dữ liệu giả để test màu
tree_res.insert("", "end", values=("1", "Tra bảng Segment ID = 0", "Hợp lệ"), tags=("ok",))
tree_res.insert("", "end", values=("2", "Kiểm tra Offset > Limit", "LỖI: OFFSET_OUT_OF_RANGE"), tags=("error",))

tree_res.pack(padx=10, pady=5, fill="both", expand=True)

# --- 4. CÁC NÚT ĐIỀU KHIỂN BƯỚC VÀ XUẤT FILE ---
frame_ctrl = tk.Frame(root)
frame_ctrl.pack(pady=10)

tk.Button(frame_ctrl, text="Bước tiếp (Step-by-step)", width=20).pack(side="left", padx=15)
tk.Button(frame_ctrl, text="Xuất kết quả ra CSV", width=20).pack(side="left", padx=15)

if __name__ == "__main__":
    root.mainloop()
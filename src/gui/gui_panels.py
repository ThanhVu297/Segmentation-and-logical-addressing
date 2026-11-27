import csv
import tkinter as tk
from tkinter import ttk, messagebox


def _make_btn(parent, text, command, bg="#ffffff", fg="#1e293b", border="#cbd5e1", bold=False, padx=10, pady=3):
    font = ("Segoe UI", 8, "bold") if bold else ("Segoe UI", 8)
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        activebackground=bg,
        activeforeground=fg,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=border,
        font=font,
        padx=padx,
        pady=pady,
        cursor="hand2",
    )
    return btn


def create_gui_panels(
    parent,
    cb_open_seg_csv=None,
    cb_clear_seg=None,
    cb_add_seg=None,
    cb_open_addr_csv=None,
    cb_clear_addr=None,
    cb_add_addr=None,
    cb_translate_selected=None,
    cb_translate_all=None,
    cb_next_step=None,
    cb_export=None,
):
    """Tạo giao diện hai cột với đầy đủ dấu tiếng Việt."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Modern.Treeview",
        background="#ffffff",
        foreground="#1e293b",
        rowheight=24,
        fieldbackground="#ffffff",
        bordercolor="#cbd5e1",
        borderwidth=1,
        font=("Segoe UI", 8),
    )
    style.configure(
        "Modern.Treeview.Heading",
        background="#e2e8f0",
        foreground="#334155",
        font=("Segoe UI", 8, "bold"),
        relief="flat",
    )

    main_frame = tk.Frame(parent, bg="#f1f5f9", padx=12, pady=8)
    main_frame.columnconfigure(0, weight=11)
    main_frame.columnconfigure(1, weight=12)
    main_frame.rowconfigure(0, weight=1)

    # ==================== CỘT TRÁI (MỤC 1, 2, 3) ====================
    left_col = tk.Frame(main_frame, bg="#f1f5f9")
    left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

    tk.Label(
        left_col, text="1. BẢNG PHÂN ĐOẠN (SEGMENT TABLE)",
        bg="#f1f5f9", fg="#334155", font=("Segoe UI", 9, "bold")
    ).pack(anchor="w")

    bar1 = tk.Frame(left_col, bg="#f1f5f9")
    bar1.pack(fill="x", pady=(2, 3))
    lbl_seg_count = tk.Label(
        bar1, text="0 SEGMENT", bg="#f1f5f9", fg="#0284c7", font=("Segoe UI", 8, "bold")
    )
    lbl_seg_count.pack(side="left")

    _make_btn(bar1, "Xóa hết", cb_clear_seg, bg="#ffffff", fg="#dc2626").pack(side="right", padx=(4, 0))
    _make_btn(bar1, "Mở tệp CSV", cb_open_seg_csv, bg="#ffffff", fg="#334155").pack(side="right")

    cols_seg = ("seg_id", "base", "limit", "perm", "action")
    tree_seg = ttk.Treeview(left_col, columns=cols_seg, show="headings", height=4, style="Modern.Treeview")
    for col, title, w in [
        ("seg_id", "Mã Segment", 75),
        ("base", "Base", 85),
        ("limit", "Limit", 85),
        ("perm", "Quyền", 85),
        ("action", "Thao tác", 85),
    ]:
        tree_seg.heading(col, text=title)
        tree_seg.column(col, width=w, anchor="center")
    tree_seg.pack(fill="x")

    form1 = tk.Frame(left_col, bg="#f1f5f9")
    form1.pack(fill="x", pady=(5, 8))

    seg_id_var = tk.StringVar()
    base_var = tk.StringVar()
    limit_var = tk.StringVar()
    perm_var = tk.StringVar(value="R-X")

    tk.Label(form1, text="Mã Segment", bg="#f1f5f9", fg="#475569", font=("Segoe UI", 8)).pack(side="left")
    tk.Entry(form1, textvariable=seg_id_var, width=5, relief="solid", bd=1).pack(side="left", padx=(3, 8))

    tk.Label(form1, text="Base (byte)", bg="#f1f5f9", fg="#475569", font=("Segoe UI", 8)).pack(side="left")
    tk.Entry(form1, textvariable=base_var, width=8, relief="solid", bd=1).pack(side="left", padx=(3, 8))

    tk.Label(form1, text="Limit (byte)", bg="#f1f5f9", fg="#475569", font=("Segoe UI", 8)).pack(side="left")
    tk.Entry(form1, textvariable=limit_var, width=8, relief="solid", bd=1).pack(side="left", padx=(3, 8))

    tk.Label(form1, text="Quyền", bg="#f1f5f9", fg="#475569", font=("Segoe UI", 8)).pack(side="left")
    ttk.Combobox(
        form1, textvariable=perm_var, values=["R-X", "RW-", "R--", "RWX", "---"],
        width=5, state="readonly"
    ).pack(side="left", padx=(3, 8))

    _make_btn(
        form1, "+ Thêm / Cập nhật",
        lambda: cb_add_seg(seg_id_var.get(), base_var.get(), limit_var.get(), perm_var.get()) if cb_add_seg else None,
        bg="#0284c7", fg="#ffffff", border="#0284c7", bold=True
    ).pack(side="left")

    # ==================== 2. BẢNG ĐỊA CHỈ LOGIC ====================
    tk.Label(
        left_col, text="2. BẢNG ĐỊA CHỈ LOGIC (LOGICAL ADDRESS TABLE)",
        bg="#f1f5f9", fg="#334155", font=("Segoe UI", 9, "bold")
    ).pack(anchor="w")

    bar2 = tk.Frame(left_col, bg="#f1f5f9")
    bar2.pack(fill="x", pady=(2, 3))
    lbl_addr_count = tk.Label(
        bar2, text="0 ĐỊA CHỈ", bg="#f1f5f9", fg="#0284c7", font=("Segoe UI", 8, "bold")
    )
    lbl_addr_count.pack(side="left")

    _make_btn(bar2, "Xóa hết", cb_clear_addr, bg="#ffffff", fg="#dc2626").pack(side="right", padx=(4, 0))
    _make_btn(bar2, "Mở tệp CSV", cb_open_addr_csv, bg="#ffffff", fg="#334155").pack(side="right")

    cols_addr = ("stt", "seg_id", "offset", "access", "action")
    tree_addr = ttk.Treeview(left_col, columns=cols_addr, show="headings", height=4, style="Modern.Treeview")
    for col, title, w in [
        ("stt", "STT", 45),
        ("seg_id", "Mã Segment", 90),
        ("offset", "Offset", 90),
        ("access", "Quyền truy cập", 80),
        ("action", "Thao tác", 90),
    ]:
        tree_addr.heading(col, text=title)
        tree_addr.column(col, width=w, anchor="center")
    tree_addr.pack(fill="x")

    form2 = tk.Frame(left_col, bg="#f1f5f9")
    form2.pack(fill="x", pady=(5, 5))

    addr_seg_var = tk.StringVar()
    addr_offset_var = tk.StringVar()
    addr_access_var = tk.StringVar(value="R")

    tk.Label(form2, text="Mã Segment", bg="#f1f5f9", fg="#475569", font=("Segoe UI", 8)).pack(side="left")
    tk.Entry(form2, textvariable=addr_seg_var, width=6, relief="solid", bd=1).pack(side="left", padx=(3, 10))

    tk.Label(form2, text="Offset", bg="#f1f5f9", fg="#475569", font=("Segoe UI", 8)).pack(side="left")
    tk.Entry(form2, textvariable=addr_offset_var, width=9, relief="solid", bd=1).pack(side="left", padx=(3, 10))

    tk.Label(form2, text="Quyền truy cập", bg="#f1f5f9", fg="#475569", font=("Segoe UI", 8)).pack(side="left")
    ttk.Combobox(
        form2, textvariable=addr_access_var, values=["R", "W", "X"],
        width=4, state="readonly"
    ).pack(side="left", padx=(3, 10))

    _make_btn(
        form2, "+ Thêm địa chỉ",
        lambda: cb_add_addr(addr_seg_var.get(), addr_offset_var.get(), addr_access_var.get()) if cb_add_addr else None,
        bg="#0284c7", fg="#ffffff", border="#0284c7", bold=True
    ).pack(side="left")

    action_row = tk.Frame(left_col, bg="#f1f5f9")
    action_row.pack(fill="x", pady=(2, 8))
    action_row.columnconfigure(0, weight=1)
    action_row.columnconfigure(1, weight=1)

    btn_sel = _make_btn(
        action_row, "Dịch dòng đang chọn", cb_translate_selected,
        bg="#0284c7", fg="#ffffff", border="#0284c7", bold=True, pady=5
    )
    btn_sel.grid(row=0, column=0, sticky="ew", padx=(0, 4))

    btn_all = _make_btn(
        action_row, "Dịch tất cả", cb_translate_all,
        bg="#15803d", fg="#ffffff", border="#15803d", bold=True, pady=5
    )
    btn_all.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    tk.Label(
        left_col, text="3. BẢNG KẾT QUẢ DỊCH ĐỊA CHỈ",
        bg="#f1f5f9", fg="#334155", font=("Segoe UI", 9, "bold")
    ).pack(anchor="w", pady=(0, 2))

    res_container = tk.Frame(left_col, bg="#f1f5f9")
    res_container.pack(fill="both", expand=True)
    res_container.rowconfigure(0, weight=1)
    res_container.columnconfigure(0, weight=1)

    res_columns = ("step", "detail", "status")
    tree_res = ttk.Treeview(res_container, columns=res_columns, show="headings", height=5, style="Modern.Treeview")
    tree_res.heading("step", text="Bước")
    tree_res.heading("detail", text="Nội dung xử lý")
    tree_res.heading("status", text="Trạng thái")

    tree_res.column("step", width=85, minwidth=85, stretch=False, anchor="center")
    tree_res.column("detail", width=330, minwidth=280, stretch=False, anchor="w")
    tree_res.column("status", width=115, minwidth=110, stretch=False, anchor="center")

    y_scroll3 = ttk.Scrollbar(res_container, orient="vertical", command=tree_res.yview)
    x_scroll3 = ttk.Scrollbar(res_container, orient="horizontal", command=tree_res.xview)
    tree_res.configure(yscrollcommand=y_scroll3.set, xscrollcommand=x_scroll3.set)

    tree_res.grid(row=0, column=0, sticky="nsew")
    y_scroll3.grid(row=0, column=1, sticky="ns")
    x_scroll3.grid(row=1, column=0, sticky="ew")

    tree_res.tag_configure("ok", background="#dcfce7", foreground="#166534")
    tree_res.tag_configure("error", background="#fee2e2", foreground="#991b1b")

    bottom_left = tk.Frame(left_col, bg="#f1f5f9")
    bottom_left.pack(fill="x", pady=(6, 0))
    _make_btn(bottom_left, "Bước tiếp theo →", cb_next_step, bg="#ffffff", fg="#334155").pack(side="left")

    # ==================== CỘT PHẢI (MỤC 4, 5) ====================
    right_col = tk.Frame(main_frame, bg="#f1f5f9")
    right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    tk.Label(
        right_col, text="4. SƠ ĐỒ BỘ NHỚ (5000 BYTE)",
        bg="#f1f5f9", fg="#334155", font=("Segoe UI", 9, "bold")
    ).pack(anchor="w", pady=(0, 3))

    canvas = tk.Canvas(
        right_col, width=520, height=265, bg="#ffffff",
        highlightthickness=1, highlightbackground="#cbd5e1"
    )
    canvas.pack(fill="both", expand=True)

    legend_frame = tk.Frame(right_col, bg="#f1f5f9")
    legend_frame.pack(fill="x", pady=(4, 2))
    legends = [
        ("#0284c7", "R-X"),
        ("#d97706", "RW-"),
        ("#16a34a", "R--"),
        ("#64748b", "Khác"),
        ("#f8fafc", "Trống"),
    ]
    for color, text in legends:
        box = tk.Label(legend_frame, bg=color, width=2, relief="solid", bd=1)
        box.pack(side="left", padx=(0, 3))
        tk.Label(legend_frame, text=text, bg="#f1f5f9", fg="#475569", font=("Segoe UI", 7)).pack(side="left", padx=(0, 8))

    tk.Label(
        legend_frame, text="--- Địa chỉ vật lý vừa dịch",
        bg="#f1f5f9", fg="#dc2626", font=("Segoe UI", 7, "bold")
    ).pack(side="left")

    lbl_map_status = tk.Label(
        right_col, text="TRẠNG THÁI: Sẵn sàng.",
        bg="#f1f5f9", fg="#334155", font=("Segoe UI", 8, "bold")
    )
    lbl_map_status.pack(anchor="w", pady=(0, 6))

    tk.Label(
        right_col, text="5. KẾT QUẢ TỔNG HỢP",
        bg="#f1f5f9", fg="#334155", font=("Segoe UI", 9, "bold")
    ).pack(anchor="w")

    bar5 = tk.Frame(right_col, bg="#f1f5f9")
    bar5.pack(fill="x", pady=(2, 3))
    lbl_batch_status = tk.Label(
        bar5, text="Chưa có kết quả", bg="#f1f5f9", fg="#d97706", font=("Segoe UI", 8, "bold")
    )
    lbl_batch_status.pack(side="left")

    _make_btn(bar5, "Xuất kết quả CSV", cb_export, bg="#ffffff", fg="#334155").pack(side="right")

    summary_container = tk.Frame(right_col, bg="#f1f5f9")
    summary_container.pack(fill="both", expand=True)
    summary_container.rowconfigure(0, weight=1)
    summary_container.columnconfigure(0, weight=1)

    summary_cols = ("stt", "seg_id", "base", "limit", "offset", "access", "physical", "status", "reason")
    tree_summary = ttk.Treeview(
        summary_container, columns=summary_cols, show="headings", height=7, style="Modern.Treeview"
    )
    for col, title, w in [
        ("stt", "STT", 38),
        ("seg_id", "Mã Segment", 65),
        ("base", "BASE", 55),
        ("limit", "LIMIT", 55),
        ("offset", "OFFSET", 58),
        ("access", "Quyền", 52),
        ("physical", "Địa chỉ vật lý", 78),
        ("status", "Trạng thái", 175),
        ("reason", "Lý do", 320),
    ]:
        tree_summary.heading(col, text=title)
        tree_summary.column(
            col,
            width=w,
            minwidth=w,
            stretch=False,
            anchor="w" if col == "reason" else "center",
        )

    y_scroll5 = ttk.Scrollbar(summary_container, orient="vertical", command=tree_summary.yview)
    x_scroll5 = ttk.Scrollbar(summary_container, orient="horizontal", command=tree_summary.xview)
    tree_summary.configure(yscrollcommand=y_scroll5.set, xscrollcommand=x_scroll5.set)

    tree_summary.grid(row=0, column=0, sticky="nsew")
    y_scroll5.grid(row=0, column=1, sticky="ns")
    x_scroll5.grid(row=1, column=0, sticky="ew")

    tree_summary.tag_configure("ok", background="#dcfce7", foreground="#166534")
    tree_summary.tag_configure("error", background="#fee2e2", foreground="#991b1b")

    return {
        "main_frame": main_frame,
        "tree_seg": tree_seg,
        "lbl_seg_count": lbl_seg_count,
        "tree_addr": tree_addr,
        "lbl_addr_count": lbl_addr_count,
        "tree_res": tree_res,
        "canvas": canvas,
        "lbl_map_status": lbl_map_status,
        "tree_summary": tree_summary,
        "lbl_batch_status": lbl_batch_status,
        "inputs": {
            "seg_id": seg_id_var,
            "base": base_var,
            "limit": limit_var,
            "perm": perm_var,
            "addr_seg": addr_seg_var,
            "addr_offset": addr_offset_var,
            "addr_access": addr_access_var,
        },
    }


def validate_and_load_csv(filepath):
    """Kiểm tra và đọc tệp CSV mã hóa UTF-8 (có hoặc không có BOM)."""
    try:
        with open(filepath, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            header = next(reader, None)
            if not header or len(header) < 3:
                raise ValueError("Tệp CSV không đúng định dạng cột.")
            rows = [r for r in reader if r]
            if not rows:
                raise ValueError("Tệp CSV không có dữ liệu.")
            return rows
    except Exception as e:
        messagebox.showerror("Lỗi dữ liệu CSV", f"Không thể đọc tệp CSV!\nNguyên nhân: {str(e)}")
        return None

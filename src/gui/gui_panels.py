
import tkinter as tk
from tkinter import ttk, messagebox
import csv


def create_gui_panels(parent):
    """
    Tao giao dien quan ly phan doan va dich dia chi logic.
    Gom Segment Table, form nhap dia chi va bang ket qua.
    """

    gui_frame = ttk.Frame(parent, padding=10)
    gui_frame.pack(fill="both", expand=True)

    # 1. SEGMENT TABLE
    seg_frame = ttk.LabelFrame(
        gui_frame,
        text="1. Segment Table",
        padding=10
    )
    seg_frame.pack(fill="x", pady=5)

    btn_open_csv = ttk.Button(
        seg_frame,
        text="Mở file CSV"
    )
    btn_open_csv.pack(side="left", padx=5)

    columns = ("seg_id", "base", "limit", "perm")

    tree_seg = ttk.Treeview(
        seg_frame,
        columns=columns,
        show="headings",
        height=4
    )

    tree_seg.heading("seg_id", text="SEG_ID")
    tree_seg.heading("base", text="BASE")
    tree_seg.heading("limit", text="LIMIT")
    tree_seg.heading("perm", text="PERM")

    tree_seg.column("seg_id", width=80, anchor="center")
    tree_seg.column("base", width=100, anchor="center")
    tree_seg.column("limit", width=100, anchor="center")
    tree_seg.column("perm", width=80, anchor="center")

    tree_seg.pack(side="left", fill="x", expand=True, padx=5)

    # 2. FORM NHAP DIA CHI DON LE
    input_frame = ttk.LabelFrame(
        gui_frame,
        text="2. Nhập địa chỉ đơn lẻ",
        padding=10
    )
    input_frame.pack(fill="x", pady=5)

    ttk.Label(input_frame, text="Segment:").pack(
        side="left", padx=2
    )

    seg_var = tk.StringVar()
    ttk.Entry(
        input_frame,
        textvariable=seg_var,
        width=10
    ).pack(side="left", padx=5)

    ttk.Label(input_frame, text="Offset:").pack(
        side="left", padx=2
    )

    offset_var = tk.StringVar()
    ttk.Entry(
        input_frame,
        textvariable=offset_var,
        width=10
    ).pack(side="left", padx=5)

    ttk.Label(input_frame, text="Access (R/W/X):").pack(
        side="left", padx=2
    )

    access_var = tk.StringVar()
    ttk.Entry(
        input_frame,
        textvariable=access_var,
        width=10
    ).pack(side="left", padx=5)

    btn_translate = ttk.Button(
        input_frame,
        text="Dịch địa chỉ"
    )
    btn_translate.pack(side="left", padx=10)

    # 3. BANG KET QUA TUNG BUOC
    res_frame = ttk.LabelFrame(
        gui_frame,
        text="3. Bảng kết quả từng bước",
        padding=10
    )
    res_frame.pack(fill="both", expand=True, pady=5)

    res_columns = ("step", "detail", "status")

    tree_res = ttk.Treeview(
        res_frame,
        columns=res_columns,
        show="headings",
        height=5
    )

    tree_res.heading("step", text="Bước")
    tree_res.heading("detail", text="Chi tiết")
    tree_res.heading("status", text="Trạng thái")

    tree_res.column("step", width=120, anchor="center")
    tree_res.column("detail", width=350, anchor="w")
    tree_res.column("status", width=150, anchor="center")

    tree_res.pack(fill="both", expand=True, pady=5)

    # Mau sac ket qua
    tree_res.tag_configure(
        "ok",
        background="#e6ffed"
    )

    tree_res.tag_configure(
        "error",
        background="#ffebe6"
    )

    # 4. CAC NUT DIEU KHIEN
    ctrl_frame = ttk.Frame(gui_frame, padding=5)
    ctrl_frame.pack(fill="x", pady=5)

    btn_next_step = ttk.Button(
        ctrl_frame,
        text="Bước tiếp"
    )
    btn_next_step.pack(side="left", expand=True, padx=5)

    btn_export = ttk.Button(
        ctrl_frame,
        text="Xuất kết quả"
    )
    btn_export.pack(side="left", expand=True, padx=5)

    # Tra ve 10 thanh phan de gui.py su dung
    return (
        gui_frame,
        tree_seg,
        tree_res,
        seg_var,
        offset_var,
        access_var,
        btn_open_csv,
        btn_translate,
        btn_next_step,
        btn_export
    )


# HIEN THI KET QUA DICH DIA CHI
def display_translation_result(tree_res, result):
    """
    Hien thi cac buoc dich dia chi.
    Buoc thanh cong mau xanh, buoc loi mau do.
    """

    # Xoa ket qua cu
    for item in tree_res.get_children():
        tree_res.delete(item)

    # Hien thi tung buoc
    for idx, step in enumerate(result.steps, start=1):

        if step.ok:
            tag = "ok"
            step_status = "Thành công"
        else:
            tag = "error"
            step_status = "Thất bại"

        tree_res.insert(
            "",
            "end",
            values=(
                f"Buoc {idx}",
                step.description,
                step_status
            ),
            tags=(tag,)
        )

    # Hien thi ket qua cuoi cung
    status = result.status.value

    if status == "OK":
        tag = "ok"
    else:
        tag = "error"

    reason = result.reason

    if result.physical is not None:
        reason += f" | Dia chi vat ly: {result.physical}"

    tree_res.insert(
        "",
        "end",
        values=(
            "KET LUAN",
            reason,
            status
        ),
        tags=(tag,)
    )


# HIEN THI THONG BAO LOI
def show_error_dialog(message):
    messagebox.showerror(
        "Loi du lieu CSV",
        message
    )


# KIEM TRA VA DOC FILE CSV
def validate_and_load_csv(filepath):
    """
    Kiem tra file CSV co du 4 cot can thiet hay khong.
    """

    try:
        with open(
            filepath,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.reader(file)
            header = next(reader, None)

            if not header or len(header) < 4:
                raise ValueError(
                    "File CSV phai co 4 cot: "
                    "seg_id, base, limit, perm."
                )

            rows = list(reader)

            if not rows:
                raise ValueError("File CSV khong co du lieu.")

            for row in rows:
                if len(row) < 4:
                    raise ValueError(
                        "Mot dong trong file CSV khong du 4 cot."
                    )

            return rows

    except Exception as e:
        show_error_dialog(
            f"Khong the doc file CSV!\nNguyen nhan: {str(e)}"
        )
        return None

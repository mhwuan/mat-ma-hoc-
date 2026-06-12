"""Simplified Tkinter GUI for RSA low public exponent demo.

This version is designed for presentation:
- User enters plaintext text, app converts it to integer m.
- Shows RSA key generation, encryption/decryption, and direct root attack step by step.
- Shows Håstad broadcast attack step by step.
- Removes the separate comparison tab to reduce UI clutter.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from rsa_core import TextbookRSA
from hastad_attack import run_hastad_attack
from math_utils import integer_root
from ui_helpers import short_num, status_text


BG = "#f5f6fa"
PANEL = "#ffffff"
TEXT = "#1f2937"
MUTED = "#6b7280"
GOOD = "#0f766e"
BAD = "#b91c1c"

SUPERSCRIPT = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def pow_text(base: str, exp: int) -> str:
    return f"{base}{str(exp).translate(SUPERSCRIPT)}"


def root_symbol(e: int, value: str) -> str:
    if e == 2:
        return f"√{value}"
    if e == 3:
        return f"∛{value}"
    return f"{str(e).translate(SUPERSCRIPT)}√{value}"


def section(title: str) -> str:
    # Tạo khoảng cách giữa các phần, không dùng đường kẻ dài để giao diện dễ đọc hơn.
    return f"\n\n{title}\n\n"


def bytes_as_hex(message: str) -> str:
    return message.encode("utf-8").hex(" ").upper()


class HastadDemoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Đề tài 05 - RSA số mũ nhỏ: minh họa dễ hiểu")
        self.root.geometry("1180x780")
        self.root.configure(bg=BG)
        self._setup_style()
        self._build_layout()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 10), font=("Arial", 11, "bold"))
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=PANEL, relief="solid", borderwidth=1)
        style.configure("Title.TLabel", background=PANEL, foreground=TEXT, font=("Arial", 16, "bold"))
        style.configure("Sub.TLabel", background=PANEL, foreground=MUTED, font=("Arial", 10))
        style.configure("Normal.TLabel", background=PANEL, foreground=TEXT, font=("Arial", 11))
        style.configure("Primary.TButton", font=("Arial", 11, "bold"), padding=(12, 8))

    def _build_layout(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=16, pady=16)

        self.tab_direct = ttk.Frame(notebook)
        self.tab_hastad = ttk.Frame(notebook)

        notebook.add(self.tab_direct, text="1. RSA + khai căn trực tiếp")
        notebook.add(self.tab_hastad, text="2. Håstad + CRT")

        self._build_direct_tab()
        self._build_hastad_tab()

    def _card(self, parent, title: str, subtitle: str | None = None):
        frame = ttk.Frame(parent, style="Card.TFrame", padding=14)
        ttk.Label(frame, text=title, style="Title.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(frame, text=subtitle, style="Sub.TLabel").pack(anchor="w", pady=(2, 10))
        return frame

    def _entry_row(self, parent, label: str, default: str, width: int = 40):
        row = ttk.Frame(parent, style="Card.TFrame")
        row.pack(fill="x", pady=5)
        ttk.Label(row, text=label, style="Normal.TLabel", width=25).pack(side="left")
        entry = ttk.Entry(row, width=width, font=("Consolas", 11))
        entry.insert(0, default)
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def _make_log(self, parent, font_size: int = 11):
        return scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=("Consolas", font_size),
            bg="#111827",
            fg="#e5e7eb",
            insertbackground="#ffffff",
            relief="flat",
            padx=14,
            pady=14,
        )

    def _build_direct_tab(self):
        left = self._card(
            self.tab_direct,
            "RSA textbook và tấn công khai căn trực tiếp",
            "Bạn nhập thông điệp dạng chữ. Chương trình tự chuyển thông điệp thành số m rồi mới mã hóa RSA.",
        )
        left.pack(side="left", fill="y", padx=(0, 10), pady=8)

        self.direct_message = self._entry_row(left, "Thông điệp bản rõ", "A", 32)
        self.direct_e = self._entry_row(left, "Số mũ công khai e", "3", 16)
        self.direct_key_size = self._entry_row(left, "Kích thước khóa demo", "128", 16)

        ttk.Button(
            left,
            text="Chạy và giải từng bước",
            style="Primary.TButton",
            command=self.run_direct,
        ).pack(anchor="w", pady=12)

        # note = tk.Label(
        #     left,
        #     text=(
        #         "Cách demo dễ hiểu:\n"
        #         "1. Nhập bản rõ ngắn, ví dụ A hoặc Hi.\n"
        #         "2. App đổi chữ thành số m.\n"
        #         "3. App mã hóa: c = m³ mod n.\n"
        #         "4. Nếu m³ < n, app khai căn ∛c để lấy lại m.\n\n"
        #         "Lưu ý: đây là RSA textbook không padding, chỉ dùng để minh họa lỗ hổng."
        #     ),
        #     bg=PANEL,
        #     fg=MUTED,
        #     justify="left",
        #     font=("Arial", 10),
        # )
        # note.pack(anchor="w", pady=10)

        right = ttk.Frame(self.tab_direct)
        right.pack(side="left", fill="both", expand=True, pady=8)

        self.direct_summary = self._card(right, "Kết luận nhanh")
        self.direct_summary.pack(fill="x", pady=(0, 10))
        self.direct_summary_text = tk.Label(
            self.direct_summary,
            text="Chưa chạy demo.",
            bg=PANEL,
            fg=TEXT,
            justify="left",
            font=("Arial", 12, "bold"),
        )
        self.direct_summary_text.pack(anchor="w", pady=6)

        self.direct_log = self._make_log(right, 11)
        self.direct_log.pack(fill="both", expand=True)

    def run_direct(self):
        try:
            message = self.direct_message.get()
            e = int(self.direct_e.get())
            key_size = int(self.direct_key_size.get())
            if not message:
                raise ValueError("Thông điệp không được rỗng.")
            if e <= 1 or e % 2 == 0:
                raise ValueError("e phải là số lẻ lớn hơn 1, ví dụ 3 hoặc 5.")

            rsa = TextbookRSA(key_size=key_size)
            keypair = rsa.generate_keypair(e=e)

            m = rsa.message_to_int(message)
            if m >= keypair.public.n:
                raise ValueError("m >= n. Thông điệp quá dài. Hãy nhập ngắn hơn hoặc tăng key_size.")

            n = keypair.public.n
            d = keypair.private.d
            p = keypair.p
            q = keypair.q
            lambda_n = keypair.lambda_n
            m_pow_e = m ** e
            c = rsa.encrypt_int(m, keypair.public)
            decrypted_m = rsa.decrypt_int(c, keypair.private)
            decrypted_text = rsa.int_to_message(decrypted_m)
            root, exact = integer_root(c, e)
            recovered_text = rsa.int_to_message(root) if exact else "không khôi phục được text đúng"
            condition = m_pow_e < n
            success = exact and root == m
            quotient, remainder = divmod(m_pow_e, n)
        except Exception as ex:
            messagebox.showerror("Lỗi", str(ex))
            return

        conclusion = (
            "TẤN CÔNG THÀNH CÔNG: m^e < n nên c = m^e, khai căn c lấy lại được bản rõ."
            if success else
            "TẤN CÔNG THẤT BẠI: c đã bị modulo n, khai căn trực tiếp không ra bản rõ gốc."
        )
        self.direct_summary_text.configure(text=conclusion, fg=GOOD if success else BAD)

        me = pow_text("m", e)
        lines = [
            section("BƯỚC 1: CHUYỂN THÔNG ĐIỆP THÀNH SỐ"),
            f"Thông điệp người dùng nhập: {message!r}",
            f"Dạng byte UTF-8: {bytes_as_hex(message)}",
            "RSA không mã hóa trực tiếp chữ, mà mã hóa một số nguyên.",
            f"m = int(bytes) = {short_num(m)}",
            section("BƯỚC 2: SINH KHÓA RSA"),
            "Chương trình sinh hai số nguyên tố p và q:",
            f"p = {short_num(p)}",
            f"q = {short_num(q)}",
            "Tính modulus n:",
            "n = p × q",
            f"n = {short_num(n)}",
            "Tính lambda(n):",
            "λ(n) = lcm(p - 1, q - 1)",
            f"λ(n) = {short_num(lambda_n)}",
            "Chọn số mũ công khai:",
            f"e = {e}",
            "Tính khóa bí mật:",
            "d = e⁻¹ mod λ(n)",
            f"d = {short_num(d)}",
            "Khóa công khai: (e, n)",
            "Khóa bí mật:    (d, n)",
            section("BƯỚC 3: MÃ HÓA"),
            f"Công thức: c = {me} mod n",
            f"Tính {me}: {me} = {short_num(m_pow_e)}",
        ]

        if condition:
            lines += [
                f"So sánh: {me} < n -> {status_text(True)}",
                "Vì m^e nhỏ hơn n nên phép mod n chưa làm thay đổi giá trị.",
                "Do đó: c = m^e",
                f"c = {short_num(c)}",
            ]
        else:
            lines += [
                f"So sánh: {me} < n -> {status_text(False)}",
                "Vì m^e lớn hơn n nên RSA lấy phần dư modulo n.",
                "Có thể hiểu: m^e = q × n + r",
                f"q = {short_num(quotient)}",
                f"r = {short_num(remainder)}",
                "Do đó: c = r, không còn bằng m^e nguyên vẹn.",
                f"c = {short_num(c)}",
            ]

        lines += [
            section("BƯỚC 4: GIẢI MÃ HỢP LỆ"),
            "Người nhận hợp lệ có khóa bí mật d nên giải mã bằng công thức:",
            "m = c^d mod n",
            f"m giải mã = {short_num(decrypted_m)}",
            f"text giải mã = {decrypted_text!r}",
            f"Giải mã đúng như ban đầu nên {status_text(decrypted_m == m)}",
            section("BƯỚC 5: TẤN CÔNG KHAI CĂN"),
            "Kẻ tấn công không có d.",
            "Kẻ tấn công chỉ thử khai căn bản mã c:",
            f"{root_symbol(e, 'c')} = {root_symbol(e, short_num(c))} = {short_num(root)}",
            f"Khai căn chính xác : {exact}",
            f"Recovered m = {short_num(root)}",
            f"Recovered plaintext = {recovered_text!r}",
            f"So sánh Recovered với m ban đầu: {status_text(root == m)}",
            section("KẾT LUẬN"),
            conclusion,
        ]

        self.direct_log.delete("1.0", tk.END)
        self.direct_log.insert(tk.END, "\n".join(lines))

    def _build_hastad_tab(self):
        top = self._card(
            self.tab_hastad,
            "Håstad Broadcast Attack: cùng bản rõ gửi cho nhiều người",
            "Bạn nhập thông điệp dạng chữ. Chương trình tự chuyển sang số m, gửi cho e người nhận, rồi dùng CRT để tấn công.",
        )
        top.pack(fill="x", pady=8)

        self.hastad_message = self._entry_row(top, "Thông điệp chung", "Hi", 50)
        self.hastad_e = self._entry_row(top, "Số mũ công khai e", "3", 12)
        self.hastad_key_size = self._entry_row(top, "Kích thước khóa demo", "256", 12)

        ttk.Button(
            top,
            text="Chạy Håstad và giải từng bước",
            style="Primary.TButton",
            command=self.run_hastad,
        ).pack(anchor="w", pady=10)

        self.hastad_summary = self._card(self.tab_hastad, "Kết luận nhanh")
        self.hastad_summary.pack(fill="x", pady=(0, 10))
        self.hastad_summary_text = tk.Label(
            self.hastad_summary,
            text="Chưa chạy demo.",
            bg=PANEL,
            fg=TEXT,
            justify="left",
            font=("Arial", 12, "bold"),
        )
        self.hastad_summary_text.pack(anchor="w", pady=6)

        self.hastad_log = self._make_log(self.tab_hastad, 10)
        self.hastad_log.pack(fill="both", expand=True)

    def run_hastad(self):
        try:
            message = self.hastad_message.get()
            e = int(self.hastad_e.get())
            key_size = int(self.hastad_key_size.get())
            if not message:
                raise ValueError("Thông điệp không được rỗng.")
            result = run_hastad_attack(message, e=e, key_size=key_size)
        except Exception as ex:
            messagebox.showerror("Lỗi", str(ex))
            return

        conclusion = (
            "TẤN CÔNG HÅSTAD THÀNH CÔNG: CRT khôi phục X = m^e, sau đó khai căn lấy lại m."
            if result.success else
            "TẤN CÔNG HÅSTAD THẤT BẠI: chưa đủ điều kiện để CRT + khai căn phục hồi m."
        )
        self.hastad_summary_text.configure(text=conclusion, fg=GOOD if result.success else BAD)

        me = pow_text("m", result.e)
        lines = [

            section("BƯỚC 1: CHUYỂN THÔNG ĐIỆP THÀNH SỐ"),
            f"Thông điệp chung: {result.message_text!r}",
            f"Dạng byte UTF-8: {bytes_as_hex(result.message_text)}",
            f"m = int(bytes) = {short_num(result.m)}",
            f"e = {result.e}",
            f"Số người nhận cần có = e = {result.e}",
            section("BƯỚC 2: MÃ HÓA CHO TỪNG NGƯỜI NHẬN"),
            f"Công thức: c_i = {me} mod n_i",
        ]

        for r in result.recipients:
            lines += [
                "",
                f"Người nhận {r.index}:",
                f"n_{r.index} = {short_num(r.public_key.n)}",
                f"c_{r.index} = {me} mod n_{r.index}",
                f"c_{r.index} = {short_num(r.ciphertext)}",
            ]

        lines += [
            section("BƯỚC 3: LẬP HỆ ĐỒNG DƯ"),
            "Đặt X = m^e. Khi đó các bản mã cho ta:",
        ]
        for r in result.recipients:
            lines.append(f"X ≡ c_{r.index} (mod n_{r.index})")

        lines += [
            section("BƯỚC 4: CRT GHÉP CÁC PHƯƠNG TRÌNH"),
            "CRT cho phép ghép nhiều phương trình đồng dư thành một số X duy nhất trong modulo N.",
            f"N = n1 × n2 × ... × n{result.e}",
            f"N = {short_num(result.total_modulus)}",
            "",
            "Công thức từng dòng:",
            "N_i = N / n_i",
            "y_i = N_i⁻¹ mod n_i",
            "term_i = c_i × y_i × N_i",
            "X = (term_1 + term_2 + ... + term_e) mod N",
        ]

        for row in result.crt_rows:
            i = row["i"]
            lines += [
                "",
                f"Dòng CRT i = {i}",
                f"N_{i}    = N / n_{i} = {short_num(row['N_i'])}",
                f"y_{i}    = N_{i}⁻¹ mod n_{i} = {short_num(row['inverse_i'])}",
                f"term_{i} = c_{i} × y_{i} × N_{i}",
                f"term_{i} = {short_num(row['term_i'])}",
            ]

        lines += [
            "",
            "Sau khi cộng các term và lấy modulo N:",
            f"X = {short_num(result.crt_value)}",
            f"Trong điều kiện Håstad hợp lệ: X = {me}",
            section(f"BƯỚC 5: KHAI CĂN BẬC {result.e}"),
            f"{root_symbol(result.e, 'X')} = {short_num(result.root)}",
            f"Khai căn chính xác hay chưa: {result.exact_root}",
            f"Recovered m = {short_num(result.root)}",
            f"Recovered plaintext = {result.recovered_text!r}",
            f"So sánh Recovered với original: {status_text(result.root == result.m)}",
            section("KẾT LUẬN"),
            conclusion,
            "",
    
        ]

        self.hastad_log.delete("1.0", tk.END)
        self.hastad_log.insert(tk.END, "\n".join(lines))


if __name__ == "__main__":
    root = tk.Tk()
    app = HastadDemoApp(root)
    root.mainloop()

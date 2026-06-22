"""Simplified Tkinter GUI for RSA low public exponent demo.

Fixes:
- Button: tk.Label giả button (macOS-safe, nhận màu bg/fg)
- Label visibility: dùng TEXT thay MUTED cho input labels
- λ(n): hiển thị 3 dòng — công thức → thay số → kết quả
- Thuật toán GIỮ NGUYÊN 100%
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from rsa_core import TextbookRSA
from hastad_attack import run_hastad_attack
from math_utils import integer_root
from ui_helpers import short_num, status_text


# ── Colour palette ────────────────────────────────────────────────────────────
BG     = "#12141c"
PANEL  = "#1c1f2e"
BORDER = "#2a2d42"
ACCENT = "#4f8ef7"
TEXT   = "#e2e8f0"
MUTED  = "#64748b"
GOOD   = "#10b981"
BAD    = "#ef4444"

LOG_BG      = "#0d1117"
LOG_FG      = "#c9d1d9"
LOG_SECTION = "#f59e0b"
LOG_VALUE   = "#7ee787"
LOG_FORMULA = "#79c0ff"
LOG_SUCCESS = "#3fb950"
LOG_FAIL    = "#ff7b72"

SUPERSCRIPT = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
SUBSCRIPT   = str.maketrans("0123456789",  "₀₁₂₃₄₅₆₇₈₉")


# ── Helper functions (unchanged) ──────────────────────────────────────────────
def sub_text(base: str, index: int) -> str:
    return f"{base}{str(index).translate(SUBSCRIPT)}"

def pow_text(base: str, exp: int) -> str:
    return f"{base}{str(exp).translate(SUPERSCRIPT)}"

def root_symbol(e: int, value: str) -> str:
    if e == 2:
        return f"√{value}"
    if e == 3:
        return f"∛{value}"
    return f"{str(e).translate(SUPERSCRIPT)}√{value}"

def section(title: str) -> str:
    return f"\n\n{title}\n\n"

def bytes_as_hex(message: str) -> str:
    return message.encode("utf-8").hex(" ").upper()


# ── Log tagger (unchanged) ────────────────────────────────────────────────────
def _tag_for(line: str) -> str:
    s = line.strip()
    if not s:
        return "normal"
    if "THÀNH CÔNG" in s:
        return "success"
    if "THẤT BẠI" in s:
        return "fail"
    if any(kw in s for kw in ("BƯỚC", "KẾT LUẬN", "MỤC TIÊU")):
        return "section"
    if any(ch in s for ch in ("≡", "×", "⁻¹", "λ")):
        return "formula"
    if "=" in s and s[0].isalpha() and len(s) < 140:
        return "value"
    return "normal"


# ── App ───────────────────────────────────────────────────────────────────────
class HastadDemoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Đề tài 05 – RSA số mũ nhỏ: minh họa dễ hiểu")
        self.root.geometry("1200x800")
        self.root.configure(bg=BG)
        self._setup_styles()
        self._build_layout()

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure(
            "TNotebook.Tab",
            background=PANEL, foreground=MUTED,
            padding=(22, 10),
            font=("Arial", 11, "bold"),
        )
        s.map(
            "TNotebook.Tab",
            background=[("selected", ACCENT)],
            foreground=[("selected", "#ffffff")],
            expand=[("selected", [0, 0, 0, 2])],
        )
        s.configure("TFrame", background=BG)

    # ── Widget builders ───────────────────────────────────────────────────────

    def _card(self, parent, title: str):
        """Dark bordered card. Returns (outer, inner)."""
        outer = tk.Frame(parent, bg=PANEL,
                         highlightbackground=BORDER, highlightthickness=1)
        inner = tk.Frame(outer, bg=PANEL)
        inner.pack(fill="both", expand=True, padx=14, pady=12)
        tk.Label(inner, text=title, bg=PANEL, fg=TEXT,
                 font=("Arial", 13, "bold")).pack(anchor="w", pady=(0, 10))
        return outer, inner

    def _inline_entry(self, parent, label: str, default: str, width: int = 18):
        """Label + Entry nằm ngang. Label dùng TEXT để đủ tương phản trên nền tối."""
        group = tk.Frame(parent, bg=PANEL)
        group.pack(side="left", padx=(0, 16))
        # Dùng TEXT thay MUTED để chữ không bị chìm
        tk.Label(group, text=label, bg=PANEL, fg=TEXT,
                 font=("Arial", 10)).pack(side="left", padx=(0, 5))
        entry = tk.Entry(
            group, width=width,
            font=("Consolas", 11),
            bg="#0d1117", fg=TEXT,
            insertbackground=TEXT,
            relief="flat", bd=0,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            highlightthickness=1,
        )
        entry.insert(0, default)
        entry.pack(side="left")
        return entry

    def _run_btn(self, parent, text: str, command):
        """
        Dùng tk.Label thay tk.Button — macOS Aqua override bg/fg của Button,
        nhưng Label thì luôn nhận màu đúng.
        """
        btn = tk.Label(
            parent, text=text,
            bg=ACCENT, fg="#ffffff",
            font=("Arial", 11, "bold"),
            padx=18, pady=8,
            cursor="hand2",
        )
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>",    lambda e: btn.config(bg="#3b7de8"))
        btn.bind("<Leave>",    lambda e: btn.config(bg=ACCENT))
        btn.pack(side="left")
        return btn

    def _summary_card(self, parent):
        outer = tk.Frame(parent, bg=PANEL,
                         highlightbackground=BORDER, highlightthickness=1)
        lbl = tk.Label(
            outer, text="Chưa chạy demo.",
            bg=PANEL, fg=MUTED,
            font=("Arial", 12, "bold"),
            padx=16, pady=10,
            anchor="w", justify="left",
        )
        lbl.pack(fill="x")
        return outer, lbl

    def _update_summary(self, frame, lbl, text: str, success: bool):
        tint_bg = "#0a2318" if success else "#2b0d0d"
        fg      = GOOD if success else BAD
        frame.config(bg=tint_bg, highlightbackground=fg)
        lbl.config(text=text, bg=tint_bg, fg=fg)

    def _make_log(self, parent, font_size: int = 11):
        log = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=("Consolas", font_size),
            bg=LOG_BG, fg=LOG_FG,
            insertbackground="#ffffff",
            selectbackground=ACCENT,
            relief="flat",
            padx=18, pady=14,
            state="disabled",
        )
        log.tag_config("section", foreground=LOG_SECTION,
                       font=("Consolas", font_size, "bold"))
        log.tag_config("value",   foreground=LOG_VALUE)
        log.tag_config("formula", foreground=LOG_FORMULA)
        log.tag_config("success", foreground=LOG_SUCCESS,
                       font=("Consolas", font_size, "bold"))
        log.tag_config("fail",    foreground=LOG_FAIL,
                       font=("Consolas", font_size, "bold"))
        log.tag_config("normal",  foreground=LOG_FG)
        return log

    def _write_log(self, log_widget, lines: list[str]):
        log_widget.config(state="normal")
        log_widget.delete("1.0", tk.END)
        flat = "\n".join(lines).split("\n")
        for line in flat:
            log_widget.insert(tk.END, line + "\n", _tag_for(line))
        log_widget.config(state="disabled")

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_layout(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=14, pady=14)

        self.tab_direct = ttk.Frame(nb)
        self.tab_hastad = ttk.Frame(nb)

        nb.add(self.tab_direct, text="  1. RSA + khai căn trực tiếp  ")
        nb.add(self.tab_hastad, text="  2. Håstad + CRT  ")

        self._build_direct_tab()
        self._build_hastad_tab()

    # ── Tab 1 — layout giống hệt Tab 2 ───────────────────────────────────────
    def _build_direct_tab(self):
        outer, inner = self._card(
            self.tab_direct,
            "RSA textbook và tấn công khai căn trực tiếp",
        )
        outer.pack(fill="x", padx=8, pady=(8, 6))

        input_row = tk.Frame(inner, bg=PANEL)
        input_row.pack(fill="x")

        self.direct_message  = self._inline_entry(input_row, "Thông điệp", "A", 18)
        self.direct_e        = self._inline_entry(input_row, "e", "3", 6)
        self.direct_key_size = self._inline_entry(input_row, "Key size", "128", 8)
        self._run_btn(input_row, "▶  Chạy RSA", self.run_direct)

        self.direct_summary_frame, self.direct_summary_text = self._summary_card(self.tab_direct)
        self.direct_summary_frame.pack(fill="x", padx=8, pady=(0, 6))

        self.direct_log = self._make_log(self.tab_direct, 11)
        self.direct_log.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # ── Tab 2 ─────────────────────────────────────────────────────────────────
    def _build_hastad_tab(self):
        outer, inner = self._card(
            self.tab_hastad,
            "Håstad Broadcast Attack",
        )
        outer.pack(fill="x", padx=8, pady=(8, 6))

        input_row = tk.Frame(inner, bg=PANEL)
        input_row.pack(fill="x")

        self.hastad_message  = self._inline_entry(input_row, "Thông điệp", "Hi", 18)
        self.hastad_e        = self._inline_entry(input_row, "e", "3", 6)
        self.hastad_key_size = self._inline_entry(input_row, "Key size", "256", 8)
        self._run_btn(input_row, "▶  Chạy Håstad", self.run_hastad)

        self.hastad_summary_frame, self.hastad_summary_text = self._summary_card(self.tab_hastad)
        self.hastad_summary_frame.pack(fill="x", padx=8, pady=(0, 6))

        self.hastad_log = self._make_log(self.tab_hastad, 10)
        self.hastad_log.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # ── run_direct: thuật toán GIỮ NGUYÊN, sửa hiển thị λ(n) ───────────────
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
            "TẤN CÔNG THÀNH CÔNG: mᵉ < n nên c = mᵉ, khai căn c lấy lại được bản rõ."
            if success else
            "TẤN CÔNG THẤT BẠI: c đã bị modulo n, khai căn trực tiếp không ra bản rõ gốc."
        )
        self._update_summary(self.direct_summary_frame, self.direct_summary_text,
                             conclusion, success)

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
            "λ(n) = (p-1) · (q-1)",
            f"λ(n) = {short_num(p - 1)} · {short_num(q - 1)}",
            f"λ(n) = {short_num(lambda_n)}",
            "Chọn số mũ công khai:",
            f"e = {e}",
            "Tính khóa bí mật d — nghịch đảo modular của e:",
            "d × e ≡ 1 (mod λ(n))",
            "d = e⁻¹ mod λ(n)",
            f"d = {short_num(d)}",
            "Khóa công khai: (e, n)",
            "Khóa bí mật:    (d, n)",
            section("BƯỚC 3: MÃ HÓA"),
            "Công thức tổng quát: c = mᵉ mod n",
            f"Thay e = {e}: c = {me} mod n",
            f"Tính {me}: {me} = {short_num(m_pow_e)}",
        ]

        if condition:
            lines += [
                f"So sánh: {me} < n -> {status_text(True)}",
                "Vì mᵉ nhỏ hơn n nên phép mod n chưa làm thay đổi giá trị.",
                "Do đó: c = mᵉ",
                f"c = {short_num(c)}",
            ]
        else:
            lines += [
                f"So sánh: {me} < n -> {status_text(False)}",
                "Vì mᵉ lớn hơn n nên RSA lấy phần dư modulo n.",
                "Có thể hiểu: mᵉ = q × n + r",
                f"q = {short_num(quotient)}",
                f"r = {short_num(remainder)}",
                "Do đó: c = r, không còn bằng mᵉ nguyên vẹn.",
                f"c = {short_num(c)}",
            ]

        lines += [
            section("BƯỚC 4: GIẢI MÃ HỢP LỆ"),
            "Người nhận hợp lệ có khóa bí mật d nên giải mã bằng công thức:",
            "m = cᵈ mod n",
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

        self._write_log(self.direct_log, lines)

    # ── run_hastad: GIỮ NGUYÊN hoàn toàn ─────────────────────────────────────
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
            "TẤN CÔNG HÅSTAD THÀNH CÔNG: CRT khôi phục X = mᵉ, sau đó khai căn lấy lại m."
            if result.success else
            "TẤN CÔNG HÅSTAD THẤT BẠI: chưa đủ điều kiện để CRT + khai căn phục hồi m."
        )
        self._update_summary(self.hastad_summary_frame, self.hastad_summary_text,
                             conclusion, result.success)

        me = pow_text("m", result.e)
        m_pow_e = result.m ** result.e

        lines = [
            section("BƯỚC 1: CHUYỂN THÔNG ĐIỆP THÀNH SỐ"),

            f"Thông điệp chung: {result.message_text!r}",
            f"Dạng byte UTF-8: {bytes_as_hex(result.message_text)}",
            f"m = int(bytes) = {short_num(result.m)}",
            "",
            f"e = {result.e}",
            f"Số người nhận cần có = e = {result.e}",

            section("BƯỚC 2: MÃ HÓA CHO TỪNG NGƯỜI NHẬN"),

            "Công thức tổng quát:",
            "",
            "cᵢ = mᵉ mod nᵢ",
            "",
            f"Thay e = {result.e}:",
            "",
            f"cᵢ = {me} mod nᵢ",
            "",
            f"Tính {me}:",
            "",
            f"{me} = {short_num(m_pow_e)}",
        ]

        for r in result.recipients:
            c_i = sub_text("c", r.index)
            n_i = sub_text("n", r.index)
            lines += [
                "",
                f"Người nhận {r.index}:",
                "",
                f"{n_i} = {short_num(r.public_key.n)}",
                "",
                f"{c_i} = {me} mod {n_i}",
                f"{c_i} = {short_num(m_pow_e)} mod {short_num(r.public_key.n)}",
                f"{c_i} = {short_num(r.ciphertext)}",
            ]

        lines += [
            section("BƯỚC 3: LẬP HỆ ĐỒNG DƯ"),
            "Đặt:",
            "",
            "X = mᵉ",
            "",
            "Vì mỗi bản mã được tạo bởi cᵢ = mᵉ mod nᵢ, ta có hệ:",
            "",
        ]

        for r in result.recipients:
            c_i = sub_text("c", r.index)
            n_i = sub_text("n", r.index)
            lines.append(f"X ≡ {c_i} (mod {n_i})")

        lines += [
            section("BƯỚC 4: CRT GHÉP CÁC PHƯƠNG TRÌNH"),

            "CRT cho phép ghép hệ đồng dư thành một giá trị X duy nhất theo modulo N.",
            "",
            "Công thức tổng quát:",
            "",
            "N = n₁ × n₂ × ... × nₑ",
            "",
            f"Thay số người nhận e = {result.e}:",
            "",
            f"N = n₁ × n₂ × ... × n{str(result.e).translate(SUBSCRIPT)}",
            "",
            f"N = {short_num(result.total_modulus)}",
            "",
            "Với từng dòng i:",
            "",
            "Nᵢ = N / nᵢ",
            "yᵢ = Nᵢ⁻¹ mod nᵢ",
            "termᵢ = cᵢ × yᵢ × Nᵢ",
            "",
            "Sau đó:",
            "",
            "X = (term₁ + term₂ + ... + termₑ) mod N",
        ]

        for row in result.crt_rows:
            i = row["i"]
            N_i    = sub_text("N", i)
            n_i    = sub_text("n", i)
            y_i    = sub_text("y", i)
            c_i    = sub_text("c", i)
            term_i = sub_text("term", i)
            lines += [
                "",
                f"Dòng CRT i = {i}:",
                "",
                f"{N_i} = N / {n_i}",
                f"{N_i} = {short_num(row['N_i'])}",
                "",
                f"{y_i} = {N_i}⁻¹ mod {n_i}",
                f"{y_i} = {short_num(row['inverse_i'])}",
                "",
                f"{term_i} = {c_i} × {y_i} × {N_i}",
                f"{term_i} = {short_num(row['term_i'])}",
            ]

        lines += [
            "",
            "Cộng các term và lấy modulo N:",
            "",
            "X = (term₁ + term₂ + ... + termₑ) mod N",
            "",
            f"X = {short_num(result.crt_value)}",
            "",
            "Theo điều kiện của Håstad:",
            "",
            "X = mᵉ",
            "",
            f"Thay e = {result.e}:",
            "",
            f"X = {me}",

            section(f"BƯỚC 5: KHAI CĂN BẬC {result.e}"),

            "Công thức tổng quát:",
            "",
            "m = căn_bậc_e(X)",
            "",
            f"Thay e = {result.e}:",
            "",
            f"m = {root_symbol(result.e, 'X')}",
            "",
            f"Thay X = {short_num(result.crt_value)}:",
            "",
            f"m = {root_symbol(result.e, short_num(result.crt_value))}",
            "",
            "Tính:",
            "",
            f"m = {short_num(result.root)}",
            "",
            f"Khai căn chính xác hay chưa: {result.exact_root}",
            f"Recovered plaintext = {result.recovered_text!r}",
            f"So sánh Recovered với original: {status_text(result.root == result.m)}",

            section("KẾT LUẬN"),

            conclusion,
            "",
        ]

        self._write_log(self.hastad_log, lines)


if __name__ == "__main__":
    root = tk.Tk()
    app = HastadDemoApp(root)
    root.mainloop()

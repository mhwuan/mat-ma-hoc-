# Đề tài 05 — Minh họa tấn công RSA với số mũ công khai nhỏ

Ứng dụng này mô phỏng:

1. RSA textbook không padding với số mũ công khai nhỏ `e = 3`.
2. Tấn công khai căn trực tiếp khi `m^e < n`.
3. Tấn công Håstad Broadcast khi cùng một bản rõ được gửi cho nhiều người nhận.

> Lưu ý: Code cố ý dùng RSA không padding để minh họa lỗ hổng. Không dùng cho bảo mật thật.

## Cài đặt

```bash
pip install gmpy2 pytest
```

## Chạy giao diện

```bash
python hastad_ui_final(1).py
```

## Chạy kiểm thử

```bash
pytest -q
```

## Cấu trúc mã nguồn

```text
rsa_core.py          # Sinh khóa, mã hóa, giải mã RSA textbook
math_utils.py        # Khai căn nguyên, Extended Euclid, CRT
hastad_attack.py     # Logic demo khai căn trực tiếp và Håstad
ui_helpers.py        # Rút gọn số lớn để giao diện dễ đọc
hastad_ui.py         # Giao diện Tkinter
tests/test_hastad.py # Unit tests
```

## Luồng tấn công Håstad

Với cùng bản rõ `m`, cùng số mũ công khai `e`, gửi cho `e` người nhận khác nhau:

```text
c1 = m^e mod n1
c2 = m^e mod n2
...
ce = m^e mod ne
```

Dùng CRT ghép hệ đồng dư để thu được:

```text
X = m^e
```

Sau đó khai căn bậc `e`:

```text
m = e-th-root(X)
```

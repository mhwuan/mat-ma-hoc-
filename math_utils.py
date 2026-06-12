"""Math helpers: integer root, extended Euclid, and CRT."""

from functools import reduce
from typing import Iterable
import math
import gmpy2


def integer_root(x: int, e: int) -> tuple[int, bool]:
    """Return floor(e-th root of x) and whether the root is exact."""
    if e <= 1:
        raise ValueError("e phải > 1.")
    if x < 0 and e % 2 == 0:
        raise ValueError("Không khai căn bậc chẵn của số âm.")
    root, exact = gmpy2.iroot(gmpy2.mpz(x), int(e))
    return int(root), bool(exact)


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """Return (g, x, y) such that ax + by = g = gcd(a, b)."""
    g, x, y = gmpy2.gcdext(gmpy2.mpz(a), gmpy2.mpz(b))
    return int(g), int(x), int(y)


def mod_inverse(a: int, n: int) -> int:
    g, x, _ = extended_gcd(a, n)
    if g != 1:
        raise ValueError(f"Không có nghịch đảo modulo vì gcd({a}, {n}) = {g}.")
    return x % n


def are_pairwise_coprime(values: Iterable[int]) -> bool:
    values = list(values)
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if math.gcd(values[i], values[j]) != 1:
                return False
    return True


def crt(residues: list[int], moduli: list[int]) -> tuple[int, list[dict]]:
    """Solve X ≡ residues[i] mod moduli[i].

    Return X and detailed rows for explanation.
    """
    if len(residues) != len(moduli):
        raise ValueError("Số lượng bản mã và modulus phải bằng nhau.")
    if not residues:
        raise ValueError("Danh sách đầu vào rỗng.")
    if not are_pairwise_coprime(moduli):
        raise ValueError("Các modulus n_i phải nguyên tố cùng nhau từng đôi một.")

    total_n = reduce(lambda a, b: a * b, moduli)
    x = 0
    rows: list[dict] = []

    for index, (c_i, n_i) in enumerate(zip(residues, moduli), start=1):
        big_n_i = total_n // n_i
        inverse_i = mod_inverse(big_n_i, n_i)
        term_i = c_i * inverse_i * big_n_i
        x += term_i
        rows.append({
            "i": index,
            "c_i": c_i,
            "n_i": n_i,
            "N_i": big_n_i,
            "inverse_i": inverse_i,
            "term_i": term_i,
        })

    return int(x % total_n), rows

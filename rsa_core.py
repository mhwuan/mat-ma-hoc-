"""RSA core functions for the Håstad broadcast attack demo.

This module intentionally uses textbook RSA without padding because the goal
of the project is to demonstrate why low public exponent RSA is dangerous.
Do not use this code for real security.
"""

from dataclasses import dataclass
import os
import math
import gmpy2


@dataclass(frozen=True)
class PublicKey:
    e: int
    n: int


@dataclass(frozen=True)
class PrivateKey:
    d: int
    n: int


@dataclass(frozen=True)
class RSAKeyPair:
    public: PublicKey
    private: PrivateKey
    p: int
    q: int
    lambda_n: int


class TextbookRSA:
    def __init__(self, key_size: int = 256):
        if key_size < 64:
            raise ValueError("key_size phải >= 64 bit để demo ổn định.")
        self.key_size = key_size
        seed = int.from_bytes(os.urandom(16), "big")
        self.rand_state = gmpy2.random_state(seed)

    def _prime(self, bits: int) -> int:
        """Generate a prime with approximately `bits` bits."""
        while True:
            x = gmpy2.mpz_urandomb(self.rand_state, bits)
            x |= gmpy2.mpz(1) << (bits - 1)  # force high bit
            x |= 1                           # force odd
            p = int(gmpy2.next_prime(x))
            if p.bit_length() == bits:
                return p

    def generate_keypair(self, e: int = 3) -> RSAKeyPair:
        if e <= 1 or e % 2 == 0:
            raise ValueError("e phải là số lẻ lớn hơn 1, ví dụ 3 hoặc 5.")

        half = self.key_size // 2
        while True:
            p = self._prime(half)
            q = self._prime(half)
            if p == q:
                continue

            n = p * q
            lambda_n = math.lcm(p - 1, q - 1)
            if math.gcd(e, lambda_n) == 1:
                d = int(gmpy2.invert(e, lambda_n))
                return RSAKeyPair(
                    public=PublicKey(e=e, n=n),
                    private=PrivateKey(d=d, n=n),
                    p=p,
                    q=q,
                    lambda_n=lambda_n,
                )

    @staticmethod
    def message_to_int(message: str | bytes) -> int:
        if isinstance(message, str):
            message = message.encode("utf-8")
        if not message:
            raise ValueError("Thông điệp không được rỗng.")
        return int.from_bytes(message, "big")

    @staticmethod
    def int_to_message(value: int) -> str:
        if value == 0:
            return ""
        raw = int(value).to_bytes((int(value).bit_length() + 7) // 8, "big")
        return raw.decode("utf-8", errors="replace")

    @staticmethod
    def encrypt_int(m: int, public_key: PublicKey) -> int:
        if m <= 0:
            raise ValueError("m phải là số nguyên dương.")
        if m >= public_key.n:
            raise ValueError("m >= n, thông điệp quá dài so với modulus n.")
        return int(pow(m, public_key.e, public_key.n))

    @staticmethod
    def decrypt_int(c: int, private_key: PrivateKey) -> int:
        return int(pow(c, private_key.d, private_key.n))

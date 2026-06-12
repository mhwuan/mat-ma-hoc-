"""Demonstrations for direct root attack and Håstad broadcast attack."""

from dataclasses import dataclass
from rsa_core import TextbookRSA, PublicKey, PrivateKey
from math_utils import integer_root, crt


@dataclass(frozen=True)
class DirectAttackResult:
    message_text: str
    m: int
    e: int
    n: int
    c: int
    decrypted_m: int
    root: int
    exact_root: bool
    condition_m_pow_e_less_than_n: bool
    success: bool

    @property
    def recovered_text(self) -> str:
        return TextbookRSA.int_to_message(self.root)


@dataclass(frozen=True)
class RecipientData:
    index: int
    public_key: PublicKey
    private_key: PrivateKey
    ciphertext: int


@dataclass(frozen=True)
class HastadAttackResult:
    message_text: str
    m: int
    e: int
    recipients: list[RecipientData]
    total_modulus: int
    crt_value: int
    crt_rows: list[dict]
    root: int
    exact_root: bool
    success: bool

    @property
    def recovered_text(self) -> str:
        return TextbookRSA.int_to_message(self.root)


def run_direct_root_demo(message: str, e: int = 3, key_size: int = 128) -> DirectAttackResult:
    rsa = TextbookRSA(key_size=key_size)
    keypair = rsa.generate_keypair(e=e)
    m = rsa.message_to_int(message)
    c = rsa.encrypt_int(m, keypair.public)
    decrypted_m = rsa.decrypt_int(c, keypair.private)
    root, exact = integer_root(c, e)

    condition = (m ** e) < keypair.public.n
    success = exact and root == m

    return DirectAttackResult(
        message_text=message,
        m=m,
        e=e,
        n=keypair.public.n,
        c=c,
        decrypted_m=decrypted_m,
        root=root,
        exact_root=exact,
        condition_m_pow_e_less_than_n=condition,
        success=success,
    )


def generate_broadcast_data(message: str, e: int = 3, key_size: int = 256) -> tuple[int, list[RecipientData]]:
    rsa = TextbookRSA(key_size=key_size)
    m = rsa.message_to_int(message)
    recipients: list[RecipientData] = []
    seen_n: set[int] = set()

    for i in range(1, e + 1):
        while True:
            keypair = rsa.generate_keypair(e=e)
            if keypair.public.n not in seen_n and m < keypair.public.n:
                seen_n.add(keypair.public.n)
                break

        c = rsa.encrypt_int(m, keypair.public)
        recipients.append(RecipientData(
            index=i,
            public_key=keypair.public,
            private_key=keypair.private,
            ciphertext=c,
        ))

    return m, recipients


def run_hastad_attack(message: str, e: int = 3, key_size: int = 256) -> HastadAttackResult:
    if e < 2:
        raise ValueError("e phải >= 2.")

    m, recipients = generate_broadcast_data(message, e=e, key_size=key_size)
    ciphertexts = [r.ciphertext for r in recipients]
    moduli = [r.public_key.n for r in recipients]

    crt_value, rows = crt(ciphertexts, moduli)
    root, exact = integer_root(crt_value, e)
    total_modulus = 1
    for n in moduli:
        total_modulus *= n

    return HastadAttackResult(
        message_text=message,
        m=m,
        e=e,
        recipients=recipients,
        total_modulus=total_modulus,
        crt_value=crt_value,
        crt_rows=rows,
        root=root,
        exact_root=exact,
        success=exact and root == m,
    )

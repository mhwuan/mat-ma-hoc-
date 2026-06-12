from rsa_core import TextbookRSA
from math_utils import integer_root, crt
from hastad_attack import run_direct_root_demo, run_hastad_attack


def test_integer_root_exact():
    assert integer_root(27, 3) == (3, True)
    assert integer_root(1000, 3) == (10, True)


def test_integer_root_inexact():
    assert integer_root(28, 3) == (3, False)


def test_crt_basic():
    x, _ = crt([2, 3, 2], [3, 5, 7])
    assert x == 23


def test_rsa_encrypt_decrypt():
    rsa = TextbookRSA(key_size=128)
    kp = rsa.generate_keypair(e=3)
    m = rsa.message_to_int("Hi")
    c = rsa.encrypt_int(m, kp.public)
    assert rsa.decrypt_int(c, kp.private) == m


def test_direct_root_success_for_small_message():
    result = run_direct_root_demo("A", e=3, key_size=128)
    assert result.success
    assert result.recovered_text == "A"


def test_hastad_success():
    result = run_hastad_attack("Hello", e=3, key_size=256)
    assert result.success
    assert result.recovered_text == "Hello"

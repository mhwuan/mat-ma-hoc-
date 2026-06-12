"""Small UI formatting helpers."""


def short_num(value: int, head: int = 24, tail: int = 24) -> str:
    s = str(int(value))
    if len(s) <= head + tail + 5:
        return s
    return f"{s[:head]}...{s[-tail:]}  ({len(s)} chữ số)"


def full_num_block(label: str, value: int) -> str:
    return f"{label}:\n{value}\n"


def status_text(ok: bool) -> str:
    return "ĐẠT" if ok else "KHÔNG ĐẠT"

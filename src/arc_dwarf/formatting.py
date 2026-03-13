def fmt_hex(x: int, width: int = 0) -> str:
    if width:
        return f"0x{x:0{width}x}"
    return f"0x{x:x}"


def fmt_bytes(n: int) -> str:
    return f"{n}B"

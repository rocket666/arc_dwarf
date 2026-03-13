from __future__ import annotations

from contextlib import contextmanager
from typing import List, Optional, TextIO


class TextEmitter:
    def __init__(self, *, stream: Optional[TextIO] = None):
        self._stream = stream
        self._indent = 0
        self._lines: List[str] = []

    def line(self, msg: str = "") -> None:
        s = (" " * self._indent) + msg
        self._lines.append(s)
        if self._stream is not None:
            self._stream.write(s + "\n")

    def rule(self, title: str = "", ch: str = "=", width: int = 72) -> None:
        if title:
            self.line(f"{ch*8} {title} {ch*8}")
        else:
            self.line(ch * width)

    @contextmanager
    def indent(self, n: int = 2):
        self._indent += n
        try:
            yield
        finally:
            self._indent -= n

    def lines(self) -> List[str]:
        return list(self._lines)

    def text(self) -> str:
        return "\n".join(self._lines)

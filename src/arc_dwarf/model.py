from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Member:
    name: str
    offset: Optional[int]          # byte offset if known; None if unknown
    type_str: str                  # pretty type name
    type_die: Optional[object]     # pyelftools DIE or None

    span: int = 0                  # FORCED offset-diff inferred footprint in bytes
    sizeof: int = 0                # best-effort sizeof(type) in bytes (DWARF/type-based)

    bit_size: Optional[int] = None
    bit_offset: Optional[int] = None

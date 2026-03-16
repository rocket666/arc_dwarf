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


@dataclass
class MemberAddress:
    """Result of resolving a dotted member path to a runtime address."""
    var_name: str                  # top-level variable name
    member_path: str               # dotted member path (e.g. "RspDbf2dCtrlParam.OutputAddr.obj_num_addr")
    base_address: int              # variable base address from symbol table
    member_offset: int             # accumulated byte offset of the member within the struct
    address: int                   # base_address + member_offset
    type_str: str                  # type name of the final member
    sizeof: int                    # byte size of the final member

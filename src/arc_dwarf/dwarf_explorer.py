from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from elftools.elf.elffile import ELFFile
from elftools.dwarf.descriptions import describe_form_class
from elftools.dwarf.dwarf_expr import DWARFExprParser
from elftools.elf.sections import SymbolTableSection

from .model import Member


class DwarfTypeExplorer:
    def __init__(self, elf_path: str):
        self.elf_path = elf_path
        self._fp = None
        self._elf = None
        self._dwarfinfo = None
        self._expr_parser = None

        self.pointer_size = 4  # default; overwritten from ELF class
        # Name -> list[(die, cu)] because DWARF may contain duplicates across CUs.
        self._types_by_name: Dict[str, List[Tuple[object, object]]] = {}

    def __enter__(self) -> "DwarfTypeExplorer":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def open(self) -> None:
        self._fp = open(self.elf_path, "rb")
        self._elf = ELFFile(self._fp)
        self.pointer_size = (self._elf.elfclass or 32) // 8

        if not self._elf.has_dwarf_info():
            raise RuntimeError("ELF has no DWARF info. Build with -g and avoid strip.")

        self._dwarfinfo = self._elf.get_dwarf_info()
        self._expr_parser = DWARFExprParser(self._dwarfinfo.structs)
        self._index_types()

    def close(self) -> None:
        if self._fp:
            self._fp.close()
            self._fp = None

    # -------------
    # Index & lookup
    # -------------

    def _index_types(self) -> None:
        wanted = {
            "DW_TAG_structure_type",
            "DW_TAG_union_type",
            "DW_TAG_typedef",
            "DW_TAG_enumeration_type",
            "DW_TAG_base_type",
        }
        for cu in self._dwarfinfo.iter_CUs():
            for die in cu.iter_DIEs():
                if die.tag not in wanted:
                    continue
                name_attr = die.attributes.get("DW_AT_name")
                if not name_attr:
                    continue
                name = self._attr_to_str(name_attr)
                if not name:
                    continue
                self._types_by_name.setdefault(name, []).append((die, cu))

    @staticmethod
    def _attr_to_str(attr) -> str:
        v = attr.value
        if isinstance(v, bytes):
            return v.decode("utf-8", "replace")
        return str(v)

    def find_type_die(self, type_name: str) -> Optional[object]:
        candidates = self._types_by_name.get(type_name)
        if not candidates:
            return None

        def score(die) -> Tuple[int, int]:
            kind = 1
            if die.tag in ("DW_TAG_structure_type", "DW_TAG_union_type"):
                kind = 3
            elif die.tag == "DW_TAG_typedef":
                kind = 2
            has_size = 1 if ("DW_AT_byte_size" in die.attributes) else 0
            return (kind, has_size)

        return max((d for (d, _cu) in candidates), key=score)

    # -----------------------
    # DIE resolution / naming
    # -----------------------

    def _die_from_type_attr(self, die) -> Optional[object]:
        if die is None or "DW_AT_type" not in die.attributes:
            return None
        try:
            return die.get_DIE_from_attribute("DW_AT_type")
        except Exception:
            return None

    def resolve_typedefs_and_qualifiers(self, die) -> object:
        seen: Set[int] = set()
        cur = die
        while cur is not None:
            off = getattr(cur, "offset", None)
            if off is not None:
                if off in seen:
                    break
                seen.add(off)

            if cur.tag in (
                "DW_TAG_typedef",
                "DW_TAG_const_type",
                "DW_TAG_volatile_type",
                "DW_TAG_restrict_type",
            ):
                nxt = self._die_from_type_attr(cur)
                if nxt is None:
                    break
                cur = nxt
                continue
            return cur
        return die

    def type_display_name(self, die) -> str:
        if die is None:
            return "unknown"

        name_attr = die.attributes.get("DW_AT_name")
        if name_attr:
            name = self._attr_to_str(name_attr)
            if name:
                return name

        if die.tag == "DW_TAG_pointer_type":
            base = self._die_from_type_attr(die)
            return f"{self.type_display_name(base)}*"
        if die.tag == "DW_TAG_array_type":
            base = self._die_from_type_attr(die)
            return f"{self.type_display_name(base)}[]"

        return die.tag.replace("DW_TAG_", "")

    # -------------
    # Size evaluation
    # -------------

    def type_byte_size(self, die) -> int:
        if die is None:
            return 0

        bs = die.attributes.get("DW_AT_byte_size")
        if bs:
            return int(bs.value)

        if die.tag in (
            "DW_TAG_typedef",
            "DW_TAG_const_type",
            "DW_TAG_volatile_type",
            "DW_TAG_restrict_type",
        ):
            return self.type_byte_size(self._die_from_type_attr(die))

        if die.tag == "DW_TAG_enumeration_type":
            return 4

        if die.tag == "DW_TAG_pointer_type":
            return self.pointer_size

        if die.tag == "DW_TAG_array_type":
            base = self._die_from_type_attr(die)
            elem = self.type_byte_size(base)
            count = self._array_total_count(die)
            if elem > 0 and count is not None:
                return elem * count
            return 0

        return 0

    def _array_total_count(self, array_die) -> Optional[int]:
        total = 1
        any_dim = False
        for child in array_die.iter_children():
            if child.tag != "DW_TAG_subrange_type":
                continue
            any_dim = True

            if "DW_AT_count" in child.attributes:
                total *= int(child.attributes["DW_AT_count"].value)
                continue
            if "DW_AT_upper_bound" in child.attributes:
                ub = int(child.attributes["DW_AT_upper_bound"].value)
                total *= (ub + 1)
                continue
            return None

        if not any_dim:
            return None
        return total

    # -------------------
    # Member offset decode
    # -------------------

    def member_offset(self, member_die) -> Optional[int]:
        attr = member_die.attributes.get("DW_AT_data_member_location")
        if not attr:
            return 0

        form_class = describe_form_class(attr.form)
        if form_class == "constant":
            return int(attr.value)

        if form_class == "exprloc":
            try:
                ops = self._expr_parser.parse_expr(attr.value)
                return self._eval_member_loc_expr(ops)
            except Exception:
                return None

        return None

    @staticmethod
    def _eval_member_loc_expr(ops) -> Optional[int]:
        stack: List[int] = []
        for op in ops:
            name = op.op_name
            args = op.args

            if name == "DW_OP_plus_uconst":
                return int(args[0])

            if name == "DW_OP_constu":
                stack.append(int(args[0]))
                continue

            if name == "DW_OP_consts":
                stack.append(int(args[0]))
                continue

            if name == "DW_OP_plus":
                if len(stack) < 2:
                    return None
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)
                continue

            if name == "DW_OP_stack_value":
                continue

            return None

        if len(stack) == 1:
            return stack[0]
        return None

    # -------------------
    # Member parsing / span
    # -------------------

    def parse_struct_or_union_members(self, struct_or_union_die) -> List[Member]:
        members: List[Member] = []

        for child in struct_or_union_die.iter_children():
            if child.tag != "DW_TAG_member":
                continue

            name_attr = child.attributes.get("DW_AT_name")
            name = self._attr_to_str(name_attr) if name_attr else "<unnamed>"

            tdie = None
            try:
                tdie = child.get_DIE_from_attribute("DW_AT_type")
            except Exception:
                tdie = None

            off = self.member_offset(child)
            type_str = self.type_display_name(tdie) if tdie is not None else "unknown"
            sizeof = self.type_byte_size(tdie) if tdie is not None else 0

            bit_size = child.attributes.get("DW_AT_bit_size")
            bit_off = child.attributes.get("DW_AT_bit_offset")

            members.append(
                Member(
                    name=name,
                    offset=off,
                    type_str=type_str,
                    type_die=tdie,
                    span=0,  # forced-inferred below
                    sizeof=sizeof,
                    bit_size=int(bit_size.value) if bit_size else None,
                    bit_offset=int(bit_off.value) if bit_off else None,
                )
            )

        self._force_infer_member_spans_by_offsets(struct_or_union_die, members)
        return members

    def _force_infer_member_spans_by_offsets(self, container_die, members: List[Member]) -> None:
        resolved = self.resolve_typedefs_and_qualifiers(container_die)
        kind = resolved.tag
        container_size = self.type_byte_size(resolved)

        if kind == "DW_TAG_union_type":
            for m in members:
                if m.bit_size is not None:
                    m.span = 0
                    continue
                if container_size > 0:
                    m.span = container_size
                else:
                    m.span = m.sizeof or 0
            return

        indexed = [(i, m) for i, m in enumerate(members) if m.offset is not None]
        indexed.sort(key=lambda im: (im[1].offset, im[0]))

        for pos, (_orig_i, m) in enumerate(indexed):
            if m.bit_size is not None:
                m.span = 0
                continue

            cur_off = m.offset if m.offset is not None else 0
            next_off: Optional[int] = None

            for pos2 in range(pos + 1, len(indexed)):
                off2 = indexed[pos2][1].offset
                if off2 is not None and off2 > cur_off:
                    next_off = off2
                    break

            if next_off is not None:
                delta = next_off - cur_off
                m.span = delta if delta > 0 else (m.sizeof or 0)
                continue

            if container_size and container_size > cur_off:
                m.span = container_size - cur_off
                continue

            m.span = m.sizeof or 0

        for m in members:
            if m.offset is None and m.bit_size is None:
                m.span = m.sizeof or 0

    # -------------------
    # Recursion target logic
    # -------------------

    def recurse_target_die(self, tdie) -> Optional[object]:
        if tdie is None:
            return None

        r = self.resolve_typedefs_and_qualifiers(tdie)

        if r.tag == "DW_TAG_pointer_type":
            return None

        if r.tag == "DW_TAG_array_type":
            elem = self._die_from_type_attr(r)
            if elem is None:
                return None
            elem_r = self.resolve_typedefs_and_qualifiers(elem)
            if elem_r.tag == "DW_TAG_pointer_type":
                return None
            if elem_r.tag in ("DW_TAG_structure_type", "DW_TAG_union_type"):
                return elem
            return None

        if r.tag in ("DW_TAG_structure_type", "DW_TAG_union_type"):
            return tdie

        return None
    
    def resolve_member_offset(
        self, type_name: str, member_path: str
    ) -> Tuple[int, str, int]:
        """
        沿点分成员路径逐层解析偏移量。

        支持数组元素访问，如 "arr[2].field"。

        参数:
            type_name:   顶层类型名 (e.g. "Rsp_Params_t")
            member_path: 点分成员路径 (e.g. "RspDbf2dCtrlParam.OutputAddr.obj_num_addr")

        返回:
            (accumulated_offset, final_type_str, final_sizeof) 元组

        异常:
            RuntimeError: 类型未找到或路径中任一成员不存在
        """
        import re as _re

        die = self.find_type_die(type_name)
        if die is None:
            raise RuntimeError(f"type not found in DWARF: {type_name}")

        # 空路径：直接返回类型本身的偏移 0
        if not member_path:
            return (0, self.type_display_name(die), self.type_byte_size(die))

        # 拆分路径："a.b[3].c" -> [("a", None), ("b", 3), ("c", None)]
        parts: List[Tuple[str, Optional[int]]] = []
        for token in member_path.split("."):
            m = _re.match(r'^([A-Za-z_][A-Za-z0-9_]*)(?:\[(\d+)\])?$', token)
            if not m:
                raise RuntimeError(f"invalid member path token: {token!r}")
            idx = int(m.group(2)) if m.group(2) is not None else None
            parts.append((m.group(1), idx))

        total_offset = 0
        current_die = die

        for field_name, array_idx in parts:
            resolved = self.resolve_typedefs_and_qualifiers(current_die)

            if resolved.tag not in ("DW_TAG_structure_type", "DW_TAG_union_type"):
                raise RuntimeError(
                    f"cannot descend into non-struct/union type "
                    f"{self.type_display_name(current_die)!r} for member {field_name!r}"
                )

            members = self.parse_struct_or_union_members(resolved)
            found = None
            for mbr in members:
                if mbr.name == field_name:
                    found = mbr
                    break

            if found is None:
                raise RuntimeError(
                    f"member {field_name!r} not found in "
                    f"{self.type_display_name(current_die)!r}"
                )

            if found.offset is not None:
                total_offset += found.offset

            # 处理数组下标
            if array_idx is not None:
                if found.type_die is None:
                    raise RuntimeError(f"no type info for member {field_name!r}")
                elem_die = self.resolve_typedefs_and_qualifiers(found.type_die)
                if elem_die.tag != "DW_TAG_array_type":
                    raise RuntimeError(f"member {field_name!r} is not an array")
                base_die = self._die_from_type_attr(elem_die)
                if base_die is None:
                    raise RuntimeError(f"cannot resolve element type of {field_name!r}")
                elem_size = self.type_byte_size(base_die)
                total_offset += array_idx * elem_size
                current_die = base_die
            else:
                if found.type_die is not None:
                    current_die = found.type_die

        final_type = self.type_display_name(current_die)
        final_size = self.type_byte_size(current_die)
        return (total_offset, final_type, final_size)

    def get_member_address(
        self, var_name: str, member_path: str, type_name: Optional[str] = None
    ) -> "MemberAddress":
        """
        获取变量中某个成员的运行时地址。

        参数:
            var_name:     全局变量名 (e.g. "gRspCfg")
            member_path:  点分成员路径 (e.g. "RspDbf2dCtrlParam.OutputAddr.obj_num_addr")
            type_name:    可选，变量的类型名。若不提供，则从 DWARF 符号信息推断。

        返回:
            MemberAddress 数据对象
        """
        from .model import MemberAddress

        var_info = self.get_variable_info(var_name)
        if var_info is None:
            raise RuntimeError(f"variable {var_name!r} not found in symbol table")

        base_addr, _var_size = var_info

        # 如果未指定类型名，尝试从 DWARF 中推断
        if type_name is None:
            type_name = self._infer_variable_type(var_name)
            if type_name is None:
                raise RuntimeError(
                    f"cannot infer type for {var_name!r}; "
                    f"please specify type_name explicitly"
                )

        offset, final_type, final_size = self.resolve_member_offset(type_name, member_path)

        return MemberAddress(
            var_name=var_name,
            member_path=member_path,
            base_address=base_addr,
            member_offset=offset,
            address=base_addr + offset,
            type_str=final_type,
            sizeof=final_size,
        )

    def _infer_variable_type(self, var_name: str) -> Optional[str]:
        """尝试从 DWARF 调试信息中推断全局变量的类型名。"""
        for cu in self._dwarfinfo.iter_CUs():
            for die in cu.iter_DIEs():
                if die.tag != "DW_TAG_variable":
                    continue
                name_attr = die.attributes.get("DW_AT_name")
                if not name_attr:
                    continue
                if self._attr_to_str(name_attr) != var_name:
                    continue
                tdie = self._die_from_type_attr(die)
                if tdie is not None:
                    return self.type_display_name(tdie)
        return None

    def get_variable_info(self, var_name: str) -> Optional[Tuple[int, int]]:
        """
        从 ELF 符号表中通过变量名查找变量。
        返回 (address, size) 元组。如果未找到则返回 None。
        """
        if self._elf is None:
            raise RuntimeError("ELF file is not opened.")

        for section in self._elf.iter_sections():
            if not isinstance(section, SymbolTableSection):
                continue

            syms = section.get_symbol_by_name(var_name)
            if not syms:
                continue

            # 优先匹配类型为 STT_OBJECT (全局/静态变量) 且地址有效的符号
            for sym in syms:
                st_type = sym['st_info']['type']
                if st_type == 'STT_OBJECT' and sym['st_value'] > 0:
                    return (sym['st_value'], sym['st_size'])

            # Fallback: 部分编译器的符号可能未正确标记为 OBJECT，只要有地址即可
            for sym in syms:
                if sym['st_value'] > 0:
                    return (sym['st_value'], sym['st_size'])

        return None

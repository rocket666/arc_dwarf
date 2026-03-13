from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

from .dwarf_explorer import DwarfTypeExplorer
from .formatting import fmt_bytes, fmt_hex
from .textout import TextEmitter


@dataclass
class DumpOptions:
    max_depth: int = 20
    recursive: bool = True
    show_notes: bool = True

    # If either is not None, recursion becomes "expand only when matched".
    expand_type_names: Optional[Set[str]] = None
    expand_member_names: Optional[Set[str]] = None
    case_insensitive_filters: bool = False


class TypeTreeDumper:
    """
    - dump(): render to text (tree + aligned table)
    - build(): return a JSON-serializable dict tree (for integration / --format json)
    """

    def __init__(self, explorer: DwarfTypeExplorer):
        self.ex = explorer

    # -------------------------
    # Public API: text rendering
    # -------------------------

    def dump(
        self,
        type_name: str,
        *,
        options: Optional[DumpOptions] = None,
        emitter: Optional[TextEmitter] = None,
    ) -> TextEmitter:
        opts = options or DumpOptions()
        out = emitter or TextEmitter()

        die = self.ex.find_type_die(type_name)
        if die is None:
            raise RuntimeError(f"type not found in DWARF: {type_name}")

        out.rule(f"DWARF Type Dump: {type_name}")
        if opts.show_notes:
            out.line("Notes:")
            with out.indent(2):
                out.line("- member span is FORCED by offset-diff (layout footprint; may include padding)")
                out.line("- sizeof is best-effort from DWARF/type rules (may be 0 if toolchain omits it)")
                out.line("- pointers are not expanded; arrays expand by element type if struct/union")
                out.line("- filters: if expand_type_names/expand_member_names set, only matched members are expanded")
            out.rule(ch="-")

        self._dump_die_tree(die, out=out, depth=0, opts=opts, visited=set())
        return out

    def _dump_die_tree(self, die, *, out: TextEmitter, depth: int, opts: DumpOptions, visited: Set[int]) -> None:
        resolved = self.ex.resolve_typedefs_and_qualifiers(die)
        kind = resolved.tag.replace("DW_TAG_", "")
        name = self.ex.type_display_name(die)
        size = self.ex.type_byte_size(resolved)

        out.line(f"Type {name} ({kind})  size={fmt_bytes(size)}")

        if resolved.tag not in ("DW_TAG_structure_type", "DW_TAG_union_type"):
            return

        if depth >= opts.max_depth:
            with out.indent(2):
                out.line("(max depth reached)")
            return

        off = getattr(resolved, "offset", None)
        if off is not None:
            if off in visited:
                with out.indent(2):
                    out.line("(cycle detected; stop)")
                return
            visited.add(off)

        members = self.ex.parse_struct_or_union_members(resolved)
        if not members:
            with out.indent(2):
                out.line("(no members)")
            return

        with out.indent(2):
            out.line(f"{'off':>6}  {'span':>6}  {'sizeof':>6}  {'name':<30}  type")
            out.line("-" * 86)

            for m in members:
                off_s = "?" if m.offset is None else fmt_hex(m.offset, 3)

                if m.bit_size is not None:
                    span_s = f"{m.bit_size}b"
                    sizeof_s = "-"
                else:
                    span_s = fmt_bytes(m.span) if m.span else "0B"
                    sizeof_s = fmt_bytes(m.sizeof) if m.sizeof else "0B"

                out.line(f"{off_s:>6}  {span_s:>6}  {sizeof_s:>6}  {m.name:<30}  {m.type_str}")

                if not opts.recursive:
                    continue

                target = self.ex.recurse_target_die(m.type_die)
                if target is None:
                    continue

                if not self._should_expand_member(m.name, target, opts):
                    continue

                with out.indent(2):
                    out.line("->")
                with out.indent(4):
                    self._dump_die_tree(target, out=out, depth=depth + 1, opts=opts, visited=visited)

    # -------------------------
    # Public API: JSON building
    # -------------------------

    def build(self, type_name: str, *, options: Optional[DumpOptions] = None) -> Dict[str, Any]:
        """
        Build a JSON-serializable tree:
        {
          "root_type": "...",
          "node": { ... }   # see _build_die_node
        }
        """
        opts = options or DumpOptions()

        die = self.ex.find_type_die(type_name)
        if die is None:
            raise RuntimeError(f"type not found in DWARF: {type_name}")

        return {
            "root_type": type_name,
            "options": {
                "max_depth": opts.max_depth,
                "recursive": opts.recursive,
                "expand_type_names": sorted(opts.expand_type_names) if opts.expand_type_names is not None else None,
                "expand_member_names": sorted(opts.expand_member_names) if opts.expand_member_names is not None else None,
                "case_insensitive_filters": opts.case_insensitive_filters,
            },
            "node": self._build_die_node(die, depth=0, opts=opts, visited=set()),
        }

    def _build_die_node(self, die, *, depth: int, opts: DumpOptions, visited: Set[int]) -> Dict[str, Any]:
        resolved = self.ex.resolve_typedefs_and_qualifiers(die)
        kind = resolved.tag.replace("DW_TAG_", "")
        display_name = self.ex.type_display_name(die)
        byte_size = self.ex.type_byte_size(resolved)
        die_offset = getattr(resolved, "offset", None)

        node: Dict[str, Any] = {
            "type_name": display_name,
            "kind": kind,
            "size": byte_size,
            "die_offset": die_offset,
        }

        # Only struct/union have members
        if resolved.tag not in ("DW_TAG_structure_type", "DW_TAG_union_type"):
            node["members"] = []
            return node

        # Depth / cycle checks
        if depth >= opts.max_depth:
            node["truncated"] = True
            node["members"] = []
            return node

        if die_offset is not None and die_offset in visited:
            node["cycle_detected"] = True
            node["members"] = []
            return node

        if die_offset is not None:
            visited.add(die_offset)

        members = self.ex.parse_struct_or_union_members(resolved)
        out_members = []

        for m in members:
            target = self.ex.recurse_target_die(m.type_die) if opts.recursive else None

            expanded = False
            child = None

            if target is not None and self._should_expand_member(m.name, target, opts):
                expanded = True
                child = self._build_die_node(target, depth=depth + 1, opts=opts, visited=visited)

            out_members.append(
                {
                    "name": m.name,
                    "offset": m.offset,
                    "type_str": m.type_str,
                    "span": m.span if m.bit_size is None else None,      # bytes
                    "sizeof": m.sizeof if m.bit_size is None else None,  # bytes
                    "bit_size": m.bit_size,
                    "bit_offset": m.bit_offset,
                    "expanded": expanded,
                    "child": child,
                }
            )

        node["members"] = out_members
        return node

    # -------------------------
    # Filter helpers
    # -------------------------

    def _norm(self, s: str, opts: DumpOptions) -> str:
        return s.lower() if opts.case_insensitive_filters else s

    def _type_match_name(self, die, opts: DumpOptions) -> str:
        if die is None:
            return ""
        r = self.ex.resolve_typedefs_and_qualifiers(die)
        name_attr = r.attributes.get("DW_AT_name")
        if name_attr:
            name = self.ex._attr_to_str(name_attr)
        else:
            name = self.ex.type_display_name(r)
        return self._norm(name, opts)

    def _should_expand_member(self, member_name: str, target_die, opts: DumpOptions) -> bool:
        # No filters => expand all (original behavior)
        if opts.expand_type_names is None and opts.expand_member_names is None:
            return True

        mname = self._norm(member_name, opts)
        tname = self._type_match_name(target_die, opts)

        if opts.expand_member_names is not None:
            allowed_members = {self._norm(x, opts) for x in opts.expand_member_names}
            if mname in allowed_members:
                return True

        if opts.expand_type_names is not None:
            allowed_types = {self._norm(x, opts) for x in opts.expand_type_names}
            if tname in allowed_types:
                return True

        return False

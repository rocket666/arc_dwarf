"""Tests for arc_dwarf.dwarf_explorer module.

Note: Full integration tests require sample ELF files with DWARF debug info.
Place test ELF files in tests/fixtures/ for integration testing.
"""

from __future__ import annotations

import pytest

from arc_dwarf.dwarf_explorer import DwarfTypeExplorer
from arc_dwarf.model import MemberAddress


class TestDwarfTypeExplorerUnit:
    def test_eval_member_loc_expr_plus_uconst(self):
        """Test DW_OP_plus_uconst expression evaluation."""

        class FakeOp:
            def __init__(self, name, args):
                self.op_name = name
                self.args = args

        ops = [FakeOp("DW_OP_plus_uconst", [16])]
        result = DwarfTypeExplorer._eval_member_loc_expr(ops)
        assert result == 16

    def test_eval_member_loc_expr_constu_plus(self):
        """Test DW_OP_constu + DW_OP_plus expression evaluation."""

        class FakeOp:
            def __init__(self, name, args):
                self.op_name = name
                self.args = args

        ops = [
            FakeOp("DW_OP_constu", [10]),
            FakeOp("DW_OP_constu", [5]),
            FakeOp("DW_OP_plus", []),
        ]
        result = DwarfTypeExplorer._eval_member_loc_expr(ops)
        assert result == 15

    def test_context_manager_without_file_raises(self):
        """Test that opening a nonexistent ELF raises an error."""
        with pytest.raises(FileNotFoundError):
            with DwarfTypeExplorer("/nonexistent/file.elf") as _ex:
                pass


class TestMemberAddress:
    def test_member_address_dataclass(self):
        """Test MemberAddress dataclass creation."""
        ma = MemberAddress(
            var_name="gRspCfg",
            member_path="RspDbf2dCtrlParam.OutputAddr.obj_num_addr",
            base_address=0x20F80000,
            member_offset=128,
            address=0x20F80000 + 128,
            type_str="uint32_t",
            sizeof=4,
        )
        assert ma.var_name == "gRspCfg"
        assert ma.member_path == "RspDbf2dCtrlParam.OutputAddr.obj_num_addr"
        assert ma.address == ma.base_address + ma.member_offset
        assert ma.type_str == "uint32_t"
        assert ma.sizeof == 4

    def test_resolve_member_offset_type_not_found(self):
        """Test resolve_member_offset raises when type is not found (no ELF needed)."""
        # DwarfTypeExplorer without open() has an empty type index
        ex = DwarfTypeExplorer.__new__(DwarfTypeExplorer)
        ex._types_by_name = {}
        with pytest.raises(RuntimeError, match="type not found"):
            ex.resolve_member_offset("NonExistentType", "field")

    def test_resolve_member_offset_invalid_path_token(self):
        """Test resolve_member_offset raises on invalid path tokens."""
        ex = DwarfTypeExplorer.__new__(DwarfTypeExplorer)
        ex._types_by_name = {"Foo": []}

        # Make find_type_die return a mock die
        class FakeDie:
            tag = "DW_TAG_structure_type"
            attributes = {}
            offset = 0
            def iter_children(self):
                return iter([])

        ex._types_by_name = {"Foo": [(FakeDie(), None)]}

        with pytest.raises(RuntimeError, match="invalid member path token"):
            ex.resolve_member_offset("Foo", "123invalid")

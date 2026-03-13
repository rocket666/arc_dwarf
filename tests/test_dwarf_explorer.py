"""Tests for arc_dwarf.dwarf_explorer module.

Note: Full integration tests require sample ELF files with DWARF debug info.
Place test ELF files in tests/fixtures/ for integration testing.
"""

from __future__ import annotations

import pytest

from arc_dwarf.dwarf_explorer import DwarfTypeExplorer


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

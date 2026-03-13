"""Tests for arc_dwarf.type_dumper module.

Note: Full integration tests require a DwarfTypeExplorer instance
backed by a real ELF file. Unit tests here focus on DumpOptions and
basic TypeTreeDumper behavior.
"""

from __future__ import annotations

from arc_dwarf.type_dumper import DumpOptions


class TestDumpOptions:
    def test_defaults(self):
        opts = DumpOptions()
        assert opts.max_depth == 20
        assert opts.recursive is True
        assert opts.show_notes is True
        assert opts.expand_type_names is None
        assert opts.expand_member_names is None
        assert opts.case_insensitive_filters is False

    def test_custom_options(self):
        opts = DumpOptions(
            max_depth=5,
            recursive=False,
            expand_type_names={"Foo", "Bar"},
        )
        assert opts.max_depth == 5
        assert opts.recursive is False
        assert opts.expand_type_names == {"Foo", "Bar"}

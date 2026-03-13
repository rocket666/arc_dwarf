"""Tests for arc_dwarf.cli module."""

from __future__ import annotations


class TestCliModule:
    def test_main_importable(self):
        """Test that the CLI main function can be imported."""
        from arc_dwarf.cli import main
        assert callable(main)

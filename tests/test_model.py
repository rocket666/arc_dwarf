"""Tests for arc_dwarf.model module."""

from __future__ import annotations

from arc_dwarf.model import Member


class TestMember:
    def test_member_creation(self):
        """Test basic Member dataclass creation."""
        m = Member(
            name="field1",
            offset=0,
            type_str="uint32_t",
            type_die=None,
            span=4,
            sizeof=4,
        )
        assert m.name == "field1"
        assert m.offset == 0
        assert m.type_str == "uint32_t"
        assert m.span == 4
        assert m.sizeof == 4
        assert m.bit_size is None
        assert m.bit_offset is None

    def test_member_with_bit_fields(self):
        """Test Member with bit-field attributes."""
        m = Member(
            name="flag",
            offset=0,
            type_str="unsigned int",
            type_die=None,
            span=0,
            sizeof=4,
            bit_size=1,
            bit_offset=31,
        )
        assert m.bit_size == 1
        assert m.bit_offset == 31

    def test_member_defaults(self):
        """Test Member default values."""
        m = Member(name="x", offset=None, type_str="int", type_die=None)
        assert m.span == 0
        assert m.sizeof == 0
        assert m.bit_size is None
        assert m.bit_offset is None

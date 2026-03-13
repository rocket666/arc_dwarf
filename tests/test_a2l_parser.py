"""Tests for arc_dwarf.a2l_parser module."""

from __future__ import annotations

from pathlib import Path

from arc_dwarf.a2l_parser import A2lParser


class TestA2lParser:
    def test_parse_measurement_block(self, tmp_path: Path):
        """Test parsing a MEASUREMENT block from A2L content."""
        a2l_content = (
            '/begin MEASUREMENT gTestVar\n'
            '  "Test variable"\n'
            '  TestStruct_t\n'
            '  NO_COMPU_METHOD\n'
            '  0 0 0 100\n'
            '/end MEASUREMENT\n'
        )
        a2l_file = tmp_path / "test.a2l"
        a2l_file.write_text(a2l_content, encoding="utf-8")

        parser = A2lParser(str(a2l_file))
        variables = parser.get_variables()

        assert len(variables) == 1
        assert variables[0]["name"] == "gTestVar"
        assert variables[0]["block"] == "MEASUREMENT"
        assert variables[0]["type"] == "TestStruct_t"

    def test_parse_characteristic_block(self, tmp_path: Path):
        """Test parsing a CHARACTERISTIC block from A2L content."""
        a2l_content = (
            '/begin CHARACTERISTIC gCalParam\n'
            '  "Calibration parameter"\n'
            '  CalType_t\n'
            '  0x80000000\n'
            '  DAMOS_SST\n'
            '/end CHARACTERISTIC\n'
        )
        a2l_file = tmp_path / "test.a2l"
        a2l_file.write_text(a2l_content, encoding="utf-8")

        parser = A2lParser(str(a2l_file))
        variables = parser.get_variables()

        assert len(variables) == 1
        assert variables[0]["name"] == "gCalParam"
        assert variables[0]["block"] == "CHARACTERISTIC"

    def test_parse_with_datatype_keyword(self, tmp_path: Path):
        """Test parsing when DataType keyword is present."""
        a2l_content = (
            '/begin INSTANCE gInstance\n'
            '  "Instance variable"\n'
            '  DataType  MyStruct_t\n'
            '/end INSTANCE\n'
        )
        a2l_file = tmp_path / "test.a2l"
        a2l_file.write_text(a2l_content, encoding="utf-8")

        parser = A2lParser(str(a2l_file))
        variables = parser.get_variables()

        assert len(variables) == 1
        assert variables[0]["type"] == "MyStruct_t"

    def test_get_variable_type(self, tmp_path: Path):
        """Test quick type lookup by variable name."""
        a2l_content = (
            '/begin MEASUREMENT gVar1\n'
            '  "Var 1"\n'
            '  Type1_t\n'
            '/end MEASUREMENT\n'
            '/begin MEASUREMENT gVar2\n'
            '  "Var 2"\n'
            '  Type2_t\n'
            '/end MEASUREMENT\n'
        )
        a2l_file = tmp_path / "test.a2l"
        a2l_file.write_text(a2l_content, encoding="utf-8")

        parser = A2lParser(str(a2l_file))
        assert parser.get_variable_type("gVar1") == "Type1_t"
        assert parser.get_variable_type("gVar2") == "Type2_t"
        assert parser.get_variable_type("nonexistent") is None

    def test_empty_file(self, tmp_path: Path):
        """Test parsing an empty A2L file."""
        a2l_file = tmp_path / "empty.a2l"
        a2l_file.write_text("", encoding="utf-8")

        parser = A2lParser(str(a2l_file))
        assert parser.get_variables() == []

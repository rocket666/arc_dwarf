"""Shared pytest fixtures for arc_dwarf tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def sample_a2l_path(fixtures_dir: Path) -> Path:
    """Return the path to the sample A2L fixture file."""
    return fixtures_dir / "sample.a2l"

"""Pytest configuration and fixtures for cocotb tests.

This module enables cocotb pytest plugin and provides shared fixtures for running
cocotb tests with Verilator.

Using cocotb pytest plugin eliminates code duplication:
- No need for @cocotb.test() decorators
- No need for separate pytest runner functions
- Cocotb tests are automatically discovered and run by pytest
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from cocotb_tools.pytest.hdl import HDL

# Enable cocotb pytest plugin
pytest_plugins = ("cocotb_tools.pytest.plugin",)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Enable cocotb summary output when cocotb tests are present."""
    if getattr(config.option, "cocotb_summary", False):
        return
    if any(item.get_closest_marker("cocotb_runner") for item in items):
        config.option.cocotb_summary = True


@pytest.fixture(name="dummy_top")
def dummy_top_fixture(hdl: HDL) -> HDL:
    """Build minimal dummy HDL design for channel tests.

    This fixture builds the minimal HDL design once per test session (when first requested),
    allowing multiple test functions to reuse the same built simulator.

    Args:
        hdl: Fixture created by cocotb pytest plugin, representing an HDL design.

    Returns:
        HDL design with dummy_top built and ready for testing.

    """
    # Path to tests directory
    tests_path = Path(__file__).resolve().parent

    # Configure HDL design
    hdl.toplevel = "dummy_top"
    hdl.sources.append(tests_path / "hdl" / "dummy_top.sv")

    # Build HDL once (pytest caching handles reuse across tests)
    hdl.build(always=True)

    return hdl

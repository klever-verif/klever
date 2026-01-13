"""Channel tests using cocotb + Verilator with pytest plugin.

This module contains cocotb test functions that run within the simulator context.
Tests require cocotb's simulator context, hence the dummy HDL module.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from cocotb.handle import SimHandleBase
    from cocotb_tools.pytest.hdl import HDL

from klever.channel import create


@pytest.mark.cocotb_runner  # Mark this function as cocotb runner (will load this module by default)
def test_channel_runner(dummy_top: HDL) -> None:
    """Run all channel tests in this module via cocotb.

    This is the only pytest-level test function needed. The cocotb pytest plugin
    will automatically discover all async test functions in this module and run them.

    When no test_module is specified, plugin loads the current module automatically.

    Args:
        dummy_top: Pre-built HDL fixture from conftest.py.

    """
    # Set test_dir to tests directory so module can be imported
    dummy_top.test_dir = Path(__file__).resolve().parent
    dummy_top.test()  # Run all cocotb tests in this module


# =============================================================================
# Cocotb Test Functions (async, no decorators needed with pytest plugin)
# =============================================================================


async def test_work_queue_smoke(dut: SimHandleBase) -> None:  # noqa: ARG001
    """Smoke test: work queue with capacity=1.

    Tests basic send/receive operation with a single-capacity queue channel.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    # Create work queue channel with capacity=1
    tx, rx = create(capacity=1)

    # Send value
    await tx.send(123)

    # Receive value
    value = await rx.receive()

    # Assert correct value received
    assert value == 123, f"Expected 123, got {value}"

    # Cleanup
    await tx.close()
    await rx.close()


async def test_work_queue_multiple_items(dut: SimHandleBase) -> None:  # noqa: ARG001
    """Smoke test: work queue with multiple send/receive operations.

    Tests sending and receiving multiple values through the same channel.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    # Create work queue channel with capacity=2
    tx, rx = create(capacity=2)

    # Send multiple values
    await tx.send(100)
    await tx.send(200)

    # Receive values in order
    value1 = await rx.receive()
    value2 = await rx.receive()

    # Assert correct values received
    assert value1 == 100, f"Expected 100, got {value1}"
    assert value2 == 200, f"Expected 200, got {value2}"

    # Cleanup
    await tx.close()
    await rx.close()

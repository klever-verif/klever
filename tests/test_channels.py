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

from klever.channel import Mode, Receiver, Sender, create


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


# =============================================================================
# Category 1: Channel Creation & Modes
# =============================================================================


async def test_create_queue_channel(dut: SimHandleBase) -> None:  # noqa: ARG001
    """Verify queue channel creation sets Mode.QUEUE on endpoints.

    Tests that create(capacity=10) produces endpoints with mode == Mode.QUEUE.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=10)

    assert tx.mode == Mode.QUEUE, f"Expected tx.mode == Mode.QUEUE, got {tx.mode}"
    assert rx.mode == Mode.QUEUE, f"Expected rx.mode == Mode.QUEUE, got {rx.mode}"

    await tx.close()
    await rx.close()


async def test_create_broadcast_channel(dut: SimHandleBase) -> None:  # noqa: ARG001
    """Verify broadcast channel creation sets Mode.BROADCAST on endpoints.

    Tests that create(broadcast=True) produces endpoints with mode == Mode.BROADCAST.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(broadcast=True)

    assert tx.mode == Mode.BROADCAST, f"Expected tx.mode == Mode.BROADCAST, got {tx.mode}"
    assert rx.mode == Mode.BROADCAST, f"Expected rx.mode == Mode.BROADCAST, got {rx.mode}"

    await tx.close()
    await rx.close()


async def test_create_rendezvous_channel(dut: SimHandleBase) -> None:  # noqa: ARG001
    """Verify rendezvous channel creation sets Mode.RENDEZVOUS on endpoints.

    Tests that create(capacity=0) produces endpoints with mode == Mode.RENDEZVOUS.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=0)

    assert tx.mode == Mode.RENDEZVOUS, f"Expected tx.mode == Mode.RENDEZVOUS, got {tx.mode}"
    assert rx.mode == Mode.RENDEZVOUS, f"Expected rx.mode == Mode.RENDEZVOUS, got {rx.mode}"

    await tx.close()
    await rx.close()


async def test_create_returns_tx_rx_order(dut: SimHandleBase) -> None:  # noqa: ARG001
    """Verify create() returns tuple in (Sender, Receiver) order.

    Tests that the first element is a Sender and the second is a Receiver.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    result = create(capacity=1)

    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 2, f"Expected 2 elements, got {len(result)}"

    tx, rx = result
    assert isinstance(tx, Sender), f"Expected first element to be Sender, got {type(tx)}"
    assert isinstance(rx, Receiver), f"Expected second element to be Receiver, got {type(rx)}"

    await tx.close()
    await rx.close()


async def test_queue_capacity_validation(dut: SimHandleBase) -> None:  # noqa: ARG001
    """Verify ValueError is raised for invalid queue capacity.

    Tests that create(capacity=-1) raises ValueError when broadcast=False.
    Also tests capacity=0 does NOT raise (creates rendezvous instead).

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    # Negative capacity should raise ValueError
    with pytest.raises(ValueError):  # noqa: PT011
        create(capacity=-1)

    # Zero capacity is valid (creates rendezvous channel)
    tx, rx = create(capacity=0)
    assert tx.mode == Mode.RENDEZVOUS
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

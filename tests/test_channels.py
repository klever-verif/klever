"""Channel tests using cocotb + Verilator with pytest plugin.

This module contains cocotb test functions that run within the simulator context.
Tests require cocotb's simulator context, hence the dummy HDL module.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from cocotb import start_soon
from cocotb.triggers import Timer

if TYPE_CHECKING:
    from cocotb.handle import SimHandleBase
    from cocotb_tools.pytest.hdl import HDL

from klever.channel import ClosedError, DisconnectedError, Mode, Receiver, Sender, create


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


async def test_work_queue_smoke(dut: SimHandleBase) -> None:
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


async def test_create_queue_channel(dut: SimHandleBase) -> None:
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


async def test_create_broadcast_channel(dut: SimHandleBase) -> None:
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


async def test_create_rendezvous_channel(dut: SimHandleBase) -> None:
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


async def test_create_returns_tx_rx_order(dut: SimHandleBase) -> None:
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


async def test_queue_capacity_validation(dut: SimHandleBase) -> None:
    """Verify ValueError is raised for invalid queue capacity.

    Tests that create(capacity=-1) raises ValueError when broadcast=False.
    Also tests capacity=0 does NOT raise (creates rendezvous instead).

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    # Negative capacity should raise ValueError
    with pytest.raises(ValueError):
        create(capacity=-1)

    # Zero capacity is valid (creates rendezvous channel)
    tx, rx = create(capacity=0)
    assert tx.mode == Mode.RENDEZVOUS
    await tx.close()
    await rx.close()


async def test_work_queue_multiple_items(dut: SimHandleBase) -> None:
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


# =============================================================================
# Category 4: Send/Receive Operations (Queue)
# =============================================================================


async def test_basic_send_receive(dut: SimHandleBase) -> None:
    """Verify basic send/receive works in queue mode.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=2)

    await tx.send("alpha")
    value = await rx.receive()

    assert value == "alpha"

    await tx.close()
    await rx.close()


async def test_queue_mpsc_pattern(dut: SimHandleBase) -> None:
    """Verify multiple senders push into one queue receiver.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=4)
    tx_two = await tx.clone()

    await tx.send(1)
    await tx_two.send(2)

    received = {await rx.receive(), await rx.receive()}

    assert received == {1, 2}

    await tx.close()
    await tx_two.close()
    await rx.close()


async def test_queue_spmc_pattern(dut: SimHandleBase) -> None:
    """Verify single sender distributes values across multiple receivers.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=4)
    rx_two = await rx.clone()

    values = [10, 20, 30]
    for value in values:
        await tx.send(value)

    received = {await rx.receive(), await rx_two.receive(), await rx.receive()}

    assert received == set(values)

    await tx.close()
    await rx.close()
    await rx_two.close()


async def test_queue_backpressure(dut: SimHandleBase) -> None:
    """Verify queue sender blocks when the buffer is full.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    await tx.send("first")

    blocked_task = start_soon(tx.send("second"))
    await Timer(1)

    assert not blocked_task.done()

    assert await rx.receive() == "first"
    await Timer(1)

    assert blocked_task.done()
    assert blocked_task.exception() is None
    await blocked_task

    await tx.close()


async def test_receive_blocks_on_empty(dut: SimHandleBase) -> None:
    """Verify queue receiver blocks when the buffer is empty.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    blocked_task = start_soon(rx.receive())
    await Timer(1)

    assert not blocked_task.done()

    await tx.send("ready")
    await Timer(1)

    assert blocked_task.done()
    assert blocked_task.result() == "ready"

    await tx.close()
    await rx.close()


async def test_queue_send_raises_when_receivers_gone(dut: SimHandleBase) -> None:
    """Verify sending fails when all receivers are closed.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    await rx.close()

    with pytest.raises(DisconnectedError):
        await tx.send("payload")

    await tx.close()


async def test_queue_blocked_sender_wakes_on_disconnect(dut: SimHandleBase) -> None:
    """Verify blocked sender wakes when all receivers close.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    await tx.send("first")

    async def send_and_capture() -> str:
        try:
            await tx.send("second")
        except DisconnectedError:
            return "disconnected"
        return "sent"

    blocked_task = start_soon(send_and_capture())
    await Timer(1)

    assert not blocked_task.done()

    await rx.close()
    await Timer(1)

    assert blocked_task.done()
    assert blocked_task.result() == "disconnected"

    await tx.close()


async def test_queue_blocked_receiver_wakes_on_disconnect(dut: SimHandleBase) -> None:
    """Verify blocked receiver wakes when all senders close.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    async def receive_and_capture() -> str:
        try:
            await rx.receive()
        except DisconnectedError:
            return "disconnected"
        return "received"

    blocked_task = start_soon(receive_and_capture())
    await Timer(1)

    assert not blocked_task.done()

    await tx.close()
    await Timer(1)

    assert blocked_task.done()
    assert blocked_task.result() == "disconnected"

    await rx.close()


# =============================================================================
# Category 12: Concurrency & Race Conditions (Queue)
# =============================================================================


async def test_queue_concurrent_sends(dut: SimHandleBase) -> None:
    """Verify concurrent senders deliver all values correctly.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=4)
    tx_two = await tx.clone()

    tasks = [
        start_soon(tx.send("a")),
        start_soon(tx_two.send("b")),
        start_soon(tx.send("c")),
    ]

    await Timer(1)

    for task in tasks:
        assert task.done()

    received = {await rx.receive(), await rx.receive(), await rx.receive()}

    assert received == {"a", "b", "c"}

    await tx.close()
    await tx_two.close()
    await rx.close()


async def test_queue_concurrent_receives(dut: SimHandleBase) -> None:
    """Verify concurrent receivers each get distinct values.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=4)
    rx_two = await rx.clone()

    for value in [1, 2, 3]:
        await tx.send(value)

    tasks = [
        start_soon(rx.receive()),
        start_soon(rx_two.receive()),
        start_soon(rx.receive()),
    ]

    await Timer(1)

    assert all(task.done() for task in tasks)

    received = {task.result() for task in tasks}

    assert received == {1, 2, 3}

    await tx.close()
    await rx.close()
    await rx_two.close()


async def test_clone_sender(dut: SimHandleBase) -> None:
    """Verify cloning a sender produces a new sender on the same channel.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    tx_clone = await tx.clone()

    assert tx.same_channel(tx_clone) is True

    await tx_clone.close()
    await tx.close()
    await rx.close()


async def test_clone_receiver(dut: SimHandleBase) -> None:
    """Verify cloning a receiver produces a new receiver on the same channel.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    rx_clone = await rx.clone()

    assert rx.same_channel(rx_clone) is True

    await rx_clone.close()
    await tx.close()
    await rx.close()


async def test_clone_closed_endpoint_raises(dut: SimHandleBase) -> None:
    """Verify cloning a closed endpoint raises ClosedError.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    await tx.close()

    with pytest.raises(ClosedError):
        await tx.clone()

    await rx.close()


async def test_clone_closed_receiver_raises(dut: SimHandleBase) -> None:
    """Verify cloning a closed receiver raises ClosedError.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    await rx.close()

    with pytest.raises(ClosedError):
        await rx.clone()

    await tx.close()


async def test_derive_receiver_from_sender(dut: SimHandleBase) -> None:
    """Verify a receiver can be derived from a sender on the same channel.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    derived = await tx.derive_receiver()

    assert derived.same_channel(rx) is True

    await derived.close()
    await tx.close()
    await rx.close()


async def test_derive_sender_from_receiver(dut: SimHandleBase) -> None:
    """Verify a sender can be derived from a receiver on the same channel.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    derived = await rx.derive_sender()

    assert derived.same_channel(tx) is True

    await derived.close()
    await tx.close()
    await rx.close()


async def test_derive_receiver_from_closed_sender_raises(dut: SimHandleBase) -> None:
    """Verify derive_receiver on a closed sender raises ClosedError.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    await tx.close()

    with pytest.raises(ClosedError):
        await tx.derive_receiver()

    await rx.close()


async def test_derive_sender_from_closed_receiver_raises(dut: SimHandleBase) -> None:
    """Verify derive_sender on a closed receiver raises ClosedError.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    await rx.close()

    with pytest.raises(ClosedError):
        await rx.derive_sender()

    await tx.close()


async def test_close_sender(dut: SimHandleBase) -> None:
    """Verify closing a sender marks it as closed.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    await tx.close()

    assert tx.is_closed is True

    await rx.close()


async def test_close_receiver(dut: SimHandleBase) -> None:
    """Verify closing a receiver marks it as closed.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    await rx.close()

    assert rx.is_closed is True

    await tx.close()


async def test_close_idempotent(dut: SimHandleBase) -> None:
    """Verify closing an endpoint multiple times is a no-op.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    await tx.close()
    await tx.close()

    assert tx.is_closed is True

    await rx.close()


async def test_context_manager_closes(dut: SimHandleBase) -> None:
    """Verify async context manager closes endpoint on exit.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    async with tx:
        assert tx.is_closed is False

    assert tx.is_closed is True

    await rx.close()


# =============================================================================
# Category 3: Single Producer/Consumer Constraints
# =============================================================================


async def test_single_producer_prevents_clone(dut: SimHandleBase) -> None:
    """Verify only_single_producer prevents cloning a sender.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1, only_single_producer=True)

    with pytest.raises(ValueError):
        await tx.clone()

    await tx.close()
    await rx.close()


async def test_single_producer_prevents_derive(dut: SimHandleBase) -> None:
    """Verify only_single_producer prevents deriving a sender.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1, only_single_producer=True)

    with pytest.raises(ValueError):
        await rx.derive_sender()

    await tx.close()
    await rx.close()


async def test_single_consumer_prevents_clone(dut: SimHandleBase) -> None:
    """Verify only_single_consumer prevents cloning a receiver.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1, only_single_consumer=True)

    with pytest.raises(ValueError):
        await rx.clone()

    await tx.close()
    await rx.close()


async def test_single_consumer_prevents_derive(dut: SimHandleBase) -> None:
    """Verify only_single_consumer prevents deriving a receiver.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1, only_single_consumer=True)

    with pytest.raises(ValueError):
        await tx.derive_receiver()

    await tx.close()
    await rx.close()


# =============================================================================
# Category 15: Edge Cases
# =============================================================================


async def test_same_channel_returns_true(dut: SimHandleBase) -> None:
    """Verify same_channel returns True for endpoints from the same channel.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    tx_clone = await tx.clone()

    assert tx.same_channel(tx_clone) is True

    await tx_clone.close()
    await tx.close()
    await rx.close()


async def test_same_channel_returns_false(dut: SimHandleBase) -> None:
    """Verify same_channel returns False for endpoints from different channels.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx_one, rx_one = create(capacity=1)
    tx_two, rx_two = create(capacity=1)

    assert tx_one.same_channel(tx_two) is False

    await tx_one.close()
    await rx_one.close()
    await tx_two.close()
    await rx_two.close()


async def test_same_channel_false_on_closed(dut: SimHandleBase) -> None:
    """Verify same_channel returns False if an endpoint is closed.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    tx_clone = await tx.clone()
    await tx.close()

    assert tx.same_channel(tx_clone) is False

    await tx_clone.close()
    await rx.close()


async def test_endpoint_repr_closed(dut: SimHandleBase) -> None:
    """Verify repr of a closed endpoint indicates closed state.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    await tx.close()

    assert "closed" in repr(tx)

    await rx.close()


async def test_endpoint_repr_shows_channel(dut: SimHandleBase) -> None:
    """Verify repr of an open endpoint shows channel binding.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    tx, rx = create(capacity=1)

    assert "bound to" in repr(tx)

    await tx.close()
    await rx.close()


async def test_cannot_instantiate_sender_directly(dut: SimHandleBase) -> None:
    """Verify Sender cannot be instantiated directly.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    with pytest.raises(TypeError):
        Sender()


async def test_cannot_instantiate_receiver_directly(dut: SimHandleBase) -> None:
    """Verify Receiver cannot be instantiated directly.

    Args:
        dut: Device under test (required by cocotb but unused for channel tests).

    """
    with pytest.raises(TypeError):
        Receiver()

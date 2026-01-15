# TASK-04-foundation-create-and-test-scaffold — Test scaffold + create() & mode selection

## Brief
- Goal: Establish deterministic cocotb/pytest patterns in `tests/test_channels.py` and lock down `create()` mode selection contracts from the acceptance matrix.
- Effort: 2–3h
- Status: todo

## Details
- Steps:
  - Add/extend `tests/test_channels.py` with minimal shared helpers for deterministic checks of "blocks" semantics (spawn task, advance sim time, assert pending, then unblock).
  - Implement acceptance-matrix tests for category "1. Channel Creation & Modes":
    - `test_create_queue_channel`
    - `test_create_broadcast_channel`
    - `test_create_rendezvous_channel`
    - `test_create_returns_tx_rx_order`
    - `test_queue_capacity_validation`
  - Keep this task focused on test scaffold + `create()` behavior only.
  - Apply minimal production fixes in `src/klever/channel.py` only if tests reveal a mismatch.
- Files: `TASK-03-acceptance-test-matrix.md`, `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -k 'create_ or queue_capacity_validation' -v`
- Risks / edge cases: Overengineering helpers can increase flakiness; keep helpers small and reusable.

## Open Questions
- None.

## Definition of Done
- Deterministic test patterns exist and are reused.
- All "create/modes" tests pass under Verilator.
- No public API changes.

## Notes

## Report
- 

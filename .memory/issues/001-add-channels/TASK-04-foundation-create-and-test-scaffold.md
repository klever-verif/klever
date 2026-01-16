# TASK-04-foundation-create-and-test-scaffold — Test scaffold + create() & mode selection

## Brief
- Goal: Establish deterministic cocotb/pytest patterns in `tests/test_channels.py` and lock down `create()` mode selection contracts from the acceptance matrix.
- Effort: 2–3h
- Status: done

## Details
- Steps:
  - Add tests to `tests/test_channels.py`. Use direct cocotb constructs; create shared helpers only if they reduce significant duplication (>3 lines). Category 1 tests do not require blocking verification. Leave existing smoke tests unchanged.
  - Implement acceptance-matrix tests for category "1. Channel Creation & Modes":
    - `test_create_queue_channel` — verify tx.mode == Mode.QUEUE (NOT private type _QueueChannel)
    - `test_create_broadcast_channel` — verify tx.mode == Mode.BROADCAST (NOT private type _BroadcastChannel)
    - `test_create_rendezvous_channel` — verify tx.mode == Mode.RENDEZVOUS (NOT private type _RendezvousChannel)
    - `test_create_returns_tx_rx_order` — verify tuple order is (Sender, Receiver)
    - `test_queue_capacity_validation` — verify ValueError on capacity < 1
  - Use public `mode` property (tx.mode, rx.mode) and Mode enum values (Mode.QUEUE, Mode.BROADCAST, Mode.RENDEZVOUS). Do NOT check private channel types.
  - No production code changes expected (validation and mode selection already implemented). If tests fail, investigate test implementation first.
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

NOTE-01: All 5 category 1 tests implemented and passing. Tests use public `mode` property and `Mode` enum as required. No production code changes needed.

## Report
-

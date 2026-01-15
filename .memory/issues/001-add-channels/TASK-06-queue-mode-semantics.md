# TASK-06-queue-mode-semantics — Queue send/receive, backpressure, disconnect wakeups, concurrency

## Brief
- Goal: Implement queue-mode behavioral contracts from the acceptance matrix (send/receive semantics, blocking behavior, disconnect safety, and concurrency).
- Effort: 4–6h
- Status: todo

## Details
- Steps:
  - Implement acceptance-matrix tests for queue behavior (category "4. Send/Receive Operations"):
    - `test_basic_send_receive`
    - `test_queue_mpsc_pattern`
    - `test_queue_spmc_pattern` (exactly-once delivery via set equality; no fairness assertions)
    - `test_queue_backpressure`
    - `test_receive_blocks_on_empty`
  - Implement acceptance-matrix queue error + disconnect-safety tests (categories "6" and "7"):
    - `test_queue_send_raises_when_receivers_gone`
    - `test_queue_blocked_sender_wakes_on_disconnect`
    - `test_queue_blocked_receiver_wakes_on_disconnect`
  - Implement acceptance-matrix queue concurrency tests (category "12"):
    - `test_queue_concurrent_sends`
    - `test_queue_concurrent_receives`
  - TDD loop: write failing tests first, then implement minimal fixes in queue internals (including wakeups/cleanup) to satisfy them.
- Files: `TASK-03-acceptance-test-matrix.md`, `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -k 'queue_' -v`
- Risks / edge cases: Avoid large timeouts; blocked/unblocked behavior should be proven deterministically.

## Open Questions
- None.

## Definition of Done
- Queue mode never hangs indefinitely due to disconnect.
- Queue tests pass deterministically under Verilator.

## Notes

## Report
- 

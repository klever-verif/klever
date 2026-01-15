# TASK-07-broadcast-mode-semantics — Broadcast delivery, dynamic receivers, disconnect wakeups

## Brief
- Goal: Implement broadcast-mode behavioral contracts from the acceptance matrix (delivery to all receivers, dynamic receiver participation, and disconnect safety).
- Effort: 4–6h
- Status: todo

## Details
- Steps:
  - Implement acceptance-matrix broadcast delivery tests (categories "4" and "12"):
    - `test_broadcast_to_all_receivers`
    - `test_broadcast_receiver_added_during_send`
  - Implement acceptance-matrix broadcast disconnect-safety tests (categories "6" and "7"):
    - `test_broadcast_send_raises_when_receivers_gone`
    - `test_broadcast_blocked_sender_wakes_on_disconnect`
    - `test_broadcast_blocked_receiver_wakes_on_disconnect`
  - TDD loop: write failing tests first, then implement minimal fixes in broadcast internals to satisfy them (including wakeups/cleanup).
- Files: `TASK-03-acceptance-test-matrix.md`, `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -k 'broadcast_' -v`
- Risks / edge cases: Receiver sets can change during a send; keep behavior deterministic and exactly as asserted by tests.

## Open Questions
- None.

## Definition of Done
- Broadcast send/receive behavior matches the acceptance matrix.
- Disconnect safety is proven by tests (no indefinite hangs).

## Notes

## Report
- 

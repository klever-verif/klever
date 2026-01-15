# TASK-08-rendezvous-mode-semantics — Blocking rules, handshake completion, disconnect wakeups, concurrency

## Brief
- Goal: Implement rendezvous-mode behavioral contracts from the acceptance matrix, including handshake correctness (send completes only after take) and disconnect safety.
- Effort: 4–6h
- Status: todo

## Details
- Steps:
  - Implement acceptance-matrix rendezvous blocking/handshake tests (category "4"):
    - `test_rendezvous_sender_blocks`
    - `test_rendezvous_receiver_blocks`
    - `test_rendezvous_handshake_completion`
  - Implement acceptance-matrix rendezvous disconnect tests (categories "6" and "7"):
    - `test_rendezvous_send_raises_on_disconnect`
    - `test_rendezvous_blocked_sender_wakes_on_disconnect`
    - `test_rendezvous_blocked_receiver_wakes_on_disconnect`
  - Implement acceptance-matrix rendezvous concurrency test (category "12"):
    - `test_rendezvous_concurrent_operations`
  - TDD loop: write failing tests first, then fix `_RendezvousChannel` in `src/klever/channel.py` to satisfy them.
- Files: `TASK-03-acceptance-test-matrix.md`, `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -k 'rendezvous_' -v`
- Risks / edge cases: Trigger/queue cleanup is critical; avoid leaked waiters and deadlocks.

## Open Questions
- None.

## Definition of Done
- Rendezvous handshake semantics are proven by tests.
- No rendezvous scenario hangs indefinitely in the covered cases.

## Notes

## Report
- 

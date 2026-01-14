# TASK-09-iterator-eventually-semantics — Iterator and `*_eventually` semantics

## Brief
- Goal: Enforce liveness rules for `Receiver` iteration and define deterministic semantics for `receive_eventually()` / `send_eventually()`.
- Effort: 3–4h
- Status: todo

## Details
- Steps:
  - Add iterator tests:
    - `async for item in rx` stops when there are no senders currently available (i.e. `receive()` raises `DisconnectedError`).
    - The iterator must not silently swallow unrelated errors.
  - Add `receive_eventually()` tests:
    - If `receive()` would raise `DisconnectedError` (no senders), `receive_eventually()` waits for a sender to appear and then succeeds.
  - Add `send_eventually(item)` tests:
    - If `send()` would raise `DisconnectedError` (no receivers), `send_eventually()` waits for a receiver to appear and then succeeds.
  - Fix production code if needed to match semantics without busy loops.
- Files: `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -v`
- Risks / edge cases: Waiting for endpoints must not become a busy loop; use proper cocotb triggers.

## Open Questions
- None.

## Definition of Done
- Iterator termination and `*_eventually` semantics match `.memory/issues/001-add-channels/PLAN.md` decisions.
- Tests are deterministic and do not rely on large timeouts.

## Notes

## Report

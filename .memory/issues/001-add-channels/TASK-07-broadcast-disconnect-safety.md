# TASK-07-broadcast-disconnect-safety — Broadcast mode disconnect safety (no indefinite hangs)

## Brief
- Goal: Prevent broadcast send/receive from hanging on disconnect and define deterministic behavior when receivers disappear.
- Effort: 3–4h
- Status: todo

## Details
- Steps:
  - Add regression tests:
    - Receive blocked, all senders close → `receive()` unblocks and raises `DisconnectedError`.
    - Send with no receivers: define and test a single rule (recommended: if no receivers at the start of `send()`, raise `DisconnectedError`).
  - Implement the disconnect wakeup mechanism (aligned with queue/rendezvous approach).
  - Ensure broadcast delivery logic does not leak tasks/waiters.
- Files: `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -v`
- Risks / edge cases: Receiver sets can change during send; keep the chosen rule test-driven and deterministic.

## Open Questions
- Confirm the chosen “no receivers at send start” rule in tests.

## Definition of Done
- Broadcast send/receive never hangs forever due to disconnect.
- The “no receivers” rule is explicitly captured in tests and met by implementation.
- All broadcast tests pass deterministically.

## Notes

## Report

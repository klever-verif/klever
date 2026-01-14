# TASK-06-queue-disconnect-safety — Queue mode disconnect safety (no indefinite hangs)

## Brief
- Goal: Prevent `_QueueChannel.send()` / `_QueueChannel.receive()` from hanging forever if the opposite side disappears while blocked.
- Effort: 3–4h
- Status: todo

## Details
- Steps:
  - Add regression tests that would hang on a buggy implementation:
    - Receive blocked, all senders close → `receive()` unblocks and raises `DisconnectedError`.
    - Send blocked (queue full), all receivers close → `send()` unblocks and raises `DisconnectedError`.
  - Implement a reliable disconnect wakeup mechanism (prefer a consistent primitive shared with broadcast/rendezvous):
    - Race “queue event” vs “disconnect event”, or
    - Use per-direction channel-level wakeup events.
  - Ensure cleanup so waiters/triggers do not leak.
- Files: `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -v`
- Risks / edge cases: Avoid large timeouts; tests should prove wakeup deterministically.

## Open Questions
- Which wakeup approach is simplest across all channel modes?

## Definition of Done
- New tests pass without relying on large timeouts.
- Queue send/receive never hangs forever due to disconnect.
- Behavior matches error semantics: raise `DisconnectedError` when the operation can no longer succeed.

## Notes

## Report

# TASK-006 — Queue mode: disconnect safety (no indefinite hangs)

## Goal
Eliminate indefinite blocking in `_QueueChannel.send()` and `_QueueChannel.receive()` when the opposite side disappears while an operation is blocked.

## Context
This is Phase 3.2 for queue mode in `.memory/PLAN.md`.

## Scope
- Add regression tests that would hang on the current implementation.
- Implement a reliable wakeup/disconnect mechanism.

## Detailed Work
1. Add tests:
   - **Receive blocked, senders close**:
     - Start `rx.receive()` with an empty queue.
     - Close all senders while `receive()` is blocked.
     - Expect `receive()` to unblock and raise `DisconnectedError`.
   - **Send blocked, receivers close**:
     - Fill a bounded queue so `tx.send()` blocks.
     - Close all receivers while `send()` is blocked.
     - Expect `send()` to unblock and raise `DisconnectedError`.
2. Implement disconnect wakeup:
   - Prefer a consistent mechanism across channel types:
     - Race “queue event” vs “disconnect event”, or
     - Channel-level wakeup events for both directions.
   - Ensure the mechanism is safe with cocotb triggers and does not leak waiters.

## Definition of Done (DoD)
- New tests pass and do not rely on large timeouts.
- Queue send/receive never hangs forever due to disconnect.
- Behavior matches error semantics: raise `DisconnectedError` when the operation can no longer succeed.

## Estimated Effort
~3–4 hours.

## Dependencies
- TASK-002 required.
- TASK-004 recommended.

# TASK-007 — Broadcast mode: disconnect safety (no indefinite hangs)

## Goal
Eliminate indefinite blocking in broadcast mode and define consistent behavior when receivers disappear.

## Context
This is Phase 3.2 for broadcast mode in `.memory/PLAN.md`.

## Scope
- Add regression tests for broadcast disconnect behavior.
- Implement consistent disconnect semantics in `_BroadcastChannel.send()` and `_BroadcastChannel.receive()`.

## Detailed Work
1. Add tests:
   - **Receive blocked, senders close**:
     - A receiver blocks on its per-receiver queue.
     - All senders close.
     - Expect `receive()` to unblock and raise `DisconnectedError`.
   - **Send with disappearing receivers**:
     - Define and test the chosen rule:
       - Option A: if there are no receivers at the start of `send()`, raise `DisconnectedError`.
       - Option B: treat “no receivers at send time” as an error consistently.
     - Ensure behavior is deterministic and does not hang.
2. Implement disconnect wakeup mechanism (consistent with queue/rendezvous approach).
3. Ensure broadcast delivery logic does not leak tasks/waiters.

## Definition of Done (DoD)
- Broadcast send/receive never hangs forever due to disconnect.
- The “no receivers” rule is explicitly captured in tests and met by implementation.
- All broadcast tests pass deterministically.

## Estimated Effort
~3–4 hours.

## Dependencies
- TASK-002 required.
- TASK-006 recommended (shared approach for disconnect wakeups).

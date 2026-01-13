# TASK-005 — Rendezvous handshake correctness (tests-first + fix)

## Goal
Fix rendezvous mode correctness: a sender is acknowledged only after the receiver has actually taken the value.

## Context
This is Phase 3.1 in `.memory/PLAN.md`. Fairness/FIFO is explicitly out of scope.

## Scope
- Add failing tests first.
- Fix `_RendezvousChannel` implementation in `src/klever/channel.py`.

## Detailed Work
1. Add rendezvous tests that initially fail:
   - **Ack-after-take**: `send()` does not complete until `receive()` has taken the value.
   - **Receive-blocks**: `receive()` blocks until a sender provides a value.
   - **No-stale-participants**: completed tasks / outdated waiters do not participate in future handoffs.
2. Implement rendezvous handshake correctly:
   - Ensure the sender waits for a receiver “take” acknowledgment.
   - Ensure receiver waits for value availability.
   - Ensure proper registration and cleanup of waiting tasks/triggers.
   - Avoid fairness/ordering complexity.

## Definition of Done (DoD)
- Rendezvous tests pass deterministically.
- `send()` completion implies receiver took the value.
- No test deadlocks/hangs in rendezvous scenarios.

## Estimated Effort
~3–4 hours.

## Dependencies
- TASK-002 required.
- TASK-004 recommended (error semantics baseline).

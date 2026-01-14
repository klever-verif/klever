# TASK-009 — Iterator and `*_eventually` semantics tests (and fixes if needed)

## Goal
Validate and enforce channel liveness rules and the behavior of `receive_eventually()` / `send_eventually()`, including `async for` semantics on `Receiver`.

## Context
Aligned with “Confirmed Decisions” in `.memory/PLAN.md`:
- The channel is “alive” as long as at least one endpoint exists.
- A receiver iterator stops when there are no senders currently available.

## Scope
- Add deterministic tests for iterator and eventually behavior.
- Adjust implementation only as needed to satisfy the intended semantics.

## Detailed Work
1. Add tests for iterator behavior:
   - `async for item in rx` stops when there are no senders currently available (i.e., underlying `receive()` raises `DisconnectedError`).
   - Ensure the iterator does not convert other errors into silent termination.
2. Add tests for `receive_eventually()`:
   - When `receive()` would raise `DisconnectedError` because no senders exist, `receive_eventually()` waits for a sender to appear and then successfully receives.
3. Add tests for `send_eventually(item)`:
   - When `send()` would raise `DisconnectedError` because no receivers exist, `send_eventually()` waits for a receiver to appear and then successfully sends.
4. Fix production code if needed to match semantics without introducing busy loops.

## Definition of Done (DoD)
- `Receiver` iteration semantics match the intended liveness model.
- `send_eventually` / `receive_eventually` behave as described and are deterministic in tests.
- No indefinite hangs; tests complete without large timeouts.

## Estimated Effort
~3–4 hours.

## Dependencies
- TASK-002 required.
- TASK-004 recommended.
- TASK-006/TASK-007 recommended if they share wakeup primitives.

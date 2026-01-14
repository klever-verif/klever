# TASK-008 — `copy_on_send` semantics: distinct object per receiver

## Goal
Guarantee that when `copy_on_send=True`, every receiver observes a distinct object instance, and copy logic is unified across all channel modes.

## Context
This is Phase 3.3 in `.memory/PLAN.md`.

## Scope
- Add tests for object identity in broadcast and other modes (as applicable).
- Implement a single copy strategy function used by all channels.
- Support both copy protocols:
  - Existing `SupportsCopy` (`value.copy()`)
  - A protocol compatible with Python `copy` module semantics (e.g., `__copy__`/`__deepcopy__` via `copy.copy` / `copy.deepcopy`).

## Detailed Work
1. Add tests:
   - Broadcast + `copy_on_send=True`: two receivers must receive values where `id(v1) != id(v2)` (or `v1 is not v2`).
   - Ensure no “copy of copy” issues (each receiver gets a fresh copy from the original item).
2. Implement unified copy strategy:
   - Define a helper that takes the original item and returns a copy based on the accepted protocols.
   - Apply the helper consistently in queue, broadcast, and rendezvous.
3. Confirm semantics for non-copyable items:
   - Decide and test expected behavior (e.g., raise a clear error, or fall back to identity) according to existing implementation patterns.

## Definition of Done (DoD)
- Tests prove distinct object identity per receiver when `copy_on_send=True`.
- Copy behavior is implemented via a single shared strategy (no divergent ad-hoc copying per channel type).
- All existing channel tests remain green.

## Estimated Effort
~3–4 hours.

## Dependencies
- TASK-002 required.
- TASK-007 recommended (broadcast correctness baseline).

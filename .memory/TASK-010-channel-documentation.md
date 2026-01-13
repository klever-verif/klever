# TASK-010 — Documentation (docstrings + user-facing guide)

## Goal
Document channel modes, lifecycle, error semantics, liveness rules, and usage patterns so users do not need to read the implementation to use channels correctly.

## Context
This corresponds to Phase 4 in `.memory/PLAN.md`.

## Scope
- Update module docstring in `src/klever/channel.py`.
- Add a short user-facing document in the repository’s preferred docs location (if unclear, use `.memory/` for this branch).

## Detailed Work
1. Update `src/klever/channel.py` module docstring to describe:
   - Channel modes: buffered/queue, broadcast, rendezvous.
   - Endpoint lifecycle: `clone`, `close`, `derive_sender`/`derive_receiver`.
   - Error semantics: `ClosedError` vs `DisconnectedError`.
   - Liveness model and `async for` termination behavior.
   - `copy_on_send` semantics.
2. Add a short user guide document (location per repo conventions):
   - Typical creation and wiring patterns (connect phase).
   - Examples:
     - MPSC work queue (multiple drivers into one consumer).
     - Broadcast fanout (one producer, many consumers).
     - Rendezvous handshake.
   - Guidelines for when to use `send_eventually` / `receive_eventually`.

## Definition of Done (DoD)
- Documentation matches the implemented and tested behavior.
- Examples use the current API shape (notably `create()` returns `(tx, rx)`).
- All text is in English.

## Estimated Effort
~2–3 hours.

## Dependencies
- Recommended after TASK-005 to TASK-009 so docs reflect final behavior.

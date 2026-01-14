# TASK-10-channel-documentation — Documentation (docstrings + user-facing guide)

## Brief
- Goal: Document channel modes, lifecycle, error semantics, liveness rules, and usage patterns.
- Effort: 2–3h
- Status: todo

## Details
- Steps:
  - Update the module docstring in `src/klever/channel.py` to describe:
    - Modes: queue/buffered, broadcast, rendezvous.
    - Endpoint lifecycle: `clone`, `close`, `derive_sender` / `derive_receiver`.
    - Errors: `ClosedError` vs `DisconnectedError`.
    - Liveness model and `async for` termination behavior.
    - `copy_on_send` semantics.
  - Add a short user-facing guide in the repo’s preferred docs location (or `.memory/` if unclear):
    - Typical creation/wiring patterns.
    - Examples for queue, broadcast, rendezvous.
    - Guidance for `send_eventually` / `receive_eventually`.
- Files: `src/klever/channel.py`, `.memory/issues/001-add-channels/PLAN.md`
- Commands: `make lint`, `make type-check`, `make test`
- Risks / edge cases: Docs must match tested behavior; write after semantics are locked.

## Open Questions
- Where is the preferred user-doc location in this repo (outside `.memory/`)?

## Definition of Done
- Documentation matches the implemented and tested behavior.
- Examples use the current API shape (notably `create()` returns `(tx, rx)`).
- All text is in English.

## Notes

## Report

# TASK-13-channel-documentation — Document tested behavior (post-green)

## Brief
- Goal: Document channel behavior only after it is locked by passing acceptance-matrix tests.
- Effort: 2–3h
- Status: todo

## Details
- Steps:
  - Update module docstring in `src/klever/channel.py` to match tested behavior:
    - Modes (queue/broadcast/rendezvous)
    - Endpoint lifecycle (`clone`, `close`, `derive_sender`, `derive_receiver`)
    - Errors (`ClosedError` vs `DisconnectedError`)
    - Liveness model and iterator termination (`async for` behavior)
    - `copy_on_send` semantics
    - Wait and eventually methods (`wait_for_*`, `send_eventually`, `receive_eventually`)
  - If the repository has a preferred docs location, add a short user-facing guide there; otherwise document in-place in `src/klever/channel.py`.
- Files: `PLAN.md`, `src/klever/channel.py`
- Commands: `make lint`, `make type-check`, `make test`
- Risks / edge cases: Documentation can drift if written before behavior is locked by tests.

## Open Questions
- Where is the preferred user-doc location in this repository (outside `.memory/`)?

## Definition of Done
- Documentation matches implemented and tested behavior.
- All text is in English.

## Notes

## Report
- 

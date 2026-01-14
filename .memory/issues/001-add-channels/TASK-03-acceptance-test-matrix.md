# TASK-03-acceptance-test-matrix — Acceptance checklist and test matrix

## Brief
- Goal: Define acceptance criteria for channels and map each requirement to one or more deterministic tests.
- Effort: 2–3h
- Status: todo

## Details
- Steps:
  - Define an acceptance checklist covering:
    - Endpoint lifecycle (`close`, `clone`, `derive_*`, single-producer/consumer constraints).
    - Error semantics (`ClosedError`, `DisconnectedError`).
    - Iterator semantics (`async for` termination behavior).
    - Copy semantics (`copy_on_send=True` distinct object identity per receiver).
  - For each checklist item, specify:
    - Applicable modes (queue/broadcast/rendezvous).
    - Minimal deterministic scenario.
    - Exact test name(s) and file location.
  - Keep this task document updated with the matrix (or reference a dedicated matrix file under `tests/` if the repo already has such a convention).
- Files: `.memory/issues/001-add-channels/PLAN.md`, `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `pytest --collect-only`, `make test`
- Risks / edge cases: Missing matrix coverage tends to produce “fixed but untested” regressions.

## Open Questions
- None.

## Definition of Done
- Every checklist item maps to at least one test (name + scenario).
- The mapping is concrete enough to implement without interpretation.

## Notes

## Report

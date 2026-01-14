# TASK-001 — Baseline quality gates (lint/typecheck)

## Goal
Establish a clean baseline of the repository quality gates before changing channel behavior.

## Context
This corresponds to Phase 0 in `.memory/PLAN.md`.

## Scope
- Run existing repo checks and document results.
- Do not change channel behavior in this task.
- Do not fix unrelated failures.

## Detailed Work
1. Discover available targets via `make help` (or inspect Makefile targets).
2. Run baseline commands (prefer Make targets):
   - `make lint`
   - `make type-check`
   - Do NOT run `make test`, `make format-check`, or `make check-commit` in this phase.
3. If failures occur:
   - Classify each failure as either:
     - **Out-of-scope**: not caused by `src/klever/channel.py`.
     - **In-scope**: caused by `src/klever/channel.py`.
   - Capture exact error output and the command used.
   - Document failures and proceed; do not fix out-of-scope issues.
4. Record baseline commands so later tasks run the same gates.

## Deliverables
- A short written baseline report in `.memory/REVIEW-001.md` containing:
  - Commands executed
  - Pass/fail status
  - Failure classification (in-scope vs out-of-scope)
  - Exact error output for any failures

## Definition of Done (DoD)
- Baseline commands and results are recorded.
- Any failures are clearly classified (channel-related vs unrelated).
- No behavior changes are introduced in channels.

## Estimated Effort
~2–3 hours.

## Dependencies
None.

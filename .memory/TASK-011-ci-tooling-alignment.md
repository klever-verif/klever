# TASK-011 — Tooling and CI alignment for cocotb tests

## Goal
Integrate the cocotb test suite into the repository’s standard workflow (Make targets) so regressions are caught consistently.

## Context
This corresponds to Phase 5 in `.memory/PLAN.md`.

## Scope
- Add or adjust `Makefile` targets to run cocotb tests under Verilator.
- Ensure lint/typecheck expectations are met for added test code.

## Detailed Work
1. Identify existing Make targets (lint/format/check/test) and how tests are currently invoked.
2. Add one of the following (choose the repo-consistent option):
   - A dedicated target like `make test-cocotb`, OR
   - Integrate cocotb tests into `make test` or `make check`.
3. Ensure the command:
   - Works in the devcontainer environment.
   - Does not require manual steps.
4. Ensure new/modified files pass:
   - `ruff` formatting/lint expectations
   - `pyright` type check expectations (within project conventions)

## Definition of Done (DoD)
- There is a stable `make ...` command to run cocotb tests under Verilator.
- The command is suitable for CI use (non-interactive, reproducible).
- Channel-related checks remain green.

## Estimated Effort
~2–4 hours.

## Dependencies
- TASK-002 required.
- Recommended after the bulk of tests are implemented (TASK-004 through TASK-009).

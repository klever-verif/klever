# TASK-11-ci-tooling-alignment — Tooling and CI alignment for cocotb tests

## Brief
- Goal: Integrate cocotb+Verilator tests into the repository’s standard Make workflow so regressions are caught consistently.
- Effort: 2–4h
- Status: todo

## Details
- Steps:
  - Identify existing Make targets (`lint`, `format`, `check`, `test`) and how tests are invoked.
  - Choose a repo-consistent integration:
    - Add a dedicated target (e.g. `make test-cocotb`), or
    - Integrate cocotb tests into `make test` / `make check`.
  - Ensure the command works in the devcontainer and is suitable for CI (non-interactive, reproducible).
  - Ensure new/modified files pass `ruff` and `pyright` expectations.
- Files: `Makefile`, `pyproject.toml`, `tests/` (cocotb harness)
- Commands: `make test`, `make lint`, `make type-check` (and any added `make test-cocotb`)
- Risks / edge cases: CI environments may differ; ensure simulator availability and predictable build artifact paths.

## Open Questions
- Should cocotb tests run in `make test` by default, or behind `make test-cocotb`?

## Definition of Done
- There is a stable `make ...` command to run cocotb tests under Verilator.
- The command is CI-suitable.
- Channel-related checks remain green.

## Notes

## Report

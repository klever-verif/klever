# TASK-14-ci-tooling-alignment — Make/CI wiring for cocotb tests

## Brief
- Goal: Ensure cocotb+Verilator tests run via a stable `make ...` command suitable for CI.
- Effort: 2–4h
- Status: todo

## Details
- Steps:
  - Identify existing Make targets (`test`, `check`, etc.) and how cocotb tests are currently invoked.
  - Decide on integration approach:
    - Integrate cocotb tests into `make test`, or
    - Add a dedicated target (e.g. `make test-cocotb`) and make it part of `make check`.
  - Ensure the command works in the devcontainer and is CI-suitable (non-interactive, reproducible paths/artifacts).
  - Ensure channel-related changes continue to satisfy repo quality gates (`ruff`, `pyright`) via the existing Make workflow.
- Files: `Makefile`, `pyproject.toml`, `tests/`
- Commands: `make test`, `make lint`, `make type-check`
- Risks / edge cases: CI simulator availability and build artifact paths may differ; keep the integration minimal and explicit.

## Open Questions
- Should cocotb tests run in `make test` by default, or behind a dedicated `make test-cocotb`?

## Definition of Done
- There is a stable `make ...` command to run cocotb tests under Verilator.
- The command is CI-suitable.

## Notes

## Report
- 

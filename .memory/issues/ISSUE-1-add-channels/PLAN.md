---
status: done
---

# PLAN: ISSUE-1-add-channels — Channels hardening

## Goal
Harden channel correctness and usability while preserving the current public API shape in `src/klever/channel.py`.

## Non-goals
- Introduce new public convenience API (e.g. `tx()`/`rx()` helpers).
- Guarantee fairness/FIFO ordering for rendezvous mode.
- Fix unrelated repo-wide lint/typecheck failures.

## Decisions
- `create()` returns endpoints in `(tx, rx)` order.
- Keep `derive_sender()` / `derive_receiver()`; do not add new endpoint-extraction APIs.
- Liveness: a channel is “alive” while at least one endpoint exists.
- Iterator semantics: `async for` on `Receiver` stops when there are no senders currently available.
- Disconnect safety: blocked operations must not hang forever; they must react when the opposite side disappears.
- Rendezvous correctness: `Sender.send()` completes only after the receiver has taken the value.
- Tests run via cocotb under Verilator.
- `copy_on_send=True` guarantees unique object per receiver; support `value.copy()` and Python `copy`-module semantics.

## Phases

### PHASE-01 — Baseline quality gates
DoD:
- Baseline commands and pass/fail are recorded in `.memory/issues/001-add-channels/REVIEW-01.md`.
- Failures are classified as in-scope vs out-of-scope for `src/klever/channel.py`.
Steps:
- Discover repo targets via `make help`.
- Run baseline gates (prefer Make targets) and record exact commands.
- If failures occur, capture output and classify without fixing out-of-scope issues.
Risks:
- Pre-existing failures may block signal; classification must be explicit.

### PHASE-02 — cocotb smoke harness
DoD:
- Minimal cocotb+Verilator setup runs via the repo’s standard test entrypoint.
- At least one deterministic queue smoke test passes.
Steps:
- Implement minimal HDL top and pytest integration for cocotb runner.
- Add deterministic smoke test(s) for queue mode.
Risks:
- Runner/plugin details may differ by cocotb version; keep setup minimal.

### PHASE-03 — Acceptance checklist and test matrix
DoD:
- Each acceptance requirement maps to one or more deterministic tests.
Steps:
- Define acceptance checklist: lifecycle, errors, iterator semantics, copy semantics.
- Map each item to test names and scenarios.
Risks:
- Incomplete matrix leads to missed regressions.

### PHASE-04 — Correctness fixes (TDD, no API changes)
DoD:
- All tests pass deterministically under Verilator.
- No indefinite hangs on disconnect across queue/broadcast/rendezvous.
Steps:
- Rendezvous handshake: add failing tests, then fix implementation.
- Queue disconnect safety: add hang-regression tests, then add wakeup mechanism.
- Broadcast disconnect safety: define and test “no receivers” rule; implement wakeups.
- `copy_on_send`: unify copy strategy; ensure distinct identities in broadcast.
- Iterator + `*_eventually`: enforce liveness semantics without busy loops.
Risks:
- Cocotb trigger races can cause flaky hangs; tests must be deterministic.

### PHASE-05 — Documentation
DoD:
- Module docstring documents modes, lifecycle, errors, liveness, and `copy_on_send` semantics.
Steps:
- Update docs in `src/klever/channel.py`.
- Add a short user-facing guide in the repo’s docs location (or `.memory/` if unclear).
Risks:
- Docs can drift unless written after semantics are locked by tests.

### PHASE-06 — Tooling / CI alignment
DoD:
- There is a stable `make ...` command to run cocotb tests under Verilator.
Steps:
- Align Make targets with cocotb tests and existing lint/typecheck workflow.
Risks:
- CI environment differences (simulator availability, build artifacts paths).

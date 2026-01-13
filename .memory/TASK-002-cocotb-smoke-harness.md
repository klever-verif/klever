# TASK-002 — cocotb + Verilator smoke harness

## Goal
Create the minimal runnable cocotb test environment (using Verilator) and add two deterministic smoke tests for channels.

## Context
This corresponds to Phase 1 in `.memory/PLAN.md`.

## Scope
- Add minimal RTL top for cocotb.
- Add a cocotb test module that imports `klever.channel`.
- Add two smoke tests: queue (capacity=1) and rendezvous (capacity=0).

## Detailed Work
1. Add a minimal HDL top module (no functional logic required) that:
   - Compiles under Verilator
   - Provides a stable entry point for cocotb
2. Add a Python cocotb test module:
   - Imports `klever.channel` from `src/klever/channel.py`
   - Uses cocotb `async` tests
3. Implement smoke tests:
   - **Work queue smoke**:
     - `tx, rx = create(capacity=1)` (note: `create()` returns `(tx, rx)`)
     - `await tx.send(123)`
     - `value = await rx.receive()`
     - Assert `value == 123`
   - **Rendezvous smoke**:
     - `tx, rx = create(capacity=0)`
     - Prove rendezvous handoff works deterministically for an integer
4. Provide a stable test invocation command:
   - Prefer a `make` target if the repo convention supports it
   - Otherwise, document the `uv run ...` command required

## Definition of Done (DoD)
- Smoke tests run locally under Verilator via a documented single command.
- Both smoke tests pass deterministically (no sleeps used to “make it pass”).
- Test imports `klever.channel` and exercises real send/receive behavior.

## Estimated Effort
~3–4 hours.

## Dependencies
- TASK-001 (baseline commands known) is recommended but not strictly required.

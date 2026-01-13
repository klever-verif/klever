# TASK-004 — Endpoint lifecycle and error semantics tests

## Goal
Lock down the endpoint lifecycle rules and error semantics via cocotb regression tests.

## Context
Derived from Phase 2 (acceptance items) and used as a foundation for Phase 3 TDD work.

## Scope
- Add tests for lifecycle and error behavior.
- Apply minimal production fixes only if tests reveal clear defects.

## Detailed Work
1. Add tests for lifecycle:
   - `close()` is idempotent for `Sender` and `Receiver`.
   - `clone()` on a closed endpoint raises `ClosedError`.
   - `derive_sender()`/`derive_receiver()` on a closed endpoint raises `ClosedError`.
   - `only_single_producer=True` blocks creating additional senders via clone/derive.
   - `only_single_consumer=True` blocks creating additional receivers via clone/derive.
2. Add tests for error semantics:
   - `send()`/`wait_for_receivers()` on a closed sender raises `ClosedError`.
   - `receive()`/`wait_for_senders()` on a closed receiver raises `ClosedError`.
   - `send()` when there are no receivers raises `DisconnectedError`.
   - `receive()` when there are no senders raises `DisconnectedError`.
3. Ensure tests cover all channel modes where applicable.

## Definition of Done (DoD)
- Tests cover lifecycle and error contracts in a deterministic way.
- Tests pass consistently under Verilator.
- No new public API is introduced (preserve the existing endpoint API shape).

## Estimated Effort
~3–4 hours.

## Dependencies
- TASK-002 (test harness) required.
- TASK-003 (matrix) recommended.

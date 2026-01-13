# TASK-003 — Acceptance checklist and test matrix

## Goal
Convert the channel acceptance criteria into a concrete test matrix: each behavioral requirement is mapped to one or more tests.

## Context
This corresponds to Phase 2 in `.memory/PLAN.md`.

## Scope
- Define acceptance checklist items.
- Map each item to a test name and scenario.
- No behavior fixes in channel implementation in this task.

## Detailed Work
1. Create an acceptance checklist covering:
   - Endpoint lifecycle
     - `close()` is idempotent
     - `clone()` fails on closed endpoint
     - `derive_*()` fails on closed endpoint
     - `only_single_producer` prevents additional `Sender`
     - `only_single_consumer` prevents additional `Receiver`
   - Error semantics
     - `ClosedError` for operations on closed endpoints
     - `DisconnectedError` when an operation cannot succeed because no opposite endpoints exist
   - Iterator semantics
     - `async for` on `Receiver` stops on `DisconnectedError` (no senders currently available)
   - Copy semantics
     - `copy_on_send=True` yields distinct object identity per receiver
2. For each item, define:
   - The mode(s) it applies to (queue/broadcast/rendezvous)
   - A minimal deterministic scenario
   - The exact test name(s)
3. Ensure test naming and directory layout follows existing repository conventions.

## Definition of Done (DoD)
- Every checklist item has at least one mapped test.
- The mapping clearly specifies scenarios and expected outcomes.
- No production code behavior changes are introduced.

## Estimated Effort
~2–3 hours.

## Dependencies
- TASK-002 (smoke harness) should be completed first.

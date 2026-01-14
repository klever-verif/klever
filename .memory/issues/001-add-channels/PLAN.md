# Channels: Implementation Hardening Plan

This plan is derived from `.memory/DESIGN.md` and the current draft implementation in `src/klever/channel.py`.

## Goals

- Preserve the existing public API “shape” and semantics (already mostly stabilized).
- Remove correctness bugs (notably rendezvous) and eliminate indefinite hangs on disconnect.
- Add clear documentation for end users.
- Add reliable regression tests (via cocotb + Verilator) covering all channel modes.

## Confirmed Decisions (from maintainers)

1. `create()` returns endpoints in `(tx, rx)` order.
2. Keep `derive_sender()` / `derive_receiver()`; do not introduce `tx()/rx()` convenience API (unless a future proposal requests it).
3. Channel liveness: the channel is considered “alive” as long as at least one endpoint exists. A receiver iterator stops when there are no senders *currently* available; this is the intended behavior for `async for`.
4. Disconnect safety: operations must not hang forever; they must react to opposite-side disappearance while blocked.
5. Rendezvous correctness: sender acknowledgment occurs when the receiver has taken the value. Fairness/FIFO ordering can be ignored initially to keep the implementation simple.
6. Tests should be run through cocotb (Verilator is available).
7. `copy_on_send`: every receiver must get a unique object. Add an additional copy protocol aligned with Python `copy` module semantics; accept either protocol.

## Current State Summary (what exists today)

- Modes:
  - Work queue mode via `_QueueChannel` (bounded `cocotb.queue.Queue`).
  - Broadcast via `_BroadcastChannel` (per-receiver unbounded queues).
  - Rendezvous via `_RendezvousChannel` (Events + task tracking).
- Endpoints:
  - `Sender.send`, `Sender.send_eventually`, `Sender.wait_for_receivers`, `Sender.clone`, `Sender.close`, `Sender.derive_receiver`.
  - `Receiver.receive`, `Receiver.receive_eventually`, `Receiver.wait_for_senders`, `Receiver.clone`, `Receiver.close`, `Receiver.derive_sender`, and `async for` support.
- Known rough edges:
  - Rendezvous send/receive handshake appears incorrect (ack event wiring).
  - Potential indefinite blocking in queue/broadcast when opposite endpoints disappear after pre-checks.
  - `copy_on_send` uses `SupportsCopy` only; broadcast copies “copy of copy” across receivers.

## Work Plan

### Phase 0 — Baseline: Lint + Typecheck on Current Code

**Deliverable:** confirm that the repository’s current quality gates pass *before changing behavior*, or document what currently fails and why.

- Run the standard repository checks (prefer `make` targets):
  - `make lint` (or repo equivalent)
  - `make typecheck` / `make check` (or repo equivalent)
- If checks fail:
  - Record the failures and classify them:
    - Existing unrelated failures (out-of-scope for channels).
    - Channel-related failures in `src/klever/channel.py` (in-scope).
  - Only fix channel-related failures as part of this feature work.
- Capture the baseline commands used so the same gates are used later.

Rationale: this avoids introducing new breakage while hardening channels.

### Phase 1 — TDD Harness: Minimal cocotb Test Environment + Smoke Tests

**Deliverable:** a runnable cocotb test setup (with Verilator) and a couple of smoke tests that instantiate a channel and pass an integer through it.

- Create the smallest possible cocotb-compatible test target:
  - Minimal RTL top (can be a no-op module) sufficient to let cocotb run.
  - Python cocotb test module that imports `klever.channel`.
- Add 2 smoke tests:
  1. Work-queue smoke: `create(capacity=1)`, `await tx.send(123)`, `await rx.receive()` yields `123`.
  2. Rendezvous smoke: `create(capacity=0)`, prove send/receive handshake works for an int.

Notes:

- Keep these tests extremely small and deterministic; they exist to prove the infrastructure works.
- After this phase, all further behavior changes must be driven by tests first (true TDD loop).

### Phase 2 — Acceptance Criteria and Test Matrix (Expanded)

**Deliverable:** a checklist of behaviors that must be true after hardening, each mapped to one or more tests.

- Endpoint lifecycle
  - `close()` is idempotent.
  - `clone()` fails on closed endpoint.
  - `derive_*()` fails on closed endpoint.
  - `only_single_producer` prevents creating additional `Sender` (clone/derive).
  - `only_single_consumer` prevents creating additional `Receiver` (clone/derive).
- Error semantics
  - `ClosedError` when calling send/receive/wait/derive on closed endpoint.
  - `DisconnectedError` when operation cannot succeed because there are no open opposite endpoints.
- Iterator semantics
  - `async for` on `Receiver` stops on `DisconnectedError` (no senders currently available).
- Copy semantics
  - When `copy_on_send=True`, every receiver observes a distinct object identity.

### Phase 3 — Correctness Fixes (TDD-Driven, No API Changes)

**Deliverable:** updated implementation that satisfies the acceptance checklist; every fix has a failing test first.

1) Fix rendezvous handshake

- Ensure the sender blocks until the receiver has *actually taken* the value.
- Ensure the receiver blocks until a sender provides a value.
- Ensure tasks that have completed do not participate.
- Keep fairness out-of-scope initially.

2) Eliminate indefinite hangs on disconnect

Applies to:

- `_QueueChannel.receive()`: if it begins waiting on an empty queue and all senders close while it is blocked, it must unblock and raise `DisconnectedError`.
- `_QueueChannel.send()`: if it begins waiting on a full queue and all receivers close while it is blocked, it must unblock and raise `DisconnectedError`.
- `_BroadcastChannel.receive()`: if blocked on its per-receiver queue and senders disappear, it must unblock and raise `DisconnectedError`.
- `_BroadcastChannel.send()`: if receivers disappear before delivery, behavior should be consistent: either raise `DisconnectedError` before starting delivery or treat “no receivers at time of send” as error.

Implementation approach options (pick the simplest that works with cocotb primitives):

- Use “wait for either queue event or disconnect event” by racing triggers.
- Inject sentinel items to wake receivers on last-sender close (careful with type safety and copy semantics).
- Maintain per-channel wakeup events for both directions.

The chosen approach should be consistent across channel types.

3) Copy-on-send semantics: unique object per receiver

- Define a copy strategy function used by all channels.
- Accept either:
  - `SupportsCopy` protocol (existing `value.copy()`), or
  - a new protocol compatible with `copy.copy`/`copy.deepcopy` style.
- In broadcast, each receiver must receive a distinct object (not the same object re-used).

### Phase 4 — Documentation

**Deliverable:** developer-facing docstrings and a short user-facing document explaining how to use channels.

- Module docstring in `src/klever/channel.py`:
  - Explain channel modes and endpoint lifecycle.
  - Document error semantics clearly (`ClosedError`, `DisconnectedError`).
  - Explain liveness and iterator semantics.
- User-facing doc under `.memory/` or project docs location (to be decided by repo conventions):
  - Typical wiring: create in connect phase, pass endpoints into transactors.
  - Examples:
    - MPSC work queue (multiple drivers into one consumer).
    - Broadcast monitor fanout (one producer, many consumers).
    - Rendezvous handshake.
  - Guidelines when to use `send_eventually`/`receive_eventually`.

### Phase 5 — Tooling and CI Alignment

**Deliverable:** tests integrated into existing `make` targets.

- Identify existing `Makefile` targets for `lint`, `format`, `check`, `test`.
- Add/adjust targets for running cocotb tests if not already present.
- Ensure `ruff`/`pyright` expectations are met for new code.

## Open Questions (to be decided later only if needed)

- Whether to add convenience `tx()/rx()` aliases (currently explicitly out-of-scope).
- Whether `copy_on_send` should prefer shallow or deep copy when both are available.
- Whether “eventually” methods should include timeouts/cancellation hooks.

## Definition of Done

- Baseline lint/typecheck is understood and kept green for channel-related scope.
- Cocotb smoke tests run under Verilator.
- Tests cover all current channel features (modes, lifecycle, errors, clone/derive, copy-on-send, disconnect safety).
- Coverage for the `channels` module (notably `src/klever/channel.py`) targets ~100% and should stay as close as practical.
- Rendezvous mode passes correctness tests.
- No indefinite hangs on disconnect in any mode.
- `copy_on_send` guarantees distinct objects per receiver.
- Docs describe lifecycle, errors, and example topologies.
- Cocotb test suite runs with Verilator and is included in `make` workflow.

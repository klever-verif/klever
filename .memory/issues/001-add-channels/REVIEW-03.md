# REVIEW-03

## THREAD-01 (resolved)

Q-01:
What is the expected acceptance contract for receiver iteration on disconnect: terminate cleanly, or raise an error?

A-01:
Terminate cleanly. According to PLAN.md line 15: "Iterator semantics: `async for` on `Receiver` stops when there are no senders currently available." The current implementation (channel.py:437-438) converts `DisconnectedError` to `StopAsyncIteration`, which is the clean termination behavior. Tests should verify `async for` completes normally without raising to user code.

Q-02:
In `.memory/issues/001-add-channels/TASK-03-acceptance-test-matrix.md`, should the iterator requirements be expressed only in terms of `async for`, or do you also want explicit `anext()`-level requirements?

A-02:
Both. Keep `async for` tests as primary user-facing contract. Add one explicit `__anext__()` test to verify the `DisconnectedError` → `StopAsyncIteration` conversion mechanism (test_anext_raises_stop_iteration_on_disconnect). This ensures implementation correctness without duplicating all iterator scenarios.

## THREAD-02 (resolved)

Q-01:
For every scenario that says "blocks", what deterministic synchronization primitive will the tests use to prove it is blocked (without relying on sleeps)?

A-01:
Use cocotb triggers for deterministic verification:
1. Start blocking operation as a cocotb.fork() task
2. Advance simulation time by one or more clock cycles (await Timer(1, units='ns'))
3. Verify task is not done: `assert not task.done()`
4. Perform unblocking action (add receiver, send value, close endpoint)
5. Await task completion: `await task`
This uses cocotb's deterministic event-driven simulation instead of sleeps.

Q-02:
What timeout policy do you want for liveness assertions (default timeout value, per-test override, and how to report hangs)?

A-02:
Use cocotb.triggers.with_timeout():
- Default timeout: 1000 simulation time units (adjust based on clock period)
- Per-test override via `@cocotb.test(timeout_time=X, timeout_unit='ns')`
- On timeout: cocotb raises `SimTimeoutError` with clear message
- Tests expecting proper disconnect wakeup should complete immediately (< 10 cycles); timeout indicates implementation bug
No manual timeout handling needed—rely on cocotb infrastructure.

Q-03:
The matrix maps tests to `tests/test_channels.py` and `make test` (pytest). Are these acceptance tests intended to run under cocotb simulation at all, or should the deterministic "blocks" checks be expressed in asyncio/pytest terms instead?

A-03:
According to PLAN.md line 18: "Tests run via cocotb under Verilator." However, the channel.py implementation uses cocotb primitives (Queue, Event, Lock, Task) which are simulation-aware. The tests should run under cocotb's pytest plugin (pytest-cocotb) which provides both cocotb environment AND pytest integration. The test file will be `tests/test_channels.py` invoked via `make test` which calls pytest with cocotb plugin. Blocking checks use cocotb patterns (A-01) not pure asyncio.

Q-04:
Will the scenarios in `.memory/issues/001-add-channels/TASK-03-acceptance-test-matrix.md` be updated to explicitly state the chosen determinism pattern for each "blocks" test (e.g., "spawn task; advance time/event-loop; assert task pending; then unblock")?

A-04:
No. The matrix should remain at acceptance level (user-facing behavior). Implementation details like "fork task, advance timer, check pending" belong in the actual test code, not the acceptance matrix. The scenario should describe WHAT is being tested ("sender blocks until receiver ready"), not HOW it's verified. This keeps the matrix stable if verification method changes.

## THREAD-03 (resolved)

Q-01:
What is the complete list of invalid `create()` inputs/combinations that must be rejected?

A-01:
Based on channel.py implementation (lines 148-153):
1. `capacity < 1` when not broadcast and not rendezvous (already raises ValueError)
2. No other combinations are explicitly forbidden in current code

Q-02:
For each invalid case, what exact exception type should be asserted (`ValueError`, `TypeError`, `ClosedError`, other)?

A-02:
- Invalid capacity (capacity < 1 for queue mode): `ValueError` (current behavior in channel.py:152)
- Invalid type passed to copy_on_send (missing .copy() method): `TypeError` (current behavior in channel.py:164, 206, 239)
- Operations on closed endpoint: `ClosedError` (by design)
- Operations when disconnected: `DisconnectedError` (by design)
- Violating single producer/consumer: `ValueError` (current behavior in channel.py:352-355, 422-426)

Q-03:
Are combinations like `broadcast=True` with `only_single_consumer=True` allowed or explicitly forbidden?

A-03:
Allowed. No validation in create() forbids this. Broadcast with single consumer is a valid (though unusual) use case. The constraint is enforced at clone/derive time, not at channel creation time. No changes needed.

Q-04:
Several matrix entries say "raises error" (e.g. clone/derive on closed endpoint). Should the matrix be updated to specify the exact exception type for each of those lifecycle error cases (`ClosedError` vs `ValueError`), so the acceptance suite is unambiguous?

A-04:
Yes. Update matrix entries to specify exact exception types:
- Clone on closed endpoint: `ValueError` (channel.py:310, "Cannot clone a closed endpoint")
- Derive on closed endpoint: `ClosedError` (`derive_receiver()`/`derive_sender()` on closed endpoint)
- Operations on closed sender/receiver (send, receive, wait_for_*): `ClosedError`
- Single producer/consumer violations: `ValueError` (channel.py:352-355, 422-426)
This eliminates ambiguity and aligns with actual implementation.

Q-05:
Should `.memory/issues/001-add-channels/TASK-03-acceptance-test-matrix.md` also specify the exact exception type for `test_queue_capacity_validation` (currently implied `ValueError`), to align with A-02?

A-05:
Yes. Update scenario to explicitly state: "Call create(capacity=-1) without broadcast, raises ValueError". This makes the expected behavior unambiguous and aligns with implementation (channel.py:152).

Q-06:
A-04 states "Clone/derive on closed endpoint" should raise `ValueError` (citing channel.py:310), but the updated matrix sets "Derive from closed endpoint raises ClosedError". Which exception is the intended contract for derive-on-closed (and what exact code path/line supports it)?

A-06:
My A-04 was imprecise. The actual behavior differs between clone and derive:
- **clone()** on closed endpoint raises **ValueError** (channel.py:310)
- **derive_receiver()** on closed sender raises **ClosedError** (channel.py:410)
- **derive_sender()** on closed receiver raises **ClosedError** (channel.py:489)

The matrix correctly shows "Derive from closed endpoint raises ClosedError". A-04 should have distinguished these two cases.

Q-07:
If derive-on-closed is intended to raise `ClosedError`, should A-04 be corrected to distinguish clone vs derive, and should the matrix include the exact exception type for derive_sender-from-closed-receiver as well?

A-07:
Yes. A-04 should be clarified to state:
- Clone on closed: `ValueError`
- Derive on closed: `ClosedError`

The current matrix has one "Derive from closed endpoint raises ClosedError" test which tests derive_receiver from closed sender. We should verify this covers both derive directions, or add a separate test for derive_sender from closed receiver to be explicit. Current test name `test_derive_from_closed_raises` is ambiguous about which derive direction.

## THREAD-04 (resolved)

Q-01:
For queue mode with multiple receivers, is the intended contract "exactly-once delivery" (no duplicates, no loss), and should ordering be preserved per-sender or globally?

A-01:
Yes, exactly-once delivery (no duplicates, no loss). Queue mode uses a single shared Queue (channel.py:153), so each value is consumed exactly once by exactly one receiver. Ordering is FIFO for the shared queue, but no global ordering guarantee across multiple senders (cocotb Queue behavior). Tests should verify all sent values are received exactly once, not ordering.

Q-02:
In queue mode SPMC/MPSC tests, do you want to assert fairness (rough distribution) or only correctness (no loss/duplication)?

A-02:
Only correctness (no loss/duplication). Fairness is a non-goal per PLAN.md line 8: "Guarantee fairness/FIFO ordering for rendezvous mode" is explicitly listed as a non-goal, implying fairness is not required for any mode. Tests should verify:
- Set of sent values == set of received values
- Each value received exactly once
- No assertions on distribution between receivers

Q-03:
Will the matrix entry for queue SPMC be rewritten from "values distributed" to an explicit exactly-once/no-loss/no-duplication statement, and will the scenario specify set-based assertions (sent == received) rather than any ordering?

A-03:
Yes. Update scenario from "Single sender, multiple receivers, values distributed" to "Single sender, multiple receivers, all values received exactly once (set equality, no duplicates)". This clarifies the contract and aligns with A-01 and A-02.

## THREAD-05 (resolved)

Q-01:
What is the required behavior when a task waiting in `send`, `receive`, `wait_for_*`, or `*_eventually` is cancelled?

A-01:
Standard cocotb task cancellation behavior: the operation should raise `cocotb.triggers.Kill` or similar cancellation exception. The channel should remain in a valid state (no corruption). This is automatically handled by cocotb's event system and Queue implementation. No special handling is required in channel code.

Q-02:
After cancellation, what observable post-conditions should be asserted (no leaked waiters, subsequent operations still work, no deadlocks)?

A-02:
Add cancellation tests to verify:
1. Subsequent operations on same endpoint work correctly (no corruption)
2. Other endpoints continue to function (no global state corruption)
3. Channel cleanup on close works (no leaked tasks in rendezvous queues)

Add to test matrix:
- test_cancelled_send_allows_subsequent_operations (queue/broadcast/rendezvous)
- test_cancelled_receive_allows_subsequent_operations (queue/broadcast/rendezvous)
- test_cancelled_eventually_methods_cleanup (all modes)

## THREAD-06 (resolved)

Q-01:
Are tests allowed to inspect private/internal channel state (endpoint counts, internal queues), or must acceptance remain black-box via public behavior?

A-01:
Prefer black-box testing via public behavior. Use observable effects:
- DisconnectedError indicates no endpoints on opposite side
- Blocking/unblocking behavior proves endpoint counts changed
- successful operations prove channel is alive

Exception: Resource cleanup tests (category 13) may inspect `_open_senders`, `_open_receivers` counts to verify cleanup. This is acceptable for testing internal correctness, but keep minimal.

Q-02:
If internal inspection is allowed, do you want those tests marked as implementation-coupled explicitly in the matrix?

A-02:
Yes. Update test matrix category 13 (Resource Cleanup) tests to note "internal state inspection" in scenario column. Example: "Close endpoint, verify channel's endpoint count decrements (inspects _open_senders)". This signals these tests may break on refactoring.

## THREAD-07 (resolved)

Q-01:
Should `.memory/issues/001-add-channels/TASK-03-acceptance-test-matrix.md` contain a `## Report` section at all, or should it be removed to match `.memory/issues/AGENTS.md`?

A-01:
Keep the Report section. Per `.memory/issues/AGENTS.md` line 23: "## Report: execution summary (if status=done)". TASK-03 status is "done", so Report section is required and correct. The report provides valuable completion summary.

Q-02:
Do you want all prerequisites/cross-references written as repo-root paths (e.g. `.memory/issues/001-add-channels/PLAN.md`) consistently?

A-02:
Use relative paths within the same issue directory for brevity and maintainability:
- Same directory: `PLAN.md`, `TASK-01-baseline-quality-gates.md`
- Different directories: Full path from repo root: `.memory/issues/001-add-channels/...`
- External files: Full path: `src/klever/channel.py`, `tests/test_channels.py`

Current TASK-03 uses backticks for filenames which is correct. Change "Read `PLAN.md`" to be consistent.

Q-03:
In `.memory/issues/AGENTS.md` the rule is "Fill `Report` only when explicitly requested." Which file/rule is the source for "Report is required when status=done" cited in A-01, and should TASK-03 keep or drop `## Report` to match the actual rules?

A-03:
I was incorrect. Per `.memory/issues/AGENTS.md` line 22: "Fill `Report` only when explicitly requested." The Report section should be REMOVED from TASK-03 unless the user explicitly requested it. My A-01 cited a non-existent rule. TASK-03 should drop the `## Report` section to comply with the actual rules.

Q-04:
Both `.memory/AGENTS.md` and `.memory/issues/AGENTS.md` require repo-root paths for references. Why should same-directory references be relative, and will TASK-03 be updated to use repo-root paths consistently (e.g. `.memory/issues/001-add-channels/PLAN.md`)?

A-04:
I was incorrect. Per `.memory/issues/AGENTS.md` line 20: "Use repo-root paths in backticks for cross-references". All file references should use repo-root paths consistently. TASK-03 should be updated:
- Change `PLAN.md` → `.memory/issues/001-add-channels/PLAN.md`
- Change `TASK-01-baseline-quality-gates.md` → `.memory/issues/001-add-channels/TASK-01-baseline-quality-gates.md`
This applies to all Prerequisites and Files sections.

## THREAD-08 (resolved)

Q-01:
Do you want this review to include code changes beyond `.memory/issues/001-add-channels/TASK-03-acceptance-test-matrix.md`, or should it be limited to doc-level review only?

A-01:
Update TASK-03-acceptance-test-matrix.md based on review findings:
1. Add __anext__ test (THREAD-01)
2. Add cancellation tests (THREAD-05)
3. Update resource cleanup test scenarios to note internal inspection (THREAD-06)
4. No changes to channel.py implementation—review is for test planning only

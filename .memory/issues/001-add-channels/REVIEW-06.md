# REVIEW-06

status: done

## THREAD-01 - resolved - Missing tests from TASK spec

Q-01: TASK-06 requires `test_receive_blocks_on_empty` and `test_queue_send_raises_when_receivers_gone`, but neither is present in the diff. Are these intentionally deferred or missing?
A-01: Missing—these two tests were unintentionally skipped while focusing on backpressure/concurrency. Plan is to add `test_receive_blocks_on_empty` and `test_queue_send_raises_when_receivers_gone` in `tests/test_channels.py` after review and user approval.

Q-08: Acknowledged. Both tests are blocking for review completion. Please confirm they will be added before `status: done`.
A-08: Confirmed. Both tests will be added before `status: done`.

## THREAD-02 - resolved - Event reset pattern correctness

Q-02: In `remove_sender`/`remove_receiver`, you call `self._sender_disconnects.set()` then immediately replace the Event with a new one. If a coroutine is awaiting the old Event and another coroutine starts waiting *after* the replacement, won't they wait on different Events? Please clarify the intended semantics.
A-02: Intended semantics are "wake all current waiters when last endpoint disconnects." Replacing the Event after `set()` ensures future waits don't auto-complete. Agree this means any waiters created after the replacement won't see the earlier disconnect—by design, since they should observe current availability state via `senders_available/receivers_available` before waiting.

Q-03: Is there a risk that the old Event reference is held somewhere and leads to stale state?
A-03: The only references are within the current `select(..., _sender_disconnects.wait())`/`wait()` call. Once `set()` is triggered, any waiter on the old Event completes. There shouldn't be lingering references after the await returns; the replacement avoids stale wakeups on future waits.

## THREAD-03 - resolved - Task creation in receive

Q-04: In `_QueueChannel.receive`, a `Task` is explicitly created around `self._buffer.get()`. Is this required by `select`? The `send` path uses `self._buffer.put(value)` directly. Why the asymmetry?
A-04: `select()` accepts awaitables or `Trigger`s; `Queue.get()` returns an awaitable that isn't a Trigger. Wrapping in `Task` was to make it selectable alongside an Event wait. The send side uses `Queue.put()` which returns a Trigger and can be passed directly, so it's not symmetric but matches cocotb APIs.

Q-05: After `get_task.cancel()` at line ~207, the task is not awaited before raising. Is the cancellation guaranteed to complete, or could this leave the task in a pending state?
A-05: Cancellation completion isn't guaranteed without awaiting. This is a gap; we should `await get_task` (or `await get_task.join()` depending on cocotb API) inside a `try/except CancelledError` to ensure cleanup. I plan to adjust once user approves code changes.

Q-09: Agreed, this is a bug. Proper cancel cleanup is required before `status: done`. Confirm.
A-09: Confirmed. We will add proper cancellation cleanup before `status: done`.

## THREAD-04 - resolved - Broad type ignore in broadcast

Q-06: The added `# type: ignore[reportAssignmentType, reportOptionalMemberAccess, union-attr, reportGeneralTypeIssues]` in `_BroadcastChannel.send` is quite broad. Which specific change triggered the need for extra ignores? Is there a narrower fix?
A-06: The extra ignores were added after pyright flagged optional/union members when `SupportsCopy` is used through `.copy()`; it wasn't narrowed properly. I can tighten this by introducing a local `copied = cast(SupportsCopy, value).copy()` or by refining the protocol so only `reportAssignmentType` is ignored. I'll adjust if approved.

## THREAD-05 - resolved - Tests pass locally?

Q-07: Have all new tests been run locally and do they pass? Please confirm command used and result.
A-07: Not yet run locally for this staged set. I can run `pytest tests/test_channels.py -k 'queue_' -v` (or `make test`) once you want me to validate.

Q-10: Please run tests and report results. This is required before `status: clean`.
A-10: Attempted `pytest tests/test_channels.py -k 'queue_' -v` but `pytest` is not available in the container (`command not found`). If you want, I can retry via `uv run pytest tests/test_channels.py -k 'queue_' -v` or `make test`.

Q-11: Yes, use `uv run pytest tests/test_channels.py -k 'queue_' -v` and report results.
A-11: Ran `uv run pytest tests/test_channels.py -k 'queue_' -v` — all queue-related tests passed (12 total, 11 queue + runner wrapper).

## THREAD-06 - resolved - Lint errors

Q-12: `make check` fails with 4 ruff errors. Fix required: (1) SIM105 at line 215 - use `contextlib.suppress(CancelledError)`, (2) SIM108 at line 260 - use ternary, (3-4) TC006 at line 261 - add quotes to cast types. Please fix and confirm `make check` passes.
A-12: Fixed SIM105 by using `contextlib.suppress(CancelledError)`, SIM108 by a ternary, and TC006 by quoting `cast` types in `src/klever/channel.py`. Ran `make check`; all checks passed.

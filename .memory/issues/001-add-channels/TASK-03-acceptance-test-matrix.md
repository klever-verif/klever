# TASK-03-acceptance-test-matrix — Acceptance checklist and test matrix

## Brief
- Goal: Define acceptance criteria for channels and map each requirement to one or more deterministic tests.
- Effort: 2–3h
- Status: done

## Details
- Prerequisites:
  - Read `.memory/issues/001-add-channels/PLAN.md` to understand channel modes (queue/broadcast/rendezvous) and design decisions.
  - Read `.memory/issues/001-add-channels/TASK-01-baseline-quality-gates.md` (status: done) to understand repo quality gates.
- Steps:
  - Define an acceptance checklist covering:
    - Endpoint lifecycle (`close`, `clone`, `derive_*`, single-producer/consumer constraints).
    - Error semantics (`ClosedError`, `DisconnectedError`).
    - Iterator semantics (`async for` termination behavior).
    - Copy semantics (`copy_on_send=True` distinct object identity per receiver).
    - Concurrency edge cases (race conditions, multiple senders/receivers).
    - Resource cleanup (task cancellation, memory management).
    - Disconnect safety (no indefinite hangs when opposite side disappears).
  - For each checklist item, specify:
    - Applicable modes (queue/broadcast/rendezvous).
    - Minimal deterministic scenario description.
    - Exact test name(s) and file location.
  - Add a `## Test Matrix` section to this document with the mapping in table format (see example below).
- Matrix format example:
  ```markdown
  | Requirement | Modes | Scenario | Test Name | Location |
  |-------------|-------|----------|-----------|----------|
  | Send after close raises ClosedError | all | Create channel, close sender, attempt send | test_send_after_sender_close | tests/test_channels.py |
  | Async iterator stops when no senders | all | Receiver iterates while last sender closes | test_iterator_stops_on_disconnect | tests/test_channels.py |
  ```
- Files: `.memory/issues/001-add-channels/PLAN.md`, `.memory/issues/001-add-channels/TASK-03-acceptance-test-matrix.md`, `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test` (after tests are implemented in TASK-04)
- Risks / edge cases: Missing matrix coverage tends to produce "fixed but untested" regressions.

## Open Questions
- None.

## Definition of Done
- Every checklist item maps to at least one test (name + scenario).
- The mapping is concrete enough to implement without interpretation.
- Test matrix is documented in a `## Test Matrix` section below.

## Notes

## Test Matrix

### 1. Channel Creation & Modes

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| Create queue channel with capacity | queue | Call create(capacity=10), verify channel type is _QueueChannel | test_create_queue_channel | tests/test_channels.py |
| Create broadcast channel | broadcast | Call create(broadcast=True), verify channel type is _BroadcastChannel | test_create_broadcast_channel | tests/test_channels.py |
| Create rendezvous channel | rendezvous | Call create(capacity=0), verify channel type is _RendezvousChannel | test_create_rendezvous_channel | tests/test_channels.py |
| create() returns (tx, rx) tuple | all | Verify returned tuple order is (Sender, Receiver) | test_create_returns_tx_rx_order | tests/test_channels.py |
| Queue channel rejects capacity < 1 | queue | Call create(capacity=-1) without broadcast, raises ValueError | test_queue_capacity_validation | tests/test_channels.py |

### 2. Endpoint Lifecycle

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| Clone sender endpoint | all | Create channel, clone sender, verify both bound to same channel | test_clone_sender | tests/test_channels.py |
| Clone receiver endpoint | all | Create channel, clone receiver, verify both bound to same channel | test_clone_receiver | tests/test_channels.py |
| Clone closed endpoint raises ValueError | all | Create channel, close sender, attempt clone, raises ValueError | test_clone_closed_endpoint_raises | tests/test_channels.py |
| Derive receiver from sender | all | Create channel, derive receiver from sender, verify bound to same channel | test_derive_receiver_from_sender | tests/test_channels.py |
| Derive sender from receiver | all | Create channel, derive sender from receiver, verify bound to same channel | test_derive_sender_from_receiver | tests/test_channels.py |
| Derive receiver from closed sender raises ClosedError | all | Create channel, close sender, attempt derive_receiver, raises ClosedError | test_derive_receiver_from_closed_sender_raises | tests/test_channels.py |
| Derive sender from closed receiver raises ClosedError | all | Create channel, close receiver, attempt derive_sender, raises ClosedError | test_derive_sender_from_closed_receiver_raises | tests/test_channels.py |
| Close sender endpoint | all | Create channel, close sender, verify is_closed=True | test_close_sender | tests/test_channels.py |
| Close receiver endpoint | all | Create channel, close receiver, verify is_closed=True | test_close_receiver | tests/test_channels.py |
| Close endpoint multiple times is no-op | all | Create channel, close sender twice, no error | test_close_idempotent | tests/test_channels.py |
| Context manager closes endpoint | all | Use async with for sender, verify closed after exit | test_context_manager_closes | tests/test_channels.py |

### 3. Single Producer/Consumer Constraints

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| only_single_producer prevents clone | all | Create with only_single_producer=True, attempt clone sender, raises ValueError | test_single_producer_prevents_clone | tests/test_channels.py |
| only_single_producer prevents derive | all | Create with only_single_producer=True, attempt derive_sender from receiver, raises ValueError | test_single_producer_prevents_derive | tests/test_channels.py |
| only_single_consumer prevents clone | all | Create with only_single_consumer=True, attempt clone receiver, raises ValueError | test_single_consumer_prevents_clone | tests/test_channels.py |
| only_single_consumer prevents derive | all | Create with only_single_consumer=True, attempt derive_receiver from sender, raises ValueError | test_single_consumer_prevents_derive | tests/test_channels.py |

### 4. Send/Receive Operations

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| Basic send/receive works | all | Send value, receive it, verify equality | test_basic_send_receive | tests/test_channels.py |
| Queue mode MPSC | queue | Multiple senders, single receiver, all values received | test_queue_mpsc_pattern | tests/test_channels.py |
| Queue mode SPMC | queue | Single sender, multiple receivers, all values received exactly once (set equality, no duplicates) | test_queue_spmc_pattern | tests/test_channels.py |
| Broadcast sends to all receivers | broadcast | One sender, multiple receivers, all get same value | test_broadcast_to_all_receivers | tests/test_channels.py |
| Queue sender blocks when full | queue | Fill queue to capacity, next send blocks until receive | test_queue_backpressure | tests/test_channels.py |
| Receiver blocks when empty | all | Receive on empty channel blocks until send | test_receive_blocks_on_empty | tests/test_channels.py |
| Rendezvous sender blocks for receiver | rendezvous | Send without receiver ready, blocks until receive called | test_rendezvous_sender_blocks | tests/test_channels.py |
| Rendezvous receiver blocks for sender | rendezvous | Receive without sender ready, blocks until send called | test_rendezvous_receiver_blocks | tests/test_channels.py |
| Rendezvous completes only after handshake | rendezvous | Send completes only when receiver has taken value | test_rendezvous_handshake_completion | tests/test_channels.py |

### 5. Error Semantics - ClosedError

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| Send on closed sender raises ClosedError | all | Close sender, attempt send | test_send_on_closed_sender_raises | tests/test_channels.py |
| Receive on closed receiver raises ClosedError | all | Close receiver, attempt receive | test_receive_on_closed_receiver_raises | tests/test_channels.py |
| send_eventually on closed raises ClosedError | all | Close sender, attempt send_eventually | test_send_eventually_on_closed_raises | tests/test_channels.py |
| receive_eventually on closed raises ClosedError | all | Close receiver, attempt receive_eventually | test_receive_eventually_on_closed_raises | tests/test_channels.py |
| wait_for_receivers on closed raises ClosedError | all | Close sender, attempt wait_for_receivers | test_wait_for_receivers_on_closed_raises | tests/test_channels.py |
| wait_for_senders on closed raises ClosedError | all | Close receiver, attempt wait_for_senders | test_wait_for_senders_on_closed_raises | tests/test_channels.py |

### 6. Error Semantics - DisconnectedError

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| Send with no receivers raises DisconnectedError | all | Create channel, close receiver, send | test_send_no_receivers_raises | tests/test_channels.py |
| Receive with no senders raises DisconnectedError | all | Create channel, close sender, receive | test_receive_no_senders_raises | tests/test_channels.py |
| Queue send raises when all receivers closed | queue | Send to queue, close all receivers, next send raises | test_queue_send_raises_when_receivers_gone | tests/test_channels.py |
| Broadcast send raises when all receivers closed | broadcast | Send to broadcast, close all receivers, next send raises | test_broadcast_send_raises_when_receivers_gone | tests/test_channels.py |
| Rendezvous send raises when receiver closes | rendezvous | Sender blocking, receiver closes before taking value | test_rendezvous_send_raises_on_disconnect | tests/test_channels.py |

### 7. Disconnect Safety (No Indefinite Hangs)

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| Blocked queue sender wakes on receiver close | queue | Sender blocked on full queue, close all receivers, sender raises | test_queue_blocked_sender_wakes_on_disconnect | tests/test_channels.py |
| Blocked queue receiver wakes on sender close | queue | Receiver blocked on empty queue, close all senders, receiver raises | test_queue_blocked_receiver_wakes_on_disconnect | tests/test_channels.py |
| Blocked broadcast sender wakes on receiver close | broadcast | Sender waiting for receiver, close all receivers, sender raises | test_broadcast_blocked_sender_wakes_on_disconnect | tests/test_channels.py |
| Blocked broadcast receiver wakes on sender close | broadcast | Receiver blocked, close all senders, receiver raises | test_broadcast_blocked_receiver_wakes_on_disconnect | tests/test_channels.py |
| Blocked rendezvous sender wakes on receiver close | rendezvous | Sender waiting for rendezvous, close all receivers, sender raises | test_rendezvous_blocked_sender_wakes_on_disconnect | tests/test_channels.py |
| Blocked rendezvous receiver wakes on sender close | rendezvous | Receiver waiting for rendezvous, close all senders, receiver raises | test_rendezvous_blocked_receiver_wakes_on_disconnect | tests/test_channels.py |

### 8. Iterator Semantics

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| async for receives all values | all | Send 3 values, iterate receiver, get all 3 | test_async_for_receives_all | tests/test_channels.py |
| async for stops when no senders | all | Iterate receiver, close all senders, iteration stops cleanly | test_async_for_stops_on_no_senders | tests/test_channels.py |
| async for works with multiple senders | all | Multiple senders send values, iterator receives all | test_async_for_multiple_senders | tests/test_channels.py |
| __anext__ converts DisconnectedError to StopAsyncIteration | all | Call __anext__ when no senders, verify StopAsyncIteration raised | test_anext_raises_stop_iteration_on_disconnect | tests/test_channels.py |

### 9. Copy Semantics (copy_on_send=True)

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| copy_on_send creates distinct objects in queue | queue | Send object with copy_on_send=True, verify different identity | test_queue_copy_on_send_distinct_identity | tests/test_channels.py |
| copy_on_send creates distinct objects in broadcast | broadcast | Send to 2 receivers with copy_on_send=True, verify 2 distinct copies | test_broadcast_copy_on_send_distinct_per_receiver | tests/test_channels.py |
| copy_on_send creates distinct object in rendezvous | rendezvous | Send with copy_on_send=True, verify receiver gets copy | test_rendezvous_copy_on_send_distinct | tests/test_channels.py |
| copy_on_send requires SupportsCopy protocol | all | Send object without .copy() method, raises TypeError | test_copy_on_send_requires_copy_protocol | tests/test_channels.py |
| copy_on_send=False shares same object | queue | Send with copy_on_send=False, verify same identity | test_no_copy_shares_identity | tests/test_channels.py |

### 10. Eventually Methods

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| send_eventually waits for receivers | all | Call send_eventually with no receivers, add receiver later, send succeeds | test_send_eventually_waits_for_receivers | tests/test_channels.py |
| receive_eventually waits for senders | all | Call receive_eventually with no senders, add sender later, receive succeeds | test_receive_eventually_waits_for_senders | tests/test_channels.py |
| send_eventually retries after DisconnectedError | all | send_eventually during disconnect, reconnect, completes | test_send_eventually_retries | tests/test_channels.py |
| receive_eventually retries after DisconnectedError | all | receive_eventually during disconnect, reconnect, completes | test_receive_eventually_retries | tests/test_channels.py |

### 11. Wait Methods

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| wait_for_receivers blocks until receiver connects | all | Call wait_for_receivers with no receivers, add one, unblocks | test_wait_for_receivers_blocks_until_connected | tests/test_channels.py |
| wait_for_senders blocks until sender connects | all | Call wait_for_senders with no senders, add one, unblocks | test_wait_for_senders_blocks_until_connected | tests/test_channels.py |
| wait_for_receivers returns immediately if receivers exist | all | With receiver connected, wait_for_receivers returns immediately | test_wait_for_receivers_immediate_if_exists | tests/test_channels.py |
| wait_for_senders returns immediately if senders exist | all | With sender connected, wait_for_senders returns immediately | test_wait_for_senders_immediate_if_exists | tests/test_channels.py |

### 12. Concurrency & Race Conditions

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| Concurrent sends to queue are serialized | queue | Multiple concurrent senders, all values received correctly | test_queue_concurrent_sends | tests/test_channels.py |
| Concurrent receives from queue work correctly | queue | Multiple concurrent receivers, all get distinct values | test_queue_concurrent_receives | tests/test_channels.py |
| Concurrent clone/close operations are safe | all | Concurrent clone and close on same endpoint, no corruption | test_concurrent_clone_close_safe | tests/test_channels.py |
| Broadcast receiver added during send gets value | broadcast | Add receiver while send is in progress, new receiver gets value | test_broadcast_receiver_added_during_send | tests/test_channels.py |
| Rendezvous handles concurrent send/receive | rendezvous | Multiple senders and receivers race, all complete correctly | test_rendezvous_concurrent_operations | tests/test_channels.py |

### 13. Task Cancellation

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| Cancelled send allows subsequent operations | all | Cancel blocked send task, verify next send works | test_cancelled_send_allows_subsequent_operations | tests/test_channels.py |
| Cancelled receive allows subsequent operations | all | Cancel blocked receive task, verify next receive works | test_cancelled_receive_allows_subsequent_operations | tests/test_channels.py |
| Cancelled eventually methods cleanup properly | all | Cancel send_eventually/receive_eventually, verify no leaked state | test_cancelled_eventually_methods_cleanup | tests/test_channels.py |

### 14. Resource Cleanup

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| Closed endpoint removes itself from channel | all | Close endpoint, verify channel's endpoint count decrements (inspects _open_senders/_open_receivers) | test_close_removes_from_channel | tests/test_channels.py |
| Channel cleanup when all endpoints closed | all | Close all endpoints, verify channel state is cleaned (inspects internal state) | test_channel_cleanup_on_all_close | tests/test_channels.py |
| Broadcast removes receiver queue on close | broadcast | Close receiver, verify its queue is removed from channel (inspects _queues dict) | test_broadcast_removes_queue_on_close | tests/test_channels.py |
| Rendezvous cleans waiting tasks on close | rendezvous | Close endpoint while tasks waiting, verify queue cleanup (inspects _senders/_receivers queues) | test_rendezvous_cleans_waiting_tasks | tests/test_channels.py |

### 15. Edge Cases

| Requirement | Modes | Scenario | Test Name | Location |
|-------------|-------|----------|-----------|----------|
| same_channel() returns True for same channel | all | Create 2 endpoints from same channel, verify same_channel() | test_same_channel_returns_true | tests/test_channels.py |
| same_channel() returns False for different channels | all | Create 2 separate channels, verify same_channel() is False | test_same_channel_returns_false | tests/test_channels.py |
| same_channel() returns False for closed endpoint | all | Close endpoint, call same_channel(), returns False | test_same_channel_false_on_closed | tests/test_channels.py |
| Endpoint repr shows closed state | all | Close endpoint, verify repr contains "closed" | test_endpoint_repr_closed | tests/test_channels.py |
| Endpoint repr shows channel binding | all | Create endpoint, verify repr shows channel | test_endpoint_repr_shows_channel | tests/test_channels.py |
| Cannot instantiate Sender directly | all | Call Sender(), raises TypeError | test_cannot_instantiate_sender_directly | tests/test_channels.py |
| Cannot instantiate Receiver directly | all | Call Receiver(), raises TypeError | test_cannot_instantiate_receiver_directly | tests/test_channels.py |

## Report

### Test Matrix Summary

Total test cases: **82**

| Category | Test Count | Notes |
|----------|------------|-------|
| 1. Channel Creation & Modes | 5 | Queue, broadcast, rendezvous validation |
| 2. Endpoint Lifecycle | 11 | Clone, derive (both directions), close operations |
| 3. Single Producer/Consumer Constraints | 4 | ValueError on constraint violations |
| 4. Send/Receive Operations | 9 | MPSC, SPMC, blocking behavior, rendezvous handshake |
| 5. Error Semantics - ClosedError | 6 | Operations on closed endpoints |
| 6. Error Semantics - DisconnectedError | 5 | Operations when opposite side disconnected |
| 7. Disconnect Safety (No Indefinite Hangs) | 6 | Wakeup on disconnect across all modes |
| 8. Iterator Semantics | 4 | async for termination, __anext__ conversion |
| 9. Copy Semantics (copy_on_send=True) | 5 | Distinct object identity verification |
| 10. Eventually Methods | 4 | Retry behavior on disconnect |
| 11. Wait Methods | 4 | Blocking until endpoints available |
| 12. Concurrency & Race Conditions | 5 | Concurrent operations, thread safety |
| 13. Task Cancellation | 3 | Graceful cancellation, state cleanup |
| 14. Resource Cleanup | 4 | Internal state inspection noted |
| 15. Edge Cases | 7 | same_channel(), repr, direct instantiation |
| **Total** | **82** | All modes covered (queue/broadcast/rendezvous) |

### Key Coverage Areas

**Exception Types Verified:**
- `ValueError`: Invalid capacity, clone/derive on closed, constraint violations
- `ClosedError`: Operations on closed endpoints (send, receive, wait_for_*, derive)
- `DisconnectedError`: Operations when opposite side unavailable
- `TypeError`: Invalid copy_on_send objects, direct endpoint instantiation
- `StopAsyncIteration`: Iterator termination (via __anext__)

**Design Decisions Tested:**
- Rendezvous handshake correctness (test_rendezvous_handshake_completion)
- Disconnect safety: 6 tests ensure no indefinite hangs
- Iterator semantics: clean termination on disconnect
- Copy-on-send: distinct object identity per receiver in broadcast mode
- Exactly-once delivery in queue mode (set equality verification)
- Task cancellation: state remains valid after cancel

**Test Execution:**
- Location: `tests/test_channels.py`
- Command: `make test`
- Framework: pytest with cocotb plugin
- Deterministic blocking verification via cocotb.fork() and Timer

### Review Updates Applied

From REVIEW-03:
- Added __anext__ test for DisconnectedError → StopAsyncIteration conversion (THREAD-01)
- Specified cocotb-based blocking verification strategy (THREAD-02)
- Added explicit exception types for all error cases (THREAD-03)
- Clarified queue SPMC as exactly-once delivery with set equality (THREAD-04)
- Added 3 task cancellation tests (THREAD-05)
- Marked resource cleanup tests with internal state inspection notes (THREAD-06)
- Used repo-root paths for all file references (THREAD-07)
- Split derive-on-closed into two tests (derive_receiver and derive_sender) (THREAD-03 Q-06/Q-07)

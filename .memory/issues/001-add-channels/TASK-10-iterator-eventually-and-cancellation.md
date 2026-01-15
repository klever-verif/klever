# TASK-10-iterator-eventually-and-cancellation — Iterator termination, eventually methods, cancellation robustness

## Brief
- Goal: Enforce iterator termination, `*_eventually` semantics, and cancellation robustness per the acceptance matrix.
- Effort: 4–6h
- Status: todo

## Details
- Steps:
  - Implement acceptance-matrix iterator tests (category "8. Iterator Semantics"):
    - `test_async_for_receives_all`
    - `test_async_for_stops_on_no_senders`
    - `test_async_for_multiple_senders`
    - `test_anext_raises_stop_iteration_on_disconnect`
  - Implement acceptance-matrix eventually-method tests (category "10. Eventually Methods"):
    - `test_send_eventually_waits_for_receivers`
    - `test_receive_eventually_waits_for_senders`
    - `test_send_eventually_retries`
    - `test_receive_eventually_retries`
  - Implement acceptance-matrix cancellation tests (category "13. Task Cancellation"):
    - `test_cancelled_send_allows_subsequent_operations`
    - `test_cancelled_receive_allows_subsequent_operations`
    - `test_cancelled_eventually_methods_cleanup`
  - Apply minimal fixes in `src/klever/channel.py` only if tests reveal busy loops, leaked waiters, or corrupted state after cancellation.
- Files: `TASK-03-acceptance-test-matrix.md`, `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -k 'async_for or anext or eventually or cancelled' -v`
- Risks / edge cases: Cancellation must not corrupt internal state; assertions should focus on "subsequent operations still work".

## Open Questions
- None.

## Definition of Done
- Iterator semantics match the acceptance matrix and stop cleanly on disconnect.
- Eventually-method and cancellation tests pass deterministically.

## Notes

## Report
- 

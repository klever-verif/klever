# TASK-12-concurrency-and-resource-cleanup — Concurrent operations + internal cleanup checks

## Brief
- Goal: Cover remaining concurrency/race and resource-cleanup requirements from the acceptance matrix.
- Effort: 4–6h
- Status: todo

## Details
- Steps:
  - Implement acceptance-matrix test for remaining concurrency/race coverage (category "12. Concurrency & Race Conditions"):
    - `test_concurrent_clone_close_safe`
  - Implement acceptance-matrix resource cleanup tests (category "14. Resource Cleanup"; internal inspection is explicitly allowed by the matrix scenarios):
    - `test_close_removes_from_channel`
    - `test_channel_cleanup_on_all_close`
    - `test_broadcast_removes_queue_on_close`
    - `test_rendezvous_cleans_waiting_tasks`
  - Apply minimal fixes in `src/klever/channel.py` only if tests reveal leaked waiters/queues or inconsistent cleanup.
- Files: `TASK-03-acceptance-test-matrix.md`, `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -k 'concurrent_ or cleanup or removes_' -v`
- Risks / edge cases: Cleanup tests are implementation-coupled; keep internal inspection minimal and scoped.

## Open Questions
- None.

## Definition of Done
- Concurrency and cleanup matrix items are covered and green.
- No persistent leaked waiters/queues after close in the covered scenarios.

## Notes

## Report
- 

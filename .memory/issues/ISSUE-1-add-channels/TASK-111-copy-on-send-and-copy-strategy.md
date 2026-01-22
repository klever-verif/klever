---
status: todo
---

# TASK-111-copy-on-send-and-copy-strategy — copy_on_send identity guarantees + non-copyable TypeError

## Brief
- Goal: Implement `copy_on_send=True` semantics across queue/broadcast/rendezvous with a unified copy strategy, as locked by the acceptance matrix.
- Effort: 3–5h

## Details
- Steps:
  - Implement acceptance-matrix tests for category "9. Copy Semantics (copy_on_send=True)":
    - `test_queue_copy_on_send_distinct_identity`
    - `test_broadcast_copy_on_send_distinct_per_receiver`
    - `test_rendezvous_copy_on_send_distinct`
    - `test_copy_on_send_requires_copy_protocol` (assert `TypeError`)
    - `test_no_copy_shares_identity`
  - Apply minimal fixes in `src/klever/channel.py` to ensure:
    - Distinct object identity is delivered where required.
    - Behavior for non-copyable values is explicit (`TypeError`).
    - The same strategy is used across modes.
- Files: `TASK-103-acceptance-test-matrix.md`, `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -k 'copy_on_send' -v`
- Risks / edge cases: Avoid "copy of a copy" in broadcast; each receiver must be derived from the original value as asserted by tests.

## Open Questions
- None.

## Definition of Done
- Copy-on-send tests pass across all modes.
- Unified copy strategy is used and behavior is explicit.

## Notes

## Report
-

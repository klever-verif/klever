# TASK-05-endpoints-lifecycle-and-constraints — Clone/derive/close + single producer/consumer + API edge cases

## Brief
- Goal: Lock down endpoint lifecycle and single-producer/consumer constraints via deterministic tests aligned with the acceptance matrix.
- Effort: 3–4h
- Status: todo

## Details
- Steps:
  - Implement acceptance-matrix tests for category "2. Endpoint Lifecycle":
    - `test_clone_sender`, `test_clone_receiver`
    - `test_clone_closed_endpoint_raises` (assert `ClosedError`)
    - `test_derive_receiver_from_sender`, `test_derive_sender_from_receiver`
    - `test_derive_receiver_from_closed_sender_raises` (assert `ClosedError`)
    - `test_derive_sender_from_closed_receiver_raises` (assert `ClosedError`)
    - `test_close_sender`, `test_close_receiver`, `test_close_idempotent`
    - `test_context_manager_closes`
  - Implement acceptance-matrix tests for category "3. Single Producer/Consumer Constraints" (assert `ValueError`):
    - `test_single_producer_prevents_clone`, `test_single_producer_prevents_derive`
    - `test_single_consumer_prevents_clone`, `test_single_consumer_prevents_derive`
  - Implement acceptance-matrix tests for category "15. Edge Cases":
    - `test_same_channel_returns_true`, `test_same_channel_returns_false`, `test_same_channel_false_on_closed`
    - `test_endpoint_repr_closed`, `test_endpoint_repr_shows_channel`
    - `test_cannot_instantiate_sender_directly`, `test_cannot_instantiate_receiver_directly`
  - Apply minimal production fixes in `src/klever/channel.py` only when tests expose a contract mismatch.
- Files: `TASK-03-acceptance-test-matrix.md`, `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -k 'clone or derive or close or single_ or same_channel or repr or instantiate' -v`
- Risks / edge cases: Keep exception types consistent with the acceptance matrix (notably `ValueError` vs `ClosedError`).

## Open Questions
- None.

## Definition of Done
- Lifecycle, constraints, and edge-case tests pass deterministically.
- No new public API is introduced.

## Notes

## Report
- 

# TASK-05-endpoints-lifecycle-and-constraints — Clone/derive/close + single producer/consumer + API edge cases

## Brief
- Goal: Lock down endpoint lifecycle and single-producer/consumer constraints via deterministic tests aligned with the acceptance matrix.
- Effort: 3–4h
- Status: done

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

NOTE-01: Added category 2/3/15 tests in `tests/test_channels.py`. Ran `uv run pytest tests/test_channels.py -k 'clone or derive or close or single_ or same_channel or repr or instantiate' -v`; all 22 selected cocotb tests passed.
NOTE-02: Added `PT011` ignore for `tests/**` in `pyproject.toml`, removed inline `# noqa: PT011` markers, and re-ran `uv run pytest tests/test_channels.py -k 'clone or derive or close or single_ or same_channel or repr or instantiate or queue_capacity_validation' -v` (23 tests passed).
NOTE-03: Kept `dut` argument to preserve cocotb plugin usage and added `ARG001` ignore for `tests/**` in `pyproject.toml`; re-ran `uv run pytest tests/test_channels.py -k 'clone or derive or close or single_ or same_channel or repr or instantiate or queue_capacity_validation' -v` (23 tests passed).
NOTE-04: Added `test_clone_closed_receiver_raises` and removed cross-type `same_channel` assertion per review feedback; verified `PT011`/`ARG001` only in `per-file-ignores`. Re-ran `uv run pytest tests/test_channels.py -k 'clone or derive or close or single_ or same_channel or repr or instantiate or queue_capacity_validation' -v` (24 tests passed).

## Report
- Added lifecycle/constraints/edge-case tests for endpoints, including closed receiver clone coverage.
- Kept ruff ignores for `PT011`/`ARG001` scoped to `tests/**` and removed cross-type `same_channel` assertion after review.
- Tests: `uv run pytest tests/test_channels.py -k 'clone or derive or close or single_ or same_channel or repr or instantiate or queue_capacity_validation' -v`.

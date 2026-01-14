# TASK-04-lifecycle-error-tests — Endpoint lifecycle and error semantics tests

## Brief
- Goal: Lock down endpoint lifecycle rules and error semantics via deterministic cocotb regression tests.
- Effort: 3–4h
- Status: todo

## Details
- Steps:
  - Add lifecycle tests:
    - `close()` is idempotent for `Sender` and `Receiver`.
    - `clone()` on a closed endpoint raises `ClosedError`.
    - `derive_sender()` / `derive_receiver()` on a closed endpoint raises `ClosedError`.
    - `only_single_producer=True` blocks creating additional `Sender` via clone/derive.
    - `only_single_consumer=True` blocks creating additional `Receiver` via clone/derive.
  - Add error semantics tests:
    - `send()` / `wait_for_receivers()` on a closed sender raises `ClosedError`.
    - `receive()` / `wait_for_senders()` on a closed receiver raises `ClosedError`.
    - `send()` with no receivers raises `DisconnectedError`.
    - `receive()` with no senders raises `DisconnectedError`.
  - Run under Verilator; avoid sleeps/timeouts where possible.
  - Apply minimal production fixes only if tests reveal clear defects.
- Files: `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -v`
- Risks / edge cases: Incorrectly relying on timing can create flaky deadlocks.

## Open Questions
- None.

## Definition of Done
- Tests cover lifecycle and error contracts deterministically.
- Tests pass consistently under Verilator.
- No new public API is introduced.

## Notes

## Report

---
status: todo
---

# TASK-109-error-and-wait-contracts — Closed/Disconnected semantics + wait_for_* contracts

## Brief
- Goal: Lock down exception semantics (`ClosedError`, `DisconnectedError`) and `wait_for_*` behavior across modes as per the acceptance matrix.
- Effort: 3–5h

## Details
- Steps:
  - Implement acceptance-matrix tests for category "5. Error Semantics - ClosedError":
    - `test_send_on_closed_sender_raises`
    - `test_receive_on_closed_receiver_raises`
    - `test_send_eventually_on_closed_raises`
    - `test_receive_eventually_on_closed_raises`
    - `test_wait_for_receivers_on_closed_raises`
    - `test_wait_for_senders_on_closed_raises`
  - Implement acceptance-matrix tests for category "6. Error Semantics - DisconnectedError":
    - `test_send_no_receivers_raises`
    - `test_receive_no_senders_raises`
  - Implement acceptance-matrix tests for category "11. Wait Methods":
    - `test_wait_for_receivers_blocks_until_connected`
    - `test_wait_for_senders_blocks_until_connected`
    - `test_wait_for_receivers_immediate_if_exists`
    - `test_wait_for_senders_immediate_if_exists`
  - Apply minimal production fixes so waits are event-driven (no busy loops) and unblock on connect/disconnect deterministically.
- Files: `TASK-103-acceptance-test-matrix.md`, `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -k 'wait_for_ or closed or disconnected' -v`
- Risks / edge cases: Wait methods must not hang indefinitely; timeouts should only act as a bug detector.

## Open Questions
- None.

## Definition of Done
- Error and wait contracts match acceptance matrix exception types.
- Tests are deterministic and stable under Verilator.

## Notes

## Report
-

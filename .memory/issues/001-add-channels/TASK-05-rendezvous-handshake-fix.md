# TASK-05-rendezvous-handshake-fix — Rendezvous handshake correctness (tests-first + fix)

## Brief
- Goal: Ensure rendezvous correctness: `Sender.send()` completes only after the receiver has taken the value.
- Effort: 3–4h
- Status: todo

## Details
- Steps:
  - Add failing rendezvous tests:
    - Ack-after-take: `send()` does not complete until `receive()` has taken the value.
    - Receive-blocks: `receive()` blocks until a sender provides a value.
    - No-stale-participants: completed waiters do not participate in future handoffs.
  - Fix `_RendezvousChannel` in `src/klever/channel.py` to satisfy tests:
    - Sender waits for receiver “take” acknowledgement.
    - Receiver waits for value availability.
    - Ensure proper registration + cleanup of waiters/triggers.
    - Keep fairness/FIFO out of scope.
- Files: `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -v`
- Risks / edge cases: Cocotb trigger races can cause hangs; tests must be deterministic.

## Open Questions
- None.

## Definition of Done
- Rendezvous tests pass deterministically.
- `send()` completion implies the receiver took the value.
- No deadlocks/hangs in rendezvous scenarios.

## Notes

## Report

# TASK-08-copy-on-send-semantics — `copy_on_send` distinct object per receiver

## Brief
- Goal: Guarantee `copy_on_send=True` delivers a distinct object per receiver, using a single shared copy strategy across all channel modes.
- Effort: 3–4h
- Status: todo

## Details
- Steps:
  - Add tests:
    - Broadcast + `copy_on_send=True`: two receivers must receive values where `v1 is not v2`.
    - Ensure broadcast does not copy “copy of copy” (each receiver gets a fresh copy from the original item).
  - Implement a unified copy strategy used by queue/broadcast/rendezvous:
    - Support `value.copy()` (existing protocol).
    - Support Python `copy`-module semantics (e.g. `copy.copy` / `copy.deepcopy` behavior).
  - Decide behavior for non-copyable items (raise a clear error vs identity fallback) based on existing patterns, and test it.
- Files: `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest tests/test_channels.py -v`
- Risks / edge cases: Copy semantics can differ between shallow/deep; keep the contract explicit and tested.

## Open Questions
- For non-copyable values, should `copy_on_send=True` raise or fall back to identity?

## Definition of Done
- Tests prove distinct object identity per receiver when `copy_on_send=True`.
- Copy behavior is implemented via a single shared strategy.
- All existing channel tests remain green.

## Notes

## Report

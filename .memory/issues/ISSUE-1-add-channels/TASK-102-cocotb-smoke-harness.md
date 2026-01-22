---
status: done
---

# TASK-102-cocotb-smoke-harness — cocotb + Verilator smoke harness

## Brief
- Goal: Add a minimal cocotb+Verilator pytest harness and a deterministic channel smoke test.
- Effort: 3–4h

## Details
- Steps:
  - Confirm cocotb cannot run without an HDL simulator context.
  - Add a minimal SystemVerilog “dummy top” suitable for Verilator compilation.
  - Integrate cocotb execution into pytest (runner/plugin) so tests run via the normal repo test entrypoint.
  - Add deterministic smoke test(s) for queue mode using `klever.channel`.
- Files: `tests/hdl/dummy_top.sv`, `tests/conftest.py`, `tests/test_channels.py`, `src/klever/channel.py`
- Commands: `make test`, `pytest --collect-only`, `pytest tests/test_channels.py -v`
- Risks / edge cases:
  - cocotb runner/plugin integration can vary across cocotb versions.
  - Avoid sleeps and timing-based assertions to keep tests deterministic.

## Open Questions
- None.

## Definition of Done
- A cocotb+Verilator-backed test run is integrated with pytest.
- At least one deterministic smoke test passes and exercises real `send()`/`receive()` behavior.

## Notes

### NOTE-01
Implementation notes (historical):
- cocotb requires HDL sources + a simulator; no pure-Python mode.
- Verilator can compile an essentially empty top; no functional logic required.
- The harness was implemented using pytest integration so tests run via `make test`.

## Report

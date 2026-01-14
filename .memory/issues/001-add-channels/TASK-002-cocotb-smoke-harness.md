# TASK-002 — cocotb + Verilator smoke harness

## Goal
Create minimal runnable cocotb test environment (using Verilator) and add a deterministic smoke test for channels.

## Context
This corresponds to Phase 1 in [](/.memory/PLAN.md).

**Architecture rationale:** cocotb channels (`klever.channel`) require execution within cocotb's simulator context (similar to how asyncio requires an event loop). Since cocotb has no mock simulator, we must run a real simulator (Verilator) with a dummy HDL design to provide the execution environment for testing the pure-Python channel API.

## Scope
- Research minimal cocotb configuration (attempt to avoid HDL if possible).
- If HDL is required: create minimal SystemVerilog dummy top for Verilator.
- Integrate `cocotb.runner` into pytest as fixture (following https://docs.cocotb.org/en/development/runner.html).
- Add one smoke test: work queue (capacity=1).
- **Experimental:** Find the minimal working approach through hands-on testing.

## Detailed Work

### 1. Research minimal cocotb setup
- Check if cocotb supports running without HDL simulation.
- If not, proceed to create dummy HDL top.

### 2. Create minimal HDL top (if needed)
- **Language:** SystemVerilog
- **Content:** Empty module or minimal clock/reset (whatever Verilator needs to compile)
- **Purpose:** Provide compilation target for Verilator; no functional logic required
- **Location:** TBD (e.g., `tests/hdl/dummy_top.sv` or similar)
- **Module name:** TBD (e.g., `tb_top` or `dummy`)

### 3. Integrate cocotb.runner with pytest
- Create pytest fixture using `cocotb.runner` API.
- Place test in `tests/` directory (integrated with existing pytest structure).
- Test file name: `test_channels.py` (or similar pytest convention).
- Import `klever.channel` from `src/klever/channel.py`.

### 4. Implement work queue smoke test
- Create channel: `tx, rx = create(capacity=1)` (note: `create()` returns `(tx, rx)`)
- Send value: `await tx.send(123)`
- Receive value: `value = await rx.receive()`
- Assert: `value == 123`
- **Constraint:** No sleeps/delays; must be deterministic

### 5. Test invocation
- Smoke tests run via standard `make test` command.
- Integration through pytest (cocotb tests discovered by pytest automatically).

## Technical Constraints
- **HDL:** SystemVerilog (if required)
- **Simulator:** Verilator (>=5.0 available in devcontainer)
- **cocotb:** Already in dependencies (`cocotb>=2.0.1` in pyproject.toml)
- **Test framework:** pytest + cocotb.runner integration
- **Location:** `tests/` (no separate cocotb directory)

## Definition of Done (DoD)
- Smoke test runs via `make test` (integrated with pytest).
- Smoke test passes deterministically (no sleeps/timing tricks).
- Test imports `klever.channel` and exercises real send/receive in cocotb context.
- Minimal HDL top compiles under Verilator (if HDL is needed).
- Documentation captures the chosen minimal approach for future reference.

## Estimated Effort
~3–4 hours (includes research/experimentation time).

## Dependencies
- TASK-001 (baseline commands) recommended but not required (already done).
- Verilator available in devcontainer (available).

## Open Questions (to resolve during implementation)
- Can cocotb run without HDL simulation? (Try first)
- If HDL needed: does Verilator require clock/reset or can module be completely empty?
- Optimal cocotb.runner fixture structure for this project.

## Implementation Notes (Completed)

### Answers to Open Questions
1. **Can cocotb run without HDL simulation?** NO - cocotb requires HDL sources and a simulator. It cannot run in a pure-Python mode.
2. **Does Verilator require clock/reset?** NO - Verilator accepts a completely empty module with just a single input port (clk). No logic or actual clock generation is needed.
3. **Optimal runner structure:** Use `test_dir` parameter to set working directory to `tests/`, allowing cocotb to import test modules from that directory.

### Chosen Minimal Approach (FINAL - Using cocotb pytest plugin)
- **Cocotb Version:** 2.1.0.dev (development) - required for pytest plugin support
- **HDL Module:** `tests/hdl/dummy_top.sv` - Minimal SystemVerilog module with single clock input, no logic
- **Test Structure (Using cocotb pytest plugin):**
  - `tests/conftest.py` - Enables cocotb pytest plugin + defines `dummy_top` fixture (builds HDL)
  - `tests/test_channels.py` - Contains:
    - **ONE** pytest runner function with `@pytest.mark.cocotb_runner` marker
    - Multiple async test functions (NO decorators needed - auto-discovered by plugin)
- **Key Configuration:**
  - Plugin enabled via `pytest_plugins = ("cocotb_tools.pytest.plugin",)` in conftest
  - HDL fixture uses `hdl.sources.append()` and `hdl.build()`
  - Runner uses `dummy_top.test_dir = Path(__file__).resolve().parent` to find test module
  - Build artifacts go to `sim_build/tests/test_channels/test_channel_runner/` directory
- **Integration:** Tests discovered by pytest automatically via plugin, run via `make test`

### File Structure Created (FINAL)
```
tests/
├── hdl/
│   ├── dummy_top.sv          # Minimal SV module for Verilator
│   └── README.md             # Explains purpose of HDL files
├── conftest.py               # Enables plugin + dummy_top HDL fixture
└── test_channels.py          # 1 pytest runner + N async cocotb tests
```

### Test Results
✓ Work queue smoke test passes deterministically (capacity=1)
✓ Multiple items test passes (capacity=2, multiple send/receive)
✓ Integrated with pytest (discovered automatically via plugin)
✓ Runs via `make test` command
✓ No sleeps/timing tricks - pure deterministic tests
✓ Tests real send/receive in cocotb context
✓ HDL builds once per session, reused by all tests (efficient)
✓ Detailed test summary via `--cocotb-summary` (configured in pyproject.toml)

### Viewing Test Results
```bash
# Standard run - shows summary automatically (configured in pyproject.toml)
make test

# Output shows:
# - 3 passed (1 pytest runner + 2 cocotb tests)
# - Cocotb test summary table with individual test results:
#   ** tests/test_channels.py::test_channel_runner::test_work_queue_smoke  PASS **
#   ** tests/test_channels.py::test_channel_runner::test_work_queue_multiple_items  PASS **

# Discover tests without running
pytest --collect-only
# Shows hierarchy: Runner -> Testbench -> Tests

# Verbose mode with live output
pytest tests/test_channels.py -s -v
```

### Architecture Benefits (FINAL - With cocotb pytest plugin)
- **Zero duplication:** Write async test function once, plugin handles everything
- **No decorators needed:** Async functions auto-discovered as cocotb tests (must start with `test_` and have `dut` arg)
- **Pytest integration:** Full pytest features (fixtures, marks, parametrize, etc.) available
- **Test discovery:** `pytest --collect-only` shows full hierarchy (Runner -> Testbench -> Tests)
- **Easy to extend:** Just add new `async def test_xxx(dut)` function - that's it!
- **Efficient:** HDL compiled once via fixture, reused by all tests
- **Clean:** One file, one runner, N tests

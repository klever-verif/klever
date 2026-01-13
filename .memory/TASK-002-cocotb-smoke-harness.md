# TASK-002 — cocotb + Verilator smoke harness

## Goal
Create minimal runnable cocotb test environment (using Verilator) and add a deterministic smoke test for channels.

## Context
This corresponds to Phase 1 in `.memory/PLAN.md`.

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

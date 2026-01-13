# HDL Sources for cocotb Tests

This directory contains minimal HDL modules required for cocotb smoke tests.

## Purpose

cocotb requires a simulator environment to run, even when testing pure-Python code like `klever.channel`. These HDL modules exist solely to provide a compilation target for the simulator (Verilator), creating the execution environment needed by cocotb.

## Files

- `dummy_top.sv`: Minimal SystemVerilog module with no functional logic
  - Single clock input port (required by Verilator)
  - No actual clock generation or logic required
  - Serves as top-level module for simulator

## Usage

These HDL files are automatically used by the cocotb.runner integration in `tests/test_channels.py`. You don't need to interact with them directly - just run `make test`.

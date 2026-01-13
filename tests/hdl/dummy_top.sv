// Minimal SystemVerilog module for cocotb smoke tests
// Purpose: Provide compilation target for Verilator to create cocotb execution environment
// No functional logic required - cocotb channels are tested in pure Python

`timescale 1ns/1ps

module dummy_top (
    input logic clk
);
    // Empty module - exists only to satisfy simulator requirements
endmodule

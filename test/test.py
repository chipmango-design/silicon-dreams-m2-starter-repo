"""Module 1 nominal smoke test - re-included in Module 2 as a regression.

This test is run by `make smoke` and must continue to pass for the
entire Module 2 sprint. If any of your bug fixes regress nominal
behaviour, this will go red before the fault matrix even runs.

The body of this file is deliberately small - the real verification
work in Module 2 happens in `fault_injection/`. We only need enough
here to prove that `rst_n` releases cleanly and the FSM reaches IDLE.
"""

from __future__ import annotations

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


@cocotb.test()
async def nominal_smoke(dut):
    """DUT comes out of reset in IDLE at floor 0."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    for _ in range(4):
        await RisingEdge(dut.clk)

    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Bits [6:4] of uo_out are the FSM state (IDLE == 0).
    state = (int(dut.uo_out.value) >> 4) & 0b111
    assert state == 0, f"expected IDLE (state=0) after reset, got {state}"

    # Bits [3:0] of uo_out are the current-floor 7-seg value.
    floor = int(dut.uo_out.value) & 0b1111
    assert floor == 0, f"expected current_floor=0 after reset, got {floor}"

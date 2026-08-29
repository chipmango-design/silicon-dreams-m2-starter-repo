"""Floor B2 - the broken reset.

Bug under test
--------------
Module 1 RTL declares the FSM block as::

    always @(posedge clk or posedge rst_n) begin
        if (rst_n) begin
            state <= IDLE;
        end else ...
    end

The sensitivity list and the polarity check are both wrong. A correctly
fixed design uses::

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
        end else ...
    end

Three-state verification
------------------------
This test must:

1. FAIL on the starter (broken) RTL - reset pulse leaves the DUT wedged.
2. PASS on the fixed RTL - recovers within 2 cycles of rst_n going high.
3. Not regress the nominal smoke test - run it inline to be sure.

Grading
-------
150 XP, all-or-nothing. A partial fix (correct sensitivity list but wrong
polarity check, or vice versa) will still fail this test.
"""

from __future__ import annotations

import cocotb
from cocotb.triggers import RisingEdge

from harness.faults import StuckAtFault, BurstFault
from harness.scoreboard import Scoreboard

from . import conftest as cf


# -----------------------------------------------------------------------------
# Test 1 - nominal behaviour still works (regression guard)
# -----------------------------------------------------------------------------


@cocotb.test()
async def floor_b2_nominal_still_passes(dut):
    """Sanity: with a clean reset, the DUT comes out of reset in IDLE.

    If this fails, you broke the nominal path while fixing the bug.
    """
    cf.start_clock(dut)
    await cf.nominal_reset(dut)

    # After reset, state should be IDLE and current_floor should be 0.
    state = cf.read_state(dut)
    floor = cf.read_current_floor(dut)

    assert state == cf.STATE_IDLE, (
        f"expected IDLE ({cf.STATE_IDLE}) after reset, got {state}"
    )
    assert floor == 0, f"expected current_floor 0 after reset, got {floor}"


# -----------------------------------------------------------------------------
# Test 2 - minimum-width reset pulse
# -----------------------------------------------------------------------------


@cocotb.test()
async def floor_b2_minimum_pulse_recovers(dut):
    """A 1-cycle active-low reset pulse must return the DUT to IDLE.

    This is the test that fails the broken RTL - `posedge rst_n` never
    fires on a negedge pulse, so the DUT stays wherever it was.
    """
    sb = Scoreboard.load_or_new()

    cf.start_clock(dut)
    await cf.nominal_reset(dut)

    # Drive the DUT into a non-IDLE state (request floor 5).
    cf.drive_request(dut, 5)
    await RisingEdge(dut.clk)
    cf.clear_request(dut)
    # Let it transition out of IDLE.
    for _ in range(3):
        await RisingEdge(dut.clk)
    pre_state = cf.read_state(dut)
    assert pre_state != cf.STATE_IDLE, (
        "test precondition failed: DUT never left IDLE after a request"
    )

    # Minimum-width reset pulse: rst_n low for 1 cycle, then high.
    pulse = BurstFault(signal_name="rst_n", low_cycles=1, high_cycles=5)
    await pulse.run(dut)

    post_state = cf.read_state(dut)
    passed = post_state == cf.STATE_IDLE
    sb.record(
        "floor_b2_reset",
        passed=passed,
        notes=(
            f"pre_state={pre_state} post_state={post_state} "
            f"(expected IDLE={cf.STATE_IDLE})"
        ),
    )
    sb.save()

    assert passed, (
        f"after 1-cycle reset pulse, expected state IDLE ({cf.STATE_IDLE}), "
        f"got {post_state}. This is Floor B2: the reset polarity bug."
    )


# -----------------------------------------------------------------------------
# Test 3 - stuck-at reset
# -----------------------------------------------------------------------------


@cocotb.test()
async def floor_b2_stuck_at_reset_holds_idle(dut):
    """While rst_n is held low, the DUT must stay in IDLE.

    On the broken RTL, the FSM actually advances while rst_n is low and
    only resets when rst_n goes high - inverted behaviour. On the fixed
    RTL, the state register is held in IDLE for the entire fault window.
    """
    cf.start_clock(dut)
    await cf.nominal_reset(dut)

    # Request floor 7 so we have somewhere to go if the reset is broken.
    cf.drive_request(dut, 7)
    await RisingEdge(dut.clk)
    cf.clear_request(dut)

    # Hold rst_n low for 10 cycles. The FSM must stay in IDLE the whole
    # time. We sample state at cycles 1, 5, 9.
    stuck = StuckAtFault(signal_name="rst_n", value=0, duration_cycles=10)
    # Fire the fault in the background so we can observe during it.
    fault_task = cocotb.start_soon(stuck.run(dut))

    observations = []
    for cycle in range(10):
        await RisingEdge(dut.clk)
        if cycle in (1, 5, 9):
            observations.append((cycle, cf.read_state(dut)))

    await fault_task

    bad = [(c, s) for (c, s) in observations if s != cf.STATE_IDLE]
    assert not bad, (
        f"during stuck-at-low reset, expected IDLE at all sampled cycles, "
        f"but observed {bad}. This is Floor B2: the reset polarity bug."
    )

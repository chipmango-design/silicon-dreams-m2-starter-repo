"""Floor 1 - the corrupted input.

Bug under test
--------------
Module 1 RTL does not validate `requested_floor`. If a user (or a
corrupted ui_in line) drives `requested_floor` to 9, 10, ... 15, the
FSM happily transitions to MOVING and the current_floor counter walks
off the end of the valid range (0..8). The 7-segment decoder then
displays garbage and - worse - `uo_out[3:0]` reads whatever bits fall
out of the adder, making the error invisible.

The fix is a two-part change:

1. Gate the request strobe on `requested_floor <= 8`.
2. Assert `uio_out[7]` (the error LED) for exactly one cycle when an
   out-of-range request is received.

Three-state verification
------------------------
This test must:

1. FAIL on the starter RTL - request for floor 10 is accepted.
2. PASS on the fixed RTL - request for floor 10 is ignored and the
   error LED pulses for 1 cycle.
3. Not regress requests for floors 0..8 (they must still be accepted).

Grading
-------
150 XP. Includes a small subscore for asserting the error LED - if the
request is correctly ignored but the LED never asserts, the test marks
half-credit (75 XP) via `xp_override`.
"""

from __future__ import annotations

import cocotb
from cocotb.triggers import RisingEdge

from harness.scoreboard import Scoreboard

from . import conftest as cf


@cocotb.test()
async def floor_1_valid_requests_still_accepted(dut):
    """Regression: requests for floors 0..8 must still move the lift."""
    cf.start_clock(dut)
    await cf.nominal_reset(dut)

    for floor in (0, 1, 4, 8):
        await cf.nominal_reset(dut)
        cf.drive_request(dut, floor)
        await RisingEdge(dut.clk)
        cf.clear_request(dut)

        # Give the FSM up to 20 cycles to leave IDLE.
        left_idle = False
        for _ in range(20):
            await RisingEdge(dut.clk)
            if cf.read_state(dut) != cf.STATE_IDLE:
                left_idle = True
                break

        if floor == 0:
            # A request for floor 0 while already at floor 0 may stay
            # in IDLE (door opens and closes without moving). Accept
            # either behaviour.
            continue

        assert left_idle, (
            f"request for valid floor {floor} did not transition FSM "
            f"out of IDLE - this would regress nominal M1 behaviour."
        )


@cocotb.test()
async def floor_1_invalid_request_is_ignored(dut):
    """Request for floor 10 (>8) must be ignored and error LED pulses."""
    sb = Scoreboard.load_or_new()

    cf.start_clock(dut)
    await cf.nominal_reset(dut)

    # Drive an invalid request: floor 10.
    cf.drive_request(dut, 10)
    await RisingEdge(dut.clk)

    # Observe: error LED should be high on this cycle on fixed RTL.
    error_during = cf.read_error_led(dut)

    cf.clear_request(dut)
    await RisingEdge(dut.clk)
    error_after = cf.read_error_led(dut)

    # Wait 10 cycles and check the FSM stayed in IDLE.
    stayed_idle = True
    for _ in range(10):
        await RisingEdge(dut.clk)
        if cf.read_state(dut) != cf.STATE_IDLE:
            stayed_idle = False
            break

    # Scoring:
    #   both stayed_idle and error_during -> full credit
    #   stayed_idle only                  -> half credit
    #   neither                           -> fail
    if stayed_idle and error_during:
        sb.record("floor_1_input", passed=True, notes="ignored + LED pulse")
    elif stayed_idle:
        sb.record(
            "floor_1_input",
            passed=True,
            notes="ignored but no LED pulse (partial credit)",
            xp_override=75,
        )
    else:
        sb.record(
            "floor_1_input",
            passed=False,
            notes=(
                f"invalid request was ACCEPTED. "
                f"error_during={error_during} error_after={error_after}"
            ),
        )
    sb.save()

    assert stayed_idle, (
        "invalid request (floor 10) was accepted - FSM left IDLE. "
        "This is Floor 1: the missing input range-clamp."
    )


@cocotb.test()
async def floor_1_error_led_pulse_width(dut):
    """The error LED must assert for exactly one cycle, not latch."""
    cf.start_clock(dut)
    await cf.nominal_reset(dut)

    cf.drive_request(dut, 12)
    await RisingEdge(dut.clk)
    cf.clear_request(dut)

    # The LED should be high on this cycle (we sampled mid-request).
    # We now wait 5 cycles and count how many cycles it stayed high.
    samples = [cf.read_error_led(dut)]
    for _ in range(5):
        await RisingEdge(dut.clk)
        samples.append(cf.read_error_led(dut))

    high_count = sum(samples)
    assert high_count <= 2, (
        f"error LED stayed high for {high_count} cycles - it must pulse, "
        f"not latch. Samples: {samples}."
    )

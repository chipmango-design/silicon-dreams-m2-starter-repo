"""Floor 5 - the state encoding war.

Bug under test
--------------
Module 1 uses a 2-bit dense binary encoding for the FSM state::

    localparam IDLE       = 2'b00;
    localparam MOVING     = 2'b01;
    localparam ARRIVED    = 2'b10;
    localparam DOOR_OPEN  = 2'b11;

A single-bit flip on the state register can silently transition the FSM
to any other legal state - there is no illegal-state detection. The fix
is a 4-bit one-hot encoding with a `default` branch in the state
transition case that forces the FSM back to IDLE::

    localparam IDLE       = 4'b0001;
    localparam MOVING     = 4'b0010;
    localparam ARRIVED    = 4'b0100;
    localparam DOOR_OPEN  = 4'b1000;

    case (state)
        IDLE:      next_state = ...;
        MOVING:    next_state = ...;
        ARRIVED:   next_state = ...;
        DOOR_OPEN: next_state = ...;
        default:   next_state = IDLE;  // SEU trap
    endcase

Three-state verification
------------------------
This test must:

1. FAIL on the 2-bit dense encoding - a flip corrupts state silently.
2. PASS on the 4-bit one-hot encoding - any illegal state returns to
   IDLE within 2 cycles.

Grading
-------
200 XP. The highest-weighted floor because SEU resilience is the single
most-tested property in real silicon.
"""

from __future__ import annotations

import cocotb
from cocotb.triggers import RisingEdge

from harness.faults import SEUFault
from harness.scoreboard import Scoreboard

from . import conftest as cf


# Path to the state register inside the top module. If your Module 1 uses
# a different hierarchy, update this path. The harness walks the dotted
# path from `dut` downward.
STATE_REG_PATH = "tt_um_example.fsm.state"

# Recovery window - after an SEU, how many cycles do we allow before the
# FSM must be back in IDLE?
RECOVERY_CYCLES = 2


@cocotb.test()
async def floor_5_seu_from_idle(dut):
    """SEU on state bit 0 while in IDLE - must recover to IDLE."""
    sb = Scoreboard.load_or_new()

    cf.start_clock(dut)
    await cf.nominal_reset(dut)

    assert cf.read_state(dut) == cf.STATE_IDLE

    # Fire SEU on bit 0 immediately.
    seu = SEUFault(register_path=STATE_REG_PATH, bit_index=0)
    await seu.run(dut)

    # Wait the recovery window.
    for _ in range(RECOVERY_CYCLES):
        await RisingEdge(dut.clk)

    post_state = cf.read_state(dut)
    passed = post_state == cf.STATE_IDLE
    sb.record(
        "floor_5_seu",
        passed=passed,
        notes=f"SEU bit 0 from IDLE; post_state={post_state}",
    )
    sb.save()

    assert passed, (
        f"after SEU on state[0] from IDLE, expected recovery to IDLE "
        f"within {RECOVERY_CYCLES} cycles; got state={post_state}. "
        f"This is Floor 5: the state encoding bug."
    )


@cocotb.test()
async def floor_5_seu_sweep_all_bits_all_states(dut):
    """SEU on every bit from every legal state - all must recover.

    The fixed one-hot encoding has 4 bits; the broken dense encoding has
    2 bits. We iterate 0..3 and skip bit indices outside the actual
    width at runtime.
    """
    cf.start_clock(dut)
    await cf.nominal_reset(dut)

    state_handle = dut
    for attr in STATE_REG_PATH.split("."):
        state_handle = getattr(state_handle, attr)
    width = len(state_handle)

    failures = []

    for from_state in (cf.STATE_IDLE, cf.STATE_MOVING, cf.STATE_ARRIVED):
        # Drive the DUT into `from_state` (skip IDLE since we're already
        # there; skip DOOR_OPEN because reaching it requires arrival).
        await cf.nominal_reset(dut)
        if from_state != cf.STATE_IDLE:
            cf.drive_request(dut, 3)
            await RisingEdge(dut.clk)
            cf.clear_request(dut)
            # Wait a bounded number of cycles for the target state.
            for _ in range(20):
                await RisingEdge(dut.clk)
                if cf.read_state(dut) == from_state:
                    break

        for bit_index in range(width):
            seu = SEUFault(register_path=STATE_REG_PATH, bit_index=bit_index)
            await seu.run(dut)
            for _ in range(RECOVERY_CYCLES):
                await RisingEdge(dut.clk)
            post = cf.read_state(dut)
            legal = post in (
                cf.STATE_IDLE,
                cf.STATE_MOVING,
                cf.STATE_ARRIVED,
                cf.STATE_DOOR_OPEN,
            )
            if not legal:
                failures.append(
                    f"from_state={from_state} bit={bit_index} "
                    f"post={post} (illegal)"
                )

    assert not failures, (
        "SEU sweep found illegal post-SEU states (no recovery):\n  "
        + "\n  ".join(failures)
        + "\nThis is Floor 5: the 2-bit dense encoding has no default trap."
    )

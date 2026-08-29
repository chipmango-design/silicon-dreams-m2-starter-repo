"""cocotb + pytest fixtures shared across all floor tests.

Provides:

    CLK_PERIOD_NS   -- standard 100 MHz clock
    start_clock(dut) -- spins up the clock coroutine
    nominal_reset(dut) -- drives a clean, correct reset sequence
    pinout constants -- ui_in bit positions copied from Module 1

The fixtures are plain async functions, not pytest fixtures, because
cocotb tests do not run under pytest - they run under the cocotb test
runner. We keep the name `conftest.py` only because editors and ruff are
happier with it.
"""

from __future__ import annotations

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# -----------------------------------------------------------------------------
# Clock and timing
# -----------------------------------------------------------------------------

CLK_PERIOD_NS = 10  # 100 MHz
RESET_CYCLES = 4    # how long nominal_reset asserts rst_n low


def start_clock(dut) -> None:
    """Start a free-running 100 MHz clock on `dut.clk`."""
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD_NS, units="ns").start())


# -----------------------------------------------------------------------------
# Reset
# -----------------------------------------------------------------------------


async def nominal_reset(dut) -> None:
    """Drive a clean active-low reset pulse.

    After this returns, the DUT is in IDLE on Floor 0 with no pending
    requests. Tests that want to start from a known-good state call this
    before injecting any faults.
    """
    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    for _ in range(RESET_CYCLES):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


# -----------------------------------------------------------------------------
# Pinout - imported from Module 1 tt_um contract
# -----------------------------------------------------------------------------

# ui_in[0]           -- request strobe (one-cycle high asserts a request)
# ui_in[3:1]         -- requested_floor (0..7, extended to 0..8 in M2)
# ui_in[7:4]         -- reserved
#
# uio_in[0]          -- external fault-injection enable (unused in nominal)
# uio_in[7:1]        -- reserved
#
# uo_out[3:0]        -- 7-segment current-floor display (BCD)
# uo_out[6:4]        -- FSM state (IDLE, MOVING, ARRIVED, DOOR_OPEN)
# uo_out[7]          -- door_open indicator LED
#
# uio_out[6:0]       -- reserved for M3
# uio_out[7]         -- error LED (asserts on invalid requested_floor in M2)
#
# uio_oe[7]          -- must be 1 so uio_out[7] drives the error LED

REQ_STROBE_BIT = 0
REQ_FLOOR_LSB = 1
REQ_FLOOR_MSB = 3  # 3 bits in M1, extended to 4 bits of space in M2

CURRENT_FLOOR_LSB = 0
CURRENT_FLOOR_MSB = 3
STATE_LSB = 4
STATE_MSB = 6
DOOR_OPEN_BIT = 7
ERROR_LED_BIT = 7  # on uio_out

# FSM state encoding (M1 uses 2-bit dense; M2 fix uses 4-bit one-hot)
STATE_IDLE = 0
STATE_MOVING = 1
STATE_ARRIVED = 2
STATE_DOOR_OPEN = 3


def drive_request(dut, floor: int) -> None:
    """Set ui_in to assert a one-cycle request for `floor`.

    Caller is responsible for clearing ui_in on the next cycle.
    """
    if not 0 <= floor <= 15:
        raise ValueError(f"floor {floor} does not fit in 4 bits")
    dut.ui_in.value = (floor << REQ_FLOOR_LSB) | (1 << REQ_STROBE_BIT)


def clear_request(dut) -> None:
    dut.ui_in.value = 0


# -----------------------------------------------------------------------------
# Convenience observers
# -----------------------------------------------------------------------------


def read_state(dut) -> int:
    """Extract the FSM state field from uo_out."""
    raw = int(dut.uo_out.value)
    mask = (1 << (STATE_MSB - STATE_LSB + 1)) - 1
    return (raw >> STATE_LSB) & mask


def read_current_floor(dut) -> int:
    raw = int(dut.uo_out.value)
    mask = (1 << (CURRENT_FLOOR_MSB - CURRENT_FLOOR_LSB + 1)) - 1
    return (raw >> CURRENT_FLOOR_LSB) & mask


def read_error_led(dut) -> int:
    return (int(dut.uio_out.value) >> ERROR_LED_BIT) & 1

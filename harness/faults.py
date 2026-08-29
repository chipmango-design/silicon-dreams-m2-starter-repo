"""Layer 2 - composable fault-type coroutines.

Each fault class is a thin wrapper around the primitives that gives a
named, declarative way to describe what you are doing to the DUT. The
three fault types cover the four Module 2 floors:

    StuckAtFault    -- Floor B2 (sustained reset polarity override)
    BurstFault      -- Floor B2 (pulse with explicit width and gap)
    SEUFault        -- Floor 5   (single-event upset on FSM state)

Floor 1 is a directed-stimulus test (no fault injection - just bad input)
and the Silent Floor is a static-analysis test (Yosys area report), so
they do not need their own fault class.

All faults expose an `async def run(self, dut)` coroutine. Tests spawn
them via `cocotb.start_soon(fault.run(dut))` and await completion.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

import cocotb
from cocotb.triggers import RisingEdge

from .primitives import (
    force_signal,
    release_signal,
    deposit_bit,
    wait_cycles,
)

log = logging.getLogger("harness.faults")


# -----------------------------------------------------------------------------
# StuckAtFault
# -----------------------------------------------------------------------------


@dataclass
class StuckAtFault:
    """Force a signal to a fixed value for a sustained window.

    Floor B2 uses this to pin `rst_n` low (broken reset) or high (missing
    reset) and prove the design either wedges or recovers.

    Attributes
    ----------
    signal_name : str
        Name of the DUT signal (looked up via `getattr(dut, signal_name)`).
    value : int
        The stuck-at value. Typically 0 or 1.
    duration_cycles : int
        How many clock cycles to hold the fault. After this, the signal
        is released and the RTL resumes driving it.
    """

    signal_name: str
    value: int
    duration_cycles: int

    async def run(self, dut) -> None:
        handle = getattr(dut, self.signal_name)
        log.info(
            "StuckAtFault: %s := %d for %d cycles",
            self.signal_name,
            self.value,
            self.duration_cycles,
        )
        force_signal(handle, self.value)
        await wait_cycles(dut.clk, self.duration_cycles)
        release_signal(handle)
        log.info("StuckAtFault: %s released", self.signal_name)


# -----------------------------------------------------------------------------
# BurstFault
# -----------------------------------------------------------------------------


@dataclass
class BurstFault:
    """Pulse a signal low-then-high (or high-then-low) with explicit widths.

    Floor B2 uses this to exercise the reset-pulse case - the design must
    cleanly recover from a reset pulse of any width >= 1 cycle. BurstFault
    with `low_cycles=1, high_cycles=5` sends a minimum-width negedge pulse
    and then waits for recovery.

    Attributes
    ----------
    signal_name : str
        Name of the DUT signal.
    low_cycles : int
        How many cycles to hold low.
    high_cycles : int
        How many cycles to hold high after the low phase.
    invert : bool
        If True, pulse high-then-low instead. Default False.
    """

    signal_name: str
    low_cycles: int
    high_cycles: int
    invert: bool = False

    async def run(self, dut) -> None:
        handle = getattr(dut, self.signal_name)
        first, second = (1, 0) if self.invert else (0, 1)
        log.info(
            "BurstFault: %s pulse (%d, %d) cycles (first=%d second=%d)",
            self.signal_name,
            self.low_cycles,
            self.high_cycles,
            first,
            second,
        )
        force_signal(handle, first)
        await wait_cycles(dut.clk, self.low_cycles)
        force_signal(handle, second)
        await wait_cycles(dut.clk, self.high_cycles)
        release_signal(handle)
        log.info("BurstFault: %s released", self.signal_name)


# -----------------------------------------------------------------------------
# SEUFault
# -----------------------------------------------------------------------------


@dataclass
class SEUFault:
    """Single-event upset - flip one bit of a register for one delta cycle.

    Floor 5 uses this to inject SEUs on the FSM state register and prove
    the design returns to IDLE within 2 cycles regardless of which bit
    is flipped and which state it is flipped from.

    Attributes
    ----------
    register_path : str
        Dotted path into the DUT. For the state register in our top-level
        instance, this is `"tt_um_example.fsm.state"` - `conftest.py`
        resolves the path and hands in a ready handle.
    bit_index : int
        Which bit to flip.
    fire_after_cycles : int
        Wait this many cycles before firing. Lets the test align the SEU
        with a specific state transition.
    """

    register_path: str
    bit_index: int
    fire_after_cycles: int = 0

    async def run(self, dut) -> None:
        # register_path is a dotted path; walk it down from dut.
        handle = dut
        for attr in self.register_path.split("."):
            handle = getattr(handle, attr)
        if self.fire_after_cycles:
            await wait_cycles(dut.clk, self.fire_after_cycles)
        log.info(
            "SEUFault: flipping %s bit %d",
            self.register_path,
            self.bit_index,
        )
        deposit_bit(handle, self.bit_index)
        # The flip is instantaneous; we do not wait after. The test
        # observer will wait for the recovery window and check the state.


# -----------------------------------------------------------------------------
# Composite faults
# -----------------------------------------------------------------------------


@dataclass
class FaultSequence:
    """Run a list of faults in sequence, one after the other.

    Useful when writing SG-M2-07 tests that combine two fault types
    (e.g. an SEU followed immediately by a reset pulse).
    """

    faults: List["_Fault"] = field(default_factory=list)

    async def run(self, dut) -> None:
        for fault in self.faults:
            await fault.run(dut)


# Type alias so FaultSequence can hold any of the fault classes.
_Fault = "StuckAtFault | BurstFault | SEUFault | FaultSequence"

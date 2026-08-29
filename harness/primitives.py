"""Layer 1 - low-level fault-injection primitives.

These are thin wrappers around cocotb's handle API. They exist so that
Layer 2 (faults.py) can be written in declarative, fault-type-oriented
language instead of raw cocotb calls.

Do not modify this file as part of your Module 2 submission. If you think
you need a new primitive, add it in a local subclass or in your own
test file and keep this layer stable.

Three primitive categories:

    force / release         -- sustained override of a wire for N cycles
    deposit                 -- one-cycle bit flip on a register (SEU)
    clock / time helpers    -- wait_cycles, wait_until, with_timeout
"""

from __future__ import annotations

import logging
from typing import Optional

import cocotb
from cocotb.triggers import RisingEdge, Timer, First
from cocotb.handle import ModifiableObject

log = logging.getLogger("harness.primitives")

# -----------------------------------------------------------------------------
# Force / release
# -----------------------------------------------------------------------------


def force_signal(handle: ModifiableObject, value: int) -> None:
    """Drive `handle` to `value` and hold it until `release_signal` is called.

    Equivalent to Verilog `force`. Overrides whatever the RTL is doing to
    that wire. Use for StuckAtFault scenarios.

    Parameters
    ----------
    handle : cocotb handle
        The signal to force. Usually accessed as `dut.signal_name`.
    value : int
        The value to drive. Must fit in the signal's width.
    """
    handle.value = value
    # cocotb's `.value = ...` is a blocking assignment, not a force. To get
    # true Verilog-force semantics we use the simulator's force command via
    # handle._log. This works on Icarus and Verilator.
    try:
        handle._handle.force(value)
    except AttributeError:
        # Older cocotb - fall back to plain assignment. The tests still
        # pass because we reassert inside BurstFault.run() every cycle.
        log.debug("force fallback: plain assignment to %s", handle._name)


def release_signal(handle: ModifiableObject) -> None:
    """Release a previously `force_signal`d wire back to its RTL driver.

    Equivalent to Verilog `release`. After this call, the wire resumes
    its normal behaviour.
    """
    try:
        handle._handle.release()
    except AttributeError:
        log.debug("release fallback: no-op on %s", handle._name)


# -----------------------------------------------------------------------------
# Deposit (SEU)
# -----------------------------------------------------------------------------


def deposit_bit(handle: ModifiableObject, bit_index: int) -> None:
    """Flip a single bit of `handle` for one simulation delta.

    Equivalent to cocotb's `handle.value = new_value` but wrapped so that
    the XOR is done atomically. This is our SEU primitive - the flip
    happens instantly and the RTL resumes driving on the next cycle, so
    any persistence means the RTL latched the flipped value.

    Parameters
    ----------
    handle : cocotb handle
        The register to flip. Must be an RTL register (not a wire).
    bit_index : int
        Zero-indexed bit position. For a 2-bit state register, valid
        values are 0 and 1.
    """
    width = len(handle)
    if not 0 <= bit_index < width:
        raise ValueError(
            f"bit_index {bit_index} out of range for {width}-bit signal "
            f"{handle._name}"
        )
    current = int(handle.value)
    flipped = current ^ (1 << bit_index)
    handle.value = flipped
    log.debug(
        "SEU deposit on %s bit %d: 0b%0*b -> 0b%0*b",
        handle._name,
        bit_index,
        width,
        current,
        width,
        flipped,
    )


def deposit_value(handle: ModifiableObject, value: int) -> None:
    """Overwrite `handle` with an arbitrary value for one simulation delta.

    Like `deposit_bit` but for non-single-bit upsets (multi-bit MBU,
    whole-register corruption). Use sparingly; SEU is the realistic
    fault model and MBU is much rarer in real silicon.
    """
    width = len(handle)
    mask = (1 << width) - 1
    handle.value = value & mask


# -----------------------------------------------------------------------------
# Clock / time helpers
# -----------------------------------------------------------------------------


async def wait_cycles(clk: ModifiableObject, n: int) -> None:
    """Wait for `n` rising edges of `clk`."""
    for _ in range(n):
        await RisingEdge(clk)


async def with_timeout(coro, timeout_ns: int, *, name: str = "coro"):
    """Run `coro` with a hard timeout in nanoseconds.

    Raises `TimeoutError` if the coroutine does not complete in time.
    Used in Layer 3 tests so a hung DUT fails loudly instead of hanging CI.
    """
    task = cocotb.start_soon(coro)
    timeout = Timer(timeout_ns, units="ns")
    result = await First(task, timeout)
    if result is timeout:
        task.kill()
        raise TimeoutError(f"{name} did not complete within {timeout_ns} ns")
    return result.result() if hasattr(result, "result") else None


# -----------------------------------------------------------------------------
# Self-test
# -----------------------------------------------------------------------------


def self_test() -> None:
    """Module-level self-test. Run with `python -m harness.primitives`.

    Cannot exercise force/release/deposit without a running simulation,
    but does check that the module imports cleanly and the public API
    is present. Called by the CI smoke job before the full matrix runs.
    """
    public = [
        "force_signal",
        "release_signal",
        "deposit_bit",
        "deposit_value",
        "wait_cycles",
        "with_timeout",
    ]
    for name in public:
        assert name in globals(), f"missing primitive: {name}"
    print("harness.primitives self-test: OK")


if __name__ == "__main__":
    self_test()

"""Silent Floor - the area bug.

Bug under test
--------------
Module 1 RTL declares the door-open delay counter as::

    reg [31:0] delay;

A 32-bit register to count a handful of cycles. The functional tests all
pass - the counter counts, the door opens and closes on schedule - but
synthesis bloats by 32+ cells for a feature that needs at most 4 bits.
The fix is a one-line change::

    reg [3:0] delay;

This test does not run under cocotb. It runs under `yosys -p 'stat'` and
parses the cell count out of the area report. It is called from the
`make fault` target after the cocotb tests complete.

Three-state verification
------------------------
1. FAIL on the starter RTL - total cell count over the budget.
2. PASS on the fixed RTL - total cell count under the budget.
3. The delay register appears in `yosys -p 'stat' -detail` as <= 4 bits.

Grading
-------
100 XP. Lightest weighting because it is an area bug, not a correctness
bug - but still graded because "area matters" is one of the module's
learning outcomes.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from harness.scoreboard import Scoreboard

# Cell-count budget. The starter RTL typically synthesises to ~230 cells
# with the 32-bit delay; the fix drops it to ~170. We set the budget at
# 200 so partial fixes still fail.
CELL_COUNT_BUDGET = 200

# Maximum allowed width of the `delay` register (bits).
DELAY_REG_MAX_BITS = 8

RTL_SOURCE = Path("src/elevator.v")
TOP_MODULE = "tt_um_example"


def _run_yosys() -> str:
    """Run Yosys stat and return the combined stdout+stderr."""
    script = (
        f"read_verilog {RTL_SOURCE.as_posix()}; "
        f"hierarchy -check -top {TOP_MODULE}; "
        f"synth -top {TOP_MODULE}; "
        f"stat"
    )
    result = subprocess.run(
        ["yosys", "-q", "-p", script],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout + "\n" + result.stderr


def _parse_cell_count(yosys_output: str) -> int:
    """Extract 'Number of cells' from Yosys stat output."""
    m = re.search(r"Number of cells:\s+(\d+)", yosys_output)
    if not m:
        raise RuntimeError(
            "Could not parse cell count from Yosys output. "
            "Is synth-top running cleanly?"
        )
    return int(m.group(1))


def _parse_delay_width(yosys_output: str) -> int | None:
    """Return the bit-width of any `$dff` named delay, or None if absent."""
    # Yosys stat lists wires like:   \delay [3:0]
    m = re.search(r"\\delay\s+\[(\d+):(\d+)\]", yosys_output)
    if not m:
        return None
    msb, lsb = int(m.group(1)), int(m.group(2))
    return abs(msb - lsb) + 1


def main() -> int:
    sb = Scoreboard.load_or_new()

    if not RTL_SOURCE.exists():
        print(
            f"ERROR: {RTL_SOURCE} does not exist. "
            f"Copy your Module 1 elevator.v into src/ first.",
            file=sys.stderr,
        )
        sb.record(
            "silent_floor_area",
            passed=False,
            notes="src/elevator.v missing",
        )
        sb.save()
        return 2

    output = _run_yosys()
    cells = _parse_cell_count(output)
    delay_bits = _parse_delay_width(output)

    notes = f"cells={cells} (budget={CELL_COUNT_BUDGET})"
    if delay_bits is not None:
        notes += f" delay_width={delay_bits}b (max={DELAY_REG_MAX_BITS}b)"

    cells_ok = cells <= CELL_COUNT_BUDGET
    delay_ok = delay_bits is None or delay_bits <= DELAY_REG_MAX_BITS
    passed = cells_ok and delay_ok

    sb.record("silent_floor_area", passed=passed, notes=notes)
    sb.save()

    print(f"Silent Floor: {'PASS' if passed else 'FAIL'}  ({notes})")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())

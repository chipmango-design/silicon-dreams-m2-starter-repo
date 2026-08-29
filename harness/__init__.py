"""Silicon Dreams Module 2 fault-injection harness.

Public API:

    from harness.primitives import force_signal, release_signal, deposit_bit
    from harness.faults import StuckAtFault, BurstFault, SEUFault
    from harness.scoreboard import Scoreboard

Three layers:

    primitives.py  -- low-level force/release/deposit helpers
    faults.py      -- composable fault-type coroutines
    scoreboard.py  -- per-floor pass/fail + XP accounting for CI

You do not modify primitives.py or faults.py this week. You extend the
test layer (test/fault_injection/) in SG-M2-07 with your own fault test.
"""

__version__ = "2.0.0"
__all__ = ["primitives", "faults", "scoreboard"]

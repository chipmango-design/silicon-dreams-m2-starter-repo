"""Layer 3 support - per-floor pass/fail scoring and XP accounting.

The scoreboard is what ChipFoundry CI reads to decide your Module 2 grade.
Each floor test calls `record()` with a pass/fail and an XP delta. At the
end of the CI run, the scoreboard writes `fault_matrix_results.json` for
the ChipFoundry grader service and the public leaderboard.

This module is intentionally simple - no cleverness, no magic. Read it
top-to-bottom and you know exactly what gets graded.

XP weights (also reflected in SG-M2-08):

    Floor B2 (reset)           150 XP
    Floor 5 (SEU)              200 XP
    Floor 1 (input)            150 XP
    Silent Floor (area)        100 XP
    Custom test (SG-M2-07)     200 XP
    Reflection (SG-M2-08)      200 XP  (graded by humans, not this file)
    -------------------------------------
    Total auto-graded          800 XP
    Total with reflection     1000 XP
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

log = logging.getLogger("harness.scoreboard")

# XP weights for auto-graded floors. Keep in sync with SG-M2-08.
XP_WEIGHTS: Dict[str, int] = {
    "floor_b2_reset": 150,
    "floor_5_seu": 200,
    "floor_1_input": 150,
    "silent_floor_area": 100,
    "custom_test": 200,
}

OUTPUT_PATH = Path(
    os.environ.get(
        "M2_SCOREBOARD_PATH",
        "test/fault_injection/fault_matrix_results.json",
    )
)


@dataclass
class FloorResult:
    """One row in the scoreboard."""

    floor: str
    passed: bool
    xp_earned: int
    xp_max: int
    notes: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds")
    )


@dataclass
class Scoreboard:
    """Aggregate per-floor results.

    Typical usage from a cocotb test:

        from harness.scoreboard import Scoreboard
        sb = Scoreboard.load_or_new()
        sb.record("floor_b2_reset", passed=True, notes="recovered in 1 cycle")
        sb.save()
    """

    results: List[FloorResult] = field(default_factory=list)

    # ---------- recording ----------

    def record(
        self,
        floor: str,
        *,
        passed: bool,
        notes: str = "",
        xp_override: int | None = None,
    ) -> None:
        """Record the result for one floor.

        If called twice for the same floor, the second call replaces the
        first. This is deliberate - cocotb sometimes re-runs tests on
        retry and we want the latest result to win.
        """
        if floor not in XP_WEIGHTS:
            raise KeyError(
                f"unknown floor '{floor}'. Known floors: "
                f"{sorted(XP_WEIGHTS)}"
            )
        xp_max = XP_WEIGHTS[floor]
        xp_earned = xp_override if xp_override is not None else (xp_max if passed else 0)
        entry = FloorResult(
            floor=floor,
            passed=passed,
            xp_earned=xp_earned,
            xp_max=xp_max,
            notes=notes,
        )
        # Replace previous entry for the same floor, if any.
        self.results = [r for r in self.results if r.floor != floor]
        self.results.append(entry)
        log.info(
            "Scoreboard: %s = %s (%d / %d XP) %s",
            floor,
            "PASS" if passed else "FAIL",
            xp_earned,
            xp_max,
            notes,
        )

    # ---------- querying ----------

    @property
    def total_xp(self) -> int:
        return sum(r.xp_earned for r in self.results)

    @property
    def total_xp_max(self) -> int:
        return sum(r.xp_max for r in self.results)

    def summary(self) -> str:
        lines = ["Silicon Dreams M2 scoreboard"]
        for r in sorted(self.results, key=lambda r: r.floor):
            status = "PASS" if r.passed else "FAIL"
            lines.append(
                f"  {r.floor:25s} {status}  {r.xp_earned:4d} / {r.xp_max:4d} XP"
            )
        lines.append(f"  {'TOTAL':25s}      {self.total_xp:4d} / {self.total_xp_max:4d} XP")
        return "\n".join(lines)

    # ---------- persistence ----------

    @classmethod
    def load_or_new(cls, path: Path | None = None) -> "Scoreboard":
        path = path or OUTPUT_PATH
        if not path.exists():
            return cls()
        with path.open() as f:
            raw = json.load(f)
        sb = cls()
        for row in raw.get("results", []):
            sb.results.append(FloorResult(**row))
        return sb

    def save(self, path: Path | None = None) -> None:
        path = path or OUTPUT_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "total_xp": self.total_xp,
            "total_xp_max": self.total_xp_max,
            "results": [asdict(r) for r in self.results],
        }
        with path.open("w") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
        log.info("Scoreboard written to %s", path)


if __name__ == "__main__":
    # Dry run - show an empty scoreboard and exit.
    sb = Scoreboard()
    print(sb.summary())

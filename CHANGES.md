# Silicon Dreams Module 2 starter — change log

All notable changes from the Module 1 starter repo.

## 2.0.0 — 2026-04-19

Initial Module 2 starter release. Scope: fault-injection harness + per-floor labs for the four deliberate M1 bugs.

### Added

- Three-layer cocotb fault-injection harness under `harness/`:
  - `primitives.py` — force/release/deposit + clock and timeout helpers
  - `faults.py` — `StuckAtFault`, `BurstFault`, `SEUFault`, `FaultSequence`
  - `scoreboard.py` — per-floor pass/fail + XP accounting with JSON export for the ChipFoundry grader service
- Four floor tests under `test/fault_injection/`:
  - `test_floor_b2_reset.py` (reset polarity)
  - `test_floor_5_seu.py` (state encoding SEU resilience)
  - `test_floor_1_input.py` (input range-clamp + error LED)
  - `test_silent_floor_area.py` (Yosys area report)
- Shared pytest/cocotb fixtures in `test/fault_injection/conftest.py`
- `test/Makefile` with `smoke` and `fault` targets
- CI workflows `smoke.yml` and `fault-matrix.yml` with ChipFoundry grader POST
- Instructor-only reference `notes/known-solutions.md` with exact diffs per floor
- Learner write-up templates for each floor under `notes/`
- Harness architecture doc at `docs/harness-architecture.md`

### Not changed from Module 1

- `src/elevator.v` — learners paste their M1 RTL here. The harness is RTL-agnostic.
- `info.yaml` — shuttle metadata stays identical.
- Course code `CM-HW-101`, partners `ChipMango × ChipFoundry`.

# Silicon Dreams · Module 2 · The Parallel Shaft

[![Smoke](../../workflows/smoke/badge.svg)](../../actions/workflows/smoke.yml) [![Fault](../../workflows/fault-matrix/badge.svg)](../../actions/workflows/fault-matrix.yml) [![Docs](../../workflows/docs/badge.svg)](../../actions/workflows/docs.yml)

This repository is the **Week 2 starter project** for the Silicon Dreams course (`CM-HW-101`), a three-week co-delivered programme from **ChipMango** and **ChipFoundry** that takes learners from RTL to real silicon.

In Module 1 you built a four-state elevator controller and shipped it to the ChipFoundry chipIgnite shuttle. In Module 2, the elevator is trapped inside a parallel shaft by AXIOM, and the four deliberate bugs that were only *documented* last week now actively break the lift. Your job this week is to build a **fault-injection harness** that proves each bug is real, then fix each bug without regressing the others.

By the end of the week, the same RTL that shipped in Module 1 will be hardened against reset-polarity errors, single-event upsets, oversized counters, and out-of-range input — and your harness will be CI-gated on ChipFoundry infrastructure.

## Course context

| | |
|---|---|
| **Course code** | CM-HW-101 |
| **Module** | M2 — The Parallel Shaft |
| **Duration** | Week 2 (≈ 8–12 practical hours) |
| **Prerequisite** | Module 1 completed, Module 1 elevator RTL imported |
| **Language** | Verilog HDL + Python (cocotb) |
| **Platform** | ChipFoundry chipIgnite + cocotb fault-injection harness |
| **Partners** | ChipMango × ChipFoundry · MoU 2026 |
| **Course home** | [chipmango.io/silicon-dreams](https://chipmango.io/silicon-dreams) |

## The four floors

Each deliberate bug from Module 1 is mapped to a floor of the parallel shaft. You must clear all four floors to escape the module.

| Floor | Bug | Technique | Pass criteria |
|---|---|---|---|
| **B2** | Reset polarity inverted (`posedge rst_n`) | `StuckAtFault` + `BurstFault` on `rst_n` | Design recovers from a low-then-high reset pulse of any width ≥ 1 cycle |
| **5** | 2-bit dense state encoding (no illegal-state guard) | `SEUFault` (cocotb deposit) on FSM state register | Design returns to IDLE within 2 cycles after any single-bit flip |
| **1** | No range-clamp on `requested_floor` | Directed stimulus with `requested_floor > 8` | Invalid request is ignored, `uio_out[7]` error LED asserts for 1 cycle |
| **Silent** | 32-bit delay counter (area bug, not functional) | Yosys area report + static analysis | `yosys -p 'stat'` shows < 200 cells, delay register ≤ 4 bits wide |

## Quick start

```bash
# 1. Use this repo as a template (green "Use this template" button in GitHub)
#    Create your own fork under your GitHub username.

# 2. Clone your fork AND your Module 1 fork as siblings
git clone https://github.com/<your-username>/mod1-elevator.git
git clone https://github.com/<your-username>/mod2-parallel-shaft.git
cd mod2-parallel-shaft

# 3. Copy your Module 1 RTL into src/ (the harness expects it there)
cp ../mod1-elevator/src/elevator.v src/elevator.v

# 4. Install simulation + harness dependencies
pip install -r test/requirements.txt
sudo apt-get install iverilog gtkwave yosys   # Ubuntu / Debian
brew install icarus-verilog gtkwave yosys     # macOS

# 5. Smoke-test (should still pass — nominal behaviour is unchanged)
make smoke

# 6. Run the fault matrix (should FAIL all four floors until you fix the bugs)
make fault
```

If `make smoke` passes and `make fault` prints four red `FAIL` lines (one per floor), you are ready to open **TB-M2-01 · Welcome to the Parallel Shaft** and begin the escape.

## What is in this repository

| Path | What it is |
|---|---|
| `src/elevator.v` | *You paste your Module 1 RTL here.* The harness is RTL-agnostic — any design that obeys the M1 pinout contract will work. |
| `harness/primitives.py` | Low-level fault primitives — `force_signal`, `release_signal`, `deposit_bit`, clock/time helpers. |
| `harness/faults.py` | Composable fault classes — `StuckAtFault`, `BurstFault`, `SEUFault`. |
| `harness/scoreboard.py` | Per-floor pass/fail scoring, XP accounting, JSON export for the CI leaderboard. |
| `test/fault_injection/conftest.py` | cocotb + pytest fixtures. Imports your Module 1 pinout constants. |
| `test/fault_injection/test_floor_b2_reset.py` | Floor B2 — reset polarity. Should FAIL on starter RTL, PASS on fixed RTL. |
| `test/fault_injection/test_floor_5_seu.py` | Floor 5 — state encoding SEU resilience. |
| `test/fault_injection/test_floor_1_input.py` | Floor 1 — `requested_floor` range-clamp. |
| `test/fault_injection/test_silent_floor_area.py` | Silent Floor — Yosys area and timing budget check. |
| `test/Makefile` | `make smoke` (nominal test) and `make fault` (full matrix). |
| `docs/harness-architecture.md` | Three-layer harness design — primitives → faults → tests. |
| `notes/` | Your per-floor write-ups, waveforms, reflection. |
| `.github/workflows/fault-matrix.yml` | CI workflow that runs the full fault matrix on every push. |

## How the harness is layered

The fault-injection harness is deliberately three layers deep so each layer can be unit-tested on its own. This separation is taken directly from **TB-M2-02 · Fault Injection 101**.

```
┌─────────────────────────────────────────────────┐
│  Layer 3 — Tests                                │
│  test_floor_*.py                                │
│  Declarative: "given this fault, expect this."  │
└────────────────────────▲────────────────────────┘
                         │ uses
┌────────────────────────┴────────────────────────┐
│  Layer 2 — Fault types                          │
│  harness/faults.py                              │
│  StuckAtFault, BurstFault, SEUFault             │
│  (async coroutines, one per fault type)         │
└────────────────────────▲────────────────────────┘
                         │ uses
┌────────────────────────┴────────────────────────┐
│  Layer 1 — Primitives                           │
│  harness/primitives.py                          │
│  force_signal / release_signal / deposit_bit    │
└─────────────────────────────────────────────────┘
```

You do not modify Layer 1 or Layer 2 this week. You will *extend* Layer 3 in **SG-M2-07** by adding your own custom fault test.

## Deliberate bugs (course policy)

This starter repo has **no RTL bugs of its own** — the bugs live in the Module 1 RTL you import. That is the whole point of Module 2: you build a harness that exposes the bugs your Module 1 code has been quietly shipping.

If you are a ChipFoundry engineer reviewing this repo, see `notes/known-solutions.md` for the private per-floor solutions (hidden from learners by course convention).

## What you will submit

By the end of Module 2 you will push the following to your fork:

- `src/elevator.v` — your Module 1 RTL, now with **all four bugs fixed**.
- `test/fault_injection/test_custom.py` — your own fault-injection test (`SG-M2-07`), worth at least 200 XP on the rubric.
- `notes/floor-b2.md` through `notes/silent-floor.md` — per-floor write-ups with waveform snapshots.
- `notes/m2-reflection.md` — your escape-room reflection, minimum 400 words.
- A passing `fault-matrix.yml` run on the `main` branch of your fork.

The ChipFoundry CI grader will automatically compute your XP score from the fault matrix run and post it to the leaderboard. See `SG-M2-08 · M2 Escape Checklist and Reflection` for the full rubric.

## Scoring rubric (summary)

| Tier | XP | What it means |
|---|---|---|
| **Minimum pass** | 600 XP | All four floors pass in CI. Custom test present but minimal. |
| **Distinction** | 900 XP | All floors pass. Custom test has three-state verification. Reflection is thorough. |
| **Bonus** | +100 XP | Clean DRC on the Module 3 re-submission (deferred to Week 3). |
| **Max** | 1000 XP | All of the above. |

The full per-line rubric is in `SG-M2-08`.

## Learning outcomes (Module 2)

By completing this module, learners will be able to:

- Articulate why fault injection is necessary in silicon design and how it differs from functional verification.
- Use cocotb `deposit`, Verilog `force`/`release`, and directed stimulus to inject three distinct fault classes.
- Interpret Yosys `stat` output to find area and timing bugs that never fail a functional test.
- Design a test that fails on broken RTL, passes on fixed RTL, and does not regress nominal behaviour.
- Build a three-layer cocotb harness (primitives → faults → tests) that is CI-friendly and reusable across modules.
- Read and fix four specific bug classes: inverted reset polarity, SEU-vulnerable state encoding, oversized counters, and missing input range-clamps.

## Resources

- ChipFoundry platform docs — [chipfoundry.io/docs](https://chipfoundry.io/docs)
- Silicon Dreams course home — [chipmango.io/silicon-dreams](https://chipmango.io/silicon-dreams)
- cocotb documentation — [docs.cocotb.org](https://docs.cocotb.org)
- Yosys manual — [yosyshq.net/yosys/documentation.html](https://yosyshq.net/yosys/documentation.html)
- Course Discord — link distributed with enrolment.

## Licence

RTL and harness code are released under **Apache-2.0**. Course materials (`docs/`, `notes/`, study guides, videos) are **CC BY-NC-SA 4.0** by ChipMango × ChipFoundry.

---
*ChipMango × ChipFoundry · MoU Partnership 2026 · CM-HW-101-M2*

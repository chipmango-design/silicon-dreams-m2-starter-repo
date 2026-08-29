# Harness architecture

This document describes the three-layer design of the Module 2 fault-injection harness. It is referenced from **TB-M2-02 · Fault Injection 101** and from **SG-M2-07 · Build Your Own Fault-Injection Test**.

## Why three layers

A fault-injection harness is easy to write badly. The most common failure mode is a pile of cocotb coroutines that each reach into `dut.*` directly, duplicate reset sequences, and share no vocabulary with each other. Six months later, nobody can refactor the harness because every test is its own bespoke universe.

The three-layer design prevents that. Each layer has exactly one job, and the layer above it is allowed to depend only on the layer below — never sideways, never upward. When a new engineer joins the course team, they can understand the harness by reading it bottom-up in under an hour.

## Layer 1 — primitives (`harness/primitives.py`)

Primitives are the raw verbs of fault injection: force a wire, release it, flip a bit of a register. They are thin wrappers around cocotb's handle API and nothing else. The point of this layer is *stability*. The cocotb API changes between versions; the Verilog force/release semantics change between simulators. Everything fragile goes here, once, so the layers above can sleep soundly.

Primitives never know what a "fault" is. They just know how to poke the simulator. If you find yourself writing `if floor == "B2":` inside this file, stop — you are in the wrong layer.

## Layer 2 — fault types (`harness/faults.py`)

Fault types are composable coroutines that describe a *kind* of fault: `StuckAtFault`, `BurstFault`, `SEUFault`. Each one is a small dataclass with an `async def run(self, dut)` method. Two rules for this layer:

1. A fault class describes a fault in terms of the signals and registers it touches, not in terms of which floor it belongs to. `StuckAtFault(signal_name="rst_n", value=0, duration_cycles=10)` is portable — it works for Floor B2 today and for any future reset-related test.
2. A fault class never calls pass/fail. It injects; the test observes.

## Layer 3 — tests (`test/fault_injection/test_floor_*.py`)

Tests are the declarative layer. A well-written floor test reads like an English specification: *start with a clean reset, drive the DUT into state S, inject fault F, wait W cycles, and assert the DUT is back in state S'*. All the mechanics of forcing wires and flipping bits live in Layers 1 and 2, so the test file stays readable.

This is the only layer you extend as a learner. `SG-M2-07` asks you to write `test_custom.py` that combines at least two fault types in a sequence the existing floors do not cover.

## How the scoreboard fits in

`harness/scoreboard.py` is a Layer-3 helper — a plain dataclass that knows how to record a pass/fail and write a JSON file. It is not a fourth layer because it does not inject anything; it just watches.

CI calls `python -m harness.scoreboard` at the end of the fault matrix to print a summary. The `fault_matrix_results.json` it writes is what the ChipFoundry grader service reads to compute your XP.

## Rules of thumb

- If you are adding a new simulator workaround, it goes in Layer 1.
- If you are adding a new fault *kind* (e.g. `ClockGlitchFault`), it goes in Layer 2.
- If you are adding a new floor or a new test scenario, it goes in Layer 3.
- Never import Layer 3 from Layer 1 or 2.
- Never put pass/fail logic below Layer 3.

If you find yourself wanting to break these rules, it usually means the layering is wrong for your use case — talk to the instructor team on the course Discord before reshaping the harness.

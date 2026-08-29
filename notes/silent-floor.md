# Silent Floor — area and timing

*Learner write-up template. Fill this in as you work through SG-M2-06.*

## What I observed in the Yosys report (broken RTL)

<!-- Paste the `Number of cells` and `delay [MSB:LSB]` lines from the `yosys -p 'synth; stat'` output on the starter RTL. -->

## What the fix was

<!-- One-line diff: `reg [31:0] delay;` -> `reg [3:0] delay;`. Explain why this is enough. -->

## Why this bug never failed a functional test

<!-- Two sentences. What is the difference between a correctness bug and an area bug? Why does "area matters" even when the chip works? -->

## Scoreboard entry

| Field | Value |
|---|---|
| Test | `test_silent_floor_area.py` |
| Result | PASS / FAIL |
| XP | / 100 |
| Notes from scoreboard | |

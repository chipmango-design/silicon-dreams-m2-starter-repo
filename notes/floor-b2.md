# Floor B2 — the broken reset

*Learner write-up template. Fill this in as you work through SG-M2-03.*

## What I observed on the broken RTL

<!-- Describe: when did Floor B2 first fail? Paste the cocotb FAIL line and the waveform around rst_n. -->

## What the fix was

<!-- Paste the diff between your starter elevator.v and your fixed elevator.v, just for the FSM block. -->

## What I learned

<!-- Three or four sentences. What does it mean for a wire to be "active-low"? Why did the broken RTL compile and even pass the Module 1 smoke test? -->

## Waveform snapshot

<!-- Insert gtkwave screenshot of rst_n, clk, and state across the reset pulse at t=~200 ns. -->

## Scoreboard entry

| Field | Value |
|---|---|
| Test | `test_floor_b2_reset.py` |
| Result | PASS / FAIL |
| XP | / 150 |
| Notes from scoreboard | |

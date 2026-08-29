# Floor 1 — the corrupted input

*Learner write-up template. Fill this in as you work through SG-M2-05.*

## What I observed on the broken RTL

<!-- Paste the cocotb output when requested_floor = 10 was accepted. What did uo_out[3:0] display? -->

## What the fix was

<!-- Paste the diff for the request gate and the error-LED block. Mention uio_oe[7]! -->

## Why the error LED pulses instead of latches

<!-- Two sentences. What would go wrong if the LED latched on? -->

## Waveform snapshot

<!-- Insert gtkwave screenshot of ui_in, uio_out[7], and state during an invalid request. -->

## Scoreboard entry

| Field | Value |
|---|---|
| Test | `test_floor_1_input.py` |
| Result | PASS / PARTIAL / FAIL |
| XP | / 150 |
| Notes from scoreboard | |

# Floor 5 — the state encoding war

*Learner write-up template. Fill this in as you work through SG-M2-04.*

## What I observed on the broken RTL

<!-- Paste the SEUFault output for at least two flip-from-state combinations that silently corrupted the FSM. -->

## What the fix was

<!-- Paste the diff: old dense encoding, new one-hot encoding, and the `default` branch in the case statement. -->

## Why one-hot (and not Gray code)

<!-- Two or three sentences. Why does one-hot turn every single-bit flip into an illegal state? -->

## Waveform snapshot

<!-- Insert gtkwave screenshot of state[3:0] before, during, and after an SEU deposit. -->

## Scoreboard entry

| Field | Value |
|---|---|
| Test | `test_floor_5_seu.py` |
| Result | PASS / FAIL |
| XP | / 200 |
| Notes from scoreboard | |

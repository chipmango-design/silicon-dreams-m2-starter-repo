"""Silicon Dreams Module 2 fault-injection test package.

Each test file corresponds to one floor of the parallel shaft:

    test_floor_b2_reset.py       Floor B2 - reset polarity
    test_floor_5_seu.py          Floor 5  - state encoding SEU
    test_floor_1_input.py        Floor 1  - input range-clamp
    test_silent_floor_area.py    Silent Floor - Yosys area check

conftest.py holds the shared fixtures (clock, reset, pinout constants).
"""

# Silicon Dreams Module 2 - cocotb + Yosys driver Makefile.
#
# Targets:
#   smoke   -- run the single nominal test (must always pass)
#   fault   -- run the full four-floor fault matrix + Yosys area check
#   clean   -- remove build artefacts
#
# The `fault` target aggregates results into fault_injection/fault_matrix_results.json
# which the ChipFoundry CI grader reads to compute your XP score.

SIM ?= icarus
TOPLEVEL_LANG ?= verilog
TOPLEVEL := tb

VERILOG_SOURCES := $(PWD)/tb.v $(PWD)/../src/elevator.v

# Where we tell cocotb to look for test modules. We override MODULE per
# target below.
export PYTHONPATH := $(PWD)/..:$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim

.PHONY: smoke fault fault_cocotb fault_area clean

# ---------------------------------------------------------------------------
# Smoke - the Module 1 nominal test, unchanged.
# ---------------------------------------------------------------------------
smoke:
	$(MAKE) MODULE=test

# ---------------------------------------------------------------------------
# Fault matrix - all four floors.
# ---------------------------------------------------------------------------
fault: fault_cocotb fault_area
	@echo ""
	@echo "==== Fault matrix complete ===="
	@cat fault_injection/fault_matrix_results.json || true

# Three cocotb fault tests (B2, 5, 1).
fault_cocotb:
	$(MAKE) MODULE=fault_injection.test_floor_b2_reset
	$(MAKE) MODULE=fault_injection.test_floor_5_seu
	$(MAKE) MODULE=fault_injection.test_floor_1_input

# Silent Floor - Yosys area check, not cocotb.
fault_area:
	cd .. && python3 -m test.fault_injection.test_silent_floor_area

clean::
	rm -rf sim_build results.xml fault_injection/fault_matrix_results.json

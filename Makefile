# Top-level build for the RE lab. Every challenge has its own Makefile that
# writes its binary into $(DIST).
DIST := $(abspath dist)
CHALLENGES := $(sort $(wildcard challenges/[0-9][0-9]-*))

.PHONY: all test lint check clean list ghidra-test rvemu-test test-z3

all:
	@mkdir -p $(DIST)
	@for c in $(CHALLENGES); do \
		$(MAKE) --no-print-directory -C $$c DIST=$(DIST) || exit 1; \
	done

test: all
	python3 tools/run_tests.py

lint:
	python3 tools/lint.py

check: rvemu-test test test-z3 lint

# z3 solvers (solve_z3.py) for older challenges. The concrete model checks
# always run; the symbolic part is skipped with a notice if z3 is missing.
test-z3: all
	@for s in challenges/*/solve_z3.py; do \
		c=$$(basename $$(dirname $$s)); echo "[z3] $$c"; \
		timeout 120 python3 $$s $(DIST)/$$c || exit 1; \
	done

rvemu-test:
	sh tools/rvemu_test.sh

list:
	@for c in $(CHALLENGES); do echo $$(basename $$c); done

clean:
	rm -rf $(DIST)

ghidra-test: all
	sh tools/ghidra_test.sh

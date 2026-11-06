DIST ?= ../../dist
NAME := 13-env-checks
# src/ generated: tables.h comes from gen_tables.py (committed, not regenerated
# at build time so the build needs no extra step).
CFLAGS ?= -O0 -g0 -Wall -Wextra

$(DIST)/$(NAME): src/main.c src/tables.h
	@mkdir -p $(DIST)
	$(CC) $(CFLAGS) -I src -o $@ src/main.c

.PHONY: clean
clean:
	rm -f $(DIST)/$(NAME)

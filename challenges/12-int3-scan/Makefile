DIST ?= ../../dist
NAME := 12-int3-scan
# -fno-toplevel-reorder keeps the functions in source order, so the region
# region_begin..region_end really contains the check functions.
CFLAGS ?= -O0 -g0 -Wall -Wextra -fno-toplevel-reorder

$(DIST)/$(NAME): src/main.c src/patch_hash.py
	@mkdir -p $(DIST)
	$(CC) $(CFLAGS) -o $@.tmp src/main.c
	python3 src/patch_hash.py $@.tmp
	mv $@.tmp $@

.PHONY: clean
clean:
	rm -f $(DIST)/$(NAME) $(DIST)/$(NAME).tmp

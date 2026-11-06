DIST ?= ../../dist
NAME := 14-smc-xor
# -fno-toplevel-reorder keeps region_begin / verify / region_end in source
# order, so the encrypted span [region_begin, region_end) is exactly those.
CFLAGS ?= -O0 -g0 -Wall -Wextra -fno-toplevel-reorder

$(DIST)/$(NAME): src/main.c src/encrypt.py
	@mkdir -p $(DIST)
	$(CC) $(CFLAGS) -o $@.tmp src/main.c
	python3 src/encrypt.py $@.tmp
	mv $@.tmp $@

.PHONY: clean
clean:
	rm -f $(DIST)/$(NAME) $(DIST)/$(NAME).tmp

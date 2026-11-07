DIST ?= ../../dist
NAME := 15-smc-layers
# -fno-toplevel-reorder keeps r1_begin/stage1/r1_end and r2_begin/stage2/r2_end
# in source order, so each encrypted span is exactly its marker + stage fn.
CFLAGS ?= -O0 -g0 -Wall -Wextra -fno-toplevel-reorder

$(DIST)/$(NAME): src/main.c src/encrypt.py
	@mkdir -p $(DIST)
	$(CC) $(CFLAGS) -o $@.tmp src/main.c
	python3 src/encrypt.py $@.tmp
	mv $@.tmp $@

.PHONY: clean
clean:
	rm -f $(DIST)/$(NAME) $(DIST)/$(NAME).tmp

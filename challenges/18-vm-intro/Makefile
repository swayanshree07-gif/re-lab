DIST ?= ../../dist
NAME := 18-vm-intro
CFLAGS ?= -O0 -g0 -Wall -Wextra

$(DIST)/$(NAME): src/main.c src/bytecode.h
	@mkdir -p $(DIST)
	$(CC) $(CFLAGS) -o $@ $<

.PHONY: clean
clean:
	rm -f $(DIST)/$(NAME)

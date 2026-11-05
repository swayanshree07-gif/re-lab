DIST ?= ../../dist
NAME := 11-timing
CFLAGS ?= -O0 -g0 -Wall -Wextra

$(DIST)/$(NAME): src/main.c
	@mkdir -p $(DIST)
	$(CC) $(CFLAGS) -o $@ $<

.PHONY: clean
clean:
	rm -f $(DIST)/$(NAME)

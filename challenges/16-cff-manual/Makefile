DIST ?= ../../dist
NAME := 16-cff-manual
CFLAGS ?= -O0 -g0 -Wall -Wextra

$(DIST)/$(NAME): src/main.c
	@mkdir -p $(DIST)
	$(CC) $(CFLAGS) -o $@ $<

.PHONY: clean
clean:
	rm -f $(DIST)/$(NAME)

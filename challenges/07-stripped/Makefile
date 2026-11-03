DIST ?= ../../dist
NAME := 07-stripped
CFLAGS ?= -O2 -g0 -Wall -Wextra

$(DIST)/$(NAME): src/main.c
	@mkdir -p $(DIST)
	$(CC) $(CFLAGS) -s -o $@ $<

.PHONY: clean
clean:
	rm -f $(DIST)/$(NAME)

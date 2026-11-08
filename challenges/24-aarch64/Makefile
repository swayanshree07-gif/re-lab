DIST ?= ../../dist
NAME := 24-aarch64
# Freestanding AArch64, static, no libc.
ACC ?= clang
ALD ?= $(shell command -v ld.lld-23 || command -v ld.lld)
AFLAGS ?= --target=aarch64-linux-gnu -O1 -g0 -ffreestanding -fno-builtin \
	-fno-stack-protector -fno-pic -Wall -Wextra

$(DIST)/$(NAME): src/main.c
	@mkdir -p $(DIST)
	$(ACC) $(AFLAGS) -c -o $(DIST)/$(NAME).o src/main.c
	$(ALD) -static -e _start -o $@ $(DIST)/$(NAME).o
	rm -f $(DIST)/$(NAME).o

.PHONY: clean
clean:
	rm -f $(DIST)/$(NAME)

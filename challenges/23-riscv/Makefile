DIST ?= ../../dist
NAME := 23-riscv
# Freestanding RV64IM (no compressed insns), static, no libc.
RVCC ?= clang
RVLD ?= $(shell command -v ld.lld-23 || command -v ld.lld)
RVFLAGS ?= --target=riscv64-unknown-elf -march=rv64im -mabi=lp64 -O1 -g0 \
	-ffreestanding -fno-builtin -fno-stack-protector -fno-pic -Wall -Wextra

$(DIST)/$(NAME): src/main.c src/table.h
	@mkdir -p $(DIST)
	$(RVCC) $(RVFLAGS) -c -o $(DIST)/$(NAME).o src/main.c
	$(RVLD) -static -e _start -o $@ $(DIST)/$(NAME).o
	rm -f $(DIST)/$(NAME).o

.PHONY: clean
clean:
	rm -f $(DIST)/$(NAME)

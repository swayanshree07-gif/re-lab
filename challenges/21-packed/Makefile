DIST ?= ../../dist
NAME := 21-packed
CFLAGS ?= -O0 -g0 -Wall -Wextra
# payload: freestanding, PIC, no stack protector / unwind tables, so the flat
# blob has no relocations and no libc calls.
PCFLAGS := -Os -fPIC -ffreestanding -fno-stack-protector -fno-asynchronous-unwind-tables -fcf-protection=none -fno-builtin
B := $(DIST)/.build-$(NAME)

$(DIST)/$(NAME): src/main.c src/payload.c src/payload.ld src/pack.py src/gen_want.py
	@mkdir -p $(B)
	python3 src/gen_want.py $(B)/want.h
	$(CC) $(PCFLAGS) -I$(B) -c src/payload.c -o $(B)/payload.o
	ld -T src/payload.ld --oformat binary -o $(B)/payload.bin $(B)/payload.o
	python3 src/pack.py $(B)/payload.bin $(B)/packed.h
	$(CC) $(CFLAGS) -I$(B) -o $@ src/main.c

.PHONY: clean
clean:
	rm -rf $(DIST)/$(NAME) $(B)

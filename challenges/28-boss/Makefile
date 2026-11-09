DIST ?= ../../dist
NAME := 28-boss
CFLAGS ?= -O1 -g0 -Wall -Wextra
PCFLAGS := -Os -fPIC -ffreestanding -fno-stack-protector -fno-asynchronous-unwind-tables -fcf-protection=none -fno-builtin
B := $(DIST)/.build-$(NAME)

$(DIST)/$(NAME): src/main.c src/stage1.h src/stage2.c src/stage2.ld src/pack.py src/SPOILERS
	@mkdir -p $(B)
	$(CC) $(PCFLAGS) -c src/stage2.c -o $(B)/stage2.o
	ld -T src/stage2.ld --oformat binary -o $(B)/stage2.bin $(B)/stage2.o
	python3 src/pack.py $(B)/stage2.bin src/SPOILERS $(B)/stage2_packed.h
	$(CC) $(CFLAGS) -s -I$(B) -o $@ src/main.c

.PHONY: clean
clean:
	rm -rf $(DIST)/$(NAME) $(B)

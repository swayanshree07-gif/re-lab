# 24-aarch64

## Goal
The program asks for a **name** and a **serial** (format `XXXX-XXXX`, upper-case
hex). Write a key generator that works for any name of 4–32 printable characters.

## Difficulty
★★★☆☆ (60–90 minutes). Classic keygen, unfamiliar instruction set: this binary is
**AArch64** (ARM64), static, freestanding (no libc, raw `svc #0` syscalls).

## Allowed tools
Anything: `file`, `llvm-objdump -d` (GNU objdump on x86 can't read it), Ghidra
(`AARCH64:LE:64:v8A`), `strings`, Python. Run it with `qemu-aarch64` if you have it.
Without qemu you have to do it fully statically — that's the point.

## Skills practised
- Reading AArch64: `mov`/`movk` constant building, `adr` + `ldr` with scaled
  index, `eor`, `ror`, `madd`, `b.lt`/`b.ne`
- Linux AArch64 syscalls (`x8` = number, 63 read / 64 write / 93 exit)
- Turning a hash loop into a keygen

## Run
```
make -C ../.. all
qemu-aarch64 ../../dist/24-aarch64
```
Not stripped, compiled `-O1`.

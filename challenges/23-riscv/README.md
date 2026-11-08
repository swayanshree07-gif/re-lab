# 23-riscv

## Goal
Find the password that makes the program print `Correct!`.

## Difficulty
★★★☆☆ (45–90 minutes). Small check, unfamiliar instruction set: this binary is
**RISC-V 64** (RV64IM), static, freestanding (no libc, raw `ecall` syscalls).

## Allowed tools
Anything: `file`, `llvm-objdump -d` (GNU objdump on x86 can't read it), Ghidra
(pick `RISCV:LE:64:default`), `strings`, Python.
Run it with `qemu-riscv64` if you have it, otherwise with the lab's own emulator
`tools/rvemu.py` (`-t` prints the instruction count, which may give you ideas).

## Skills practised
- Reading RISC-V: `lui`/`addi` constant building, `lbu`, `mul`, `andi`, branch forms
- Spotting Linux RISC-V syscalls (`a7` = number, 63 read / 64 write / 93 exit)
- Side-channel solving: counting executed instructions per guess

## Run
```
make -C ../.. all
python3 ../../tools/rvemu.py ../../dist/23-riscv     # or: qemu-riscv64 ../../dist/23-riscv
```
Not stripped, compiled `-O1`.

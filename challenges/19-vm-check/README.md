# 19-vm-check

## Goal
Find the password that makes the program print `Correct!`. Like 18, the check
runs inside a small interpreter, but this VM has registers, flags and jumps,
so the bytecode contains a real loop instead of one block per character.

## Difficulty
★★★★☆ (1.5–3 hours). Recover the instruction set (operand encoding matters),
write a disassembler, then understand the loop body. Each character's check
depends on the characters before it.

## Allowed tools
Anything: Ghidra, gdb (+GEF), objdump, Python. Writing your own disassembler
and an emulator for the bytecode is the intended path.

## Skills practised
- Reconstructing a register-machine ISA: register fields packed into one byte, immediates, flags
- Finding loops in bytecode (backward jumps) and the loop-carried state
- Inverting a chained per-character transform, or solving it by emulation

## Run
```
make -C ../.. all
echo guess | ../../dist/19-vm-check
```
Not stripped, compiled `-O0`, dynamically linked.

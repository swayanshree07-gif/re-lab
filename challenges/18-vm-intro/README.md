# 18-vm-intro

## Goal
Find the password that makes the program print `Correct!`. The check is not
written in x86: the binary contains a tiny interpreter, and the real logic is
a blob of bytecode that it runs.

## Difficulty
★★★★☆ (60–120 minutes). The native code is short and boring on purpose. The
work is figuring out what each opcode does, then reading the program it runs.

## Allowed tools
Anything: Ghidra, gdb (+GEF), objdump, Python. Writing your own disassembler
for the bytecode is the intended path.

## Skills practised
- Recognising a fetch–decode–dispatch loop (a `switch` on a byte read via a program counter)
- Reconstructing an instruction set: opcode numbers, operand sizes, stack effects
- Extracting the bytecode from the binary and writing a disassembler
- Inverting simple per-character checks

## Run
```
make -C ../.. all
echo guess | ../../dist/18-vm-intro
```
Not stripped, compiled `-O0`, dynamically linked.

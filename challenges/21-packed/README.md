# 21-packed

## Goal
Find the password that makes the program print `Correct!`. Look for the
check in the disassembly and you won't find it: the program carries its real
code in a form the CPU can't run, and only turns it into code at runtime.

## Difficulty
★★★★☆ (1–3 hours). Two ways in: dump the code while it runs, or write your own
unpacker and work fully statically.

## Allowed tools
Anything: Ghidra, gdb (+GEF), objdump, strace, Python. No third-party
unpackers needed (or useful).

## Skills practised
- Recognising a packer stub (fresh memory, decode loop, permission change, indirect call)
- Dumping runtime-generated code from gdb, or reimplementing the unpacker
- Disassembling a raw code blob (`objdump -b binary`)

## Run
```
make -C ../.. all
echo guess | ../../dist/21-packed
```
Not stripped, stub compiled `-O0`, dynamically linked.

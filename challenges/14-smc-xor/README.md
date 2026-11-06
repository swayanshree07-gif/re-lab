# 14-smc-xor

## Goal
Find the password that makes the program print `Correct!`.

## Difficulty
★★★☆☆ (45–90 minutes).

## Allowed tools
Anything: gdb (+GEF), Ghidra, objdump, strace, ltrace, Python.
Note: the function that checks your password does not look like valid code on
disk. The program fixes that itself, in memory, just before it runs the check.

## Skills practised
- Recognising self-modifying code: a function stored encrypted in `.text` and
  decrypted at runtime (watch for `mprotect` making code pages writable)
- Dumping the real bytes after decryption (dynamically in gdb, or statically by
  reversing the decrypt routine) so a disassembler shows actual instructions
- Spotting a small key hidden inside the encrypted code and searching for it

## Run
```
make -C ../.. all
../../dist/14-smc-xor
```
Not stripped, compiled `-O0`, dynamically linked.

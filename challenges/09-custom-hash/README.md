# 09-custom-hash

## Goal
The program doesn't store the password anywhere, not even encoded: it only keeps a
**hash** of it. Find an input whose hash matches, so the program prints `Correct!`.
The input rules (length, allowed characters) are checked first; read them from the binary.

## Difficulty
★★★☆☆ (60–120 minutes).

## Allowed tools
Anything: gdb (+GEF), Ghidra, objdump, strace, ltrace, Python.
Plain brute force over every possible input is too slow. Look closely at each
step of the hash and ask whether it can be run **backwards**.

## Skills practised
- Recognising a hash loop and well-known constants
- Which operations are invertible (and how to undo them)
- Meet-in-the-middle search

## Run
```
make -C ../.. all
../../dist/09-custom-hash
```
Not stripped, compiled `-O0`, dynamically linked. Your solver should finish in seconds.

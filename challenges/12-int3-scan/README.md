# 12-int3-scan

## Goal
Find the password that makes the program print `Correct!` **when run normally**.

## Difficulty
★★★☆☆ (45–90 minutes).

## Allowed tools
Anything: gdb (+GEF), Ghidra, objdump, strace, ltrace, Python.
Warning: this program reads its own machine code before it checks your input.
Debugging it the usual way may give you an answer that only works inside the
debugger, so always check your answer with a normal run.

## Skills practised
- Seeing how gdb software breakpoints really work (the `int3` / `0xCC` byte),
  and why a program can notice them
- Code that reads its own `.text` section: how to spot it in Ghidra/objdump
- Getting around it: hardware breakpoints, choosing *when* to set a breakpoint,
  or solving it without running it

## Run
```
make -C ../.. all
../../dist/12-int3-scan
```
Not stripped, compiled `-O0`, dynamically linked.

# 11-timing

## Goal
Find the password that makes the program print `Correct!` **when run normally**
(no breakpoints, no single-stepping).

## Difficulty
★★★☆☆ (45–90 minutes).

## Allowed tools
Anything: gdb (+GEF), Ghidra, objdump, strace, ltrace, Python.
Warning: this program notices when it is being slowed down. An answer you find
while paused in a debugger may not work outside it, so always check it with a
normal run.

## Skills practised
- Spotting timing checks (`rdtsc`, `clock_gettime`) in disassembly
- Why breakpoints and single-stepping are detectable, and how to get around
  timing checks (patching, changing memory in gdb, solving statically)
- Telling a decoy path from the real one

## Run
```
make -C ../.. all
../../dist/11-timing
```
Not stripped, compiled `-O0`, dynamically linked.

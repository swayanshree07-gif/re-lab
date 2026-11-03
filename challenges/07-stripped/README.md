# 07-stripped

## Goal
Find the activation code that makes the program print `Correct!`.
Exactly one code works.

## Difficulty
★★★☆☆ (60–90 minutes). The first one with **no symbols**: `nm` says "no symbols", there's no
`main` to break on, and the compiler optimised with `-O2`, so helper functions may be inlined.

## Allowed tools
Anything: `objdump -d`, gdb (+GEF), Ghidra, Python.

## Skills practised
- Finding `main` in a stripped binary (follow `_start` → `__libc_start_main`'s first argument)
- Reading `-O2` code: registers instead of stack slots, inlined helpers, merged compares
- rip-relative data references (`0x2de5(%rip)`) and reading `.data`
- Undoing a 32-bit multiply (hint: the multiplier is odd)

## Run
```
make -C ../.. all
../../dist/07-stripped
```
Stripped, compiled `-O2`, dynamically linked, PIE.

# 26-signals

## Goal
Find the password that makes the program print `Correct!`.

## Difficulty
★★★★☆ (1–2 hours).

## Allowed tools
Anything: Ghidra, gdb (+GEF), objdump, strace, ltrace, Python.
Hint: this program crashes on purpose, many times, and survives. Follow where
control goes after each crash. In gdb you will want to read `help handle`.

## Skills practised
- Reading `sigaction` setup and finding handlers that are never called directly
- `sigsetjmp`/`siglongjmp` as non-local control flow
- Watching signals with `strace` and passing them through in gdb

## Run
```
make -C ../.. all
../../dist/26-signals
```
Not stripped, compiled `-O0`, dynamically linked.

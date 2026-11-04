# 10-ptrace

## Goal
Find the password that makes the program print `Correct!` **when run normally**
(no debugger, no tracer, no preloaded libraries).

## Difficulty
★★★☆☆ (45–90 minutes).

## Allowed tools
Anything: gdb (+GEF), Ghidra, objdump, strace, ltrace, Python.
Warning: this program behaves differently when it's being watched. Don't trust
the first answer you see in a debugger; always check it outside one.

## Skills practised
- Code that runs before `main` (`.init_array`, constructors)
- `ptrace`-based debugger detection and ways around it (patching, changing
  registers or memory in gdb, `LD_PRELOAD`), and why a naive bypass can fail
- Telling a decoy path from the real one

## Run
```
make -C ../.. all
../../dist/10-ptrace
```
Not stripped, compiled `-O0`, dynamically linked.

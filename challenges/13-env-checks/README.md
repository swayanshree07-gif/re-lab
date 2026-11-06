# 13-env-checks

## Goal
Find the password that makes the program print `Correct!` **when run normally**.

## Difficulty
★★★☆☆ (45–90 minutes).

## Allowed tools
Anything: gdb (+GEF), Ghidra, objdump, strace, ltrace, Python.
Warning: this program looks at the environment it runs in before it checks your
input. Running it under a tracer, with library preloading, or from an unusual
parent may give you an answer that only works there. Always confirm with a plain
`./13-env-checks` in a normal shell.

## Skills practised
- How a program detects a debugger without `ptrace`: `TracerPid` in
  `/proc/self/status`, `LD_PRELOAD` / `LD_AUDIT`, the parent process name
- Why raw `syscall` instructions dodge `ltrace` and libc-function hooks
- Finding XOR-encoded strings that are only decoded on the stack at runtime
- Getting around it: set a hardware watchpoint on the flag, patch it, or solve
  statically

## Run
```
make -C ../.. all
../../dist/13-env-checks
```
Not stripped, compiled `-O0`, dynamically linked.

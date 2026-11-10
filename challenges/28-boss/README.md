# 28-boss (final boss, multi-stage)

## Goal
Find the key that makes the program print `Correct!`. The boss has several
stages; the input is one line, stages separated by `|`. There are **three stages**; each one prints a
banner when you clear it.

## Difficulty
★★★★★ (stage 1: 1–3 hours, stage 2: 2–4 hours, stage 3: 1–2 hours).

## Allowed tools
Anything: Ghidra, gdb (+GEF), objdump, strace, ltrace, Python.
Warning: the binary notices when it is being watched, and it won't tell you.

## Skills practised
- Working on a stripped binary: finding `main` from `__libc_start_main`, naming functions yourself
- Defeating combined anti-debug without patching one jump at a time
- Finding where a packed stage is decrypted and what key it needs
- Dumping code that only exists at runtime, then reversing a small custom VM
- Writing a keygen (an SMT solver such as z3 helps, but isn't required)

## Run
```
make -C ../.. all
../../dist/28-boss
```
Stripped, `gcc -O1`, x86-64.

# 28-boss (final boss, multi-stage)

## Goal
Find the key that makes the program print `Correct!`. The boss has several
stages; the input is one line, stages separated by `|`. Right now only
**stage 1** is live (stages 2 and 3 arrive on later days).

## Difficulty
★★★★★ (stage 1 alone: 1–3 hours).

## Allowed tools
Anything: Ghidra, gdb (+GEF), objdump, strace, ltrace, Python.
Warning: the binary notices when it is being watched, and it won't tell you.

## Skills practised
- Working on a stripped binary: finding `main` from `__libc_start_main`, naming functions yourself
- Defeating combined anti-debug without patching one jump at a time
- Finding where a packed stage is decrypted and what key it needs

## Run
```
make -C ../.. all
../../dist/28-boss
```
Stripped, `gcc -O1`, x86-64.

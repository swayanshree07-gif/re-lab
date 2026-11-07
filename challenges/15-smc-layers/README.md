# 15-smc-layers

## Goal
Find the password that makes the program print `Correct!`.

## Difficulty
★★★★☆ (60–120 minutes).

## Allowed tools
Anything: gdb (+GEF), Ghidra, objdump, strace, ltrace, Python.
Note: two separate parts of the program are stored as invalid code on disk and
fixed up in memory at runtime. The second part is only repaired once the
program is happy with the *first few characters* you typed — so dumping it
statically is not enough on its own.

## Skills practised
- Peeling layered self-modifying code: one region decrypted at startup, a
  second region decrypted later with a *different*, input-dependent key
- Recovering a short secret from a one-way hash check (small brute-force space)
- Reproducing a runtime key-derivation routine to decrypt a code region
  offline, so a disassembler shows the real second-stage check

## Run
```
make -C ../.. all
../../dist/15-smc-layers
```
Not stripped, compiled `-O0`, dynamically linked.

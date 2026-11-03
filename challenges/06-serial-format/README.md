# 06-serial-format

## Goal
Find a serial number of the form `XXXX-XXXX-XXXX-XXXX` that makes the program print `Correct!`.
Many serials work. Find one, then write a generator that makes as many as you like.

## Difficulty
★★☆☆☆ (45–75 minutes). The serial is never stored: it's checked piece by piece.

## Allowed tools
Anything: `objdump -d`, gdb (+GEF), Ghidra, Python.
Bonus: a key generator that prints 20 different valid serials.

## Skills practised
- Recognising a character-set lookup (a loop over a table returning an index)
- 2-D arrays on the stack (`v[g][j]` → `base + g*16 + j*4`)
- Weighted checksums and `% 32` (watch for `and $0x1f` and the sign fix-up before it)
- Turning "check" rules into "generate" rules

## Run
```
make -C ../.. all
../../dist/06-serial-format
```
Not stripped, compiled `-O0`, dynamically linked.

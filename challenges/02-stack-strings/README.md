# 02-stack-strings

## Goal
Find the password that makes the program print `Correct!`.

## Difficulty
★☆☆☆☆ (10–20 minutes). Challenge 01's quickest trick won't work here.

## Allowed tools
Anything: `strings`, `ltrace`, `objdump -d`, gdb (+GEF), Ghidra.
Bonus: solve it once purely statically (no running) and once purely dynamically.

## Skills practised
- Reading stack-relative addressing (`-0x14(%rbp)`) and immediates in x86-64
- Turning a sequence of stores back into data
- Dumping memory in gdb (`x/s`, `x/32bx`)

## Run
```
make -C ../.. all
../../dist/02-stack-strings
```
Not stripped, compiled `-O0`, dynamically linked.

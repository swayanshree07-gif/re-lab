# 04-xor-rolling

## Goal
Find the password that makes the program print `Correct!`.

## Difficulty
★★☆☆☆ (30–60 minutes). Brute-forcing one key byte won't help this time:
you need to understand the encoding loop well enough to run it backwards.

## Allowed tools
Anything: `objdump -d`, `nm`, `readelf -s`, gdb (+GEF), Ghidra, Python.
Bonus: find the data blobs through the symbol table (`nm`/`readelf -s`) rather than by scrolling.

## Skills practised
- Reading a loop with an index modulo (`i % n` compiles into a multiply/shift or a `div`)
- Following a value carried from one iteration to the next
- Inverting a transform: undo each step in reverse order
- Locating named data with the symbol table

## Run
```
make -C ../.. all
../../dist/04-xor-rolling
```
Not stripped, compiled `-O0`, dynamically linked.

# 05-math-key

## Goal
Find a license key that makes the program print `Correct!`.
There is no single answer: many keys work. Find one, then find a way to make as many as you like.

## Difficulty
★★☆☆☆ (40–60 minutes). Nothing to dump this time: the key is never stored anywhere.

## Allowed tools
Anything: `objdump -d`, gdb (+GEF), Ghidra, Python.
Bonus: write a key generator that outputs 10 different valid keys.

## Skills practised
- Calls through a table of function pointers (`call *%rdx`)
- Reading arithmetic in assembly: `sub $0x30` (char → digit), `imul`, `div`
- Turning a list of conditions into a search that finishes in under a second

## Run
```
make -C ../.. all
../../dist/05-math-key
```
Not stripped, compiled `-O0`, dynamically linked.

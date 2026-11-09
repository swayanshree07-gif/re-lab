# 25-constraints

## Goal
Find the 16-character password that makes the program print `Correct!`.
The program checks the input against a **table of small rules**, each one relating
one or two characters. No rule tells you a character on its own: you'll have to
solve them all together.

## Difficulty
★★★☆☆ (45–90 minutes).

## Allowed tools
Anything: Ghidra, gdb (+GEF), objdump, nm, Python. A constraint solver (z3) is
the intended tool, but you can also write your own search.

## Skills practised
- Recovering a data table and the meaning of each record from the code that reads it
- Turning code into constraints
- Solving with z3, or by search with propagation

## Run
```
make -C ../.. all
../../dist/25-constraints
```
Not stripped, compiled `-O0`, dynamically linked.

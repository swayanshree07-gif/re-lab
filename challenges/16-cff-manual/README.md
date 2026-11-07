# 16-cff-manual

## Goal
Find the password that makes the program print `Correct!`.

## Difficulty
★★★★☆ (60–120 minutes). The check is small, but its control flow has been
*flattened*: in a graph view it is one big hub that every block jumps back to,
and the blocks are not in any useful order.

## Allowed tools
Anything: Ghidra, gdb (+GEF), objdump, Python. `tools/gdbtrace.py` in this repo
(prints an expression every time a breakpoint is hit) is allowed and useful.

## Skills practised
- Recognising control-flow flattening: dispatcher, state variable, blocks
- Recovering the real order of the blocks, statically (how does each block
  pick its successor?) and dynamically (trace the state variable)
- Rebuilding the original loop from the blocks, then inverting it
- Not trusting every block you see: is it actually reachable?

## Run
```
make -C ../.. all
../../dist/16-cff-manual
```
Not stripped, compiled `-O0`, dynamically linked.

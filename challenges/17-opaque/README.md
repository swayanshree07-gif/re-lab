# 17-opaque

## Goal
Write a **keygen**: given any name (4+ characters), produce the serial that
makes the program print `Correct!`. Input is two lines: name, then serial.

## Difficulty
★★★★☆ (60–120 minutes). The registration code is small, but it is buried in
branches that look meaningful and calls that look important. More than one
function in this binary looks like "the license check". Not all of them run.

## Allowed tools
Anything: Ghidra, gdb (+GEF), objdump, Python. `tools/gdbtrace.py` is allowed.

## Skills practised
- Spotting *opaque predicates*: conditions whose outcome is fixed even though
  the compiler (and the decompiler) can't tell
- Proving which side of a branch is dead (a bit of modular arithmetic helps)
- Ignoring junk code that only writes values nobody reads
- Confirming a static hunch dynamically (which functions are actually hit?)
- Writing a keygen from the cleaned-up algorithm

## Run
```
make -C ../.. all
printf 'alice\nAAAA-BBBB-CCCC-DDDD\n' | ../../dist/17-opaque
```
Not stripped, compiled `-O0`, dynamically linked.

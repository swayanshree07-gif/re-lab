# 03-xor-single

## Goal
Find the password that makes the program print `Correct!`.

## Difficulty
★★☆☆☆ (20–40 minutes). The password is in the binary, but not as readable text.
Watch out for anything that looks too easy.

## Allowed tools
Anything: `strings`, `ltrace`, `objdump -d`, `xxd`, gdb (+GEF), Ghidra, a few lines of Python.
Bonus: write a tiny script that recovers the password without knowing the key in advance.

## Skills practised
- Spotting an XOR decode/encode loop in disassembly (`xor $imm,%eax` / `^` in Ghidra)
- Finding a data blob in `.rodata` and dumping it (`objdump -s -j .rodata`, Ghidra "Copy Special")
- Brute-forcing a tiny keyspace

## Run
```
make -C ../.. all
../../dist/03-xor-single
```
Not stripped, compiled `-O0`, dynamically linked.

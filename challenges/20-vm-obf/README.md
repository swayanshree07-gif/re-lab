# 20-vm-obf

## Goal
Find the password that makes the program print `Correct!`. The check runs in
a register VM again, but the opcode numbers are scrambled and the program
bytes are not stored in plain form.

## Difficulty
★★★★☆+ (2–4 hours). Before you can disassemble anything you have to work out
how the interpreter turns stored bytes into instructions.

## Allowed tools
Anything: Ghidra, gdb (+GEF), objdump, Python. A disassembler plus an
emulator of your own is the intended path.

## Skills practised
- Recovering an opcode mapping from an interpreter's dispatch
- Decrypting data that is only decoded at fetch time
- Reusing (and adapting) tools from earlier challenges

## Run
```
make -C ../.. all
echo guess | ../../dist/20-vm-obf
```
Not stripped, compiled `-O0`, dynamically linked.

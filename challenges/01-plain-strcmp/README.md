# 01-plain-strcmp

## Goal
Find the password that makes the program print `Correct!`.
The binary asks for a password on stdin and answers `Correct!` or `Wrong.`.

## Difficulty
★☆☆☆☆ (first contact: warm-up, 5–15 minutes)

## Allowed tools
Anything: `strings`, `ltrace`, `strace`, `objdump -d`, gdb (+GEF), Ghidra.
Try solving it **three different ways** — it's the easiest place to learn
what each tool shows you.

## Skills practised
- Finding strings in a binary
- Recognising library calls in a disassembly
- Setting a breakpoint on a libc function and reading its arguments

## Run
```
make -C ../.. all
../../dist/01-plain-strcmp
```
Not stripped, compiled `-O0`, dynamically linked.

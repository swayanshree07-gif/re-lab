# 08-keygen-name

## Goal
The program asks for a **name** and a **serial**. Every name has its own serial.
Find the serial for your name, then write a key generator that works for any name
(4–32 printable characters).

## Difficulty
★★☆☆☆ (45–75 minutes).

## Allowed tools
Anything: gdb (+GEF), Ghidra, objdump, strace, ltrace, Python.
Bonus: do it twice — once by "fishing" the serial at runtime, once with a real keygen.

## Skills practised
- Two-line input; following a value from input to a compare
- Recognising rotate, XOR and multiply in a hashing loop
- `sprintf` format strings as a spec for the output

## Run
```
make -C ../.. all
printf 'alice\nXXXXXXXX-XXXX\n' | ../../dist/08-keygen-name
```
Not stripped, compiled `-O0`, dynamically linked.

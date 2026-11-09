# 27-cpp-vtables

## Goal
Find the password that makes the program print `Correct!`.

## Difficulty
★★★☆☆ (45–90 minutes).

## Allowed tools
Anything: Ghidra, gdb (+GEF), objdump, strace, ltrace, `nm -C`, `c++filt`, Python.
Hint: the interesting calls are `call *%rax`/`call *0x10(%rax)`, not named
functions. Work out which class each object really is.

## Skills practised
- Recognising C++ objects in assembly: `this` in `%rdi`, the vtable pointer at offset 0
- Reading vtables and RTTI (`typeinfo for …`) to rebuild a class hierarchy
- Resolving virtual calls by hand or with a gdb breakpoint after `new`

## Run
```
make -C ../.. all
../../dist/27-cpp-vtables
```
Not stripped, compiled `g++ -O0`, dynamically linked against libstdc++.

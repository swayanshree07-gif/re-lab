# 22-antidebug-mix

## Goal
Find the password that makes the program print `Correct!` **when run normally**
(no debugger, no tracer, no preloaded libraries).

## Difficulty
★★★★☆ (1.5–3 hours).

## Allowed tools
Anything: gdb (+GEF), Ghidra, objdump, strace, ltrace, Python.
Warning: this program notices being watched in more than one way, and it never
tells you. There is no "debugger detected" branch to patch: it just quietly
computes a different answer.

## Skills practised
- Spotting several anti-debug checks (some before `main`) and seeing how their
  results flow into the data instead of into a jump
- Software vs. hardware breakpoints and what an `int3` does to code bytes
- Solving statically when dynamic analysis is unreliable

## Run
```
make -C ../.. all
../../dist/22-antidebug-mix
```
Not stripped, compiled `-O0`, dynamically linked.

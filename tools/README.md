# tools/

| File | What it does |
|---|---|
| `run_tests.py` | `make test`: runs every `challenges/NN/solve.py` against `dist/NN`, plus a generic wrong-input check (`""`, a wrong word, 200×`A` must all exit 1). `tools/run_tests.py 16-cff-manual` runs just one. |
| `lint.py` | `make lint`: every challenge has `src/ Makefile README.md solve.py src/SPOILERS`, the README has the Goal / Difficulty / Allowed tools sections and leaks no line of `SPOILERS`; warns if the desk writeup is missing. |
| `crackme.py` | Shared helpers for solvers: `run()` / `accepted()` (stdin in, verdict out), `printable_strings()` (like `strings`), and a dependency-free ELF64 reader `Elf` (`section_bytes`, `symbols`, `symbol_bytes`, `read_vaddr`). |
| `gdbtrace.py` | Value tracer (Day 11): runs a binary under `gdb -batch` with given stdin and prints an expression every time a location is hit. Made for flattened code (break on the dispatcher, print the state variable), works for any "what does X look like each time we get here" question. `--hw` uses a hardware breakpoint (needed for 12-int3-scan / SMC targets). |
| `ghidra_dump.sh <bin> [out]` + `ghidra/DumpAll.java` | Ghidra-headless dump (functions, strings, decompiled C) to `dist/ghidra/<name>.txt`. Needs a JDK ≥ 25 for Ghidra 12.2 (set `JAVA_HOME`). `make ghidra-test` (`ghidra_test.sh`) checks the dump of 01, or prints SKIP. |
| `new-challenge.sh NN-name` | Scaffolds `challenges/NN-name/` with Makefile, stub `main.c`, SPOILERS, README brief and solver stub. |

## gdbtrace examples
```
# order of the blocks of 16-cff-manual for some input
tools/gdbtrace.py dist/16-cff-manual '*check+0x4f' '*(unsigned*)($rbp-0x24)' --input abc
# from Python (used by challenges/16-cff-manual/solve.py)
import gdbtrace; states = gdbtrace.trace(binary, "*check+0x4f", "$eax", "input")
```
gdb is run from a command file, one command per line (multi-line `-ex`
arguments hang gdb). The program's prompt can share a line with the first
`TRACE` print, so output is matched with a regex, not by line start.

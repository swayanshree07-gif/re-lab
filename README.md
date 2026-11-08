# re-lab — a self-made reverse engineering course

About 27 original, harmless Linux crackmes that get steadily harder, built to
practise with Ghidra, gdb (+GEF), objdump, strace and ltrace. Path: plain string
compare → stack strings → XOR → math keys → stripped binaries → keygens →
anti-debug → self-modifying code → hand-made control-flow flattening → custom VM →
multi-stage final boss. The day-by-day plan is in [PLAN.md](PLAN.md), the log in
[PROGRESS.md](PROGRESS.md).

Every crackme reads one line (08: two lines, name then serial) from stdin and prints `Correct!` (exit 0) or `Wrong.`
(exit 1). No networking, no files touched, nothing persistent.

## Build and test
```
make all     # build every challenge into dist/ (git-ignored)
make test    # builds, then runs each solve.py + a wrong-input check
make lint    # required files present, README briefs leak no spoilers
make check   # test + lint
make clean
```
Requires `gcc`, `make`, `python3`, `objdump` (binutils). The 10-ptrace, 11-timing and
12-int3-scan, 16-cff-manual and 17-opaque tests also use `gdb` (and 10 uses `strace`) when installed (skipped otherwise).

## Play
```
make all
./dist/01-plain-strcmp
```
Read only `challenges/NN-name/README.md` (the brief). **Spoilers:** `src/`, `solve.py`.
Full writeups live outside this repo, in the owner's desk
(`~/Personal-Desk/06-security/reverse-engineering/re-lab/notes/`).

## Layout
```
challenges/NN-name/
  README.md     brief: goal, difficulty, allowed tools (no spoilers)
  Makefile      builds $(DIST)/NN-name
  src/          source (spoiler) + SPOILERS (secret strings, used by lint)
  solve.py      automated solver = the test
tools/
  run_tests.py  test runner (make test)
  lint.py       structure/spoiler lint (make lint)
  crackme.py    helpers shared by solvers (run/accepted, strings, tiny ELF64 reader:
                sections, symbols, bytes at a vaddr)
  gdbtrace.py   gdb value tracer: print an expression on every breakpoint hit
                (dispatcher state traces for flattened code; --hw option)
  new-challenge.sh NN-name   scaffold a new challenge
  README.md     what each tool does, with examples
```

## Status
| # | Challenge | Topic | Status |
|---|---|---|---|
| 01 | 01-plain-strcmp | password in `.rodata`, `strcmp`, decoys | ✅ built + solver passes |
| 02 | 02-stack-strings | password built byte-by-byte on the stack, custom compare | ✅ built + solver passes |
| 03 | 03-xor-single | single-byte XOR blob in `.rodata`, decoy string | ✅ built + solver passes |
| 04 | 04-xor-rolling | 5-byte repeating XOR key + chained add | ✅ built + solver passes |
| 05 | 05-math-key | 12-digit key, six arithmetic rules via function-pointer table | ✅ built + keygen/fuzz solver passes |
| 06 | 06-serial-format | `XXXX-XXXX-XXXX-XXXX` serial, weighted check chars, keygen | ✅ built + keygen/model solver passes |
| 07 | 07-stripped | stripped `-O2`, constants in `.data`, modular inverse | ✅ built + solver (parses stripped disassembly) passes |
| 08 | 08-keygen-name | name → serial (rotl/xor/imul hash), two-line input, keygen | ✅ built + keygen solver passes |
| 09 | 09-custom-hash | 64-bit invertible hash, meet-in-the-middle preimage | ✅ built + MITM solver passes (< 1 s) |
| 10 | 10-ptrace | constructor + double `PTRACE_TRACEME`, silent decoy under a debugger | ✅ built + solver/anti-debug tests pass |
| 11 | 11-timing | `rdtsc` + `clock_gettime` timing window, silent decoy when slowed down | ✅ built + solver/gdb timing tests pass |
| 12 | 12-int3-scan | self-hash of its own `.text` region + `0xCC` count, decoy under software breakpoints; post-link hash patch | ✅ built + solver/gdb breakpoint tests pass |
| 13 | 13-env-checks | TracerPid + LD_PRELOAD/LD_AUDIT + parent `comm` checks via raw syscalls, decoy path | ✅ built + solver/anti-debug tests pass |
| 14 | 14-smc-xor | `verify()` XOR-encrypted in `.text`, self-decrypted at runtime via `mprotect`; 1-byte inner key | ✅ built + solver passes |
| 15 | 15-smc-layers | layered SMC: layer 1 static key, layer 2 key derived from the password prefix (FNV-1a gate) | ✅ built + solver passes |
| 16 | 16-cff-manual | hand-made control-flow flattening: random state ids, XOR-delta transitions, branchless edges, dead junk states | ✅ built + solver (static CFG recovery + gdb dispatcher trace) passes |
| 17 | 17-opaque | name/serial keygen behind opaque predicates, junk calls, decoy license checks | ✅ built + keygen solver (gdb confirms decoys never run) passes |
| 18 | 18-vm-intro | tiny stack VM runs bytecode that checks the password | ✅ built + solver with bytecode disassembler passes |
| 19 | 19-vm-check | 8-register VM with loops checks the password | ✅ built + solver (disassembler + emulator) passes |
| 20 | 20-vm-obf | register VM with shuffled opcodes + encrypted bytecode | ✅ built + solver (opcode-map recovery, decrypt, reuse 19 emulator) passes |
| 21 | 21-packed | hand-written packer (LZ77 + LCG-XOR), code unpacked into an mmap page | ✅ built + static-unpacker solver passes |
| 22–28 | see PLAN.md | anti-debug mix, RISC-V, AArch64, z3 constraints, signals, C++, boss | planned (PLAN.md Days 17–27 rewritten on Day 16 for the extended goals) |

**Ghidra headless:** `tools/ghidra_dump.sh <binary>` dumps functions, strings and decompiled C; `make ghidra-test` checks it. Currently it skips: Ghidra 12.2 needs JDK 25, and only JDK 21 is installed.

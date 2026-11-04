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
Requires `gcc`, `make`, `python3`, `objdump` (binutils). The 10-ptrace test also
uses `gdb` and `strace` when they are installed (skipped otherwise).

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
  new-challenge.sh NN-name   scaffold a new challenge
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
| 11–27 | see PLAN.md | | planned (10 of 27 done on Day 5: five days ahead of PLAN.md) |

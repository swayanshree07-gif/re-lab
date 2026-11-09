#!/usr/bin/env python3
"""Solver + signal test (spoiler!). Usage: solve.py <binary>

Reads `kinds` and `expect` from the symbol table, replays the three handler
mixes (src/model.py, which mirrors the disassembly) and brute-forces each
byte left to right: exactly one printable char must match bits 8..23 of the
state. Then checks: password accepted, near misses rejected, password not in
strings, and (if strace exists) the run raises the exact SIGSEGV/SIGFPE/SIGILL
sequence given by `kinds`.
"""
import os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "src"))
import crackme  # noqa: E402
from model import step, SEED  # noqa: E402

NAMES = ["SIGSEGV", "SIGFPE", "SIGILL"]


def main(binary):
    elf = crackme.Elf(binary)
    kinds = list(elf.symbol_bytes("kinds"))
    e = elf.symbol_bytes("expect")
    expect = [int.from_bytes(e[i:i + 2], "little") for i in range(0, len(e), 2)]
    h, pw = SEED, ""
    for k, want in zip(kinds, expect):
        hits = [c for c in range(0x21, 0x7f) if (step(k, h, c) >> 8) & 0xffff == want]
        if len(hits) != 1:
            print("position", len(pw), "candidates", hits); return 1
        h = step(k, h, hits[0]); pw += chr(hits[0])
    problems = []
    if not crackme.accepted(binary, pw):
        problems.append(f"{pw!r} rejected")
    for i in (0, len(pw) // 2, len(pw) - 1):
        bad = pw[:i] + chr(ord(pw[i]) ^ 1) + pw[i + 1:]
        if crackme.accepted(binary, bad):
            problems.append(f"near miss {bad!r} accepted")
    if crackme.accepted(binary, pw[:-1]):
        problems.append("short input accepted")
    if pw in crackme.printable_strings(open(binary, "rb").read()):
        problems.append("password in strings")
    if shutil.which("strace"):
        p = subprocess.run(["timeout", "30", "strace", "-e", "trace=none", binary],
                           input=(pw + "\n").encode(), stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        seen = re.findall(r"--- (SIG[A-Z]+) ", p.stderr.decode())
        if seen != [NAMES[k] for k in kinds]:
            problems.append(f"strace signals {seen} != kinds")
    else:
        print("NOTICE: strace missing, signal sequence not checked")
    for p in problems:
        print(p)
    if problems:
        return 1
    print(f"password={pw!r}; {len(kinds)} faults "
          f"({', '.join(f'{kinds.count(i)} {n}' for i, n in enumerate(NAMES))}) seen in strace")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

#!/usr/bin/env python3
"""Automated solver (spoiler!). Usage: solve.py <binary>

The binary is a static RV64IM ELF, so it runs under tools/rvemu.py (or
qemu-riscv64). Approach: instruction-count side channel, like a pintool
attack. The check exits at the first wrong byte, so a longer run means more
correct bytes:
  1. length: try 1..64 filler chars; the one that gets past the length test
     executes more instructions;
  2. each position: try every printable char, keep the one with the highest
     count (the last one is confirmed by the exit code).
No knowledge of the algorithm or table is used. Then checks the answer
through crackme.run (qemu if installed, else rvemu), checks near misses,
and that the password isn't in the file.
"""
import os, string, sys
TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools")
sys.path.insert(0, TOOLS)
import crackme, rvemu  # noqa: E402

CHARSET = string.ascii_letters + string.digits + "_-!?{}@#$."


def count(binary, s):
    rc, out, n = rvemu.run(binary, s.encode() + b"\n", max_steps=200_000)
    return rc, n


def main(binary):
    runs = 0
    lens = {}
    for L in range(1, 65):
        lens[L] = count(binary, "A" * L)[1]
        runs += 1
    # reading costs a fixed number of insns per char; subtract that trend
    steps = sorted(lens[L + 1] - lens[L] for L in range(1, 64))
    per = steps[len(steps) // 2]
    excess = {L: n - per * L for L, n in lens.items()}
    base = sorted(excess.values())[len(excess) // 2]
    longer = [L for L, e in excess.items() if e > base + 4]
    if len(longer) != 1:
        print(f"length not found clearly: {longer}")
        return 1
    L = longer[0]
    print(f"length {L} (+{excess[L] - base} insns over the trend)")
    pw = ""
    for i in range(L):
        best = None
        for c in CHARSET:
            cand = pw + c + "A" * (L - i - 1)
            rc, n = count(binary, cand)
            runs += 1
            if rc == 0:
                best = (1 << 62, c)
                break
            if best is None or n > best[0]:
                best = (n, c)
        pw += best[1]
    print(f"password: {pw}  ({runs} emulated runs)")
    ok = crackme.accepted(binary, pw)
    near = [pw[:-1], pw + "x", pw[:-1] + chr(ord(pw[-1]) ^ 1), chr(ord(pw[0]) ^ 1) + pw[1:]]
    bad = [n for n in near if crackme.accepted(binary, n)]
    leaked = pw.encode() in open(binary, "rb").read()
    print(f"accepted={ok} near-misses-accepted={bad} plain-in-file={leaked} "
          f"launcher={os.path.basename(crackme.launcher(binary)[0])}")
    return 0 if ok and not bad and not leaked else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

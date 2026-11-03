#!/usr/bin/env python3
"""Keygen (spoiler!). Usage: solve.py <binary>

The seed and multiplier are read from the disassembly of make_serial
(`movl $imm,-0x..(%rbp)` and `imul $imm`); rotate/xor/sum are modelled.
Test: keygen serials accepted for 50 random names; a one-char-off serial,
a too-short name and a serial for a different name are rejected.
"""
import os, random, re, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402

M32 = 0xFFFFFFFF


def constants(binary):
    asm = subprocess.run(["objdump", "-d", "--no-show-raw-insn", binary],
                         stdout=subprocess.PIPE, text=True, check=True).stdout
    body = asm.split("<make_serial>:")[1].split("\n\n")[0]
    seed = int(re.search(r"movl\s+\$0x([0-9a-f]+),-0x[0-9a-f]+\(%rbp\)", body).group(1), 16)
    mul = int(re.search(r"imul\s+\$0x([0-9a-f]+)", body).group(1), 16)
    return seed, mul


def keygen(name, seed, mul):
    h, s = seed, 0
    for c in name.encode():
        h = ((h << 5) | (h >> 27)) & M32
        h = ((h ^ c) * mul) & M32
        s += c
    return f"{h:08X}-{(s * len(name)) & 0xFFFF:04X}"


def main(binary):
    seed, mul = constants(binary)
    rng = random.Random(8)
    alpha = "".join(chr(i) for i in range(0x20, 0x7f))
    names = ["alice", "Swayanshree"] + ["".join(rng.choice(alpha) for _ in range(rng.randint(4, 32)))
                                        for _ in range(48)]
    for n in names:
        if not crackme.accepted(binary, n + "\n" + keygen(n, seed, mul)):
            print("keygen serial rejected for", repr(n))
            return 1
    good = keygen("alice", seed, mul)
    bad = [("alice", good[:-1] + ("0" if good[-1] != "0" else "1")),
           ("abc", keygen("abc", seed, mul)), ("bob1", good)]
    for n, s in bad:
        if crackme.accepted(binary, n + "\n" + s):
            print("wrong pair accepted:", n, s)
            return 1
    print(f"seed={seed:#x} mul={mul:#x}; alice -> {good}; 50 names accepted, 3 bad pairs rejected")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

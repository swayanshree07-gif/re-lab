#!/usr/bin/env python3
"""Meet-in-the-middle preimage solver (spoiler!). Usage: solve.py <binary>

Constants are parsed from objdump: seed and multiplier (the two `movabs` in
hash64), rotate amount (`mov $imm,%esi`, the second argument of rotl64), final xorshift
(`shr $imm`), target (`movabs` in main) and length (`cmpq $imm` in main).
Every hash step is invertible, so: 26^(n/2) forward states from the seed,
26^(n/2) backward states from the target, intersect.
Test: the found password is accepted, one-letter mutants and an upper-case
variant are rejected, the password is not in `strings`, and it runs < 10 s.
"""
import os, re, subprocess, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402

M64 = (1 << 64) - 1
ALPHA = b"abcdefghijklmnopqrstuvwxyz"


def func(asm, name):
    return asm.split(f"<{name}>:")[1].split("\n\n")[0]


def constants(binary):
    asm = subprocess.run(["objdump", "-d", "--no-show-raw-insn", binary],
                         stdout=subprocess.PIPE, text=True, check=True).stdout
    h = func(asm, "hash64")
    seed, mul = (int(x, 16) for x in re.findall(r"movabs\s+\$0x([0-9a-f]+)", h)[:2])
    rot = int(re.search(r"mov\s+\$0x([0-9a-f]+),%esi", h).group(1), 16)
    shr = int(re.search(r"shr\s+\$0x([0-9a-f]+)", h).group(1), 16)
    m = func(asm, "main")
    target = int(re.search(r"movabs\s+\$0x([0-9a-f]+)", m).group(1), 16)
    length = int(re.search(r"cmpq\s+\$0x([0-9a-f]+),", m).group(1), 16)
    return seed, mul, rot, shr, target, length


def solve(seed, mul, rot, shr, target, length):
    inv = pow(mul, -1, 1 << 64)
    half = length // 2
    # forward: state after `half` chars -> prefix
    fwd = {seed: b""}
    for _ in range(half):
        nxt = {}
        for h, p in fwd.items():
            r = ((h << rot) | (h >> (64 - rot))) & M64
            for c in ALPHA:
                nxt[((r ^ c) * mul) & M64] = p + bytes([c])
        fwd = nxt
    # undo final xorshift: x = y ^ y>>s ^ y>>2s ...
    x, y = 0, target
    while y:
        x ^= y
        y >>= shr
    # backward: state before the last `length-half` chars -> suffix
    bwd = {x: b""}
    for _ in range(length - half):
        nxt = {}
        for h, s in bwd.items():
            t = (h * inv) & M64
            for c in ALPHA:
                u = t ^ c
                nxt[((u >> rot) | (u << (64 - rot))) & M64] = bytes([c]) + s
        bwd = nxt
    return sorted((fwd[k] + bwd[k]).decode() for k in fwd.keys() & bwd.keys())


def main(binary):
    t0 = time.time()
    k = constants(binary)
    found = solve(*k)
    dt = time.time() - t0
    if not found:
        print("no preimage found")
        return 1
    pw = found[0]
    if not crackme.accepted(binary, pw):
        print("found preimage rejected:", pw)
        return 1
    if pw in crackme.printable_strings(open(binary, "rb").read()):
        print("password visible in strings")
        return 1
    bad = [pw.upper(), pw[:-1], pw + "a"] + \
          [pw[:i] + ("a" if pw[i] != "a" else "b") + pw[i + 1:] for i in range(len(pw))]
    for b in bad:
        if crackme.accepted(binary, b):
            print("mutant accepted:", b)
            return 1
    if dt > 10:
        print(f"too slow: {dt:.1f} s")
        return 1
    print(f"seed={k[0]:#x} mul={k[1]:#x} rot={k[2]} shr={k[3]} target={k[4]:#x} len={k[5]}; "
          f"preimages={found} in {dt:.2f} s; {len(bad)} mutants rejected")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

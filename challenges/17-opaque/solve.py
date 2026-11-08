#!/usr/bin/env python3
"""Keygen (spoiler!). Usage: solve.py <binary>

make_serial() is a keygen wrapped in opaque predicates + junk calls. Once the
opaque branches are resolved (x*(x+1) even, x*x mod 4 < 2, 7y^2-1 != x^2), the
live path is:
    h = K[0]; for i,c: h = (h^c)*K[1]; h ^= h>>15; s += c*(i+1)
    a = h; b = rotl(h,13)^K[2]; c = (s*len)^K[3]
    serial = %04X-%04X-%04X-%04X of a>>16, b&0xffff, c&0xffff, (a^b^c)>>16
K[] is read from the symbol table.
Tests: 30 random names accepted; near-miss / swapped / short-name pairs and
the decoy validate_license() serial rejected; if gdb is present, the decoy
functions are never hit while make_serial is hit once.
"""
import os, random, shutil, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402
import gdbtrace  # noqa: E402

M = 0xFFFFFFFF


def rotl(v, r):
    return ((v << r) | (v >> (32 - r))) & M


def keygen(name, K):
    h, s = K[0], 0
    for i, c in enumerate(name.encode()):
        h = ((h ^ c) * K[1]) & M
        h ^= h >> 15
        s = (s + c * (i + 1)) & M
    a = h
    b = rotl(h, 13) ^ K[2]
    c = ((s * len(name)) & M) ^ K[3]
    return "%04X-%04X-%04X-%04X" % (a >> 16, b & 0xFFFF, c & 0xFFFF, ((a ^ b ^ c) >> 16))


def decoy_serial(name, K):
    h = 0x811C9DC5
    for c in name.encode():
        h = ((h ^ c) * 16777619) & M
    return "%08X-%08X" % (h, h ^ K[2])


def hits(binary, fn, stdin):
    try:
        return len(gdbtrace.trace(binary, fn, "1", stdin))
    except RuntimeError as e:
        if "never hit" in str(e):
            return 0
        raise


def main(binary):
    elf = crackme.Elf(binary)
    addr, size = elf.symbols()["K"]
    K = struct.unpack("<4I", elf.read_vaddr(addr, 16))
    rng = random.Random(17)
    alpha = "".join(chr(i) for i in range(0x21, 0x7f))
    names = ["alice", "Swayanshree"] + ["".join(rng.choice(alpha) for _ in range(rng.randint(4, 40)))
                                        for _ in range(28)]
    for n in names:
        if not crackme.accepted(binary, n + "\n" + keygen(n, K)):
            print("keygen serial rejected for", repr(n))
            return 1
    good = keygen("alice", K)
    last = good[-1]
    bad = [("alice", good[:-1] + ("0" if last != "0" else "1")),
           ("alicf", good), ("abc", keygen("abc", K)),
           ("alice", decoy_serial("alice", K)),
           ("alice", "PRO-%08X-LIC" % (K[0] ^ 0xDEADBEEF))]
    for n, s in bad:
        if crackme.accepted(binary, n + "\n" + s):
            print("wrong pair accepted:", n, s)
            return 1
    msg = f"K={[hex(k) for k in K]}; alice -> {good}; 30 names ok, {len(bad)} bad/decoy pairs rejected"
    if shutil.which("gdb"):
        inp = "alice\n" + good
        hv = {f: hits(binary, f, inp) for f in ("make_serial", "validate_license", "pro_check")}
        if hv != {"make_serial": 1, "validate_license": 0, "pro_check": 0}:
            print("unexpected gdb hit counts:", hv)
            return 1
        msg += f"; gdb hits {hv}"
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

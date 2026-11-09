#!/usr/bin/env python3
"""Solver for 28-boss stage 1 (spoiler!). Usage: solve.py <binary>

The binary is stripped, so the tables are found by shape, not by symbol:
  1. .rodata: an S1_LEN-byte window that is a permutation of 0..n-1 is s1_perm;
     every other n-byte window is a candidate for s1_ct.
  2. The keystream seed is a 32-bit immediate in .text (at -O1 gcc folds it into `xor $imm` with the first salt);
     all immediates are tried.
  3. Clean-run salts are 0, so state = mix^3(seed, 0); undo the xorshift
     keystream and the permutation. A candidate wins if it is printable.
Then: run it (stage 1 clear + Correct!), near misses rejected, key not in
strings, and the anti-debug salts really change the result under strace."""
import os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402

M = 0xFFFFFFFF


def mix(s, v):
    s = ((s ^ v) * 0x9E3779B1) & M
    return ((s << 13) | (s >> 19)) & M


def recover(seed, perm, ct):
    s = seed
    for _ in range(3):
        s = mix(s, 0)
    out = [0] * len(perm)
    for i in range(len(perm)):
        s ^= (s << 13) & M; s ^= s >> 17; s ^= (s << 5) & M
        out[perm[i]] = ct[i] ^ ((s + 13 * i) & 0xFF)
    return bytes(out)


def main(binary):
    elf = crackme.Elf(binary)
    problems = []
    if elf.section(".symtab") is not None:
        problems.append("binary is not stripped")
    ro = elf.section_bytes(".rodata")
    asm = subprocess.run(["objdump", "-d", "-j", ".text", binary], stdout=subprocess.PIPE,
                         check=True).stdout.decode()
    imms = {int(x, 16) for x in re.findall(r"\$0x([0-9a-f]{7,8}),%e", asm)}
    found = set()
    for n in range(8, 33):
        perms = [o for o in range(len(ro) - n + 1) if sorted(ro[o:o + n]) == list(range(n))]
        for po in perms:
            perm = list(ro[po:po + n])
            for co in range(len(ro) - n + 1):
                if co == po:
                    continue
                ct = ro[co:co + n]
                for seed in imms:
                    pw = recover(seed, perm, ct)
                    if all(0x21 <= c < 0x7F and c != ord("|") for c in pw):
                        found.add((pw.decode(), seed, n, po, co))
    print(f"{len(imms)} immediates, candidates: {[(f[0], hex(f[1])) for f in found]}")
    good = [f for f in found if crackme.accepted(binary, f[0])]
    if len(good) != 1:
        print("expected exactly one working stage-1 key")
        return 1
    pw, seed, n, po, co = good[0]
    print(f"stage 1 key {pw!r} (seed 0x{seed:08x}, perm @.rodata+{po:#x}, ct @.rodata+{co:#x})")
    rc, out = crackme.run(binary, pw)
    if "Stage 1 clear." not in out:
        problems.append("stage 1 banner missing")
    for bad in (pw[:-1], pw + "x", pw[:-1] + chr(ord(pw[-1]) ^ 1), pw[1:] + pw[0]):
        if crackme.accepted(binary, bad):
            problems.append(f"near miss accepted: {bad!r}")
    if pw in crackme.printable_strings(elf.data):
        problems.append("key visible in strings")
    if shutil.which("strace"):
        p = subprocess.run(["strace", "-o", os.devnull, binary], input=(pw + "\n").encode(),
                           stdout=subprocess.PIPE, timeout=30)
        if p.returncode == 0:
            problems.append("anti-debug: correct key still accepted under strace")
        else:
            print("under strace: rejected as intended")
    for p in problems:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

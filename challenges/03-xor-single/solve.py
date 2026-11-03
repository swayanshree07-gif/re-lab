#!/usr/bin/env python3
"""Automated solver (spoiler!). Usage: solve.py <binary>

Approach (no knowledge of the key or the blob location): take the raw
.rodata section, XOR it with every key 1..255, and look for runs that decode
to a plausible password ([A-Za-z0-9_]{8,}) terminated by a NUL
(00 bytes such as alignment padding decode to chr(key), so they act as
separators). Try every
candidate against the binary, best-looking first. Also checks that the
plaintext password is not present in the file.
"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402

CAND = re.compile(rb"[A-Za-z0-9_]{8,64}(?=\0)")


def main(binary):
    elf = crackme.Elf(binary)
    rodata = elf.section_bytes(".rodata")
    plain_strings = set(crackme.printable_strings(rodata))
    cands = []
    for key in range(1, 256):
        dec = bytes(b ^ key for b in rodata)
        for m in CAND.finditer(dec):
            # 00 bytes (padding, other data) decode to chr(key): treat them as
            # separators and keep what follows the last one
            s = m.group().decode().rsplit(chr(key), 1)[-1]
            if len(s) < 8:
                continue
            if s in plain_strings:  # already readable without XOR: decoy/prompt
                continue
            # score: mix of letters+digits+underscore looks like a leet password
            score = sum(c.islower() for c in s) + 2 * any(c.isdigit() for c in s) \
                + 2 * ("_" in s)
            cands.append((score, key, s))
    cands.sort(reverse=True)
    for tries, (_, key, s) in enumerate(cands, 1):
        if crackme.accepted(binary, s):
            if s.encode() in elf.data:
                print("password appears as plain bytes in the binary: challenge is broken")
                return 1
            print(f"password: {s}  (key {key:#04x}, {tries}/{len(cands)} candidates tried)")
            return 0
    print(f"no candidate accepted ({len(cands)} tried)")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

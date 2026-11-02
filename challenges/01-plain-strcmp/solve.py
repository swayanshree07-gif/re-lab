#!/usr/bin/env python3
"""Automated solver (spoiler!). Usage: solve.py <binary>

Approach: the password is a plain string in the binary, so pull every
printable string out of the file (like `strings`) and try each one.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402


def main(binary):
    data = open(binary, "rb").read()
    candidates = [s for s in crackme.printable_strings(data, 4) if " " not in s]
    for cand in candidates:
        if crackme.accepted(binary, cand):
            print(f"password: {cand}  (tried {candidates.index(cand) + 1}/{len(candidates)} strings)")
            return 0
    print(f"no candidate accepted out of {len(candidates)}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

#!/usr/bin/env python3
"""Solver + vtable test (spoiler!). Usage: solve.py <binary>

Reads `stage_params` (kind, a, b, target[4] per stage) from the symbol table,
inverts each stage's transform (src/model.py mirrors the four transform()
overrides) and checks: password accepted, near misses in every stage
rejected, password not in strings, and `nm -C` lists the five vtables plus
the typeinfo that shows MulStage derives from AddStage.
"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "src"))
import crackme  # noqa: E402
from model import inv, NAMES  # noqa: E402

CLASSES = ["Stage", "RotStage", "AddStage", "XorStage", "MulStage"]


def main(binary):
    raw = crackme.Elf(binary).symbol_bytes("stage_params")
    rows = [raw[i:i + 7] for i in range(0, len(raw), 7)]
    pw = bytes(b for r in rows for b in inv(r[0], r[1], r[2], list(r[3:7]))).decode()
    problems = []
    if not crackme.accepted(binary, pw):
        problems.append(f"{pw!r} rejected")
    for s in range(len(rows)):
        i = 4 * s + s % 4
        bad = pw[:i] + chr(ord(pw[i]) ^ 2) + pw[i + 1:]
        if crackme.accepted(binary, bad):
            problems.append(f"near miss {bad!r} accepted")
    if crackme.accepted(binary, pw + "x"):
        problems.append("long input accepted")
    if pw in crackme.printable_strings(open(binary, "rb").read()):
        problems.append("password in strings")
    nm = subprocess.run(["nm", "-C", binary], capture_output=True, text=True).stdout
    for c in CLASSES:
        if f"vtable for {c}\n" not in nm:
            problems.append(f"no vtable for {c}")
    # RTTI: MulStage's typeinfo is an __si_class_type_info whose base is AddStage
    if "typeinfo for MulStage" not in nm:
        problems.append("no typeinfo for MulStage")
    for p in problems:
        print(p)
    if problems:
        return 1
    print(f"password={pw!r}; stages: {', '.join(NAMES[r[0]] for r in rows)}; "
          f"{len(CLASSES)} vtables in nm")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

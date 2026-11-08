#!/usr/bin/env python3
"""Solver (spoiler!). Usage: solve.py <binary>

Reads the `bytecode` symbol from the ELF, disassembles it with a small
disassembler for the 18-vm-intro ISA, then recovers the password by
pattern-matching each `LOAD i; PUSH k; XOR|ADD|SUB; PUSH v; EQ; AND` block and
inverting the op. Tests: password accepted, near misses rejected, password not
visible to `strings`.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402

OPS = {1: ("PUSH", 1), 2: ("LOAD", 1), 3: ("XOR", 0), 4: ("ADD", 0), 5: ("SUB", 0),
       6: ("EQ", 0), 7: ("AND", 0), 8: ("JZ", 1), 9: ("LEN", 0), 10: ("HALT", 0),
       11: ("DUP", 0), 12: ("POP", 0)}


def disasm(code):
    pc, out = 0, []
    while pc < len(code):
        name, nargs = OPS.get(code[pc], ("DB 0x%02x" % code[pc], 0))
        args = list(code[pc + 1:pc + 1 + nargs])
        out.append((pc, name, args))
        pc += 1 + nargs
    return out


def solve(ins):
    names = [n for _, n, _ in ins]
    length = ins[1][2][0] if names[:4] == ["LEN", "PUSH", "EQ", "JZ"] else None
    pw = {}
    for j in range(len(ins) - 5):
        w = ins[j:j + 6]
        if [x[1] for x in w] == ["LOAD", "PUSH", w[2][1], "PUSH", "EQ", "AND"] and w[2][1] in ("XOR", "ADD", "SUB"):
            i, k, v = w[0][2][0], w[1][2][0], w[3][2][0]
            pw[i] = {"XOR": v ^ k, "ADD": (v - k) & 0xFF, "SUB": (v + k) & 0xFF}[w[2][1]]
    assert length is not None and sorted(pw) == list(range(length)), (length, pw)
    return bytes(pw[i] for i in range(length)).decode()


def main(binary):
    code = crackme.Elf(binary).symbol_bytes("bytecode")
    ins = disasm(code)
    if "-v" in sys.argv:
        for pc, n, a in ins:
            print("%04x  %-5s %s" % (pc, n, " ".join("0x%02x" % x for x in a)))
    pw = solve(ins)
    if not crackme.accepted(binary, pw + "\n"):
        print("recovered password rejected:", pw); return 1
    for bad in (pw[:-1], pw + "x", pw[:-1] + chr(ord(pw[-1]) ^ 1), chr(ord(pw[0]) ^ 1) + pw[1:], ""):
        if crackme.accepted(binary, bad + "\n"):
            print("near miss accepted:", repr(bad)); return 1
    if any(pw in s for s in crackme.printable_strings(open(binary, "rb").read())):
        print("password visible to strings"); return 1
    print(f"OK: {len(code)} bytes, {len(ins)} insns disassembled; password {pw!r} accepted, 5 near misses rejected")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

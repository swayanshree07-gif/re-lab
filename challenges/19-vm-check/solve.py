#!/usr/bin/env python3
"""Solver (spoiler!). Usage: solve.py <binary> [-v]

Reads the `bytecode` and `vmdata` symbols, disassembles the register-VM
program, then *emulates* it in Python. The loop ORs a per-character error into
one register and h depends on earlier chars, so we recover the password one
char at a time: for position i, try every byte and keep the one for which the
error register is still 0 after the i-th trip round the loop (emulator trace).
Tests: password accepted, near misses rejected, not visible to `strings`.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402

# opcode -> (name, operand bytes, kind) kind: "rr" packed regs, "ri" reg+imm, "r" reg, "a" addr
OPS = {0x10: ("MOVI", "ri"), 0x11: ("MOV", "rr"), 0x12: ("LDI", "rr"), 0x13: ("LDM", "rr"),
       0x20: ("ADD", "rr"), 0x21: ("SUB", "rr"), 0x22: ("XOR", "rr"), 0x23: ("MUL", "rr"),
       0x24: ("ROL", "ri"), 0x25: ("ADDI", "ri"), 0x26: ("OR", "rr"), 0x30: ("CMP", "rr"),
       0x31: ("JMP", "a"), 0x32: ("JZ", "a"), 0x33: ("JNZ", "a"), 0x40: ("LEN", "r"), 0xFF: ("HALT", "r")}
SIZE = {"ri": 3, "rr": 2, "r": 2, "a": 2}


def disasm(code):
    pc, out = 0, []
    while pc < len(code):
        op = code[pc]
        if op not in OPS:
            out.append((pc, "DB", "0x%02x" % op)); pc += 1; continue
        name, kind = OPS[op]
        x = code[pc + 1]
        txt = {"rr": "r%d, r%d" % (x >> 4 & 7, x & 7), "r": "r%d" % (x & 7), "a": "0x%02x" % x,
               "ri": None}[kind]
        if kind == "ri":
            txt = "r%d, 0x%02x" % (x & 7, code[pc + 2])
        out.append((pc, name, txt)); pc += SIZE[kind]
    return out


def emulate(code, data, inp, hook=None, max_steps=100000):
    r, zf, pc = [0] * 8, False, 0
    for _ in range(max_steps):
        if pc >= len(code): return False
        op = code[pc]
        if op not in OPS: return False
        name, kind = OPS[op]
        x = code[pc + 1]; a, b = x >> 4 & 7, x & 7
        if hook: hook(pc, name, r)
        nxt = pc + SIZE[kind]
        if name == "MOVI": r[b] = code[pc + 2]
        elif name == "ADDI": r[b] = (r[b] + code[pc + 2]) & 0xFF
        elif name == "ROL": s = code[pc + 2] & 7; r[b] = ((r[b] << s) | (r[b] >> ((8 - s) & 7))) & 0xFF
        elif name == "MOV": r[a] = r[b]
        elif name == "LDI": r[a] = inp[r[b]] if r[b] < len(inp) else 0
        elif name == "LDM": r[a] = data[r[b]] if r[b] < len(data) else 0
        elif name == "ADD": r[a] = (r[a] + r[b]) & 0xFF
        elif name == "SUB": r[a] = (r[a] - r[b]) & 0xFF
        elif name == "XOR": r[a] ^= r[b]
        elif name == "MUL": r[a] = (r[a] * r[b]) & 0xFF
        elif name == "OR": r[a] |= r[b]
        elif name == "CMP": zf = r[a] == r[b]
        elif name == "JMP": nxt = x
        elif name == "JZ": nxt = x if zf else nxt
        elif name == "JNZ": nxt = nxt if zf else x
        elif name == "LEN": r[b] = min(len(inp), 255)
        elif name == "HALT": return r[b] == 0
        pc = nxt
    return False


def solve(code, data, ins):
    # length: the first LEN rX / MOVI rY, n / CMP pair
    length = next(int(t.split(", ")[1], 16) for _, n, t in ins if n == "MOVI")
    # loop head = target of the backward JNZ; error register = HALT operand before fail stub
    back = [(pc, int(t, 16)) for pc, n, t in ins if n == "JNZ" and int(t, 16) < pc]
    assert back, "no loop found"
    head = back[0][1]
    err = int(next(t for _, n, t in ins if n == "HALT")[1:])
    pw = bytearray(b"A" * length)
    for i in range(length):
        for c in range(0x20, 0x7F):
            pw[i] = c
            snaps = []
            emulate(code, data, bytes(pw), hook=lambda pc, n, r: pc == head and snaps.append(r[err]))
            if i == length - 1:
                if emulate(code, data, bytes(pw)):
                    break
            elif len(snaps) > i + 1 and snaps[i + 1] == 0:   # error still clean after i+1 trips
                break
        else:
            raise SystemExit("no char fits at position %d" % i)
    assert emulate(code, data, bytes(pw))
    return pw.decode()


def main(binary):
    elf = crackme.Elf(binary)
    code, data = elf.symbol_bytes("bytecode"), elf.symbol_bytes("vmdata")
    ins = disasm(code)
    if "-v" in sys.argv:
        for pc, n, t in ins:
            print("%04x  %-5s %s" % (pc, n, t))
    pw = solve(code, data, ins)
    if not crackme.accepted(binary, pw + "\n"):
        print("recovered password rejected:", pw); return 1
    for bad in (pw[:-1], pw + "x", pw[:-1] + chr(ord(pw[-1]) ^ 1), chr(ord(pw[0]) ^ 1) + pw[1:], "", "A" * len(pw)):
        if crackme.accepted(binary, bad + "\n"):
            print("near miss accepted:", repr(bad)); return 1
    if any(pw in s for s in crackme.printable_strings(open(binary, "rb").read())):
        print("password visible to strings"); return 1
    print(f"OK: {len(code)}-byte program, {len(ins)} insns, {len(data)} data bytes; "
          f"password {pw!r} recovered by emulation, accepted; 6 near misses rejected")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

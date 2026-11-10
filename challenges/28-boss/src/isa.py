#!/usr/bin/env python3
"""SPOILER. ISA of the 28-boss stage-2 VM, shared by gen2.py and solve.py.
4 byte registers r0..r3 and a sticky `bad` accumulator. Every instruction is
opcode + 2 operand bytes. The bytecode is stored XOR-encrypted with a rolling
key k (k = k*37 + 0x5B per byte, k0 = BC_KEY) and decrypted by the VM one
instruction at a time (it is never fully plaintext in memory)."""
BC_KEY = 0x6D
OPS = {  # name: (opcode, operand kinds)   r = register, i = imm8
    "LDI":  (0x3A, "ri"),   # r = imm
    "LDB":  (0xC5, "ri"),   # r = input[imm] (0 if past the end)
    "LEN":  (0x17, "r_"),   # r = length of stage-2 text (capped at 255)
    "XORI": (0x9E, "ri"),   # r ^= imm
    "MULI": (0x52, "ri"),   # r *= imm
    "ADD":  (0xE1, "rr"),   # r += r2
    "ROLI": (0x08, "ri"),   # r = rol8(r, imm & 7)
    "MOV":  (0x7B, "rr"),   # r = r2
    "CHK":  (0xA4, "ri"),   # bad |= r ^ imm
    "HALT": (0x66, "__"),   # return bad == 0 ? 0x5732 : 0
}
BY_CODE = {v[0]: k for k, v in OPS.items()}


def next_key(k):
    return (k * 37 + 0x5B) & 0xFF


def crypt(data, k=BC_KEY):
    out = bytearray()
    for b in data:
        out.append(b ^ k)
        k = next_key(k)
    return bytes(out)


def assemble(prog):
    out = bytearray()
    for name, *args in prog:
        op, _ = OPS[name]
        args = list(args) + [0] * (2 - len(args))
        out += bytes([op, args[0] & 0xFF, args[1] & 0xFF])
    return bytes(out)


def disasm(code):
    """Plain bytecode -> list of (name, a, b). Raises ValueError if invalid."""
    out = []
    for pc in range(0, len(code) - 2, 3):
        op, a, b = code[pc:pc + 3]
        if op not in BY_CODE:
            raise ValueError(f"bad opcode {op:#x} at {pc}")
        name = BY_CODE[op]
        kinds = OPS[name][1]
        if any(k == "r" and v > 3 for k, v in zip(kinds, (a, b))):
            raise ValueError(f"bad register at {pc}")
        out.append((name, a, b))
        if name == "HALT":
            return out
    raise ValueError("no HALT")


def run(prog, text, trace=None):
    """Emulate; returns (accepted, list of per-CHK booleans)."""
    r, bad, checks = [0] * 4, 0, []
    for name, a, b in prog:
        if name == "LDI": r[a] = b
        elif name == "LDB": r[a] = text[b] if b < len(text) else 0
        elif name == "LEN": r[a] = min(len(text), 255)
        elif name == "XORI": r[a] ^= b
        elif name == "MULI": r[a] = (r[a] * b) & 0xFF
        elif name == "ADD": r[a] = (r[a] + r[b]) & 0xFF
        elif name == "ROLI": s = b & 7; r[a] = ((r[a] << s) | (r[a] >> (8 - s))) & 0xFF
        elif name == "MOV": r[a] = r[b]
        elif name == "CHK": bad |= r[a] ^ b; checks.append(r[a] == b)
        elif name == "HALT": break
    return bad == 0, checks

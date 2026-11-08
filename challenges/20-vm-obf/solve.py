#!/usr/bin/env python3
"""Solver (spoiler!). Usage: solve.py <binary> [-v]

1. Reads `optab` (encoded opcode -> handler index), `vmkey` and `blob`.
2. Decrypts on the same schedule as fetch(): plain[pc] = blob[pc] ^ (vmkey[pc&3] + 0x3b*pc).
3. Handler index -> semantics comes from reading run_vm's switch (fixed table
   HANDLERS below, in case order). Each encoded opcode is translated to the
   canonical opcode of 19-vm-check, then 19's disassembler and emulator do the rest.
Tests: password accepted, near misses rejected, not in `strings`, the plain
blob is not plain 19-style code, and the mapping is a real permutation.
"""
import os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import crackme  # noqa: E402

spec = importlib.util.spec_from_file_location("s19", os.path.join(HERE, "..", "19-vm-check", "solve.py"))
s19 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s19)
CANON = {name: op for op, (name, _) in s19.OPS.items()}
HANDLERS = ["MOVI", "MOV", "LDI", "LDM", "ADD", "SUB", "XOR", "MUL", "ROL", "ADDI", "OR",
            "CMP", "JMP", "JZ", "JNZ", "LEN", "HALT"]


def decrypt(blob, key):
    return bytes(b ^ ((key[pc & 3] + pc * 0x3b) & 0xFF) for pc, b in enumerate(blob))


def translate(plain, optab):
    """Walk the decrypted program, mapping only opcode bytes (operands stay)."""
    out, pc = bytearray(plain), 0
    while pc < len(plain):
        h = optab[plain[pc]]
        if h >= len(HANDLERS):
            raise SystemExit("invalid opcode 0x%02x at %d" % (plain[pc], pc))
        name = HANDLERS[h]
        out[pc] = CANON[name]
        pc += s19.SIZE[s19.OPS[CANON[name]][1]]
    return bytes(out)


def main(binary):
    elf = crackme.Elf(binary)
    optab, key = elf.symbol_bytes("optab"), elf.symbol_bytes("vmkey")
    blob, data = elf.symbol_bytes("blob"), elf.symbol_bytes("vmdata")
    used = [i for i, h in enumerate(optab) if h < len(HANDLERS)]
    assert sorted(optab[i] for i in used) == list(range(len(HANDLERS))), "optab not a permutation"
    mapping = {"%02x" % i: HANDLERS[optab[i]] for i in used}
    code = translate(decrypt(blob, key), optab)
    ins = s19.disasm(code)
    if "-v" in sys.argv:
        print("opcode map:", mapping)
        for pc, n, t in ins:
            print("%04x  %-5s %s" % (pc, n, t))
    pw = s19.solve(code, data, ins)
    if not crackme.accepted(binary, pw + "\n"):
        print("recovered password rejected:", pw); return 1
    for bad in (pw[:-1], pw + "x", pw[:-1] + chr(ord(pw[-1]) ^ 1), chr(ord(pw[0]) ^ 1) + pw[1:], "", "A" * len(pw)):
        if crackme.accepted(binary, bad + "\n"):
            print("near miss accepted:", repr(bad)); return 1
    if any(pw in s for s in crackme.printable_strings(open(binary, "rb").read())):
        print("password visible to strings"); return 1
    if s19.disasm(blob)[:3] == ins[:3]:
        print("blob looks unencrypted"); return 1
    print(f"OK: {len(used)} shuffled opcodes recovered, {len(blob)}-byte program decrypted "
          f"({len(ins)} insns); password {pw!r} accepted; 6 near misses rejected")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

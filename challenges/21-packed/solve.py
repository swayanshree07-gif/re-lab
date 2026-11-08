#!/usr/bin/env python3
"""Solver (spoiler!). Usage: solve.py <binary>

Static unpacking, no debugger:
  1. Read packed[] from the symbol table.
  2. The keystream seed is a one-byte immediate in unpack(); instead of
     parsing it we try all 256 seeds and keep the one whose output
     decompresses cleanly (valid back-references, consumes the whole blob)
     and disassembles to code with no "(bad)" before the first `ret`.
  3. Disassemble the unpacked blob with objdump and read the constants:
     length from `cmp $N,%rsi`, initial key from `mov $K,%eax`, the expected
     table from the `lea X(%rip)` target.
  4. Invert t = ((c ^ k) + 3i) & 0xff ; k = (k*5 + c) & 0xff char by char.
"""
import os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402


def unpack(packed, seed):
    s, ip, out = seed, 0, bytearray()
    def nxt():
        nonlocal s, ip
        if ip >= len(packed):
            raise ValueError("truncated")
        s = (s * 0x1D + 0x4B) & 0xFF
        b = packed[ip] ^ s
        ip += 1
        return b
    while ip < len(packed):
        t = nxt()
        if t < 0x80:
            for _ in range(t + 1):
                out.append(nxt())
        else:
            ln = t - 0x80 + 3
            off = nxt() | nxt() << 8
            if off == 0 or off > len(out):
                raise ValueError("bad backref")
            for _ in range(ln):
                out.append(out[-off])
        if len(out) > 4096:
            raise ValueError("too big")
    return bytes(out)


def disasm(blob):
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(blob)
    try:
        return subprocess.run(["objdump", "-D", "-b", "binary", "-m", "i386:x86-64", f.name],
                              stdout=subprocess.PIPE, check=True).stdout.decode()
    finally:
        os.unlink(f.name)


def code_part(asm):
    lines = []
    for line in asm.splitlines():
        if re.match(r"\s+[0-9a-f]+:\t", line):
            lines.append(line)
            if "\tret" in line:
                break
    return lines


def main(binary):
    elf = crackme.Elf(binary)
    packed = elf.symbol_bytes("packed")
    cands = []
    for seed in range(256):
        try:
            blob = unpack(packed, seed)
        except ValueError:
            continue
        code = code_part(disasm(blob))
        if code and "\tret" in code[-1] and not any("(bad)" in l for l in code):
            cands.append((seed, blob, code))
    if len(cands) != 1:
        print(f"expected one seed, got {[c[0] for c in cands]}")
        return 1
    seed, blob, code = cands[0]
    print(f"seed 0x{seed:02x}: unpacked {len(packed)} -> {len(blob)} bytes, {len(code)} insns")
    text = "\n".join(code)
    n = int(re.search(r"cmp\s+\$0x([0-9a-f]+),%rsi", text).group(1), 16)
    k = int(re.search(r"mov\s+\$0x([0-9a-f]+),%eax", text).group(1), 16)
    tab = int(re.search(r"lea\s+0x[0-9a-f]+\(%rip\),%r\w+\s+# 0x([0-9a-f]+)", text).group(1), 16)
    want = blob[tab:tab + n]
    k0 = k
    pw = bytearray()
    for i, t in enumerate(want):
        c = ((t - 3 * i) & 0xFF) ^ k
        pw.append(c)
        k = (k * 5 + c) & 0xFF
    pw = pw.decode()
    print(f"len {n}, k0 0x{k0:02x}, table @0x{tab:x} -> {pw!r}")
    problems = []
    if not crackme.accepted(binary, pw):
        problems.append("password rejected")
    for bad in (pw[:-1], pw + "x", pw[:-1] + chr(ord(pw[-1]) ^ 1)):
        if crackme.accepted(binary, bad):
            problems.append(f"near miss accepted: {bad!r}")
    if pw in crackme.printable_strings(elf.data):
        problems.append("password visible in strings")
    if b"\x48\x83\xfe" + bytes([n]) in elf.data:
        problems.append("payload length check visible in plain binary")
    for p in problems:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

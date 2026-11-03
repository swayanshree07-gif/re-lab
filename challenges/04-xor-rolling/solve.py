#!/usr/bin/env python3
"""Automated solver (spoiler!). Usage: solve.py <binary>

Approach: read `key_bytes` and `expected` straight out of the ELF via the
symbol table (address + size), grab the IV from the `mov`/`movb` that
initialises `prev` in check_password (objdump), then invert:
    in[i] = ((e[i] - e[i-1]) & 0xff) ^ key[i % len(key)],  e[-1] = IV
"""
import os, re, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402


def find_iv(binary):
    asm = subprocess.run(["objdump", "-d", "--no-show-raw-insn", binary],
                         stdout=subprocess.PIPE, check=True).stdout.decode()
    body = re.search(r"<check_password>:\n(.*?)\n\n", asm, re.S).group(1)
    # the only byte-sized immediate store to a stack slot is `prev = IV`
    m = re.search(r"movb\s+\$0x([0-9a-f]+),-0x[0-9a-f]+\(%rbp\)", body)
    return int(m.group(1), 16)


def main(binary):
    elf = crackme.Elf(binary)
    key = elf.symbol_bytes("key_bytes")
    exp = elf.symbol_bytes("expected")
    iv = find_iv(binary)
    out, prev = bytearray(), iv
    for i, e in enumerate(exp):
        out.append(((e - prev) & 0xff) ^ key[i % len(key)])
        prev = e
    pw = out.decode()
    if pw.encode() in elf.data:
        print("password appears as plain bytes in the binary: challenge is broken")
        return 1
    # one-character change must fail (the check really covers every byte)
    if crackme.accepted(binary, pw[:-1] + chr(ord(pw[-1]) ^ 1)):
        print("near-miss accepted: check is broken")
        return 1
    if crackme.accepted(binary, pw):
        print(f"password: {pw}  (key {key.hex()}, iv {iv:#04x}, {len(exp)} bytes)")
        return 0
    print(f"recovered {pw!r} but it was rejected")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

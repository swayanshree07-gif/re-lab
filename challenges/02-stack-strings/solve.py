#!/usr/bin/env python3
"""Automated solver (spoiler!). Usage: solve.py <binary>

Approach: disassemble with objdump, collect every
`movb $imm, -off(%rbp)` inside check_password, place each byte at its
stack offset (lowest address = key[0]) and read the buffer back.
"""
import os, re, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402

MOVB = re.compile(r"movb\s+\$0x([0-9a-f]+),-0x([0-9a-f]+)\(%rbp\)")


def main(binary):
    asm = subprocess.run(["objdump", "-d", "--no-show-raw-insn", binary],
                         stdout=subprocess.PIPE, check=True).stdout.decode()
    m = re.search(r"<check_password>:\n(.*?)\n\n", asm, re.S)
    if not m:
        print("check_password not found")
        return 1
    stack = {}
    for imm, off in MOVB.findall(m.group(1)):
        stack[-int(off, 16)] = int(imm, 16)
    key = bytes(stack[o] for o in sorted(stack)).split(b"\0")[0].decode()
    if key.encode() in open(binary, "rb").read():
        print("password appears as plain bytes in the binary: challenge is broken")
        return 1
    if crackme.accepted(binary, key):
        print(f"password: {key}  (from {len(stack)} movb stores)")
        return 0
    print(f"recovered {key!r} but it was rejected")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

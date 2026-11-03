#!/usr/bin/env python3
"""Automated solver (spoiler!). Usage: solve.py <binary>

The binary is stripped, so there are no symbols to look up. Instead:
  1. objdump -d, find the instruction pattern of the check:
       mov <A>(%rip),%reg ; imul ; cmp <B>(%rip) ; ... ; rol %cl ; xor ; cmp <C>(%rip)
     and the rip-relative load into %ecx just before `rol %cl` (<R>).
     objdump prints the absolute target of each rip-relative operand as `# addr`.
  2. read the four 32-bit constants from .data at those addresses (tiny ELF reader)
  3. invert:  hi = t1 * inverse(mul) mod 2^32 ;  lo = rotl(hi, r) ^ t2
Checks: the key isn't in `strings`, the answer is accepted, the decoy key and
two near-misses are rejected, and `nm` finds no symbols.
"""
import os, re, struct, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402

PATTERN = re.compile(
    r"mov\s+0x[0-9a-f]+\(%rip\),%(\w+)\s+# (?P<mul>[0-9a-f]+).*?\n"
    r"(?:.*\n){0,2}?.*imul\s+%\w+,%\w+\n"
    r".*cmp\s+0x[0-9a-f]+\(%rip\),%\w+\s+# (?P<t1>[0-9a-f]+).*?\n"
    r"(?:.*\n){0,3}?.*mov\s+0x[0-9a-f]+\(%rip\),%ecx\s+# (?P<rot>[0-9a-f]+).*?\n"
    r".*rol\s+%cl,%\w+\n"
    r".*xor\s+.*\n"
    r".*cmp\s+0x[0-9a-f]+\(%rip\),%\w+\s+# (?P<t2>[0-9a-f]+)")


def rotl(x, r):
    r &= 31
    return ((x << r) | (x >> (32 - r))) & 0xFFFFFFFF


def main(binary):
    nm = subprocess.run(["nm", binary], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout
    if b"no symbols" not in nm:
        print("binary is not stripped")
        return 1
    asm = subprocess.run(["objdump", "-d", "--no-show-raw-insn", binary],
                         stdout=subprocess.PIPE, check=True).stdout.decode()
    m = PATTERN.search(asm)
    if not m:
        print("check pattern not found in disassembly")
        return 1
    elf = crackme.Elf(binary)
    c = {k: struct.unpack("<I", elf.read_vaddr(int(m.group(k), 16), 4))[0]
         for k in ("mul", "t1", "rot", "t2")}
    hi = c["t1"] * pow(c["mul"], -1, 1 << 32) & 0xFFFFFFFF
    lo = rotl(hi, c["rot"]) ^ c["t2"]
    key = f"{hi:08X}{lo:08X}"
    if key in crackme.printable_strings(elf.data):
        print("key visible in strings: challenge is broken")
        return 1
    for bad in ("DEADBEEFCAFEBABE", key[:-1] + ("0" if key[-1] != "0" else "1"),
                key.lower() if key.lower() != key else key[:-1] + "G"):
        if crackme.accepted(binary, bad):
            print(f"{bad} accepted: check is broken")
            return 1
    if not crackme.accepted(binary, key):
        print(f"recovered {key} (consts {c}) but it was rejected")
        return 1
    print(f"constants at {', '.join(k + '=' + m.group(k) for k in ('mul', 't1', 'rot', 't2'))}"
          f" -> key {key} accepted")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

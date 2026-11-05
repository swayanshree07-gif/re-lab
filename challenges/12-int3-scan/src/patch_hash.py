#!/usr/bin/env python3
"""Post-link step (spoiler!): hash region_begin..region_end in the ELF file and
write {hash, number of 0xCC bytes} over the `expected[2]` placeholders.
Usage: patch_hash.py <binary>"""
import os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import crackme  # noqa: E402

PLACEHOLDER = (0x1BADC0DE, 0x0BADF00D)


def region_hash(elf):
    syms = elf.symbols()
    start, end = syms["region_begin"][0], syms["region_end"][0]
    if not start < end:
        raise SystemExit("region_end is not after region_begin (function order changed?)")
    code = elf.read_vaddr(start, end - start)
    h = 0x811C9DC5
    for b in code:
        h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return code, h


def main(path):
    elf = crackme.Elf(path)
    code, h = region_hash(elf)
    ccs = code.count(0xCC)
    addr, size = elf.symbols()["expected"]
    sec = next(s for s in elf.sections if s["addr"] <= addr < s["addr"] + s["size"] and s["type"] != 8)
    off = sec["offset"] + addr - sec["addr"]
    if size != 8:
        raise SystemExit(f"`expected` has size {size}, want 8")
    cur = struct.unpack_from("<II", elf.data, off)
    if cur not in (PLACEHOLDER, (h, ccs)):
        raise SystemExit(f"unexpected values {cur} at `expected`")
    data = bytearray(elf.data)
    struct.pack_into("<II", data, off, h, ccs)
    with open(path, "r+b") as f:
        f.write(data)
    print(f"patched expected = {{{h:#010x}, {ccs}}} ({len(code)} code bytes hashed)")


if __name__ == "__main__":
    main(sys.argv[1])

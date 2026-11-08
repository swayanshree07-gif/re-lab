#!/usr/bin/env python3
"""Post-link step (spoiler!): FNV-1a of region_begin..region_end_marker written
over the `expected` placeholder. Usage: patch_hash.py <binary>"""
import os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import crackme  # noqa: E402

PLACEHOLDER = 0x1BADC0DE


def region_hash(elf):
    syms = elf.symbols()
    a, b = syms["region_begin"][0], syms["region_end_marker"][0]
    if not a < b:
        raise SystemExit("region_end_marker not after region_begin")
    h = 0x811C9DC5
    for x in elf.read_vaddr(a, b - a):
        h = ((h ^ x) * 0x01000193) & 0xFFFFFFFF
    return h


def main(path):
    elf = crackme.Elf(path)
    h = region_hash(elf)
    addr, size = elf.symbols()["expected"]
    sec = next(s for s in elf.sections if s["addr"] <= addr < s["addr"] + s["size"] and s["type"] != 8)
    off = sec["offset"] + addr - sec["addr"]
    cur = struct.unpack_from("<I", elf.data, off)[0]
    if size != 4 or cur not in (PLACEHOLDER, h):
        raise SystemExit(f"bad `expected` slot (size {size}, value {cur:#x})")
    with open(path, "r+b") as f:
        f.seek(off)
        f.write(struct.pack("<I", h))
    print(f"patched expected = {h:#010x}")


if __name__ == "__main__":
    main(sys.argv[1])

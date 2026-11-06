#!/usr/bin/env python3
"""Post-link step (spoiler!): XOR-encrypt the verify() code region in place in
the ELF file, so the on-disk binary disassembles to garbage. The runtime
unlock() reverses it with the same xkey[]. Usage: encrypt.py <binary>"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import crackme  # noqa: E402


def region_file_offset(elf, vaddr):
    for s in elf.sections:
        if s["type"] != 8 and s["addr"] and s["addr"] <= vaddr < s["addr"] + s["size"]:
            return s["offset"] + (vaddr - s["addr"])
    raise SystemExit(f"vaddr {vaddr:#x} not in a file-backed section")


def main(path):
    elf = crackme.Elf(path)
    syms = elf.symbols()
    start, end = syms["region_begin"][0], syms["region_end"][0]
    if not start < end:
        raise SystemExit("region_end is not after region_begin (function order changed?)")
    xkey = elf.symbol_bytes("xkey")
    off = region_file_offset(elf, start)
    n = end - start
    data = bytearray(elf.data)
    for i in range(n):
        data[off + i] ^= xkey[i % len(xkey)]
    with open(path, "r+b") as f:
        f.write(data)
    print(f"encrypted {n} code bytes of the verify() region with a {len(xkey)}-byte key")


if __name__ == "__main__":
    main(sys.argv[1])

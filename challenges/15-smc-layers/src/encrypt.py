#!/usr/bin/env python3
"""Post-link step (spoiler!). Three edits to the freshly-linked ELF:

  1. Patch target_h with fnv1a32(PREFIX).
  2. XOR-encrypt layer-1 code [r1_begin, r1_end) with the static xkey1[].
  3. XOR-encrypt layer-2 code [r2_begin, r2_end) with key2 = KDF(PREFIX).

At runtime unlock1() reverses (2) with xkey1[], and unlock2() reverses (3) by
recomputing key2 from the user's (correct) prefix. Usage: encrypt.py <binary>
"""
import os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import crackme  # noqa: E402

PREFIX = b"deep"   # the secret password prefix (spoiler)


def fnv32(data):
    h = 2166136261
    for b in data:
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def key2_from_prefix(prefix):
    h = fnv32(prefix)
    return bytes((prefix[i & 3] ^ ((h >> (8 * (i & 3))) & 0xFF)) for i in range(8))


def file_offset(elf, vaddr):
    for s in elf.sections:
        if s["type"] != 8 and s["addr"] and s["addr"] <= vaddr < s["addr"] + s["size"]:
            return s["offset"] + (vaddr - s["addr"])
    raise SystemExit(f"vaddr {vaddr:#x} not in a file-backed section")


def xor_span(data, elf, start_sym, end_sym, key, syms):
    start, end = syms[start_sym][0], syms[end_sym][0]
    if not start < end:
        raise SystemExit(f"{end_sym} not after {start_sym} (function order changed?)")
    off = file_offset(elf, start)
    for i in range(end - start):
        data[off + i] ^= key[i % len(key)]
    return end - start


def main(path):
    elf = crackme.Elf(path)
    syms = elf.symbols()
    data = bytearray(elf.data)

    # 1. patch target_h
    th_addr = syms["target_h"][0]
    th_off = file_offset(elf, th_addr)
    struct.pack_into("<I", data, th_off, fnv32(PREFIX))

    # 2. layer 1: static key
    xkey1 = elf.symbol_bytes("xkey1")
    n1 = xor_span(data, elf, "r1_begin", "r1_end", xkey1, syms)

    # 3. layer 2: prefix-derived key
    key2 = key2_from_prefix(PREFIX)
    n2 = xor_span(data, elf, "r2_begin", "r2_end", key2, syms)

    with open(path, "r+b") as f:
        f.write(data)
    print(f"target_h={fnv32(PREFIX):#010x}; encrypted {n1} bytes (layer1) and "
          f"{n2} bytes (layer2, prefix-derived key)")


if __name__ == "__main__":
    main(sys.argv[1])

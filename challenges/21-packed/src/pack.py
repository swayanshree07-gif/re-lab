#!/usr/bin/env python3
"""Hand-written packer (spoiler!): pack.py payload.bin packed.h
LZ77-style compression, then XOR with an LCG keystream.
Tokens: 0x00..0x7f -> (t+1) literal bytes follow
        0x80..0xff -> copy (t-0x80+3) bytes from offset (2 bytes LE) back
Keystream: s = (s*0x1d + 0x4b) & 0xff, byte ^= s (s updated first)."""
import sys

SEED = 0xC3

def compress(data):
    out, lit, i = bytearray(), bytearray(), 0
    def flush():
        while lit:
            chunk = lit[:128]; del lit[:128]
            out.append(len(chunk) - 1); out.extend(chunk)
    while i < len(data):
        best_len = best_off = 0
        for j in range(max(0, i - 0xFFFF), i):
            l = 0
            while l < 130 and i + l < len(data) and data[j + l] == data[i + l]:
                l += 1
            if l > best_len:
                best_len, best_off = l, i - j
        if best_len >= 3:
            flush()
            out.append(0x80 + best_len - 3); out += best_off.to_bytes(2, "little")
            i += best_len
        else:
            lit.append(data[i]); i += 1
    flush()
    return bytes(out)

def crypt(data, seed=SEED):
    s, out = seed, bytearray()
    for b in data:
        s = (s * 0x1D + 0x4B) & 0xFF
        out.append(b ^ s)
    return bytes(out)

if __name__ == "__main__":
    raw = open(sys.argv[1], "rb").read()
    packed = crypt(compress(raw))
    with open(sys.argv[2], "w") as f:
        f.write(f"#define PACK_SEED 0x{SEED:02x}\n#define UNPACKED_SIZE {len(raw)}\n")
        f.write("static const unsigned char packed[] = {\n")
        for i in range(0, len(packed), 16):
            f.write("    " + ", ".join(f"0x{b:02x}" for b in packed[i:i + 16]) + ",\n")
        f.write("};\n")

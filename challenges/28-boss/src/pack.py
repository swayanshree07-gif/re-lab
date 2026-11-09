#!/usr/bin/env python3
"""SPOILER. pack.py stage2.bin SPOILERS out.h
LZ77 (same token format as 21-packed), then XOR with a xorshift32 keystream
seeded by fnv1a(stage-1 key) ^ PACK_SALT. Without the stage-1 key the blob
can't be decrypted; the FNV of the plaintext is stored so main can check it."""
import sys
PACK_SALT = 0xA5C3F00D


def fnv1a(b):
    h = 0x811C9DC5
    for c in b:
        h = ((h ^ c) * 0x01000193) & 0xFFFFFFFF
    return h


def compress(data):
    out, lit, i = bytearray(), bytearray(), 0
    def flush():
        while lit:
            chunk = lit[:128]; del lit[:128]
            out.append(len(chunk) - 1); out.extend(chunk)
    while i < len(data):
        bl = bo = 0
        for j in range(max(0, i - 0xFFFF), i):
            l = 0
            while l < 130 and i + l < len(data) and data[j + l] == data[i + l]:
                l += 1
            if l > bl:
                bl, bo = l, i - j
        if bl >= 3:
            flush(); out.append(0x80 + bl - 3); out += bo.to_bytes(2, "little"); i += bl
        else:
            lit.append(data[i]); i += 1
    flush()
    return bytes(out)


def crypt(data, key):
    s = (fnv1a(key) ^ PACK_SALT) or 1
    out = bytearray()
    for b in data:
        s ^= (s << 13) & 0xFFFFFFFF; s ^= s >> 17; s ^= (s << 5) & 0xFFFFFFFF
        out.append(b ^ (s >> 24))
    return bytes(out)


def key_from_spoilers(path):
    return open(path).read().split("stage 1 key:")[1].split()[0].encode()


if __name__ == "__main__":
    raw = open(sys.argv[1], "rb").read()
    data = crypt(compress(raw), key_from_spoilers(sys.argv[2]))
    with open(sys.argv[3], "w") as f:
        f.write(f"#define PACK_SALT 0x{PACK_SALT:08x}u\n#define S2_SIZE {len(raw)}\n#define S2_FNV 0x{fnv1a(raw):08x}u\n")
        f.write("static const unsigned char s2_blob[] = {\n")
        for i in range(0, len(data), 16):
            f.write("    " + ", ".join(f"0x{b:02x}" for b in data[i:i + 16]) + ",\n")
        f.write("};\n")

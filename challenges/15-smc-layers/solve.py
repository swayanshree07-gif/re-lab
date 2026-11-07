#!/usr/bin/env python3
"""Solver + two-layer SMC demo (spoiler!). Usage: solve.py <binary>

Layer 1 (stage1) is XOR-encrypted on disk under a static key; layer 2 (stage2)
is XOR-encrypted under a key DERIVED FROM THE PASSWORD PREFIX, so stage2's real
code cannot be read statically until the prefix is known. This solver:

  1. Recovers the 4-char prefix by brute-forcing [a-z]{4} against the stored
     fnv1a32 target (global target_h) -- "derive the prefix".
  2. Derives key2 = KDF(prefix), decrypts the on-disk stage2 region with it, and
     confirms the garbage turns back into real code (fewer objdump (bad) insns).
     Then recovers the rest of the password with a 256-key search over the K2
     immediate, verified against the live binary -- "derive the rest".
  3. Confirms the full password is not visible in `strings`, and that the static
     layer-1 region also decrypts to real code.
"""
import itertools, os, string, struct, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402

PREFIX_LEN, REST_LEN = 4, 8


def fnv32(data):
    h = 2166136261
    for b in data:
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def key2_from_prefix(prefix):
    h = fnv32(prefix)
    return bytes((prefix[i & 3] ^ ((h >> (8 * (i & 3))) & 0xFF)) for i in range(8))


def bad_count(blob):
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(blob)
        name = f.name
    try:
        out = subprocess.run(["objdump", "-D", "-b", "binary", "-m", "i386:x86-64", name],
                             stdout=subprocess.PIPE, check=True).stdout.decode()
    finally:
        os.unlink(name)
    return out.count("(bad)")


def main(binary):
    elf = crackme.Elf(binary)
    syms = elf.symbols()
    problems = []

    # 1. recover the prefix from the fnv1a32 target.
    (th_addr, _) = syms["target_h"]
    target_h = struct.unpack("<I", elf.read_vaddr(th_addr, 4))[0]
    prefix = None
    for combo in itertools.product(string.ascii_lowercase, repeat=PREFIX_LEN):
        cand = "".join(combo).encode()
        if fnv32(cand) == target_h:
            prefix = cand
            break
    if prefix is None:
        print(f"no [a-z]{{4}} prefix hashes to {target_h:#010x}")
        return 1

    # 2. decrypt stage2 with the prefix-derived key, and recover the rest.
    r2b, r2e = syms["r2_begin"][0], syms["r2_end"][0]
    key2 = key2_from_prefix(prefix)
    enc2 = elf.read_vaddr(r2b, r2e - r2b)
    dec2 = bytes(b ^ key2[i % len(key2)] for i, b in enumerate(enc2))
    bad_enc2, bad_dec2 = bad_count(enc2), bad_count(dec2)
    if not (bad_dec2 < bad_enc2):
        problems.append(f"layer2 decrypt did not reduce (bad): enc={bad_enc2} dec={bad_dec2}")

    rest_enc = elf.symbol_bytes("rest_enc")
    found = []
    for k2 in range(256):
        rest = bytes((rest_enc[i] ^ ((k2 + i) & 0xFF)) for i in range(REST_LEN))
        pw = prefix + rest
        if all(0x20 <= c < 0x7F for c in pw) and crackme.accepted(binary, pw.decode()):
            found.append((k2, pw.decode()))
    if len(found) != 1:
        print(f"expected exactly one working K2, got {found}")
        return 1
    k2, pw = found[0]

    # 3. password not in strings; layer-1 static region also decrypts to code.
    if pw in crackme.printable_strings(elf.data):
        problems.append("password visible in strings")
    r1b, r1e = syms["r1_begin"][0], syms["r1_end"][0]
    xkey1 = elf.symbol_bytes("xkey1")
    enc1 = elf.read_vaddr(r1b, r1e - r1b)
    dec1 = bytes(b ^ xkey1[i % len(xkey1)] for i, b in enumerate(enc1))
    bad_enc1, bad_dec1 = bad_count(enc1), bad_count(dec1)
    if not (bad_dec1 < bad_enc1):
        problems.append(f"layer1 decrypt did not reduce (bad): enc={bad_enc1} dec={bad_dec1}")

    for p in problems:
        print(p)
    if problems:
        return 1
    print(f"prefix={prefix.decode()!r} (target_h={target_h:#010x}) K2={k2:#04x} "
          f"password={pw!r}")
    print(f"layer1 region: {bad_enc1} (bad) -> {bad_dec1} (bad); "
          f"layer2 region: {bad_enc2} (bad) -> {bad_dec2} (bad)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

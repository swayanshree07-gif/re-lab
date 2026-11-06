#!/usr/bin/env python3
"""Solver + self-modifying-code demo (spoiler!). Usage: solve.py <binary>

The real check verify() is XOR-encrypted in the on-disk binary, so objdump of
verify() is garbage; unlock() decrypts it at runtime with xkey[]. This solver:

  1. Recovers the password with a 256-key search. The check is
     enc[i] = password[i] ^ ((KEY0 + i) & 0xff) with KEY0 a one-byte immediate
     buried in the encrypted code. For each of the 256 KEY0 values we rebuild a
     candidate password and confirm it against the live binary.
  2. Confirms the password is not visible in `strings`.
  3. Shows the SMC directly: reads the encrypted verify() region from the file,
     XORs it with xkey[] (exactly what unlock() does), and checks that the
     decrypted bytes disassemble to far fewer "(bad)" instructions than the
     encrypted bytes on disk — i.e. the garbage turns back into real code.
"""
import os, re, struct, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402


def bad_count(blob):
    """Disassemble a raw x86-64 blob and count (bad) instructions."""
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
    enc = elf.symbol_bytes("enc")
    problems = []

    # 1. 256-key search for KEY0, verified against the live binary.
    found = []
    for k in range(256):
        pw = bytes((enc[i] ^ ((k + i) & 0xFF)) for i in range(len(enc)))
        if all(0x20 <= c < 0x7F for c in pw) and crackme.accepted(binary, pw.decode()):
            found.append((k, pw.decode()))
    if len(found) != 1:
        problems.append(f"expected exactly one working KEY0, got {found}")
        for p in problems:
            print(p)
        return 1
    key0, pw = found[0]

    # 2. not in strings
    if pw in crackme.printable_strings(elf.data):
        problems.append("password visible in strings")

    # 3. SMC: encrypted region on disk -> decrypt with xkey -> real code
    start, end = syms["region_begin"][0], syms["region_end"][0]
    xkey = elf.symbol_bytes("xkey")
    enc_region = elf.read_vaddr(start, end - start)
    dec_region = bytes(b ^ xkey[i % len(xkey)] for i, b in enumerate(enc_region))
    bad_enc, bad_dec = bad_count(enc_region), bad_count(dec_region)
    if not (bad_dec < bad_enc):
        problems.append(f"decrypting did not reduce (bad) instructions: enc={bad_enc} dec={bad_dec}")

    for p in problems:
        print(p)
    if problems:
        return 1
    print(f"password={pw!r} KEY0={key0:#04x}; "
          f"on-disk verify region: {bad_enc} (bad) insns, decrypted: {bad_dec} (bad)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

#!/usr/bin/env python3
"""Solver for 28-boss stages 1-3 (spoiler!). Usage: solve.py <binary>

The binary is stripped, so the tables are found by shape, not by symbol:
  1. .rodata: an S1_LEN-byte window that is a permutation of 0..n-1 is s1_perm;
     every other n-byte window is a candidate for s1_ct.
  2. The keystream seed is a 32-bit immediate in .text (at -O1 gcc folds it into `xor $imm` with the first salt);
     all immediates are tried.
  3. Clean-run salts are 0, so state = mix^3(seed, 0); undo the xorshift
     keystream and the permutation. A candidate wins if it is printable.
Then: run it (stage 1 clear + Correct!), near misses rejected, key not in
strings, and the anti-debug salts really change the result under strace.
Stage 2: LD_PRELOAD tools/dump_mprotect.so dumps the page main makes
executable (the unpacked VM). The bytecode is found by trying every offset
and every first key byte with the rolling-XOR decryption until it decodes as
valid bytecode ending in HALT (ISA from src/isa.py, which is what you
reverse from the VM's switch). The emulator records each CHK, so the key is
brute-forced one byte at a time.
Stage 3 (keygen): the model is in src/stage3.py (four Feistel rounds mapping
the serial to fnv(key1), fnv(key2)^0x5732). Its round keys and multiplier
must appear as immediates/data in the binary, which proves the model matches
it. With z3: solve the forward model symbolically (and prove uniqueness);
without z3: invert the Feistel network directly (fallback)."""
import os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
import isa  # noqa: E402
import stage3  # noqa: E402


def clears1(binary, text):
    return "Stage 1 clear." in crackme.run(binary, text)[1]


def clears2(binary, text):
    return "Stage 2 clear." in crackme.run(binary, text)[1]

M = 0xFFFFFFFF


def mix(s, v):
    s = ((s ^ v) * 0x9E3779B1) & M
    return ((s << 13) | (s >> 19)) & M


def recover(seed, perm, ct):
    s = seed
    for _ in range(3):
        s = mix(s, 0)
    out = [0] * len(perm)
    for i in range(len(perm)):
        s ^= (s << 13) & M; s ^= s >> 17; s ^= (s << 5) & M
        out[perm[i]] = ct[i] ^ ((s + 13 * i) & 0xFF)
    return bytes(out)


def main(binary):
    elf = crackme.Elf(binary)
    problems = []
    if elf.section(".symtab") is not None:
        problems.append("binary is not stripped")
    ro = elf.section_bytes(".rodata")
    asm = subprocess.run(["objdump", "-d", "-j", ".text", binary], stdout=subprocess.PIPE,
                         check=True).stdout.decode()
    imms = {int(x, 16) for x in re.findall(r"\$0x([0-9a-f]{7,8}),%e", asm)}
    found = set()
    for n in range(8, 33):
        perms = [o for o in range(len(ro) - n + 1) if sorted(ro[o:o + n]) == list(range(n))]
        for po in perms:
            perm = list(ro[po:po + n])
            for co in range(len(ro) - n + 1):
                if co == po:
                    continue
                ct = ro[co:co + n]
                for seed in imms:
                    pw = recover(seed, perm, ct)
                    if all(0x21 <= c < 0x7F and c != ord("|") for c in pw):
                        found.add((pw.decode(), seed, n, po, co))
    print(f"{len(imms)} immediates, candidates: {[(f[0], hex(f[1])) for f in found]}")
    good = [f for f in found if clears1(binary, f[0])]
    if len(good) != 1:
        print("expected exactly one working stage-1 key")
        return 1
    pw, seed, n, po, co = good[0]
    print(f"stage 1 key {pw!r} (seed 0x{seed:08x}, perm @.rodata+{po:#x}, ct @.rodata+{co:#x})")
    if crackme.accepted(binary, pw):
        problems.append("stage 1 key alone is accepted (stage 2 not enforced)")
    for bad in (pw[:-1], pw + "x", pw[:-1] + chr(ord(pw[-1]) ^ 1), pw[1:] + pw[0]):
        if clears1(binary, bad):
            problems.append(f"near miss accepted: {bad!r}")
    if pw in crackme.printable_strings(elf.data):
        problems.append("key visible in strings")
    if shutil.which("strace"):
        p = subprocess.run(["strace", "-o", os.devnull, binary], input=(pw + "\n").encode(),
                           stdout=subprocess.PIPE, timeout=30)
        if b"Stage 1 clear." in p.stdout:
            problems.append("anti-debug: stage 1 key still clears under strace")
        else:
            print("under strace: rejected as intended")
    problems += stage2(binary, pw)
    for p in problems:
        print(p)
    return 1 if problems else 0


def dump_stage2(binary, key):
    here = os.path.dirname(os.path.abspath(__file__))
    work = os.path.join(os.path.dirname(os.path.abspath(binary)), ".build-28-boss")
    os.makedirs(work, exist_ok=True)
    so, dump = os.path.join(work, "dump_mprotect.so"), os.path.join(work, "stage2.dump")
    subprocess.run(["cc", "-shared", "-fPIC", "-O1", "-o", so, os.path.join(here, "tools", "dump_mprotect.c"), "-ldl"],
                   check=True)
    if os.path.exists(dump):
        os.remove(dump)
    crackme.run(binary, key + "|", env=dict(os.environ, LD_PRELOAD=so, DUMP_PATH=dump))
    return open(dump, "rb").read() if os.path.exists(dump) else None


def find_bytecode(page):
    hits = []
    for off in range(len(page) - 30):
        for k0 in range(256):
            # cheap prefilter: first opcode must be valid
            if page[off] ^ k0 not in isa.BY_CODE:
                continue
            try:
                prog = isa.disasm(isa.crypt(page[off:off + 3 * 128], k0))
            except ValueError:
                continue
            if len(prog) >= 10:
                hits.append((off, k0, prog))
    return hits


def stage2(binary, key1):
    problems = []
    page = dump_stage2(binary, key1)
    if page is None:
        return ["stage 2 dump failed (mprotect hook did not fire)"]
    hits = find_bytecode(page)
    # every suffix of the real program (from a later instruction, with the
    # key byte at that point) also decodes, so take the longest one
    best = max((len(h[2]) for h in hits), default=0)
    longest = [h for h in hits if len(h[2]) == best]
    if len(longest) != 1:
        return [f"expected one longest bytecode candidate, got {len(longest)} of {len(hits)}"]
    off, k0, prog = longest[0]
    print(f"stage 2: {len(prog)} VM instructions at page+{off:#x}, key0 {k0:#04x}")
    length = next(b for n, a, b in prog if n == "CHK")  # first CHK is the length
    key = bytearray(b"A" * length)
    for i in range(length):
        for c in range(0x21, 0x7F):
            if c == ord("|"):
                continue
            key[i] = c
            if all(isa.run(prog, bytes(key))[1][:i + 2]):
                break
        else:
            return [f"stage 2: no byte fits position {i}"]
    k2 = key.decode()
    full = f"{key1}|{k2}"
    print(f"stage 2 key {k2!r}")
    if not clears2(binary, full):
        problems.append("stage1|stage2 input does not clear stage 2")
    for bad in (f"{key1}|{k2[:-1]}", f"{key1}|{k2}x", f"{key1}|{k2[:-1]}{chr(ord(k2[-1]) ^ 1)}", key1, f"{key1}|"):
        if clears2(binary, bad):
            problems.append(f"stage 2 near miss accepted: {bad!r}")
    if not clears2(binary, full + "|stage3-later"):
        problems.append("text after a second '|' must be ignored by stage 2")
    if crackme.accepted(binary, full):
        problems.append("stage 1+2 alone accepted (stage 3 not enforced)")
    if k2 in crackme.printable_strings(open(binary, "rb").read()) or k2.encode() in page:
        problems.append("stage 2 key visible in binary or unpacked page")
    return problems + stage3_check(binary, key1, k2)


def solve3_z3(h1, h2):
    import z3
    a, b = z3.BitVecs("a b", 32)
    fa, fb = stage3.forward(a, b, rotl=z3.RotateLeft, mask=0xFFFFFFFF)
    s = z3.Solver()
    s.add(fa == h1, fb == h2)
    if s.check() != z3.sat:
        raise SystemExit("z3: unsat")
    m = s.model()
    va, vb = m[a].as_long(), m[b].as_long()
    s.add(z3.Or(a != va, b != vb))
    if s.check() != z3.unsat:
        raise SystemExit("z3: serial not unique")
    return va, vb


def stage3_check(binary, key1, key2):
    problems = []
    data = open(binary, "rb").read()
    for k in stage3.RK + [stage3.MUL]:
        if k.to_bytes(4, "little") not in data:
            problems.append(f"stage 3 model constant {k:#010x} not in binary (model out of date)")
    h1, h2 = stage3.target(key1, key2)
    a, b = stage3.inverse(h1, h2)
    if stage3.forward(a, b) != (h1, h2):
        problems.append("stage 3 inverse disagrees with forward model")
    use_z3 = "--no-z3" not in sys.argv
    if use_z3:
        try:
            import z3  # noqa: F401
        except ImportError:
            print("NOTICE: z3 not installed, stage 3 uses the Feistel inversion fallback")
            use_z3 = False
    if use_z3:
        za, zb = solve3_z3(h1, h2)
        print("stage 3: z3 found a unique serial")
        if (za, zb) != (a, b):
            problems.append("z3 and fallback disagree")
    ser = f"{a:08X}-{b:08X}"
    full = f"{key1}|{key2}|{ser}"
    print(f"stage 3 serial {ser!r} -> full input {full!r}")
    if not crackme.accepted(binary, full):
        problems.append("full chain rejected")
    flip = ser[:-1] + ("0" if ser[-1] != "0" else "1")
    for bad in (f"{key1}|{key2}|{flip}", f"{key1}|{key2}|{ser.lower()}" if ser.lower() != ser else full + "x",
                f"{key1}|{key2}|{ser[:8]}{ser[9:]}", f"{key1}|{key2}|{ser}x", f"{key1}|{key2}x|{ser}"):
        if crackme.accepted(binary, bad):
            problems.append(f"stage 3 near miss accepted: {bad!r}")
    return problems

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

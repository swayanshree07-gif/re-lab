#!/usr/bin/env python3
"""Keygen (spoiler!). Usage: solve.py <binary>

Static: the seed and multiplier are the two mov/movk constant pairs in
`llvm-objdump -d` of make_serial (in order: seed, multiplier); the four
round keys are the 16 bytes of the `ktab` symbol. Model:
    h = ror32(h ^ c, 7) * MUL + ktab[i & 3];  sum += c
    serial = h ^ (sum << 16) ^ len   -> "XXXX-XXXX" (upper-case hex)
Dynamic test:
  - qemu-aarch64 installed: 40 random names accepted, near misses rejected.
  - otherwise (documented skip): build a native x86_64 twin of src/main.c
    (same C, x86 syscalls) in a temp dir and run the same tests on it. This
    proves the keygen matches the algorithm; the constants still come from
    the AArch64 binary only, and are checked against the twin's symbols.
"""
import os, random, re, shutil, string, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import crackme  # noqa: E402

M32 = 0xFFFFFFFF
OBJDUMP = shutil.which("llvm-objdump-23") or shutil.which("llvm-objdump")


def constants(binary):
    asm = subprocess.run([OBJDUMP, "-d", binary], stdout=subprocess.PIPE,
                         text=True, check=True).stdout
    body = asm.split("<make_serial>:")[1].split("\n\n")[0]
    lo = {m.group(1): int(m.group(2), 16)
          for m in re.finditer(r"\bmov\s+(w\d+), #0x([0-9a-f]+)", body)}
    consts = []
    for m in re.finditer(r"\bmovk\s+(w\d+), #0x([0-9a-f]+), lsl #16", body):
        consts.append(int(m.group(2), 16) << 16 | lo[m.group(1)])
    assert len(consts) == 2, consts
    kt = crackme.Elf(binary).symbol_bytes("ktab")
    ktab = [int.from_bytes(kt[i:i + 4], "little") for i in range(0, 16, 4)]
    return consts[0], consts[1], ktab


def keygen(name, seed, mul, ktab):
    h, s = seed, 0
    for i, c in enumerate(name.encode()):
        x = h ^ c
        h = ((((x >> 7) | (x << 25)) & M32) * mul + ktab[i & 3]) & M32
        s += c
    v = (h ^ (s << 16) ^ len(name)) & M32
    return "%04X-%04X" % (v >> 16, v & 0xFFFF)


def native_twin(tmp):
    out = os.path.join(tmp, "twin")
    subprocess.run(["cc", "-O1", "-static", "-nostdlib", "-ffreestanding", "-fno-builtin",
                    "-fno-stack-protector", "-fno-pie", "-no-pie", "-e", "_start", "-o", out,
                    os.path.join(HERE, "src", "main.c")], check=True)
    return out


def test(target, k):
    rnd = random.Random(24)
    for _ in range(40):
        name = "".join(rnd.choice(string.ascii_letters + string.digits + " _")
                       for _ in range(rnd.randint(4, 32)))
        assert crackme.accepted(target, name + "\n" + k(name)), name
    ser = k("analyst")
    bad = [("analyst", ser[:-1] + ("0" if ser[-1] != "0" else "1")),
           ("analyst", ser.lower() if ser.lower() != ser else ser.replace("-", "")),
           ("ana", k("ana")), ("analysT", ser), ("analyst", ser.replace("-", ""))]
    for n, s in bad:
        assert not crackme.accepted(target, n + "\n" + s), (n, s)
    print(f"  40 keygen serials accepted, {len(bad)} near misses rejected")


def main(binary):
    seed, mul, ktab = constants(binary)
    print("seed %08x mul %08x ktab %s" % (seed, mul, " ".join("%08x" % x for x in ktab)))
    k = lambda n: keygen(n, seed, mul, ktab)  # noqa: E731
    print("analyst ->", k("analyst"))
    with open(binary, "rb") as f:
        data = f.read()
    assert k("analyst").encode() not in data
    if crackme.runnable(binary):
        print("running AArch64 binary via", crackme.launcher(binary)[0])
        test(binary, k)
    else:
        print("SKIP run: qemu-aarch64 not installed; testing on a native twin of src/main.c")
        with tempfile.TemporaryDirectory() as tmp:
            twin = native_twin(tmp)
            tw = crackme.Elf(twin).symbol_bytes("ktab")
            assert [int.from_bytes(tw[i:i + 4], "little") for i in range(0, 16, 4)] == ktab
            test(twin, k)
    print("OK")


if __name__ == "__main__":
    main(sys.argv[1])

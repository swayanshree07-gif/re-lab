#!/usr/bin/env python3
"""Solver + anti-debug behaviour test (spoiler!). Usage: solve.py <binary>

Static solve: re-derive the keystream state the program computes when
nothing is watching: all three salts 0 and (code hash ^ expected) == 0. SEED is taken
from the `mov $imm32` in derive_key (objdump), the table from the symbol.
Then checks the behaviour:
  - gdb -batch: password rejected (ptrace + TracerPid salts)
  - LD_PRELOAD ptrace stub returning 0: rejected (double-TRACEME check)
  - gdb bypass: break main, then hbreak derive_key, zero salts[0..2] -> accepted
  - same bypass plus a *software* breakpoint on check -> rejected (code hash)
"""
import os, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402

STUB = "long ptrace(int r, ...) { (void)r; return 0; }\n"
ZERO = ["set {unsigned int}((char*)&salts+%d) = 0" % o for o in (0, 4, 8)]


def mix(s, v):
    s = ((s ^ v) * 0x9E3779B1) & 0xFFFFFFFF
    return ((s << 13) | (s >> 19)) & 0xFFFFFFFF


def find_seed(binary):
    out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", binary], stdout=subprocess.PIPE,
                         text=True, check=True).stdout
    body = out.split("<derive_key>:")[1].split("\n\n")[0]
    imms = [int(m, 16) for m in re.findall(r"movl\s+\$0x([0-9a-f]+),", body)]
    return [x for x in imms if x not in (0x811C9DC5,)]


def decrypt(table, seed):
    st = seed
    for _ in range(4):
        st = mix(st, 0)
    out = bytearray()
    for i, c in enumerate(table):
        st ^= (st << 13) & 0xFFFFFFFF
        st ^= st >> 17
        st ^= (st << 5) & 0xFFFFFFFF
        out.append(c ^ ((st + 7 * i) & 0xFF))
    return bytes(out)


def gdb_ok(binary, text, cmds):
    with tempfile.NamedTemporaryFile("w", suffix=".in", delete=False) as f:
        f.write(text + "\n")
    try:
        cmd = ["gdb", "-nx", "-batch"]
        for c in cmds:
            cmd += ["-ex", c.replace("@IN", f.name)]
        out = subprocess.run(cmd + [binary], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, timeout=60).stdout.decode(errors="replace")
    finally:
        os.unlink(f.name)
    return crackme.SUCCESS_MARK in out


def main(binary):
    table = crackme.Elf(binary).symbol_bytes("table")
    pw = None
    for seed in find_seed(binary):
        cand = decrypt(table, seed)
        if all(0x21 <= b < 0x7f for b in cand):
            pw = cand.decode()
            break
    if pw is None or not crackme.accepted(binary, pw):
        print("static solve failed:", pw)
        return 1
    problems = []
    if pw in crackme.printable_strings(open(binary, "rb").read()):
        problems.append("password visible in strings")
    if shutil.which("gdb"):
        if gdb_ok(binary, pw, ["run < @IN"]):
            problems.append("password accepted under plain gdb")
        bypass = ["break main", "run < @IN", "delete", "hbreak derive_key", "continue"] + ZERO + ["delete", "continue"]
        if not gdb_ok(binary, pw, bypass):
            problems.append("gdb bypass (zero salts, hw breakpoint) failed")
        swbp = ["break main", "run < @IN", "delete", "hbreak derive_key", "break check", "continue"] + ZERO + ["continue", "continue"]
        if gdb_ok(binary, pw, swbp):
            problems.append("software breakpoint in region not detected")
    cc = shutil.which("cc") or shutil.which("gcc")
    if cc:
        with tempfile.TemporaryDirectory() as d:
            src, so = os.path.join(d, "s.c"), os.path.join(d, "s.so")
            open(src, "w").write(STUB)
            subprocess.run([cc, "-shared", "-fPIC", "-o", so, src], check=True)
            if crackme.accepted(binary, pw, env=dict(os.environ, LD_PRELOAD=so)):
                problems.append("LD_PRELOAD ptrace stub not detected")
    for near in (pw[:-1], pw + "x", pw[:-1] + chr(ord(pw[-1]) ^ 1)):
        if crackme.accepted(binary, near):
            problems.append(f"near miss {near!r} accepted")
    for p in problems:
        print(p)
    if problems:
        return 1
    print(f"password={pw!r}; gdb and LD_PRELOAD stub rejected; salt-zeroing bypass works "
          f"with hbreak, fails with a software breakpoint")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

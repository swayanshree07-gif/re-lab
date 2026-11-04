#!/usr/bin/env python3
"""Solver + anti-debug behaviour test (spoiler!). Usage: solve.py <binary>

Reads `keys` and `blobs` from the symbol table and decodes both candidates;
the one accepted in a normal run is the password, the other is the decoy.
Then checks the anti-debug behaviour:
  - under `gdb -batch` the decoy is accepted and the password is rejected
  - same under `strace` (if installed)
  - a naive LD_PRELOAD ptrace() stub that always returns 0 is also detected
  - bypass: in gdb, `set {int}&mode = 0` at main makes the password work again
"""
import os, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402

STUB = "long ptrace(int r, ...) { (void)r; return 0; }\n"


def gdb_run(binary, text, extra=()):
    with tempfile.NamedTemporaryFile("w", suffix=".in", delete=False) as f:
        f.write(text + "\n")
    try:
        cmd = ["gdb", "-nx", "-batch"]
        if extra:
            cmd += ["-ex", "break main", "-ex", f"run < {f.name}"]
            for e in extra:
                cmd += ["-ex", e]
            cmd += ["-ex", "continue"]
        else:
            cmd += ["-ex", f"run < {f.name}"]
        out = subprocess.run(cmd + [binary], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, timeout=60).stdout.decode(errors="replace")
    finally:
        os.unlink(f.name)
    return crackme.SUCCESS_MARK in out


def main(binary):
    elf = crackme.Elf(binary)
    keys = elf.symbol_bytes("keys")
    blobs = elf.symbol_bytes("blobs")
    n = len(blobs) // len(keys)
    cands = [bytes(b ^ k for b in blobs[i * n:(i + 1) * n]).decode() for i, k in enumerate(keys)]
    ok = [c for c in cands if crackme.accepted(binary, c)]
    if len(ok) != 1:
        print("expected exactly one candidate accepted normally:", cands, ok)
        return 1
    pw = ok[0]
    decoy = [c for c in cands if c != pw][0]
    problems = []
    if shutil.which("gdb"):
        if gdb_run(binary, pw):
            problems.append("password accepted under gdb (anti-debug not working)")
        if not gdb_run(binary, decoy):
            problems.append("decoy not accepted under gdb")
        if not gdb_run(binary, pw, ["set {int}&mode = 0"]):
            problems.append("bypass (mode = 0) did not work")
    if shutil.which("strace"):
        p = subprocess.run(["strace", "-o", os.devnull, binary], input=(decoy + "\n").encode(),
                           stdout=subprocess.PIPE, timeout=30)
        if crackme.SUCCESS_MARK not in p.stdout.decode():
            problems.append("decoy not accepted under strace")
    cc = shutil.which("cc") or shutil.which("gcc")
    if cc:
        with tempfile.TemporaryDirectory() as d:
            src, so = os.path.join(d, "stub.c"), os.path.join(d, "stub.so")
            open(src, "w").write(STUB)
            subprocess.run([cc, "-shared", "-fPIC", "-o", so, src], check=True)
            env = dict(os.environ, LD_PRELOAD=so)
            if crackme.accepted(binary, pw, env=env):
                problems.append("naive LD_PRELOAD stub not detected")
    for p in problems:
        print(p)
    if problems:
        return 1
    print(f"password={pw!r} decoy={decoy!r}; gdb/strace take the decoy path, "
          f"LD_PRELOAD stub detected, gdb bypass works")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

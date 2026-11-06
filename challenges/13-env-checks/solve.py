#!/usr/bin/env python3
"""Solver + anti-debug behaviour test for 13-env-checks (spoiler!).

Usage: solve.py <binary>

Static solve: read `pw_keys` and `pw_enc` from the symbol table and invert the
check `rotl8(in[i] ^ (key + 11*i), 3) == pw_enc[row][i]` for both rows. The
candidate accepted in a plain run is the real password; the other is the decoy.

Then confirm each environment check flips the program to the decoy, driving the
three detection vectors one at a time:
  - TracerPid:  run under `gdb -batch` and under `strace`
  - LD_PRELOAD: run with LD_PRELOAD pointing at a tiny empty .so
  - bad parent: run from a forking launcher whose own name is `gdb`
and that the real password still works from a clean shell.
"""
import os, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402


def rotr8(x, r):
    return ((x >> r) | (x << (8 - r))) & 0xFF


def recover(binary):
    elf = crackme.Elf(binary)
    keys = elf.symbol_bytes("pw_keys")
    enc = elf.symbol_bytes("pw_enc")
    n = len(enc) // len(keys)
    out = []
    for row, k in enumerate(keys):
        s = bytes((rotr8(enc[row * n + i], 3) ^ ((k + 11 * i) & 0xFF)) for i in range(n))
        out.append(s.decode())
    return out  # [real, decoy] by construction, verified below


def gdb_ok(binary, text):
    with tempfile.NamedTemporaryFile("w", suffix=".in", delete=False) as f:
        f.write(text + "\n")
    try:
        out = subprocess.run(
            ["gdb", "-nx", "-batch", "-ex", f"run < {f.name}", binary],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, timeout=60).stdout.decode(errors="replace")
    finally:
        os.unlink(f.name)
    return crackme.SUCCESS_MARK in out


LAUNCHER = r"""
#include <unistd.h>
#include <sys/wait.h>
#include <fcntl.h>
int main(int argc, char **argv) {
    int fd = open(argv[2], O_RDONLY); dup2(fd, 0);
    pid_t p = fork();
    if (p == 0) { execl(argv[1], "13-env-checks", (char *)0); _exit(1); }
    int st; waitpid(p, &st, 0); return 0;
}
"""


def main(binary):
    cands = recover(binary)
    accepted = [c for c in cands if crackme.accepted(binary, c)]
    if len(accepted) != 1:
        print("expected exactly one candidate accepted in a clean run:", cands, accepted)
        return 1
    pw = accepted[0]
    decoy = [c for c in cands if c != pw][0]
    problems = []
    cc = shutil.which("cc") or shutil.which("gcc")

    if shutil.which("gdb"):
        if gdb_ok(binary, pw):
            problems.append("real password accepted under gdb (TracerPid check failed)")
        if not gdb_ok(binary, decoy):
            problems.append("decoy not accepted under gdb")

    if shutil.which("strace"):
        for label, text, want in (("real", pw, False), ("decoy", decoy, True)):
            out = subprocess.run(["strace", "-o", os.devnull, binary],
                                 input=(text + "\n").encode(), stdout=subprocess.PIPE,
                                 timeout=30).stdout.decode(errors="replace")
            if (crackme.SUCCESS_MARK in out) != want:
                problems.append(f"{label} password unexpected under strace")

    if cc:
        with tempfile.TemporaryDirectory() as d:
            so = os.path.join(d, "e.so")
            open(os.path.join(d, "e.c"), "w").write("")
            subprocess.run([cc, "-shared", "-fPIC", "-o", so, os.path.join(d, "e.c")], check=True)
            env = dict(os.environ, LD_PRELOAD=so)
            if crackme.accepted(binary, pw, env=env):
                problems.append("real password accepted with LD_PRELOAD set")
            if not crackme.accepted(binary, decoy, env=env):
                problems.append("decoy not accepted with LD_PRELOAD set")

            # bad parent: a launcher named "gdb" that forks the crackme
            gdbname = os.path.join(d, "gdb")
            subprocess.run([cc, "-o", gdbname, "-xc", "-"], input=LAUNCHER.encode(), check=True)
            for label, text, want in (("real", pw, False), ("decoy", decoy, True)):
                inp = os.path.join(d, "in")
                open(inp, "w").write(text + "\n")
                out = subprocess.run([gdbname, os.path.abspath(binary), inp],
                                     stdout=subprocess.PIPE, timeout=30).stdout.decode(errors="replace")
                if (crackme.SUCCESS_MARK in out) != want:
                    problems.append(f"{label} password unexpected with parent named 'gdb'")

    for p in problems:
        print(p)
    if problems:
        return 1
    print(f"password={pw!r} decoy={decoy!r}; TracerPid (gdb/strace), LD_PRELOAD "
          f"and parent-name checks each switch to the decoy; clean run accepts the password")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

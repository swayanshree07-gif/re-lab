#!/usr/bin/env python3
"""Solver + timing anti-debug test (spoiler!). Usage: solve.py <binary>

Reads `keys` and `enc` from the symbol table, decodes both candidates
(enc[i] ^ (key + 7*i)); the one accepted in a normal run is the password,
the other one is the decoy. Then, if gdb is installed, checks:
  - breakpoint in compare + 0.3 s pause  -> decoy accepted, password rejected
  - scripted single-step (stepi 1000 from check) -> decoy accepted
  - bypass: break at the instruction that reads `slow` (found in objdump),
    `set {int}&slow = 0` -> password accepted even after the pause
"""
import os, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402


def gdb_script(binary, text, lines):
    """Run gdb with a command file; returns True if the program printed Correct!."""
    with tempfile.TemporaryDirectory() as d:
        inp, cmd = os.path.join(d, "in"), os.path.join(d, "cmds.gdb")
        open(inp, "w").write(text + "\n")
        body = ["set debuginfod enabled off"] + [l.replace("@IN", inp) for l in lines]
        open(cmd, "w").write("\n".join(body) + "\n")
        out = subprocess.run(["gdb", "-nx", "-batch", "-x", cmd, binary],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, timeout=60).stdout.decode(errors="replace")
    return crackme.SUCCESS_MARK in out


def slow_read_offset(binary):
    """Offset inside check() of the first instruction that loads `slow` into eax."""
    dis = subprocess.run(["objdump", "-d", "--no-show-raw-insn", binary],
                         stdout=subprocess.PIPE, check=True).stdout.decode()
    m = re.search(r"^([0-9a-f]+) <check>:\n(.*?)\n\n", dis, re.S | re.M)
    start = int(m.group(1), 16)
    for line in m.group(2).splitlines():
        mm = re.match(r"\s*([0-9a-f]+):\s+mov\s+0x[0-9a-f]+\(%rip\),%eax\s+# [0-9a-f]+ <slow>", line)
        if mm:
            return int(mm.group(1), 16) - start
    raise SystemExit("could not find the read of `slow` in check()")


def main(binary):
    elf = crackme.Elf(binary)
    keys = elf.symbol_bytes("keys")
    enc = elf.symbol_bytes("enc")
    n = len(enc) // len(keys)
    cands = [bytes(b ^ ((k + 7 * i) & 0xFF) for i, b in enumerate(enc[j * n:(j + 1) * n])).decode()
             for j, k in enumerate(keys)]
    ok = [c for c in cands if crackme.accepted(binary, c)]
    if len(ok) != 1:
        print("expected exactly one candidate accepted normally:", cands, ok)
        return 1
    pw = ok[0]
    decoy = [c for c in cands if c != pw][0]
    problems = []
    # normal runs must never trip the timer
    for _ in range(50):
        if not crackme.accepted(binary, pw):
            problems.append("password rejected in a normal run (false timing trigger)")
            break
    if shutil.which("gdb"):
        pause = ["break compare", "run < @IN", "delete", "shell sleep 0.3", "continue"]
        if gdb_script(binary, pw, pause):
            problems.append("password accepted after a breakpoint pause (timing check not working)")
        if not gdb_script(binary, decoy, pause):
            problems.append("decoy not accepted after a breakpoint pause")
        if not gdb_script(binary, decoy, ["break check", "run < @IN", "delete", "stepi 1000", "continue"]):
            problems.append("scripted single-step did not hit the timing trap")
        off = slow_read_offset(binary)
        bypass = pause[:-1] + [f"break *check+{off}", "continue", "set {int}&slow = 0", "continue"]
        if not gdb_script(binary, pw, bypass):
            problems.append("bypass (slow = 0 before it is read) did not work")
    for p in problems:
        print(p)
    if problems:
        return 1
    print(f"password={pw!r} decoy={decoy!r}; breakpoint pause and stepi both hit the "
          f"timing trap, bypass at check+{off:#x} works" if shutil.which("gdb") else
          f"password={pw!r} (gdb not installed: timing tests skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

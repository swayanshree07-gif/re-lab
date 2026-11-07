#!/usr/bin/env python3
"""Value tracer: run a binary under gdb with some stdin and print an expression
every time a breakpoint is hit. Made for control-flow-flattened code: put the
breakpoint on the dispatcher and print the state variable to get the order in
which the blocks ran.

Usage:
  tools/gdbtrace.py BINARY LOCATION EXPR [--input TEXT] [--max N] [--hw]

  LOCATION  any gdb location, e.g. '*check+0x4f' or '*0x401258'
  EXPR      a gdb expression printed as hex, e.g. '*(unsigned*)($rbp-0x24)' or '$eax'
  --hw      use a hardware breakpoint (for self-checksumming / SMC targets)

Prints one hex value per line. As a module: trace(binary, loc, expr, stdin_text)
returns a list of ints (raises RuntimeError if gdb is missing or nothing hit).
"""
import argparse, os, re, shutil, subprocess, sys, tempfile


def trace(binary, location, expr, stdin_text="", max_hits=100000, hw=False, timeout=60):
    if not shutil.which("gdb"):
        raise RuntimeError("gdb not installed")
    with tempfile.TemporaryDirectory() as tmp:
        inp = os.path.join(tmp, "stdin")
        with open(inp, "w") as f:
            f.write(stdin_text + "\n")
        cmds = os.path.join(tmp, "cmds.gdb")
        with open(cmds, "w") as f:
            # one command per line: multi-line -ex arguments hang gdb (Day 6 note)
            f.write("set pagination off\nset confirm off\nset debuginfod enabled off\n")
            if hw:
                f.write("starti < %s\n" % inp)
                f.write("hbreak %s\n" % location)
            else:
                f.write("break %s\n" % location)
            f.write("commands\nsilent\nprintf \"TRACE %%x\\n\", %s\ncontinue\nend\n" % expr)
            f.write("continue\n" if hw else "run < %s\n" % inp)
            f.write("kill\nquit\n")
        p = subprocess.run(["gdb", "-nx", "-batch", "-x", cmds, os.path.abspath(binary)],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    # the program's own output (e.g. a prompt without newline) can share a line
    out = [int(v, 16) for v in re.findall(r"TRACE ([0-9a-f]+)", p.stdout.decode(errors="replace"))]
    if not out:
        raise RuntimeError("breakpoint never hit:\n" + p.stdout.decode(errors="replace")[-2000:])
    return out[:max_hits]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("binary")
    ap.add_argument("location")
    ap.add_argument("expr")
    ap.add_argument("--input", default="")
    ap.add_argument("--max", type=int, default=100000)
    ap.add_argument("--hw", action="store_true")
    a = ap.parse_args()
    for v in trace(a.binary, a.location, a.expr, a.input, a.max, a.hw):
        print(f"{v:#010x}")


if __name__ == "__main__":
    sys.exit(main())

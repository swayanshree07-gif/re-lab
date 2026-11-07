#!/usr/bin/env python3
"""Automated solver (spoiler!). Usage: solve.py <binary>

check() is a hand-flattened state machine: one dispatcher (a chain of
`cmpl $STATE, slot ; je BLOCK`) and blocks that update the state slot with
`xorl $DELTA, slot` (unconditional edges) or a branchless mask (2-way edges).

  1. static CFG recovery: parse objdump of check(), map each `je` target to its
     case constant, and resolve every unconditional edge as STATE ^ DELTA; all
     of them must land on another case constant (proves the model of the
     flattening is right). The dispatcher head = the first `cmpl` on the slot.
  2. data: `mix` = {seed, step, mul} and `exp_tab` from the symbol table
     (alt_tab is the decoy used only by the dead JUNK states).
  3. invert per character (h depends only on earlier chars):
       c = ((rotr8(exp[i], i%5+1) - i*step) & 0xff) ^ h ;  h = h*mul + c
  4. if gdb is installed: trace the dispatcher state with tools/gdbtrace.py:
     correct input runs 2 + 7*14 + 4 blocks and never visits the dead states;
     a wrong 14-char guess runs the same number (no early exit); a wrong
     length goes INIT, LEN, FAIL, EXIT.
"""
import os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402
import gdbtrace  # noqa: E402


def rotr8(x, r):
    return ((x >> r) | (x << (8 - r))) & 0xFF


def recover_cfg(binary):
    asm = subprocess.run(["objdump", "-d", "--no-show-raw-insn", binary],
                         stdout=subprocess.PIPE, check=True).stdout.decode()
    m = re.search(r"^[0-9a-f]+ <check>:\n(.*?)\n\n", asm, re.S | re.M)
    lines = m.group(1).splitlines()
    insns = []  # (addr, text)
    for ln in lines:
        mm = re.match(r"\s*([0-9a-f]+):\s+(.*)", ln)
        if mm:
            insns.append((int(mm.group(1), 16), mm.group(2).strip()))
    func = insns[0][0]
    # the state slot is the first `movl $imm, -X(%rbp)` (st = S_INIT)
    slot = re.search(r"movl\s+\$0x[0-9a-f]+,(-0x[0-9a-f]+\(%rbp\))", "\n".join(t for _, t in insns)).group(1)
    cases, head = {}, None  # block addr -> state
    for k, (a, t) in enumerate(insns):
        mm = re.match(r"cmpl\s+\$(0x[0-9a-f]+)," + re.escape(slot), t)
        if mm:
            head = a if head is None else head
            nxt = insns[k + 1][1] if k + 1 < len(insns) else ""
            jm = re.match(r"je\s+([0-9a-f]+)", nxt)
            if jm:
                cases[int(jm.group(1), 16)] = int(mm.group(1), 16)
    starts = sorted(cases)
    edges = {}
    for idx, blk in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else insns[-1][0] + 1
        body = [t for a, t in insns if blk <= a < end]
        for t in body:
            mm = re.match(r"xorl\s+\$(0x[0-9a-f]+)," + re.escape(slot), t)
            if mm:
                edges[cases[blk]] = cases[blk] ^ int(mm.group(1), 16)
    return slot, head - func, set(cases.values()), edges


def invert(exp, seed, step, mul):
    h, out = seed, bytearray()
    for i, e in enumerate(exp):
        c = ((rotr8(e, i % 5 + 1) - i * step) & 0xFF) ^ h
        out.append(c)
        h = (h * mul + c) & 0xFF
    return out.decode()


def main(binary):
    slot, head_off, states, edges = recover_cfg(binary)
    bad = {hex(s): hex(d) for s, d in edges.items() if d not in states}
    if len(states) < 12 or len(edges) < 8 or bad:
        print(f"CFG recovery failed: {len(states)} states, {len(edges)} edges, bad={bad}")
        return 1
    print(f"dispatcher at check+{head_off:#x}, state slot {slot}: "
          f"{len(states)} case states, {len(edges)} unconditional edges resolved")

    elf = crackme.Elf(binary)
    seed, step, mul = elf.symbol_bytes("mix")
    pw = invert(elf.symbol_bytes("exp_tab"), seed, step, mul)
    decoy = invert(elf.symbol_bytes("alt_tab"), seed, step, mul)
    if pw in crackme.printable_strings(elf.data):
        print("password visible in strings: challenge is broken")
        return 1
    if not crackme.accepted(binary, pw):
        print(f"recovered {pw!r} but it was rejected")
        return 1
    for wrong in (decoy, pw[:-1] + chr(ord(pw[-1]) ^ 1), pw + "x", pw[:-1]):
        if crackme.accepted(binary, wrong):
            print(f"{wrong!r} accepted: check is broken")
            return 1
    print(f"password {pw!r} accepted; decoy {decoy!r} (dead JUNK path) rejected")

    if not shutil.which("gdb"):
        print("gdb not installed: skipping the dispatcher trace")
        return 0
    loc, expr = f"*check+{head_off:#x}", f"*(unsigned*)($rbp{slot.split('(')[0]})"
    good = gdbtrace.trace(binary, loc, expr, pw)
    wrong14 = gdbtrace.trace(binary, loc, expr, "A" * len(pw))
    short = gdbtrace.trace(binary, loc, expr, "abc")
    want = 2 + 7 * len(pw) + 4
    # the states reached only from SEL(i > 0x40, ...) and their successors
    dead = states - set(good) - set(wrong14) - set(short)
    problems = []
    if len(good) != want:
        problems.append(f"correct run visited {len(good)} blocks, expected {want}")
    if len(wrong14) != want:
        problems.append(f"wrong 14-char run visited {len(wrong14)} blocks (early exit?)")
    if len(short) != 4 or short[0] != good[0]:
        problems.append(f"wrong-length trace {[hex(x) for x in short]}")
    if len(dead) != 3:
        problems.append(f"expected 3 never-visited (junk) states, got {len(dead)}")
    if problems:
        print("\n".join(problems))
        return 1
    print(f"gdb dispatcher trace: {len(good)} blocks for the password, {len(wrong14)} for a "
          f"wrong guess, {len(short)} for a wrong length; {len(dead)} states never run (junk)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

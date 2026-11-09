#!/usr/bin/env python3
"""Constraint solver (spoiler!). Usage: solve.py [--no-z3] <binary>

Reads the `rules` table (4-byte records op,a,b,k; count from the symbol
size) straight out of the ELF. Solves the byte constraint system with z3 if it
is importable, otherwise (or with --no-z3) with a hand-written search: unary
rules shrink each domain, then variables are assigned in BFS order over the
"determining" rules (add/xor/sub/mul-mod-251), so most variables follow from
one already chosen. Every complete candidate is checked against all rules.
Test: unique solution accepted, near misses rejected, not in strings, < 30 s.
"""
import os, struct, subprocess, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))

N = 16
DOM = range(0x21, 0x7f)
STRONG = (0, 1, 2, 3)


def evaluate(r, p):
    """Value the binary compares k against (op 5 uses b as a bit index)."""
    op, a, b, _ = r
    x, y = p[a], (0 if op == 5 else p[b])
    return [(x + y) & 0xff, x ^ y, (x * y) % 251, (x - y) & 0xff,
            int(x < y), (x >> b) & 1][op]


def holds(r, p):
    return evaluate(r, p) == r[3]


def fallback_solve(rules, limit=2):
    dom = {i: [c for c in DOM if all(holds(r, {i: c}) for r in rules
                                     if r[0] == 5 and r[1] == i)] for i in range(N)}
    order, seen = [], set()
    adj = {i: [r for r in rules if r[0] in STRONG and i in r[1:3]] for i in range(N)}
    for root in range(N):
        if root in seen:
            continue
        seen.add(root); queue = [root]
        while queue:
            v = queue.pop(0); order.append(v)
            for r in adj[v]:
                w = r[2] if r[1] == v else r[1]
                if w not in seen:
                    seen.add(w); queue.append(w)
    # rules to check once position order[d] is assigned
    pos = {v: d for d, v in enumerate(order)}
    check_at = [[] for _ in range(N)]
    for r in rules:
        last = pos[r[1]] if r[0] == 5 else max(pos[r[1]], pos[r[2]])
        check_at[last].append(r)
    sols, p = [], {}

    def rec(d):
        if len(sols) >= limit:
            return
        if d == N:
            sols.append(bytes(p[i] for i in range(N)))
            return
        v = order[d]
        for c in dom[v]:
            p[v] = c
            if all(holds(r, p) for r in check_at[d]):
                rec(d + 1)
        del p[v]
    rec(0)
    return sols


def z3_solve(rules, limit=2):
    import z3
    xs = [z3.BitVec(f"p{i}", 16) for i in range(N)]
    s = z3.Solver()
    for x in xs:
        s.add(z3.UGE(x, 0x21), z3.ULE(x, 0x7e))
    for op, a, b, k in rules:
        x, y = xs[a], xs[b]
        e = [(x + y) & 0xff, x ^ y, z3.URem(x * y, 251), (x - y) & 0xff,
             z3.If(z3.ULT(x, y), z3.BitVecVal(1, 16), z3.BitVecVal(0, 16)),
             z3.LShR(x, b) & 1][op]
        s.add(e == k)
    sols = []
    while len(sols) < limit and s.check() == z3.sat:
        m = s.model()
        pw = bytes(m[x].as_long() for x in xs)
        sols.append(pw)
        s.add(z3.Or([x != c for x, c in zip(xs, pw)]))
    return sols


def read_symbol(binary, name):
    out = subprocess.run(["nm", "-S", binary], stdout=subprocess.PIPE, text=True,
                         check=True).stdout
    for line in out.splitlines():
        f = line.split()
        if len(f) == 4 and f[3] == name:
            addr, size = int(f[0], 16), int(f[1], 16)
            break
    else:
        raise SystemExit(f"symbol {name} not found")
    data = open(binary, "rb").read()
    shoff, = struct.unpack_from("<Q", data, 0x28)
    shentsize, shnum = struct.unpack_from("<HH", data, 0x3a)
    for i in range(shnum):
        _, typ, _, sa, so, ss = struct.unpack_from("<IIQQQQ", data, shoff + i * shentsize)
        if typ != 8 and sa <= addr < sa + ss:
            return data[so + addr - sa: so + addr - sa + size]
    raise SystemExit("symbol not in a file-backed section")


def main(argv):
    use_z3 = "--no-z3" not in argv
    binary = [a for a in argv if not a.startswith("--")][0]
    import crackme
    raw = read_symbol(binary, "rules")
    rules = [tuple(raw[i:i + 4]) for i in range(0, len(raw), 4)]
    mode = "fallback"
    if use_z3:
        try:
            import z3  # noqa: F401
            mode = "z3"
        except ImportError:
            print("z3 not importable: using the fallback search")
    t0 = time.time()
    sols = (z3_solve if mode == "z3" else fallback_solve)(rules)
    dt = time.time() - t0
    if len(sols) != 1:
        print(f"expected exactly one solution, got {len(sols)}")
        return 1
    pw = sols[0].decode()
    if not crackme.accepted(binary, pw):
        print("solution rejected:", pw)
        return 1
    if pw in crackme.printable_strings(open(binary, "rb").read()):
        print("password visible in strings")
        return 1
    bad = [pw[:-1], pw + "x", pw[1:] + pw[0]] + \
          [pw[:i] + chr(ord(pw[i]) ^ 1) + pw[i + 1:] for i in (0, 7, 15)]
    for b in bad:
        if crackme.accepted(binary, b):
            print("near miss accepted:", b)
            return 1
    if dt > 30:
        print(f"too slow: {dt:.1f} s")
        return 1
    print(f"{len(rules)} rules; mode={mode}; unique solution {pw!r} in {dt:.2f} s; "
          f"{len(bad)} near misses rejected")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

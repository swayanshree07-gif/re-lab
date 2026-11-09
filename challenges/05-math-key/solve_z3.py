#!/usr/bin/env python3
"""z3 solver (spoiler!). Usage: solve_z3.py <binary> [--no-z3]

The six rules are written once in `rules()`, using only operators that work on
both z3 BitVecs and plain Python ints. So without z3 the same model is still
checked: against keys from the existing keygen (solve.py) and the binary.
With z3: find 8 distinct keys (blocking clauses), all must be accepted.
"""
import importlib.util, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import crackme  # noqa: E402


def rules(d):
    """d: 12 digits (ints or 64-bit BitVecs). Returns the list of conditions."""
    value = 0
    for x in d:
        value = value * 10 + x
    return [d[0] >= 1, *[x >= 0 for x in d], *[x <= 9 for x in d],
            sum(d) == 54, d[11] == sum(d[:11]) % 10, d[3] == d[8],
            d[1] * d[6] == 24, value % 9973 == 1337]


def model_ok(key):
    return len(key) == 12 and key.isdigit() and all(rules([int(c) for c in key]))


def concrete_check(binary):
    spec = importlib.util.spec_from_file_location("solve05", os.path.join(HERE, "solve.py"))
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    rng = random.Random(21)
    for _ in range(5):
        k = old.keygen(rng)
        if not (model_ok(k) and crackme.accepted(binary, k)):
            raise SystemExit(f"keygen key {k}: model/binary disagree")
        m = k[:5] + str((int(k[5]) + 1) % 10) + k[6:]
        if model_ok(m) != crackme.accepted(binary, m):
            raise SystemExit(f"mutant {m}: model/binary disagree")
    print("model agrees with binary on 5 keygen keys + 5 mutants")


def z3_solve(binary, n=8):
    import z3
    d = [z3.BitVec(f"d{i}", 64) for i in range(12)]
    s = z3.Solver()
    s.add(*rules(d))
    keys = []
    while len(keys) < n and s.check() == z3.sat:
        m = s.model()
        k = "".join(str(m[x].as_long()) for x in d)
        keys.append(k)
        s.add(z3.Or([x != m[x] for x in d]))
    for k in keys:
        if not (model_ok(k) and crackme.accepted(binary, k)):
            print(f"z3 key {k} rejected")
            return 1
    print(f"z3: {len(keys)} distinct keys accepted, e.g. {keys[0] if keys else '-'}")
    return 0 if len(keys) == n else 1


def main(argv):
    binary = argv[0]
    concrete_check(binary)
    if "--no-z3" in argv or importlib.util.find_spec("z3") is None:
        print("NOTICE: z3 not available, symbolic part skipped")
        return 0
    return z3_solve(binary)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

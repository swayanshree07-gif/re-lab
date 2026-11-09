#!/usr/bin/env python3
"""z3 "reverse keygen" (spoiler!). Usage: solve_z3.py <binary> [--no-z3]

Instead of serial-for-name, ask z3 for a *name* (8 printable chars) whose
serial is a chosen vanity value, TARGET. The hash is written once in
`serial_parts()` and works on z3 32-bit BitVecs and on plain ints, so without
z3 the model is still checked against the binary on random names.
"""
import importlib.util, os, random, string, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import crackme  # noqa: E402

M32 = 0xFFFFFFFF
NAMELEN = 8
TARGET = (0xC0FFEE00, 0x1800)   # 0x1800 = 8 * 768, i.e. byte sum 768


def serial_parts(cs, shr):
    """cs: name bytes; shr: logical right shift for the value type."""
    h, s = 0x5EED1234, 0
    for c in cs:
        h = ((h << 5) | shr(h, 27)) & M32
        h = ((h ^ c) * 0x2F) & M32
        s = s + c
    return h, (s * len(cs)) & 0xFFFF


def serial(name):
    h, s = serial_parts(list(name.encode()), lambda x, n: x >> n)
    return f"{h:08X}-{s:04X}"


def concrete_check(binary):
    rng = random.Random(21)
    for _ in range(5):
        name = "".join(rng.choice(string.ascii_letters) for _ in range(rng.randrange(4, 20)))
        good = serial(name)
        bad = good[:-1] + ("0" if good[-1] != "0" else "1")
        if not crackme.accepted(binary, f"{name}\n{good}"):
            raise SystemExit(f"model serial for {name!r} rejected")
        if crackme.accepted(binary, f"{name}\n{bad}"):
            raise SystemExit(f"wrong serial for {name!r} accepted")
    print("model agrees with binary on 5 random names (+5 wrong serials rejected)")


def z3_solve(binary):
    import z3
    cs = [z3.BitVec(f"c{i}", 32) for i in range(NAMELEN)]
    s = z3.Solver()
    for c in cs:   # printable, no space so the name reads cleanly
        s.add(z3.UGE(c, 0x21), z3.ULE(c, 0x7e))
    h, sm = serial_parts(cs, z3.LShR)
    s.add(h == TARGET[0], sm == TARGET[1])
    if s.check() != z3.sat:
        print("z3: unsat")
        return 1
    m = s.model()
    name = "".join(chr(m[c].as_long()) for c in cs)
    want = f"{TARGET[0]:08X}-{TARGET[1]:04X}"
    if serial(name) != want or not crackme.accepted(binary, f"{name}\n{want}"):
        print(f"z3 name {name!r} rejected")
        return 1
    print(f"z3: name {name!r} gets vanity serial {want}, accepted")
    return 0


def main(argv):
    binary = argv[0]
    concrete_check(binary)
    if "--no-z3" in argv or importlib.util.find_spec("z3") is None:
        print("NOTICE: z3 not available, symbolic part skipped")
        return 0
    return z3_solve(binary)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

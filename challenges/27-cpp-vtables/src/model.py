"""Python model of the four stage classes (spoiler!). Shared by gen.py and solve.py.
Each stage maps a 4-byte chunk to 4 bytes compared with `target`."""
ROT, ADD, XORK, MUL = 0, 1, 2, 3
NAMES = {ROT: "RotStage", ADD: "AddStage", XORK: "XorStage", MUL: "MulStage"}


def fwd(kind, a, b, chunk):
    out = []
    for i, c in enumerate(chunk):
        if kind == ROT:
            r = (a + i) & 7
            out.append(((c << r) | (c >> (8 - r))) & 0xff)
        elif kind == ADD:
            out.append((c + a + i * b) & 0xff)
        elif kind == XORK:
            out.append(c ^ ((a * (i + 1)) & 0xff) ^ b)
        else:  # MUL, a odd
            out.append((c * a + b) & 0xff)
    return out


def inv(kind, a, b, target):
    out = []
    for i, t in enumerate(target):
        if kind == ROT:
            r = (a + i) & 7
            out.append(((t >> r) | (t << (8 - r))) & 0xff)
        elif kind == ADD:
            out.append((t - a - i * b) & 0xff)
        elif kind == XORK:
            out.append(t ^ ((a * (i + 1)) & 0xff) ^ b)
        else:
            out.append(((t - b) * pow(a, -1, 256)) & 0xff)
    return out

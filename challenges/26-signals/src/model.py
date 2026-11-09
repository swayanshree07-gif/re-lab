"""Python model of the three signal handlers (spoiler!)."""
SEED = 0x5167A11
M = 0xffffffff
def rol(x, r): return ((x << r) | (x >> (32 - r))) & M
def step(kind, h, c):
    if kind == 0:   # SIGSEGV
        return rol(h, 5) ^ (c * 0x01000193) & M
    if kind == 1:   # SIGFPE
        return ((h + c * 0x2F1D3) * 0x9E3779B1) & M
    return ((h ^ (c << 11) ^ c) * 0x85EBCA6B) & M   # SIGILL

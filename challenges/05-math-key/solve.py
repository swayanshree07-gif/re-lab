#!/usr/bin/env python3
"""Automated solver / keygen (spoiler!). Usage: solve.py <binary>

The rules (read from the disassembly, see the desk writeup) are modelled in
`valid()`. Keygen: random 8-digit prefix obeying the product rule; the modulus rule
then fixes the last 4 digits; keep keys that pass the remaining rules.
Test: 10 generated keys accepted + 1000 random 12-digit keys rejected
(skipping any that the model says are valid).
"""
import os, random, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402

MOD, REM = 9973, 1337


def valid(k):
    if len(k) != 12 or not k.isdigit() or k[0] == "0":
        return False
    d = [int(c) for c in k]
    return (sum(d) == 54 and d[11] == sum(d[:11]) % 10 and d[3] == d[8]
            and d[1] * d[6] == 24 and int(k) % MOD == REM)


def keygen(rng):
    """Pick an 8-digit prefix that already satisfies the product rule, then
    the modulus rule fixes the last 4 digits (at most 1-2 choices since
    9973 < 10000). Check the remaining rules; retry until one passes."""
    pairs = [(3, 8), (4, 6), (6, 4), (8, 3)]
    while True:
        d = [rng.randrange(1, 10)] + [rng.randrange(10) for _ in range(7)]
        d[1], d[6] = rng.choice(pairs)
        prefix = int("".join(map(str, d)))
        suffix = (REM - prefix * 10**4) % MOD
        for suf in (suffix, suffix + MOD):
            if suf < 10**4:
                k = f"{prefix}{suf:04d}"
                if valid(k):
                    return k


def run_many(binary, keys):
    """Run the binary once per key, quickly (no Python overhead per check)."""
    script = 'while IFS= read -r k; do printf "%s\\n" "$k" | "$1" >/dev/null; echo $?; done'
    p = subprocess.run(["bash", "-c", script, "_", binary], input="\n".join(keys) + "\n",
                       stdout=subprocess.PIPE, text=True, timeout=120, check=True)
    return [int(x) for x in p.stdout.split()]


def main(binary):
    rng = random.Random(5)
    keys = set()
    while len(keys) < 10:
        keys.add(keygen(rng))
    for k in sorted(keys):
        if not crackme.accepted(binary, k):
            print(f"generated key {k} rejected")
            return 1
    fuzz = [str(rng.randrange(10**11, 10**12)) for _ in range(1000)]
    fuzz = [k for k in fuzz if not valid(k)]
    rcs = run_many(binary, fuzz)
    bad = [k for k, rc in zip(fuzz, rcs) if rc != 1]
    if bad or len(rcs) != len(fuzz):
        print(f"random keys not rejected: {bad[:5]}")
        return 1
    # each single rule matters: break one rule at a time on a good key
    k = sorted(keys)[0]
    for i in range(12):
        for c in "0123456789":
            m = k[:i] + c + k[i + 1:]
            if m != k and not valid(m) and crackme.accepted(binary, m):
                print(f"mutant {m} accepted but model says invalid")
                return 1
    print(f"keys: {', '.join(sorted(keys)[:3])} ... (10 accepted); "
          f"{len(fuzz)} random keys rejected; 108 mutants agree with the model")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

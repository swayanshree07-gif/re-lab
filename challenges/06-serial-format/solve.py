#!/usr/bin/env python3
"""Automated solver / keygen (spoiler!). Usage: solve.py <binary>

The 32-char alphabet is read from the binary (`alphabet` symbol). The weights
(3, 5, 7, +group index) and the "group 3 = column sum" rule are modelled in
`valid()` (read from the disassembly, see the desk writeup). Keygen: pick
9 free characters, compute the 7 dependent ones.
Test: 20 distinct generated serials accepted; 500 random well-formed serials
rejected unless the model says valid; every single-char mutation of a good
serial agrees with the model; all-identical-groups serials rejected.
"""
import os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402

W = (3, 5, 7)


def get_alphabet(binary):
    a = crackme.Elf(binary).symbol_bytes("alphabet").rstrip(b"\0").decode()
    assert len(a) == 32 and len(set(a)) == 32, a
    return a


def check_char(A, vals, g):
    return A[(sum(w * v for w, v in zip(W, vals)) + g) % 32]


def valid(A, s):
    if len(s) != 19 or s[4] != "-" or s[9] != "-" or s[14] != "-":
        return False
    groups = s.split("-")
    if len(groups) != 4 or any(len(g) != 4 for g in groups):
        return False
    if any(c not in A for g in groups for c in g):
        return False
    v = [[A.index(c) for c in g] for g in groups]
    for g in range(4):
        if A[v[g][3]] != check_char(A, v[g][:3], g):
            return False
    if any((v[0][j] + v[1][j] + v[2][j]) % 32 != v[3][j] for j in range(3)):
        return False
    return len(set(groups)) > 1


def keygen(A, rng):
    free = [[rng.randrange(32) for _ in range(3)] for _ in range(3)]
    free.append([sum(free[g][j] for g in range(3)) % 32 for j in range(3)])
    return "-".join("".join(A[x] for x in f) + check_char(A, f, g) for g, f in enumerate(free))


def run_many(binary, keys):
    import subprocess
    script = 'while IFS= read -r k; do printf "%s\\n" "$k" | "$1" >/dev/null; echo $?; done'
    p = subprocess.run(["bash", "-c", script, "_", binary], input="\n".join(keys) + "\n",
                       stdout=subprocess.PIPE, text=True, timeout=120, check=True)
    return [int(x) for x in p.stdout.split()]


def main(binary):
    A = get_alphabet(binary)
    rng = random.Random(6)
    serials = set()
    while len(serials) < 20:
        s = keygen(A, rng)
        if valid(A, s):
            serials.add(s)
    serials = sorted(serials)
    rcs = run_many(binary, serials)
    if rcs != [0] * 20:
        print("generated serial rejected:", [s for s, r in zip(serials, rcs) if r])
        return 1
    # random well-formed serials + all single-char mutations of one good serial
    probes = ["-".join("".join(rng.choice(A) for _ in range(4)) for _ in range(4))
              for _ in range(500)]
    good = serials[0]
    for i in range(19):
        for c in A + "-a0":
            m = good[:i] + c + good[i + 1:]
            if m != good:
                probes.append(m)
    # rule 5 (all groups identical -> reject) can never fire: the check char
    # depends on the group index, so identical groups already fail rule 2.
    # Probe the obvious ones anyway.
    probes += ["-".join([g] * 4) for g in ("AAAA", "SSSS", A[16] * 4)]
    rcs = run_many(binary, probes)
    bad = [p for p, r in zip(probes, rcs) if (r == 0) != valid(A, p)]
    if bad or len(rcs) != len(probes):
        print("binary and model disagree on:", bad[:5])
        return 1
    print(f"serials: {', '.join(serials[:3])} ... (20 accepted); "
          f"{len(probes)} random/mutant probes agree with the model")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

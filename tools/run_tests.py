#!/usr/bin/env python3
"""Run every challenge's solve.py against its built binary, plus a generic
negative check (an obviously wrong answer must be rejected with exit 1).

Usage: tools/run_tests.py [NN-name ...]   (default: all challenges)
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import crackme  # noqa: E402

WRONG_INPUTS = ["", "definitely-not-the-password", "A" * 200]


def main(argv):
    names = argv or sorted(d for d in os.listdir(os.path.join(ROOT, "challenges"))
                           if d[:2].isdigit())
    failures = 0
    for name in names:
        binary = os.path.join(ROOT, "dist", name)
        solver = os.path.join(ROOT, "challenges", name, "solve.py")
        problems = []
        if not os.path.exists(binary):
            problems.append("binary missing (run make all)")
        else:
            for w in WRONG_INPUTS:
                rc, out = crackme.run(binary, w)
                if rc != 1 or crackme.SUCCESS_MARK in out:
                    problems.append(f"wrong input {w[:20]!r} not rejected (rc={rc})")
            try:
                p = subprocess.run([sys.executable, solver, binary], timeout=120,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if p.returncode != 0:
                    problems.append("solve.py failed:\n" + p.stdout.decode(errors="replace"))
            except subprocess.TimeoutExpired:
                problems.append("solve.py timed out")
        status = "PASS" if not problems else "FAIL"
        print(f"[{status}] {name}")
        for pr in problems:
            print("       " + pr)
        failures += bool(problems)
    print(f"\n{len(names) - failures}/{len(names)} challenges passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

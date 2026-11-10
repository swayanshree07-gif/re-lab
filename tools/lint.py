#!/usr/bin/env python3
"""Structure + spoiler lint for every challenge.

Checks per challenges/NN-name/:
  - src/, Makefile, README.md, solve.py, src/SPOILERS exist
  - README.md does not contain any line of src/SPOILERS (case-insensitive)
  - HINTS.md has Levels 1-3 and no SPOILERS line
  - README.md has the Goal / Difficulty / Allowed tools sections
  - the desk writeup notes/NN-name.md exists and is spoiler-marked in its first
    5 lines (error; skipped with a warning when the desk folder is absent)
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESK = os.path.expanduser("~/Personal-Desk/06-security/reverse-engineering/re-lab")
REQUIRED = ["src", "Makefile", "README.md", "solve.py", "src/SPOILERS", "HINTS.md"]
SECTIONS = ["## Goal", "## Difficulty", "## Allowed tools"]


def main():
    errors, warnings = [], []
    names = sorted(d for d in os.listdir(os.path.join(ROOT, "challenges")) if d[:2].isdigit())
    for name in names:
        cdir = os.path.join(ROOT, "challenges", name)
        for f in REQUIRED:
            if not os.path.exists(os.path.join(cdir, f)):
                errors.append(f"{name}: missing {f}")
        readme_path = os.path.join(cdir, "README.md")
        spoil_path = os.path.join(cdir, "src", "SPOILERS")
        if os.path.exists(readme_path):
            readme = open(readme_path).read()
            for s in SECTIONS:
                if s not in readme:
                    errors.append(f"{name}: README.md lacks section '{s}'")
            if os.path.exists(spoil_path):
                for line in open(spoil_path):
                    secret = line.strip()
                    if secret and not secret.startswith("#") and secret.lower() in readme.lower():
                        errors.append(f"{name}: README.md leaks a spoiler")
        hints_path = os.path.join(cdir, "HINTS.md")
        if os.path.exists(hints_path):
            hints = open(hints_path).read()
            for lvl in (1, 2, 3):
                if f"Level {lvl}:" not in hints:
                    errors.append(f"{name}: HINTS.md lacks Level {lvl}")
            if os.path.exists(spoil_path):
                for line in open(spoil_path):
                    secret = line.strip()
                    if secret and not secret.startswith("#") and len(secret) > 3 and secret.lower() in hints.lower():
                        errors.append(f"{name}: HINTS.md leaks a spoiler")
        wpath = os.path.join(DESK, "notes", name + ".md")
        if not os.path.isdir(DESK):
            warnings.append(f"{name}: desk folder absent, writeup not checked")
        elif not os.path.exists(wpath):
            errors.append(f"{name}: no writeup at {wpath}")
        elif "spoiler" not in "".join(open(wpath).readlines()[:5]).lower():
            errors.append(f"{name}: writeup not spoiler-marked at the top")
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"lint: {len(names)} challenges, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

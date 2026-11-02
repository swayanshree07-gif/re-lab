#!/usr/bin/env python3
"""Structure + spoiler lint for every challenge.

Checks per challenges/NN-name/:
  - src/, Makefile, README.md, solve.py, src/SPOILERS exist
  - README.md does not contain any line of src/SPOILERS (case-insensitive)
  - README.md has the Goal / Difficulty / Allowed tools sections
  - optional: the desk writeup notes/NN-name.md exists (warning only)
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESK = os.path.expanduser("~/Personal-Desk/06-security/reverse-engineering/re-lab")
REQUIRED = ["src", "Makefile", "README.md", "solve.py", "src/SPOILERS"]
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
        if os.path.isdir(DESK) and not os.path.exists(os.path.join(DESK, "notes", name + ".md")):
            warnings.append(f"{name}: no writeup at {DESK}/notes/{name}.md")
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"lint: {len(names)} challenges, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Print a markdown difficulty table from each challenge README's '## Difficulty' line."""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print("| # | Challenge | Difficulty | Time |\n|---|---|---|---|")
for n in sorted(d for d in os.listdir(os.path.join(ROOT, "challenges")) if d[:2].isdigit()):
    lines = open(os.path.join(ROOT, "challenges", n, "README.md")).read().split("\n")
    line = lines[lines.index("## Difficulty") + 1]
    m = re.match(r"(\S+)\s*\(([^)]*)\)", line)
    stars, time = (m.group(1), m.group(2).split(":")[-1].strip() if n != "28-boss" else m.group(2)) if m else (line, "")
    print(f"| {n[:2]} | {n} | {stars} | {time} |")

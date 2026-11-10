#!/usr/bin/env bash
# Final demo: clean build, then solve every challenge and print a summary table.
# Exits 0 only if every challenge is solved.
set -u
cd "$(dirname "$0")/.."
timeout 600 make clean all >/dev/null || { echo "build failed"; exit 1; }
printf '%-4s %-20s %-12s %-8s %s\n' "#" "Challenge" "Difficulty" "Result" "Time"
pass=0; total=0
for d in challenges/[0-9][0-9]-*/; do
  name=$(basename "$d"); total=$((total+1))
  diff=$(python3 tools/difficulty.py | awk -F'|' -v n="$name" '$3 ~ " "n" " {gsub(/ /,"",$4); print $4}')
  t0=$(date +%s.%N)
  if timeout 120 python3 "$d/solve.py" "dist/$name" >/dev/null 2>&1; then r=solved; pass=$((pass+1)); else r=FAILED; fi
  t=$(echo "$(date +%s.%N) - $t0" | bc)
  printf '%-4s %-20s %-12s %-8s %.1fs\n' "${name:0:2}" "$name" "$diff" "$r" "$t"
done
echo "$pass/$total solved"
[ "$pass" -eq "$total" ]

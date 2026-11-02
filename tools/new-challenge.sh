#!/usr/bin/env bash
# Scaffold a new challenge: tools/new-challenge.sh NN-name
set -euo pipefail
name="${1:?usage: $0 NN-name}"
[[ "$name" =~ ^[0-9]{2}-[a-z0-9-]+$ ]] || { echo "name must look like 07-stripped"; exit 1; }
root="$(cd "$(dirname "$0")/.." && pwd)"
dir="$root/challenges/$name"
[[ -e "$dir" ]] && { echo "$dir already exists"; exit 1; }
mkdir -p "$dir/src"
cat > "$dir/Makefile" <<MK
DIST ?= ../../dist
NAME := $name
CFLAGS ?= -O0 -g0 -Wall -Wextra

\$(DIST)/\$(NAME): src/main.c
	@mkdir -p \$(DIST)
	\$(CC) \$(CFLAGS) -o \$@ \$<

.PHONY: clean
clean:
	rm -f \$(DIST)/\$(NAME)
MK
cat > "$dir/src/main.c" <<'C'
#include <stdio.h>
#include <string.h>

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) return 1;
    buf[strcspn(buf, "\n")] = 0;
    /* TODO: the check */
    puts("Wrong.");
    return 1;
}
C
printf '# One secret per line; tools/lint.py makes sure README.md never contains these.\n' > "$dir/src/SPOILERS"
cat > "$dir/README.md" <<MD
# $name

## Goal
Find the input that makes the program print \`Correct!\`.

## Difficulty
★☆☆☆☆

## Allowed tools
Anything: Ghidra, gdb (+GEF), objdump, strings, strace, ltrace.

## Run
\`\`\`
make -C ../.. all
../../dist/$name
\`\`\`
MD
cat > "$dir/solve.py" <<'PY'
#!/usr/bin/env python3
"""Automated solver (spoiler!). Usage: solve.py <binary>"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402


def main(binary):
    raise SystemExit("TODO")


if __name__ == "__main__":
    main(sys.argv[1])
PY
echo "created $dir"

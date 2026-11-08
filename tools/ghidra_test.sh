#!/bin/sh
# make ghidra-test: dump 01-plain-strcmp with Ghidra headless and check the output.
# Skips (exit 0, with a notice) if Ghidra or a new-enough JDK isn't available.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
GHIDRA=${GHIDRA_HOME:-$HOME/re-tools/ghidra_12.2_PUBLIC}
[ -x "$GHIDRA/support/analyzeHeadless" ] || { echo "SKIP: no Ghidra at $GHIDRA"; exit 0; }
need=$(sed -n 's/^application.java.min=//p' "$GHIDRA/Ghidra/application.properties")
jv=$(java -version 2>&1 | sed -n '1s/^[^"]*"\([0-9]*\).*/\1/p')
if [ -z "${JAVA_HOME:-}" ] && [ "${jv:-0}" -lt "${need:-0}" ]; then
    echo "SKIP: Ghidra needs JDK $need, found JDK ${jv:-none} (set JAVA_HOME to a JDK >= $need)"; exit 0
fi
out=$("$here/ghidra_dump.sh" "$here/../dist/01-plain-strcmp")
for pat in '## decompiled' ' main' 'strcmp' '// ---- main'; do
    grep -q -- "$pat" "$out" || { echo "FAIL: '$pat' missing in $out"; exit 1; }
done
echo "PASS: ghidra dump $out"

#!/bin/sh
# Ghidra-headless dump: functions, strings, decompiled C of a binary.
# usage: tools/ghidra_dump.sh <binary> [out.txt]   (default: dist/ghidra/<name>.txt)
set -eu
GHIDRA=${GHIDRA_HOME:-$HOME/re-tools/ghidra_12.2_PUBLIC}
if [ -z "${JAVA_HOME:-}" ]; then JAVA_HOME=$(dirname "$(dirname "$(readlink -f "$(command -v java)")")"); export JAVA_HOME; fi
bin=$(realpath "$1")
here=$(cd "$(dirname "$0")" && pwd)
name=$(basename "$bin")
out=${2:-$here/../dist/ghidra/$name.txt}
mkdir -p "$(dirname "$out")"
out=$(realpath "$(dirname "$out")")/$(basename "$out")
proj=$(mktemp -d)
trap 'rm -rf "$proj"' EXIT
timeout ${GHIDRA_TIMEOUT:-300} "$GHIDRA/support/analyzeHeadless" "$proj" tmp \
    -import "$bin" -scriptPath "$here/ghidra" -postScript DumpAll.java "$out" \
    -deleteProject > "$proj/log.txt" 2>&1 || { tail -30 "$proj/log.txt"; exit 1; }
echo "$out"

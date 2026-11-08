#!/bin/sh
# Self-test for tools/rvemu.py: build tools/rvtest/ops.c natively and for
# RV64IM, run both, compare the printed hashes. Exit 0 on match.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
LD=$(command -v ld.lld-23 || command -v ld.lld)
cc -O1 -DNATIVE -o "$out/native" "$here/rvtest/ops.c"
clang --target=riscv64-unknown-elf -march=rv64im -mabi=lp64 -O1 -ffreestanding \
  -fno-builtin -fno-stack-protector -fno-pic -c -o "$out/rv.o" "$here/rvtest/ops.c"
"$LD" -static -e _start -o "$out/rv" "$out/rv.o"
a=$("$out/native"); b=$(timeout 120 python3 "$here/rvemu.py" "$out/rv" </dev/null)
echo "native $a / rvemu $b"
[ "$a" = "$b" ] && echo "rvemu self-test: PASS" || { echo "rvemu self-test: FAIL"; exit 1; }

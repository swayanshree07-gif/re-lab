#!/usr/bin/env python3
"""Writes want.h for the password in SPOILERS (spoiler!)."""
import sys
pw = b"unp4ck3d_1n_m3m0ry"
k, out = 0x5A, []
for i, c in enumerate(pw):
    out.append(((c ^ k) + 3 * i) & 0xFF)
    k = (k * 5 + c) & 0xFF
open(sys.argv[1], "w").write(", ".join(f"0x{b:02x}" for b in out) + "\n")

"""Shared helpers for solve.py scripts and the test runner.

Convention: a crackme reads one line from stdin, prints "Correct!" and exits 0
on success, prints "Wrong." and exits 1 on failure.
"""
import subprocess

SUCCESS_MARK = "Correct!"


def run(binary, stdin_text, timeout=10, env=None):
    """Run the binary with stdin_text (a newline is appended). Returns (rc, stdout)."""
    p = subprocess.run([binary], input=(stdin_text + "\n").encode(),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=timeout, env=env)
    return p.returncode, p.stdout.decode(errors="replace")


def accepted(binary, stdin_text, **kw):
    rc, out = run(binary, stdin_text, **kw)
    return rc == 0 and SUCCESS_MARK in out


def printable_strings(data, min_len=4):
    """Like `strings`: runs of printable ASCII of at least min_len bytes."""
    out, cur = [], bytearray()
    for b in data:
        if 0x20 <= b < 0x7f:
            cur.append(b)
        else:
            if len(cur) >= min_len:
                out.append(cur.decode())
            cur = bytearray()
    if len(cur) >= min_len:
        out.append(cur.decode())
    return out

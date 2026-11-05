#!/usr/bin/env python3
"""Solver + int3-scan anti-debug test (spoiler!). Usage: solve.py <binary>

Static solve: hash the bytes region_begin..region_end straight from the file
(FNV-1a; that is what the program sees when nobody has patched it), check it
matches the patched `expected[0]`, build key = base_key ^ hash ^ expected[0]
and invert enc[i] = ((pw[i] ^ keybyte(i%4)) + 13*i). The decoy is dec[i] ^ (0xa5-3i).
Then, if gdb is installed:
  - software breakpoint in check_password  -> decoy accepted, password rejected
  - hardware breakpoint (hbreak) in check_password -> password accepted
  - bypass: break in main *after* the guard() call, only then set the software
    breakpoint in check_password -> password accepted, breakpoint is hit
Also: a 1-byte code patch inside the region (endbr64 -> 4-byte nop) in a temp
copy makes the real password fail (the hash feeds the key).
"""
import os, re, shutil, struct, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import crackme  # noqa: E402


def fnv1a(data):
    h = 0x811C9DC5
    for b in data:
        h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return h


def gdb_script(binary, text, lines):
    """Run gdb with a command file; returns the combined output."""
    with tempfile.TemporaryDirectory() as d:
        inp, cmd = os.path.join(d, "in"), os.path.join(d, "cmds.gdb")
        open(inp, "w").write(text + "\n")
        body = ["set debuginfod enabled off"] + [l.replace("@IN", inp) for l in lines]
        open(cmd, "w").write("\n".join(body) + "\n")
        return subprocess.run(["gdb", "-nx", "-batch", "-x", cmd, binary],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL, timeout=60).stdout.decode(errors="replace")


def after_guard_offset(binary):
    """Offset inside main of the instruction right after `call guard`."""
    dis = subprocess.run(["objdump", "-d", "--no-show-raw-insn", binary],
                         stdout=subprocess.PIPE, check=True).stdout.decode()
    m = re.search(r"^([0-9a-f]+) <main>:\n(.*?)\n\n", dis, re.S | re.M)
    start, lines = int(m.group(1), 16), m.group(2).splitlines()
    for i, line in enumerate(lines):
        if re.search(r"call\s+[0-9a-f]+ <guard>", line):
            return int(lines[i + 1].split(":")[0], 16) - start
    raise SystemExit("could not find `call guard` in main")


def main(binary):
    elf = crackme.Elf(binary)
    syms = elf.symbols()
    start, end = syms["region_begin"][0], syms["region_end"][0]
    code = elf.read_vaddr(start, end - start)
    h = fnv1a(code)
    exp_hash, exp_cc = struct.unpack("<II", elf.symbol_bytes("expected"))
    problems = []
    if h != exp_hash or code.count(0xCC) != exp_cc:
        problems.append(f"file hash/cc {h:#x}/{code.count(0xCC)} != expected {exp_hash:#x}/{exp_cc}")
    (base,) = struct.unpack("<I", elf.symbol_bytes("base_key"))
    key = base ^ h ^ exp_hash
    enc = elf.symbol_bytes("enc")
    pw = bytes((((b - 13 * i) & 0xFF) ^ ((key >> (8 * (i % 4))) & 0xFF))
               for i, b in enumerate(enc)).decode()
    decoy = bytes(b ^ ((0xA5 - 3 * i) & 0xFF) for i, b in enumerate(elf.symbol_bytes("dec"))).decode()
    if not crackme.accepted(binary, pw):
        problems.append(f"recovered password {pw!r} rejected")
    if crackme.accepted(binary, decoy):
        problems.append("decoy accepted in a normal run")
    if pw in crackme.printable_strings(elf.data):
        problems.append("password visible in strings")

    # tamper: replace the endbr64 of region_begin by a 4-byte nop in a temp copy
    with tempfile.TemporaryDirectory() as d:
        copy = os.path.join(d, "patched")
        data = bytearray(elf.data)
        sec = next(s for s in elf.sections if s["name"] == ".text")
        off = sec["offset"] + start - sec["addr"]
        if data[off:off + 4] == b"\xf3\x0f\x1e\xfa":
            data[off:off + 4] = b"\x0f\x1f\x40\x00"
        else:  # no endbr64 (older gcc / no CET): skip the tamper test
            copy = None
        if copy:
            open(copy, "wb").write(data)
            os.chmod(copy, 0o755)
            if crackme.accepted(copy, pw):
                problems.append("password still accepted after patching a code byte in the region")

    gdb = shutil.which("gdb")
    if gdb:
        sw = ["break check_password", "run < @IN", "continue"]
        if crackme.SUCCESS_MARK in gdb_script(binary, pw, sw):
            problems.append("password accepted with a software breakpoint in the region")
        if crackme.SUCCESS_MARK not in gdb_script(binary, decoy, sw):
            problems.append("decoy not accepted with a software breakpoint in the region")
        hw = ["starti < @IN", "hbreak check_password", "continue", "continue"]
        out = gdb_script(binary, pw, hw)
        if crackme.SUCCESS_MARK not in out or "in check_password" not in out:
            problems.append("hardware breakpoint run did not hit check_password and accept the password")
        offg = after_guard_offset(binary)
        late = [f"break *main+{offg}", "run < @IN", "break check_password", "continue", "continue"]
        out = gdb_script(binary, pw, late)
        if crackme.SUCCESS_MARK not in out or "in check_password" not in out:
            problems.append("late software breakpoint (after guard) bypass did not work")
    for p in problems:
        print(p)
    if problems:
        return 1
    print(f"password={pw!r} decoy={decoy!r} hash={h:#010x} cc={exp_cc}; "
          + ("sw bp -> decoy, hbreak and bp-after-guard -> password" if gdb else "gdb not installed: skipped"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

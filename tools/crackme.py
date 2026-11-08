"""Shared helpers for solve.py scripts and the test runner.

Convention: a crackme reads one line from stdin, prints "Correct!" and exits 0
on success, prints "Wrong." and exits 1 on failure.
"""
import os, subprocess

SUCCESS_MARK = "Correct!"


def launcher(binary):
    """argv to run binary: native, or RISC-V via qemu-riscv64 if installed,
    else via tools/rvemu.py (our own RV64IM emulator)."""
    with open(binary, "rb") as f:
        hdr = f.read(20)
    if hdr[:4] == b"\x7fELF" and int.from_bytes(hdr[18:20], "little") == 0xF3:
        import shutil, sys
        q = shutil.which("qemu-riscv64")
        if q and not os.environ.get("RE_LAB_FORCE_RVEMU"):
            return [q, binary]
        return [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             "rvemu.py"), binary]
    return [binary]


def run(binary, stdin_text, timeout=10, env=None):
    """Run the binary with stdin_text (a newline is appended). Returns (rc, stdout)."""
    p = subprocess.run(launcher(binary), input=(stdin_text + "\n").encode(),
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


# --- minimal ELF64 little-endian reader (no third-party deps) -------------
import struct


class Elf:
    """Just enough ELF64 parsing for solvers: sections, symbols, vaddr reads."""

    def __init__(self, path):
        self.data = open(path, "rb").read()
        d = self.data
        if d[:4] != b"\x7fELF" or d[4] != 2 or d[5] != 1:
            raise ValueError("not an ELF64 little-endian file")
        (self.e_shoff,) = struct.unpack_from("<Q", d, 0x28)
        self.e_shentsize, self.e_shnum, self.e_shstrndx = struct.unpack_from("<HHH", d, 0x3A)
        self.sections = []
        for i in range(self.e_shnum):
            off = self.e_shoff + i * self.e_shentsize
            name, typ, flags, addr, offset, size, link, info, align, entsize = \
                struct.unpack_from("<IIQQQQIIQQ", d, off)
            self.sections.append(dict(name_off=name, type=typ, addr=addr, offset=offset,
                                      size=size, link=link, entsize=entsize))
        strtab = self.sections[self.e_shstrndx]
        for s in self.sections:
            s["name"] = self._cstr(strtab["offset"] + s["name_off"])

    def _cstr(self, off):
        end = self.data.index(b"\0", off)
        return self.data[off:end].decode(errors="replace")

    def section(self, name):
        for s in self.sections:
            if s["name"] == name:
                return s
        return None

    def section_bytes(self, name):
        s = self.section(name)
        return None if s is None else self.data[s["offset"]:s["offset"] + s["size"]]

    def symbols(self):
        """dict name -> (value/vaddr, size) from .symtab (empty if stripped)."""
        out = {}
        for s in self.sections:
            if s["type"] != 2:  # SHT_SYMTAB
                continue
            strs = self.sections[s["link"]]["offset"]
            for i in range(s["size"] // 24):
                st_name, st_info, st_other, st_shndx, st_value, st_size = \
                    struct.unpack_from("<IBBHQQ", self.data, s["offset"] + i * 24)
                if st_name:
                    out[self._cstr(strs + st_name)] = (st_value, st_size)
        return out

    def read_vaddr(self, vaddr, size):
        """Read bytes at a virtual address (via the section that contains it)."""
        for s in self.sections:
            if s["type"] != 8 and s["addr"] and s["addr"] <= vaddr < s["addr"] + s["size"]:
                off = s["offset"] + (vaddr - s["addr"])
                return self.data[off:off + size]
        raise ValueError(f"vaddr {vaddr:#x} not in any file-backed section")

    def symbol_bytes(self, name):
        addr, size = self.symbols()[name]
        return self.read_vaddr(addr, size)

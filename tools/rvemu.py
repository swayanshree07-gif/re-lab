#!/usr/bin/env python3
"""Tiny RV64IM user-mode emulator (stand-in for qemu-riscv64, which is not
installed here). Static ELF64 little-endian only; no compressed (C)
instructions, no floating point, no atomics.

Syscalls: read(63), write(64), exit(93), exit_group(94). Anything else
returns -ENOSYS.

CLI:  rvemu.py [-t] [-n MAXSTEPS] <elf>   (stdin/stdout passed through,
      exit status = guest exit code; -t prints the instruction count to stderr)
API:  run(path, stdin_bytes) -> (exit_code, stdout_bytes, instret)
"""
import struct, sys

MASK = (1 << 64) - 1
STACK_TOP = 0x7fff_0000
STACK_SIZE = 0x10000


class Fault(Exception):
    pass


def sx(v, bits):
    v &= (1 << bits) - 1
    return v - (1 << bits) if v >> (bits - 1) else v


def s64(v):
    return sx(v, 64)


class Machine:
    def __init__(self, path, stdin=b""):
        data = open(path, "rb").read()
        if data[:4] != b"\x7fELF" or data[4] != 2 or data[5] != 1:
            raise Fault("not an ELF64 little-endian file")
        e_machine, = struct.unpack_from("<H", data, 18)
        if e_machine != 0xF3:
            raise Fault(f"not RISC-V (e_machine={e_machine:#x})")
        self.pc, = struct.unpack_from("<Q", data, 24)
        phoff, = struct.unpack_from("<Q", data, 32)
        phentsize, phnum = struct.unpack_from("<HH", data, 54)
        self.segs = []  # [base, bytearray, writable]
        for i in range(phnum):
            p_type, p_flags, p_off, p_vaddr, _, p_filesz, p_memsz, _ = \
                struct.unpack_from("<IIQQQQQQ", data, phoff + i * phentsize)
            if p_type != 1:  # PT_LOAD
                continue
            mem = bytearray(data[p_off:p_off + p_filesz]) + bytearray(p_memsz - p_filesz)
            self.segs.append([p_vaddr, mem, bool(p_flags & 2)])
        self.segs.append([STACK_TOP - STACK_SIZE, bytearray(STACK_SIZE), True])
        self.x = [0] * 32
        sp = STACK_TOP - 64
        self.x[2] = sp  # argc=0, argv=NULL, envp=NULL, auxv AT_NULL (all zero)
        self.stdin = stdin
        self.stdout = bytearray()
        self.exit_code = None
        self.instret = 0

    # memory -----------------------------------------------------------
    def _seg(self, addr, n):
        for base, mem, w in self.segs:
            if base <= addr and addr + n <= base + len(mem):
                return base, mem, w
        raise Fault(f"bad memory access at {addr:#x} (pc={self.pc:#x})")

    def load(self, addr, n, signed=False):
        base, mem, _ = self._seg(addr, n)
        return int.from_bytes(mem[addr - base:addr - base + n], "little", signed=signed)

    def store(self, addr, n, val):
        base, mem, w = self._seg(addr, n)
        if not w:
            raise Fault(f"write to read-only memory at {addr:#x} (pc={self.pc:#x})")
        mem[addr - base:addr - base + n] = (val & ((1 << (8 * n)) - 1)).to_bytes(n, "little")

    # syscalls -----------------------------------------------------------
    def ecall(self):
        x = self.x
        num, a0, a1, a2 = x[17], x[10], x[11], x[12]
        if num == 63:  # read
            chunk = self.stdin[:a2] if a0 == 0 else b""
            self.stdin = self.stdin[len(chunk):]
            for i, b in enumerate(chunk):
                self.store(a1 + i, 1, b)
            x[10] = len(chunk)
        elif num == 64:  # write
            buf = bytes(self.load(a1 + i, 1) for i in range(a2))
            if a0 in (1, 2):
                self.stdout += buf
            x[10] = a2
        elif num in (93, 94):
            self.exit_code = a0 & 0xff
        else:
            x[10] = (-38) & MASK

    # execution ----------------------------------------------------------
    def step(self):
        x = self.x
        pc = self.pc
        ins = self.load(pc, 4)
        if ins & 3 != 3:
            raise Fault(f"compressed instruction at {pc:#x} (not supported)")
        op = ins & 0x7f
        rd = (ins >> 7) & 31
        f3 = (ins >> 12) & 7
        rs1 = (ins >> 15) & 31
        rs2 = (ins >> 20) & 31
        f7 = ins >> 25
        a, b = x[rs1], x[rs2]
        npc = pc + 4
        res = None
        if op == 0x37:  # LUI
            res = sx(ins & 0xfffff000, 32)
        elif op == 0x17:  # AUIPC
            res = pc + sx(ins & 0xfffff000, 32)
        elif op == 0x6f:  # JAL
            imm = ((ins >> 31) << 20) | (((ins >> 12) & 0xff) << 12) | \
                (((ins >> 20) & 1) << 11) | (((ins >> 21) & 0x3ff) << 1)
            res = npc
            npc = pc + sx(imm, 21)
        elif op == 0x67:  # JALR
            res = npc
            npc = (a + sx(ins >> 20, 12)) & ~1
        elif op == 0x63:  # branches
            imm = ((ins >> 31) << 12) | (((ins >> 7) & 1) << 11) | \
                (((ins >> 25) & 0x3f) << 5) | (((ins >> 8) & 0xf) << 1)
            sa, sb = s64(a), s64(b)
            take = {0: a == b, 1: a != b, 4: sa < sb, 5: sa >= sb,
                    6: a < b, 7: a >= b}.get(f3)
            if take is None:
                raise Fault(f"bad branch at {pc:#x}")
            if take:
                npc = pc + sx(imm, 13)
        elif op == 0x03:  # loads
            addr = (a + sx(ins >> 20, 12)) & MASK
            size = {0: 1, 1: 2, 2: 4, 3: 8, 4: 1, 5: 2, 6: 4}[f3]
            res = self.load(addr, size, signed=f3 < 4)
        elif op == 0x23:  # stores
            imm = sx(((ins >> 25) << 5) | ((ins >> 7) & 31), 12)
            self.store((a + imm) & MASK, 1 << f3, b)
        elif op in (0x13, 0x1b):  # OP-IMM / OP-IMM-32
            imm = sx(ins >> 20, 12)
            w = op == 0x1b
            sh = (ins >> 20) & (31 if w else 63)
            if f3 == 0:
                res = a + imm
            elif f3 == 1:
                res = a << sh
            elif f3 == 5:
                src = a & 0xffffffff if w else a
                if ins >> 30 & 1:
                    res = (sx(src, 32) if w else s64(src)) >> sh
                else:
                    res = src >> sh
            elif not w and f3 == 2:
                res = int(s64(a) < imm)
            elif not w and f3 == 3:
                res = int(a < (imm & MASK))
            elif not w and f3 == 4:
                res = a ^ (imm & MASK)
            elif not w and f3 == 6:
                res = a | (imm & MASK)
            elif not w and f3 == 7:
                res = a & (imm & MASK)
            else:
                raise Fault(f"bad OP-IMM at {pc:#x}")
            if w:
                res = sx(res, 32)
        elif op in (0x33, 0x3b):  # OP / OP-32
            w = op == 0x3b
            if w:
                a32, b32 = a & 0xffffffff, b & 0xffffffff
            if f7 == 1:  # M extension
                if w:
                    sa, sb = sx(a32, 32), sx(b32, 32)
                    if f3 == 0:
                        res = sa * sb
                    elif f3 in (4, 6):  # DIVW / REMW
                        q = -1 if sb == 0 else (abs(sa) // abs(sb)) * (1 if (sa < 0) == (sb < 0) else -1)
                        res = q if f3 == 4 else (sa if sb == 0 else sa - q * sb)
                    elif f3 in (5, 7):  # DIVUW / REMUW
                        q = 0xffffffff if b32 == 0 else a32 // b32
                        res = q if f3 == 5 else (a32 if b32 == 0 else a32 % b32)
                    else:
                        raise Fault(f"bad OP-32 M at {pc:#x}")
                    res = sx(res, 32)
                else:
                    sa, sb = s64(a), s64(b)
                    if f3 == 0:
                        res = a * b
                    elif f3 == 1:
                        res = (sa * sb) >> 64
                    elif f3 == 2:
                        res = (sa * b) >> 64
                    elif f3 == 3:
                        res = (a * b) >> 64
                    elif f3 in (4, 6):
                        q = -1 if sb == 0 else (abs(sa) // abs(sb)) * (1 if (sa < 0) == (sb < 0) else -1)
                        res = q if f3 == 4 else (sa if sb == 0 else sa - q * sb)
                    else:
                        q = MASK if b == 0 else a // b
                        res = q if f3 == 5 else (a if b == 0 else a % b)
            elif w:
                sh = b32 & 31
                key = (f3, f7)
                if key == (0, 0):
                    res = a32 + b32
                elif key == (0, 0x20):
                    res = a32 - b32
                elif key == (1, 0):
                    res = a32 << sh
                elif key == (5, 0):
                    res = a32 >> sh
                elif key == (5, 0x20):
                    res = sx(a32, 32) >> sh
                else:
                    raise Fault(f"bad OP-32 at {pc:#x}")
                res = sx(res, 32)
            else:
                sh = b & 63
                key = (f3, f7)
                if key == (0, 0):
                    res = a + b
                elif key == (0, 0x20):
                    res = a - b
                elif key == (1, 0):
                    res = a << sh
                elif key == (2, 0):
                    res = int(s64(a) < s64(b))
                elif key == (3, 0):
                    res = int(a < b)
                elif key == (4, 0):
                    res = a ^ b
                elif key == (5, 0):
                    res = a >> sh
                elif key == (5, 0x20):
                    res = s64(a) >> sh
                elif key == (6, 0):
                    res = a | b
                elif key == (7, 0):
                    res = a & b
                else:
                    raise Fault(f"bad OP at {pc:#x}")
        elif op == 0x0f:  # FENCE: no-op
            pass
        elif op == 0x73 and ins == 0x00000073:  # ECALL
            self.ecall()
        else:
            raise Fault(f"unsupported instruction {ins:#010x} at {pc:#x}")
        if res is not None and rd:
            x[rd] = res & MASK
        self.pc = npc & MASK
        self.instret += 1

    def run(self, max_steps=10_000_000):
        while self.exit_code is None:
            if self.instret >= max_steps:
                raise Fault(f"step limit {max_steps} reached")
            self.step()
        return self.exit_code


def run(path, stdin=b"", max_steps=10_000_000):
    m = Machine(path, stdin)
    rc = m.run(max_steps)
    return rc, bytes(m.stdout), m.instret


def main(argv):
    trace, max_steps, args = False, 10_000_000, list(argv)
    while args and args[0].startswith("-"):
        o = args.pop(0)
        if o == "-t":
            trace = True
        elif o == "-n":
            max_steps = int(args.pop(0))
        else:
            break
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        rc, out, n = run(args[0], sys.stdin.buffer.read(), max_steps)
    except Fault as e:
        print(f"rvemu: {e}", file=sys.stderr)
        return 139
    sys.stdout.buffer.write(out)
    sys.stdout.flush()
    if trace:
        print(f"rvemu: {n} instructions", file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

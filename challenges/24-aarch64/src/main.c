/* 24-aarch64: freestanding AArch64 keygen crackme (no libc). Spoiler source.
 * The x86_64 branch of sys3() only exists so the test suite can build a
 * native twin when qemu-aarch64 is missing; the challenge is the AArch64 ELF. */
static const unsigned ktab[4] = {0x9e3779b9u, 0x7f4a7c15u, 0x85ebca6bu, 0xc2b2ae35u};

static long sys3(long n, long a, long b, long c) {
#if defined(__aarch64__)
    register long x0 asm("x0") = a;
    register long x1 asm("x1") = b;
    register long x2 asm("x2") = c;
    register long x8 asm("x8") = n;
    asm volatile("svc #0" : "+r"(x0) : "r"(x1), "r"(x2), "r"(x8) : "memory");
    return x0;
#elif defined(__x86_64__)
    static const long map[] = {[63] = 0, [64] = 1, [93] = 60};
    long r;
    asm volatile("syscall" : "=a"(r) : "a"(map[n]), "D"(a), "S"(b), "d"(c) : "rcx", "r11", "memory");
    return r;
#else
#error unsupported
#endif
}

static void say(const char *s) {
    long n = 0;
    while (s[n]) n++;
    sys3(64, 1, (long)s, n);
}

static __attribute__((noreturn)) void quit(int code) {
    sys3(93, code, 0, 0);
    for (;;) {}
}

static long readline(char *buf, long cap) {
    long len = 0;
    while (len < cap) {
        if (sys3(63, 0, (long)(buf + len), 1) != 1 || buf[len] == '\n') break;
        len++;
    }
    return len;
}

static unsigned ror32(unsigned x, int r) { return (x >> r) | (x << (32 - r)); }

__attribute__((noinline)) unsigned make_serial(const unsigned char *name, long len) {
    unsigned h = 0x1f3a5c77u, sum = 0;
    for (long i = 0; i < len; i++) {
        h = ror32(h ^ name[i], 7) * 0x2c9277b5u + ktab[i & 3];
        sum += name[i];
    }
    return h ^ (sum << 16) ^ (unsigned)len;
}

static int check(const char *name, long nlen, const char *ser, long slen) {
    if (nlen < 4 || nlen > 32 || slen != 9 || ser[4] != '-') return 0;
    for (long i = 0; i < nlen; i++)
        if (name[i] < 0x20 || name[i] > 0x7e) return 0;
    unsigned want = make_serial((const unsigned char *)name, nlen), got = 0;
    for (long i = 0; i < 9; i++) {
        if (i == 4) continue;
        char c = ser[i];
        unsigned d;
        if (c >= '0' && c <= '9') d = c - '0';
        else if (c >= 'A' && c <= 'F') d = c - 'A' + 10;
        else return 0;
        got = got << 4 | d;
    }
    return got == want;
}

void _start(void) {
    static char name[64], ser[64];
    say("Name: ");
    long nlen = readline(name, sizeof name);
    say("Serial: ");
    long slen = readline(ser, sizeof ser);
    if (check(name, nlen, ser, slen)) { say("Correct!\n"); quit(0); }
    say("Wrong.\n");
    quit(1);
}

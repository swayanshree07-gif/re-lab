/* 23-riscv: freestanding RV64IM crackme (no libc). Spoiler source. */
#include "table.h"

static long sys3(long n, long a, long b, long c) {
    register long a0 asm("a0") = a;
    register long a1 asm("a1") = b;
    register long a2 asm("a2") = c;
    register long a7 asm("a7") = n;
    asm volatile("ecall" : "+r"(a0) : "r"(a1), "r"(a2), "r"(a7) : "memory");
    return a0;
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

static int check(const unsigned char *s, long len) {
    if (len != PW_LEN) return 0;
    unsigned h = 0x5a;
    for (long i = 0; i < len; i++) {
        unsigned t = ((s[i] * 37u + h) ^ (unsigned)(i * 11 + 0x3c)) & 0xff;
        if (t != expected[i]) return 0;
        h = (h * 131u + s[i]) & 0xffff;
    }
    return 1;
}

void _start(void) {
    static unsigned char buf[128];
    long len = 0;
    say("Password: ");
    while (len < (long)sizeof buf) {
        if (sys3(63, 0, (long)(buf + len), 1) != 1 || buf[len] == '\n') break;
        len++;
    }
    if (check(buf, len)) { say("Correct!\n"); quit(0); }
    say("Wrong.\n");
    quit(1);
}

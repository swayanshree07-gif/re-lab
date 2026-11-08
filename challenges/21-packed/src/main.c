/* 21-packed stub (spoiler!). The check code isn't in this file: it lives in
 * packed[] (generated), is decrypted + decompressed into a fresh mmap page,
 * made executable and called. */
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include "packed.h"

typedef int (*check_fn)(const unsigned char *, unsigned long);

static unsigned char *unpack(void) {
    unsigned char *dst = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                              MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (dst == MAP_FAILED) return NULL;
    unsigned char s = PACK_SEED;
    size_t ip = 0, op = 0;
#define NEXT() (s = (unsigned char)(s * 0x1d + 0x4b), (unsigned char)(packed[ip++] ^ s))
    while (ip < sizeof packed && op < UNPACKED_SIZE) {
        unsigned char t = NEXT();
        if (t < 0x80) {
            for (int k = 0; k <= t && ip < sizeof packed && op < 4096; k++) dst[op++] = NEXT();
        } else {
            unsigned len = t - 0x80 + 3;
            unsigned off = NEXT();
            off |= (unsigned)NEXT() << 8;
            if (off == 0 || off > op || op + len > 4096) return NULL;
            for (unsigned k = 0; k < len; k++, op++) dst[op] = dst[op - off];
        }
    }
    if (op != UNPACKED_SIZE || mprotect(dst, 4096, PROT_READ | PROT_EXEC) != 0) return NULL;
    return dst;
}

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) buf[0] = 0;
    buf[strcspn(buf, "\n")] = 0;
    unsigned char *code = unpack();
    if (!code) { puts("Wrong."); return 1; }
    int ok = ((check_fn)code)((const unsigned char *)buf, strlen(buf));
    munmap(code, 4096);
    puts(ok ? "Correct!" : "Wrong.");
    return ok ? 0 : 1;
}

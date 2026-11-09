/* 28-boss (SPOILER). Stage 1 of the final boss, built stripped.
 * Anti-debug never branches to "Wrong." directly: three salts (0 on a clean
 * run) are mixed into the stage-1 keystream.
 *   salts[0] ptrace(PTRACE_TRACEME) twice (constructor)
 *   salts[1] TracerPid from /proc/self/status
 *   salts[2] busy-loop wall time > 250 ms
 * A correct stage-1 key is also the decryption key of the packed stage 2
 * (s2_blob), which is unpacked into an mmap page and called. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/mman.h>
#include <sys/ptrace.h>
#include "stage1.h"
#include "stage2_packed.h"

static unsigned int salts[3];

static unsigned int tracer_pid(void) {
    FILE *f = fopen("/proc/self/status", "r");
    char line[256];
    unsigned int pid = 0;
    if (!f) return 0x6666;
    while (fgets(line, sizeof line, f))
        if (!strncmp(line, "TracerPid:", 10)) { pid = (unsigned)strtoul(line + 10, NULL, 10); break; }
    fclose(f);
    return pid;
}

__attribute__((constructor)) static void probe(void) {
    salts[1] = tracer_pid();
    long a = ptrace(PTRACE_TRACEME, 0, NULL, NULL);
    long b = ptrace(PTRACE_TRACEME, 0, NULL, NULL);
    salts[0] = (unsigned)(a != 0) * 0x3301 + (unsigned)(b != -1) * 0x10000;
}

static unsigned int timing(void) {
    struct timespec t0, t1;
    volatile unsigned int x = 1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < 200000; i++) x = x * 33 + (unsigned)i;
    clock_gettime(CLOCK_MONOTONIC, &t1);
    long ms = (t1.tv_sec - t0.tv_sec) * 1000 + (t1.tv_nsec - t0.tv_nsec) / 1000000;
    return ms > 250 ? (unsigned)ms : 0;
}

static unsigned int mix(unsigned int s, unsigned int v) {
    s = (s ^ v) * 0x9E3779B1u;
    return (s << 13) | (s >> 19);
}

static unsigned int xs(unsigned int s) { s ^= s << 13; s ^= s >> 17; s ^= s << 5; return s; }

static int stage1(const char *in, size_t n) {
    unsigned int s = S1_SEED, diff = 0;
    for (int k = 0; k < 3; k++) s = mix(s, salts[k]);
    if (n != S1_LEN) return 0;
    for (int i = 0; i < S1_LEN; i++) {
        s = xs(s);
        diff |= ((unsigned char)in[s1_perm[i]] ^ (unsigned char)(s + 13 * i)) ^ s1_ct[i];
    }
    return diff == 0;
}

static unsigned int fnv(const unsigned char *p, size_t n) {
    unsigned int h = 0x811C9DC5u;
    while (n--) h = (h ^ *p++) * 0x01000193u;
    return h;
}

typedef int (*stage_fn)(const unsigned char *, unsigned long);

static unsigned char *unpack(const char *key) {
    unsigned char *dst = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (dst == MAP_FAILED) return NULL;
    unsigned int s = fnv((const unsigned char *)key, strlen(key)) ^ PACK_SALT;
    if (!s) s = 1;
    size_t ip = 0, op = 0;
#define NEXT() (s = xs(s), (unsigned char)(s2_blob[ip++] ^ (s >> 24)))
    while (ip < sizeof s2_blob && op < S2_SIZE) {
        unsigned char t = NEXT();
        if (t < 0x80) {
            for (int k = 0; k <= t && ip < sizeof s2_blob && op < 4096; k++) dst[op++] = NEXT();
        } else {
            unsigned len = t - 0x80 + 3, off = NEXT();
            off |= (unsigned)NEXT() << 8;
            if (off == 0 || off > op || op + len > 4096) goto bad;
            for (unsigned k = 0; k < len; k++, op++) dst[op] = dst[op - off];
        }
    }
    if (op != S2_SIZE || fnv(dst, op) != S2_FNV || mprotect(dst, 4096, PROT_READ | PROT_EXEC)) goto bad;
    return dst;
bad:
    munmap(dst, 4096);
    return NULL;
}

int main(void) {
    char buf[160];
    salts[2] = timing();
    printf("Key: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) buf[0] = 0;
    buf[strcspn(buf, "\n")] = 0;
    /* stage 1 key is the part before the first '|' (later stages follow it) */
    char *rest = strchr(buf, '|');
    if (rest) *rest++ = 0; else rest = buf + strlen(buf);
    if (!stage1(buf, strlen(buf))) { puts("Wrong."); return 1; }
    unsigned char *code = unpack(buf);
    if (!code) { puts("Wrong."); return 1; }
    puts("Stage 1 clear.");
    int r = ((stage_fn)code)((const unsigned char *)rest, strlen(rest));
    munmap(code, 4096);
    if (r != 0x5732) { puts("Wrong."); return 1; }
    puts("Correct!");
    return 0;
}

/* 22-antidebug-mix — SPOILER: solution source.
 * Four detectors, none of which branches to "Wrong." directly. Each yields a
 * 32-bit salt that is 0 on a clean run, and all four are mixed into the
 * keystream state:
 *   salts[0] ptrace(PTRACE_TRACEME) twice (constructor): traced or faked -> != 0
 *   salts[1] TracerPid from /proc/self/status
 *   salts[2] wall time of a fixed busy loop (> 250 ms -> elapsed ms)
 *   (inline) FNV-1a of region_begin..region_end ^ expected (int3 -> != 0)
 * Patching one jump only fixes one salt; the key is still wrong.
 * Password in SPOILERS; gen.py makes table.h, patch_hash.py fills `expected`. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/ptrace.h>
#include "table.h"

unsigned int salts[3];
volatile unsigned int expected = 0x1BADC0DE;   /* patched after linking */

static unsigned int tracer_pid(void) {
    FILE *f = fopen("/proc/self/status", "r");
    char line[256];
    unsigned int pid = 0;
    if (!f) return 0x7777;           /* hidden /proc counts as suspicious */
    while (fgets(line, sizeof line, f))
        if (!strncmp(line, "TracerPid:", 10)) { pid = (unsigned)strtoul(line + 10, NULL, 10); break; }
    fclose(f);
    return pid;
}

/* TracerPid must be read first: our own TRACEME makes the parent the tracer. */
__attribute__((constructor)) static void probe_ptrace(void) {
    salts[1] = tracer_pid();
    long a = ptrace(PTRACE_TRACEME, 0, NULL, NULL);
    long b = ptrace(PTRACE_TRACEME, 0, NULL, NULL);
    salts[0] = (unsigned)(a != 0) * 0x51 + (unsigned)(b != -1) * 0x2700;
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

__attribute__((noinline)) void region_begin(void) { __asm__ volatile(""); }
void region_end_marker(void);

static unsigned int mix(unsigned int s, unsigned int v) {
    s = (s ^ v) * 0x9E3779B1u;
    return (s << 13) | (s >> 19);
}

__attribute__((noinline)) unsigned int derive_key(void) {
    const unsigned char *p = (const unsigned char *)region_begin;
    const unsigned char *e = (const unsigned char *)region_end_marker;
    unsigned int h = 0x811C9DC5u, s = SEED;
    for (; p < e; p++) h = (h ^ *p) * 0x01000193u;
    s = mix(s, salts[0]);
    s = mix(s, salts[1]);
    s = mix(s, salts[2]);
    return mix(s, h ^ expected);
}

__attribute__((noinline)) int check(const char *in) {
    unsigned int st = derive_key(), diff = 0;
    if (strlen(in) != PW_LEN) return 0;
    for (int i = 0; i < PW_LEN; i++) {
        st ^= st << 13; st ^= st >> 17; st ^= st << 5;
        diff |= (unsigned char)(in[i] ^ (unsigned char)(st + 7 * i)) ^ table[i];
    }
    return diff == 0;
}

__attribute__((noinline)) void region_end_marker(void) { __asm__ volatile(""); }

int main(void) {
    char buf[128];
    salts[2] = timing();
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    if (check(buf)) { puts("Correct! Nothing was watching."); return 0; }
    puts("Wrong.");
    return 1;
}

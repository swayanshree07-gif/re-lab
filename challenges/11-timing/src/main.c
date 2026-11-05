/* 11-timing — SPOILER: this is the solution source.
 * The check loop is timed twice: rdtsc (CPU cycles) and
 * clock_gettime(CLOCK_MONOTONIC). If either says the check took too long
 * (a breakpoint, single-stepping), the verdict is silently taken from the
 * decoy comparison instead of the real one.
 * Encoding: enc[i] = (in[i] ^ (key + 7*i)) & 0xff.
 * Real password: t1m3_fl135 (key 0x3c). Decoy: sl0w_st3p! (key 0x91). */
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <x86intrin.h>

#define PW_LEN 10
#define MAX_NS    20000000ULL   /* 20 ms */
#define MAX_TSC   80000000ULL   /* ~20-40 ms of cycles */

static const unsigned char keys[2] = { 0x3c, 0x91 };
static const unsigned char enc[2][PW_LEN] = {
    { 0x48, 0x72, 0x27, 0x62, 0x07, 0x39, 0x0a, 0x5c, 0x47, 0x4e },
    { 0xe2, 0xf4, 0xaf, 0xd1, 0xf2, 0xc7, 0xcf, 0xf1, 0xb9, 0xf1 },
};

static int slow;   /* 1 = the check was too slow (debugger) */

static unsigned long long now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (unsigned long long)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

static int compare(const char *in, int which) {
    int ok = 1;
    for (int i = 0; i < PW_LEN; i++) {
        unsigned char k = (unsigned char)(keys[which] + 7 * i);
        if ((unsigned char)(in[i] ^ k) != enc[which][i]) ok = 0;
    }
    return ok;
}

static int check(const char *in) {
    if (strlen(in) != PW_LEN) return 0;
    unsigned long long t0 = now_ns();
    unsigned long long c0 = __rdtsc();
    int real = compare(in, 0);
    int decoy = compare(in, 1);
    unsigned long long c1 = __rdtsc();
    unsigned long long t1 = now_ns();
    if (t1 - t0 > MAX_NS || c1 - c0 > MAX_TSC)
        slow = 1;
    return slow ? decoy : real;
}

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    if (check(buf)) {
        puts("Correct! Right on time.");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

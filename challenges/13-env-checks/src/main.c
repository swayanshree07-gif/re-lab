/* 13-env-checks — SPOILER: solution source.
 * probe() runs three environment checks before the password check and records
 * bits in env_mask:
 *   1 = TracerPid in /proc/self/status is not 0
 *   2 = LD_PRELOAD= or LD_AUDIT= set to a non-empty value (environ walked by hand)
 *   4 = parent's /proc/<ppid>/comm is a known analysis tool name
 * File reads use raw syscalls so ltrace / libc-function hooks don't see them.
 * Strings used by the checks are XOR-encoded (gen_tables.py), decoded on the
 * stack only while needed. Any bit set -> the decoy password is accepted.
 * Check: rotl8(in[i] ^ (key + 11*i), 3) == pw_enc[mask != 0][i]
 * Real: 3nv_l00ks_ok   Decoy: c4ught_y0u!! */
#include <stdio.h>
#include <string.h>

#include "tables.h"

extern char **environ;

int env_mask;

#define SYS_read 0
#define SYS_open 2
#define SYS_close 3
#define SYS_getppid 110

static long sc3(long n, long a, long b, long c) {
    long r;
    __asm__ volatile("syscall" : "=a"(r)
                     : "a"(n), "D"(a), "S"(b), "d"(c) : "rcx", "r11", "memory");
    return r;
}

static void unhide(char *out, const unsigned char *in, int n, unsigned char seed) {
    for (int i = 0; i < n; i++) out[i] = (char)(in[i] ^ (unsigned char)(seed + 7 * i));
}

static void wipe(char *p, int n) {
    volatile char *v = p;
    while (n--) *v++ = 0;
}

static long slurp(const char *path, char *buf, long cap) {
    long fd = sc3(SYS_open, (long)path, 0, 0);
    if (fd < 0) return -1;
    long len = 0, r;
    while (len < cap - 1 && (r = sc3(SYS_read, fd, (long)(buf + len), cap - 1 - len)) > 0)
        len += r;
    sc3(SYS_close, fd, 0, 0);
    buf[len] = 0;
    return len;
}

static int traced(void) {
    char path[S_STATUS_LEN], key[S_TRACER_LEN], buf[4096];
    int hit = 0;
    unhide(path, s_status, S_STATUS_LEN, S_STATUS_SEED);
    unhide(key, s_tracer, S_TRACER_LEN, S_TRACER_SEED);
    if (slurp(path, buf, sizeof buf) > 0) {
        char *p = strstr(buf, key);
        if (p) {
            p += S_TRACER_LEN - 1;
            while (*p == ' ' || *p == '\t') p++;
            long pid = 0;
            while (*p >= '0' && *p <= '9') pid = pid * 10 + (*p++ - '0');
            hit = pid != 0;
        }
    }
    wipe(path, sizeof path);
    wipe(key, sizeof key);
    return hit;
}

static int preloaded(void) {
    char a[S_PRELOAD_LEN], b[S_AUDIT_LEN];
    int hit = 0;
    unhide(a, s_preload, S_PRELOAD_LEN, S_PRELOAD_SEED);
    unhide(b, s_audit, S_AUDIT_LEN, S_AUDIT_SEED);
    for (char **e = environ; e && *e; e++) {
        if (strncmp(*e, a, S_PRELOAD_LEN - 1) == 0 && (*e)[S_PRELOAD_LEN - 1]) hit = 1;
        if (strncmp(*e, b, S_AUDIT_LEN - 1) == 0 && (*e)[S_AUDIT_LEN - 1]) hit = 1;
    }
    wipe(a, sizeof a);
    wipe(b, sizeof b);
    return hit;
}

static int bad_parent(void) {
    char path[64], comm[64], names[S_PARENTS_LEN], digits[24];
    int n = 0, hit = 0;
    long ppid = sc3(SYS_getppid, 0, 0, 0);
    do { digits[n++] = (char)('0' + ppid % 10); ppid /= 10; } while (ppid && n < 20);
    unhide(path, s_proc, S_PROC_LEN, S_PROC_SEED);
    int len = S_PROC_LEN - 1;
    while (n) path[len++] = digits[--n];
    unhide(path + len, s_comm, S_COMM_LEN, S_COMM_SEED);
    if (slurp(path, comm, sizeof comm) > 0) {
        comm[strcspn(comm, "\n")] = 0;
        unhide(names, s_parents, S_PARENTS_LEN, S_PARENTS_SEED);
        char *bar;
        for (char *tok = names; tok; tok = bar ? bar + 1 : NULL) {
            bar = strchr(tok, '|');
            size_t tl = bar ? (size_t)(bar - tok) : strlen(tok);
            if (tl == strlen(comm) && strncmp(tok, comm, tl) == 0) hit = 1;
        }
        wipe(names, sizeof names);
    }
    wipe(path, sizeof path);
    return hit;
}

static void probe(void) {
    env_mask = 0;
    if (traced()) env_mask |= 1;
    if (preloaded()) env_mask |= 2;
    if (bad_parent()) env_mask |= 4;
}

static unsigned char rotl8(unsigned char x, int r) {
    return (unsigned char)((x << r) | (x >> (8 - r)));
}

static int check(const char *in) {
    if (strlen(in) != PW_LEN) return 0;
    int row = env_mask != 0;
    unsigned char k = pw_keys[row];
    int ok = 1;
    for (int i = 0; i < PW_LEN; i++)
        if (rotl8((unsigned char)(in[i] ^ (unsigned char)(k + 11 * i)), 3) != pw_enc[row][i]) ok = 0;
    return ok;
}

int main(void) {
    char buf[128];
    probe();
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    if (check(buf)) {
        puts("Correct! A clean environment.");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

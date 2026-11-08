/* 17-opaque (SPOILER: this is the source).
 * Name + serial keygen check hidden behind opaque predicates and junk code.
 *
 * Real algorithm (K[] lives in .data):
 *   h = K[0]; s = 0
 *   for c in name: h = (h ^ c) * K[1]; h ^= h >> 15; s += c * (i + 1)
 *   a = h; b = rotl32(h, 13) ^ K[2]; c = (s * len) ^ K[3]
 *   serial = "%04X-%04X-%04X-%04X" of a>>16, b&0xffff, c&0xffff, (a^b^c)>>16
 *
 * Opaque predicates (value known to the author, not obvious to a decompiler):
 *   OP_TRUE1(x)  x*(x+1) is always even
 *   OP_TRUE2(x)  x*x mod 4 is 0 or 1
 *   OP_FALSE(x,y) 7*y*y - 1 == x*x  never holds (squares mod 7 are 0,1,2,4)
 * Their inputs come from `volatile` globals so gcc cannot fold them.
 * Decoys: validate_license() / pro_check() look like the real check and
 * reference a tempting "PRO-" format, but are only called on opaque-false paths.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

uint32_t K[4] = {0x9e3779b1u, 0x01000193u, 0x5eed1e55u, 0x0000c0deu};
volatile uint32_t noise = 0x1337;      /* feeds the opaque predicates */
volatile uint32_t sink;                /* junk code writes here */

#define OP_TRUE1(x)   ((((uint32_t)(x)) * ((uint32_t)(x) + 1u)) % 2u == 0u)
#define OP_TRUE2(x)   ((((uint32_t)(x)) * ((uint32_t)(x))) % 4u < 2u)
#define OP_FALSE(x,y) ((7u * ((uint32_t)(y) % 7u) * ((uint32_t)(y) % 7u)) % 7u == \
                       (((uint32_t)(x) % 7u) * ((uint32_t)(x) % 7u) + 1u) % 7u)

static uint32_t rotl32(uint32_t v, int r) { return (v << r) | (v >> (32 - r)); }

/* ---- decoys: look plausible, never reached ---- */
__attribute__((noinline)) int pro_check(const char *serial)
{
    static const char fmt[] = "PRO-%08X-LIC";
    char buf[32];
    snprintf(buf, sizeof buf, fmt, K[0] ^ 0xdeadbeefu);
    return strcmp(serial, buf) == 0;
}

__attribute__((noinline)) int validate_license(const char *name, const char *serial)
{
    uint32_t h = 0x811c9dc5u;
    for (size_t i = 0; name[i]; i++) h = (h ^ (uint8_t)name[i]) * 16777619u;
    char buf[32];
    snprintf(buf, sizeof buf, "%08X-%08X", h, h ^ K[2]);
    return strcmp(serial, buf) == 0 || pro_check(serial);
}

/* ---- real logic, wrapped in junk ---- */
__attribute__((noinline)) static void junk(uint32_t v)
{
    uint32_t t = v;
    for (int i = 0; i < 3; i++) { t = rotl32(t ^ 0xa5a5a5a5u, 7) + (uint32_t)i; }
    if (OP_FALSE(t, noise)) t = 0;        /* never */
    sink = t;
}

__attribute__((noinline)) void make_serial(const char *name, char *out)
{
    uint32_t h = K[0], s = 0, n = noise;
    size_t len = strlen(name);
    for (size_t i = 0; i < len; i++) {
        uint8_t c = (uint8_t)name[i];
        if (OP_TRUE1(n + i)) {
            h = (h ^ c) * K[1];
        } else {
            h = (h + c) * 0x45d9f3bu;     /* dead */
        }
        junk(h);
        if (OP_TRUE2(h ^ n)) h ^= h >> 15;
        else h = rotl32(h, 3);            /* dead */
        if (OP_FALSE(h, c)) s -= c;       /* dead */
        else s += (uint32_t)c * (uint32_t)(i + 1);
    }
    uint32_t a = h, b = rotl32(h, 13) ^ K[2], c = (s * (uint32_t)len) ^ K[3];
    if (OP_FALSE(a, b)) { a = b; junk(a); }  /* dead */
    snprintf(out, 32, "%04X-%04X-%04X-%04X",
             a >> 16, b & 0xffff, c & 0xffff, (a ^ b ^ c) >> 16);
}

static void chomp(char *s) { s[strcspn(s, "\r\n")] = 0; }

int main(void)
{
    char name[64], serial[64], want[32];
    printf("Name: ");
    fflush(stdout);
    if (!fgets(name, sizeof name, stdin)) { puts("Wrong."); return 1; }
    printf("Serial: ");
    fflush(stdout);
    if (!fgets(serial, sizeof serial, stdin)) { puts("Wrong."); return 1; }
    chomp(name); chomp(serial);
    if (strlen(name) < 4) { puts("Wrong."); return 1; }

    int ok;
    if (OP_FALSE(noise, strlen(name))) {
        ok = validate_license(name, serial);   /* decoy, never */
    } else if (OP_TRUE1(noise ^ (uint32_t)strlen(serial))) {
        make_serial(name, want);
        junk((uint32_t)want[0]);
        ok = strcmp(serial, want) == 0;
    } else {
        ok = validate_license(name, serial);   /* decoy, never */
    }
    if (ok) { printf("Correct! Registered to %s.\n", name); return 0; }
    puts("Wrong.");
    return 1;
}

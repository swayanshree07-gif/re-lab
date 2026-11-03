/* 07-stripped — SPOILER: this is the solution source.
 * Built -O2 and stripped: no symbols, gcc inlines and reorders everything.
 * Key: 16 upper-case hex chars = two 32-bit words, hi (first 8) and lo (last 8).
 *   1. length 16, only 0-9 A-F (own parser, no strtoul to hook)
 *   2. hi * 0x9E3779B1 == 0xD9EA7484   (mod 2^32; the multiplier is odd, so
 *      this has exactly one solution: hi = 0xD9EA7484 * inverse(0x9E3779B1))
 *   3. rotl(hi, ROT) ^ lo == 0xC8B6E217
 * Exactly one valid key: 7A3F19C42B8E6D50.
 * A decoy compare against a fake key runs first and only prints a taunt. */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* Not const and not static: with plain #defines gcc -O2 inverts the multiply
 * at compile time and emits `cmpl $<answer>`. A writable global table keeps the
 * maths in the binary. Order on purpose not "mul, t1, t2". */
uint32_t params[4] = { 0xC8B6E217u, 13u, 0x9E3779B1u, 0xD9EA7484u };
#define TGT2 params[0]
#define ROT  params[1]
#define MUL  params[2]
#define TGT1 params[3]

static int parse_word(const char *s, uint32_t *out) {
    uint32_t w = 0;
    for (int i = 0; i < 8; i++) {
        char c = s[i];
        uint32_t d;
        if (c >= '0' && c <= '9') d = c - '0';
        else if (c >= 'A' && c <= 'F') d = c - 'A' + 10;
        else return 0;
        w = (w << 4) | d;
    }
    *out = w;
    return 1;
}

static uint32_t rotl(uint32_t x, uint32_t r) { r &= 31; return (x << r) | (x >> ((32 - r) & 31)); }

static int check(const char *k) {
    uint32_t hi, lo;
    if (strlen(k) != 16) return 0;
    if (!parse_word(k, &hi) || !parse_word(k + 8, &lo)) return 0;
    if (hi * MUL != TGT1) return 0;
    if ((rotl(hi, ROT) ^ lo) != TGT2) return 0;
    return 1;
}

int main(void) {
    char buf[128];
    printf("Activation code: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    if (!strcmp(buf, "DEADBEEFCAFEBABE")) {
        puts("Nice try. Wrong.");
        return 1;
    }
    if (check(buf)) {
        puts("Correct! Activated.");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

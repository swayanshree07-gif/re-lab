/* 09-custom-hash — SPOILER: this is the solution source.
 * Password: exactly 8 lowercase letters. Accepted iff hash64(pw) == TARGET.
 *   h = 0x5EEDFACE0BADF00D
 *   for each c: h = rotl64(h, 13) ^ c; h *= 0x100000001B3   (FNV-1 64-bit prime)
 *   h ^= h >> 31                                            (final mix)
 * Every step is invertible (odd multiplier, rotate, xor, xorshift >= 32 bits),
 * so the intended attack is meet-in-the-middle: 26^4 forward states from the
 * seed vs 26^4 backward states from the target. 26^8 brute force is too slow.
 * Intended password: zebrafin. */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

#define PW_LEN 8

static uint64_t rotl64(uint64_t x, unsigned r) {
    return (x << r) | (x >> (64 - r));
}

static uint64_t hash64(const char *s, size_t n) {
    uint64_t h = 0x5EEDFACE0BADF00Dull;
    for (size_t i = 0; i < n; i++) {
        h = rotl64(h, 13) ^ (unsigned char)s[i];
        h *= 0x100000001B3ull;
    }
    h ^= h >> 31;
    return h;
}

static int valid_charset(const char *s, size_t n) {
    for (size_t i = 0; i < n; i++)
        if (s[i] < 'a' || s[i] > 'z') return 0;
    return 1;
}

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    size_t n = strlen(buf);
    if (n != PW_LEN || !valid_charset(buf, n)) { puts("Wrong."); return 1; }
    if (hash64(buf, n) == 0x733D1A5BE9412BF5ull) {
        puts("Correct! Nice preimage.");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

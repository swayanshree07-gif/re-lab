/* 04-xor-rolling — SPOILER: this is the solution source.
 * Each input byte is XORed with a 5-byte repeating key, then the previous
 * *encoded* byte is added (a chained/rolling add, starting from an IV):
 *     e[i] = ((in[i] ^ key[i % 5]) + e[i-1]) & 0xff,   e[-1] = IV
 * The result must equal `expected`. Length is checked first (via sizeof).
 * Inverse: in[i] = ((e[i] - e[i-1]) & 0xff) ^ key[i % 5].
 * Re-generate `expected` with the snippet in the desk writeup. */
#include <stdio.h>
#include <string.h>

#define KEYLEN 5
#define IV 0x2c

static const unsigned char key_bytes[KEYLEN] = { 0xc3, 0x1e, 0x77, 0x9a, 0x05 };

static const unsigned char expected[] = {
    0xdd, 0x0b, 0x26, 0x1c, 0x50, 0xfd, 0x76, 0x9e,
    0x8f, 0xc5, 0x7f, 0xec, 0x14, 0xc2, 0x39, 0x29,
    0x6a, 0x7f, 0x28, 0x99, 0x50, 0x7d, 0x82
};

static int check_password(const char *in) {
    if (strlen(in) != sizeof expected) return 0;
    unsigned char prev = IV;
    int diff = 0;
    for (size_t i = 0; i < sizeof expected; i++) {
        unsigned char e = (unsigned char)(((unsigned char)in[i] ^ key_bytes[i % KEYLEN]) + prev);
        diff |= e ^ expected[i];
        prev = e;
    }
    return diff == 0;
}

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    if (check_password(buf)) {
        puts("Correct! Rolling keys still roll backwards.");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

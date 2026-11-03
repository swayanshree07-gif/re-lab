/* 05-math-key — SPOILER: this is the solution source.
 * The key is a 12-digit number. It must pass every rule:
 *   1. exactly 12 characters, all digits, first digit not '0'
 *   2. sum of all 12 digits == 54
 *   3. last digit == (sum of the first 11 digits) % 10
 *   4. digit[3] == digit[8]
 *   5. digit[1] * digit[6] == 24   (as numbers)
 *   6. the 12-digit value % 9973 == 1337
 * Many keys are valid; any one works. Each rule is its own function so the
 * call graph in Ghidra mirrors the rules. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define KEYLEN 12

static int rule_format(const char *k) {
    if (strlen(k) != KEYLEN || k[0] == '0') return 0;
    for (int i = 0; i < KEYLEN; i++)
        if (k[i] < '0' || k[i] > '9') return 0;
    return 1;
}

static int digit_sum(const char *k, int n) {
    int s = 0;
    for (int i = 0; i < n; i++) s += k[i] - '0';
    return s;
}

static int rule_sum(const char *k)      { return digit_sum(k, KEYLEN) == 54; }
static int rule_check(const char *k)    { return k[11] - '0' == digit_sum(k, 11) % 10; }
static int rule_mirror(const char *k)   { return k[3] == k[8]; }
static int rule_product(const char *k)  { return (k[1] - '0') * (k[6] - '0') == 24; }
static int rule_modulus(const char *k)  { return strtoull(k, NULL, 10) % 9973 == 1337; }

static int (*const rules[])(const char *) = {
    rule_format, rule_sum, rule_check, rule_mirror, rule_product, rule_modulus,
};

int main(void) {
    char buf[128];
    printf("License key: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    for (size_t i = 0; i < sizeof rules / sizeof rules[0]; i++) {
        if (!rules[i](buf)) {
            puts("Wrong.");
            return 1;
        }
    }
    puts("Correct! Your key adds up.");
    return 0;
}

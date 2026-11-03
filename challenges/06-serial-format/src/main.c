/* 06-serial-format — SPOILER: this is the solution source.
 * Serial: XXXX-XXXX-XXXX-XXXX, 4 groups of 4 chars from a 32-char alphabet
 * (no 0/1/I/O). Let v(c) = index of c in the alphabet.
 *   1. length 19, '-' at positions 4, 9, 14, every other char in the alphabet
 *   2. groups 0..2: last char == alphabet[(3*v0 + 5*v1 + 7*v2 + g) % 32]
 *      (g = group index: the same three chars give a different check char
 *       in each group)
 *   3. group 3, chars 0..2: v(g3[j]) == (v(g0[j]) + v(g1[j]) + v(g2[j])) % 32
 *   4. group 3, last char: same weighted checksum as rule 2 with g = 3
 *   5. not every group may be identical. Dead code: identical groups already
 *      fail rule 2 because the check char depends on g. A red herring.
 * 9 free characters, so 32^9 valid serials. */
#include <stdio.h>
#include <string.h>

static const char alphabet[] = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";

static int val(char c) {
    for (int i = 0; i < 32; i++)
        if (alphabet[i] == c) return i;
    return -1;
}

static int group_check(const int *v, int g) {
    return (3 * v[0] + 5 * v[1] + 7 * v[2] + g) % 32 == v[3];
}

static int check_serial(const char *s) {
    int v[4][4];
    if (strlen(s) != 19) return 0;
    for (int g = 0; g < 4; g++) {
        for (int j = 0; j < 4; j++) {
            v[g][j] = val(s[g * 5 + j]);
            if (v[g][j] < 0) return 0;
        }
        if (g < 3 && s[g * 5 + 4] != '-') return 0;
    }
    for (int g = 0; g < 3; g++)
        if (!group_check(v[g], g)) return 0;
    for (int j = 0; j < 3; j++)
        if ((v[0][j] + v[1][j] + v[2][j]) % 32 != v[3][j]) return 0;
    if (!group_check(v[3], 3)) return 0;
    if (!memcmp(s, s + 5, 4) && !memcmp(s, s + 10, 4) && !memcmp(s, s + 15, 4))
        return 0;
    return 1;
}

int main(void) {
    char buf[128];
    printf("Serial (XXXX-XXXX-XXXX-XXXX): ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    if (check_serial(buf)) {
        puts("Correct! Serial registered.");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

#include <stdio.h>
#include <string.h>

#define N 16
struct rule { unsigned char op, a, b, k; };
#include "rules.h"

static int eval_rule(const struct rule *r, const unsigned char *p) {
    unsigned x = p[r->a], y = p[r->b];
    switch (r->op) {
    case 0: return ((x + y) & 0xff) == r->k;
    case 1: return (x ^ y) == r->k;
    case 2: return (x * y) % 251 == r->k;
    case 3: return ((x - y) & 0xff) == r->k;
    case 4: return (x < y) == r->k;
    case 5: return ((x >> r->b) & 1) == r->k;
    }
    return 0;
}

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) return 1;
    buf[strcspn(buf, "\n")] = 0;
    int ok = strlen(buf) == N;
    for (int i = 0; ok && i < N; i++)
        ok = buf[i] > 0x20 && buf[i] < 0x7f;
    for (int i = 0; ok && i < NRULES; i++)
        ok &= eval_rule(&rules[i], (const unsigned char *)buf);
    if (ok) { puts("Correct!"); return 0; }
    puts("Wrong.");
    return 1;
}

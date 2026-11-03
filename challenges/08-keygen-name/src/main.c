/* 08-keygen-name — SPOILER: this is the solution source.
 * Line 1: name (4..32 printable chars). Line 2: serial "XXXXXXXX-YYYY" (upper hex).
 *   h = 0x5EED1234; for each c: h = rotl(h, 5) ^ c; h *= 0x2F   (32-bit)
 *   s = sum(c) * len(name) & 0xFFFF
 *   serial = sprintf("%08X-%04X", h, s)
 * The serial is computed and compared with strcmp: a classic "serial fishing"
 * spot (break at strcmp, read the expected serial). */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

static void make_serial(const char *name, char *out) {
    uint32_t h = 0x5EED1234u, s = 0;
    size_t n = strlen(name);
    for (size_t i = 0; i < n; i++) {
        unsigned char c = (unsigned char)name[i];
        h = (h << 5) | (h >> 27);
        h ^= c;
        h *= 0x2Fu;
        s += c;
    }
    s = (s * (uint32_t)n) & 0xFFFF;
    sprintf(out, "%08X-%04X", h, s);
}

int main(void) {
    char name[128], serial[128], expect[32];
    printf("Name: ");
    fflush(stdout);
    if (!fgets(name, sizeof name, stdin)) { puts("Wrong."); return 1; }
    name[strcspn(name, "\n")] = 0;
    printf("Serial: ");
    fflush(stdout);
    if (!fgets(serial, sizeof serial, stdin)) { puts("Wrong."); return 1; }
    serial[strcspn(serial, "\n")] = 0;
    size_t n = strlen(name);
    if (n < 4 || n > 32) { puts("Wrong."); return 1; }
    for (size_t i = 0; i < n; i++)
        if (name[i] < 0x20 || name[i] > 0x7e) { puts("Wrong."); return 1; }
    make_serial(name, expect);
    if (strcmp(serial, expect) == 0) {
        printf("Correct! Registered to %s.\n", name);
        return 0;
    }
    puts("Wrong.");
    return 1;
}

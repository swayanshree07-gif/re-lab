/* 02-stack-strings — SPOILER: this is the solution source.
 * The password is never stored as a string: it is written byte-by-byte
 * into a stack buffer (in shuffled order) by `movb $imm, off(%rbp)`
 * instructions, so `strings` can't see it. The compare is a hand-written
 * loop, so ltrace shows no strcmp either. Solve it by reading the movb
 * immediates in objdump/Ghidra, or by dumping the buffer in gdb. */
#include <stdio.h>
#include <string.h>

#define KEYLEN 18

static int check_password(const char *in) {
    volatile char key[KEYLEN + 1];
    key[14] = 'c';
    key[12] = 's';
    key[7] = 'u';
    key[17] = 't';
    key[6] = 'b';
    key[0] = 's';
    key[8] = '1';
    key[3] = 'c';
    key[9] = 'l';
    key[4] = 'k';
    key[10] = 't';
    key[11] = '_';
    key[15] = 'r';
    key[13] = '3';
    key[5] = '_';
    key[16] = '3';
    key[2] = '4';
    key[1] = 't';
    key[KEYLEN] = 0;

    size_t n = strlen(in);
    if (n != KEYLEN) return 0;
    int diff = 0;
    for (int i = 0; i < KEYLEN; i++)
        diff |= key[i] ^ in[i];
    return diff == 0;
}

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    if (check_password(buf)) {
        puts("Correct! strings(1) can't save you now.");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

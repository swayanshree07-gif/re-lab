/* 03-xor-single — SPOILER: this is the solution source.
 * The password is stored in .rodata XORed with one byte (0x5a), including
 * its NUL terminator (so the blob ends in the key byte itself). The input is
 * XORed with the same key and compared with memcmp, so even ltrace only sees
 * encoded bytes. A plaintext decoy password sits in .rodata for `strings`.
 * Re-generate the blob with:
 *   python3 -c "print(', '.join('0x%02x'%(c^0x5a) for c in b'PASSWORD\0'))" */
#include <stdio.h>
#include <string.h>

#define KEY 0x5a

static const unsigned char enc_password[] = {
    0x22, 0x6a, 0x28, 0x05, 0x6b, 0x29, 0x05, 0x34, 0x6a,
    0x2e, 0x05, 0x39, 0x28, 0x23, 0x2a, 0x2e, 0x6a, 0x5a,
};

static const char decoy[] = "hunter2_is_the_password";

static int check_password(const char *in) {
    unsigned char tmp[sizeof enc_password];
    size_t n = strlen(in);
    if (n + 1 != sizeof enc_password) return 0;
    for (size_t i = 0; i <= n; i++)       /* includes the NUL */
        tmp[i] = (unsigned char)in[i] ^ KEY;
    return memcmp(tmp, enc_password, sizeof enc_password) == 0;
}

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    if (strcmp(buf, decoy) == 0) {
        puts("Wrong. Nice try, but strings(1) lies sometimes.");
        return 1;
    }
    if (check_password(buf)) {
        puts("Correct! One byte of key is no key at all.");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

/* 14-smc-xor — SPOILER: this is the solution source.
 *
 * The real check, verify(), is stored XOR-encrypted in the on-disk binary, so
 * `objdump -d` of verify() shows garbage (invalid instructions). Just before
 * the check runs, unlock() marks the page(s) spanning region_begin..region_end
 * writable+executable (mprotect), XORs the bytes back with xkey[] in place,
 * then restores read+exec. Only after that does main() call verify().
 *
 * region_begin() / region_end() are empty markers kept in source order with
 * -fno-toplevel-reorder; the encrypted span is [region_begin, region_end), so
 * it contains exactly the marker + verify(). unlock(), main() and the data
 * live outside the span and stay in the clear.
 *
 * Real check: enc[i] = password[i] ^ ((KEY0 + i) & 0xff), KEY0 = 0x4d is a
 * one-byte immediate hidden inside the encrypted verify() — a 256-key search
 * against the live binary (or decrypting verify() and reading the immediate)
 * recovers it. Password: s3lf_mod_x0r */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include <sys/mman.h>
#include <unistd.h>

#define PW_LEN 12

/* password[i] ^ ((0x4d + i) & 0xff) */
static const unsigned char enc[PW_LEN] = {
    0x3e, 0x7d, 0x23, 0x36, 0x0e, 0x3f, 0x3c, 0x30, 0x0a, 0x2e, 0x67, 0x2a };

/* repeating key used to encrypt/decrypt the verify() code region */
static const unsigned char xkey[8] = {
    0x3b, 0x9e, 0x44, 0xd7, 0x12, 0xa8, 0x6c, 0xf1 };

/* plaintext decoy to tempt `strings` */
static const char decoy[] __attribute__((used)) = "try-letmein-please";

__attribute__((noinline)) void region_begin(void) { __asm__ volatile(""); }

__attribute__((noinline)) int verify(const char *in) {
    if (strlen(in) != PW_LEN) return 0;
    unsigned char k = 0x4d;                 /* KEY0, hidden in encrypted code */
    for (int i = 0; i < PW_LEN; i++) {
        unsigned char ks = (unsigned char)(k + (unsigned char)i);
        if ((unsigned char)(in[i] ^ ks) != enc[i]) return 0;
    }
    return 1;
}

__attribute__((noinline)) void region_end(void) { __asm__ volatile(""); }

static void unlock(void) {
    uintptr_t b = (uintptr_t)(void *)region_begin;
    uintptr_t e = (uintptr_t)(void *)region_end;
    long pg = sysconf(_SC_PAGESIZE);
    uintptr_t page = b & ~(uintptr_t)(pg - 1);
    size_t len = (size_t)(e - page);
    if (mprotect((void *)page, len, PROT_READ | PROT_WRITE | PROT_EXEC) != 0) return;
    unsigned char *p = (unsigned char *)b;
    for (size_t i = 0; i < (size_t)(e - b); i++)
        p[i] ^= xkey[i % sizeof xkey];
    mprotect((void *)page, len, PROT_READ | PROT_EXEC);
}

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    unlock();
    if (verify(buf)) {
        puts("Correct! Code decrypted itself.");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

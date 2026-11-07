/* 15-smc-layers — SPOILER: this is the solution source.
 *
 * Two layers of self-modifying code.
 *
 *   Layer 1 (static): stage1() lives between r1_begin/r1_end and is stored
 *   XOR-encrypted on disk under a fixed 8-byte key xkey1[]. unlock1() decrypts
 *   it at startup (mprotect RWX, XOR, restore RX) before main calls it. This is
 *   exactly the 14-smc-xor trick.
 *
 *   Layer 2 (input-derived): stage2() lives between r2_begin/r2_end and is
 *   stored XOR-encrypted under an 8-byte key that is DERIVED FROM THE PASSWORD
 *   PREFIX. stage1() validates the 4-char prefix via a 32-bit FNV-1a hash
 *   (target_h, patched in by encrypt.py), and only if it matches does it call
 *   unlock2(prefix), which recomputes the same key from the prefix and decrypts
 *   stage2 in place. So stage2's real code cannot be read statically without
 *   first recovering the prefix.
 *
 * Password: prefix "deep" (4 chars) + rest "-la_yers" (8 chars) = "deep-la_yers".
 *   - prefix: fnv1a32("deep") == target_h  (brute-force [a-z]{4} to recover it)
 *   - key2[i] = prefix[i&3] ^ ((h >> (8*(i&3))) & 0xff)   (h = fnv1a32(prefix))
 *   - stage2 check: rest[i] ^ ((K2 + i) & 0xff) == rest_enc[i], K2 = 0x6b, an
 *     immediate hidden inside the encrypted stage2.
 *
 * fnv32(), unlock1(), unlock2() stay in the clear (they reveal the mechanism);
 * the prefix and stage2's body do not.
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include <sys/mman.h>
#include <unistd.h>

#define PREFIX_LEN 4
#define REST_LEN   8
#define PW_LEN     (PREFIX_LEN + REST_LEN)

/* rest[i] ^ ((0x6b + i) & 0xff); contains a NUL on purpose (byte array). */
static const unsigned char rest_enc[REST_LEN] = {
    0x46, 0x00, 0x0c, 0x31, 0x16, 0x15, 0x03, 0x01 };

/* static key for layer 1 */
static const unsigned char xkey1[8] = {
    0x7c, 0x1d, 0xe3, 0x4a, 0x90, 0x2b, 0xd6, 0x5f };

/* fnv1a32 of the correct prefix; patched into the binary by encrypt.py.
 * Non-zero initialiser so it lands in .data (file-backed) and can be patched. */
static volatile uint32_t target_h = 0xffffffffu;

/* plaintext decoy to tempt `strings` */
static const char decoy[] __attribute__((used)) = "layer-cake-is-a-lie";

static void unlock2(const char *prefix);

/* 32-bit FNV-1a, in the clear: reveals the hash but not its preimage. */
__attribute__((noinline)) uint32_t fnv32(const unsigned char *p, size_t n) {
    uint32_t h = 2166136261u;
    for (size_t i = 0; i < n; i++) {
        h ^= p[i];
        h *= 16777619u;
    }
    return h;
}

__attribute__((noinline)) void r1_begin(void) { __asm__ volatile(""); }

/* LAYER 1 code (encrypted on disk under xkey1). Validates the prefix, then
 * decrypts layer 2 using a key derived from that prefix. */
__attribute__((noinline)) int stage1(const char *in) {
    uint32_t h = fnv32((const unsigned char *)in, PREFIX_LEN);
    if (h != target_h) return 0;
    unlock2(in);                 /* prefix is correct -> decrypt stage2 */
    return 1;
}

__attribute__((noinline)) void r1_end(void) { __asm__ volatile(""); }

__attribute__((noinline)) void r2_begin(void) { __asm__ volatile(""); }

/* LAYER 2 code (encrypted on disk under a prefix-derived key). Checks the rest
 * of the password. K2 is a one-byte immediate buried in this encrypted body. */
__attribute__((noinline)) int stage2(const char *rest) {
    unsigned char k2 = 0x6b;
    for (int i = 0; i < REST_LEN; i++) {
        unsigned char ks = (unsigned char)(k2 + (unsigned char)i);
        if ((unsigned char)(rest[i] ^ ks) != rest_enc[i]) return 0;
    }
    return 1;
}

__attribute__((noinline)) void r2_end(void) { __asm__ volatile(""); }

/* --- the SMC plumbing, in the clear ------------------------------------- */

static void xor_region(uintptr_t b, uintptr_t e, const unsigned char *key, size_t klen) {
    long pg = sysconf(_SC_PAGESIZE);
    uintptr_t page = b & ~(uintptr_t)(pg - 1);
    size_t len = (size_t)(e - page);
    if (mprotect((void *)page, len, PROT_READ | PROT_WRITE | PROT_EXEC) != 0) return;
    unsigned char *p = (unsigned char *)b;
    for (size_t i = 0; i < (size_t)(e - b); i++)
        p[i] ^= key[i % klen];
    mprotect((void *)page, len, PROT_READ | PROT_EXEC);
}

static void unlock1(void) {
    xor_region((uintptr_t)(void *)r1_begin, (uintptr_t)(void *)r1_end, xkey1, sizeof xkey1);
}

/* key2[i] = prefix[i&3] ^ ((h >> (8*(i&3))) & 0xff), h = fnv1a32(prefix) */
static void unlock2(const char *prefix) {
    uint32_t h = fnv32((const unsigned char *)prefix, PREFIX_LEN);
    unsigned char key2[8];
    for (int i = 0; i < 8; i++)
        key2[i] = (unsigned char)prefix[i & 3] ^ (unsigned char)((h >> (8 * (i & 3))) & 0xff);
    xor_region((uintptr_t)(void *)r2_begin, (uintptr_t)(void *)r2_end, key2, sizeof key2);
}

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    if (strlen(buf) != PW_LEN) { puts("Wrong."); return 1; }

    unlock1();                       /* layer 1: static decrypt */
    if (stage1(buf) && stage2(buf + PREFIX_LEN)) {
        puts("Correct! Peeled both layers.");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

/* 12-int3-scan — SPOILER: this is the solution source.
 * guard() walks the machine code between region_begin() and region_end()
 * (the check functions, kept in source order with -fno-toplevel-reorder):
 *   - more 0xCC bytes than the clean build has (int3 = a gdb software
 *     breakpoint; the count is needed because 0xCC can occur naturally
 *     inside an instruction, e.g. a rip-relative displacement) -> decoy path
 *   - FNV-1a hash of the bytes is folded into the key:
 *       key = base_key ^ hash ^ expected[0]
 *     so the key is only right while the code is untouched. `expected[0]` is a
 *     placeholder patched in after linking by src/patch_hash.py,
 *     together with the clean 0xCC count (expected[1]).
 * Real check: enc[i] = ((in[i] ^ keybyte(i % 4)) + 13*i) & 0xff
 * Decoy:      dec[i] = in[i] ^ (0xa5 - 3*i)
 * Real password: n0_cc_h3r3!  Decoy: br34kp01nt */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define PW_LEN 11
#define DECOY_LEN 10

static const uint32_t base_key = 0x7a3c91e5;
/* placeholders, replaced after linking by {FNV-1a hash, number of 0xCC bytes}
 * of the region */
static volatile const uint32_t expected[2] = { 0x1badc0deu, 0x0badf00du };
static const unsigned char enc[PW_LEN] = {
    0x8b, 0xae, 0x7d, 0x40, 0xba, 0x0f, 0xa2, 0xa4, 0xff, 0x17, 0x9f };
static const unsigned char dec[DECOY_LEN] = {
    0xc7, 0xd0, 0xac, 0xa8, 0xf2, 0xe6, 0xa3, 0xa1, 0xe3, 0xfe };

static uint32_t key;      /* set by guard() */
static int tampered;      /* 1 = extra int3 bytes found in the region */

__attribute__((noinline)) void region_begin(void) { __asm__ volatile(""); }

__attribute__((noinline)) int check_password(const char *in) {
    if (strlen(in) != PW_LEN) return 0;
    int ok = 1;
    for (int i = 0; i < PW_LEN; i++) {
        unsigned char kb = (unsigned char)(key >> (8 * (i % 4)));
        if ((unsigned char)((in[i] ^ kb) + 13 * i) != enc[i]) ok = 0;
    }
    return ok;
}

__attribute__((noinline)) int check_decoy(const char *in) {
    if (strlen(in) != DECOY_LEN) return 0;
    for (int i = 0; i < DECOY_LEN; i++)
        if ((unsigned char)(in[i] ^ (0xa5 - 3 * i)) != dec[i]) return 0;
    return 1;
}

__attribute__((noinline)) int verify(const char *in) {
    return tampered ? check_decoy(in) : check_password(in);
}

__attribute__((noinline)) void region_end(void) { __asm__ volatile(""); }

static void guard(void) {
    const volatile unsigned char *p = (const volatile unsigned char *)(uintptr_t)region_begin;
    const volatile unsigned char *end = (const volatile unsigned char *)(uintptr_t)region_end;
    uint32_t h = 0x811c9dc5u, ccs = 0;
    for (; p < end; p++) {
        unsigned char b = *p;
        if (b == 0xCC) ccs++;
        h = (h ^ b) * 0x01000193u;
    }
    if (ccs != expected[1]) tampered = 1;
    key = base_key ^ h ^ expected[0];
}

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    guard();
    if (verify(buf)) {
        puts("Correct! Clean code, clean run.");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

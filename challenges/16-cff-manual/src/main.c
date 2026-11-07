/* 16-cff-manual — SPOILER: source of the challenge.
 *
 * The password check was written as a normal loop first (see check_reference
 * in the writeup) and then flattened BY HAND into a state machine:
 *
 *   - every basic block of the loop is one `case` of a single switch inside
 *     `for (;;)`, so the CFG in Ghidra is one dispatcher fanning out to ~16
 *     blocks that all jump back to it;
 *   - state ids are random 32-bit constants (no 0,1,2,... order);
 *   - a block never writes its successor directly: it XORs a delta into the
 *     state (`st ^= S_CUR ^ S_NEXT`), so the immediate you see is neither the
 *     current nor the next state;
 *   - two-way branches are branchless: SEL(c, a, b) picks a delta with a mask
 *     instead of a jump, so the only conditional jumps left are the dispatcher's;
 *   - three junk states (JUNK1..3) look like a second check against a decoy
 *     table and lead to WIN, but the condition that reaches them can never be
 *     true (i > 0x40 after the length was checked to be 14).
 *
 * Reference algorithm (per character, no early exit):
 *     t = rotl8(((c ^ h) + i*step) & 0xff, i % 5 + 1);   ok &= (t == exp_tab[i]);
 *     h = (h * mul + c) & 0xff;                         h starts at seed
 */
#include <stdio.h>
#include <string.h>

#define S_INIT  0x5c8cc1abu
#define S_LEN   0x781ef86fu
#define S_LOOP  0x7b00c7f4u
#define S_LOAD  0x48f165d5u
#define S_MIX   0x6abd685au
#define S_ROT   0x3a0562d5u
#define S_CMP   0x725ed09du
#define S_HASH  0x017f9ee6u
#define S_INC   0x68d605d4u
#define S_DONE  0xdaa8b2a6u
#define S_WIN   0xa85f68b6u
#define S_FAIL  0xb6043106u
#define S_EXIT  0x424458b6u
#define S_JUNK1 0x3ce44e27u
#define S_JUNK2 0xa28f17d8u
#define S_JUNK3 0x38f12d92u

#define PW_LEN 14

/* branchless select: c ? a : b */
#define SEL(c, a, b) ((b) ^ (((a) ^ (b)) & (0u - (unsigned)!!(c))))
/* move from state `cur` to `next` by XOR delta */
#define GO(cur, next) (st ^= ((cur) ^ (next)))
#define GO2(cur, c, a, b) (st ^= SEL((c), (cur) ^ (a), (cur) ^ (b)))

/* seed, step, mul. Note: even at -O0 gcc folds const-array reads with a
 * constant index, so these show up as immediates ($0x5a, $0x7, $0x1f) in the
 * blocks; the array itself stays in .rodata as a second place to read them. */
const unsigned char mix[3] = {0x5a, 0x07, 0x1f};

const unsigned char exp_tab[PW_LEN] = {
    0x78, 0x9c, 0x15, 0x5f, 0x06, 0x94, 0x6c, 0xdf, 0xa2, 0x02, 0x7a, 0x9b, 0xdb, 0x9e};

/* only used by the unreachable junk states */
const unsigned char alt_tab[PW_LEN] = {
    0x5e, 0xf0, 0x19, 0x45, 0x2d, 0xa5, 0xde, 0x79, 0xc7, 0x43, 0xf8, 0x91, 0x33, 0xac};

int check(const char *in) {
    unsigned st = S_INIT;
    unsigned i = 0, n = 0, ok = 0, ret = 0;
    unsigned h = 0, c = 0, t = 0, r = 0;

    for (;;) {
        switch (st) {
        case S_INIT:
            h = mix[0]; i = 0; ok = 1; ret = 0;
            n = (unsigned)strlen(in);
            GO(S_INIT, S_LEN);
            break;
        case S_LEN:
            GO2(S_LEN, n == PW_LEN, S_LOOP, S_FAIL);
            break;
        case S_LOOP:
            /* i > 0x40 is impossible here: the junk path is dead */
            GO2(S_LOOP, i < PW_LEN, S_LOAD, SEL(i > 0x40, S_JUNK1, S_DONE));
            break;
        case S_LOAD:
            c = (unsigned char)in[i];
            GO(S_LOAD, S_MIX);
            break;
        case S_MIX:
            t = ((c ^ h) + i * mix[1]) & 0xff;
            GO(S_MIX, S_ROT);
            break;
        case S_ROT:
            r = i % 5 + 1;
            t = ((t << r) | (t >> (8 - r))) & 0xff;
            GO(S_ROT, S_CMP);
            break;
        case S_CMP:
            ok &= (t == exp_tab[i]);
            GO(S_CMP, S_HASH);
            break;
        case S_HASH:
            h = (h * mix[2] + c) & 0xff;
            GO(S_HASH, S_INC);
            break;
        case S_INC:
            i++;
            GO(S_INC, S_LOOP);
            break;
        case S_DONE:
            GO2(S_DONE, ok, S_WIN, S_FAIL);
            break;
        case S_JUNK1: /* dead: looks like a second, "real" check */
            ok = 1; h = mix[0];
            for (i = 0; i < PW_LEN; i++) {
                c = (unsigned char)in[i];
                t = ((c ^ h) + i * mix[1]) & 0xff;
                r = i % 5 + 1;
                t = ((t << r) | (t >> (8 - r))) & 0xff;
                ok &= (t == alt_tab[i]);
                h = (h * mix[2] + c) & 0xff;
            }
            GO(S_JUNK1, S_JUNK2);
            break;
        case S_JUNK2:
            ok ^= (n != PW_LEN);
            GO(S_JUNK2, S_JUNK3);
            break;
        case S_JUNK3:
            GO2(S_JUNK3, ok, S_WIN, S_FAIL);
            break;
        case S_WIN:
            ret = 1;
            GO(S_WIN, S_EXIT);
            break;
        case S_FAIL:
            ret = 0;
            GO(S_FAIL, S_EXIT);
            break;
        case S_EXIT:
            return (int)ret;
        default: /* corrupted state: fail closed */
            return 0;
        }
    }
}

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) return 1;
    buf[strcspn(buf, "\n")] = 0;
    if (check(buf)) {
        puts("Correct!");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

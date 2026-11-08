/* rvemu self-test: same source built natively (libc) and for RV64IM
 * (freestanding); both print a hash of many arithmetic results. */
#ifdef NATIVE
#include <unistd.h>
#include <stdlib.h>
#define WRITE(p, n) if (write(1, p, n) < 0) exit(1)
#define EXIT(c) exit(c)
#else
static long sys3(long n, long a, long b, long c) {
    register long a0 asm("a0") = a; register long a1 asm("a1") = b;
    register long a2 asm("a2") = c; register long a7 asm("a7") = n;
    asm volatile("ecall" : "+r"(a0) : "r"(a1), "r"(a2), "r"(a7) : "memory");
    return a0;
}
#define WRITE(p, n) sys3(64, 1, (long)(p), n)
#define EXIT(c) sys3(93, c, 0, 0)
#endif
typedef unsigned long u64; typedef long s64; typedef int s32; typedef unsigned u32;

static volatile u64 vals[] = {0, 1, 2, 3, 7, 0xff, 0x7fffffff, 0x80000000, 0xffffffff,
    0x123456789abcdefull, 0x8000000000000000ull, 0xffffffffffffffffull, (u64)-7, (u64)-2};
#define NV (sizeof vals / sizeof vals[0])

static u64 h = 0xcbf29ce484222325ull;
static void mix(u64 v) { h = (h ^ v) * 0x100000001b3ull; }

#ifdef NATIVE
int main(void)
#else
void _start(void)
#endif
{
    for (unsigned i = 0; i < NV; i++) for (unsigned j = 0; j < NV; j++) {
        u64 a = vals[i], b = vals[j];
        s64 sa = (s64)a, sb = (s64)b; s32 a32 = (s32)a, b32 = (s32)b;
        mix(a + b); mix(a - b); mix(a * b); mix(a ^ b); mix(a | b); mix(a & b);
        mix(a << (b & 63)); mix(a >> (b & 63)); mix((u64)(sa >> (b & 63)));
        mix(sa < sb); mix(a < b);
        mix((u64)(s64)(s32)((u32)a32 + (u32)b32)); mix((u64)(s64)(s32)((u32)a32 * (u32)b32));
        mix((u64)(s64)(s32)((u32)a32 << (b & 31))); mix((u64)(s64)(a32 >> (b & 31)));
        mix((u64)(s64)(s32)((u32)a32 >> (b & 31)));
        mix((u64)(((__int128)sa * sb) >> 64)); mix((u64)(((unsigned __int128)a * b) >> 64));
        if (b) { mix(a / b); mix(a % b); }
        if (sb && !(sa == (s64)0x8000000000000000ull && sb == -1)) { mix((u64)(sa / sb)); mix((u64)(sa % sb)); }
        if (b32 && !(a32 == (s32)0x80000000 && b32 == -1)) { mix((u64)(s64)(a32 / b32)); mix((u64)(s64)(a32 % b32)); }
        if ((u32)b) { mix((u64)(s64)(s32)((u32)a / (u32)b)); mix((u64)(s64)(s32)((u32)a % (u32)b)); }
    }
    char out[17];
    for (int k = 0; k < 16; k++) out[k] = "0123456789abcdef"[(h >> (60 - 4 * k)) & 15];
    out[16] = '\n';
    WRITE(out, 17);
    EXIT(0);
#ifdef NATIVE
    return 0;
#endif
}

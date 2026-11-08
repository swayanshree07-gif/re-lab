/* The real check. Compiled freestanding into a flat position-independent
 * blob (payload.ld), then compressed + encrypted by pack.py.
 * int check(const unsigned char *s, unsigned long n) -> 1 if correct. */
static const unsigned char want[18] = {
#include "want.h"
};

__attribute__((section(".text.entry")))
int check(const unsigned char *s, unsigned long n) {
    unsigned k = 0x5a, bad = 0;
    if (n != sizeof want) return 0;
    for (unsigned long i = 0; i < n; i++) {
        unsigned t = ((s[i] ^ k) + 3 * i) & 0xff;
        bad |= t ^ want[i];
        k = (k * 5 + s[i]) & 0xff;
    }
    return bad == 0;
}

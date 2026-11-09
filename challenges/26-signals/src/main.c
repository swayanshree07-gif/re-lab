/* 26-signals (spoiler!). Each password byte is fed to a signal handler that
 * is reached only through a deliberate fault: NULL write -> SIGSEGV,
 * divide by zero -> SIGFPE, ud2 -> SIGILL. The handler mixes the byte into
 * the state and siglongjmps back. No direct call to the mixing code exists. */
#include <setjmp.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "table.h"

static sigjmp_buf back;
static volatile uint32_t h = 0x5167A11;
static volatile unsigned char cur;
static volatile int zero;
static volatile int sink = 1;

static uint32_t rol(uint32_t x, int r) { return (x << r) | (x >> (32 - r)); }

static void on_segv(int s) { (void)s; h = rol(h, 5) ^ (uint32_t)cur * 0x01000193u; siglongjmp(back, 1); }
static void on_fpe(int s)  { (void)s; h = (h + (uint32_t)cur * 0x2F1D3u) * 0x9E3779B1u; siglongjmp(back, 2); }
static void on_ill(int s)  { (void)s; h = (h ^ ((uint32_t)cur << 11) ^ cur) * 0x85EBCA6Bu; siglongjmp(back, 3); }

static void fault(int kind) {
    if (kind == 0) *(volatile int *)(uintptr_t)zero = 1;
    else if (kind == 1) sink = sink / zero;   /* idiv by 0 */
    else __builtin_trap();
}

int main(void) {
    char buf[128];
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_segv; sigaction(SIGSEGV, &sa, NULL);
    sa.sa_handler = on_fpe;  sigaction(SIGFPE, &sa, NULL);
    sa.sa_handler = on_ill;  sigaction(SIGILL, &sa, NULL);

    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) return 1;
    buf[strcspn(buf, "\n")] = 0;
    if (strlen(buf) != PW_LEN) { puts("Wrong."); return 1; }

    int ok = 1;
    for (volatile int i = 0; i < PW_LEN; i++) {
        cur = (unsigned char)buf[i];
        if (sigsetjmp(back, 1) == 0) {
            fault(kinds[i]);
            puts("Wrong.");          /* never reached */
            return 1;
        }
        ok &= ((h >> 8) & 0xffff) == expect[i];
    }
    puts(ok ? "Correct!" : "Wrong.");
    return ok ? 0 : 1;
}

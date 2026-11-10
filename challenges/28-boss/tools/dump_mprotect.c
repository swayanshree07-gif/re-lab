/* Solver helper (LD_PRELOAD): when the target makes a page executable with
 * mprotect, write that page to $DUMP_PATH, then do the real mprotect.
 * The boss checks for ptrace tracers and timing, not for preloads. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>

int mprotect(void *addr, size_t len, int prot) {
    static int (*real)(void *, size_t, int);
    if (!real) real = (int (*)(void *, size_t, int))dlsym(RTLD_NEXT, "mprotect");
    const char *path = getenv("DUMP_PATH");
    if (path && (prot & PROT_EXEC)) {
        FILE *f = fopen(path, "wb");
        if (f) { fwrite(addr, 1, len, f); fclose(f); }
    }
    return real(addr, len, prot);
}

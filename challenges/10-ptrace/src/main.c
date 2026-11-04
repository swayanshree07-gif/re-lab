/* 10-ptrace — SPOILER: this is the solution source.
 * A constructor runs before main and calls ptrace(PTRACE_TRACEME) twice:
 *   - 1st call fails (-1)      -> a debugger/tracer (gdb, strace, ltrace) is attached
 *   - 1st and 2nd both succeed -> ptrace was faked (LD_PRELOAD stub returning 0)
 *   - normal: 1st succeeds, 2nd fails (already traced by the parent)
 * Any "traced" verdict silently switches to a decoy password (blobs[1]), which
 * is then *accepted* inside the debugger and rejected outside it.
 * Real password: tr4c3l3ss (blobs[0] ^ 0x5A). Decoy: gdb_found (blobs[1] ^ 0x73). */
#include <stdio.h>
#include <string.h>
#include <sys/ptrace.h>

#define PW_LEN 9

static const unsigned char keys[2] = { 0x5a, 0x73 };
static const unsigned char blobs[2][PW_LEN] = {
    { 0x2e, 0x28, 0x6e, 0x39, 0x69, 0x36, 0x69, 0x29, 0x29 },
    { 0x14, 0x17, 0x11, 0x2c, 0x15, 0x1c, 0x06, 0x1d, 0x17 },
};

static int mode;   /* 0 = clean, 1 = traced (decoy) */

__attribute__((constructor))
static void init_runtime(void) {
    long first = ptrace(PTRACE_TRACEME, 0, NULL, NULL);
    long second = ptrace(PTRACE_TRACEME, 0, NULL, NULL);
    if (first == -1 || second != -1)
        mode = 1;
}

static int check(const char *in) {
    if (strlen(in) != PW_LEN) return 0;
    const unsigned char *b = blobs[mode];
    unsigned char k = keys[mode];
    for (int i = 0; i < PW_LEN; i++)
        if ((unsigned char)(in[i] ^ k) != b[i]) return 0;
    return 1;
}

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;
    if (check(buf)) {
        puts("Correct! No one was watching.");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

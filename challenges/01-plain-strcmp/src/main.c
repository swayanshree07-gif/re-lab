/* 01-plain-strcmp — SPOILER: this is the solution source.
 * The password sits in .rodata as a plain C string and is checked with
 * strcmp(). Find it with `strings`, `ltrace`, a gdb breakpoint on strcmp,
 * or Ghidra's Defined Strings window. A couple of decoys keep `strings`
 * from being a one-shot answer. */
#include <stdio.h>
#include <string.h>

static const char *decoys[] = { "admin", "hunter2", "letmein-please" };
static const char password[] = "gh1dra_and_ch1ll";

int main(void) {
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) { puts("Wrong."); return 1; }
    buf[strcspn(buf, "\n")] = 0;

    for (size_t i = 0; i < sizeof decoys / sizeof *decoys; i++)
        if (strcmp(buf, decoys[i]) == 0) {
            puts("Nice try, that one is a decoy.");
            puts("Wrong.");
            return 1;
        }

    if (strcmp(buf, password) == 0) {
        puts("Correct! Welcome to the lab.");
        return 0;
    }
    puts("Wrong.");
    return 1;
}

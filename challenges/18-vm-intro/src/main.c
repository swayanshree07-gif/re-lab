/* 18-vm-intro: a tiny stack VM runs bytecode that checks the password. */
#include <stdio.h>
#include <string.h>
#include "bytecode.h"

enum { OP_PUSH = 1, OP_LOAD, OP_XOR, OP_ADD, OP_SUB, OP_EQ, OP_AND, OP_JZ,
       OP_LEN, OP_HALT, OP_DUP, OP_POP };

static int run_vm(const unsigned char *code, unsigned n, const char *in)
{
    unsigned char st[64];
    int sp = 0;
    unsigned pc = 0;
    size_t len = strlen(in);
    while (pc < n) {
        unsigned char op = code[pc++], a, b;
        switch (op) {
        case OP_PUSH: if (sp >= 64) return 0; st[sp++] = code[pc++]; break;
        case OP_LOAD: { unsigned char i = code[pc++];
                        if (sp >= 64) return 0;
                        st[sp++] = i < len ? (unsigned char)in[i] : 0; break; }
        case OP_LEN:  if (sp >= 64) return 0; st[sp++] = (unsigned char)(len > 255 ? 255 : len); break;
        case OP_DUP:  if (sp < 1 || sp >= 64) return 0; st[sp] = st[sp - 1]; sp++; break;
        case OP_POP:  if (sp < 1) return 0; sp--; break;
        case OP_XOR: case OP_ADD: case OP_SUB: case OP_EQ: case OP_AND:
            if (sp < 2) return 0;
            b = st[--sp]; a = st[--sp];
            st[sp++] = op == OP_XOR ? a ^ b : op == OP_ADD ? (unsigned char)(a + b)
                     : op == OP_SUB ? (unsigned char)(a - b) : op == OP_EQ ? a == b
                     : (a && b);
            break;
        case OP_JZ: { unsigned char t = code[pc++];
                      if (sp < 1) return 0;
                      if (st[--sp] == 0)
                          pc = t;
                      break; }
        case OP_HALT: return sp >= 1 && st[sp - 1];
        default: return 0;
        }
    }
    return 0;
}

int main(void)
{
    char buf[128];
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) return 1;
    buf[strcspn(buf, "\r\n")] = 0;
    if (run_vm(bytecode, sizeof bytecode, buf)) { puts("Correct!"); return 0; }
    puts("Wrong.");
    return 1;
}

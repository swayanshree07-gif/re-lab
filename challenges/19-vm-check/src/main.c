/* 19-vm-check: an 8-register VM with loops checks the password. */
#include <stdio.h>
#include <string.h>
#include "bytecode.h"

enum { MOVI = 0x10, MOV, LDI, LDM, ADD = 0x20, SUB, XOR, MUL, ROL, ADDI, OR,
       CMP = 0x30, JMP, JZ, JNZ, LEN = 0x40, HALT = 0xFF };

typedef struct { unsigned char r[8]; int zf; unsigned pc; } vm_t;

static int run_vm(vm_t *vm, const unsigned char *code, unsigned n, const char *in)
{
    size_t len = strlen(in);
    unsigned steps = 0;
    while (vm->pc < n && steps++ < 100000) {
        unsigned char op = code[vm->pc++];
        unsigned char x = vm->pc < n ? code[vm->pc] : 0;
        unsigned char *ra = &vm->r[(x >> 4) & 7], *rb = &vm->r[x & 7];
        if ((op == MOVI || op == ADDI || op == ROL) && vm->pc + 1 >= n) return 0;
        switch (op) {
        case MOVI: vm->r[x & 7] = code[vm->pc + 1]; vm->pc += 2; break;
        case ADDI: vm->r[x & 7] += code[vm->pc + 1]; vm->pc += 2; break;
        case ROL:  { unsigned s = code[vm->pc + 1] & 7; unsigned char v = vm->r[x & 7];
                     vm->r[x & 7] = (unsigned char)((v << s) | (v >> ((8 - s) & 7))); vm->pc += 2; break; }
        case MOV: *ra = *rb; vm->pc++; break;
        case LDI: *ra = *rb < len ? (unsigned char)in[*rb] : 0; vm->pc++; break;
        case LDM: *ra = *rb < sizeof vmdata ? vmdata[*rb] : 0; vm->pc++; break;
        case ADD: *ra += *rb; vm->pc++; break;
        case SUB: *ra -= *rb; vm->pc++; break;
        case XOR: *ra ^= *rb; vm->pc++; break;
        case MUL: *ra *= *rb; vm->pc++; break;
        case OR:  *ra |= *rb; vm->pc++; break;
        case CMP: vm->zf = *ra == *rb; vm->pc++; break;
        case JMP: vm->pc = x; break;
        case JZ:  vm->pc = vm->zf ? x : vm->pc + 1; break;
        case JNZ: vm->pc = vm->zf ? vm->pc + 1 : x; break;
        case LEN: vm->r[x & 7] = (unsigned char)(len > 255 ? 255 : len); vm->pc++; break;
        case HALT: return vm->r[x & 7] == 0;
        default: return 0;
        }
    }
    return 0;
}

int main(void)
{
    char buf[128];
    vm_t vm = {0};
    printf("Password: ");
    fflush(stdout);
    if (!fgets(buf, sizeof buf, stdin)) return 1;
    buf[strcspn(buf, "\r\n")] = 0;
    if (run_vm(&vm, bytecode, sizeof bytecode, buf)) { puts("Correct!"); return 0; }
    puts("Wrong.");
    return 1;
}

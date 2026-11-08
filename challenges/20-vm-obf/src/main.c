/* 20-vm-obf: register VM with a shuffled opcode table and encrypted bytecode. */
#include <stdio.h>
#include <string.h>
#include "bytecode.h"

/* handler indexes; the encoded opcode bytes are mapped through optab[] */
enum { H_MOVI, H_MOV, H_LDI, H_LDM, H_ADD, H_SUB, H_XOR, H_MUL, H_ROL, H_ADDI, H_OR,
       H_CMP, H_JMP, H_JZ, H_JNZ, H_LEN, H_HALT };

typedef struct { unsigned char r[8]; int zf; unsigned pc; } vm_t;

static unsigned char fetch(unsigned pc)
{
    return blob[pc] ^ (unsigned char)(vmkey[pc & 3] + pc * 0x3b);
}

static int run_vm(vm_t *vm, unsigned n, const char *in)
{
    size_t len = strlen(in);
    unsigned steps = 0;
    while (vm->pc < n && steps++ < 100000) {
        unsigned char h = optab[fetch(vm->pc++)];
        unsigned char x = vm->pc < n ? fetch(vm->pc) : 0;
        unsigned char *ra = &vm->r[(x >> 4) & 7], *rb = &vm->r[x & 7];
        if ((h == H_MOVI || h == H_ADDI || h == H_ROL) && vm->pc + 1 >= n) return 0;
        switch (h) {
        case H_MOVI: vm->r[x & 7] = fetch(vm->pc + 1); vm->pc += 2; break;
        case H_ADDI: vm->r[x & 7] += fetch(vm->pc + 1); vm->pc += 2; break;
        case H_ROL:  { unsigned s = fetch(vm->pc + 1) & 7; unsigned char v = vm->r[x & 7];
                       vm->r[x & 7] = (unsigned char)((v << s) | (v >> ((8 - s) & 7))); vm->pc += 2; break; }
        case H_MOV: *ra = *rb; vm->pc++; break;
        case H_LDI: *ra = *rb < len ? (unsigned char)in[*rb] : 0; vm->pc++; break;
        case H_LDM: *ra = *rb < sizeof vmdata ? vmdata[*rb] : 0; vm->pc++; break;
        case H_ADD: *ra += *rb; vm->pc++; break;
        case H_SUB: *ra -= *rb; vm->pc++; break;
        case H_XOR: *ra ^= *rb; vm->pc++; break;
        case H_MUL: *ra *= *rb; vm->pc++; break;
        case H_OR:  *ra |= *rb; vm->pc++; break;
        case H_CMP: vm->zf = *ra == *rb; vm->pc++; break;
        case H_JMP: vm->pc = x; break;
        case H_JZ:  vm->pc = vm->zf ? x : vm->pc + 1; break;
        case H_JNZ: vm->pc = vm->zf ? vm->pc + 1 : x; break;
        case H_LEN: vm->r[x & 7] = (unsigned char)(len > 255 ? 255 : len); vm->pc++; break;
        case H_HALT: return vm->r[x & 7] == 0;
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
    if (run_vm(&vm, sizeof blob, buf)) { puts("Correct!"); return 0; }
    puts("Wrong.");
    return 1;
}

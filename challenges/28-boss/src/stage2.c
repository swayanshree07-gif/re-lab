/* Stage 2 (SPOILER): a byte-register VM. Only exists after stage 1 decrypts
 * it. The bytecode (vm_code.h, from gen2.py; ISA in isa.py) is XOR-encrypted
 * with a rolling key and decrypted one instruction at a time. Input = the
 * text after the first '|', up to the next '|'. Returns 0x5732 ("W2") on
 * success; anything else is a failure. Freestanding: no libc, no relocs. */
#include "vm_code.h"

__attribute__((section(".text.entry")))
int stage2(const unsigned char *rest, unsigned long n) {
    unsigned char r[4] = {0, 0, 0, 0}, bad = 0, k = BC_KEY;
    unsigned long len = 0;
    while (len < n && rest[len] != '|') len++;
    for (unsigned pc = 0; pc + 2 < sizeof bc; pc += 3) {
        unsigned char op = bc[pc] ^ k;   k = (unsigned char)(k * 37 + 0x5B);
        unsigned char a = bc[pc + 1] ^ k; k = (unsigned char)(k * 37 + 0x5B);
        unsigned char b = bc[pc + 2] ^ k; k = (unsigned char)(k * 37 + 0x5B);
        unsigned char *ra = &r[a & 3];
        switch (op) {
        case OP_LDI:  *ra = b; break;
        case OP_LDB:  *ra = b < len ? rest[b] : 0; break;
        case OP_LEN:  *ra = len > 255 ? 255 : (unsigned char)len; break;
        case OP_XORI: *ra ^= b; break;
        case OP_MULI: *ra = (unsigned char)(*ra * b); break;
        case OP_ADD:  *ra = (unsigned char)(*ra + r[b & 3]); break;
        case OP_ROLI: { unsigned s = b & 7; *ra = (unsigned char)((*ra << s) | (*ra >> ((8 - s) & 7))); break; }
        case OP_MOV:  *ra = r[b & 3]; break;
        case OP_CHK:  bad |= *ra ^ b; break;
        case OP_HALT: return bad ? 0 : 0x5732;
        default:      return 0;
        }
    }
    return 0;
}

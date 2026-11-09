/* Stage 2 (SPOILER). Placeholder until Day 26 replaces it with the VM stage:
 * a flat PIC blob that only exists after stage 1 decrypts it. Returns the
 * magic 0x5732 ("W2") so main can tell a real decrypt from garbage that
 * happened to pass the checksum. */
__attribute__((section(".text.entry")))
int stage2(const unsigned char *rest, unsigned long n) {
    (void)rest; (void)n;
    return 0x5732;
}

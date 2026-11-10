# 23-riscv: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

Not x86. Use `file`, then `riscv64-*-objdump` or `llvm-objdump`.

</details>

<details><summary>Level 2: Direction</summary>

It's freestanding: no libc. Find the `ecall`s for read and write.

</details>

<details><summary>Level 3: Near-spoiler</summary>

Either read the compare statically, or count executed instructions per guess (side channel) in an emulator.

</details>


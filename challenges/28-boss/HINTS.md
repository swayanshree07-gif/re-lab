# 28-boss: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

Three stages, input `a|b|c`. Each one unlocks the next.

</details>

<details><summary>Level 2: Direction</summary>

Stage 1: anti-debug salts change the keystream, and the right key decrypts stage 2. Stage 2: a new VM. Stage 3: a block cipher.

</details>

<details><summary>Level 3: Near-spoiler</summary>

Solve stage 1 statically, dump the unpacked page (an mprotect hook works), write a VM disassembler, then invert the Feistel rounds (or z3).

</details>

